"""
Video export pipeline with FFmpeg integration for karaoke subtitle creator.

This module provides comprehensive video export functionality including:
- HD/4K resolution support
- Multiple video format encoding (MP4, MOV, AVI)
- Quality presets and custom encoding parameters
- Progress tracking and error handling
"""

import os
import subprocess
import tempfile
import logging
from typing import Dict, Any, Optional, Callable, List, Tuple
from pathlib import Path
import json
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
import queue
from datetime import datetime, timedelta

from ..core.models import ExportSettings, Project, ValidationResult
from ..graphics.opengl_renderer import OpenGLRenderer
from PyQt6.QtCore import QObject, pyqtSignal


logger = logging.getLogger(__name__)


class ExportStatus(Enum):
    """Export operation status."""
    IDLE = "idle"
    QUEUED = "queued"
    PREPARING = "preparing"
    RENDERING = "rendering"
    ENCODING = "encoding"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class QueueStatus(Enum):
    """Export queue status."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


@dataclass
class ExportProgress:
    """Export progress information."""
    status: ExportStatus
    current_frame: int
    total_frames: int
    elapsed_time: float
    estimated_remaining: Optional[float] = None
    current_operation: str = ""
    error_message: Optional[str] = None
    start_time: Optional[datetime] = None
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress as percentage (0-100)."""
        if self.total_frames <= 0:
            return 0.0
        return min(100.0, (self.current_frame / self.total_frames) * 100.0)
    
    @property
    def eta_datetime(self) -> Optional[datetime]:
        """Calculate estimated completion time."""
        if self.estimated_remaining is not None and self.start_time is not None:
            return datetime.now() + timedelta(seconds=self.estimated_remaining)
        return None


@dataclass
class ExportJob:
    """Represents a single export job in the queue."""
    id: str
    project: Project
    output_path: str
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    progress: Optional[ExportProgress] = None
    
    def __post_init__(self):
        """Initialize progress if not provided."""
        if self.progress is None:
            total_frames = int(self.project.video_asset.duration * self.project.export_settings.fps)
            self.progress = ExportProgress(
                status=ExportStatus.QUEUED,
                current_frame=0,
                total_frames=total_frames,
                elapsed_time=0.0,
                start_time=datetime.now()
            )


@dataclass
class BatchExportProgress:
    """Progress information for batch export operations."""
    total_jobs: int
    completed_jobs: int
    current_job: Optional[ExportJob] = None
    queue_status: QueueStatus = QueueStatus.IDLE
    overall_start_time: Optional[datetime] = None
    
    @property
    def overall_progress_percentage(self) -> float:
        """Calculate overall batch progress as percentage (0-100)."""
        if self.total_jobs <= 0:
            return 0.0
        return min(100.0, (self.completed_jobs / self.total_jobs) * 100.0)
    
    @property
    def estimated_completion_time(self) -> Optional[datetime]:
        """Estimate when the entire batch will complete."""
        if (self.overall_start_time is None or 
            self.completed_jobs == 0 or 
            self.queue_status != QueueStatus.RUNNING):
            return None
        
        elapsed = (datetime.now() - self.overall_start_time).total_seconds()
        avg_time_per_job = elapsed / self.completed_jobs
        remaining_jobs = self.total_jobs - self.completed_jobs
        
        # Add current job progress if available
        if self.current_job and self.current_job.progress:
            current_job_remaining = 0
            if self.current_job.progress.estimated_remaining:
                current_job_remaining = self.current_job.progress.estimated_remaining
            
            estimated_remaining = (remaining_jobs - 1) * avg_time_per_job + current_job_remaining
        else:
            estimated_remaining = remaining_jobs * avg_time_per_job
        
        return datetime.now() + timedelta(seconds=estimated_remaining)


class QualityPreset:
    """Predefined quality presets for video export."""
    
    PRESETS = {
        'draft': {
            'name': 'Draft Quality',
            'description': 'Fast export for preview purposes',
            'video_codec': 'libx264',
            'video_bitrate': '2M',
            'audio_codec': 'aac',
            'audio_bitrate': '128k',
            'crf': 28,
            'preset': 'ultrafast',
            'profile': 'baseline'
        },
        'normal': {
            'name': 'Normal Quality',
            'description': 'Balanced quality and file size',
            'video_codec': 'libx264',
            'video_bitrate': '5M',
            'audio_codec': 'aac',
            'audio_bitrate': '192k',
            'crf': 23,
            'preset': 'medium',
            'profile': 'high'
        },
        'high': {
            'name': 'High Quality',
            'description': 'Maximum quality for final output',
            'video_codec': 'libx264',
            'video_bitrate': '10M',
            'audio_codec': 'aac',
            'audio_bitrate': '320k',
            'crf': 18,
            'preset': 'slow',
            'profile': 'high'
        },
        'custom': {
            'name': 'Custom Settings',
            'description': 'User-defined encoding parameters',
            'video_codec': 'libx264',
            'video_bitrate': '5M',
            'audio_codec': 'aac',
            'audio_bitrate': '192k',
            'crf': 23,
            'preset': 'medium',
            'profile': 'high'
        }
    }
    
    @classmethod
    def get_preset(cls, preset_name: str) -> Dict[str, Any]:
        """Get quality preset configuration."""
        return cls.PRESETS.get(preset_name.lower(), cls.PRESETS['normal']).copy()
    
    @classmethod
    def get_available_presets(cls) -> List[str]:
        """Get list of available preset names."""
        return list(cls.PRESETS.keys())


class VideoExportPipeline(QObject):
    """
    Complete video export pipeline with OpenGL rendering and FFmpeg encoding.
    
    Handles the entire export process from subtitle rendering to final video output.
    Supports both single exports and batch processing with queue management.
    """
    
    # Signals for UI integration
    progress_updated = pyqtSignal(dict)
    export_complete = pyqtSignal()
    export_error = pyqtSignal(str)
    
    def __init__(self, renderer: Optional[OpenGLRenderer] = None):
        """
        Initialize export pipeline.
        
        Args:
            renderer: OpenGL renderer instance for subtitle rendering
        """
        super().__init__()
        self.renderer = renderer
        self._ffmpeg_available = self._check_ffmpeg_availability()
        
        # Single export management
        self._export_thread: Optional[threading.Thread] = None
        self._cancel_requested = False
        self._progress_callback: Optional[Callable[[ExportProgress], None]] = None
        
        # Batch export management
        self._export_queue: queue.PriorityQueue = queue.PriorityQueue()
        self._batch_thread: Optional[threading.Thread] = None
        self._queue_status = QueueStatus.IDLE
        self._pause_requested = False
        self._stop_requested = False
        self._batch_progress_callback: Optional[Callable[[BatchExportProgress], None]] = None
        self._completed_jobs: List[ExportJob] = []
        self._failed_jobs: List[ExportJob] = []
        self._current_batch_job: Optional[ExportJob] = None
        self._job_counter = 0
        
        # Supported output formats
        self.supported_formats = {
            'mp4': {
                'container': 'mp4',
                'video_codecs': ['libx264', 'libx265', 'h264_nvenc'],
                'audio_codecs': ['aac', 'mp3'],
                'extension': '.mp4'
            },
            'mov': {
                'container': 'mov',
                'video_codecs': ['libx264', 'prores', 'dnxhd'],
                'audio_codecs': ['aac', 'pcm_s16le'],
                'extension': '.mov'
            },
            'avi': {
                'container': 'avi',
                'video_codecs': ['libx264', 'libxvid', 'huffyuv'],
                'audio_codecs': ['mp3', 'pcm_s16le'],
                'extension': '.avi'
            }
        }
        
        if not self._ffmpeg_available:
            logger.warning("FFmpeg not available - video export will be disabled")
    
    def export_project(self, project: Project, output_path: str, export_settings: dict):
        """
        Export project with given settings.
        
        Args:
            project: Project to export
            output_path: Output file path
            export_settings: Export configuration
        """
        try:
            # Emit progress updates
            self.progress_updated.emit({
                'progress': 0,
                'operation': 'Starting export...',
                'details': f'Exporting to {output_path}'
            })
            
            # Simulate export process for now
            import time
            for i in range(101):
                if i % 10 == 0:
                    self.progress_updated.emit({
                        'progress': i,
                        'operation': f'Processing frame {i}/100',
                        'frame_info': f'{i}/100',
                        'details': f'Rendering frame {i}'
                    })
                time.sleep(0.05)  # Simulate work
            
            self.export_complete.emit()
            
        except Exception as e:
            self.export_error.emit(str(e))
    
    def validate_export_settings(self, settings: ExportSettings) -> ValidationResult:
        """
        Validate export settings for compatibility and correctness.
        
        Args:
            settings: Export settings to validate
            
        Returns:
            ValidationResult with validation status and details
        """
        errors = []
        warnings = []
        
        # Basic validation from model
        model_validation = settings.validate()
        if not model_validation.is_valid:
            errors.append(model_validation.error_message)
        if model_validation.warnings:
            warnings.extend(model_validation.warnings)
        
        # Check FFmpeg availability
        if not self._ffmpeg_available:
            errors.append("FFmpeg is not available for video encoding")
        
        # Validate format support
        format_info = self.supported_formats.get(settings.format.lower())
        if not format_info:
            errors.append(f"Unsupported output format: {settings.format}")
        else:
            # Validate codec compatibility
            if settings.codec not in format_info['video_codecs']:
                available_codecs = ', '.join(format_info['video_codecs'])
                errors.append(f"Codec '{settings.codec}' not supported for {settings.format}. Available: {available_codecs}")
        
        # Validate resolution constraints
        width, height = settings.resolution
        
        # Check for even dimensions (required by most codecs)
        if width % 2 != 0 or height % 2 != 0:
            errors.append("Resolution dimensions must be even numbers")
        
        # Check resolution limits
        if width < 320 or height < 240:
            errors.append("Minimum resolution is 320x240")
        elif width > 7680 or height > 4320:
            warnings.append("Very high resolution (>8K) may cause performance issues")
        
        # Validate frame rate
        if settings.fps < 1:
            errors.append("Frame rate must be at least 1 FPS")
        elif settings.fps > 120:
            warnings.append("Very high frame rate (>120 FPS) may cause large file sizes")
        
        # Validate bitrate if specified
        if settings.bitrate is not None:
            if settings.bitrate < 100000:  # 100 kbps minimum
                warnings.append("Very low bitrate may result in poor quality")
            elif settings.bitrate > 100000000:  # 100 Mbps maximum
                warnings.append("Very high bitrate may result in large file sizes")
        
        # Check quality preset
        if settings.quality_preset not in QualityPreset.get_available_presets():
            available_presets = ', '.join(QualityPreset.get_available_presets())
            errors.append(f"Invalid quality preset. Available: {available_presets}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            error_message="; ".join(errors) if errors else None,
            warnings=warnings
        )
    
    def export_video(
        self,
        project: Project,
        output_path: str,
        progress_callback: Optional[Callable[[ExportProgress], None]] = None
    ) -> bool:
        """
        Export project to video file.
        
        Args:
            project: Project to export
            output_path: Path for output video file
            progress_callback: Optional callback for progress updates
            
        Returns:
            True if export successful, False otherwise
        """
        if not self._ffmpeg_available:
            logger.error("Cannot export video: FFmpeg not available")
            return False
        
        # Validate export settings
        validation = self.validate_export_settings(project.export_settings)
        if not validation.is_valid:
            logger.error(f"Invalid export settings: {validation.error_message}")
            return False
        
        # Store progress callback
        self._progress_callback = progress_callback
        self._cancel_requested = False
        
        # Start export in separate thread
        self._export_thread = threading.Thread(
            target=self._export_worker,
            args=(project, output_path),
            daemon=True
        )
        self._export_thread.start()
        
        return True
    
    def cancel_export(self) -> None:
        """Cancel ongoing export operation."""
        self._cancel_requested = True
        logger.info("Export cancellation requested")
    
    def is_exporting(self) -> bool:
        """Check if export is currently in progress."""
        return self._export_thread is not None and self._export_thread.is_alive()
    
    # Batch Export Methods
    
    def add_to_export_queue(
        self,
        project: Project,
        output_path: str,
        priority: int = 0
    ) -> str:
        """
        Add a project to the export queue.
        
        Args:
            project: Project to export
            output_path: Path for output video file
            priority: Export priority (lower numbers = higher priority)
            
        Returns:
            Job ID for tracking
        """
        job_id = f"job_{self._job_counter}_{int(time.time())}"
        self._job_counter += 1
        
        job = ExportJob(
            id=job_id,
            project=project,
            output_path=output_path,
            priority=priority
        )
        
        # Add to priority queue (priority, creation_time, counter, job)
        # Counter ensures unique ordering when priority and timestamp are equal
        self._export_queue.put((priority, job.created_at.timestamp(), self._job_counter, job))
        
        logger.info(f"Added job {job_id} to export queue with priority {priority}")
        return job_id
    
    def start_batch_export(
        self,
        progress_callback: Optional[Callable[[BatchExportProgress], None]] = None
    ) -> bool:
        """
        Start processing the export queue.
        
        Args:
            progress_callback: Optional callback for batch progress updates
            
        Returns:
            True if batch export started successfully, False otherwise
        """
        if self._queue_status == QueueStatus.RUNNING:
            logger.warning("Batch export already running")
            return False
        
        if self._export_queue.empty():
            logger.warning("No jobs in export queue")
            return False
        
        self._batch_progress_callback = progress_callback
        self._queue_status = QueueStatus.RUNNING
        self._stop_requested = False
        self._pause_requested = False
        
        # Start batch processing thread
        self._batch_thread = threading.Thread(
            target=self._batch_export_worker,
            daemon=True
        )
        self._batch_thread.start()
        
        logger.info("Started batch export processing")
        return True
    
    def pause_batch_export(self) -> bool:
        """
        Pause the batch export queue.
        
        Returns:
            True if pause was successful, False otherwise
        """
        if self._queue_status != QueueStatus.RUNNING:
            return False
        
        self._pause_requested = True
        self._queue_status = QueueStatus.PAUSED
        logger.info("Batch export pause requested")
        return True
    
    def resume_batch_export(self) -> bool:
        """
        Resume the paused batch export queue.
        
        Returns:
            True if resume was successful, False otherwise
        """
        if self._queue_status != QueueStatus.PAUSED:
            return False
        
        self._pause_requested = False
        self._queue_status = QueueStatus.RUNNING
        logger.info("Batch export resumed")
        return True
    
    def stop_batch_export(self) -> bool:
        """
        Stop the batch export queue completely.
        
        Returns:
            True if stop was successful, False otherwise
        """
        if self._queue_status == QueueStatus.IDLE:
            return False
        
        self._stop_requested = True
        self._queue_status = QueueStatus.STOPPED
        
        # Cancel current export if running
        if self.is_exporting():
            self.cancel_export()
        
        logger.info("Batch export stop requested")
        return True
    
    def get_queue_status(self) -> QueueStatus:
        """Get current queue status."""
        return self._queue_status
    
    def get_queue_size(self) -> int:
        """Get number of jobs remaining in queue."""
        return self._export_queue.qsize()
    
    def get_completed_jobs(self) -> List[ExportJob]:
        """Get list of completed jobs."""
        return self._completed_jobs.copy()
    
    def get_failed_jobs(self) -> List[ExportJob]:
        """Get list of failed jobs."""
        return self._failed_jobs.copy()
    
    def clear_queue(self) -> int:
        """
        Clear all jobs from the export queue.
        
        Returns:
            Number of jobs that were cleared
        """
        cleared_count = 0
        while not self._export_queue.empty():
            try:
                self._export_queue.get_nowait()
                cleared_count += 1
            except queue.Empty:
                break
        
        logger.info(f"Cleared {cleared_count} jobs from export queue")
        return cleared_count
    
    def remove_job_from_queue(self, job_id: str) -> bool:
        """
        Remove a specific job from the queue.
        
        Args:
            job_id: ID of job to remove
            
        Returns:
            True if job was found and removed, False otherwise
        """
        # This is a bit complex with PriorityQueue, so we'll rebuild the queue
        temp_jobs = []
        found = False
        
        while not self._export_queue.empty():
            try:
                priority, timestamp, counter, job = self._export_queue.get_nowait()
                if job.id == job_id:
                    found = True
                    logger.info(f"Removed job {job_id} from export queue")
                else:
                    temp_jobs.append((priority, timestamp, counter, job))
            except queue.Empty:
                break
        
        # Rebuild queue without the removed job
        for priority, timestamp, counter, job in temp_jobs:
            self._export_queue.put((priority, timestamp, counter, job))
        
        return found
    
    def _batch_export_worker(self) -> None:
        """
        Worker method for batch export processing (runs in separate thread).
        """
        total_jobs = self._export_queue.qsize()
        completed_count = 0
        
        batch_progress = BatchExportProgress(
            total_jobs=total_jobs,
            completed_jobs=0,
            queue_status=self._queue_status,
            overall_start_time=datetime.now()
        )
        self._update_batch_progress(batch_progress)
        
        while not self._export_queue.empty() and not self._stop_requested:
            # Handle pause
            while self._pause_requested and not self._stop_requested:
                time.sleep(0.1)
            
            if self._stop_requested:
                break
            
            try:
                # Get next job from queue
                priority, timestamp, counter, job = self._export_queue.get_nowait()
                self._current_batch_job = job
                
                # Update batch progress
                batch_progress.current_job = job
                batch_progress.completed_jobs = completed_count
                self._update_batch_progress(batch_progress)
                
                logger.info(f"Starting batch export job {job.id}: {job.output_path}")
                
                # Execute the export
                success = self._execute_single_export(job)
                
                if success:
                    job.progress.status = ExportStatus.COMPLETED
                    self._completed_jobs.append(job)
                    logger.info(f"Batch export job {job.id} completed successfully")
                else:
                    job.progress.status = ExportStatus.ERROR
                    self._failed_jobs.append(job)
                    logger.error(f"Batch export job {job.id} failed")
                
                completed_count += 1
                
            except queue.Empty:
                break
            except Exception as e:
                logger.error(f"Error processing batch export job: {e}")
                if self._current_batch_job:
                    self._current_batch_job.progress.status = ExportStatus.ERROR
                    self._current_batch_job.progress.error_message = str(e)
                    self._failed_jobs.append(self._current_batch_job)
                completed_count += 1
        
        # Final batch progress update
        batch_progress.completed_jobs = completed_count
        batch_progress.current_job = None
        batch_progress.queue_status = QueueStatus.IDLE if not self._stop_requested else QueueStatus.STOPPED
        self._queue_status = batch_progress.queue_status
        self._update_batch_progress(batch_progress)
        
        logger.info(f"Batch export completed: {len(self._completed_jobs)} successful, {len(self._failed_jobs)} failed")
    
    def _execute_single_export(self, job: ExportJob) -> bool:
        """
        Execute a single export job.
        
        Args:
            job: Export job to execute
            
        Returns:
            True if export successful, False otherwise
        """
        start_time = time.time()
        
        try:
            # Update job progress
            job.progress.status = ExportStatus.PREPARING
            job.progress.start_time = datetime.now()
            job.progress.current_operation = "Preparing export..."
            
            # Create temporary directory for frame rendering
            with tempfile.TemporaryDirectory() as temp_dir:
                frames_dir = Path(temp_dir) / "frames"
                frames_dir.mkdir()
                
                # Render frames
                if not self._render_frames_for_job(job, frames_dir):
                    return False
                
                # Encode video
                if not self._encode_video_for_job(job, frames_dir):
                    return False
                
                # Export completed successfully
                job.progress.status = ExportStatus.COMPLETED
                job.progress.current_frame = job.progress.total_frames
                job.progress.elapsed_time = time.time() - start_time
                job.progress.current_operation = "Export completed"
                
                return True
                
        except Exception as e:
            logger.error(f"Export job {job.id} failed: {e}")
            job.progress.status = ExportStatus.ERROR
            job.progress.error_message = str(e)
            job.progress.elapsed_time = time.time() - start_time
            return False
    
    def _render_frames_for_job(self, job: ExportJob, frames_dir: Path) -> bool:
        """
        Render all frames for a specific job.
        
        Args:
            job: Export job to render
            frames_dir: Directory to save rendered frames
            
        Returns:
            True if rendering successful, False otherwise
        """
        job.progress.status = ExportStatus.RENDERING
        job.progress.current_operation = "Rendering frames..."
        
        # Get export settings
        settings = job.project.export_settings
        width, height = settings.resolution
        fps = settings.fps
        duration = job.project.video_asset.duration
        
        # Calculate frame times
        frame_duration = 1.0 / fps
        total_frames = int(duration * fps)
        
        for frame_idx in range(total_frames):
            if self._stop_requested or (self._pause_requested and self._queue_status == QueueStatus.PAUSED):
                return False
            
            # Calculate current time
            current_time = frame_idx * frame_duration
            
            # Render frame
            frame_path = frames_dir / f"frame_{frame_idx:06d}.png"
            if not self._render_single_frame(job.project, current_time, frame_path, (width, height)):
                logger.error(f"Failed to render frame {frame_idx} for job {job.id}")
                return False
            
            # Update progress with enhanced ETA calculation
            job.progress.current_frame = frame_idx + 1
            job.progress.elapsed_time = time.time() - job.progress.start_time.timestamp()
            job.progress.current_operation = f"Rendering frame {frame_idx + 1}/{total_frames}"
            
            # Enhanced ETA calculation
            if frame_idx > 0:
                avg_time_per_frame = job.progress.elapsed_time / (frame_idx + 1)
                remaining_frames = total_frames - (frame_idx + 1)
                job.progress.estimated_remaining = avg_time_per_frame * remaining_frames
        
        return True
    
    def _encode_video_for_job(self, job: ExportJob, frames_dir: Path) -> bool:
        """
        Encode rendered frames for a specific job.
        
        Args:
            job: Export job to encode
            frames_dir: Directory containing rendered frames
            
        Returns:
            True if encoding successful, False otherwise
        """
        job.progress.status = ExportStatus.ENCODING
        job.progress.current_operation = "Encoding video..."
        
        try:
            # Get encoding parameters
            settings = job.project.export_settings
            preset_config = QualityPreset.get_preset(settings.quality_preset)
            
            # Merge custom parameters if provided
            if settings.custom_parameters:
                preset_config.update(settings.custom_parameters)
            
            # Build FFmpeg command
            cmd = self._build_ffmpeg_command(
                frames_dir,
                job.output_path,
                settings,
                preset_config,
                job.project.video_asset.path if hasattr(job.project, 'video_asset') else None
            )
            
            logger.info(f"Starting FFmpeg encoding for job {job.id}: {' '.join(cmd)}")
            
            # Run FFmpeg with progress monitoring
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True
            )
            
            # Monitor encoding progress
            while process.poll() is None:
                if self._stop_requested or (self._pause_requested and self._queue_status == QueueStatus.PAUSED):
                    process.terminate()
                    return False
                
                time.sleep(0.1)
                job.progress.current_operation = "Encoding video..."
            
            # Check if encoding was successful
            if process.returncode == 0:
                logger.info(f"Video encoding completed successfully for job {job.id}")
                return True
            else:
                stderr_output = process.stderr.read() if process.stderr else "Unknown error"
                logger.error(f"FFmpeg encoding failed for job {job.id}: {stderr_output}")
                job.progress.error_message = f"Encoding failed: {stderr_output}"
                return False
                
        except Exception as e:
            logger.error(f"Video encoding failed for job {job.id}: {e}")
            job.progress.error_message = str(e)
            return False
    
    def _export_worker(self, project: Project, output_path: str) -> None:
        """
        Worker method for video export (runs in separate thread).
        
        Args:
            project: Project to export
            output_path: Path for output video file
        """
        start_time = time.time()
        
        try:
            # Calculate total frames
            duration = project.video_asset.duration
            fps = project.export_settings.fps
            total_frames = int(duration * fps)
            
            # Initialize progress with enhanced tracking
            progress = ExportProgress(
                status=ExportStatus.PREPARING,
                current_frame=0,
                total_frames=total_frames,
                elapsed_time=0.0,
                current_operation="Preparing export...",
                start_time=datetime.now()
            )
            self._update_progress(progress)
            
            # Create temporary directory for frame rendering
            with tempfile.TemporaryDirectory() as temp_dir:
                frames_dir = Path(temp_dir) / "frames"
                frames_dir.mkdir()
                
                # Render frames
                if not self._render_frames(project, frames_dir, progress):
                    return
                
                # Encode video
                if not self._encode_video(project, frames_dir, output_path, progress):
                    return
                
                # Export completed successfully
                progress.status = ExportStatus.COMPLETED
                progress.current_frame = total_frames
                progress.elapsed_time = time.time() - start_time
                progress.current_operation = "Export completed"
                self._update_progress(progress)
                
                logger.info(f"Export completed successfully: {output_path}")
                
        except Exception as e:
            logger.error(f"Export failed: {e}")
            progress = ExportProgress(
                status=ExportStatus.ERROR,
                current_frame=0,
                total_frames=total_frames,
                elapsed_time=time.time() - start_time,
                error_message=str(e)
            )
            self._update_progress(progress)
    
    def _render_frames(self, project: Project, frames_dir: Path, progress: ExportProgress) -> bool:
        """
        Render all frames for the project.
        
        Args:
            project: Project to render
            frames_dir: Directory to save rendered frames
            progress: Progress tracking object
            
        Returns:
            True if rendering successful, False otherwise
        """
        progress.status = ExportStatus.RENDERING
        progress.current_operation = "Rendering frames..."
        self._update_progress(progress)
        
        # Get export settings
        settings = project.export_settings
        width, height = settings.resolution
        fps = settings.fps
        duration = project.video_asset.duration
        
        # Calculate frame times
        frame_duration = 1.0 / fps
        total_frames = int(duration * fps)
        
        for frame_idx in range(total_frames):
            if self._cancel_requested:
                progress.status = ExportStatus.CANCELLED
                progress.current_operation = "Export cancelled"
                self._update_progress(progress)
                return False
            
            # Calculate current time
            current_time = frame_idx * frame_duration
            
            # Render frame (placeholder - would use actual OpenGL renderer)
            frame_path = frames_dir / f"frame_{frame_idx:06d}.png"
            if not self._render_single_frame(project, current_time, frame_path, (width, height)):
                logger.error(f"Failed to render frame {frame_idx}")
                return False
            
            # Update progress with enhanced ETA calculation
            progress.current_frame = frame_idx + 1
            progress.elapsed_time = time.time() - progress.start_time.timestamp()
            progress.current_operation = f"Rendering frame {frame_idx + 1}/{total_frames}"
            
            # Enhanced ETA calculation
            if frame_idx > 0:
                avg_time_per_frame = progress.elapsed_time / (frame_idx + 1)
                remaining_frames = total_frames - (frame_idx + 1)
                progress.estimated_remaining = avg_time_per_frame * remaining_frames
            
            self._update_progress(progress)
        
        return True
    
    def _render_single_frame(self, project: Project, time: float, output_path: Path, resolution: Tuple[int, int]) -> bool:
        """
        Render a single frame at the specified time.
        
        Args:
            project: Project to render
            time: Time in seconds for this frame
            output_path: Path to save rendered frame
            resolution: Output resolution (width, height)
            
        Returns:
            True if rendering successful, False otherwise
        """
        # Placeholder implementation - would integrate with actual OpenGL renderer
        # For now, create a simple test frame
        try:
            import numpy as np
            from PIL import Image
            
            width, height = resolution
            
            # Create a simple gradient background
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Add gradient
            for y in range(height):
                intensity = int((y / height) * 255)
                frame[y, :, 0] = intensity // 3  # Red
                frame[y, :, 1] = intensity // 2  # Green
                frame[y, :, 2] = intensity      # Blue
            
            # Add time indicator (simple text simulation)
            text_y = height // 2
            text_width = int(width * 0.8)
            text_height = 50
            
            # Simple white rectangle as text placeholder
            frame[text_y:text_y+text_height, (width-text_width)//2:(width+text_width)//2] = [255, 255, 255]
            
            # Save frame
            image = Image.fromarray(frame)
            image.save(output_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to render frame: {e}")
            return False
    
    def _encode_video(self, project: Project, frames_dir: Path, output_path: str, progress: ExportProgress) -> bool:
        """
        Encode rendered frames into final video file.
        
        Args:
            project: Project being exported
            frames_dir: Directory containing rendered frames
            output_path: Path for output video file
            progress: Progress tracking object
            
        Returns:
            True if encoding successful, False otherwise
        """
        progress.status = ExportStatus.ENCODING
        progress.current_operation = "Encoding video..."
        self._update_progress(progress)
        
        try:
            # Get encoding parameters
            settings = project.export_settings
            preset_config = QualityPreset.get_preset(settings.quality_preset)
            
            # Merge custom parameters if provided
            if settings.custom_parameters:
                preset_config.update(settings.custom_parameters)
            
            # Build FFmpeg command
            cmd = self._build_ffmpeg_command(
                frames_dir,
                output_path,
                settings,
                preset_config,
                project.video_asset.path if hasattr(project, 'video_asset') else None
            )
            
            logger.info(f"Starting FFmpeg encoding: {' '.join(cmd)}")
            
            # Run FFmpeg with progress monitoring
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True
            )
            
            # Monitor encoding progress
            while process.poll() is None:
                if self._cancel_requested:
                    process.terminate()
                    progress.status = ExportStatus.CANCELLED
                    progress.current_operation = "Export cancelled"
                    self._update_progress(progress)
                    return False
                
                # Read FFmpeg output for progress (simplified)
                time.sleep(0.1)
                progress.current_operation = "Encoding video..."
                self._update_progress(progress)
            
            # Check if encoding was successful
            if process.returncode == 0:
                logger.info("Video encoding completed successfully")
                return True
            else:
                stderr_output = process.stderr.read() if process.stderr else "Unknown error"
                logger.error(f"FFmpeg encoding failed: {stderr_output}")
                return False
                
        except Exception as e:
            logger.error(f"Video encoding failed: {e}")
            return False
    
    def _build_ffmpeg_command(
        self,
        frames_dir: Path,
        output_path: str,
        settings: ExportSettings,
        preset_config: Dict[str, Any],
        audio_source: Optional[str] = None
    ) -> List[str]:
        """
        Build FFmpeg command for video encoding.
        
        Args:
            frames_dir: Directory containing input frames
            output_path: Output video file path
            settings: Export settings
            preset_config: Quality preset configuration
            audio_source: Optional audio source file
            
        Returns:
            FFmpeg command as list of arguments
        """
        cmd = ['ffmpeg', '-y']  # -y to overwrite output file
        
        # Input frames
        frame_pattern = str(frames_dir / "frame_%06d.png")
        cmd.extend(['-framerate', str(settings.fps)])
        cmd.extend(['-i', frame_pattern])
        
        # Add audio input if available
        if audio_source and os.path.exists(audio_source):
            cmd.extend(['-i', audio_source])
        
        # Video encoding parameters
        cmd.extend(['-c:v', preset_config.get('video_codec', 'libx264')])
        
        # Quality settings
        if 'crf' in preset_config:
            cmd.extend(['-crf', str(preset_config['crf'])])
        elif settings.bitrate:
            cmd.extend(['-b:v', str(settings.bitrate)])
        elif 'video_bitrate' in preset_config:
            cmd.extend(['-b:v', preset_config['video_bitrate']])
        
        # Encoding preset and profile
        if 'preset' in preset_config:
            cmd.extend(['-preset', preset_config['preset']])
        if 'profile' in preset_config:
            cmd.extend(['-profile:v', preset_config['profile']])
        
        # Audio encoding (if audio source available)
        if audio_source and os.path.exists(audio_source):
            cmd.extend(['-c:a', preset_config.get('audio_codec', 'aac')])
            if 'audio_bitrate' in preset_config:
                cmd.extend(['-b:a', preset_config['audio_bitrate']])
        else:
            cmd.extend(['-an'])  # No audio
        
        # Output format
        format_info = self.supported_formats.get(settings.format.lower())
        if format_info:
            cmd.extend(['-f', format_info['container']])
        
        # Pixel format for compatibility
        cmd.extend(['-pix_fmt', 'yuv420p'])
        
        # Resolution
        width, height = settings.resolution
        cmd.extend(['-s', f"{width}x{height}"])
        
        # Output file
        cmd.append(output_path)
        
        return cmd
    
    def _update_progress(self, progress: ExportProgress) -> None:
        """Update progress via callback if available."""
        if self._progress_callback:
            self._progress_callback(progress)
    
    def _update_batch_progress(self, batch_progress: BatchExportProgress) -> None:
        """Update batch progress via callback if available."""
        if self._batch_progress_callback:
            self._batch_progress_callback(batch_progress)
    
    def _check_ffmpeg_availability(self) -> bool:
        """Check if FFmpeg is available in the system."""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def get_supported_formats(self) -> Dict[str, Dict[str, Any]]:
        """Get information about supported output formats."""
        return self.supported_formats.copy()
    
    def get_available_codecs(self, format_name: str) -> Dict[str, List[str]]:
        """
        Get available codecs for a specific format.
        
        Args:
            format_name: Output format name
            
        Returns:
            Dictionary with video and audio codec lists
        """
        format_info = self.supported_formats.get(format_name.lower())
        if not format_info:
            return {'video_codecs': [], 'audio_codecs': []}
        
        return {
            'video_codecs': format_info['video_codecs'].copy(),
            'audio_codecs': format_info['audio_codecs'].copy()
        }
    
    def estimate_file_size(self, project: Project) -> Optional[int]:
        """
        Estimate output file size in bytes.
        
        Args:
            project: Project to estimate size for
            
        Returns:
            Estimated file size in bytes, or None if cannot estimate
        """
        try:
            settings = project.export_settings
            duration = project.video_asset.duration
            
            # Get bitrate from settings or preset
            if settings.bitrate:
                video_bitrate = settings.bitrate
            else:
                preset_config = QualityPreset.get_preset(settings.quality_preset)
                bitrate_str = preset_config.get('video_bitrate', '5M')
                
                # Parse bitrate string (e.g., "5M" -> 5000000)
                if bitrate_str.endswith('M'):
                    video_bitrate = int(float(bitrate_str[:-1]) * 1000000)
                elif bitrate_str.endswith('k'):
                    video_bitrate = int(float(bitrate_str[:-1]) * 1000)
                else:
                    video_bitrate = int(bitrate_str)
            
            # Estimate video size (bitrate * duration / 8 for bytes)
            video_size = int((video_bitrate * duration) / 8)
            
            # Add audio size estimate (if audio present)
            audio_size = 0
            if project.audio_asset:
                # Assume 192 kbps audio bitrate
                audio_bitrate = 192000
                audio_size = int((audio_bitrate * duration) / 8)
            
            return video_size + audio_size
            
        except Exception as e:
            logger.warning(f"Could not estimate file size: {e}")
            return None