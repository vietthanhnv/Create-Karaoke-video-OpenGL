#!/usr/bin/env python3
"""
Demo script for animation effects system.

This script demonstrates the basic text animation effects including:
- Fade in/out animations
- Slide transitions
- Typewriter effect
- Bounce animations

Run this script to see the animation effects in action.
"""

import time
from src.effects.animation_effects import AnimationEffectProcessor
from src.core.models import (
    AnimationEffect, AnimationType, EasingType, TextElement
)


def demo_fade_effects():
    """Demonstrate fade animation effects."""
    print("=== Fade Effects Demo ===")
    
    processor = AnimationEffectProcessor()
    
    # Create sample text element
    text_element = TextElement(
        content="Fade Animation Demo",
        font_family="Arial",
        font_size=24.0,
        color=(1.0, 1.0, 1.0, 1.0),
        position=(100.0, 200.0),
        rotation=(0.0, 0.0, 0.0),
        effects=[]
    )
    
    # Create fade in effect
    fade_in_config = AnimationEffect(
        type=AnimationType.FADE_IN,
        duration=2.0,
        parameters={'fade_type': 'in', 'start_alpha': 0.0, 'end_alpha': 1.0},
        easing_curve=EasingType.EASE_OUT
    )
    
    print("Fade In Animation:")
    for i in range(11):
        current_time = i * 0.2  # 0.0 to 2.0 seconds
        properties = processor.apply_animation_effects(
            text_element, [fade_in_config], current_time, 0.0
        )
        
        alpha = properties.get('alpha', 1.0)
        progress = (current_time / 2.0) * 100
        print(f"  Time: {current_time:.1f}s, Progress: {progress:5.1f}%, Alpha: {alpha:.3f}")
    
    print()


def demo_slide_effects():
    """Demonstrate slide animation effects."""
    print("=== Slide Effects Demo ===")
    
    processor = AnimationEffectProcessor()
    
    text_element = TextElement(
        content="Slide Animation Demo",
        font_family="Arial",
        font_size=20.0,
        color=(0.0, 1.0, 0.0, 1.0),
        position=(200.0, 300.0),
        rotation=(0.0, 0.0, 0.0),
        effects=[]
    )
    
    # Create slide left effect
    slide_config = AnimationEffect(
        type=AnimationType.SLIDE_LEFT,
        duration=1.5,
        parameters={'direction': 'left', 'distance': 150.0, 'slide_type': 'in'},
        easing_curve=EasingType.EASE_IN_OUT
    )
    
    print("Slide Left In Animation:")
    original_x = text_element.position[0]
    
    for i in range(8):
        current_time = i * 0.2  # 0.0 to 1.4 seconds
        properties = processor.apply_animation_effects(
            text_element, [slide_config], current_time, 0.0
        )
        
        if 'position' in properties:
            new_x = properties['position'][0]
            offset = new_x - original_x
            progress = (current_time / 1.5) * 100
            print(f"  Time: {current_time:.1f}s, Progress: {progress:5.1f}%, X: {new_x:.1f}, Offset: {offset:+.1f}")
    
    print()


def demo_typewriter_effect():
    """Demonstrate typewriter animation effect."""
    print("=== Typewriter Effect Demo ===")
    
    processor = AnimationEffectProcessor()
    
    text_element = TextElement(
        content="Hello, World! This is a typewriter effect demonstration.",
        font_family="Courier New",
        font_size=16.0,
        color=(1.0, 1.0, 0.0, 1.0),
        position=(50.0, 100.0),
        rotation=(0.0, 0.0, 0.0),
        effects=[]
    )
    
    # Create typewriter effect
    typewriter_config = AnimationEffect(
        type=AnimationType.TYPEWRITER,
        duration=4.0,
        parameters={
            'show_cursor': True,
            'cursor_char': '|',
            'cursor_blink_rate': 2.0,
            'typing_speed': 'linear'
        },
        easing_curve=EasingType.LINEAR
    )
    
    print("Typewriter Animation:")
    total_chars = len(text_element.content)
    
    for i in range(21):
        current_time = i * 0.2  # 0.0 to 4.0 seconds
        properties = processor.apply_animation_effects(
            text_element, [typewriter_config], current_time, 0.0
        )
        
        if 'content' in properties:
            visible_text = properties['content']
            visible_chars = properties.get('visible_chars', 0)
            progress = (visible_chars / total_chars) * 100
            
            # Truncate long text for display
            display_text = visible_text[:30] + "..." if len(visible_text) > 30 else visible_text
            print(f"  Time: {current_time:.1f}s, Progress: {progress:5.1f}%, Text: '{display_text}'")
    
    print()


def demo_bounce_effect():
    """Demonstrate bounce animation effect."""
    print("=== Bounce Effect Demo ===")
    
    processor = AnimationEffectProcessor()
    
    text_element = TextElement(
        content="BOUNCE!",
        font_family="Arial Black",
        font_size=32.0,
        color=(1.0, 0.0, 1.0, 1.0),
        position=(150.0, 250.0),
        rotation=(0.0, 0.0, 0.0),
        effects=[]
    )
    
    # Create bounce effect
    bounce_config = AnimationEffect(
        type=AnimationType.BOUNCE,
        duration=3.0,
        parameters={
            'bounce_height': 80.0,
            'gravity': 980.0,
            'damping': 0.7,
            'bounce_count': 4,
            'direction': 'vertical'
        },
        easing_curve=EasingType.LINEAR
    )
    
    print("Bounce Animation:")
    original_y = text_element.position[1]
    
    for i in range(16):
        current_time = i * 0.2  # 0.0 to 3.0 seconds
        properties = processor.apply_animation_effects(
            text_element, [bounce_config], current_time, 0.0
        )
        
        if 'position' in properties:
            new_y = properties['position'][1]
            offset_y = properties.get('offset_y', 0.0)
            bounce_height = properties.get('bounce_height', 0.0)
            progress = (current_time / 3.0) * 100
            
            print(f"  Time: {current_time:.1f}s, Progress: {progress:5.1f}%, Y: {new_y:.1f}, "
                  f"Offset: {offset_y:+.1f}, Bounce: {bounce_height:.1f}")
    
    print()


def demo_combined_effects():
    """Demonstrate combining multiple animation effects."""
    print("=== Combined Effects Demo ===")
    
    processor = AnimationEffectProcessor()
    
    text_element = TextElement(
        content="Combined Animation",
        font_family="Arial",
        font_size=28.0,
        color=(0.5, 0.5, 1.0, 1.0),
        position=(100.0, 200.0),
        rotation=(0.0, 0.0, 0.0),
        effects=[]
    )
    
    # Create multiple effects
    fade_config = AnimationEffect(
        type=AnimationType.FADE_IN,
        duration=2.0,
        parameters={'fade_type': 'in'},
        easing_curve=EasingType.EASE_OUT
    )
    
    slide_config = AnimationEffect(
        type=AnimationType.SLIDE_UP,
        duration=2.0,
        parameters={'direction': 'up', 'distance': 50.0, 'slide_type': 'in'},
        easing_curve=EasingType.EASE_OUT
    )
    
    print("Combined Fade In + Slide Up Animation:")
    
    for i in range(11):
        current_time = i * 0.2  # 0.0 to 2.0 seconds
        properties = processor.apply_animation_effects(
            text_element, [fade_config, slide_config], current_time, 0.0
        )
        
        alpha = properties.get('alpha', 1.0)
        position = properties.get('position', text_element.position)
        offset_y = properties.get('offset_y', 0.0)
        progress = (current_time / 2.0) * 100
        
        print(f"  Time: {current_time:.1f}s, Progress: {progress:5.1f}%, "
              f"Alpha: {alpha:.3f}, Y: {position[1]:.1f}, Offset: {offset_y:+.1f}")
    
    print()


def demo_real_time_parameter_updates():
    """Demonstrate real-time parameter updates."""
    print("=== Real-time Parameter Updates Demo ===")
    
    processor = AnimationEffectProcessor()
    
    # Original effect configuration
    original_config = AnimationEffect(
        type=AnimationType.FADE_IN,
        duration=2.0,
        parameters={'fade_type': 'in'},
        easing_curve=EasingType.LINEAR
    )
    
    print("Original Configuration:")
    print(f"  Duration: {original_config.duration}s")
    print(f"  Easing: {original_config.easing_curve.value}")
    print(f"  Parameters: {original_config.parameters}")
    
    # Update parameters
    parameter_updates = {
        'duration': 3.0,
        'fade_type': 'in_out',
        'easing_curve': EasingType.BOUNCE,
        'start_alpha': 0.2,
        'end_alpha': 0.9
    }
    
    updated_config = processor.update_effect_parameters(original_config, parameter_updates)
    
    print("\nUpdated Configuration:")
    print(f"  Duration: {updated_config.duration}s")
    print(f"  Easing: {updated_config.easing_curve.value}")
    print(f"  Parameters: {updated_config.parameters}")
    
    print()


def demo_supported_effects():
    """Show all supported animation effect types."""
    print("=== Supported Animation Effects ===")
    
    processor = AnimationEffectProcessor()
    supported_types = processor.get_supported_effect_types()
    
    print("Available Animation Types:")
    for effect_type in supported_types:
        parameters = processor.get_effect_parameters(effect_type)
        print(f"  - {effect_type.value}")
        if parameters:
            print(f"    Default parameters: {parameters}")
    
    print()


def main():
    """Run all animation effect demonstrations."""
    print("Animation Effects System Demo")
    print("=" * 50)
    print()
    
    try:
        demo_supported_effects()
        demo_fade_effects()
        demo_slide_effects()
        demo_typewriter_effect()
        demo_bounce_effect()
        demo_combined_effects()
        demo_real_time_parameter_updates()
        
        print("Demo completed successfully!")
        print("\nThe animation effects system supports:")
        print("✓ Fade in/out animations with customizable alpha ranges")
        print("✓ Slide transitions in all directions with distance control")
        print("✓ Typewriter effect with cursor and typing speed options")
        print("✓ Physics-based bounce animations with gravity and damping")
        print("✓ Keyframe-based interpolation with multiple easing curves")
        print("✓ Real-time parameter adjustment during animation")
        print("✓ Combining multiple effects on the same text element")
        
    except Exception as e:
        print(f"Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()