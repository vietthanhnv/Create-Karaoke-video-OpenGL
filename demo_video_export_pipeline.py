#!/usr/bin/env python3
"""
Demo script for video export pipeline functionality.

This script demonstrates the video export pipeline capabilities including:
- Quality preset management
- Export settings validation
- Progress tracking simulation
- FFmpeg command generation
"""

import sys
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.video.export_pipeline import (
    VideoExportPipeline, QualityPreset, ExportStatus, ExportProgress
)
from src.core.models import (
    Project, VideoAsset, AudioAsset, ExportSettings, SubtitleTrack, 
    TextElement, AnimationType, EasingType, AnimationEffect
)


def print_header(title: str) -> None:
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'-'*40}")
    print(f" {title}")
    print(f"{'-'*40}")


def demo_quality_presets():
    """Demonstrate quality preset functionality."""
    print_section("Quality Presets")
    
    # Show available presets
    presets = QualityPreset.get_available_presets()
    print(f"Available presets: {', '.join(presets)}")
    
    # Show preset details
    for preset_name in presets:
        preset = QualityPreset.get_preset(preset_name)
        print(f"\n{preset_name.upper()} Preset:")
        print(f"  Name: {preset['name']}")
        print(f"  Description: {preset['description']}")
        print(f"  Video Codec: {preset['video_codec']}")
        print(f"  Video Bitrate: {preset['video_bitrate']}")
        print(f"  Audio Codec: {preset['audio_codec']}")
        print(f"  Audio Bitrate: {preset['audio_bitrate']}")
        print(f"  CRF: {preset['crf']}")
        print(f"  Preset: {preset['preset']}")


def demo_export_settings_validation():
    """Demonstrate export settings validation."""
    print_section("Export Settings Validation")
    
    pipeline = VideoExportPipeline()
    
    # Test valid settings
    print("Testing valid export settings:")
    valid_settings = ExportSettings(
        resolution=(1920, 1080),
        fps=30.0,
        format="mp4",
        quality_preset="normal",
        codec="libx264",
        bitrate=5000000
    )
    
    result = pipeline.validate_export_settings(valid_settings)
    print(f"  Valid: {result.is_valid}")
    if result.warnings:
        print(f"  Warnings: {', '.join(result.warnings)}")
    
    # Test invalid settings
    print("\nTesting invalid export settings:")
    
    # Invalid resolution (odd numbers)
    invalid_settings = ExportSettings(
        resolution=(1921, 1081),  # Odd numbers
        fps=30.0,
        format="mp4",
        quality_preset="normal",
        codec="libx264"
    )
    
    result = pipeline.validate_export_settings(invalid_settings)
    print(f"  Odd resolution - Valid: {result.is_valid}")
    if not result.is_valid:
        print(f"  Error: {result.error_message}")
    
    # Invalid format
    invalid_settings.resolution = (1920, 1080)
    invalid_settings.format = "invalid_format"
    
    result = pipeline.validate_export_settings(invalid_settings)
    print(f"  Invalid format - Valid: {result.is_valid}")
    if not result.is_valid:
        print(f"  Error: {result.error_message}")
    
    # Invalid codec
    invalid_settings.format = "mp4"
    invalid_settings.codec = "invalid_codec"
    
    result = pipeline.validate_export_settings(invalid_settings)
    print(f"  Invalid codec - Valid: {result.is_valid}")
    if not result.is_valid:
        print(f"  Error: {result.error_message}")


def demo_supported_formats():
    """Demonstrate supported format information."""
    print_section("Supported Formats")
    
    pipeline = VideoExportPipeline()
    formats = pipeline.get_supported_formats()
    
    for format_name, format_info in formats.items():
        print(f"\n{format_name.upper()} Format:")
        print(f"  Container: {format_info['container']}")
        print(f"  Extension: {format_info['extension']}")
        print(f"  Video Codecs: {', '.join(format_info['video_codecs'])}")
        print(f"  Audio Codecs: {', '.join(format_info['audio_codecs'])}")
        
        # Show available codecs
        codecs = pipeline.get_available_codecs(format_name)
        print(f"  Available Video Codecs: {', '.join(codecs['video_codecs'])}")
        print(f"  Available Audio Codecs: {', '.join(codecs['audio_codecs'])}")


def demo_ffmpeg_command_generation():
    """Demonstrate FFmpeg command generation."""
    print_section("FFmpeg Command Generation")
    
    pipeline = VideoExportPipeline()
    
    # Create test export settings
    settings = ExportSettings(
        resolution=(1920, 1080),
        fps=30.0,
        format="mp4",
        quality_preset="normal",
        codec="libx264",
        bitrate=5000000
    )
    
    # Get preset configuration
    preset_config = QualityPreset.get_preset(settings.quality_preset)
    
    # Generate command
    frames_dir = Path("/tmp/frames")
    output_path = "/tmp/output.mp4"
    
    cmd = pipeline._build_ffmpeg_command(
        frames_dir, output_path, settings, preset_config
    )
    
    print("Generated FFmpeg command:")
    print(f"  {' '.join(cmd)}")
    
    # Generate command with audio
    print("\nGenerated FFmpeg command with audio:")
    cmd_with_audio = pipeline._build_ffmpeg_command(
        frames_dir, output_path, settings, preset_config, "/tmp/audio.mp3"
    )
    print(f"  {' '.join(cmd_with_audio)}")


def demo_file_size_estimation():
    """Demonstrate file size estimation."""
    print_section("File Size Estimation")
    
    pipeline = VideoExportPipeline()
    
    # Create test project
    video_asset = VideoAsset(
        path="test_video.mp4",
        duration=120.0,  # 2 minutes
        fps=30.0,
        resolution=(1920, 1080),
        codec="h264"
    )
    
    audio_asset = AudioAsset(
        path="test_audio.mp3",
        duration=120.0,
        sample_rate=44100,
        channels=2,
        format="mp3"
    )
    
    # Test different quality presets
    for preset_name in QualityPreset.get_available_presets():
        export_settings = ExportSettings(
            resolution=(1920, 1080),
            fps=30.0,
            format="mp4",
            quality_preset=preset_name,
            codec="libx264"
        )
        
        project = Project(
            name=f"Test Project - {preset_name}",
            video_asset=video_asset,
            audio_asset=audio_asset,
            subtitle_tracks=[],
            export_settings=export_settings,
            created_at=datetime.now(),
            modified_at=datetime.now()
        )
        
        estimated_size = pipeline.estimate_file_size(project)
        if estimated_size:
            size_mb = estimated_size / (1024 * 1024)
            print(f"  {preset_name.upper()} preset: {size_mb:.1f} MB")
        else:
            print(f"  {preset_name.upper()} preset: Could not estimate")


def demo_progress_tracking():
    """Demonstrate progress tracking functionality."""
    print_section("Progress Tracking Simulation")
    
    # Simulate export progress
    total_frames = 100
    
    print("Simulating export progress:")
    
    for frame in range(0, total_frames + 1, 10):
        progress = ExportProgress(
            status=ExportStatus.RENDERING if frame < total_frames else ExportStatus.COMPLETED,
            current_frame=frame,
            total_frames=total_frames,
            elapsed_time=frame * 0.1,  # Simulate 0.1s per frame
            current_operation=f"Rendering frame {frame}/{total_frames}" if frame < total_frames else "Export completed"
        )
        
        # Calculate estimated remaining time
        if frame > 0 and frame < total_frames:
            avg_time_per_frame = progress.elapsed_time / frame
            remaining_frames = total_frames - frame
            progress.estimated_remaining = avg_time_per_frame * remaining_frames
        
        # Display progress
        percentage = progress.progress_percentage
        elapsed = progress.elapsed_time
        remaining = progress.estimated_remaining or 0
        
        print(f"  Progress: {percentage:5.1f}% | "
              f"Frame: {frame:3d}/{total_frames} | "
              f"Elapsed: {elapsed:5.1f}s | "
              f"Remaining: {remaining:5.1f}s | "
              f"Status: {progress.status.value}")
        
        # Small delay for demonstration
        time.sleep(0.1)


def create_sample_project():
    """Create a sample project for demonstration."""
    print_section("Sample Project Creation")
    
    # Create video asset
    video_asset = VideoAsset(
        path="sample_karaoke_video.mp4",
        duration=180.0,  # 3 minutes
        fps=30.0,
        resolution=(1920, 1080),
        codec="h264"
    )
    
    # Create audio asset
    audio_asset = AudioAsset(
        path="sample_karaoke_audio.mp3",
        duration=180.0,
        sample_rate=44100,
        channels=2,
        format="mp3"
    )
    
    # Create text elements with effects
    text_element1 = TextElement(
        content="Welcome to karaoke night!",
        font_family="Arial",
        font_size=48.0,
        color=(1.0, 1.0, 1.0, 1.0),  # White
        position=(960.0, 540.0),  # Center
        rotation=(0.0, 0.0, 0.0),
        effects=[
            AnimationEffect(
                type=AnimationType.FADE_IN,
                duration=1.0,
                parameters={'start_alpha': 0.0, 'end_alpha': 1.0},
                easing_curve=EasingType.EASE_IN_OUT
            )
        ]
    )
    
    text_element2 = TextElement(
        content="Sing along with the lyrics!",
        font_family="Arial",
        font_size=36.0,
        color=(1.0, 0.8, 0.2, 1.0),  # Golden
        position=(960.0, 800.0),  # Bottom
        rotation=(0.0, 0.0, 0.0),
        effects=[
            AnimationEffect(
                type=AnimationType.SLIDE_UP,
                duration=2.0,
                parameters={'start_y': 1080, 'end_y': 800},
                easing_curve=EasingType.BOUNCE
            )
        ]
    )
    
    # Create subtitle track
    subtitle_track = SubtitleTrack(
        id="main_track",
        elements=[text_element1, text_element2],
        keyframes=[],
        start_time=0.0,
        end_time=180.0
    )
    
    # Create export settings
    export_settings = ExportSettings(
        resolution=(1920, 1080),
        fps=30.0,
        format="mp4",
        quality_preset="high",
        codec="libx264",
        bitrate=8000000,  # 8 Mbps
        custom_parameters={
            'profile': 'high',
            'level': '4.1',
            'tune': 'film'
        }
    )
    
    # Create project
    project = Project(
        name="Sample Karaoke Project",
        video_asset=video_asset,
        audio_asset=audio_asset,
        subtitle_tracks=[subtitle_track],
        export_settings=export_settings,
        created_at=datetime.now(),
        modified_at=datetime.now()
    )
    
    print("Created sample project:")
    print(f"  Name: {project.name}")
    print(f"  Duration: {project.video_asset.duration}s")
    print(f"  Resolution: {project.video_asset.resolution}")
    print(f"  Subtitle tracks: {len(project.subtitle_tracks)}")
    print(f"  Text elements: {sum(len(track.elements) for track in project.subtitle_tracks)}")
    print(f"  Export format: {project.export_settings.format}")
    print(f"  Export quality: {project.export_settings.quality_preset}")
    
    return project


def demo_export_pipeline_integration():
    """Demonstrate complete export pipeline integration."""
    print_section("Export Pipeline Integration")
    
    # Create sample project
    project = create_sample_project()
    
    # Initialize pipeline
    pipeline = VideoExportPipeline()
    
    # Validate project export settings
    print("\nValidating export settings:")
    validation = pipeline.validate_export_settings(project.export_settings)
    print(f"  Valid: {validation.is_valid}")
    if validation.warnings:
        print(f"  Warnings: {', '.join(validation.warnings)}")
    
    # Estimate file size
    print("\nEstimating output file size:")
    estimated_size = pipeline.estimate_file_size(project)
    if estimated_size:
        size_mb = estimated_size / (1024 * 1024)
        size_gb = size_mb / 1024
        print(f"  Estimated size: {size_mb:.1f} MB ({size_gb:.2f} GB)")
    else:
        print("  Could not estimate file size")
    
    # Show FFmpeg command that would be generated
    print("\nFFmpeg command preview:")
    preset_config = QualityPreset.get_preset(project.export_settings.quality_preset)
    if project.export_settings.custom_parameters:
        preset_config.update(project.export_settings.custom_parameters)
    
    cmd = pipeline._build_ffmpeg_command(
        Path("/tmp/frames"),
        "/tmp/output.mp4",
        project.export_settings,
        preset_config,
        project.audio_asset.path if project.audio_asset else None
    )
    
    print(f"  Command: {' '.join(cmd[:10])}...")  # Show first 10 arguments
    print(f"  Full length: {len(cmd)} arguments")


def main():
    """Main demo function."""
    print_header("Video Export Pipeline Demo")
    
    print("This demo showcases the video export pipeline functionality")
    print("including quality presets, validation, and FFmpeg integration.")
    
    try:
        # Run all demonstrations
        demo_quality_presets()
        demo_export_settings_validation()
        demo_supported_formats()
        demo_ffmpeg_command_generation()
        demo_file_size_estimation()
        demo_progress_tracking()
        demo_export_pipeline_integration()
        
        print_header("Demo Complete")
        print("All video export pipeline features demonstrated successfully!")
        
    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())