#!/usr/bin/env python3
"""
Demo script for color effects implementation.

This script demonstrates the color effects system including:
- Rainbow cycling effects
- Pulse animations with BPM synchronization
- Strobe effects with different patterns
- Color temperature shift effects

The demo shows how to create, configure, and apply color effects
to text elements with real-time parameter adjustment.
"""

import time
import math
from typing import List, Tuple

from src.effects.color_effects import (
    ColorEffectProcessor, RainbowEffect, PulseEffect, StrobeEffect,
    ColorTemperatureEffect
)
from src.core.models import ColorEffect, TextElement


def create_sample_text_element() -> TextElement:
    """Create a sample text element for testing."""
    return TextElement(
        content="KARAOKE DEMO",
        font_family="Arial",
        font_size=48.0,
        color=(1.0, 1.0, 1.0, 1.0),  # White
        position=(100.0, 100.0),
        rotation=(0.0, 0.0, 0.0),
        effects=[]
    )


def format_color(color: Tuple[float, float, float, float]) -> str:
    """Format RGBA color for display."""
    r, g, b, a = color
    return f"RGBA({r:.3f}, {g:.3f}, {b:.3f}, {a:.3f})"


def demo_rainbow_effect():
    """Demonstrate rainbow cycling effect."""
    print("\n" + "="*60)
    print("RAINBOW EFFECT DEMO")
    print("="*60)
    
    processor = ColorEffectProcessor()
    text_element = create_sample_text_element()
    
    # Create rainbow effect
    rainbow_config = processor.create_rainbow_effect(
        speed=1.0,      # 1 cycle per second
        intensity=1.0   # Full intensity
    )
    
    print(f"Original color: {format_color(text_element.color)}")
    print("\nRainbow cycling over time:")
    
    # Simulate time progression
    for i in range(8):
        current_time = i * 0.125  # 8 steps over 1 second
        
        result_color = processor.apply_color_effects(
            text_element, [rainbow_config], current_time
        )
        
        print(f"Time {current_time:.3f}s: {format_color(result_color)}")
    
    # Test with different intensities
    print("\nRainbow effect with different intensities:")
    for intensity in [0.25, 0.5, 0.75, 1.0]:
        rainbow_config.intensity = intensity
        result_color = processor.apply_color_effects(
            text_element, [rainbow_config], 0.25  # Quarter cycle
        )
        print(f"Intensity {intensity}: {format_color(result_color)}")


def demo_pulse_effect():
    """Demonstrate pulse effect."""
    print("\n" + "="*60)
    print("PULSE EFFECT DEMO")
    print("="*60)
    
    processor = ColorEffectProcessor()
    text_element = create_sample_text_element()
    text_element.color = (1.0, 0.0, 0.0, 1.0)  # Red base
    
    # Create pulse effect
    pulse_config = processor.create_pulse_effect(
        speed=2.0,      # 2 pulses per second
        intensity=1.0
    )
    
    # Create the effect and set pulse color
    pulse_effect = processor.create_effect(pulse_config)
    pulse_effect.set_pulse_color((0.0, 1.0, 0.0, 1.0))  # Green pulse
    
    print(f"Base color: {format_color(text_element.color)}")
    print(f"Pulse color: {format_color((0.0, 1.0, 0.0, 1.0))}")
    print("\nPulse animation over time:")
    
    # Simulate pulse cycle
    for i in range(8):
        current_time = i * 0.125  # 8 steps over 1 second
        
        result_color = pulse_effect.calculate_color(current_time, text_element.color)
        
        print(f"Time {current_time:.3f}s: {format_color(result_color)}")
    
    # Test different pulse curves
    print("\nPulse effect with different curves (at peak time):")
    for curve in ['sine', 'triangle', 'square']:
        pulse_effect.set_pulse_curve(curve)
        result_color = pulse_effect.calculate_color(0.125, text_element.color)  # Peak
        print(f"Curve '{curve}': {format_color(result_color)}")


def demo_bpm_synchronization():
    """Demonstrate BPM synchronization."""
    print("\n" + "="*60)
    print("BPM SYNCHRONIZATION DEMO")
    print("="*60)
    
    processor = ColorEffectProcessor()
    text_element = create_sample_text_element()
    
    # Create BPM-synchronized pulse effect
    bpm_pulse = processor.create_pulse_effect(
        speed=1.0,      # 1 pulse per beat
        intensity=1.0,
        bpm_sync=True,
        bpm=120.0       # 120 BPM = 2 beats per second
    )
    
    print(f"BPM: {bpm_pulse.bpm}")
    print(f"Beats per second: {bpm_pulse.bpm / 60.0}")
    print("\nBPM-synchronized pulse:")
    
    # Simulate time with BPM sync
    for i in range(6):
        current_time = i * 0.25  # Quarter-second intervals
        beats = current_time * (bpm_pulse.bpm / 60.0)
        
        result_color = processor.apply_color_effects(
            text_element, [bpm_pulse], current_time
        )
        
        print(f"Time {current_time:.2f}s (Beat {beats:.2f}): {format_color(result_color)}")


def demo_strobe_effect():
    """Demonstrate strobe effect."""
    print("\n" + "="*60)
    print("STROBE EFFECT DEMO")
    print("="*60)
    
    processor = ColorEffectProcessor()
    text_element = create_sample_text_element()
    text_element.color = (0.0, 0.0, 0.0, 1.0)  # Black base
    
    # Create strobe effect
    strobe_config = processor.create_strobe_effect(
        speed=4.0,      # 4 flashes per second
        intensity=1.0
    )
    
    strobe_effect = processor.create_effect(strobe_config)
    strobe_effect.set_strobe_color((1.0, 1.0, 1.0, 1.0))  # White flash
    strobe_effect.set_flash_duration(0.1)  # 100ms flashes
    
    print(f"Base color: {format_color(text_element.color)}")
    print(f"Strobe color: {format_color((1.0, 1.0, 1.0, 1.0))}")
    print(f"Flash duration: 0.1s")
    print("\nStrobe pattern over time:")
    
    # Simulate strobe cycle
    for i in range(16):
        current_time = i * 0.0625  # 16 steps over 1 second
        
        result_color = strobe_effect.calculate_color(current_time, text_element.color)
        flash_status = "FLASH" if result_color != text_element.color else "OFF"
        
        print(f"Time {current_time:.4f}s: {format_color(result_color)} [{flash_status}]")
    
    # Test different strobe patterns
    print("\nDifferent strobe patterns (at flash time):")
    for pattern in ['single', 'double', 'triple']:
        strobe_effect.set_pattern(pattern)
        result_color = strobe_effect.calculate_color(0.05, text_element.color)
        print(f"Pattern '{pattern}': {format_color(result_color)}")


def demo_temperature_effect():
    """Demonstrate color temperature effect."""
    print("\n" + "="*60)
    print("COLOR TEMPERATURE EFFECT DEMO")
    print("="*60)
    
    processor = ColorEffectProcessor()
    text_element = create_sample_text_element()
    
    # Create temperature effect
    temp_config = processor.create_temperature_effect(
        speed=0.5,      # Half cycle per second
        intensity=1.0
    )
    
    temp_effect = processor.create_effect(temp_config)
    temp_effect.set_temperature_range(2000, 8000)  # Warm to cool
    
    print(f"Base color: {format_color(text_element.color)}")
    print(f"Temperature range: 2000K (warm) to 8000K (cool)")
    print("\nTemperature shift over time:")
    
    # Simulate temperature cycle
    for i in range(8):
        current_time = i * 0.25  # 8 steps over 2 seconds
        
        result_color = temp_effect.calculate_color(current_time, text_element.color)
        
        # Calculate approximate temperature for display
        cycle_progress = (current_time * temp_effect.config.speed) % 1.0
        temp_factor = (math.sin(cycle_progress * 2 * math.pi) + 1.0) / 2.0
        approx_temp = 2000 + (8000 - 2000) * temp_factor
        
        print(f"Time {current_time:.2f}s (~{approx_temp:.0f}K): {format_color(result_color)}")
    
    # Test different transition curves
    print("\nTemperature effect with different curves:")
    for curve in ['sine', 'linear', 'ease_in_out']:
        temp_effect.set_transition_curve(curve)
        result_color = temp_effect.calculate_color(0.5, text_element.color)
        print(f"Curve '{curve}': {format_color(result_color)}")


def demo_combined_effects():
    """Demonstrate combining multiple color effects."""
    print("\n" + "="*60)
    print("COMBINED EFFECTS DEMO")
    print("="*60)
    
    processor = ColorEffectProcessor()
    text_element = create_sample_text_element()
    
    # Create multiple effects
    effects = [
        processor.create_rainbow_effect(speed=0.5, intensity=0.7),
        processor.create_pulse_effect(speed=3.0, intensity=0.3)
    ]
    
    print(f"Base color: {format_color(text_element.color)}")
    print("Effects: Rainbow (70% intensity) + Pulse (30% intensity)")
    print("\nCombined effects over time:")
    
    # Simulate combined effects
    for i in range(8):
        current_time = i * 0.25
        
        result_color = processor.apply_color_effects(
            text_element, effects, current_time
        )
        
        print(f"Time {current_time:.2f}s: {format_color(result_color)}")


def demo_real_time_parameters():
    """Demonstrate real-time parameter updates."""
    print("\n" + "="*60)
    print("REAL-TIME PARAMETER UPDATES DEMO")
    print("="*60)
    
    processor = ColorEffectProcessor()
    text_element = create_sample_text_element()
    
    # Create effect and store in processor
    rainbow_config = processor.create_rainbow_effect(speed=1.0, intensity=1.0)
    effect = processor.create_effect(rainbow_config)
    effect_id = "rainbow_demo"
    processor._active_effects[effect_id] = effect
    
    print("Demonstrating real-time parameter changes:")
    
    # Test different speeds
    for speed in [0.5, 1.0, 2.0, 4.0]:
        processor.update_effect_parameters(effect_id, {'speed': speed})
        result_color = processor.apply_color_effects(
            text_element, [rainbow_config], 0.25
        )
        print(f"Speed {speed}: {format_color(result_color)}")
    
    # Test different intensities
    print("\nIntensity changes:")
    for intensity in [0.25, 0.5, 0.75, 1.0]:
        processor.update_effect_parameters(effect_id, {'intensity': intensity})
        result_color = processor.apply_color_effects(
            text_element, [rainbow_config], 0.25
        )
        print(f"Intensity {intensity}: {format_color(result_color)}")


def main():
    """Run all color effects demos."""
    print("COLOR EFFECTS SYSTEM DEMO")
    print("This demo showcases the color effects implementation for karaoke subtitles.")
    
    try:
        demo_rainbow_effect()
        demo_pulse_effect()
        demo_bpm_synchronization()
        demo_strobe_effect()
        demo_temperature_effect()
        demo_combined_effects()
        demo_real_time_parameters()
        
        print("\n" + "="*60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nColor effects system features demonstrated:")
        print("✓ Rainbow cycling with HSV color space")
        print("✓ Pulse animations with multiple curve types")
        print("✓ BPM synchronization for music-responsive effects")
        print("✓ Strobe effects with configurable patterns")
        print("✓ Color temperature shifting")
        print("✓ Multiple effects combination")
        print("✓ Real-time parameter adjustment")
        print("\nAll effects support:")
        print("- Configurable speed and intensity")
        print("- BPM synchronization for audio sync")
        print("- Real-time parameter updates")
        print("- Smooth color transitions")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())