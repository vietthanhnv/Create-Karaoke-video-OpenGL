"""
Tests for the timeline engine and keyframe system.
"""

import pytest
import numpy as np
from datetime import datetime
from unittest.mock import patch

from src.core.timeline_engine import TimelineEngine
from src.core.keyframe_system import KeyframeSystem
from src.core.models import (
    VideoAsset, AudioAsset, SubtitleTrack, TextElement, Keyframe,
    InterpolationType, EasingType, AnimationEffect, AnimationType
)


class TestTimelineEngine:
    """Test cases for TimelineEngine class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.video_asset = VideoAsset(
            path="test_video.mp4",
            duration=10.0,
            fps=30.0,
            resolution=(1920, 1080),
            codec="h264"
        )
        
        self.audio_asset = AudioAsset(
            path="test_audio.mp3",
            duration=10.0,
            sample_rate=44100,
            channels=2,
            format="mp3"
        )
        
        self.timeline = TimelineEngine(self.video_asset)
    
    def test_timeline_initialization(self):
        """Test timeline engine initialization."""
        assert self.timeline.video_asset == self.video_asset
        assert self.timeline.current_time == 0.0
        assert self.timeline.duration == 10.0
        assert not self.timeline.is_playing()
    
    def test_timeline_without_video(self):
        """Test timeline engine without video asset."""
        timeline = TimelineEngine()
        assert timeline.video_asset is None
        assert timeline.duration == 0.0
    
    def test_current_time_bounds(self):
        """Test current time bounds checking."""
        # Test setting time within bounds
        self.timeline.current_time = 5.0
        assert self.timeline.current_time == 5.0
        
        # Test setting time below bounds
        self.timeline.current_time = -1.0
        assert self.timeline.current_time == 0.0
        
        # Test setting time above bounds
        self.timeline.current_time = 15.0
        assert self.timeline.current_time == 10.0
    
    def test_video_asset_update(self):
        """Test updating video asset."""
        new_video = VideoAsset(
            path="new_video.mp4",
            duration=20.0,
            fps=60.0,
            resolution=(3840, 2160),
            codec="h265"
        )
        
        self.timeline.video_asset = new_video
        assert self.timeline.video_asset == new_video
        assert self.timeline.duration == 20.0
    
    def test_audio_asset_management(self):
        """Test audio asset management."""
        assert self.timeline.audio_asset is None
        
        self.timeline.audio_asset = self.audio_asset
        assert self.timeline.audio_asset == self.audio_asset
        
        # Setting audio asset should clear waveform cache
        self.timeline.audio_asset = None
        assert self.timeline.audio_asset is None
    
    def test_subtitle_track_management(self):
        """Test subtitle track management."""
        track = SubtitleTrack(
            id="track1",
            elements=[],
            keyframes=[],
            start_time=0.0,
            end_time=5.0
        )
        
        # Add track
        self.timeline.add_subtitle_track(track)
        assert self.timeline.get_subtitle_track("track1") == track
        assert len(self.timeline.get_all_tracks()) == 1
        
        # Remove track
        assert self.timeline.remove_subtitle_track("track1")
        assert self.timeline.get_subtitle_track("track1") is None
        assert len(self.timeline.get_all_tracks()) == 0
        
        # Try to remove non-existent track
        assert not self.timeline.remove_subtitle_track("nonexistent")
    
    def test_keyframe_management(self):
        """Test keyframe addition and removal."""
        track = SubtitleTrack(
            id="track1",
            elements=[],
            keyframes=[],
            start_time=0.0,
            end_time=10.0
        )
        self.timeline.add_subtitle_track(track)
        
        # Add keyframe
        properties = {"opacity": 1.0, "position": (100, 200)}
        assert self.timeline.add_keyframe("track1", 2.0, properties)
        
        # Check keyframe was added
        keyframes = self.timeline.get_keyframes_at_time("track1", 2.0)
        assert len(keyframes) == 1
        assert keyframes[0].time == 2.0
        assert keyframes[0].properties == properties
        
        # Add keyframe at same time (should replace)
        new_properties = {"opacity": 0.5, "position": (150, 250)}
        assert self.timeline.add_keyframe("track1", 2.0, new_properties)
        keyframes = self.timeline.get_keyframes_at_time("track1", 2.0)
        assert len(keyframes) == 1
        assert keyframes[0].properties == new_properties
        
        # Remove keyframe
        assert self.timeline.remove_keyframe("track1", 2.0)
        keyframes = self.timeline.get_keyframes_at_time("track1", 2.0)
        assert len(keyframes) == 0
        
        # Try to add keyframe outside track bounds
        assert not self.timeline.add_keyframe("track1", 15.0, properties)
        
        # Try to add keyframe to non-existent track
        assert not self.timeline.add_keyframe("nonexistent", 2.0, properties)
    
    def test_keyframe_interpolation(self):
        """Test keyframe property interpolation."""
        track = SubtitleTrack(
            id="track1",
            elements=[],
            keyframes=[],
            start_time=0.0,
            end_time=10.0
        )
        self.timeline.add_subtitle_track(track)
        
        # Add keyframes
        self.timeline.add_keyframe("track1", 1.0, {"opacity": 0.0, "scale": 1.0})
        self.timeline.add_keyframe("track1", 3.0, {"opacity": 1.0, "scale": 2.0})
        
        # Test interpolation at midpoint
        props = self.timeline.interpolate_properties("track1", 2.0)
        assert props["opacity"] == 0.5
        assert props["scale"] == 1.5
        
        # Test interpolation at keyframe positions
        props = self.timeline.interpolate_properties("track1", 1.0)
        assert props["opacity"] == 0.0
        assert props["scale"] == 1.0
        
        props = self.timeline.interpolate_properties("track1", 3.0)
        assert props["opacity"] == 1.0
        assert props["scale"] == 2.0
        
        # Test interpolation outside keyframe range
        props = self.timeline.interpolate_properties("track1", 0.5)
        assert props["opacity"] == 0.0  # Should use first keyframe
        
        props = self.timeline.interpolate_properties("track1", 5.0)
        assert props["opacity"] == 1.0  # Should use last keyframe
    
    def test_keyframe_copy_paste(self):
        """Test keyframe copy and paste operations."""
        track = SubtitleTrack(
            id="track1",
            elements=[],
            keyframes=[],
            start_time=0.0,
            end_time=10.0
        )
        self.timeline.add_subtitle_track(track)
        
        # Add original keyframes
        self.timeline.add_keyframe("track1", 1.0, {"opacity": 0.5})
        self.timeline.add_keyframe("track1", 2.0, {"opacity": 1.0})
        
        # Copy keyframes
        original_keyframes = track.keyframes.copy()
        copied = self.timeline.copy_keyframes("track1", original_keyframes)
        
        # Verify copies are independent
        assert len(copied) == 2
        assert copied[0].time == 1.0
        assert copied[0].properties == {"opacity": 0.5}
        
        # Modify original and verify copy is unchanged
        original_keyframes[0].properties["opacity"] = 0.8
        assert copied[0].properties["opacity"] == 0.5
        
        # Paste with offset
        assert self.timeline.paste_keyframes("track1", copied, offset_time=3.0)
        
        # Verify pasted keyframes
        keyframes_at_4 = self.timeline.get_keyframes_at_time("track1", 4.0)
        assert len(keyframes_at_4) == 1
        assert keyframes_at_4[0].properties["opacity"] == 0.5
    
    def test_frame_time_conversion(self):
        """Test conversion between frames and time."""
        # Test frame to time conversion
        assert self.timeline.sync_to_video_frame(0) == 0.0
        assert self.timeline.sync_to_video_frame(30) == 1.0
        assert self.timeline.sync_to_video_frame(150) == 5.0
        
        # Test time to frame conversion
        assert self.timeline.get_frame_from_time(0.0) == 0
        assert self.timeline.get_frame_from_time(1.0) == 30
        assert self.timeline.get_frame_from_time(5.0) == 150
    
    def test_playback_controls(self):
        """Test playback control methods."""
        # Initial state
        assert not self.timeline.is_playing()
        assert self.timeline.get_playback_speed() == 1.0
        
        # Play
        self.timeline.play()
        assert self.timeline.is_playing()
        
        # Pause
        self.timeline.pause()
        assert not self.timeline.is_playing()
        
        # Set playback speed
        self.timeline.set_playback_speed(2.0)
        assert self.timeline.get_playback_speed() == 2.0
        
        # Test speed bounds
        self.timeline.set_playback_speed(0.05)  # Below minimum
        assert self.timeline.get_playback_speed() == 0.1
        
        self.timeline.set_playback_speed(15.0)  # Above maximum
        assert self.timeline.get_playback_speed() == 10.0
        
        # Stop
        self.timeline.current_time = 5.0
        self.timeline.stop()
        assert not self.timeline.is_playing()
        assert self.timeline.current_time == 0.0
    
    def test_timeline_update(self):
        """Test timeline update during playback."""
        self.timeline.play()
        
        # Update with normal speed
        self.timeline.update(0.1)  # 100ms
        assert self.timeline.current_time == 0.1
        
        # Update with faster speed
        self.timeline.set_playback_speed(2.0)
        self.timeline.update(0.1)
        assert abs(self.timeline.current_time - 0.3) < 1e-10  # 0.1 + (0.1 * 2.0)
        
        # Update past end of timeline
        self.timeline.current_time = 9.9
        self.timeline.update(0.2)
        assert self.timeline.current_time == 10.0
        assert not self.timeline.is_playing()  # Should auto-pause
    
    def test_seek_operation(self):
        """Test seek functionality."""
        self.timeline.seek(5.0)
        assert self.timeline.current_time == 5.0
        
        # Seek outside bounds
        self.timeline.seek(-1.0)
        assert self.timeline.current_time == 0.0
        
        self.timeline.seek(15.0)
        assert self.timeline.current_time == 10.0
    
    def test_waveform_generation(self):
        """Test audio waveform generation."""
        # Mock the audio asset validation to pass
        with patch.object(self.audio_asset, 'validate') as mock_validate:
            from src.core.models import ValidationResult
            mock_validate.return_value = ValidationResult(is_valid=True)
            
            # Force fallback mode for consistent testing
            self.timeline._waveform_generator._ffmpeg_available = False
            
            waveform_data = self.timeline.get_waveform_data(self.audio_asset, resolution=100)
            
            assert waveform_data is not None
            from src.audio.waveform_generator import WaveformData
            assert isinstance(waveform_data, WaveformData)
            assert waveform_data.resolution == 100
            assert len(waveform_data.samples) == 100
            assert np.all(np.abs(waveform_data.samples) <= 1.0)  # Should be normalized
            
            # Test caching
            waveform_data2 = self.timeline.get_waveform_data(self.audio_asset, resolution=100)
            assert waveform_data is waveform_data2  # Should be same cached object
    
    def test_active_elements_query(self):
        """Test querying active elements at specific time."""
        # Create track with elements
        text_element = TextElement(
            content="Test text",
            font_family="Arial",
            font_size=24.0,
            color=(1.0, 1.0, 1.0, 1.0),
            position=(100.0, 200.0),
            rotation=(0.0, 0.0, 0.0),
            effects=[]
        )
        
        track = SubtitleTrack(
            id="track1",
            elements=[text_element],
            keyframes=[],
            start_time=2.0,
            end_time=8.0
        )
        self.timeline.add_subtitle_track(track)
        
        # Query before track starts
        active = self.timeline.get_active_elements_at_time(1.0)
        assert len(active) == 0
        
        # Query during track
        active = self.timeline.get_active_elements_at_time(5.0)
        assert len(active) == 1
        assert active[0][0] == "track1"
        assert len(active[0][1]) == 1
        
        # Query after track ends
        active = self.timeline.get_active_elements_at_time(9.0)
        assert len(active) == 0
    
    def test_timeline_validation(self):
        """Test timeline validation."""
        # Valid timeline
        validation = self.timeline.validate_timeline()
        assert validation.is_valid
        
        # Add invalid track
        invalid_track = SubtitleTrack(
            id="",  # Invalid empty ID
            elements=[],
            keyframes=[],
            start_time=5.0,
            end_time=2.0  # Invalid: end < start
        )
        self.timeline.add_subtitle_track(invalid_track)
        
        validation = self.timeline.validate_timeline()
        assert not validation.is_valid
        assert "Track" in validation.error_message


class TestKeyframeSystem:
    """Test cases for KeyframeSystem class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.keyframe_system = KeyframeSystem()
    
    def test_keyframe_creation(self):
        """Test keyframe creation with validation."""
        properties = {"opacity": 1.0, "position": (100, 200)}
        
        keyframe = self.keyframe_system.create_keyframe(2.0, properties)
        assert keyframe.time == 2.0
        assert keyframe.properties == properties
        assert keyframe.interpolation_type == InterpolationType.LINEAR
        
        # Test with different interpolation type
        keyframe = self.keyframe_system.create_keyframe(
            3.0, properties, InterpolationType.BEZIER
        )
        assert keyframe.interpolation_type == InterpolationType.BEZIER
    
    def test_keyframe_creation_validation(self):
        """Test keyframe creation validation."""
        # Test negative time
        with pytest.raises(ValueError, match="time cannot be negative"):
            self.keyframe_system.create_keyframe(-1.0, {"opacity": 1.0})
        
        # Test empty properties
        with pytest.raises(ValueError, match="must have at least one property"):
            self.keyframe_system.create_keyframe(1.0, {})
    
    def test_interpolation_between_keyframes(self):
        """Test interpolation between keyframes."""
        kf1 = Keyframe(1.0, {"opacity": 0.0, "scale": 1.0}, InterpolationType.LINEAR)
        kf2 = Keyframe(3.0, {"opacity": 1.0, "scale": 2.0}, InterpolationType.LINEAR)
        
        # Test midpoint interpolation
        result = self.keyframe_system.interpolate_between(kf1, kf2, 0.5)
        assert result["opacity"] == 0.5
        assert result["scale"] == 1.5
        
        # Test at keyframe positions
        result = self.keyframe_system.interpolate_between(kf1, kf2, 0.0)
        assert result["opacity"] == 0.0
        
        result = self.keyframe_system.interpolate_between(kf1, kf2, 1.0)
        assert result["opacity"] == 1.0
    
    def test_easing_curves(self):
        """Test different easing curve applications."""
        # Test linear easing (no change)
        t = self.keyframe_system._apply_easing(0.5, EasingType.LINEAR)
        assert t == 0.5
        
        # Test ease-in (should be less than linear)
        t = self.keyframe_system._apply_easing(0.5, EasingType.EASE_IN)
        assert t < 0.5
        
        # Test ease-out (should be greater than linear)
        t = self.keyframe_system._apply_easing(0.5, EasingType.EASE_OUT)
        assert t > 0.5
        
        # Test bounce and elastic (should return valid values)
        t = self.keyframe_system._apply_easing(0.5, EasingType.BOUNCE)
        assert 0.0 <= t <= 1.0
        
        t = self.keyframe_system._apply_easing(0.5, EasingType.ELASTIC)
        assert isinstance(t, float)
    
    def test_value_interpolation_types(self):
        """Test interpolation of different value types."""
        # Numeric values
        result = self.keyframe_system._interpolate_value(0.0, 10.0, 0.3)
        assert result == 3.0
        
        # Integer values (should preserve type)
        result = self.keyframe_system._interpolate_value(0, 10, 0.3)
        assert result == 3
        assert isinstance(result, int)
        
        # Tuple values (colors, positions)
        result = self.keyframe_system._interpolate_value((0, 0, 0), (10, 20, 30), 0.5)
        assert result == (5, 10, 15)
        
        # Mixed tuple (numeric and non-numeric)
        result = self.keyframe_system._interpolate_value((0, "start"), (10, "end"), 0.3)
        assert result[0] == 3
        assert result[1] == "start"  # Step interpolation for strings
        
        # Boolean values (step interpolation)
        result = self.keyframe_system._interpolate_value(False, True, 0.3)
        assert result == False
        
        result = self.keyframe_system._interpolate_value(False, True, 0.7)
        assert result == True
        
        # Dictionary values (nested interpolation)
        dict1 = {"x": 0, "y": 0, "name": "start"}
        dict2 = {"x": 10, "y": 20, "name": "end"}
        result = self.keyframe_system._interpolate_value(dict1, dict2, 0.5)
        assert result["x"] == 5
        assert result["y"] == 10
        assert result["name"] == "end"  # Step interpolation for strings (t >= 0.5)
    
    def test_keyframe_copying(self):
        """Test keyframe copying functionality."""
        keyframes = [
            Keyframe(1.0, {"opacity": 0.5, "nested": {"x": 10}}, InterpolationType.LINEAR),
            Keyframe(2.0, {"opacity": 1.0, "nested": {"x": 20}}, InterpolationType.BEZIER)
        ]
        
        copied = self.keyframe_system.copy_keyframes(keyframes)
        
        # Verify copies are independent
        assert len(copied) == 2
        assert copied[0].time == 1.0
        assert copied[0].properties["opacity"] == 0.5
        
        # Modify original and verify copy is unchanged
        keyframes[0].properties["opacity"] = 0.8
        keyframes[0].properties["nested"]["x"] = 15
        
        assert copied[0].properties["opacity"] == 0.5
        assert copied[0].properties["nested"]["x"] == 10
    
    def test_keyframe_offset(self):
        """Test keyframe time offset."""
        keyframes = [
            Keyframe(1.0, {"opacity": 0.5}, InterpolationType.LINEAR),
            Keyframe(2.0, {"opacity": 1.0}, InterpolationType.LINEAR)
        ]
        
        offset_keyframes = self.keyframe_system.offset_keyframes(keyframes, 3.0)
        
        assert len(offset_keyframes) == 2
        assert offset_keyframes[0].time == 4.0
        assert offset_keyframes[1].time == 5.0
        assert offset_keyframes[0].properties["opacity"] == 0.5
        
        # Test negative offset (should clamp to 0)
        offset_keyframes = self.keyframe_system.offset_keyframes(keyframes, -2.0)
        assert offset_keyframes[0].time == 0.0
        assert offset_keyframes[1].time == 0.0
    
    def test_keyframe_scaling(self):
        """Test keyframe time scaling."""
        keyframes = [
            Keyframe(2.0, {"opacity": 0.5}, InterpolationType.LINEAR),
            Keyframe(4.0, {"opacity": 1.0}, InterpolationType.LINEAR)
        ]
        
        # Scale by 2x around pivot 0
        scaled = self.keyframe_system.scale_keyframes(keyframes, 2.0, pivot_time=0.0)
        assert scaled[0].time == 4.0
        assert scaled[1].time == 8.0
        
        # Scale by 0.5x around pivot 2
        scaled = self.keyframe_system.scale_keyframes(keyframes, 0.5, pivot_time=2.0)
        assert scaled[0].time == 2.0  # (2-2)*0.5 + 2 = 2
        assert scaled[1].time == 3.0  # (4-2)*0.5 + 2 = 3
        
        # Test invalid scale
        with pytest.raises(ValueError, match="Time scale must be positive"):
            self.keyframe_system.scale_keyframes(keyframes, -1.0)
    
    def test_keyframe_range_finding(self):
        """Test finding keyframes in time range."""
        keyframes = [
            Keyframe(1.0, {"opacity": 0.0}, InterpolationType.LINEAR),
            Keyframe(3.0, {"opacity": 0.5}, InterpolationType.LINEAR),
            Keyframe(5.0, {"opacity": 1.0}, InterpolationType.LINEAR),
            Keyframe(7.0, {"opacity": 0.5}, InterpolationType.LINEAR)
        ]
        
        # Find keyframes in range
        in_range = self.keyframe_system.find_keyframes_in_range(keyframes, 2.0, 6.0)
        assert len(in_range) == 2
        assert in_range[0].time == 3.0
        assert in_range[1].time == 5.0
        
        # Test reversed range (should still work)
        in_range = self.keyframe_system.find_keyframes_in_range(keyframes, 6.0, 2.0)
        assert len(in_range) == 2
    
    def test_keyframe_bounds(self):
        """Test getting keyframe time bounds."""
        keyframes = [
            Keyframe(3.0, {"opacity": 0.5}, InterpolationType.LINEAR),
            Keyframe(1.0, {"opacity": 0.0}, InterpolationType.LINEAR),
            Keyframe(5.0, {"opacity": 1.0}, InterpolationType.LINEAR)
        ]
        
        min_time, max_time = self.keyframe_system.get_keyframe_bounds(keyframes)
        assert min_time == 1.0
        assert max_time == 5.0
        
        # Test empty list
        min_time, max_time = self.keyframe_system.get_keyframe_bounds([])
        assert min_time == 0.0
        assert max_time == 0.0
    
    def test_keyframe_sorting(self):
        """Test keyframe sorting by time."""
        keyframes = [
            Keyframe(5.0, {"opacity": 1.0}, InterpolationType.LINEAR),
            Keyframe(1.0, {"opacity": 0.0}, InterpolationType.LINEAR),
            Keyframe(3.0, {"opacity": 0.5}, InterpolationType.LINEAR)
        ]
        
        sorted_kfs = self.keyframe_system.sort_keyframes(keyframes)
        times = [kf.time for kf in sorted_kfs]
        assert times == [1.0, 3.0, 5.0]
    
    def test_duplicate_removal(self):
        """Test removing duplicate keyframes."""
        keyframes = [
            Keyframe(1.0, {"opacity": 0.0}, InterpolationType.LINEAR),
            Keyframe(1.001, {"opacity": 0.1}, InterpolationType.LINEAR),  # Close duplicate
            Keyframe(3.0, {"opacity": 0.5}, InterpolationType.LINEAR),
            Keyframe(3.0, {"opacity": 0.6}, InterpolationType.LINEAR),    # Exact duplicate
            Keyframe(5.0, {"opacity": 1.0}, InterpolationType.LINEAR)
        ]
        
        unique_kfs = self.keyframe_system.remove_duplicate_keyframes(keyframes, tolerance=0.01)
        
        # Should have 3 unique keyframes
        assert len(unique_kfs) == 3
        times = [kf.time for kf in unique_kfs]
        assert times == [1.001, 3.0, 5.0]  # Should keep later keyframes
        
        # Check that later values are preserved
        assert unique_kfs[0].properties["opacity"] == 0.1
        assert unique_kfs[1].properties["opacity"] == 0.6