"""
Tests for data models and validation system.
"""

import unittest
import tempfile
import os
import json
from datetime import datetime
from src.core.models import (
    TextElement, SubtitleTrack, Keyframe, VideoAsset, AudioAsset, Project,
    ExportSettings, AnimationType, VisualEffectType, ParticleType, EasingType,
    InterpolationType, AnimationEffect, VisualEffect, ParticleEffect, ColorEffect,
    ValidationResult, CapabilityReport
)
from src.core.validation import ValidationSystem

class TestValidationSystem(unittest.TestCase):
    """Test cases for ValidationSystem class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validation_system = ValidationSystem()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_temp_file(self, filename: str, content: str = "test content") -> str:
        """Create a temporary file for testing."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath
    
    def test_validate_video_file_supported_format(self):
        """Test validation of supported video formats."""
        # Create temporary video files
        mp4_file = self.create_temp_file("test.mp4")
        mov_file = self.create_temp_file("test.mov")
        avi_file = self.create_temp_file("test.avi")
        mkv_file = self.create_temp_file("test.mkv")
        
        # Test each supported format
        for video_file in [mp4_file, mov_file, avi_file, mkv_file]:
            result = self.validation_system.validate_video_file(video_file)
            self.assertTrue(result.is_valid, f"Should validate {video_file}")
            self.assertIsNone(result.error_message)
    
    def test_validate_video_file_unsupported_format(self):
        """Test validation of unsupported video formats."""
        unsupported_file = self.create_temp_file("test.wmv")
        
        result = self.validation_system.validate_video_file(unsupported_file)
        self.assertFalse(result.is_valid)
        self.assertIn("Unsupported video format", result.error_message)
    
    def test_validate_video_file_nonexistent(self):
        """Test validation of non-existent video file."""
        result = self.validation_system.validate_video_file("nonexistent.mp4")
        self.assertFalse(result.is_valid)
        self.assertIn("does not exist", result.error_message)
    
    def test_validate_audio_file_supported_format(self):
        """Test validation of supported audio formats."""
        # Create temporary audio files
        mp3_file = self.create_temp_file("test.mp3")
        wav_file = self.create_temp_file("test.wav")
        aac_file = self.create_temp_file("test.aac")
        flac_file = self.create_temp_file("test.flac")
        ogg_file = self.create_temp_file("test.ogg")
        
        # Test each supported format
        for audio_file in [mp3_file, wav_file, aac_file, flac_file, ogg_file]:
            result = self.validation_system.validate_audio_file(audio_file)
            self.assertTrue(result.is_valid, f"Should validate {audio_file}")
            self.assertIsNone(result.error_message)
    
    def test_validate_audio_file_unsupported_format(self):
        """Test validation of unsupported audio formats."""
        unsupported_file = self.create_temp_file("test.wma")
        
        result = self.validation_system.validate_audio_file(unsupported_file)
        self.assertFalse(result.is_valid)
        self.assertIn("Unsupported audio format", result.error_message)
    
    def test_validate_subtitle_file_supported_format(self):
        """Test validation of supported subtitle formats."""
        # Create temporary subtitle files
        srt_content = "1\n00:00:01,000 --> 00:00:05,000\nHello World\n"
        ass_content = "[Script Info]\nTitle: Test\n"
        vtt_content = "WEBVTT\n\n00:01.000 --> 00:05.000\nHello World\n"
        
        srt_file = self.create_temp_file("test.srt", srt_content)
        ass_file = self.create_temp_file("test.ass", ass_content)
        vtt_file = self.create_temp_file("test.vtt", vtt_content)
        
        # Test each supported format
        for subtitle_file in [srt_file, ass_file, vtt_file]:
            result = self.validation_system.validate_subtitle_file(subtitle_file)
            self.assertTrue(result.is_valid, f"Should validate {subtitle_file}")
            self.assertIsNone(result.error_message)
    
    def test_validate_subtitle_file_empty(self):
        """Test validation of empty subtitle file."""
        empty_file = self.create_temp_file("empty.srt", "")
        
        result = self.validation_system.validate_subtitle_file(empty_file)
        self.assertTrue(result.is_valid)  # Should still be valid but with warning
        self.assertIn("appears to be empty", str(result.warnings))
    
    def test_validate_opengl_capabilities(self):
        """Test OpenGL capability validation."""
        report = self.validation_system.validate_opengl_capabilities()
        
        self.assertIsInstance(report, CapabilityReport)
        self.assertIsInstance(report.opengl_version, str)
        self.assertIsInstance(report.glsl_version, str)
        self.assertIsInstance(report.max_texture_size, int)
        self.assertIsInstance(report.supports_vertex_arrays, bool)
        self.assertIsInstance(report.supports_framebuffers, bool)
    
    def test_validate_export_settings_valid(self):
        """Test validation of valid export settings."""
        settings = ExportSettings(
            resolution=(1920, 1080),
            fps=30.0,
            format="mp4",
            quality_preset="normal",
            codec="h264",
            bitrate=5000
        )
        
        result = self.validation_system.validate_export_settings(settings)
        self.assertTrue(result.is_valid)
        self.assertIsNone(result.error_message)
    
    def test_validate_export_settings_invalid_format(self):
        """Test validation of export settings with invalid format."""
        settings = ExportSettings(
            resolution=(1920, 1080),
            fps=30.0,
            format="invalid",
            quality_preset="normal",
            codec="h264"
        )
        
        result = self.validation_system.validate_export_settings(settings)
        self.assertFalse(result.is_valid)
        self.assertIn("Unsupported export format", result.error_message)
    
    def test_validate_export_settings_invalid_codec(self):
        """Test validation of export settings with invalid codec for format."""
        settings = ExportSettings(
            resolution=(1920, 1080),
            fps=30.0,
            format="mp4",
            quality_preset="normal",
            codec="invalid_codec"
        )
        
        result = self.validation_system.validate_export_settings(settings)
        self.assertFalse(result.is_valid)
        self.assertIn("not supported for format", result.error_message)
    
    def test_validate_export_settings_invalid_resolution(self):
        """Test validation of export settings with invalid resolution."""
        settings = ExportSettings(
            resolution=(0, 1080),
            fps=30.0,
            format="mp4",
            quality_preset="normal",
            codec="h264"
        )
        
        result = self.validation_system.validate_export_settings(settings)
        self.assertFalse(result.is_valid)
        self.assertIn("Invalid resolution", result.error_message)
    
    def test_validate_export_settings_odd_resolution_warning(self):
        """Test validation warning for odd resolution dimensions."""
        settings = ExportSettings(
            resolution=(1921, 1081),  # Odd dimensions
            fps=30.0,
            format="mp4",
            quality_preset="normal",
            codec="h264"
        )
        
        result = self.validation_system.validate_export_settings(settings)
        self.assertTrue(result.is_valid)
        self.assertIn("even numbers", str(result.warnings))
    
    def test_get_supported_formats(self):
        """Test getting supported file formats."""
        formats = self.validation_system.get_supported_formats()
        
        self.assertIn('video', formats)
        self.assertIn('audio', formats)
        self.assertIn('subtitle', formats)
        
        # Check that expected formats are present
        self.assertIn('.mp4', formats['video'])
        self.assertIn('.mp3', formats['audio'])
        self.assertIn('.srt', formats['subtitle'])
    
    def test_get_export_codec_compatibility(self):
        """Test getting export codec compatibility matrix."""
        compatibility = self.validation_system.get_export_codec_compatibility()
        
        self.assertIn('mp4', compatibility)
        self.assertIn('mov', compatibility)
        self.assertIn('avi', compatibility)
        
        # Check that expected codecs are present
        self.assertIn('h264', compatibility['mp4'])
    
    def test_check_opengl_minimum_requirements(self):
        """Test OpenGL minimum requirements validation."""
        result = self.validation_system.check_opengl_minimum_requirements()
        
        self.assertIsInstance(result, ValidationResult)
        # Should be valid since we're using simulated modern OpenGL
        self.assertTrue(result.is_valid)
        self.assertIn('capabilities', result.metadata)
    
    def test_validate_format_compatibility(self):
        """Test format compatibility validation."""
        # Test compatible formats
        result = self.validation_system.validate_format_compatibility('mp4', 'mp4')
        self.assertTrue(result.is_valid)
        
        # Test quality loss warning
        result = self.validation_system.validate_format_compatibility('mov', 'avi')
        self.assertTrue(result.is_valid)
        self.assertTrue(any('quality loss' in str(w) for w in result.warnings))
        
        # Test unsupported format
        result = self.validation_system.validate_format_compatibility('wmv', 'mp4')
        self.assertFalse(result.is_valid)
        self.assertIn('not supported', result.error_message)
    
    def test_validate_system_requirements(self):
        """Test comprehensive system requirements validation."""
        result = self.validation_system.validate_system_requirements()
        
        self.assertIsInstance(result, ValidationResult)
        # Should have metadata about system capabilities
        self.assertIn('opengl', result.metadata)
        self.assertIn('ffmpeg_available', result.metadata)


class TestDataModelValidation(unittest.TestCase):
    """Test cases for data model validation methods."""
    
    def test_text_element_validation_valid(self):
        """Test validation of valid TextElement."""
        element = TextElement(
            content="Hello World",
            font_family="Arial",
            font_size=24.0,
            color=(1.0, 1.0, 1.0, 1.0),
            position=(100.0, 200.0),
            rotation=(0.0, 0.0, 0.0),
            effects=[]
        )
        
        result = element.validate()
        self.assertTrue(result.is_valid)
        self.assertIsNone(result.error_message)
    
    def test_text_element_validation_empty_content(self):
        """Test validation of TextElement with empty content."""
        element = TextElement(
            content="",
            font_family="Arial",
            font_size=24.0,
            color=(1.0, 1.0, 1.0, 1.0),
            position=(100.0, 200.0),
            rotation=(0.0, 0.0, 0.0),
            effects=[]
        )
        
        result = element.validate()
        self.assertFalse(result.is_valid)
        self.assertIn("cannot be empty", result.error_message)
    
    def test_text_element_validation_invalid_color(self):
        """Test validation of TextElement with invalid color values."""
        element = TextElement(
            content="Hello",
            font_family="Arial",
            font_size=24.0,
            color=(2.0, 1.0, 1.0, 1.0),  # Invalid: >1.0
            position=(100.0, 200.0),
            rotation=(0.0, 0.0, 0.0),
            effects=[]
        )
        
        result = element.validate()
        self.assertFalse(result.is_valid)
        self.assertIn("must be between 0 and 1", result.error_message)
    
    def test_keyframe_validation_valid(self):
        """Test validation of valid Keyframe."""
        keyframe = Keyframe(
            time=5.0,
            properties={"opacity": 1.0, "scale": 1.2},
            interpolation_type=InterpolationType.LINEAR
        )
        
        result = keyframe.validate()
        self.assertTrue(result.is_valid)
        self.assertIsNone(result.error_message)
    
    def test_keyframe_validation_negative_time(self):
        """Test validation of Keyframe with negative time."""
        keyframe = Keyframe(
            time=-1.0,
            properties={"opacity": 1.0},
            interpolation_type=InterpolationType.LINEAR
        )
        
        result = keyframe.validate()
        self.assertFalse(result.is_valid)
        self.assertIn("cannot be negative", result.error_message)
    
    def test_video_asset_validation_valid(self):
        """Test validation of valid VideoAsset."""
        # Create a temporary video file
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_file.close()
        
        try:
            asset = VideoAsset(
                path=temp_file.name,
                duration=120.0,
                fps=30.0,
                resolution=(1920, 1080),
                codec="h264"
            )
            
            result = asset.validate()
            self.assertTrue(result.is_valid)
            self.assertIsNone(result.error_message)
        finally:
            os.unlink(temp_file.name)
    
    def test_video_asset_validation_nonexistent_file(self):
        """Test validation of VideoAsset with non-existent file."""
        asset = VideoAsset(
            path="nonexistent.mp4",
            duration=120.0,
            fps=30.0,
            resolution=(1920, 1080),
            codec="h264"
        )
        
        result = asset.validate()
        self.assertFalse(result.is_valid)
        self.assertIn("does not exist", result.error_message)
    
    def test_export_settings_validation_valid(self):
        """Test validation of valid ExportSettings."""
        settings = ExportSettings(
            resolution=(1920, 1080),
            fps=30.0,
            format="mp4",
            quality_preset="normal",
            codec="h264",
            bitrate=5000
        )
        
        result = settings.validate()
        self.assertTrue(result.is_valid)
        self.assertIsNone(result.error_message)
    
    def test_export_settings_validation_invalid_fps(self):
        """Test validation of ExportSettings with invalid FPS."""
        settings = ExportSettings(
            resolution=(1920, 1080),
            fps=-1.0,
            format="mp4",
            quality_preset="normal",
            codec="h264"
        )
        
        result = settings.validate()
        self.assertFalse(result.is_valid)
        self.assertIn("must be positive", result.error_message)
    
    def test_project_validation_valid(self):
        """Test validation of valid Project."""
        # Create temporary video file
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_file.close()
        
        try:
            video_asset = VideoAsset(
                path=temp_file.name,
                duration=120.0,
                fps=30.0,
                resolution=(1920, 1080),
                codec="h264"
            )
            
            export_settings = ExportSettings(
                resolution=(1920, 1080),
                fps=30.0,
                format="mp4",
                quality_preset="normal",
                codec="h264"
            )
            
            project = Project(
                name="Test Project",
                video_asset=video_asset,
                audio_asset=None,
                subtitle_tracks=[],
                export_settings=export_settings,
                created_at=datetime.now(),
                modified_at=datetime.now()
            )
            
            result = project.validate()
            self.assertTrue(result.is_valid)
            # Should have warning about no subtitle tracks
            self.assertIn("no subtitle tracks", str(result.warnings))
        finally:
            os.unlink(temp_file.name)


class TestDataModelSerialization(unittest.TestCase):
    """Test cases for data model serialization/deserialization."""
    
    def test_text_element_serialization(self):
        """Test TextElement serialization and deserialization."""
        original = TextElement(
            content="Hello World",
            font_family="Arial",
            font_size=24.0,
            color=(1.0, 0.5, 0.0, 1.0),
            position=(100.0, 200.0),
            rotation=(0.0, 15.0, 0.0),
            effects=[]
        )
        
        # Serialize to dict
        data = original.to_dict()
        self.assertIsInstance(data, dict)
        self.assertEqual(data['content'], "Hello World")
        self.assertEqual(data['font_size'], 24.0)
        
        # Deserialize back
        restored = TextElement.from_dict(data)
        self.assertEqual(restored.content, original.content)
        self.assertEqual(restored.font_family, original.font_family)
        self.assertEqual(restored.color, original.color)
    
    def test_export_settings_serialization(self):
        """Test ExportSettings serialization and deserialization."""
        original = ExportSettings(
            resolution=(1920, 1080),
            fps=30.0,
            format="mp4",
            quality_preset="high",
            codec="h264",
            bitrate=8000
        )
        
        # Serialize to dict
        data = original.to_dict()
        self.assertIsInstance(data, dict)
        self.assertEqual(data['resolution'], [1920, 1080])
        self.assertEqual(data['fps'], 30.0)
        
        # Deserialize back
        restored = ExportSettings.from_dict(data)
        self.assertEqual(restored.resolution, original.resolution)
        self.assertEqual(restored.fps, original.fps)
        self.assertEqual(restored.format, original.format)
    
    def test_project_json_serialization(self):
        """Test Project JSON serialization and deserialization."""
        # Create temporary video file
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_file.close()
        
        try:
            video_asset = VideoAsset(
                path=temp_file.name,
                duration=120.0,
                fps=30.0,
                resolution=(1920, 1080),
                codec="h264"
            )
            
            export_settings = ExportSettings(
                resolution=(1920, 1080),
                fps=30.0,
                format="mp4",
                quality_preset="normal",
                codec="h264"
            )
            
            now = datetime.now()
            original = Project(
                name="Test Project",
                video_asset=video_asset,
                audio_asset=None,
                subtitle_tracks=[],
                export_settings=export_settings,
                created_at=now,
                modified_at=now
            )
            
            # Serialize to JSON
            json_str = original.to_json()
            self.assertIsInstance(json_str, str)
            
            # Verify it's valid JSON
            parsed = json.loads(json_str)
            self.assertEqual(parsed['name'], "Test Project")
            
            # Deserialize back
            restored = Project.from_json(json_str)
            self.assertEqual(restored.name, original.name)
            self.assertEqual(restored.video_asset.path, original.video_asset.path)
            self.assertEqual(restored.export_settings.format, original.export_settings.format)
        finally:
            os.unlink(temp_file.name)


if __name__ == '__main__':
    unittest.main()