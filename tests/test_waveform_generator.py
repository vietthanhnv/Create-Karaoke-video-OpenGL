"""
Tests for audio waveform generation and display functionality.
"""

import os
import tempfile
import numpy as np
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.audio.waveform_generator import WaveformGenerator, WaveformData, WaveformRenderer
from src.core.models import AudioAsset, ValidationResult


class TestWaveformGenerator:
    """Test cases for WaveformGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = WaveformGenerator()
        
        # Create a mock audio asset
        self.mock_audio = AudioAsset(
            path="/test/audio.mp3",
            duration=10.0,
            sample_rate=44100,
            channels=2,
            format=".mp3"
        )
    
    def test_initialization(self):
        """Test WaveformGenerator initialization."""
        generator = WaveformGenerator()
        assert generator is not None
        assert hasattr(generator, '_waveform_cache')
        assert hasattr(generator, '_ffmpeg_available')
    
    def test_cache_key_creation(self):
        """Test cache key creation for waveform data."""
        # Mock os.path.getmtime to return consistent value
        with patch('os.path.getmtime', return_value=1234567890):
            key1 = self.generator._create_cache_key("/test/audio.mp3", 1000, None)
            key2 = self.generator._create_cache_key("/test/audio.mp3", 1000, None)
            key3 = self.generator._create_cache_key("/test/audio.mp3", 2000, None)
            
            assert key1 == key2  # Same parameters should give same key
            assert key1 != key3  # Different resolution should give different key
    
    def test_fallback_waveform_generation(self):
        """Test fallback waveform generation when FFmpeg is not available."""
        # Force fallback mode
        self.generator._ffmpeg_available = False
        
        waveform_data = self.generator._generate_fallback(self.mock_audio, 100, None)
        
        assert isinstance(waveform_data, WaveformData)
        assert len(waveform_data.samples) == 100
        assert waveform_data.duration == 10.0
        assert waveform_data.channels == 1
        assert waveform_data.resolution == 100
        
        # Check that samples are normalized to [-1, 1]
        assert np.all(waveform_data.samples >= -1.0)
        assert np.all(waveform_data.samples <= 1.0)
    
    def test_waveform_generation_with_invalid_audio(self):
        """Test waveform generation with invalid audio asset."""
        # Create invalid audio asset
        invalid_audio = AudioAsset(
            path="",  # Empty path
            duration=0.0,
            sample_rate=0,
            channels=0,
            format=""
        )
        
        with pytest.raises(ValueError):
            self.generator.generate_waveform(invalid_audio, 100)
    
    @patch('os.path.exists')
    def test_waveform_caching(self, mock_exists):
        """Test that waveform data is properly cached."""
        # Mock file existence
        mock_exists.return_value = True
        
        # Force fallback mode to avoid FFmpeg issues
        self.generator._ffmpeg_available = False
        
        # Mock the audio asset validation to pass
        with patch.object(self.mock_audio, 'validate') as mock_validate:
            mock_validate.return_value = ValidationResult(is_valid=True)
            
            # Mock the fallback generation to track calls
            with patch.object(self.generator, '_generate_fallback') as mock_fallback:
                mock_waveform = WaveformData(
                    samples=np.zeros(100),
                    sample_rate=100.0,
                    duration=10.0,
                    channels=1,
                    resolution=100
                )
                mock_fallback.return_value = mock_waveform
                
                # First call should generate waveform
                result1 = self.generator.generate_waveform(self.mock_audio, 100)
                assert mock_fallback.call_count == 1
                
                # Second call with same parameters should use cache
                result2 = self.generator.generate_waveform(self.mock_audio, 100)
                assert mock_fallback.call_count == 1  # Should not be called again
                
                assert result1 is result2  # Should be same cached object
    
    def test_waveform_segment_extraction(self):
        """Test extraction of waveform segments."""
        # Create test waveform data
        samples = np.sin(np.linspace(0, 4 * np.pi, 1000))  # 1000 samples
        waveform_data = WaveformData(
            samples=samples,
            sample_rate=100.0,  # 100 samples per second
            duration=10.0,
            channels=1,
            resolution=1000
        )
        
        # Extract segment from 2s to 4s (should be samples 200-400)
        segment = self.generator.get_waveform_segment(waveform_data, 2.0, 4.0)
        
        assert len(segment) == 200  # 2 seconds * 100 samples/second
        np.testing.assert_array_equal(segment, samples[200:400])
    
    def test_waveform_resampling(self):
        """Test waveform resampling to different resolutions."""
        # Create test waveform data
        original_samples = np.sin(np.linspace(0, 2 * np.pi, 100))
        waveform_data = WaveformData(
            samples=original_samples,
            sample_rate=10.0,
            duration=10.0,
            channels=1,
            resolution=100
        )
        
        # Resample to different resolution
        resampled = self.generator.resample_waveform(waveform_data, 200)
        
        assert resampled.resolution == 200
        assert len(resampled.samples) == 200
        assert resampled.duration == waveform_data.duration
        assert resampled.sample_rate == 20.0  # 200 samples / 10 seconds
    
    def test_peak_levels_extraction(self):
        """Test extraction of peak levels for visualization."""
        # Create test waveform with known peaks
        samples = np.array([0.5, -0.8, 0.3, -0.2, 0.9, -0.1] * 50)  # 300 samples
        waveform_data = WaveformData(
            samples=samples,
            sample_rate=30.0,
            duration=10.0,
            channels=1,
            resolution=300
        )
        
        # Get peak levels
        peaks = self.generator.get_peak_levels(waveform_data, num_peaks=10)
        
        assert len(peaks) == 10
        assert all(isinstance(peak, tuple) and len(peak) == 2 for peak in peaks)
        assert all(min_val <= max_val for min_val, max_val in peaks)
    
    def test_cache_management(self):
        """Test cache management functionality."""
        # Add some data to cache
        self.generator._waveform_cache['test_key'] = WaveformData(
            samples=np.zeros(100),
            sample_rate=10.0,
            duration=10.0,
            channels=1,
            resolution=100
        )
        
        # Check cache info
        cache_info = self.generator.get_cache_info()
        assert cache_info['cached_waveforms'] == 1
        assert cache_info['total_samples'] == 100
        
        # Clear cache
        self.generator.clear_cache()
        cache_info = self.generator.get_cache_info()
        assert cache_info['cached_waveforms'] == 0
        assert cache_info['total_samples'] == 0
    
    @patch('subprocess.run')
    def test_ffmpeg_availability_check(self, mock_run):
        """Test FFmpeg availability checking."""
        # Test when FFmpeg is available
        mock_run.return_value.returncode = 0
        generator = WaveformGenerator()
        assert generator.is_ffmpeg_available()
        
        # Test when FFmpeg is not available
        mock_run.side_effect = FileNotFoundError()
        generator = WaveformGenerator()
        assert not generator.is_ffmpeg_available()
    
    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('numpy.fromfile')
    def test_ffmpeg_waveform_generation(self, mock_fromfile, mock_exists, mock_run):
        """Test waveform generation using FFmpeg."""
        # Mock successful FFmpeg execution
        mock_run.return_value.returncode = 0
        mock_exists.return_value = True
        
        # Mock audio data
        mock_audio_data = np.sin(np.linspace(0, 4 * np.pi, 44100))  # 1 second of audio
        mock_fromfile.return_value = mock_audio_data
        
        # Enable FFmpeg for this test
        self.generator._ffmpeg_available = True
        
        waveform_data = self.generator._generate_with_ffmpeg(self.mock_audio, 1000, None)
        
        assert isinstance(waveform_data, WaveformData)
        assert waveform_data.resolution == 1000
        assert len(waveform_data.samples) == 1000
        
        # Verify FFmpeg was called
        mock_run.assert_called()


class TestWaveformData:
    """Test cases for WaveformData dataclass."""
    
    def test_waveform_data_creation(self):
        """Test WaveformData creation and properties."""
        samples = np.random.randn(1000)
        waveform_data = WaveformData(
            samples=samples,
            sample_rate=100.0,
            duration=10.0,
            channels=2,
            resolution=1000
        )
        
        assert np.array_equal(waveform_data.samples, samples)
        assert waveform_data.sample_rate == 100.0
        assert waveform_data.duration == 10.0
        assert waveform_data.channels == 2
        assert waveform_data.resolution == 1000


class TestWaveformRenderer:
    """Test cases for WaveformRenderer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.renderer = WaveformRenderer()
        
        # Create test waveform data
        samples = np.sin(np.linspace(0, 4 * np.pi, 1000))
        self.waveform_data = WaveformData(
            samples=samples,
            sample_rate=100.0,
            duration=10.0,
            channels=1,
            resolution=1000
        )
    
    def test_renderer_initialization(self):
        """Test WaveformRenderer initialization."""
        renderer = WaveformRenderer()
        assert renderer is not None
        assert hasattr(renderer, 'background_color')
        assert hasattr(renderer, 'waveform_color')
        assert hasattr(renderer, 'center_line_color')
        assert hasattr(renderer, 'peak_color')
    
    def test_waveform_rendering(self):
        """Test waveform rendering to pixel array."""
        width, height = 800, 200
        
        rendered = self.renderer.render_waveform_data(
            self.waveform_data, width, height
        )
        
        assert rendered.shape == (height, width, 4)  # RGBA format
        assert rendered.dtype == np.float32
        
        # Check that values are in valid range [0, 1]
        assert np.all(rendered >= 0.0)
        assert np.all(rendered <= 1.0)
    
    def test_waveform_rendering_with_time_range(self):
        """Test waveform rendering with specific time range."""
        width, height = 400, 100
        
        rendered = self.renderer.render_waveform_data(
            self.waveform_data, width, height, start_time=2.0, end_time=6.0
        )
        
        assert rendered.shape == (height, width, 4)
        # Should render only the specified time segment
    
    def test_color_customization(self):
        """Test custom color setting."""
        custom_bg = (0.2, 0.2, 0.2, 1.0)
        custom_waveform = (1.0, 0.5, 0.0, 0.8)
        
        self.renderer.set_colors(
            background=custom_bg,
            waveform=custom_waveform
        )
        
        assert self.renderer.background_color == custom_bg
        assert self.renderer.waveform_color == custom_waveform
    
    def test_empty_waveform_rendering(self):
        """Test rendering with empty waveform data."""
        empty_waveform = WaveformData(
            samples=np.array([]),
            sample_rate=0.0,
            duration=0.0,
            channels=1,
            resolution=0
        )
        
        rendered = self.renderer.render_waveform_data(empty_waveform, 100, 50)
        
        # Should return background-filled image
        assert rendered.shape == (50, 100, 4)
        # All pixels should be background color
        expected_bg = np.full((50, 100, 4), self.renderer.background_color, dtype=np.float32)
        np.testing.assert_array_equal(rendered, expected_bg)


class TestWaveformIntegration:
    """Integration tests for waveform functionality."""
    
    def test_end_to_end_waveform_processing(self):
        """Test complete waveform processing pipeline."""
        # Create audio asset with mock validation
        audio_asset = AudioAsset(
            path="/mock/audio.mp3",
            duration=5.0,
            sample_rate=44100,
            channels=2,
            format=".mp3"
        )
        
        # Mock validation to pass
        with patch.object(audio_asset, 'validate') as mock_validate:
            mock_validate.return_value = ValidationResult(is_valid=True)
            
            # Generate waveform (will use fallback)
            generator = WaveformGenerator()
            generator._ffmpeg_available = False  # Force fallback
            waveform_data = generator.generate_waveform(audio_asset, resolution=500)
            
            # Render waveform
            renderer = WaveformRenderer()
            rendered = renderer.render_waveform_data(waveform_data, 400, 100)
            
            # Verify results
            assert isinstance(waveform_data, WaveformData)
            assert waveform_data.resolution == 500
            assert rendered.shape == (100, 400, 4)
    
    def test_waveform_with_timeline_engine(self):
        """Test waveform integration with timeline engine."""
        from src.core.timeline_engine import TimelineEngine
        
        # Create mock audio asset
        audio_asset = AudioAsset(
            path="/test/audio.mp3",
            duration=10.0,
            sample_rate=44100,
            channels=2,
            format=".mp3"
        )
        
        # Mock validation to pass
        with patch.object(audio_asset, 'validate') as mock_validate:
            mock_validate.return_value = ValidationResult(is_valid=True)
            
            # Create timeline engine
            timeline = TimelineEngine()
            timeline.audio_asset = audio_asset
            
            # Force fallback mode for consistent testing
            timeline._waveform_generator._ffmpeg_available = False
            
            # Get waveform data through timeline
            waveform_data = timeline.get_waveform_data(resolution=1000)
            
            # Should return waveform data (fallback mode)
            assert waveform_data is not None
            assert isinstance(waveform_data, WaveformData)
            assert waveform_data.resolution == 1000
    
    def test_waveform_segment_extraction_integration(self):
        """Test waveform segment extraction through timeline engine."""
        from src.core.timeline_engine import TimelineEngine
        
        # Create mock audio asset
        audio_asset = AudioAsset(
            path="/test/audio.mp3",
            duration=20.0,
            sample_rate=44100,
            channels=2,
            format=".mp3"
        )
        
        # Mock validation to pass
        with patch.object(audio_asset, 'validate') as mock_validate:
            mock_validate.return_value = ValidationResult(is_valid=True)
            
            # Create timeline engine
            timeline = TimelineEngine()
            timeline.audio_asset = audio_asset
            
            # Force fallback mode for consistent testing
            timeline._waveform_generator._ffmpeg_available = False
            
            # Get waveform segment
            segment = timeline.get_waveform_segment(5.0, 10.0, resolution=500)
            
            # Should return segment data
            assert segment is not None
            assert isinstance(segment, np.ndarray)
            assert len(segment) > 0


if __name__ == '__main__':
    pytest.main([__file__])