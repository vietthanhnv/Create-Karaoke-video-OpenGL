"""
Animation effects implementation for text elements.

This module provides concrete implementations of animation effects including:
- Fade in/out animations
- Slide transitions (left, right, up, down)
- Typewriter effect with character-by-character reveal
- Bounce animations with physics-based motion

All effects support keyframe-based animation interpolation with easing curves
and real-time parameter adjustment.
"""

import math
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass

from ..core.models import (
    AnimationEffect, AnimationType, EasingType, TextElement, Keyframe,
    InterpolationType
)
from ..core.keyframe_system import KeyframeSystem


@dataclass
class AnimationState:
    """Current state of an animation effect."""
    progress: float  # 0.0 to 1.0
    is_active: bool
    start_time: float
    end_time: float
    properties: Dict[str, Any]


class BaseAnimationEffect(ABC):
    """
    Base class for all animation effects.
    
    Provides common functionality for animation timing, easing curves,
    and property interpolation.
    """
    
    def __init__(self, effect_config: AnimationEffect):
        """
        Initialize base animation effect.
        
        Args:
            effect_config: Animation effect configuration
        """
        self.config = effect_config
        self.keyframe_system = KeyframeSystem()
        self._initial_properties: Dict[str, Any] = {}
        self._target_properties: Dict[str, Any] = {}
    
    @abstractmethod
    def calculate_properties(self, progress: float, text_element: TextElement) -> Dict[str, Any]:
        """
        Calculate animated properties at given progress.
        
        Args:
            progress: Animation progress (0.0 to 1.0)
            text_element: Text element being animated
            
        Returns:
            Dictionary of animated property values
        """
        pass
    
    def get_animation_state(self, current_time: float, start_time: float) -> AnimationState:
        """
        Get current animation state based on timing.
        
        Args:
            current_time: Current timeline time
            start_time: Animation start time
            
        Returns:
            Current animation state
        """
        end_time = start_time + self.config.duration
        
        if current_time < start_time:
            progress = 0.0
            is_active = False
        elif current_time >= end_time:
            progress = 1.0
            is_active = False
        else:
            # Calculate raw progress
            raw_progress = (current_time - start_time) / self.config.duration
            # Apply easing curve
            progress = self._apply_easing(raw_progress, self.config.easing_curve)
            is_active = True
        
        return AnimationState(
            progress=progress,
            is_active=is_active,
            start_time=start_time,
            end_time=end_time,
            properties={}
        )
    
    def _apply_easing(self, t: float, easing: EasingType) -> float:
        """Apply easing curve to progress value."""
        return self.keyframe_system._apply_easing(t, easing)
    
    def set_initial_properties(self, properties: Dict[str, Any]) -> None:
        """Set initial properties for the animation."""
        self._initial_properties = properties.copy()
    
    def set_target_properties(self, properties: Dict[str, Any]) -> None:
        """Set target properties for the animation."""
        self._target_properties = properties.copy()
    
    def interpolate_property(self, initial_value: Any, target_value: Any, progress: float) -> Any:
        """Interpolate between initial and target values."""
        return self.keyframe_system._interpolate_value(initial_value, target_value, progress)


class FadeEffect(BaseAnimationEffect):
    """
    Fade in/out animation effect.
    
    Animates the alpha/opacity of text elements with smooth transitions.
    Supports both fade in and fade out animations.
    """
    
    def __init__(self, effect_config: AnimationEffect):
        """Initialize fade effect."""
        super().__init__(effect_config)
        
        # Set default parameters if not provided
        default_params = {
            'fade_type': 'in',  # 'in', 'out', or 'in_out'
            'start_alpha': 0.0,
            'end_alpha': 1.0
        }
        
        for key, value in default_params.items():
            if key not in self.config.parameters:
                self.config.parameters[key] = value
    
    def calculate_properties(self, progress: float, text_element: TextElement) -> Dict[str, Any]:
        """Calculate fade animation properties."""
        fade_type = self.config.parameters.get('fade_type', 'in')
        start_alpha = self.config.parameters.get('start_alpha', 0.0)
        end_alpha = self.config.parameters.get('end_alpha', 1.0)
        
        if fade_type == 'in':
            alpha = self.interpolate_property(start_alpha, end_alpha, progress)
        elif fade_type == 'out':
            alpha = self.interpolate_property(end_alpha, start_alpha, progress)
        elif fade_type == 'in_out':
            # Fade in for first half, fade out for second half
            if progress <= 0.5:
                alpha = self.interpolate_property(start_alpha, end_alpha, progress * 2.0)
            else:
                alpha = self.interpolate_property(end_alpha, start_alpha, (progress - 0.5) * 2.0)
        else:
            alpha = end_alpha
        
        # Apply alpha to text color
        current_color = list(text_element.color)
        current_color[3] = alpha  # Set alpha channel
        
        return {
            'color': tuple(current_color),
            'alpha': alpha
        }


class SlideEffect(BaseAnimationEffect):
    """
    Slide animation effect.
    
    Animates text position with directional movement (left, right, up, down).
    Supports customizable slide distance and direction.
    """
    
    def __init__(self, effect_config: AnimationEffect):
        """Initialize slide effect."""
        super().__init__(effect_config)
        
        # Set default parameters
        default_params = {
            'direction': 'left',  # 'left', 'right', 'up', 'down'
            'distance': 100.0,    # Slide distance in pixels
            'slide_type': 'in'    # 'in', 'out', or 'through'
        }
        
        for key, value in default_params.items():
            if key not in self.config.parameters:
                self.config.parameters[key] = value
    
    def calculate_properties(self, progress: float, text_element: TextElement) -> Dict[str, Any]:
        """Calculate slide animation properties."""
        direction = self.config.parameters.get('direction', 'left')
        distance = self.config.parameters.get('distance', 100.0)
        slide_type = self.config.parameters.get('slide_type', 'in')
        
        # Calculate direction vector
        direction_vectors = {
            'left': (-1.0, 0.0),
            'right': (1.0, 0.0),
            'up': (0.0, -1.0),
            'down': (0.0, 1.0)
        }
        
        dx, dy = direction_vectors.get(direction, (-1.0, 0.0))
        
        # Calculate offset based on slide type
        if slide_type == 'in':
            # Start offset, end at original position
            offset_x = dx * distance * (1.0 - progress)
            offset_y = dy * distance * (1.0 - progress)
        elif slide_type == 'out':
            # Start at original position, end offset
            offset_x = dx * distance * progress
            offset_y = dy * distance * progress
        elif slide_type == 'through':
            # Slide through from one side to the other
            offset_x = dx * distance * (progress - 0.5) * 2.0
            offset_y = dy * distance * (progress - 0.5) * 2.0
        else:
            offset_x = offset_y = 0.0
        
        # Apply offset to current position
        new_position = (
            text_element.position[0] + offset_x,
            text_element.position[1] + offset_y
        )
        
        return {
            'position': new_position,
            'offset_x': offset_x,
            'offset_y': offset_y
        }


class TypewriterEffect(BaseAnimationEffect):
    """
    Typewriter animation effect.
    
    Reveals text character by character with customizable typing speed
    and optional cursor display.
    """
    
    def __init__(self, effect_config: AnimationEffect):
        """Initialize typewriter effect."""
        super().__init__(effect_config)
        
        # Set default parameters
        default_params = {
            'show_cursor': True,
            'cursor_char': '|',
            'cursor_blink_rate': 2.0,  # Blinks per second
            'typing_speed': 'linear',   # 'linear', 'accelerate', 'decelerate'
            'character_delay': 0.0      # Additional delay between characters
        }
        
        for key, value in default_params.items():
            if key not in self.config.parameters:
                self.config.parameters[key] = value
    
    def calculate_properties(self, progress: float, text_element: TextElement) -> Dict[str, Any]:
        """Calculate typewriter animation properties."""
        text_content = text_element.content
        show_cursor = self.config.parameters.get('show_cursor', True)
        cursor_char = self.config.parameters.get('cursor_char', '|')
        cursor_blink_rate = self.config.parameters.get('cursor_blink_rate', 2.0)
        typing_speed = self.config.parameters.get('typing_speed', 'linear')
        
        # Apply typing speed curve
        if typing_speed == 'accelerate':
            char_progress = progress * progress
        elif typing_speed == 'decelerate':
            char_progress = 1.0 - (1.0 - progress) * (1.0 - progress)
        else:  # linear
            char_progress = progress
        
        # Calculate number of characters to show
        total_chars = len(text_content)
        chars_to_show = int(char_progress * total_chars)
        chars_to_show = min(chars_to_show, total_chars)
        
        # Build visible text
        visible_text = text_content[:chars_to_show]
        
        # Add cursor if enabled and animation is active
        if show_cursor and progress < 1.0:
            # Calculate cursor blink
            blink_cycle = (progress * self.config.duration * cursor_blink_rate) % 1.0
            show_cursor_now = blink_cycle < 0.5
            
            if show_cursor_now:
                visible_text += cursor_char
        
        return {
            'content': visible_text,
            'visible_chars': chars_to_show,
            'total_chars': total_chars,
            'typing_progress': char_progress
        }


class BounceEffect(BaseAnimationEffect):
    """
    Bounce animation effect.
    
    Creates physics-based bouncing motion with customizable bounce height,
    gravity, and damping parameters.
    """
    
    def __init__(self, effect_config: AnimationEffect):
        """Initialize bounce effect."""
        super().__init__(effect_config)
        
        # Set default parameters
        default_params = {
            'bounce_height': 50.0,    # Maximum bounce height in pixels
            'gravity': 980.0,         # Gravity acceleration (pixels/s²)
            'damping': 0.8,           # Bounce damping factor (0-1)
            'bounce_count': 3,        # Number of bounces
            'direction': 'vertical'   # 'vertical', 'horizontal', or 'both'
        }
        
        for key, value in default_params.items():
            if key not in self.config.parameters:
                self.config.parameters[key] = value
    
    def calculate_properties(self, progress: float, text_element: TextElement) -> Dict[str, Any]:
        """Calculate bounce animation properties."""
        bounce_height = self.config.parameters.get('bounce_height', 50.0)
        gravity = self.config.parameters.get('gravity', 980.0)
        damping = self.config.parameters.get('damping', 0.8)
        bounce_count = self.config.parameters.get('bounce_count', 3)
        direction = self.config.parameters.get('direction', 'vertical')
        
        # Calculate bounce physics
        time = progress * self.config.duration
        
        # Calculate bounce position using physics simulation
        bounce_y = self._calculate_bounce_position(
            time, bounce_height, gravity, damping, bounce_count
        )
        
        # Apply direction
        offset_x = 0.0
        offset_y = 0.0
        
        if direction in ['vertical', 'both']:
            offset_y = -bounce_y  # Negative for upward bounce
        
        if direction in ['horizontal', 'both']:
            # Add horizontal oscillation
            horizontal_freq = bounce_count * 2.0  # Oscillations per animation
            offset_x = bounce_height * 0.3 * math.sin(progress * horizontal_freq * 2 * math.pi)
            offset_x *= (1.0 - progress)  # Dampen over time
        
        # Apply offset to current position
        new_position = (
            text_element.position[0] + offset_x,
            text_element.position[1] + offset_y
        )
        
        return {
            'position': new_position,
            'offset_x': offset_x,
            'offset_y': offset_y,
            'bounce_height': bounce_y
        }
    
    def _calculate_bounce_position(self, time: float, height: float, gravity: float,
                                 damping: float, bounce_count: int) -> float:
        """
        Calculate bounce position using physics simulation.
        
        Args:
            time: Current time in animation
            height: Initial bounce height
            gravity: Gravity acceleration
            damping: Bounce damping factor
            bounce_count: Number of bounces
            
        Returns:
            Current bounce height
        """
        if time <= 0:
            return 0.0
        
        # Calculate time for one complete bounce cycle
        bounce_time = math.sqrt(2 * height / gravity) * 2  # Time for up and down
        
        # Determine which bounce we're in
        total_time = 0.0
        current_height = height
        
        for bounce in range(bounce_count + 1):
            if time <= total_time + bounce_time:
                # We're in this bounce
                local_time = time - total_time
                
                # Calculate position within this bounce
                if local_time <= bounce_time / 2:
                    # Going up
                    t = local_time
                    pos = current_height * t / (bounce_time / 2) - 0.5 * gravity * t * t
                else:
                    # Coming down
                    t = local_time - bounce_time / 2
                    max_pos = current_height
                    pos = max_pos - 0.5 * gravity * t * t
                
                return max(0.0, pos)
            
            # Move to next bounce
            total_time += bounce_time
            current_height *= damping
            bounce_time = math.sqrt(2 * current_height / gravity) * 2
            
            if current_height < 0.1:  # Stop bouncing when too small
                break
        
        return 0.0


class AnimationEffectProcessor:
    """
    Main processor for managing and applying animation effects to text elements.
    
    This class coordinates multiple animation effects, handles keyframe-based
    animation interpolation, and provides real-time parameter adjustment.
    """
    
    def __init__(self):
        """Initialize animation effect processor."""
        self.keyframe_system = KeyframeSystem()
        self._effect_factories = {
            AnimationType.FADE_IN: lambda config: FadeEffect(config),
            AnimationType.FADE_OUT: lambda config: FadeEffect(config),
            AnimationType.SLIDE_LEFT: lambda config: SlideEffect(config),
            AnimationType.SLIDE_RIGHT: lambda config: SlideEffect(config),
            AnimationType.SLIDE_UP: lambda config: SlideEffect(config),
            AnimationType.SLIDE_DOWN: lambda config: SlideEffect(config),
            AnimationType.TYPEWRITER: lambda config: TypewriterEffect(config),
            AnimationType.BOUNCE: lambda config: BounceEffect(config)
        }
    
    def create_effect(self, effect_config: AnimationEffect) -> BaseAnimationEffect:
        """
        Create an animation effect instance from configuration.
        
        Args:
            effect_config: Animation effect configuration
            
        Returns:
            Animation effect instance
            
        Raises:
            ValueError: If effect type is not supported
        """
        factory = self._effect_factories.get(effect_config.type)
        if not factory:
            raise ValueError(f"Unsupported animation type: {effect_config.type}")
        
        return factory(effect_config)
    
    def apply_animation_effects(self, text_element: TextElement, effects: List[AnimationEffect],
                              current_time: float, start_time: float) -> Dict[str, Any]:
        """
        Apply multiple animation effects to a text element.
        
        Args:
            text_element: Text element to animate
            effects: List of animation effects to apply
            current_time: Current timeline time
            start_time: Animation start time
            
        Returns:
            Dictionary of combined animated properties
        """
        if not effects:
            return {}
        
        combined_properties = {}
        
        for effect_config in effects:
            try:
                effect = self.create_effect(effect_config)
                state = effect.get_animation_state(current_time, start_time)
                
                if state.is_active or state.progress > 0:
                    properties = effect.calculate_properties(state.progress, text_element)
                    
                    # Combine properties (later effects override earlier ones)
                    combined_properties.update(properties)
                    
            except Exception as e:
                # Log error but continue with other effects
                print(f"Error applying animation effect {effect_config.type}: {e}")
                continue
        
        return combined_properties
    
    def interpolate_keyframe_animations(self, keyframes: List[Keyframe], current_time: float,
                                     text_element: TextElement) -> Dict[str, Any]:
        """
        Interpolate animation properties from keyframes.
        
        Args:
            keyframes: List of keyframes with animation data
            current_time: Current timeline time
            text_element: Text element being animated
            
        Returns:
            Dictionary of interpolated properties
        """
        if not keyframes:
            return {}
        
        # Sort keyframes by time
        sorted_keyframes = self.keyframe_system.sort_keyframes(keyframes)
        
        # Find surrounding keyframes
        before_kf = None
        after_kf = None
        
        for kf in sorted_keyframes:
            if kf.time <= current_time:
                before_kf = kf
            elif kf.time > current_time and after_kf is None:
                after_kf = kf
                break
        
        # Handle edge cases
        if before_kf is None and after_kf is None:
            return {}
        elif before_kf is None:
            return after_kf.properties.copy()
        elif after_kf is None:
            return before_kf.properties.copy()
        elif before_kf.time == after_kf.time:
            return after_kf.properties.copy()
        
        # Interpolate between keyframes
        t = (current_time - before_kf.time) / (after_kf.time - before_kf.time)
        
        # Use easing from the later keyframe's interpolation type
        easing = EasingType.LINEAR  # Default easing
        if 'easing' in after_kf.properties:
            try:
                easing = EasingType(after_kf.properties['easing'])
            except ValueError:
                pass
        
        return self.keyframe_system.interpolate_between(before_kf, after_kf, t, easing)
    
    def update_effect_parameters(self, effect_config: AnimationEffect, 
                               parameter_updates: Dict[str, Any]) -> AnimationEffect:
        """
        Update animation effect parameters in real-time.
        
        Args:
            effect_config: Original effect configuration
            parameter_updates: Dictionary of parameter updates
            
        Returns:
            Updated animation effect configuration
        """
        # Create a copy of the effect config
        updated_config = AnimationEffect(
            type=effect_config.type,
            duration=effect_config.duration,
            parameters=effect_config.parameters.copy(),
            easing_curve=effect_config.easing_curve
        )
        
        # Apply parameter updates
        for key, value in parameter_updates.items():
            if key == 'duration':
                updated_config.duration = max(0.1, float(value))  # Minimum duration
            elif key == 'easing_curve':
                if isinstance(value, EasingType):
                    updated_config.easing_curve = value
                elif isinstance(value, str):
                    try:
                        updated_config.easing_curve = EasingType(value)
                    except ValueError:
                        pass  # Keep original easing
            else:
                updated_config.parameters[key] = value
        
        return updated_config
    
    def get_supported_effect_types(self) -> List[AnimationType]:
        """Get list of supported animation effect types."""
        return list(self._effect_factories.keys())
    
    def get_effect_parameters(self, effect_type: AnimationType) -> Dict[str, Any]:
        """
        Get default parameters for an effect type.
        
        Args:
            effect_type: Animation effect type
            
        Returns:
            Dictionary of default parameters
        """
        # Create a temporary effect to get default parameters
        temp_config = AnimationEffect(
            type=effect_type,
            duration=1.0,
            parameters={},
            easing_curve=EasingType.LINEAR
        )
        
        try:
            effect = self.create_effect(temp_config)
            return effect.config.parameters.copy()
        except ValueError:
            return {}