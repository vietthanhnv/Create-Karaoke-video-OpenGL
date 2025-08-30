#!/usr/bin/env python3
"""
Demo script showing the timeline engine functionality.
"""

from datetime import datetime
from src.core.timeline_engine import TimelineEngine
from src.core.keyframe_system import KeyframeSystem
from src.core.models import (
    VideoAsset, AudioAsset, SubtitleTrack, TextElement, Keyframe,
    InterpolationType, EasingType, ExportSettings
)


def main():
    """Demonstrate timeline engine functionality."""
    print("=== Karaoke Subtitle Creator - Timeline Engine Demo ===\n")
    
    # Create a sample video asset
    video_asset = VideoAsset(
        path="sample_video.mp4",
        duration=30.0,  # 30 seconds
        fps=30.0,
        resolution=(1920, 1080),
        codec="h264"
    )
    
    # Create timeline engine
    timeline = TimelineEngine(video_asset)
    print(f"Timeline created with duration: {timeline.duration} seconds")
    print(f"Video FPS: {video_asset.fps}")
    
    # Create a subtitle track
    text_element = TextElement(
        content="Hello Karaoke World!",
        font_family="Arial",
        font_size=48.0,
        color=(1.0, 1.0, 1.0, 1.0),  # White
        position=(960.0, 540.0),     # Center of 1920x1080
        rotation=(0.0, 0.0, 0.0),
        effects=[]
    )
    
    subtitle_track = SubtitleTrack(
        id="main_lyrics",
        elements=[text_element],
        keyframes=[],
        start_time=5.0,   # Start at 5 seconds
        end_time=25.0     # End at 25 seconds
    )
    
    timeline.add_subtitle_track(subtitle_track)
    print(f"Added subtitle track: {subtitle_track.id}")
    
    # Add keyframes for animation
    print("\nAdding keyframes for text animation...")
    
    # Fade in animation (5-7 seconds)
    timeline.add_keyframe("main_lyrics", 5.0, {
        "opacity": 0.0,
        "scale": 0.8,
        "position": (960.0, 600.0)
    })
    
    timeline.add_keyframe("main_lyrics", 7.0, {
        "opacity": 1.0,
        "scale": 1.0,
        "position": (960.0, 540.0)
    })
    
    # Highlight effect (10-12 seconds)
    timeline.add_keyframe("main_lyrics", 10.0, {
        "opacity": 1.0,
        "scale": 1.0,
        "color": (1.0, 1.0, 1.0, 1.0)  # White
    })
    
    timeline.add_keyframe("main_lyrics", 12.0, {
        "opacity": 1.0,
        "scale": 1.2,
        "color": (1.0, 1.0, 0.0, 1.0)  # Yellow highlight
    })
    
    # Fade out animation (23-25 seconds)
    timeline.add_keyframe("main_lyrics", 23.0, {
        "opacity": 1.0,
        "scale": 1.0,
        "position": (960.0, 540.0)
    })
    
    timeline.add_keyframe("main_lyrics", 25.0, {
        "opacity": 0.0,
        "scale": 0.8,
        "position": (960.0, 480.0)
    })
    
    print("Keyframes added successfully!")
    
    # Demonstrate interpolation at different time points
    print("\n=== Timeline Interpolation Demo ===")
    
    test_times = [4.0, 6.0, 8.0, 11.0, 15.0, 24.0, 26.0]
    
    for time in test_times:
        properties = timeline.interpolate_properties("main_lyrics", time)
        active_elements = timeline.get_active_elements_at_time(time)
        
        print(f"\nTime: {time:4.1f}s")
        if active_elements:
            print(f"  Active tracks: {len(active_elements)}")
            if properties:
                opacity = properties.get("opacity", "N/A")
                scale = properties.get("scale", "N/A")
                position = properties.get("position", "N/A")
                print(f"  Opacity: {opacity}")
                print(f"  Scale: {scale}")
                print(f"  Position: {position}")
            else:
                print("  No interpolated properties")
        else:
            print("  No active elements")
    
    # Demonstrate playback simulation
    print("\n=== Playback Simulation ===")
    
    timeline.seek(5.0)  # Start at 5 seconds
    timeline.play()
    
    print("Simulating playback...")
    simulation_time = 0.0
    frame_time = 1.0 / 60.0  # 60 FPS simulation
    
    while timeline.is_playing() and simulation_time < 3.0:  # Simulate 3 seconds
        timeline.update(frame_time)
        simulation_time += frame_time
        
        # Print status every 0.5 seconds
        if int(simulation_time * 2) != int((simulation_time - frame_time) * 2):
            current_frame = timeline.get_frame_from_time(timeline.current_time)
            print(f"  Time: {timeline.current_time:5.2f}s, Frame: {current_frame:4d}")
    
    timeline.pause()
    print(f"Playback paused at: {timeline.current_time:.2f}s")
    
    # Demonstrate keyframe system
    print("\n=== Keyframe System Demo ===")
    
    keyframe_system = KeyframeSystem()
    
    # Create some test keyframes
    kf1 = keyframe_system.create_keyframe(0.0, {"value": 0.0})
    kf2 = keyframe_system.create_keyframe(2.0, {"value": 100.0})
    
    print("Testing different easing curves:")
    
    easing_types = [EasingType.LINEAR, EasingType.EASE_IN, EasingType.EASE_OUT, EasingType.BOUNCE]
    
    for easing in easing_types:
        result = keyframe_system.interpolate_between(kf1, kf2, 0.5, easing)
        print(f"  {easing.value:12s}: {result['value']:6.2f}")
    
    # Demonstrate keyframe manipulation
    print("\nKeyframe manipulation:")
    
    original_keyframes = [
        keyframe_system.create_keyframe(1.0, {"x": 10, "y": 20}),
        keyframe_system.create_keyframe(3.0, {"x": 30, "y": 40})
    ]
    
    # Copy and offset
    copied_keyframes = keyframe_system.copy_keyframes(original_keyframes)
    offset_keyframes = keyframe_system.offset_keyframes(copied_keyframes, 5.0)
    
    print(f"  Original times: {[kf.time for kf in original_keyframes]}")
    print(f"  Offset times:   {[kf.time for kf in offset_keyframes]}")
    
    # Scale timing
    scaled_keyframes = keyframe_system.scale_keyframes(original_keyframes, 2.0)
    print(f"  Scaled times:   {[kf.time for kf in scaled_keyframes]}")
    
    # Audio waveform demo (placeholder)
    print("\n=== Audio Waveform Demo ===")
    
    audio_asset = AudioAsset(
        path="sample_audio.mp3",
        duration=30.0,
        sample_rate=44100,
        channels=2,
        format="mp3"
    )
    
    timeline.audio_asset = audio_asset
    waveform = timeline.get_waveform_data(audio_asset, resolution=50)
    
    print(f"Generated waveform with {len(waveform)} samples")
    print(f"Waveform range: [{waveform.min():.3f}, {waveform.max():.3f}]")
    
    # Validation demo
    print("\n=== Validation Demo ===")
    
    validation = timeline.validate_timeline()
    if validation.is_valid:
        print("✓ Timeline validation passed")
    else:
        print(f"✗ Timeline validation failed: {validation.error_message}")
    
    if validation.warnings:
        print("Warnings:")
        for warning in validation.warnings:
            print(f"  - {warning}")
    
    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    main()