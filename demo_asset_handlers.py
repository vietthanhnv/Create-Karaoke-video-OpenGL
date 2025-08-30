#!/usr/bin/env python3
"""
Demonstration script for video and audio asset handlers.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, 'src')

from src.video.asset_handler import VideoAssetHandler
from src.audio.asset_handler import AudioAssetHandler
from src.core.project_manager import ProjectManager


def demo_video_handler():
    """Demonstrate video asset handler functionality."""
    print("=== Video Asset Handler Demo ===")
    
    handler = VideoAssetHandler()
    
    # Show supported formats
    print("Supported video formats:")
    for ext, mime in handler.get_supported_formats().items():
        print(f"  {ext}: {mime}")
    
    # Check FFmpeg availability
    print(f"\nFFmpeg available: {handler.is_ffmpeg_available()}")
    print(f"FFprobe available: {handler.is_ffprobe_available()}")
    
    # Check if test video exists
    test_video = "test_video.mp4"
    if os.path.exists(test_video):
        print(f"\nAnalyzing {test_video}...")
        
        # Validate the video
        validation = handler.validate_video_file(test_video)
        print(f"Valid: {validation.is_valid}")
        if validation.warnings:
            print(f"Warnings: {validation.warnings}")
        
        # Create video asset
        try:
            video_asset = handler.create_video_asset(test_video)
            print(f"Video Asset created:")
            print(f"  Path: {video_asset.path}")
            print(f"  Duration: {video_asset.duration:.2f} seconds")
            print(f"  FPS: {video_asset.fps}")
            print(f"  Resolution: {video_asset.resolution}")
            print(f"  Codec: {video_asset.codec}")
            
            # Get info summary
            summary = handler.get_video_info_summary(test_video)
            print(f"  Summary: {summary}")
            
        except Exception as e:
            print(f"Error creating video asset: {e}")
    else:
        print(f"\nNo test video file found ({test_video})")
        print("You can place a video file named 'test_video.mp4' in the current directory to test with real data")


def demo_audio_handler():
    """Demonstrate audio asset handler functionality."""
    print("\n=== Audio Asset Handler Demo ===")
    
    handler = AudioAssetHandler()
    
    # Show supported formats
    print("Supported audio formats:")
    for ext, mime in handler.get_supported_formats().items():
        print(f"  {ext}: {mime}")
    
    # Check FFmpeg availability
    print(f"\nFFmpeg available: {handler.is_ffmpeg_available()}")
    print(f"FFprobe available: {handler.is_ffprobe_available()}")
    
    # Check if test audio exists
    test_audio = "test_audio.mp3"
    if os.path.exists(test_audio):
        print(f"\nAnalyzing {test_audio}...")
        
        # Validate the audio
        validation = handler.validate_audio_file(test_audio)
        print(f"Valid: {validation.is_valid}")
        if validation.warnings:
            print(f"Warnings: {validation.warnings}")
        
        # Create audio asset
        try:
            audio_asset = handler.create_audio_asset(test_audio)
            print(f"Audio Asset created:")
            print(f"  Path: {audio_asset.path}")
            print(f"  Duration: {audio_asset.duration:.2f} seconds")
            print(f"  Sample Rate: {audio_asset.sample_rate} Hz")
            print(f"  Channels: {audio_asset.channels}")
            print(f"  Format: {audio_asset.format}")
            
            # Get info summary
            summary = handler.get_audio_info_summary(test_audio)
            print(f"  Summary: {summary}")
            
        except Exception as e:
            print(f"Error creating audio asset: {e}")
    else:
        print(f"\nNo test audio file found ({test_audio})")
        print("You can place an audio file named 'test_audio.mp3' in the current directory to test with real data")


def demo_project_manager():
    """Demonstrate project manager integration."""
    print("\n=== Project Manager Integration Demo ===")
    
    manager = ProjectManager()
    
    # Check if test video exists for project creation
    test_video = "test_video.mp4"
    if os.path.exists(test_video):
        print(f"\nCreating project with {test_video}...")
        
        try:
            # Create project
            project = manager.create_project(test_video, "Demo Project")
            print(f"Project created: {project.name}")
            print(f"Video duration: {project.video_asset.duration:.2f} seconds")
            print(f"Export settings: {project.export_settings.format} at {project.export_settings.resolution}")
            
            # Try importing audio if available
            test_audio = "test_audio.mp3"
            if os.path.exists(test_audio):
                print(f"\nImporting audio {test_audio}...")
                audio_asset = manager.import_audio(test_audio)
                project.audio_asset = audio_asset
                print(f"Audio imported: {audio_asset.duration:.2f} seconds, {audio_asset.channels} channels")
            
            # Save project
            project_path = "demo_project.ksp"
            if manager.save_project(project, project_path):
                print(f"\nProject saved to {project_path}")
                
                # Load it back
                loaded_project = manager.load_project(project_path)
                print(f"Project loaded: {loaded_project.name}")
                
                # Clean up
                os.remove(project_path)
                print("Demo project file cleaned up")
            
        except Exception as e:
            print(f"Error in project operations: {e}")
    else:
        print(f"\nNo test video file found ({test_video})")
        print("Project creation requires a video file")


def main():
    """Run all demonstrations."""
    print("Asset Handlers Demonstration")
    print("=" * 50)
    
    demo_video_handler()
    demo_audio_handler()
    demo_project_manager()
    
    print("\n" + "=" * 50)
    print("Demo completed!")
    print("\nNote: For full functionality demonstration, place test files:")
    print("  - test_video.mp4 (any MP4 video file)")
    print("  - test_audio.mp3 (any MP3 audio file)")
    print("in the current directory and run this script again.")


if __name__ == "__main__":
    main()