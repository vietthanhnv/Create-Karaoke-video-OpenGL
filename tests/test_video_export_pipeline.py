"""
Tests for video export pipeline functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path
import threading
import time
from datetime import datetime

from src.video.export_pipeline import (
    VideoExportPipeline, QualityPreset, ExportStatus, ExportProgress,
    ExportJob, BatchExportProgress, QueueStatus
)
from src.core.models import (
    Project, VideoAsset, ExportSettings, SubtitleTrack, TextElement,
    AnimationType, EasingType
)


class TestQualityPreset(unittest.TestCase):
    """Test quality preset functionality."""
    
    def test_get_preset_valid(self):
        """Test getting valid quality presets."""
        draft = QualityPreset.get_preset('draft')
        self.assertIsInstance(draft, dict)
        self.assertEqual(draft['name'], 'Draft Quality')
        self.assertEqual(draft['video_codec'], 'libx264')
        
        normal = QualityPreset.get_preset('normal')
        self.assertEqual(normal['name'], 'Normal Quality')
        
        high = QualityPreset.get_preset('high')
        self.assertEqual(high['name'], 'High Quality')
    
    def test_get_preset_invalid(self):
        """Test getting invalid preset returns normal."""
        invalid = QualityPreset.get_preset('invalid')
        normal = QualityPreset.get_preset('normal')
        self.assertEqual(invalid, normal)
    
    def test_get_available_presets(self):
        """Test getting list of available presets."""
        presets = QualityPreset.get_available_presets()
        self.assertIn('draft', presets)
        self.assertIn('normal', presets)
        self.assertIn('high', presets)
        self.assertIn('custom', presets)


class TestExportProgress(unittest.TestCase):
    """Test export progress tracking."""
    
    def test_progress_percentage(self):
        """Test progress percentage calculation."""
        progress = ExportProgress(
            status=ExportStatus.RENDERING,
            current_frame=25,
            total_frames=100,
            elapsed_time=10.0
        )
        self.assertEqual(progress.progress_percentage, 25.0)
        
        # Test edge cases
        progress.current_frame = 0
        self.assertEqual(progress.progress_percentage, 0.0)
        
        progress.current_frame = 100
        self.assertEqual(progress.progress_percentage, 100.0)
        
        progress.current_frame = 150  # Over 100%
        self.assertEqual(progress.progress_percentage, 100.0)
        
        progress.total_frames = 0  # Division by zero
        self.assertEqual(progress.progress_percentage, 0.0)


class TestVideoExportPipeline(unittest.TestCase):
    """Test video export pipeline functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.pipeline = VideoExportPipeline()
        
        # Create test project
        self.video_asset = VideoAsset(
            path="test_video.mp4",
            duration=10.0,
            fps=30.0,
            resolution=(1920, 1080),
            codec="h264"
        )
        
        self.export_settings = ExportSettings(
            resolution=(1920, 1080),
            fps=30.0,
            format="mp4",
            quality_preset="normal",
            codec="libx264"
        )
        
        self.project = Project(
            name="Test Project",
            video_asset=self.video_asset,
            audio_asset=None,
            subtitle_tracks=[],
            export_settings=self.export_settings,
            created_at=datetime.now(),
            modified_at=datetime.now()
        )
    
    def test_initialization(self):
        """Test pipeline initialization."""
        self.assertIsInstance(self.pipeline.supported_formats, dict)
        self.assertIn('mp4', self.pipeline.supported_formats)
        self.assertIn('mov', self.pipeline.supported_formats)
        self.assertIn('avi', self.pipeline.supported_formats)
    
    def test_validate_export_settings_valid(self):
        """Test validation of valid export settings."""
        with patch.object(self.pipeline, '_ffmpeg_available', True):
            result = self.pipeline.validate_export_settings(self.export_settings)
            self.assertTrue(result.is_valid)
    
    def test_validate_export_settings_no_ffmpeg(self):
        """Test validation when FFmpeg is not available."""
        with patch.object(self.pipeline, '_ffmpeg_available', False):
            result = self.pipeline.validate_export_settings(self.export_settings)
            self.assertFalse(result.is_valid)
            self.assertIn("FFmpeg is not available", result.error_message)
    
    def test_validate_export_settings_invalid_format(self):
        """Test validation with invalid format."""
        self.export_settings.format = "invalid"
        with patch.object(self.pipeline, '_ffmpeg_available', True):
            result = self.pipeline.validate_export_settings(self.export_settings)
            self.assertFalse(result.is_valid)
            self.assertIn("Unsupported output format", result.error_message)
    
    def test_validate_export_settings_invalid_codec(self):
        """Test validation with invalid codec."""
        self.export_settings.codec = "invalid_codec"
        with patch.object(self.pipeline, '_ffmpeg_available', True):
            result = self.pipeline.validate_export_settings(self.export_settings)
            self.assertFalse(result.is_valid)
            self.assertIn("not supported for mp4", result.error_message)
    
    def test_validate_export_settings_odd_resolution(self):
        """Test validation with odd resolution dimensions."""
        self.export_settings.resolution = (1921, 1081)  # Odd numbers
        with patch.object(self.pipeline, '_ffmpeg_available', True):
            result = self.pipeline.validate_export_settings(self.export_settings)
            self.assertFalse(result.is_valid)
            self.assertIn("even numbers", result.error_message)
    
    def test_validate_export_settings_low_resolution(self):
        """Test validation with too low resolution."""
        self.export_settings.resolution = (100, 100)
        with patch.object(self.pipeline, '_ffmpeg_available', True):
            result = self.pipeline.validate_export_settings(self.export_settings)
            self.assertFalse(result.is_valid)
            self.assertIn("Minimum resolution", result.error_message)
    
    def test_validate_export_settings_high_resolution_warning(self):
        """Test validation with very high resolution generates warning."""
        self.export_settings.resolution = (7682, 4322)  # Greater than 8K, even numbers
        with patch.object(self.pipeline, '_ffmpeg_available', True):
            result = self.pipeline.validate_export_settings(self.export_settings)
            self.assertTrue(result.is_valid)
            self.assertTrue(any("performance issues" in warning for warning in result.warnings))
    
    def test_validate_export_settings_invalid_fps(self):
        """Test validation with invalid frame rate."""
        self.export_settings.fps = 0
        with patch.object(self.pipeline, '_ffmpeg_available', True):
            result = self.pipeline.validate_export_settings(self.export_settings)
            self.assertFalse(result.is_valid)
            self.assertIn("at least 1 FPS", result.error_message)
    
    def test_validate_export_settings_high_fps_warning(self):
        """Test validation with very high FPS generates warning."""
        self.export_settings.fps = 240
        with patch.object(self.pipeline, '_ffmpeg_available', True):
            result = self.pipeline.validate_export_settings(self.export_settings)
            self.assertTrue(result.is_valid)
            self.assertTrue(any("120 FPS" in warning for warning in result.warnings))
    
    def test_get_supported_formats(self):
        """Test getting supported formats."""
        formats = self.pipeline.get_supported_formats()
        self.assertIsInstance(formats, dict)
        self.assertIn('mp4', formats)
        self.assertIn('container', formats['mp4'])
        self.assertIn('video_codecs', formats['mp4'])
        self.assertIn('audio_codecs', formats['mp4'])
    
    def test_get_available_codecs_valid_format(self):
        """Test getting codecs for valid format."""
        codecs = self.pipeline.get_available_codecs('mp4')
        self.assertIn('video_codecs', codecs)
        self.assertIn('audio_codecs', codecs)
        self.assertIn('libx264', codecs['video_codecs'])
        self.assertIn('aac', codecs['audio_codecs'])
    
    def test_get_available_codecs_invalid_format(self):
        """Test getting codecs for invalid format."""
        codecs = self.pipeline.get_available_codecs('invalid')
        self.assertEqual(codecs['video_codecs'], [])
        self.assertEqual(codecs['audio_codecs'], [])
    
    def test_estimate_file_size_with_bitrate(self):
        """Test file size estimation with explicit bitrate."""
        self.export_settings.bitrate = 5000000  # 5 Mbps
        size = self.pipeline.estimate_file_size(self.project)
        
        # Expected: (5Mbps * 10s) / 8 = ~6.25MB
        expected_size = (5000000 * 10) // 8
        self.assertAlmostEqual(size, expected_size, delta=1000000)  # Within 1MB
    
    def test_estimate_file_size_with_preset(self):
        """Test file size estimation using preset bitrate."""
        size = self.pipeline.estimate_file_size(self.project)
        self.assertIsInstance(size, int)
        self.assertGreater(size, 0)
    
    def test_estimate_file_size_error_handling(self):
        """Test file size estimation error handling."""
        # Create invalid project with invalid duration that will cause exception
        invalid_project = Project(
            name="Invalid",
            video_asset=VideoAsset("", float('nan'), 0, (0, 0), ""),  # NaN duration will cause error
            audio_asset=None,
            subtitle_tracks=[],
            export_settings=ExportSettings((0, 0), 0, "", "", ""),
            created_at=datetime.now(),
            modified_at=datetime.now()
        )
        
        size = self.pipeline.estimate_file_size(invalid_project)
        self.assertIsNone(size)
    
    @patch('subprocess.run')
    def test_check_ffmpeg_availability_success(self, mock_run):
        """Test FFmpeg availability check when available."""
        mock_run.return_value.returncode = 0
        pipeline = VideoExportPipeline()
        self.assertTrue(pipeline._ffmpeg_available)
    
    @patch('subprocess.run')
    def test_check_ffmpeg_availability_failure(self, mock_run):
        """Test FFmpeg availability check when not available."""
        mock_run.side_effect = FileNotFoundError()
        pipeline = VideoExportPipeline()
        self.assertFalse(pipeline._ffmpeg_available)
    
    def test_build_ffmpeg_command_basic(self):
        """Test building basic FFmpeg command."""
        frames_dir = Path("/tmp/frames")
        output_path = "/tmp/output.mp4"
        preset_config = QualityPreset.get_preset('normal')
        
        cmd = self.pipeline._build_ffmpeg_command(
            frames_dir, output_path, self.export_settings, preset_config
        )
        
        self.assertIn('ffmpeg', cmd)
        self.assertIn('-y', cmd)
        self.assertIn('-framerate', cmd)
        self.assertIn('30.0', cmd)
        self.assertIn('-c:v', cmd)
        self.assertIn('libx264', cmd)
        self.assertIn('/tmp/output.mp4', cmd)
    
    def test_build_ffmpeg_command_with_audio(self):
        """Test building FFmpeg command with audio source."""
        frames_dir = Path("/tmp/frames")
        output_path = "/tmp/output.mp4"
        preset_config = QualityPreset.get_preset('normal')
        
        with patch('os.path.exists', return_value=True):
            cmd = self.pipeline._build_ffmpeg_command(
                frames_dir, output_path, self.export_settings, 
                preset_config, "/tmp/audio.mp3"
            )
        
        self.assertIn('-c:a', cmd)
        self.assertIn('aac', cmd)
    
    def test_build_ffmpeg_command_no_audio(self):
        """Test building FFmpeg command without audio."""
        frames_dir = Path("/tmp/frames")
        output_path = "/tmp/output.mp4"
        preset_config = QualityPreset.get_preset('normal')
        
        cmd = self.pipeline._build_ffmpeg_command(
            frames_dir, output_path, self.export_settings, preset_config
        )
        
        self.assertIn('-an', cmd)  # No audio flag
    
    def test_cancel_export(self):
        """Test export cancellation."""
        self.assertFalse(self.pipeline._cancel_requested)
        self.pipeline.cancel_export()
        self.assertTrue(self.pipeline._cancel_requested)
    
    def test_is_exporting_false(self):
        """Test is_exporting when not exporting."""
        self.assertFalse(self.pipeline.is_exporting())
    
    @patch('src.video.export_pipeline.VideoExportPipeline._render_single_frame')
    def test_render_single_frame_success(self, mock_render):
        """Test successful single frame rendering."""
        mock_render.return_value = True
        
        result = self.pipeline._render_single_frame(
            self.project, 1.0, Path("/tmp/frame.png"), (1920, 1080)
        )
        self.assertTrue(result)
    
    @patch('src.video.export_pipeline.VideoExportPipeline._render_single_frame')
    def test_render_single_frame_failure(self, mock_render):
        """Test failed single frame rendering."""
        mock_render.return_value = False
        
        result = self.pipeline._render_single_frame(
            self.project, 1.0, Path("/tmp/frame.png"), (1920, 1080)
        )
        self.assertFalse(result)


class TestVideoExportIntegration(unittest.TestCase):
    """Integration tests for video export pipeline."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.pipeline = VideoExportPipeline()
        
        # Create minimal test project
        self.video_asset = VideoAsset(
            path="test_video.mp4",
            duration=1.0,  # Short duration for testing
            fps=30.0,
            resolution=(640, 480),  # Small resolution for testing
            codec="h264"
        )
        
        self.export_settings = ExportSettings(
            resolution=(640, 480),
            fps=30.0,
            format="mp4",
            quality_preset="draft",  # Fast preset for testing
            codec="libx264"
        )
        
        # Create test subtitle track
        text_element = TextElement(
            content="Test subtitle",
            font_family="Arial",
            font_size=24.0,
            color=(1.0, 1.0, 1.0, 1.0),
            position=(320.0, 240.0),
            rotation=(0.0, 0.0, 0.0),
            effects=[]
        )
        
        subtitle_track = SubtitleTrack(
            id="track1",
            elements=[text_element],
            keyframes=[],
            start_time=0.0,
            end_time=1.0
        )
        
        self.project = Project(
            name="Integration Test Project",
            video_asset=self.video_asset,
            audio_asset=None,
            subtitle_tracks=[subtitle_track],
            export_settings=self.export_settings,
            created_at=datetime.now(),
            modified_at=datetime.now()
        )
    
    def test_export_validation_integration(self):
        """Test complete export validation process."""
        with patch.object(self.pipeline, '_ffmpeg_available', True):
            result = self.pipeline.validate_export_settings(self.export_settings)
            self.assertTrue(result.is_valid)
    
    def test_progress_callback_integration(self):
        """Test progress callback functionality."""
        progress_updates = []
        
        def progress_callback(progress):
            progress_updates.append(progress)
        
        # Test progress update mechanism
        test_progress = ExportProgress(
            status=ExportStatus.RENDERING,
            current_frame=10,
            total_frames=30,
            elapsed_time=5.0
        )
        
        self.pipeline._progress_callback = progress_callback
        self.pipeline._update_progress(test_progress)
        
        self.assertEqual(len(progress_updates), 1)
        self.assertEqual(progress_updates[0].current_frame, 10)
        self.assertEqual(progress_updates[0].total_frames, 30)


class TestBatchExport(unittest.TestCase):
    """Test batch export functionality."""
    
    def setUp(self):
        """Set up batch export test fixtures."""
        self.pipeline = VideoExportPipeline()
        
        # Create test projects
        self.projects = []
        for i in range(3):
            video_asset = VideoAsset(
                path=f"test_video_{i}.mp4",
                duration=2.0,
                fps=30.0,
                resolution=(640, 480),
                codec="h264"
            )
            
            export_settings = ExportSettings(
                resolution=(640, 480),
                fps=30.0,
                format="mp4",
                quality_preset="draft",
                codec="libx264"
            )
            
            project = Project(
                name=f"Test Project {i}",
                video_asset=video_asset,
                audio_asset=None,
                subtitle_tracks=[],
                export_settings=export_settings,
                created_at=datetime.now(),
                modified_at=datetime.now()
            )
            self.projects.append(project)
    
    def test_add_to_export_queue(self):
        """Test adding jobs to export queue."""
        job_id = self.pipeline.add_to_export_queue(
            self.projects[0], "/tmp/output1.mp4", priority=1
        )
        
        self.assertIsInstance(job_id, str)
        self.assertIn("job_", job_id)
        self.assertEqual(self.pipeline.get_queue_size(), 1)
    
    def test_add_multiple_jobs_with_priority(self):
        """Test adding multiple jobs with different priorities."""
        job_id1 = self.pipeline.add_to_export_queue(
            self.projects[0], "/tmp/output1.mp4", priority=2
        )
        job_id2 = self.pipeline.add_to_export_queue(
            self.projects[1], "/tmp/output2.mp4", priority=1
        )
        job_id3 = self.pipeline.add_to_export_queue(
            self.projects[2], "/tmp/output3.mp4", priority=3
        )
        
        self.assertEqual(self.pipeline.get_queue_size(), 3)
        self.assertNotEqual(job_id1, job_id2)
        self.assertNotEqual(job_id2, job_id3)
    
    def test_queue_status_management(self):
        """Test queue status management."""
        self.assertEqual(self.pipeline.get_queue_status(), QueueStatus.IDLE)
        
        # Add job and start batch export
        self.pipeline.add_to_export_queue(self.projects[0], "/tmp/output1.mp4")
        
        with patch.object(self.pipeline, '_ffmpeg_available', True):
            success = self.pipeline.start_batch_export()
            self.assertTrue(success)
            
            # Give it a moment to start
            time.sleep(0.1)
            
            # Test pause
            pause_success = self.pipeline.pause_batch_export()
            self.assertTrue(pause_success)
            self.assertEqual(self.pipeline.get_queue_status(), QueueStatus.PAUSED)
            
            # Test resume
            resume_success = self.pipeline.resume_batch_export()
            self.assertTrue(resume_success)
            self.assertEqual(self.pipeline.get_queue_status(), QueueStatus.RUNNING)
            
            # Test stop
            stop_success = self.pipeline.stop_batch_export()
            self.assertTrue(stop_success)
            self.assertEqual(self.pipeline.get_queue_status(), QueueStatus.STOPPED)
    
    def test_start_batch_export_empty_queue(self):
        """Test starting batch export with empty queue."""
        success = self.pipeline.start_batch_export()
        self.assertFalse(success)
    
    def test_start_batch_export_already_running(self):
        """Test starting batch export when already running."""
        self.pipeline.add_to_export_queue(self.projects[0], "/tmp/output1.mp4")
        self.pipeline._queue_status = QueueStatus.RUNNING
        
        success = self.pipeline.start_batch_export()
        self.assertFalse(success)
    
    def test_clear_queue(self):
        """Test clearing the export queue."""
        # Add multiple jobs
        for i, project in enumerate(self.projects):
            self.pipeline.add_to_export_queue(project, f"/tmp/output{i}.mp4")
        
        self.assertEqual(self.pipeline.get_queue_size(), 3)
        
        cleared_count = self.pipeline.clear_queue()
        self.assertEqual(cleared_count, 3)
        self.assertEqual(self.pipeline.get_queue_size(), 0)
    
    def test_remove_job_from_queue(self):
        """Test removing specific job from queue."""
        job_id1 = self.pipeline.add_to_export_queue(
            self.projects[0], "/tmp/output1.mp4"
        )
        job_id2 = self.pipeline.add_to_export_queue(
            self.projects[1], "/tmp/output2.mp4"
        )
        
        self.assertEqual(self.pipeline.get_queue_size(), 2)
        
        # Remove first job
        removed = self.pipeline.remove_job_from_queue(job_id1)
        self.assertTrue(removed)
        self.assertEqual(self.pipeline.get_queue_size(), 1)
        
        # Try to remove non-existent job
        removed = self.pipeline.remove_job_from_queue("non_existent")
        self.assertFalse(removed)
        self.assertEqual(self.pipeline.get_queue_size(), 1)
    
    def test_batch_progress_callback(self):
        """Test batch progress callback functionality."""
        progress_updates = []
        
        def batch_progress_callback(progress):
            progress_updates.append(progress)
        
        # Test batch progress update mechanism
        test_job = ExportJob(
            id="test_job",
            project=self.projects[0],
            output_path="/tmp/test.mp4"
        )
        
        batch_progress = BatchExportProgress(
            total_jobs=3,
            completed_jobs=1,
            current_job=test_job,
            queue_status=QueueStatus.RUNNING
        )
        
        self.pipeline._batch_progress_callback = batch_progress_callback
        self.pipeline._update_batch_progress(batch_progress)
        
        self.assertEqual(len(progress_updates), 1)
        self.assertEqual(progress_updates[0].total_jobs, 3)
        self.assertEqual(progress_updates[0].completed_jobs, 1)
        self.assertEqual(progress_updates[0].current_job.id, "test_job")
    
    def test_export_job_creation(self):
        """Test export job creation and properties."""
        job = ExportJob(
            id="test_job",
            project=self.projects[0],
            output_path="/tmp/test.mp4",
            priority=1
        )
        
        self.assertEqual(job.id, "test_job")
        self.assertEqual(job.project, self.projects[0])
        self.assertEqual(job.output_path, "/tmp/test.mp4")
        self.assertEqual(job.priority, 1)
        self.assertIsNotNone(job.progress)
        self.assertEqual(job.progress.status, ExportStatus.QUEUED)
    
    def test_batch_export_progress_calculations(self):
        """Test batch export progress calculations."""
        batch_progress = BatchExportProgress(
            total_jobs=5,
            completed_jobs=2,
            overall_start_time=datetime.now()
        )
        
        # Test overall progress percentage
        self.assertEqual(batch_progress.overall_progress_percentage, 40.0)
        
        # Test with zero jobs
        empty_batch = BatchExportProgress(total_jobs=0, completed_jobs=0)
        self.assertEqual(empty_batch.overall_progress_percentage, 0.0)
        
        # Test completion time estimation
        batch_progress.queue_status = QueueStatus.RUNNING
        completion_time = batch_progress.estimated_completion_time
        self.assertIsInstance(completion_time, datetime)
    
    @patch('src.video.export_pipeline.VideoExportPipeline._execute_single_export')
    def test_batch_export_worker_success(self, mock_execute):
        """Test batch export worker with successful jobs."""
        mock_execute.return_value = True
        
        # Add jobs to queue
        for i, project in enumerate(self.projects):
            self.pipeline.add_to_export_queue(project, f"/tmp/output{i}.mp4")
        
        # Mock the batch worker execution
        self.pipeline._batch_export_worker()
        
        # Verify all jobs were processed
        self.assertEqual(len(self.pipeline.get_completed_jobs()), 3)
        self.assertEqual(len(self.pipeline.get_failed_jobs()), 0)
        self.assertEqual(mock_execute.call_count, 3)
    
    @patch('src.video.export_pipeline.VideoExportPipeline._execute_single_export')
    def test_batch_export_worker_with_failures(self, mock_execute):
        """Test batch export worker with some failed jobs."""
        # First job succeeds, second fails, third succeeds
        mock_execute.side_effect = [True, False, True]
        
        # Add jobs to queue
        for i, project in enumerate(self.projects):
            self.pipeline.add_to_export_queue(project, f"/tmp/output{i}.mp4")
        
        # Mock the batch worker execution
        self.pipeline._batch_export_worker()
        
        # Verify job results
        self.assertEqual(len(self.pipeline.get_completed_jobs()), 2)
        self.assertEqual(len(self.pipeline.get_failed_jobs()), 1)
        self.assertEqual(mock_execute.call_count, 3)
    
    def test_pause_resume_functionality(self):
        """Test pause and resume functionality."""
        # Test pause when not running
        self.assertFalse(self.pipeline.pause_batch_export())
        
        # Test resume when not paused
        self.assertFalse(self.pipeline.resume_batch_export())
        
        # Set to running state
        self.pipeline._queue_status = QueueStatus.RUNNING
        
        # Test pause when running
        self.assertTrue(self.pipeline.pause_batch_export())
        self.assertEqual(self.pipeline.get_queue_status(), QueueStatus.PAUSED)
        
        # Test resume when paused
        self.assertTrue(self.pipeline.resume_batch_export())
        self.assertEqual(self.pipeline.get_queue_status(), QueueStatus.RUNNING)
    
    def test_stop_functionality(self):
        """Test stop functionality."""
        # Test stop when idle
        self.assertFalse(self.pipeline.stop_batch_export())
        
        # Set to running state
        self.pipeline._queue_status = QueueStatus.RUNNING
        
        # Test stop when running
        self.assertTrue(self.pipeline.stop_batch_export())
        self.assertEqual(self.pipeline.get_queue_status(), QueueStatus.STOPPED)


class TestExportProgress(unittest.TestCase):
    """Test export progress tracking functionality."""
    
    def test_export_progress_percentage(self):
        """Test progress percentage calculation."""
        progress = ExportProgress(
            status=ExportStatus.RENDERING,
            current_frame=25,
            total_frames=100,
            elapsed_time=10.0
        )
        
        self.assertEqual(progress.progress_percentage, 25.0)
        
        # Test with zero total frames
        progress_zero = ExportProgress(
            status=ExportStatus.RENDERING,
            current_frame=10,
            total_frames=0,
            elapsed_time=5.0
        )
        self.assertEqual(progress_zero.progress_percentage, 0.0)
        
        # Test with completion
        progress_complete = ExportProgress(
            status=ExportStatus.COMPLETED,
            current_frame=100,
            total_frames=100,
            elapsed_time=40.0
        )
        self.assertEqual(progress_complete.progress_percentage, 100.0)
    
    def test_eta_datetime_calculation(self):
        """Test ETA datetime calculation."""
        start_time = datetime.now()
        progress = ExportProgress(
            status=ExportStatus.RENDERING,
            current_frame=25,
            total_frames=100,
            elapsed_time=10.0,
            estimated_remaining=30.0,
            start_time=start_time
        )
        
        eta = progress.eta_datetime
        self.assertIsInstance(eta, datetime)
        self.assertGreater(eta, datetime.now())
        
        # Test without estimated remaining time
        progress_no_eta = ExportProgress(
            status=ExportStatus.RENDERING,
            current_frame=25,
            total_frames=100,
            elapsed_time=10.0,
            start_time=start_time
        )
        self.assertIsNone(progress_no_eta.eta_datetime)


if __name__ == '__main__':
    unittest.main()