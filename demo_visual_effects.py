#!/usr/bin/env python3
"""
Demo script for visual effects system.

This script demonstrates the visual effects implementation including:
- Glow effects with configurable intensity and radius
- Outline/stroke rendering with width and color controls
- Drop shadow effects with offset and blur parameters
- Gradient fills (linear, radial, conic) with color stops

The demo creates various visual effects and shows how to configure
and apply them to text elements.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unittest.mock import Mock
from src.core.models import (
    VisualEffect, VisualEffectType, TextElement
)
from src.effects.visual_effects import (
    VisualEffectProcessor, GradientStop
)


def create_mock_shader_manager():
    """Create a mock shader manager for demonstration."""
    mock_shader = Mock()
    
    # Create a mock shader program object
    mock_program = Mock()
    mock_program.use.return_value = None
    mock_program.set_uniform.return_value = None
    
    mock_shader.load_shader_program.return_value = mock_program
    mock_shader.use_program.return_value = True
    mock_shader.set_uniform_vec4.return_value = None
    mock_shader.set_uniform_float.return_value = None
    mock_shader.set_uniform_vec2.return_value = None
    mock_shader.set_uniform_int.return_value = None
    return mock_shader


def create_sample_text_element():
    """Create a sample text element for demonstration."""
    return TextElement(
        content="KARAOKE",
        font_family="Arial",
        font_size=48.0,
        color=(1.0, 1.0, 1.0, 1.0),
        position=(400.0, 300.0),
        rotation=(0.0, 0.0, 0.0),
        effects=[]
    )


def demo_glow_effects():
    """Demonstrate glow effects with various configurations."""
    print("=== Glow Effects Demo ===")
    
    shader_manager = create_mock_shader_manager()
    processor = VisualEffectProcessor(shader_manager)
    text_element = create_sample_text_element()
    
    # Basic glow effect
    print("\n1. Basic Glow Effect:")
    glow_basic = processor.create_glow_effect(
        intensity=0.8,
        color=(1.0, 1.0, 0.0, 1.0),  # Yellow glow
        radius=8.0
    )
    print(f"   Type: {glow_basic.type.value}")
    print(f"   Intensity: {glow_basic.intensity}")
    print(f"   Color: {glow_basic.color}")
    print(f"   Radius: {glow_basic.parameters['radius']}")
    
    # Intense red glow
    print("\n2. Intense Red Glow:")
    glow_red = processor.create_glow_effect(
        intensity=1.0,
        color=(1.0, 0.2, 0.2, 1.0),  # Red glow
        radius=15.0
    )
    print(f"   Intensity: {glow_red.intensity}")
    print(f"   Color: {glow_red.color}")
    print(f"   Radius: {glow_red.parameters['radius']}")
    
    # Soft blue glow
    print("\n3. Soft Blue Glow:")
    glow_blue = processor.create_glow_effect(
        intensity=0.6,
        color=(0.2, 0.5, 1.0, 1.0),  # Blue glow
        radius=12.0
    )
    print(f"   Intensity: {glow_blue.intensity}")
    print(f"   Color: {glow_blue.color}")
    print(f"   Radius: {glow_blue.parameters['radius']}")
    
    # Apply glow effects
    effects = [glow_basic, glow_red, glow_blue]
    texture_size = (512, 128)
    
    print(f"\n4. Applying {len(effects)} glow effects to text element...")
    success = processor.apply_visual_effects(text_element, effects, texture_size)
    print(f"   Application successful: {success}")
    
    return processor, effects


def demo_outline_effects():
    """Demonstrate outline effects with various configurations."""
    print("\n=== Outline Effects Demo ===")
    
    shader_manager = create_mock_shader_manager()
    processor = VisualEffectProcessor(shader_manager)
    text_element = create_sample_text_element()
    
    # Basic black outline
    print("\n1. Basic Black Outline:")
    outline_basic = processor.create_outline_effect(
        intensity=1.0,
        color=(0.0, 0.0, 0.0, 1.0),  # Black outline
        width=2.0
    )
    print(f"   Type: {outline_basic.type.value}")
    print(f"   Color: {outline_basic.color}")
    print(f"   Width: {outline_basic.parameters['width']}")
    
    # Thick white outline
    print("\n2. Thick White Outline:")
    outline_white = processor.create_outline_effect(
        intensity=1.0,
        color=(1.0, 1.0, 1.0, 1.0),  # White outline
        width=4.0
    )
    print(f"   Color: {outline_white.color}")
    print(f"   Width: {outline_white.parameters['width']}")
    
    # Colored outline with custom parameters
    print("\n3. Custom Colored Outline:")
    outline_custom = VisualEffect(
        type=VisualEffectType.OUTLINE,
        intensity=0.8,
        color=(0.8, 0.2, 0.8, 1.0),  # Purple outline
        parameters={
            'width': 3.0,
            'mode': 'outer',
            'smoothness': 0.5
        }
    )
    print(f"   Color: {outline_custom.color}")
    print(f"   Width: {outline_custom.parameters['width']}")
    print(f"   Mode: {outline_custom.parameters['mode']}")
    print(f"   Smoothness: {outline_custom.parameters['smoothness']}")
    
    # Apply outline effects
    effects = [outline_basic, outline_white, outline_custom]
    texture_size = (512, 128)
    
    print(f"\n4. Applying {len(effects)} outline effects...")
    success = processor.apply_visual_effects(text_element, effects, texture_size)
    print(f"   Application successful: {success}")
    
    return processor, effects


def demo_shadow_effects():
    """Demonstrate shadow effects with various configurations."""
    print("\n=== Shadow Effects Demo ===")
    
    shader_manager = create_mock_shader_manager()
    processor = VisualEffectProcessor(shader_manager)
    text_element = create_sample_text_element()
    
    # Basic drop shadow
    print("\n1. Basic Drop Shadow:")
    shadow_basic = processor.create_shadow_effect(
        intensity=0.8,
        color=(0.0, 0.0, 0.0, 0.6),  # Semi-transparent black
        offset_x=4.0,
        offset_y=4.0,
        blur=2.0
    )
    print(f"   Type: {shadow_basic.type.value}")
    print(f"   Color: {shadow_basic.color}")
    print(f"   Offset: ({shadow_basic.parameters['offset_x']}, {shadow_basic.parameters['offset_y']})")
    print(f"   Blur: {shadow_basic.parameters['blur']}")
    
    # Long shadow
    print("\n2. Long Shadow:")
    shadow_long = processor.create_shadow_effect(
        intensity=0.7,
        color=(0.2, 0.2, 0.2, 0.5),
        offset_x=12.0,
        offset_y=8.0,
        blur=1.0
    )
    print(f"   Offset: ({shadow_long.parameters['offset_x']}, {shadow_long.parameters['offset_y']})")
    print(f"   Blur: {shadow_long.parameters['blur']}")
    
    # Soft blurred shadow
    print("\n3. Soft Blurred Shadow:")
    shadow_soft = processor.create_shadow_effect(
        intensity=0.6,
        color=(0.0, 0.0, 0.0, 0.4),
        offset_x=6.0,
        offset_y=6.0,
        blur=8.0
    )
    print(f"   Offset: ({shadow_soft.parameters['offset_x']}, {shadow_soft.parameters['offset_y']})")
    print(f"   Blur: {shadow_soft.parameters['blur']}")
    
    # Colored shadow
    print("\n4. Colored Shadow:")
    shadow_colored = VisualEffect(
        type=VisualEffectType.SHADOW,
        intensity=0.9,
        color=(0.5, 0.0, 0.5, 0.7),  # Purple shadow
        parameters={
            'offset_x': 3.0,
            'offset_y': 3.0,
            'blur': 4.0,
            'opacity': 0.8
        }
    )
    print(f"   Color: {shadow_colored.color}")
    print(f"   Opacity: {shadow_colored.parameters['opacity']}")
    
    # Apply shadow effects
    effects = [shadow_basic, shadow_long, shadow_soft, shadow_colored]
    texture_size = (512, 128)
    
    print(f"\n5. Applying {len(effects)} shadow effects...")
    success = processor.apply_visual_effects(text_element, effects, texture_size)
    print(f"   Application successful: {success}")
    
    return processor, effects


def demo_gradient_effects():
    """Demonstrate gradient effects with various configurations."""
    print("\n=== Gradient Effects Demo ===")
    
    shader_manager = create_mock_shader_manager()
    processor = VisualEffectProcessor(shader_manager)
    text_element = create_sample_text_element()
    
    # Linear gradient
    print("\n1. Linear Gradient (Red to Blue):")
    gradient_linear = processor.create_gradient_effect(
        intensity=1.0,
        gradient_type='linear',
        start_color=(1.0, 0.0, 0.0, 1.0),  # Red
        end_color=(0.0, 0.0, 1.0, 1.0),    # Blue
        angle=0.0
    )
    print(f"   Type: {gradient_linear.type.value}")
    print(f"   Gradient Type: {gradient_linear.parameters['type']}")
    print(f"   Start Color: {gradient_linear.parameters['start_color']}")
    print(f"   End Color: {gradient_linear.parameters['end_color']}")
    print(f"   Angle: {gradient_linear.parameters['angle']}°")
    
    # Diagonal linear gradient
    print("\n2. Diagonal Linear Gradient:")
    gradient_diagonal = processor.create_gradient_effect(
        intensity=1.0,
        gradient_type='linear',
        start_color=(1.0, 1.0, 0.0, 1.0),  # Yellow
        end_color=(1.0, 0.0, 1.0, 1.0),    # Magenta
        angle=45.0
    )
    print(f"   Start Color: {gradient_diagonal.parameters['start_color']}")
    print(f"   End Color: {gradient_diagonal.parameters['end_color']}")
    print(f"   Angle: {gradient_diagonal.parameters['angle']}°")
    
    # Radial gradient
    print("\n3. Radial Gradient:")
    gradient_radial = processor.create_gradient_effect(
        intensity=1.0,
        gradient_type='radial',
        start_color=(1.0, 1.0, 1.0, 1.0),  # White center
        end_color=(0.0, 0.0, 0.0, 1.0),    # Black edge
        angle=0.0
    )
    gradient_radial.parameters['center'] = (0.5, 0.5)
    gradient_radial.parameters['radius'] = 0.8
    print(f"   Gradient Type: {gradient_radial.parameters['type']}")
    print(f"   Center: {gradient_radial.parameters['center']}")
    print(f"   Radius: {gradient_radial.parameters['radius']}")
    
    # Conic gradient
    print("\n4. Conic Gradient:")
    gradient_conic = processor.create_gradient_effect(
        intensity=1.0,
        gradient_type='conic',
        start_color=(1.0, 0.0, 0.0, 1.0),  # Red
        end_color=(0.0, 1.0, 0.0, 1.0),    # Green
        angle=0.0
    )
    print(f"   Gradient Type: {gradient_conic.parameters['type']}")
    
    # Gradient with color stops
    print("\n5. Multi-Color Gradient with Stops:")
    gradient_multi = VisualEffect(
        type=VisualEffectType.GRADIENT,
        intensity=1.0,
        color=(1.0, 0.0, 0.0, 1.0),
        parameters={
            'type': 'linear',
            'start_color': (1.0, 0.0, 0.0, 1.0),  # Red
            'end_color': (0.0, 0.0, 1.0, 1.0),    # Blue
            'angle': 90.0,
            'color_stops': []
        }
    )
    
    # Create gradient effect to add color stops
    gradient_effect = processor.create_effect(gradient_multi)
    gradient_effect.add_color_stop(0.25, (1.0, 1.0, 0.0, 1.0))  # Yellow at 25%
    gradient_effect.add_color_stop(0.5, (0.0, 1.0, 0.0, 1.0))   # Green at 50%
    gradient_effect.add_color_stop(0.75, (0.0, 1.0, 1.0, 1.0))  # Cyan at 75%
    
    stops = gradient_effect.get_color_stops()
    print(f"   Color Stops: {len(stops)}")
    for i, stop in enumerate(stops):
        print(f"     Stop {i+1}: Position {stop.position}, Color {stop.color}")
    
    # Apply gradient effects
    effects = [gradient_linear, gradient_diagonal, gradient_radial, gradient_conic, gradient_multi]
    texture_size = (512, 128)
    
    print(f"\n6. Applying {len(effects)} gradient effects...")
    success = processor.apply_visual_effects(text_element, effects, texture_size)
    print(f"   Application successful: {success}")
    
    return processor, effects


def demo_combined_effects():
    """Demonstrate combining multiple visual effects."""
    print("\n=== Combined Effects Demo ===")
    
    shader_manager = create_mock_shader_manager()
    processor = VisualEffectProcessor(shader_manager)
    text_element = create_sample_text_element()
    
    print("\n1. Creating Combined Effect Stack:")
    
    # Create a stack of effects: gradient + glow + outline + shadow
    effects = []
    
    # Base gradient fill
    gradient = processor.create_gradient_effect(
        intensity=1.0,
        gradient_type='linear',
        start_color=(1.0, 0.8, 0.0, 1.0),  # Gold
        end_color=(1.0, 0.4, 0.0, 1.0),    # Orange
        angle=45.0
    )
    effects.append(gradient)
    print("   ✓ Added gradient fill (gold to orange)")
    
    # Glow effect
    glow = processor.create_glow_effect(
        intensity=0.8,
        color=(1.0, 1.0, 0.5, 1.0),  # Warm yellow glow
        radius=10.0
    )
    effects.append(glow)
    print("   ✓ Added glow effect (warm yellow)")
    
    # Outline effect
    outline = processor.create_outline_effect(
        intensity=1.0,
        color=(0.2, 0.1, 0.0, 1.0),  # Dark brown outline
        width=3.0
    )
    effects.append(outline)
    print("   ✓ Added outline effect (dark brown)")
    
    # Drop shadow
    shadow = processor.create_shadow_effect(
        intensity=0.7,
        color=(0.0, 0.0, 0.0, 0.5),
        offset_x=6.0,
        offset_y=6.0,
        blur=4.0
    )
    effects.append(shadow)
    print("   ✓ Added drop shadow")
    
    print(f"\n2. Effect Stack Summary:")
    for i, effect in enumerate(effects, 1):
        print(f"   Layer {i}: {effect.type.value.title()} Effect")
        print(f"            Intensity: {effect.intensity}")
        print(f"            Color: {effect.color}")
    
    # Apply combined effects
    texture_size = (512, 128)
    print(f"\n3. Applying {len(effects)} combined effects...")
    success = processor.apply_visual_effects(text_element, effects, texture_size)
    print(f"   Application successful: {success}")
    
    # Demonstrate real-time parameter updates
    print(f"\n4. Demonstrating Real-time Parameter Updates:")
    
    # Update glow intensity
    glow_id = f"glow_{id(glow)}"
    processor._active_effects[glow_id] = processor.create_effect(glow)
    
    update_success = processor.update_effect_parameters(glow_id, {
        'intensity': 1.0,
        'radius': 15.0
    })
    print(f"   Glow parameter update: {update_success}")
    
    # Update shadow offset
    shadow_id = f"shadow_{id(shadow)}"
    processor._active_effects[shadow_id] = processor.create_effect(shadow)
    
    update_success = processor.update_effect_parameters(shadow_id, {
        'offset_x': 8.0,
        'offset_y': 8.0,
        'blur': 6.0
    })
    print(f"   Shadow parameter update: {update_success}")
    
    return processor, effects


def demo_effect_parameters():
    """Demonstrate getting and setting effect parameters."""
    print("\n=== Effect Parameters Demo ===")
    
    shader_manager = create_mock_shader_manager()
    processor = VisualEffectProcessor(shader_manager)
    
    print("\n1. Supported Effect Types:")
    supported_types = processor.get_supported_effect_types()
    for effect_type in supported_types:
        print(f"   ✓ {effect_type.value.title()}")
    
    print("\n2. Default Parameters for Each Effect Type:")
    
    for effect_type in supported_types:
        print(f"\n   {effect_type.value.title()} Effect Parameters:")
        params = processor.get_effect_parameters(effect_type)
        for key, value in params.items():
            print(f"     {key}: {value}")
    
    print("\n3. Parameter Validation and Constraints:")
    
    # Test parameter bounds
    glow = processor.create_glow_effect(intensity=1.5)  # Should clamp to 1.0
    print(f"   Glow intensity (input 1.5): {glow.intensity}")
    
    outline = processor.create_outline_effect(intensity=-0.5)  # Should clamp to 0.0
    print(f"   Outline intensity (input -0.5): {outline.intensity}")
    
    # Test color format handling
    shadow = processor.create_shadow_effect(color=(0.5, 0.5, 0.5))  # RGB -> RGBA
    print(f"   Shadow color (RGB input): {shadow.color}")


def main():
    """Main demo function."""
    print("Visual Effects System Demo")
    print("=" * 50)
    
    try:
        # Run individual effect demos
        demo_glow_effects()
        demo_outline_effects()
        demo_shadow_effects()
        demo_gradient_effects()
        demo_combined_effects()
        demo_effect_parameters()
        
        print("\n" + "=" * 50)
        print("✅ Visual Effects Demo Completed Successfully!")
        print("\nKey Features Demonstrated:")
        print("• Glow effects with configurable intensity and radius")
        print("• Outline/stroke rendering with width and color controls")
        print("• Drop shadow effects with offset and blur parameters")
        print("• Gradient fills (linear, radial, conic) with color stops")
        print("• Real-time parameter adjustment")
        print("• Effect combination and layering")
        print("• GLSL shader integration")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())