"""
Tests for animation effects implementation.
"""

import pytest
import math
from src.effects.animation_effects import (
    AnimationEffectProcessor, FadeEffect, SlideEffect, 
    TypewriterEffect, BounceEffect, AnimationState
)
from src.core.models import (
    AnimationEffect, AnimationType, EasingType, TextElement, Keyframe,
    InterpolationType
)


class TestAnimationEffectProcessor:
    """Test cases for AnimationEffectProcessor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = AnimationEffectProcessor()
        self.sample_text = TextElement(
            content="Hello World",
            font_family="Arial",
            font_size=24.0,
            color=(1.0, 1.0, 1.0, 1.0),
            position=(100.0, 200.0),
            rotation=(0.0, 0.0, 0.0),
            effects=[]
        )
    
    def test_create_fade_effect(self):
        """Test creating fade effect."""
        config = AnimationEffect(
            type=AnimationType.FADE_IN,
            duration=2.0,
            parameters={'fade_type': 'in'},
            easing_curve=EasingType.LINEAR
        )
        
        effect = self.processor.create_effect(config)
        assert isinstance(effect, FadeEffect)
        assert effect.config.type == AnimationType.FADE_IN
        assert effect.config.duration == 2.0
    
    def test_create_slide_effect(self):
        """Test creating slide effect."""
        config = AnimationEffect(
            type=AnimationType.SLIDE_LEFT,
            duration=1.5,
            parameters={'direction': 'left', 'distance': 150.0},
            easing_curve=EasingType.EASE_OUT
        )
        
        effect = self.processor.create_effect(config)
        assert isinstance(effect, SlideEffect)
        assert effect.config.parameters['direction'] == 'left'
        assert effect.config.parameters['distance'] == 150.0
    
    def test_create_typewriter_effect(self):
        """Test creating typewriter effect."""
        config = AnimationEffect(
            type=AnimationType.TYPEWRITER,
            duration=3.0,
            parameters={'show_cursor': True, 'cursor_char': '_'},
            easing_curve=EasingType.LINEAR
        )
        
        effect = self.processor.create_effect(config)
        assert isinstance(effect, TypewriterEffect)
        assert effect.config.parameters['show_cursor'] is True
        assert effect.config.parameters['cursor_char'] == '_'
    
    def test_create_bounce_effect(self):
        """Test creating bounce effect."""
        config = AnimationEffect(
            type=AnimationType.BOUNCE,
            duration=2.5,
            parameters={'bounce_height': 75.0, 'bounce_count': 4},
            easing_curve=EasingType.BOUNCE
        )
        
        effect = self.processor.create_effect(config)
        assert isinstance(effect, BounceEffect)
        assert effect.config.parameters['bounce_height'] == 75.0
        assert effect.config.parameters['bounce_count'] == 4
    
    def test_unsupported_effect_type(self):
        """Test handling of unsupported effect type."""
        # Create a mock animation type that doesn't exist
        config = AnimationEffect(
            type="INVALID_TYPE",  # This will cause an error
            duration=1.0,
            parameters={},
            easing_curve=EasingType.LINEAR
        )
        
        with pytest.raises(ValueError, match="Unsupported animation type"):
            self.processor.create_effect(config)
    
    def test_apply_single_animation_effect(self):
        """Test applying a single animation effect."""
        fade_config = AnimationEffect(
            type=AnimationType.FADE_IN,
            duration=2.0,
            parameters={'fade_type': 'in'},
            easing_curve=EasingType.LINEAR
        )
        
        # Test at 50% progress
        properties = self.processor.apply_animation_effects(
            self.sample_text, [fade_config], current_time=1.0, start_time=0.0
        )
        
        assert 'color' in properties
        assert 'alpha' in properties
        # At 50% progress, alpha should be 0.5
        assert abs(properties['alpha'] - 0.5) < 0.01
    
    def test_apply_multiple_animation_effects(self):
        """Test applying multiple animation effects."""
        fade_config = AnimationEffect(
            type=AnimationType.FADE_IN,
            duration=2.0,
            parameters={'fade_type': 'in'},
            easing_curve=EasingType.LINEAR
        )
        
        slide_config = AnimationEffect(
            type=AnimationType.SLIDE_LEFT,
            duration=2.0,
            parameters={'direction': 'left', 'distance': 100.0},
            easing_curve=EasingType.LINEAR
        )
        
        properties = self.processor.apply_animation_effects(
            self.sample_text, [fade_config, slide_config], 
            current_time=1.0, start_time=0.0
        )
        
        assert 'color' in properties  # From fade effect
        assert 'position' in properties  # From slide effect
        assert 'alpha' in properties
        assert 'offset_x' in properties
    
    def test_update_effect_parameters(self):
        """Test real-time parameter updates."""
        config = AnimationEffect(
            type=AnimationType.FADE_IN,
            duration=2.0,
            parameters={'fade_type': 'in'},
            easing_curve=EasingType.LINEAR
        )
        
        updates = {
            'duration': 3.0,
            'fade_type': 'out',
            'easing_curve': EasingType.EASE_IN
        }
        
        updated_config = self.processor.update_effect_parameters(config, updates)
        
        assert updated_config.duration == 3.0
        assert updated_config.parameters['fade_type'] == 'out'
        assert updated_config.easing_curve == EasingType.EASE_IN
    
    def test_get_supported_effect_types(self):
        """Test getting supported effect types."""
        supported_types = self.processor.get_supported_effect_types()
        
        assert AnimationType.FADE_IN in supported_types
        assert AnimationType.SLIDE_LEFT in supported_types
        assert AnimationType.TYPEWRITER in supported_types
        assert AnimationType.BOUNCE in supported_types
        assert len(supported_types) >= 4


class TestFadeEffect:
    """Test cases for FadeEffect."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sample_text = TextElement(
            content="Test Text",
            font_family="Arial",
            font_size=20.0,
            color=(1.0, 0.5, 0.0, 1.0),
            position=(50.0, 100.0),
            rotation=(0.0, 0.0, 0.0),
            effects=[]
        )
    
    def test_fade_in_effect(self):
        """Test fade in animation."""
        config = AnimationEffect(
            type=AnimationType.FADE_IN,
            duration=2.0,
            parameters={'fade_type': 'in', 'start_alpha': 0.0, 'end_alpha': 1.0},
            easing_curve=EasingType.LINEAR
        )
        
        effect = FadeEffect(config)
        
        # Test at different progress points
        props_0 = effect.calculate_properties(0.0, self.sample_text)
        props_50 = effect.calculate_properties(0.5, self.sample_text)
        props_100 = effect.calculate_properties(1.0, self.sample_text)
        
        assert props_0['alpha'] == 0.0
        assert abs(props_50['alpha'] - 0.5) < 0.01
        assert props_100['alpha'] == 1.0
    
    def test_fade_out_effect(self):
        """Test fade out animation."""
        config = AnimationEffect(
            type=AnimationType.FADE_OUT,
            duration=1.5,
            parameters={'fade_type': 'out', 'start_alpha': 0.0, 'end_alpha': 1.0},
            easing_curve=EasingType.LINEAR
        )
        
        effect = FadeEffect(config)
        
        props_0 = effect.calculate_properties(0.0, self.sample_text)
        props_100 = effect.calculate_properties(1.0, self.sample_text)
        
        assert props_0['alpha'] == 1.0  # Starts at full opacity
        assert props_100['alpha'] == 0.0  # Ends at transparent
    
    def test_fade_in_out_effect(self):
        """Test fade in-out animation."""
        config = AnimationEffect(
            type=AnimationType.FADE_IN,
            duration=2.0,
            parameters={'fade_type': 'in_out'},
            easing_curve=EasingType.LINEAR
        )
        
        effect = FadeEffect(config)
        
        props_0 = effect.calculate_properties(0.0, self.sample_text)
        props_25 = effect.calculate_properties(0.25, self.sample_text)
        props_50 = effect.calculate_properties(0.5, self.sample_text)
        props_75 = effect.calculate_properties(0.75, self.sample_text)
        props_100 = effect.calculate_properties(1.0, self.sample_text)
        
        # Should fade in to 50%, then fade out
        assert props_0['alpha'] == 0.0
        assert props_25['alpha'] > 0.0
        assert props_50['alpha'] == 1.0  # Peak at middle
        assert props_75['alpha'] < 1.0
        assert props_100['alpha'] == 0.0


class TestSlideEffect:
    """Test cases for SlideEffect."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sample_text = TextElement(
            content="Slide Text",
            font_family="Arial",
            font_size=18.0,
            color=(0.0, 1.0, 0.0, 1.0),
            position=(200.0, 300.0),
            rotation=(0.0, 0.0, 0.0),
            effects=[]
        )
    
    def test_slide_left_in(self):
        """Test slide left in animation."""
        config = AnimationEffect(
            type=AnimationType.SLIDE_LEFT,
            duration=1.0,
            parameters={'direction': 'left', 'distance': 100.0, 'slide_type': 'in'},
            easing_curve=EasingType.LINEAR
        )
        
        effect = SlideEffect(config)
        
        props_0 = effect.calculate_properties(0.0, self.sample_text)
        props_50 = effect.calculate_properties(0.5, self.sample_text)
        props_100 = effect.calculate_properties(1.0, self.sample_text)
        
        # Should start offset to the left and slide to original position
        assert props_0['position'][0] < self.sample_text.position[0]
        assert abs(props_50['position'][0] - (self.sample_text.position[0] - 50.0)) < 0.01
        assert abs(props_100['position'][0] - self.sample_text.position[0]) < 0.01
    
    def test_slide_right_out(self):
        """Test slide right out animation."""
        config = AnimationEffect(
            type=AnimationType.SLIDE_RIGHT,
            duration=1.5,
            parameters={'direction': 'right', 'distance': 150.0, 'slide_type': 'out'},
            easing_curve=EasingType.LINEAR
        )
        
        effect = SlideEffect(config)
        
        props_0 = effect.calculate_properties(0.0, self.sample_text)
        props_100 = effect.calculate_properties(1.0, self.sample_text)
        
        # Should start at original position and slide right
        assert abs(props_0['position'][0] - self.sample_text.position[0]) < 0.01
        assert props_100['position'][0] > self.sample_text.position[0]
    
    def test_slide_up_through(self):
        """Test slide up through animation."""
        config = AnimationEffect(
            type=AnimationType.SLIDE_UP,
            duration=2.0,
            parameters={'direction': 'up', 'distance': 200.0, 'slide_type': 'through'},
            easing_curve=EasingType.LINEAR
        )
        
        effect = SlideEffect(config)
        
        props_0 = effect.calculate_properties(0.0, self.sample_text)
        props_50 = effect.calculate_properties(0.5, self.sample_text)
        props_100 = effect.calculate_properties(1.0, self.sample_text)
        
        # Should slide from bottom to top through the original position
        assert props_0['position'][1] > self.sample_text.position[1]  # Start below
        assert abs(props_50['position'][1] - self.sample_text.position[1]) < 0.01  # Middle at original
        assert props_100['position'][1] < self.sample_text.position[1]  # End above


class TestTypewriterEffect:
    """Test cases for TypewriterEffect."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sample_text = TextElement(
            content="Hello World!",
            font_family="Courier",
            font_size=16.0,
            color=(1.0, 1.0, 1.0, 1.0),
            position=(0.0, 0.0),
            rotation=(0.0, 0.0, 0.0),
            effects=[]
        )
    
    def test_typewriter_progression(self):
        """Test typewriter character progression."""
        config = AnimationEffect(
            type=AnimationType.TYPEWRITER,
            duration=3.0,
            parameters={'show_cursor': False},
            easing_curve=EasingType.LINEAR
        )
        
        effect = TypewriterEffect(config)
        
        props_0 = effect.calculate_properties(0.0, self.sample_text)
        props_25 = effect.calculate_properties(0.25, self.sample_text)
        props_50 = effect.calculate_properties(0.5, self.sample_text)
        props_100 = effect.calculate_properties(1.0, self.sample_text)
        
        # Check character progression
        assert props_0['content'] == ""
        assert len(props_25['content']) < len(props_50['content'])
        assert len(props_50['content']) < len(props_100['content'])
        assert props_100['content'] == self.sample_text.content
    
    def test_typewriter_with_cursor(self):
        """Test typewriter with cursor display."""
        config = AnimationEffect(
            type=AnimationType.TYPEWRITER,
            duration=2.0,
            parameters={'show_cursor': True, 'cursor_char': '|'},
            easing_curve=EasingType.LINEAR
        )
        
        effect = TypewriterEffect(config)
        
        props_50 = effect.calculate_properties(0.5, self.sample_text)
        
        # Should have cursor when animation is active
        assert '|' in props_50['content'] or len(props_50['content']) > 0
        assert props_50['visible_chars'] < len(self.sample_text.content)


class TestBounceEffect:
    """Test cases for BounceEffect."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sample_text = TextElement(
            content="Bounce!",
            font_family="Arial",
            font_size=24.0,
            color=(1.0, 0.0, 1.0, 1.0),
            position=(150.0, 250.0),
            rotation=(0.0, 0.0, 0.0),
            effects=[]
        )
    
    def test_bounce_vertical_motion(self):
        """Test vertical bounce motion."""
        config = AnimationEffect(
            type=AnimationType.BOUNCE,
            duration=2.0,
            parameters={'bounce_height': 100.0, 'direction': 'vertical'},
            easing_curve=EasingType.LINEAR
        )
        
        effect = BounceEffect(config)
        
        props_0 = effect.calculate_properties(0.0, self.sample_text)
        props_25 = effect.calculate_properties(0.25, self.sample_text)
        props_50 = effect.calculate_properties(0.5, self.sample_text)
        
        # Should start at original position
        assert abs(props_0['position'][1] - self.sample_text.position[1]) < 0.01
        
        # Should have some vertical movement during animation
        assert 'offset_y' in props_25
        assert 'offset_y' in props_50
    
    def test_bounce_physics_calculation(self):
        """Test bounce physics calculation."""
        config = AnimationEffect(
            type=AnimationType.BOUNCE,
            duration=3.0,
            parameters={
                'bounce_height': 50.0,
                'gravity': 980.0,
                'damping': 0.8,
                'bounce_count': 2
            },
            easing_curve=EasingType.LINEAR
        )
        
        effect = BounceEffect(config)
        
        # Test bounce position calculation
        pos_0 = effect._calculate_bounce_position(0.0, 50.0, 980.0, 0.8, 2)
        pos_mid = effect._calculate_bounce_position(0.5, 50.0, 980.0, 0.8, 2)
        
        assert pos_0 == 0.0  # Should start at ground
        assert pos_mid >= 0.0  # Should be above ground during bounce


class TestAnimationState:
    """Test cases for AnimationState and timing."""
    
    def test_animation_timing(self):
        """Test animation timing and state calculation."""
        config = AnimationEffect(
            type=AnimationType.FADE_IN,
            duration=2.0,
            parameters={},
            easing_curve=EasingType.LINEAR
        )
        
        effect = FadeEffect(config)
        
        # Test before animation starts
        state_before = effect.get_animation_state(-1.0, 0.0)
        assert state_before.progress == 0.0
        assert not state_before.is_active
        
        # Test during animation
        state_during = effect.get_animation_state(1.0, 0.0)
        assert state_during.progress == 0.5
        assert state_during.is_active
        
        # Test after animation ends
        state_after = effect.get_animation_state(3.0, 0.0)
        assert state_after.progress == 1.0
        assert not state_after.is_active
    
    def test_easing_curves(self):
        """Test different easing curves."""
        config_linear = AnimationEffect(
            type=AnimationType.FADE_IN,
            duration=2.0,
            parameters={},
            easing_curve=EasingType.LINEAR
        )
        
        config_ease_in = AnimationEffect(
            type=AnimationType.FADE_IN,
            duration=2.0,
            parameters={},
            easing_curve=EasingType.EASE_IN
        )
        
        effect_linear = FadeEffect(config_linear)
        effect_ease_in = FadeEffect(config_ease_in)
        
        # Test at 50% time
        state_linear = effect_linear.get_animation_state(1.0, 0.0)
        state_ease_in = effect_ease_in.get_animation_state(1.0, 0.0)
        
        # Ease-in should have slower progress at 50% time
        assert state_linear.progress == 0.5
        assert state_ease_in.progress < 0.5


if __name__ == "__main__":
    pytest.main([__file__])