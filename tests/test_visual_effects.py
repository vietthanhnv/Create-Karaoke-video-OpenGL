"""
Tests for visual effects implementation.
"""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock

from src.core.models import (
    VisualEffect, VisualEffectType, TextElement
)
from src.effects.visual_effects import (
    VisualEffectProcessor, GlowEffect, OutlineEffect, 
    ShadowEffect, GradientEffect, GradientStop
)


class TestVisualEffectProcessor:
    """Test cases for VisualEffectProcessor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_shader_manager = Mock()
        self.processor = VisualEffectProcessor(self.mock_shader_manager)
        
        # Create test text element
        self.text_element = TextElement(
            content="Test Text",
            font_family="Arial",
            font_size=24.0,
            color=(1.0, 1.0, 1.0, 1.0),
            position=(100.0, 100.0),
            rotation=(0.0, 0.0, 0.0),
            effects=[]
        )
        
        self.texture_size = (256, 64)
    
    def test_create_glow_effect(self):
        """Test creating glow effect."""
        effect_config = VisualEffect(
            type=VisualEffectType.GLOW,
            intensity=0.8,
            color=(1.0, 0.5, 0.0, 1.0),
            parameters={'radius': 10.0}
        )
        
        effect = self.processor.create_effect(effect_config)
        assert isinstance(effect, GlowEffect)
        assert effect.config.intensity == 0.8
        assert effect.config.color == (1.0, 0.5, 0.0, 1.0)
        assert effect.config.parameters['radius'] == 10.0
    
    def test_create_outline_effect(self):
        """Test creating outline effect."""
        effect_config = VisualEffect(
            type=VisualEffectType.OUTLINE,
            intensity=1.0,
            color=(0.0, 0.0, 0.0, 1.0),
            parameters={'width': 3.0}
        )
        
        effect = self.processor.create_effect(effect_config)
        assert isinstance(effect, OutlineEffect)
        assert effect.config.parameters['width'] == 3.0
    
    def test_create_shadow_effect(self):
        """Test creating shadow effect."""
        effect_config = VisualEffect(
            type=VisualEffectType.SHADOW,
            intensity=0.7,
            color=(0.0, 0.0, 0.0, 0.5),
            parameters={'offset_x': 5.0, 'offset_y': 5.0, 'blur': 3.0}
        )
        
        effect = self.processor.create_effect(effect_config)
        assert isinstance(effect, ShadowEffect)
        assert effect.config.parameters['offset_x'] == 5.0
        assert effect.config.parameters['blur'] == 3.0
    
    def test_create_gradient_effect(self):
        """Test creating gradient effect."""
        effect_config = VisualEffect(
            type=VisualEffectType.GRADIENT,
            intensity=1.0,
            color=(1.0, 0.0, 0.0, 1.0),
            parameters={
                'type': 'linear',
                'start_color': (1.0, 0.0, 0.0, 1.0),
                'end_color': (0.0, 0.0, 1.0, 1.0)
            }
        )
        
        effect = self.processor.create_effect(effect_config)
        assert isinstance(effect, GradientEffect)
        assert effect.config.parameters['type'] == 'linear'
    
    def test_unsupported_effect_type(self):
        """Test handling of unsupported effect type."""
        # Create a mock effect type that doesn't exist
        with pytest.raises(ValueError, match="Unsupported visual effect type"):
            effect_config = Mock()
            effect_config.type = "unsupported_type"
            self.processor.create_effect(effect_config)
    
    def test_apply_visual_effects_empty_list(self):
        """Test applying empty effects list."""
        result = self.processor.apply_visual_effects(
            self.text_element, [], self.texture_size
        )
        assert result is True
    
    def test_apply_visual_effects_success(self):
        """Test successful application of visual effects."""
        # Mock shader program object
        mock_program = Mock()
        mock_program.use.return_value = None
        mock_program.set_uniform.return_value = None
        
        # Mock shader operations
        self.mock_shader_manager.load_shader_program.return_value = mock_program
        
        effects = [
            VisualEffect(
                type=VisualEffectType.GLOW,
                intensity=0.8,
                color=(1.0, 1.0, 1.0, 1.0),
                parameters={'radius': 8.0}
            )
        ]
        
        result = self.processor.apply_visual_effects(
            self.text_element, effects, self.texture_size
        )
        assert result is True
    
    def test_get_supported_effect_types(self):
        """Test getting supported effect types."""
        types = self.processor.get_supported_effect_types()
        expected_types = [
            VisualEffectType.GLOW,
            VisualEffectType.OUTLINE,
            VisualEffectType.SHADOW,
            VisualEffectType.GRADIENT
        ]
        
        for effect_type in expected_types:
            assert effect_type in types
    
    def test_get_effect_parameters(self):
        """Test getting default effect parameters."""
        params = self.processor.get_effect_parameters(VisualEffectType.GLOW)
        assert 'radius' in params
        assert 'samples' in params
        assert 'falloff' in params
    
    def test_convenience_methods(self):
        """Test convenience methods for creating effects."""
        # Test glow effect creation
        glow = self.processor.create_glow_effect(
            intensity=0.8, 
            color=(1.0, 0.5, 0.0, 1.0), 
            radius=12.0
        )
        assert glow.type == VisualEffectType.GLOW
        assert glow.intensity == 0.8
        assert glow.parameters['radius'] == 12.0
        
        # Test outline effect creation
        outline = self.processor.create_outline_effect(
            intensity=1.0,
            color=(0.0, 0.0, 0.0, 1.0),
            width=3.0
        )
        assert outline.type == VisualEffectType.OUTLINE
        assert outline.parameters['width'] == 3.0
        
        # Test shadow effect creation
        shadow = self.processor.create_shadow_effect(
            intensity=0.7,
            offset_x=6.0,
            offset_y=6.0,
            blur=4.0
        )
        assert shadow.type == VisualEffectType.SHADOW
        assert shadow.parameters['offset_x'] == 6.0
        assert shadow.parameters['blur'] == 4.0
        
        # Test gradient effect creation
        gradient = self.processor.create_gradient_effect(
            intensity=1.0,
            gradient_type='radial',
            start_color=(1.0, 0.0, 0.0, 1.0),
            end_color=(0.0, 1.0, 0.0, 1.0),
            angle=45.0
        )
        assert gradient.type == VisualEffectType.GRADIENT
        assert gradient.parameters['type'] == 'radial'
        assert gradient.parameters['angle'] == 45.0


class TestGlowEffect:
    """Test cases for GlowEffect."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_shader_manager = Mock()
        self.effect_config = VisualEffect(
            type=VisualEffectType.GLOW,
            intensity=0.8,
            color=(1.0, 0.5, 0.0, 1.0),
            parameters={'radius': 10.0}
        )
        self.effect = GlowEffect(self.effect_config, self.mock_shader_manager)
        
        self.text_element = TextElement(
            content="Test",
            font_family="Arial",
            font_size=24.0,
            color=(1.0, 1.0, 1.0, 1.0),
            position=(100.0, 100.0),
            rotation=(0.0, 0.0, 0.0),
            effects=[]
        )
    
    def test_initialization_with_defaults(self):
        """Test glow effect initialization with default parameters."""
        config = VisualEffect(
            type=VisualEffectType.GLOW,
            intensity=1.0,
            color=(1.0, 1.0, 1.0, 1.0),
            parameters={}
        )
        effect = GlowEffect(config, self.mock_shader_manager)
        
        # Check default parameters were set
        assert effect.config.parameters['radius'] == 8.0
        assert effect.config.parameters['samples'] == 16
        assert effect.config.parameters['falloff'] == 1.0
    
    def test_get_shader_names(self):
        """Test getting shader names."""
        vertex, fragment = self.effect.get_shader_names()
        assert vertex == "glow_vertex"
        assert fragment == "glow_fragment"
    
    def test_set_shader_uniforms(self):
        """Test setting shader uniforms."""
        # Mock shader program object
        mock_program = Mock()
        mock_program.set_uniform.return_value = None
        self.effect._shader_program = mock_program
        
        texture_size = (256, 64)
        
        self.effect.set_shader_uniforms(self.text_element, texture_size)
        
        # Verify shader program calls
        mock_program.set_uniform.assert_called()
    
    def test_update_parameters(self):
        """Test updating effect parameters."""
        updates = {
            'intensity': 0.5,
            'color': (0.0, 1.0, 0.0, 1.0),
            'radius': 15.0
        }
        
        self.effect.update_parameters(updates)
        
        assert self.effect.config.intensity == 0.5
        assert self.effect.config.color == (0.0, 1.0, 0.0, 1.0)
        assert self.effect.config.parameters['radius'] == 15.0


class TestOutlineEffect:
    """Test cases for OutlineEffect."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_shader_manager = Mock()
        self.effect_config = VisualEffect(
            type=VisualEffectType.OUTLINE,
            intensity=1.0,
            color=(0.0, 0.0, 0.0, 1.0),
            parameters={'width': 3.0}
        )
        self.effect = OutlineEffect(self.effect_config, self.mock_shader_manager)
    
    def test_initialization_with_defaults(self):
        """Test outline effect initialization with default parameters."""
        config = VisualEffect(
            type=VisualEffectType.OUTLINE,
            intensity=1.0,
            color=(0.0, 0.0, 0.0, 1.0),
            parameters={}
        )
        effect = OutlineEffect(config, self.mock_shader_manager)
        
        # Check default parameters were set
        assert effect.config.parameters['width'] == 2.0
        assert effect.config.parameters['mode'] == 'outer'
        assert effect.config.parameters['smoothness'] == 1.0
    
    def test_get_shader_names(self):
        """Test getting shader names."""
        vertex, fragment = self.effect.get_shader_names()
        assert vertex == "outline_vertex"
        assert fragment == "outline_fragment"


class TestShadowEffect:
    """Test cases for ShadowEffect."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_shader_manager = Mock()
        self.effect_config = VisualEffect(
            type=VisualEffectType.SHADOW,
            intensity=0.7,
            color=(0.0, 0.0, 0.0, 0.8),
            parameters={'offset_x': 5.0, 'offset_y': 5.0, 'blur': 3.0}
        )
        self.effect = ShadowEffect(self.effect_config, self.mock_shader_manager)
    
    def test_initialization_with_defaults(self):
        """Test shadow effect initialization with default parameters."""
        config = VisualEffect(
            type=VisualEffectType.SHADOW,
            intensity=1.0,
            color=(0.0, 0.0, 0.0, 1.0),
            parameters={}
        )
        effect = ShadowEffect(config, self.mock_shader_manager)
        
        # Check default parameters were set
        assert effect.config.parameters['offset_x'] == 4.0
        assert effect.config.parameters['offset_y'] == 4.0
        assert effect.config.parameters['blur'] == 2.0
        assert effect.config.parameters['opacity'] == 0.7
    
    def test_get_shader_names(self):
        """Test getting shader names."""
        vertex, fragment = self.effect.get_shader_names()
        assert vertex == "shadow_vertex"
        assert fragment == "shadow_fragment"


class TestGradientEffect:
    """Test cases for GradientEffect."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_shader_manager = Mock()
        self.effect_config = VisualEffect(
            type=VisualEffectType.GRADIENT,
            intensity=1.0,
            color=(1.0, 0.0, 0.0, 1.0),
            parameters={
                'type': 'linear',
                'start_color': (1.0, 0.0, 0.0, 1.0),
                'end_color': (0.0, 0.0, 1.0, 1.0)
            }
        )
        self.effect = GradientEffect(self.effect_config, self.mock_shader_manager)
    
    def test_initialization_with_defaults(self):
        """Test gradient effect initialization with default parameters."""
        config = VisualEffect(
            type=VisualEffectType.GRADIENT,
            intensity=1.0,
            color=(1.0, 1.0, 1.0, 1.0),
            parameters={}
        )
        effect = GradientEffect(config, self.mock_shader_manager)
        
        # Check default parameters were set
        assert effect.config.parameters['type'] == 'linear'
        assert effect.config.parameters['direction'] == (1.0, 0.0)
        assert effect.config.parameters['center'] == (0.5, 0.5)
        assert effect.config.parameters['radius'] == 0.5
        assert effect.config.parameters['angle'] == 0.0
    
    def test_get_shader_names(self):
        """Test getting shader names."""
        vertex, fragment = self.effect.get_shader_names()
        assert vertex == "gradient_vertex"
        assert fragment == "gradient_fragment"
    
    def test_add_color_stop(self):
        """Test adding color stops to gradient."""
        self.effect.add_color_stop(0.5, (0.0, 1.0, 0.0, 1.0))
        
        stops = self.effect.get_color_stops()
        assert len(stops) == 1
        assert stops[0].position == 0.5
        assert stops[0].color == (0.0, 1.0, 0.0, 1.0)
    
    def test_multiple_color_stops_sorted(self):
        """Test that color stops are sorted by position."""
        self.effect.add_color_stop(0.8, (0.0, 1.0, 0.0, 1.0))
        self.effect.add_color_stop(0.2, (1.0, 1.0, 0.0, 1.0))
        self.effect.add_color_stop(0.5, (0.0, 0.0, 1.0, 1.0))
        
        stops = self.effect.get_color_stops()
        assert len(stops) == 3
        assert stops[0].position == 0.2
        assert stops[1].position == 0.5
        assert stops[2].position == 0.8
    
    def test_clear_color_stops(self):
        """Test clearing color stops."""
        self.effect.add_color_stop(0.5, (0.0, 1.0, 0.0, 1.0))
        assert len(self.effect.get_color_stops()) == 1
        
        self.effect.clear_color_stops()
        assert len(self.effect.get_color_stops()) == 0


class TestGradientStop:
    """Test cases for GradientStop."""
    
    def test_gradient_stop_creation(self):
        """Test creating gradient stop."""
        stop = GradientStop(
            position=0.5,
            color=(1.0, 0.0, 0.0, 1.0)
        )
        
        assert stop.position == 0.5
        assert stop.color == (1.0, 0.0, 0.0, 1.0)


if __name__ == '__main__':
    pytest.main([__file__])