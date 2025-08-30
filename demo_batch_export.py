#!/usr/bin/env python3
"""
Demo script for batch export functionality in the Karaoke Subtitle Creator.

This script demonstrates:
- Adding multiple projects to export queue
- Progress tracking with ETA estimation
- Queue management (pause/resume/stop)
- Batch processing with priority handling
"""

import sys
import os
import time
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.video.export_pipeline import (
    VideoExportPipeline, 
    ExportProgress, 
    BatchExportProgress,
    ExportStatus,
    QueueStatus
)
from src.core.models import (
    Project, VideoAsset, ExportSettings, SubtitleTrack, TextElement,
    AudioAsset
)


def create_sample_project(name: str, duration: float = 10.0) -> Project:
    """Create a sample project for testing."""
    
    # Create video asset
    video_asset = VideoAsset(
        path=f"sample_{name.lower().replace(' ', '_')}.mp4",
        duration=duration,
        fps=30.0,
        resolution=(1920, 1080),
        codec="h264"
    )
    
    # Create audio asset
    audio_asset = AudioAsset(
        path=f"sample_{name.lower().replace(' ', '_')}.mp3",
        duration=duration,
        sample_rate=44100,
        channels=2,
        format="mp3"
    )
    
    # Create export settings
    export_settings = ExportSettings(
        resolution=(1920, 1080),
        fps=30.0,
        format="mp4",
        quality_preset="normal",
        codec="libx264",
        bitrate=5000000
    )
    
    # Create sample text element
    text_element = TextElement(
        content=f"Sample karaoke text for {name}",
        font_family="Arial",
        font_size=48.0,
        color=(1.0, 1.0, 1.0, 1.0),  # White
        position=(960.0, 540.0),  # Center
        rotation=(0.0, 0.0, 0.0),
        effects=[]
    )
    
    # Create subtitle track
    subtitle_track = SubtitleTrack(
        id="main_track",
        elements=[text_element],
        keyframes=[],
        start_time=0.0,
        end_time=duration
    )
    
    # Create project
    project = Project(
        name=name,
        video_asset=video_asset,
        audio_asset=audio_asset,
        subtitle_tracks=[subtitle_track],
        export_settings=export_settings,
        created_at=datetime.now(),
        modified_at=datetime.now()
    )
    
    return project


def progress_callback(progress: ExportProgress):
    """Callback for single export progress updates."""
    print(f"  Export Progress: {progress.progress_percentage:.1f}% "
          f"({progress.current_frame}/{progress.total_frames} frames)")
    print(f"    Status: {progress.status.value}")
    print(f"    Operation: {progress.current_operation}")
    print(f"    Elapsed: {progress.elapsed_time:.1f}s")
    
    if progress.estimated_remaining:
        print(f"    ETA: {progress.estimated_remaining:.1f}s remaining")
        if progress.eta_datetime:
            print(f"    Completion: {progress.eta_datetime.strftime('%H:%M:%S')}")
    
    if progress.error_message:
        print(f"    Error: {progress.error_message}")
    
    print()


def batch_progress_callback(batch_progress: BatchExportProgress):
    """Callback for batch export progress updates."""
    print(f"\n=== Batch Export Progress ===")
    print(f"Overall: {batch_progress.overall_progress_percentage:.1f}% "
          f"({batch_progress.completed_jobs}/{batch_progress.total_jobs} jobs)")
    print(f"Queue Status: {batch_progress.queue_status.value}")
    
    if batch_progress.current_job:
        print(f"Current Job: {batch_progress.current_job.id}")
        print(f"  Project: {batch_progress.current_job.project.name}")
        print(f"  Output: {batch_progress.current_job.output_path}")
        
        if batch_progress.current_job.progress:
            job_progress = batch_progress.current_job.progress
            print(f"  Job Progress: {job_progress.progress_percentage:.1f}%")
    
    if batch_progress.estimated_completion_time:
        completion_time = batch_progress.estimated_completion_time
        print(f"Estimated Completion: {completion_time.strftime('%H:%M:%S')}")
    
    print("=" * 30)


def demo_single_export():
    """Demonstrate single export with progress tracking."""
    print("=== Single Export Demo ===\n")
    
    # Create export pipeline
    pipeline = VideoExportPipeline()
    
    # Create sample project
    project = create_sample_project("Single Export Demo", duration=5.0)
    
    print(f"Created project: {project.name}")
    print(f"Video duration: {project.video_asset.duration}s")
    print(f"Export resolution: {project.export_settings.resolution}")
    print(f"Export format: {project.export_settings.format}")
    print()
    
    # Validate export settings
    validation = pipeline.validate_export_settings(project.export_settings)
    if not validation.is_valid:
        print(f"Export validation failed: {validation.error_message}")
        return
    
    print("Export settings validated successfully")
    
    if validation.warnings:
        print("Warnings:")
        for warning in validation.warnings:
            print(f"  - {warning}")
    
    print()
    
    # Estimate file size
    estimated_size = pipeline.estimate_file_size(project)
    if estimated_size:
        size_mb = estimated_size / (1024 * 1024)
        print(f"Estimated file size: {size_mb:.1f} MB")
    
    print()
    
    # Start export (simulated)
    output_path = "output/single_export_demo.mp4"
    print(f"Starting export to: {output_path}")
    print("Note: This is a simulation - actual export requires FFmpeg")
    print()
    
    # Simulate export progress
    total_frames = int(project.video_asset.duration * project.export_settings.fps)
    
    for frame in range(0, total_frames + 1, 5):  # Update every 5 frames
        progress = ExportProgress(
            status=ExportStatus.RENDERING if frame < total_frames else ExportStatus.COMPLETED,
            current_frame=frame,
            total_frames=total_frames,
            elapsed_time=frame * 0.1,  # Simulate 0.1s per frame
            estimated_remaining=(total_frames - frame) * 0.1 if frame < total_frames else 0,
            current_operation=f"Rendering frame {frame}/{total_frames}" if frame < total_frames else "Export completed",
            start_time=datetime.now()
        )
        
        progress_callback(progress)
        time.sleep(0.2)  # Simulate processing time
    
    print("Single export demo completed!\n")


def demo_batch_export():
    """Demonstrate batch export with queue management."""
    print("=== Batch Export Demo ===\n")
    
    # Create export pipeline
    pipeline = VideoExportPipeline()
    
    # Create multiple sample projects
    projects = [
        create_sample_project("Music Video A", duration=8.0),
        create_sample_project("Music Video B", duration=12.0),
        create_sample_project("Music Video C", duration=6.0),
        create_sample_project("Music Video D", duration=10.0),
    ]
    
    print(f"Created {len(projects)} sample projects:")
    for i, project in enumerate(projects):
        print(f"  {i+1}. {project.name} ({project.video_asset.duration}s)")
    print()
    
    # Add projects to export queue with different priorities
    job_ids = []
    priorities = [2, 1, 3, 1]  # Lower numbers = higher priority
    
    for i, (project, priority) in enumerate(zip(projects, priorities)):
        output_path = f"output/batch_export_{i+1}.mp4"
        job_id = pipeline.add_to_export_queue(project, output_path, priority)
        job_ids.append(job_id)
        print(f"Added to queue: {project.name} (Priority: {priority}, Job ID: {job_id})")
    
    print(f"\nQueue size: {pipeline.get_queue_size()} jobs")
    print(f"Queue status: {pipeline.get_queue_status().value}")
    print()
    
    # Demonstrate queue management
    print("=== Queue Management Demo ===")
    
    # Remove one job from queue
    removed_job = job_ids[2]  # Remove third job
    if pipeline.remove_job_from_queue(removed_job):
        print(f"Removed job {removed_job} from queue")
        print(f"Queue size after removal: {pipeline.get_queue_size()}")
    
    print()
    
    # Start batch export (simulated)
    print("Starting batch export...")
    print("Note: This is a simulation - actual export requires FFmpeg")
    print()
    
    # Simulate batch processing
    remaining_jobs = pipeline.get_queue_size()
    completed_jobs = 0
    
    # Create mock jobs for simulation
    mock_jobs = []
    for i in range(remaining_jobs):
        project = projects[i] if i < len(projects) else projects[0]
        mock_job = type('MockJob', (), {
            'id': job_ids[i],
            'project': project,
            'output_path': f"output/batch_export_{i+1}.mp4",
            'progress': ExportProgress(
                status=ExportStatus.QUEUED,
                current_frame=0,
                total_frames=int(project.video_asset.duration * project.export_settings.fps),
                elapsed_time=0.0,
                start_time=datetime.now()
            )
        })()
        mock_jobs.append(mock_job)
    
    # Simulate batch processing
    for job_idx, job in enumerate(mock_jobs):
        print(f"\n--- Processing Job {job_idx + 1}/{len(mock_jobs)} ---")
        print(f"Project: {job.project.name}")
        print(f"Output: {job.output_path}")
        
        # Simulate job processing
        total_frames = job.progress.total_frames
        
        for frame in range(0, total_frames + 1, 10):  # Update every 10 frames
            # Update job progress
            job.progress.status = ExportStatus.RENDERING if frame < total_frames else ExportStatus.COMPLETED
            job.progress.current_frame = frame
            job.progress.elapsed_time = frame * 0.05  # Simulate 0.05s per frame
            job.progress.estimated_remaining = (total_frames - frame) * 0.05 if frame < total_frames else 0
            job.progress.current_operation = f"Rendering frame {frame}/{total_frames}" if frame < total_frames else "Job completed"
            
            # Create batch progress
            batch_progress = BatchExportProgress(
                total_jobs=len(mock_jobs),
                completed_jobs=completed_jobs,
                current_job=job,
                queue_status=QueueStatus.RUNNING,
                overall_start_time=datetime.now()
            )
            
            batch_progress_callback(batch_progress)
            time.sleep(0.1)  # Simulate processing time
        
        completed_jobs += 1
        print(f"Job {job.id} completed successfully!")
    
    # Final batch status
    final_batch_progress = BatchExportProgress(
        total_jobs=len(mock_jobs),
        completed_jobs=completed_jobs,
        current_job=None,
        queue_status=QueueStatus.IDLE
    )
    
    batch_progress_callback(final_batch_progress)
    print("\nBatch export demo completed!")
    print(f"Successfully processed {completed_jobs} jobs")


def demo_queue_controls():
    """Demonstrate queue control features (pause/resume/stop)."""
    print("=== Queue Control Demo ===\n")
    
    pipeline = VideoExportPipeline()
    
    # Add some jobs
    projects = [
        create_sample_project("Control Demo A", duration=5.0),
        create_sample_project("Control Demo B", duration=5.0),
    ]
    
    for i, project in enumerate(projects):
        pipeline.add_to_export_queue(project, f"output/control_demo_{i+1}.mp4")
    
    print(f"Added {len(projects)} jobs to queue")
    print(f"Initial queue status: {pipeline.get_queue_status().value}")
    print()
    
    # Simulate starting batch export
    print("Simulating batch export start...")
    pipeline._queue_status = QueueStatus.RUNNING
    print(f"Queue status: {pipeline.get_queue_status().value}")
    print()
    
    # Test pause
    print("Testing pause functionality...")
    if pipeline.pause_batch_export():
        print(f"Successfully paused. Status: {pipeline.get_queue_status().value}")
    else:
        print("Failed to pause")
    print()
    
    # Test resume
    print("Testing resume functionality...")
    if pipeline.resume_batch_export():
        print(f"Successfully resumed. Status: {pipeline.get_queue_status().value}")
    else:
        print("Failed to resume")
    print()
    
    # Test stop
    print("Testing stop functionality...")
    if pipeline.stop_batch_export():
        print(f"Successfully stopped. Status: {pipeline.get_queue_status().value}")
    else:
        print("Failed to stop")
    print()
    
    # Test clear queue
    print("Testing queue clearing...")
    cleared_count = pipeline.clear_queue()
    print(f"Cleared {cleared_count} jobs from queue")
    print(f"Final queue size: {pipeline.get_queue_size()}")


def main():
    """Main demo function."""
    print("Karaoke Subtitle Creator - Batch Export Demo")
    print("=" * 50)
    print()
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    try:
        # Run demos
        demo_single_export()
        print("\n" + "=" * 50 + "\n")
        
        demo_batch_export()
        print("\n" + "=" * 50 + "\n")
        
        demo_queue_controls()
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nDemo error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nDemo completed!")


if __name__ == "__main__":
    main()