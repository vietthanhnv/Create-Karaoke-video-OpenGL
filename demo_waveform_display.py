#!/usr/bin/env python3
"""
Demo script for audio waveform generation and display functionality.

This script demonstrates:
- Audio waveform generation with fallback mode
- Waveform data caching and processing
- Timeline integration with waveform display
- Waveform rendering and visualization
"""

import sys
import numpy as np
from src.core.models import AudioAsset, ValidationResult
from src.audio.waveform_generator import WaveformGenerator, WaveformRenderer
from src.core.timeline_engine import TimelineEngine


def create_mock_audio_asset(duration: float = 30.0) -> AudioAsset:
    """Create a mock audio asset for demonstration."""
    audio_asset = AudioAsset(
        path="/demo/sample_audio.mp3",
        duration=duration,
        sample_rate=44100,
        channels=2,
        format=".mp3"
    )
    
    # Mock the validation to always pass for demo
    def mock_validate():
        return ValidationResult(is_valid=True)
    
    audio_asset.validate = mock_validate
    return audio_asset


def demo_waveform_generation():
    """Demonstrate waveform generation capabilities."""
    print("=== Audio Waveform Generation Demo ===\n")
    
    # Create mock audio asset
    audio_asset = create_mock_audio_asset(duration=15.0)
    print(f"Created mock audio asset:")
    print(f"  Path: {audio_asset.path}")
    print(f"  Duration: {audio_asset.duration}s")
    print(f"  Sample Rate: {audio_asset.sample_rate} Hz")
    print(f"  Channels: {audio_asset.channels}")
    
    # Create waveform generator
    generator = WaveformGenerator()
    generator._ffmpeg_available = False  # Use fallback for demo
    
    print(f"\nFFmpeg available: {generator.is_ffmpeg_available()}")
    print("Using fallback waveform generation for demo...")
    
    # Generate waveform data
    print("\nGenerating waveform data...")
    waveform_data = generator.generate_waveform(audio_asset, resolution=1000)
    
    print(f"Generated waveform:")
    print(f"  Resolution: {waveform_data.resolution} samples")
    print(f"  Duration: {waveform_data.duration}s")
    print(f"  Sample Rate: {waveform_data.sample_rate} samples/second")
    print(f"  Channels: {waveform_data.channels}")
    print(f"  Amplitude Range: [{np.min(waveform_data.samples):.3f}, {np.max(waveform_data.samples):.3f}]")
    
    # Test waveform segment extraction
    print("\nExtracting waveform segment (5s to 10s)...")
    segment = generator.get_waveform_segment(waveform_data, 5.0, 10.0)
    print(f"Segment length: {len(segment)} samples")
    print(f"Segment amplitude range: [{np.min(segment):.3f}, {np.max(segment):.3f}]")
    
    # Test peak levels
    print("\nExtracting peak levels...")
    peaks = generator.get_peak_levels(waveform_data, num_peaks=20)
    print(f"Generated {len(peaks)} peak pairs")
    print(f"First few peaks: {peaks[:5]}")
    
    # Test resampling
    print("\nResampling waveform to different resolution...")
    resampled = generator.resample_waveform(waveform_data, 500)
    print(f"Resampled resolution: {resampled.resolution}")
    print(f"Resampled sample rate: {resampled.sample_rate} samples/second")
    
    return waveform_data


def demo_waveform_rendering(waveform_data):
    """Demonstrate waveform rendering capabilities."""
    print("\n=== Waveform Rendering Demo ===\n")
    
    # Create waveform renderer
    renderer = WaveformRenderer()
    
    print("Default renderer colors:")
    print(f"  Background: {renderer.background_color}")
    print(f"  Waveform: {renderer.waveform_color}")
    print(f"  Center Line: {renderer.center_line_color}")
    print(f"  Peak: {renderer.peak_color}")
    
    # Render full waveform
    print("\nRendering full waveform (800x200)...")
    full_render = renderer.render_waveform_data(waveform_data, 800, 200)
    print(f"Rendered image shape: {full_render.shape}")
    print(f"Image data type: {full_render.dtype}")
    print(f"Pixel value range: [{np.min(full_render):.3f}, {np.max(full_render):.3f}]")
    
    # Render waveform segment
    print("\nRendering waveform segment (3s to 8s, 400x100)...")
    segment_render = renderer.render_waveform_data(
        waveform_data, 400, 100, start_time=3.0, end_time=8.0
    )
    print(f"Segment image shape: {segment_render.shape}")
    
    # Test custom colors
    print("\nTesting custom colors...")
    renderer.set_colors(
        background=(0.05, 0.05, 0.1, 1.0),  # Dark blue
        waveform=(0.2, 0.8, 0.2, 0.9),      # Green
        peak=(1.0, 0.2, 0.2, 1.0)           # Red
    )
    
    custom_render = renderer.render_waveform_data(waveform_data, 400, 100)
    print(f"Custom colored render shape: {custom_render.shape}")
    
    return full_render


def demo_timeline_integration():
    """Demonstrate timeline engine integration with waveform."""
    print("\n=== Timeline Integration Demo ===\n")
    
    # Create audio asset and timeline
    audio_asset = create_mock_audio_asset(duration=20.0)
    timeline = TimelineEngine()
    
    # Force fallback mode for consistent demo
    timeline._waveform_generator._ffmpeg_available = False
    
    print("Setting audio asset on timeline...")
    timeline.audio_asset = audio_asset
    
    # Get waveform data through timeline
    print("Getting waveform data through timeline...")
    waveform_data = timeline.get_waveform_data(resolution=800)
    
    if waveform_data:
        print(f"Timeline waveform data:")
        print(f"  Resolution: {waveform_data.resolution}")
        print(f"  Duration: {waveform_data.duration}s")
        
        # Test waveform segment extraction through timeline
        print("\nExtracting segment through timeline (2s to 6s)...")
        segment = timeline.get_waveform_segment(2.0, 6.0, resolution=400)
        
        if segment is not None:
            print(f"Timeline segment length: {len(segment)}")
            print(f"Segment stats: mean={np.mean(segment):.3f}, std={np.std(segment):.3f}")
        
        # Test peak levels through timeline
        print("\nGetting peak levels through timeline...")
        peaks = timeline.get_waveform_peaks(num_peaks=50)
        
        if peaks:
            print(f"Timeline peaks count: {len(peaks)}")
            max_peak = max(max(abs(min_val), abs(max_val)) for min_val, max_val in peaks)
            print(f"Maximum peak amplitude: {max_peak:.3f}")
    else:
        print("No waveform data available from timeline")
    
    # Test timeline playback simulation
    print("\nSimulating timeline playback...")
    timeline.current_time = 0.0
    timeline.play()
    
    for i in range(5):
        timeline.update(1.0)  # Simulate 1 second updates
        print(f"  Time: {timeline.current_time:.1f}s, Playing: {timeline.is_playing()}")
    
    timeline.pause()
    print(f"Paused at: {timeline.current_time:.1f}s")


def demo_waveform_caching():
    """Demonstrate waveform caching functionality."""
    print("\n=== Waveform Caching Demo ===\n")
    
    generator = WaveformGenerator()
    generator._ffmpeg_available = False  # Use fallback
    
    # Check initial cache state
    cache_info = generator.get_cache_info()
    print(f"Initial cache state: {cache_info}")
    
    # Generate multiple waveforms
    audio1 = create_mock_audio_asset(duration=10.0)
    audio2 = create_mock_audio_asset(duration=15.0)
    
    print("\nGenerating first waveform...")
    waveform1 = generator.generate_waveform(audio1, resolution=500)
    cache_info = generator.get_cache_info()
    print(f"Cache after first generation: {cache_info}")
    
    print("\nGenerating second waveform...")
    waveform2 = generator.generate_waveform(audio2, resolution=1000)
    cache_info = generator.get_cache_info()
    print(f"Cache after second generation: {cache_info}")
    
    print("\nRe-generating first waveform (should use cache)...")
    waveform1_cached = generator.generate_waveform(audio1, resolution=500)
    cache_info = generator.get_cache_info()
    print(f"Cache after cached access: {cache_info}")
    print(f"Same object returned: {waveform1 is waveform1_cached}")
    
    print("\nClearing cache...")
    generator.clear_cache()
    cache_info = generator.get_cache_info()
    print(f"Cache after clearing: {cache_info}")


def demo_performance_analysis():
    """Demonstrate performance characteristics of waveform processing."""
    print("\n=== Performance Analysis Demo ===\n")
    
    import time
    
    generator = WaveformGenerator()
    generator._ffmpeg_available = False  # Use fallback for consistent timing
    
    # Test different resolutions
    resolutions = [100, 500, 1000, 2000, 5000]
    audio_asset = create_mock_audio_asset(duration=60.0)  # 1 minute audio
    
    print("Testing waveform generation performance:")
    print("Resolution | Time (ms) | Samples/ms")
    print("-" * 40)
    
    for resolution in resolutions:
        start_time = time.time()
        waveform_data = generator.generate_waveform(audio_asset, resolution)
        end_time = time.time()
        
        duration_ms = (end_time - start_time) * 1000
        samples_per_ms = resolution / duration_ms if duration_ms > 0 else 0
        
        print(f"{resolution:>10} | {duration_ms:>8.2f} | {samples_per_ms:>10.1f}")
    
    # Test rendering performance
    print("\nTesting waveform rendering performance:")
    print("Size       | Time (ms) | Pixels/ms")
    print("-" * 40)
    
    waveform_data = generator.generate_waveform(audio_asset, resolution=2000)
    renderer = WaveformRenderer()
    
    sizes = [(400, 100), (800, 200), (1200, 300), (1600, 400)]
    
    for width, height in sizes:
        start_time = time.time()
        rendered = renderer.render_waveform_data(waveform_data, width, height)
        end_time = time.time()
        
        duration_ms = (end_time - start_time) * 1000
        pixels = width * height
        pixels_per_ms = pixels / duration_ms if duration_ms > 0 else 0
        
        print(f"{width}x{height:>6} | {duration_ms:>8.2f} | {pixels_per_ms:>10.0f}")


def main():
    """Run all waveform demos."""
    print("Audio Waveform Generation and Display Demo")
    print("=" * 50)
    
    try:
        # Run all demos
        waveform_data = demo_waveform_generation()
        demo_waveform_rendering(waveform_data)
        demo_timeline_integration()
        demo_waveform_caching()
        demo_performance_analysis()
        
        print("\n" + "=" * 50)
        print("Demo completed successfully!")
        print("\nKey features demonstrated:")
        print("✓ Audio waveform generation with fallback mode")
        print("✓ Waveform data caching and reuse")
        print("✓ Segment extraction and peak analysis")
        print("✓ Waveform rendering with customizable colors")
        print("✓ Timeline engine integration")
        print("✓ Performance characteristics")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())