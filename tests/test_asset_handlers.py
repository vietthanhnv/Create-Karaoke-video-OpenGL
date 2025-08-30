"""
Tests for video and audio asset handlers.
"""

import os
import tempfile
import pytest
from pathlib import Path

from src.video.asset_handler import VideoAssetHandler
from src.audio.asset_handler import AudioAssetHandler
from src.core.models import VideoAsset, AudioAsset, ValidationResult


class TestVideoAssetHandler:
    """Test cases for VideoAssetHandler."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.handler = VideoAssetHandler()
    
    def test_supported_formats(self):
        """Test that supported formats are correctly defined."""
        formats = self.handler.get_supported_formats()
        
        assert '.mp4' in formats
        assert '.mov' in formats
        assert '.avi' in formats
        assert '.mkv' in formats
        
        assert formats['.mp4'] == 'video/mp4'
        assert formats['.mov'] == 'video/quicktime'
    
    def test_validate_nonexistent_file(self):
        """Test validation of non-existent file."""
        result = self.handler.validate_video_file('/nonexistent/file.mp4')
        
        assert not result.is_valid
        assert 'does not exist' in result.error_message
    
    def test_validate_unsupported_format(self):
        """Test validation of unsupported format."""
        # Create a temporary file with unsupported extension
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(b'dummy content')
        
        try:
            result = self.handler.validate_video_file(tmp_path)
            assert not result.is_valid
            assert 'Unsupported video format' in result.error_message
        finally:
            os.unlink(tmp_path)
    
    def test_validate_empty_file(self):
        """Test validation of empty file."""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            # File is empty by default
        
        try:
            result = self.handler.validate_video_file(tmp_path)
            assert not result.is_valid
            assert 'empty' in result.error_message
        finally:
            os.unlink(tmp_path)
    
    def test_basic_file_info_extraction(self):
        """Test basic file info extraction when FFprobe is not available."""
        # Create a dummy MP4 file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(b'dummy video content')
        
        try:
            # Test basic file info extraction
            info = self.handler._get_basic_file_info(tmp_path)
            
            assert 'file_size' in info
            assert info['file_size'] > 0
            assert info['container'] == 'mp4'
            assert info['codec'] == 'h264'  # Default for MP4
            assert info['fps'] == 30.0  # Default FPS
            assert info['resolution'] == (1920, 1080)  # Default resolution
        finally:
            os.unlink(tmp_path)
    
    def test_create_video_asset_with_dummy_file(self):
        """Test creating video asset with a dummy file."""
        # Create a dummy MP4 file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(b'dummy video content')
        
        try:
            # This should work even without FFprobe
            video_asset = self.handler.create_video_asset(tmp_path)
            
            assert isinstance(video_asset, VideoAsset)
            assert video_asset.path == os.path.abspath(tmp_path)
            assert video_asset.fps > 0
            assert video_asset.resolution[0] > 0
            assert video_asset.resolution[1] > 0
        finally:
            os.unlink(tmp_path)
    
    def test_create_video_asset_nonexistent_file(self):
        """Test creating video asset with non-existent file."""
        with pytest.raises(FileNotFoundError):
            self.handler.create_video_asset('/nonexistent/file.mp4')
    
    def test_create_video_asset_unsupported_format(self):
        """Test creating video asset with unsupported format."""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(b'dummy content')
        
        try:
            with pytest.raises(ValueError, match='Unsupported video format'):
                self.handler.create_video_asset(tmp_path)
        finally:
            os.unlink(tmp_path)
    
    def test_ffmpeg_availability_check(self):
        """Test FFmpeg availability checking."""
        # This will return False in most test environments
        ffmpeg_available = self.handler.is_ffmpeg_available()
        ffprobe_available = self.handler.is_ffprobe_available()
        
        # These should be boolean values
        assert isinstance(ffmpeg_available, bool)
        assert isinstance(ffprobe_available, bool)
    
    def test_video_info_summary(self):
        """Test video info summary generation."""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(b'dummy video content')
        
        try:
            summary = self.handler.get_video_info_summary(tmp_path)
            
            assert 'duration' in summary
            assert 'resolution' in summary
            assert 'fps' in summary
            assert 'codec' in summary
            assert 'file_size' in summary
            assert 'container' in summary
        finally:
            os.unlink(tmp_path)


class TestAudioAssetHandler:
    """Test cases for AudioAssetHandler."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.handler = AudioAssetHandler()
    
    def test_supported_formats(self):
        """Test that supported formats are correctly defined."""
        formats = self.handler.get_supported_formats()
        
        assert '.mp3' in formats
        assert '.wav' in formats
        assert '.aac' in formats
        assert '.flac' in formats
        assert '.ogg' in formats
        
        assert formats['.mp3'] == 'audio/mpeg'
        assert formats['.wav'] == 'audio/wav'
    
    def test_validate_nonexistent_file(self):
        """Test validation of non-existent file."""
        result = self.handler.validate_audio_file('/nonexistent/file.mp3')
        
        assert not result.is_valid
        assert 'does not exist' in result.error_message
    
    def test_validate_unsupported_format(self):
        """Test validation of unsupported format."""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(b'dummy content')
        
        try:
            result = self.handler.validate_audio_file(tmp_path)
            assert not result.is_valid
            assert 'Unsupported audio format' in result.error_message
        finally:
            os.unlink(tmp_path)
    
    def test_validate_empty_file(self):
        """Test validation of empty file."""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            # File is empty by default
        
        try:
            result = self.handler.validate_audio_file(tmp_path)
            assert not result.is_valid
            assert 'empty' in result.error_message
        finally:
            os.unlink(tmp_path)
    
    def test_basic_file_info_extraction(self):
        """Test basic file info extraction when FFprobe is not available."""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(b'dummy audio content')
        
        try:
            info = self.handler._get_basic_file_info(tmp_path)
            
            assert 'file_size' in info
            assert info['file_size'] > 0
            assert info['container'] == 'mp3'
            assert info['codec'] == 'mp3'  # Default for MP3
            assert info['sample_rate'] == 44100  # Default sample rate
            assert info['channels'] == 2  # Default channels
        finally:
            os.unlink(tmp_path)
    
    def test_create_audio_asset_with_dummy_file(self):
        """Test creating audio asset with a dummy file."""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(b'dummy audio content')
        
        try:
            audio_asset = self.handler.create_audio_asset(tmp_path)
            
            assert isinstance(audio_asset, AudioAsset)
            assert audio_asset.path == os.path.abspath(tmp_path)
            assert audio_asset.sample_rate > 0
            assert audio_asset.channels > 0
        finally:
            os.unlink(tmp_path)
    
    def test_create_audio_asset_nonexistent_file(self):
        """Test creating audio asset with non-existent file."""
        with pytest.raises(FileNotFoundError):
            self.handler.create_audio_asset('/nonexistent/file.mp3')
    
    def test_create_audio_asset_unsupported_format(self):
        """Test creating audio asset with unsupported format."""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(b'dummy content')
        
        try:
            with pytest.raises(ValueError, match='Unsupported audio format'):
                self.handler.create_audio_asset(tmp_path)
        finally:
            os.unlink(tmp_path)
    
    def test_ffmpeg_availability_check(self):
        """Test FFmpeg availability checking."""
        ffmpeg_available = self.handler.is_ffmpeg_available()
        ffprobe_available = self.handler.is_ffprobe_available()
        
        assert isinstance(ffmpeg_available, bool)
        assert isinstance(ffprobe_available, bool)
    
    def test_audio_info_summary(self):
        """Test audio info summary generation."""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(b'dummy audio content')
        
        try:
            summary = self.handler.get_audio_info_summary(tmp_path)
            
            assert 'duration' in summary
            assert 'sample_rate' in summary
            assert 'channels' in summary
            assert 'codec' in summary
            assert 'file_size' in summary
            assert 'bit_rate' in summary
            assert 'container' in summary
        finally:
            os.unlink(tmp_path)


class TestAssetHandlerIntegration:
    """Integration tests for asset handlers with project manager."""
    
    def test_project_manager_video_import(self):
        """Test video import through project manager."""
        from src.core.project_manager import ProjectManager
        
        manager = ProjectManager()
        
        # Create a dummy video file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(b'dummy video content')
        
        try:
            video_asset = manager.import_video(tmp_path)
            
            assert isinstance(video_asset, VideoAsset)
            assert video_asset.path == os.path.abspath(tmp_path)
            assert video_asset.fps > 0
            assert video_asset.resolution[0] > 0
            assert video_asset.resolution[1] > 0
        finally:
            os.unlink(tmp_path)
    
    def test_project_manager_audio_import(self):
        """Test audio import through project manager."""
        from src.core.project_manager import ProjectManager
        
        manager = ProjectManager()
        
        # Create a dummy audio file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(b'dummy audio content')
        
        try:
            audio_asset = manager.import_audio(tmp_path)
            
            assert isinstance(audio_asset, AudioAsset)
            assert audio_asset.path == os.path.abspath(tmp_path)
            assert audio_asset.sample_rate > 0
            assert audio_asset.channels > 0
        finally:
            os.unlink(tmp_path)
    
    def test_project_creation_with_video(self):
        """Test creating a project with video asset."""
        from src.core.project_manager import ProjectManager
        
        manager = ProjectManager()
        
        # Create a dummy video file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(b'dummy video content')
        
        try:
            project = manager.create_project(tmp_path, "Test Project")
            
            assert project.name == "Test Project"
            assert project.video_asset.path == os.path.abspath(tmp_path)
            assert len(project.subtitle_tracks) == 0  # No tracks by default
            assert project.export_settings is not None
        finally:
            os.unlink(tmp_path)


if __name__ == '__main__':
    pytest.main([__file__])