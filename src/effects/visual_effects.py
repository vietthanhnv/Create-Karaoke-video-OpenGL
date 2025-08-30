"""
Visual effects implementation for text elements.

This module provides concrete implementations of visual effects including:
- Glow effect with configurable intensity and radius
- Outline/stroke rendering with width and color controls
- Drop shadow effect with offset and blur parameters
- Gradient fills (linear, radial, conic) with color stops

All effects are implemented using GLSL shaders for hardware acceleration
and support real-time parameter adjustment.
"""

import math
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import numpy as np

from ..core.models import (
    VisualEffect, VisualEffectType, TextElement
)
from ..graphics.shader_manager import ShaderManager


@dataclass
class VisualEffectState:
    """Current state of a visual effect."""
    is_active: bool
    intensity: float
    color: Tuple[float, float, float, float]
    parameters: Dict[str, Any]


class BaseVisualEffect(ABC):
    """
    Base class for all visual effects.
    
    Provides common functionality for shader management, parameter handling,
    and OpenGL rendering integration.
    """
    
    def __init__(self, effect_config: VisualEffect, shader_manager: ShaderManager):
        """
        Initialize base visual effect.
        
        Args:
            effect_config: Visual effect configuration
            shader_manager: Shader manager for OpenGL operations
        """
        self.config = effect_config
        self.shader_manager = shader_manager
        self._shader_program = None
        self._program_name = None
        self._is_initialized = False
    
    @abstractmethod
    def get_shader_names(self) -> Tuple[str, str]:
        """
        Get vertex and fragment shader names for this effect.
        
        Returns:
            Tuple of (vertex_shader_name, fragment_shader_name)
        """
        pass
    
    @abstractmethod
    def set_shader_uniforms(self, text_element: TextElement, 
                          texture_size: Tuple[int, int]) -> None:
        """
        Set shader uniforms for rendering this effect.
        
        Args:
            text_element: Text element being rendered
            texture_size: Size of the text texture
        """
        pass
    
    def initialize(self) -> bool:
        """
        Initialize the visual effect (load shaders, etc.).
        
        Returns:
            True if initialization successful, False otherwise
        """
        if self._is_initialized:
            return True
        
        try:
            vertex_name, fragment_name = self.get_shader_names()
            self._shader_program = self.shader_manager.load_shader_program(
                vertex_name, fragment_name
            )
            if self._shader_program:
                self._program_name = f"{vertex_name}_{fragment_name}"
                self._is_initialized = True
                return True
            return False
        except Exception as e:
            print(f"Failed to initialize visual effect {self.config.type}: {e}")
            return False
    
    def bind_shader(self) -> bool:
        """
        Bind the effect's shader program.
        
        Returns:
            True if shader bound successfully, False otherwise
        """
        if not self._is_initialized:
            if not self.initialize():
                return False
        
        if self._shader_program:
            self._shader_program.use()
            return True
        return False
    
    def get_effect_state(self) -> VisualEffectState:
        """
        Get current visual effect state.
        
        Returns:
            Current visual effect state
        """
        return VisualEffectState(
            is_active=True,
            intensity=self.config.intensity,
            color=self.config.color,
            parameters=self.config.parameters.copy()
        )
    
    def update_parameters(self, parameter_updates: Dict[str, Any]) -> None:
        """
        Update effect parameters in real-time.
        
        Args:
            parameter_updates: Dictionary of parameter updates
        """
        for key, value in parameter_updates.items():
            if key == 'intensity':
                self.config.intensity = max(0.0, min(1.0, float(value)))
            elif key == 'color':
                if isinstance(value, (list, tuple)) and len(value) >= 3:
                    # Ensure RGBA format
                    if len(value) == 3:
                        self.config.color = tuple(value) + (1.0,)
                    else:
                        self.config.color = tuple(value[:4])
            else:
                self.config.parameters[key] = value


class GlowEffect(BaseVisualEffect):
    """
    Glow visual effect.
    
    Creates a soft glow around text with configurable intensity, radius,
    and color. Uses multi-sampling for smooth glow falloff.
    """
    
    def __init__(self, effect_config: VisualEffect, shader_manager: ShaderManager):
        """Initialize glow effect."""
        super().__init__(effect_config, shader_manager)
        
        # Set default parameters if not provided
        default_params = {
            'radius': 8.0,      # Glow radius in pixels
            'samples': 16,      # Number of samples for glow quality
            'falloff': 1.0      # Glow falloff curve (1.0 = linear, 2.0 = quadratic)
        }
        
        for key, value in default_params.items():
            if key not in self.config.parameters:
                self.config.parameters[key] = value
    
    def get_shader_names(self) -> Tuple[str, str]:
        """Get glow shader names."""
        return ("glow_vertex", "glow_fragment")
    
    def set_shader_uniforms(self, text_element: TextElement, 
                          texture_size: Tuple[int, int]) -> None:
        """Set glow shader uniforms."""
        if not self._shader_program:
            return
        
        # Use the shader program object directly
        if not self._shader_program:
            return
        
        # Set basic uniforms
        self._shader_program.set_uniform("textColor", text_element.color)
        self._shader_program.set_uniform("glowColor", self.config.color)
        self._shader_program.set_uniform("glowIntensity", self.config.intensity)
        self._shader_program.set_uniform("glowRadius", self.config.parameters.get('radius', 8.0))
        self._shader_program.set_uniform("textureSize", texture_size)
        
        # Set texture sampler
        self._shader_program.set_uniform("textTexture", 0)


class OutlineEffect(BaseVisualEffect):
    """
    Outline/stroke visual effect.
    
    Creates an outline around text with configurable width and color.
    Supports both inner and outer outline modes.
    """
    
    def __init__(self, effect_config: VisualEffect, shader_manager: ShaderManager):
        """Initialize outline effect."""
        super().__init__(effect_config, shader_manager)
        
        # Set default parameters if not provided
        default_params = {
            'width': 2.0,       # Outline width in pixels
            'mode': 'outer',    # 'outer', 'inner', or 'center'
            'smoothness': 1.0   # Edge smoothness
        }
        
        for key, value in default_params.items():
            if key not in self.config.parameters:
                self.config.parameters[key] = value
    
    def get_shader_names(self) -> Tuple[str, str]:
        """Get outline shader names."""
        return ("outline_vertex", "outline_fragment")
    
    def set_shader_uniforms(self, text_element: TextElement, 
                          texture_size: Tuple[int, int]) -> None:
        """Set outline shader uniforms."""
        if not self._shader_program:
            return
        
        # Use the shader program object directly
        if not self._shader_program:
            return
        
        # Set basic uniforms
        self._shader_program.set_uniform("textColor", text_element.color)
        self._shader_program.set_uniform("outlineColor", self.config.color)
        self._shader_program.set_uniform("outlineWidth", self.config.parameters.get('width', 2.0))
        self._shader_program.set_uniform("textureSize", texture_size)
        
        # Set texture sampler
        self._shader_program.set_uniform("textTexture", 0)


class ShadowEffect(BaseVisualEffect):
    """
    Drop shadow visual effect.
    
    Creates a drop shadow behind text with configurable offset, blur,
    and color. Supports gaussian blur for smooth shadow edges.
    """
    
    def __init__(self, effect_config: VisualEffect, shader_manager: ShaderManager):
        """Initialize shadow effect."""
        super().__init__(effect_config, shader_manager)
        
        # Set default parameters if not provided
        default_params = {
            'offset_x': 4.0,    # Shadow X offset in pixels
            'offset_y': 4.0,    # Shadow Y offset in pixels
            'blur': 2.0,        # Shadow blur radius
            'opacity': 0.7      # Shadow opacity multiplier
        }
        
        for key, value in default_params.items():
            if key not in self.config.parameters:
                self.config.parameters[key] = value
    
    def get_shader_names(self) -> Tuple[str, str]:
        """Get shadow shader names."""
        return ("shadow_vertex", "shadow_fragment")
    
    def set_shader_uniforms(self, text_element: TextElement, 
                          texture_size: Tuple[int, int]) -> None:
        """Set shadow shader uniforms."""
        if not self._shader_program:
            return
        
        # Calculate shadow color with opacity
        shadow_color = list(self.config.color)
        shadow_color[3] *= self.config.parameters.get('opacity', 0.7)
        
        # Use the shader program object directly
        if not self._shader_program:
            return
        
        # Set basic uniforms
        self._shader_program.set_uniform("textColor", text_element.color)
        self._shader_program.set_uniform("shadowColor", tuple(shadow_color))
        self._shader_program.set_uniform("shadowOffset", (
            self.config.parameters.get('offset_x', 4.0),
            self.config.parameters.get('offset_y', 4.0)
        ))
        self._shader_program.set_uniform("shadowBlur", self.config.parameters.get('blur', 2.0))
        self._shader_program.set_uniform("textureSize", texture_size)
        
        # Set texture sampler
        self._shader_program.set_uniform("textTexture", 0)


@dataclass
class GradientStop:
    """Color stop for gradient effects."""
    position: float  # 0.0 to 1.0
    color: Tuple[float, float, float, float]


class GradientEffect(BaseVisualEffect):
    """
    Gradient fill visual effect.
    
    Creates gradient fills for text with support for linear, radial,
    and conic gradients. Supports multiple color stops.
    """
    
    def __init__(self, effect_config: VisualEffect, shader_manager: ShaderManager):
        """Initialize gradient effect."""
        super().__init__(effect_config, shader_manager)
        
        # Set default parameters if not provided
        default_params = {
            'type': 'linear',           # 'linear', 'radial', 'conic'
            'direction': (1.0, 0.0),    # Direction vector for linear
            'center': (0.5, 0.5),       # Center point (normalized)
            'radius': 0.5,              # Radius for radial gradient
            'angle': 0.0,               # Rotation angle in degrees
            'start_color': (1.0, 0.0, 0.0, 1.0),  # Default red
            'end_color': (0.0, 0.0, 1.0, 1.0),    # Default blue
            'color_stops': []           # Additional color stops
        }
        
        for key, value in default_params.items():
            if key not in self.config.parameters:
                self.config.parameters[key] = value
    
    def get_shader_names(self) -> Tuple[str, str]:
        """Get gradient shader names."""
        return ("gradient_vertex", "gradient_fragment")
    
    def set_shader_uniforms(self, text_element: TextElement, 
                          texture_size: Tuple[int, int]) -> None:
        """Set gradient shader uniforms."""
        if not self._shader_program:
            return
        
        gradient_type = self.config.parameters.get('type', 'linear')
        
        # Map gradient type to integer
        type_map = {'linear': 0, 'radial': 1, 'conic': 2}
        gradient_type_int = type_map.get(gradient_type, 0)
        
        # Use the shader program object directly
        if not self._shader_program:
            return
        
        # Set basic uniforms
        self._shader_program.set_uniform("gradientStart", 
            self.config.parameters.get('start_color', (1.0, 0.0, 0.0, 1.0)))
        self._shader_program.set_uniform("gradientEnd", 
            self.config.parameters.get('end_color', (0.0, 0.0, 1.0, 1.0)))
        
        # Calculate direction vector with rotation
        angle = math.radians(self.config.parameters.get('angle', 0.0))
        base_direction = self.config.parameters.get('direction', (1.0, 0.0))
        
        # Rotate direction vector
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        rotated_direction = (
            base_direction[0] * cos_a - base_direction[1] * sin_a,
            base_direction[0] * sin_a + base_direction[1] * cos_a
        )
        
        self._shader_program.set_uniform("gradientDirection", rotated_direction)
        
        # Convert normalized center to world coordinates
        center_norm = self.config.parameters.get('center', (0.5, 0.5))
        center_world = (
            text_element.position[0] + center_norm[0] * texture_size[0],
            text_element.position[1] + center_norm[1] * texture_size[1]
        )
        
        self._shader_program.set_uniform("gradientCenter", center_world)
        self._shader_program.set_uniform("gradientRadius", 
            self.config.parameters.get('radius', 0.5) * max(texture_size))
        self._shader_program.set_uniform("gradientType", gradient_type_int)
        
        # Set texture sampler
        self._shader_program.set_uniform("textTexture", 0)
    
    def add_color_stop(self, position: float, color: Tuple[float, float, float, float]) -> None:
        """
        Add a color stop to the gradient.
        
        Args:
            position: Position along gradient (0.0 to 1.0)
            color: RGBA color tuple
        """
        if 'color_stops' not in self.config.parameters:
            self.config.parameters['color_stops'] = []
        
        stop = GradientStop(position=position, color=color)
        self.config.parameters['color_stops'].append(stop)
        
        # Sort stops by position
        self.config.parameters['color_stops'].sort(key=lambda s: s.position)
    
    def clear_color_stops(self) -> None:
        """Clear all color stops."""
        self.config.parameters['color_stops'] = []
    
    def get_color_stops(self) -> List[GradientStop]:
        """Get all color stops."""
        return self.config.parameters.get('color_stops', [])


class VisualEffectProcessor:
    """
    Main processor for managing and applying visual effects to text elements.
    
    This class coordinates multiple visual effects, handles shader management,
    and provides real-time parameter adjustment and rendering.
    """
    
    def __init__(self, shader_manager: ShaderManager):
        """
        Initialize visual effect processor.
        
        Args:
            shader_manager: Shader manager for OpenGL operations
        """
        self.shader_manager = shader_manager
        self._effect_factories = {
            VisualEffectType.GLOW: lambda config: GlowEffect(config, shader_manager),
            VisualEffectType.OUTLINE: lambda config: OutlineEffect(config, shader_manager),
            VisualEffectType.SHADOW: lambda config: ShadowEffect(config, shader_manager),
            VisualEffectType.GRADIENT: lambda config: GradientEffect(config, shader_manager)
        }
        self._active_effects: Dict[str, BaseVisualEffect] = {}
    
    def create_effect(self, effect_config: VisualEffect) -> BaseVisualEffect:
        """
        Create a visual effect instance from configuration.
        
        Args:
            effect_config: Visual effect configuration
            
        Returns:
            Visual effect instance
            
        Raises:
            ValueError: If effect type is not supported
        """
        factory = self._effect_factories.get(effect_config.type)
        if not factory:
            raise ValueError(f"Unsupported visual effect type: {effect_config.type}")
        
        return factory(effect_config)
    
    def apply_visual_effects(self, text_element: TextElement, effects: List[VisualEffect],
                           texture_size: Tuple[int, int]) -> bool:
        """
        Apply multiple visual effects to a text element during rendering.
        
        Args:
            text_element: Text element to apply effects to
            effects: List of visual effects to apply
            texture_size: Size of the text texture
            
        Returns:
            True if effects applied successfully, False otherwise
        """
        if not effects:
            return True
        
        success = True
        
        for effect_config in effects:
            try:
                effect = self.create_effect(effect_config)
                
                if not effect.bind_shader():
                    print(f"Failed to bind shader for effect {effect_config.type}")
                    success = False
                    continue
                
                # Set shader uniforms for this effect
                effect.set_shader_uniforms(text_element, texture_size)
                
                # Store active effect for parameter updates
                effect_id = f"{effect_config.type.value}_{id(effect_config)}"
                self._active_effects[effect_id] = effect
                
            except Exception as e:
                print(f"Error applying visual effect {effect_config.type}: {e}")
                success = False
                continue
        
        return success
    
    def render_effect_pass(self, effect: BaseVisualEffect, text_element: TextElement,
                          texture_size: Tuple[int, int]) -> bool:
        """
        Render a single effect pass.
        
        Args:
            effect: Visual effect to render
            text_element: Text element being rendered
            texture_size: Size of the text texture
            
        Returns:
            True if render successful, False otherwise
        """
        try:
            if not effect.bind_shader():
                return False
            
            effect.set_shader_uniforms(text_element, texture_size)
            
            # The actual rendering (quad drawing) should be handled by the renderer
            # This method just sets up the effect for rendering
            return True
            
        except Exception as e:
            print(f"Error rendering effect pass: {e}")
            return False
    
    def update_effect_parameters(self, effect_id: str, 
                               parameter_updates: Dict[str, Any]) -> bool:
        """
        Update visual effect parameters in real-time.
        
        Args:
            effect_id: ID of the effect to update
            parameter_updates: Dictionary of parameter updates
            
        Returns:
            True if update successful, False otherwise
        """
        effect = self._active_effects.get(effect_id)
        if not effect:
            return False
        
        try:
            effect.update_parameters(parameter_updates)
            return True
        except Exception as e:
            print(f"Error updating effect parameters: {e}")
            return False
    
    def get_supported_effect_types(self) -> List[VisualEffectType]:
        """Get list of supported visual effect types."""
        return list(self._effect_factories.keys())
    
    def get_effect_parameters(self, effect_type: VisualEffectType) -> Dict[str, Any]:
        """
        Get default parameters for an effect type.
        
        Args:
            effect_type: Visual effect type
            
        Returns:
            Dictionary of default parameters
        """
        # Create a temporary effect to get default parameters
        temp_config = VisualEffect(
            type=effect_type,
            intensity=1.0,
            color=(1.0, 1.0, 1.0, 1.0),
            parameters={}
        )
        
        try:
            effect = self.create_effect(temp_config)
            return effect.config.parameters.copy()
        except ValueError:
            return {}
    
    def cleanup_effects(self) -> None:
        """Clean up all active effects."""
        self._active_effects.clear()
    
    def create_glow_effect(self, intensity: float = 1.0, 
                          color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
                          radius: float = 8.0) -> VisualEffect:
        """
        Create a glow effect with common parameters.
        
        Args:
            intensity: Glow intensity (0.0 to 1.0)
            color: Glow color (RGBA)
            radius: Glow radius in pixels
            
        Returns:
            Configured glow effect
        """
        return VisualEffect(
            type=VisualEffectType.GLOW,
            intensity=intensity,
            color=color,
            parameters={'radius': radius}
        )
    
    def create_outline_effect(self, intensity: float = 1.0,
                            color: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0),
                            width: float = 2.0) -> VisualEffect:
        """
        Create an outline effect with common parameters.
        
        Args:
            intensity: Outline intensity (0.0 to 1.0)
            color: Outline color (RGBA)
            width: Outline width in pixels
            
        Returns:
            Configured outline effect
        """
        return VisualEffect(
            type=VisualEffectType.OUTLINE,
            intensity=intensity,
            color=color,
            parameters={'width': width}
        )
    
    def create_shadow_effect(self, intensity: float = 1.0,
                           color: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.7),
                           offset_x: float = 4.0, offset_y: float = 4.0,
                           blur: float = 2.0) -> VisualEffect:
        """
        Create a shadow effect with common parameters.
        
        Args:
            intensity: Shadow intensity (0.0 to 1.0)
            color: Shadow color (RGBA)
            offset_x: Shadow X offset in pixels
            offset_y: Shadow Y offset in pixels
            blur: Shadow blur radius
            
        Returns:
            Configured shadow effect
        """
        return VisualEffect(
            type=VisualEffectType.SHADOW,
            intensity=intensity,
            color=color,
            parameters={
                'offset_x': offset_x,
                'offset_y': offset_y,
                'blur': blur
            }
        )
    
    def create_gradient_effect(self, intensity: float = 1.0,
                             gradient_type: str = 'linear',
                             start_color: Tuple[float, float, float, float] = (1.0, 0.0, 0.0, 1.0),
                             end_color: Tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0),
                             angle: float = 0.0) -> VisualEffect:
        """
        Create a gradient effect with common parameters.
        
        Args:
            intensity: Gradient intensity (0.0 to 1.0)
            gradient_type: Type of gradient ('linear', 'radial', 'conic')
            start_color: Starting color (RGBA)
            end_color: Ending color (RGBA)
            angle: Gradient angle in degrees
            
        Returns:
            Configured gradient effect
        """
        return VisualEffect(
            type=VisualEffectType.GRADIENT,
            intensity=intensity,
            color=start_color,  # Use start color as primary color
            parameters={
                'type': gradient_type,
                'start_color': start_color,
                'end_color': end_color,
                'angle': angle
            }
        )