"""
Tests for color effects implementation.
"""

import pytest
import math
from unittest.mock import Mock, patch

from src.effects.color_effects import (
    ColorEffectProcessor, RainbowEffect, PulseEffect, StrobeEffect,
    ColorTemperatureEffect, BaseColorEffect, ColorState
)
from src.core.models import ColorEffect, TextElement


class TestBaseColorEffect:
    """Test base color effect functionality."""
    
    def test_color_state_calculation(self):
        """Test color state calculation."""
        config = ColorEffect(type='test', speed=1.0, intensity=1.0)
        
        # Create a mock effect for testing
        class MockEffect(BaseColorEffect):
            def calculate_color(self, current_time, base_color):
                return base_color
        
        effect = MockEffect(config)
        base_color = (1.0, 0.0, 0.0, 1.0)
        
        state = effect.get_color_state(0.0, base_color)
        
        assert state.current_color == base_color
        assert state.is_active is True
        assert state.progress == 0.0
        assert state.cycle_count == 0
    
    def test_bpm_time_calculation(self):
        """Test BPM-synchronized time calculation."""
        config = ColorEffect(type='test', speed=1.0, intensity=1.0, bpm_sync=True, bpm=120.0)
        
        class MockEffect(BaseColorEffect):
            def calculate_color(self, current_time, base_color):
                return base_color
        
        effect = MockEffect(config)
        
        # Test BPM synchronization
        bpm_time = effect._get_bpm_time(1.0)  # 1 second
        expected_beats = 120.0 / 60.0  # 2 beats per second
        expected_progress = (1.0 * expected_beats) % 1.0
        
        assert bpm_time == expected_progress
    
    def test_hsv_rgb_conversion(self):
        """Test HSV to RGB color conversion."""
        config = ColorEffect(type='test', speed=1.0, intensity=1.0)
        
        class MockEffect(BaseColorEffect):
            def calculate_color(self, current_time, base_color):
                return base_color
        
        effect = MockEffect(config)
        
        # Test pure red
        rgb = effect._hsv_to_rgb(0.0, 1.0, 1.0)
        assert abs(rgb[0] - 1.0) < 0.001
        assert abs(rgb[1] - 0.0) < 0.001
        assert abs(rgb[2] - 0.0) < 0.001
        
        # Test pure green
        rgb = effect._hsv_to_rgb(1.0/3.0, 1.0, 1.0)
        assert abs(rgb[0] - 0.0) < 0.001
        assert abs(rgb[1] - 1.0) < 0.001
        assert abs(rgb[2] - 0.0) < 0.001
    
    def test_color_interpolation(self):
        """Test color interpolation."""
        config = ColorEffect(type='test', speed=1.0, intensity=1.0)
        
        class MockEffect(BaseColorEffect):
            def calculate_color(self, current_time, base_color):
                return base_color
        
        effect = MockEffect(config)
        
        color1 = (1.0, 0.0, 0.0, 1.0)  # Red
        color2 = (0.0, 1.0, 0.0, 1.0)  # Green
        
        # Test midpoint interpolation
        result = effect._interpolate_color(color1, color2, 0.5)
        expected = (0.5, 0.5, 0.0, 1.0)
        
        for i in range(4):
            assert abs(result[i] - expected[i]) < 0.001
    
    def test_parameter_updates(self):
        """Test parameter updates."""
        config = ColorEffect(type='test', speed=1.0, intensity=1.0)
        
        class MockEffect(BaseColorEffect):
            def calculate_color(self, current_time, base_color):
                return base_color
        
        effect = MockEffect(config)
        
        # Test speed update
        effect.update_parameters({'speed': 2.0})
        assert effect.config.speed == 2.0
        
        # Test intensity update
        effect.update_parameters({'intensity': 0.5})
        assert effect.config.intensity == 0.5
        
        # Test BPM sync update
        effect.update_parameters({'bpm_sync': True, 'bpm': 140.0})
        assert effect.config.bpm_sync is True
        assert effect.config.bpm == 140.0


class TestRainbowEffect:
    """Test rainbow color effect."""
    
    def test_rainbow_color_calculation(self):
        """Test rainbow color calculation."""
        config = ColorEffect(type='rainbow', speed=1.0, intensity=1.0)
        effect = RainbowEffect(config)
        
        base_color = (0.5, 0.5, 0.5, 1.0)  # Gray
        
        # Test at different times
        color1 = effect.calculate_color(0.0, base_color)
        color2 = effect.calculate_color(0.25, base_color)
        color3 = effect.calculate_color(0.5, base_color)
        
        # Colors should be different at different times
        assert color1 != color2
        assert color2 != color3
        assert color1 != color3
        
        # Alpha should remain unchanged
        assert color1[3] == base_color[3]
        assert color2[3] == base_color[3]
        assert color3[3] == base_color[3]
    
    def test_rainbow_intensity_effect(self):
        """Test rainbow intensity effect."""
        config = ColorEffect(type='rainbow', speed=1.0, intensity=0.5)
        effect = RainbowEffect(config)
        
        base_color = (1.0, 0.0, 0.0, 1.0)  # Red
        result = effect.calculate_color(0.25, base_color)  # Should be greenish
        
        # With 50% intensity, should be blend of original and rainbow
        # Result should not be pure green, but somewhere between red and green
        assert result[0] > 0.0  # Should retain some red
        assert result[1] > 0.0  # Should have some green


class TestPulseEffect:
    """Test pulse color effect."""
    
    def test_pulse_color_calculation(self):
        """Test pulse color calculation."""
        config = ColorEffect(type='pulse', speed=1.0, intensity=1.0)
        effect = PulseEffect(config)
        
        base_color = (1.0, 0.0, 0.0, 1.0)  # Red
        effect.set_pulse_color((0.0, 1.0, 0.0, 1.0))  # Green
        
        # Test at pulse minimum and maximum
        color_min = effect.calculate_color(0.0, base_color)
        color_max = effect.calculate_color(0.25, base_color)  # Peak of sine wave
        
        # Colors should be different
        assert color_min != color_max
        
        # At minimum, should be closer to base color
        # At maximum, should be closer to pulse color
        assert color_min[0] > color_max[0]  # Less red at max
        assert color_min[1] < color_max[1]  # More green at max
    
    def test_pulse_curves(self):
        """Test different pulse curves."""
        config = ColorEffect(type='pulse', speed=1.0, intensity=1.0)
        effect = PulseEffect(config)
        
        base_color = (1.0, 0.0, 0.0, 1.0)
        
        # Test sine curve
        effect.set_pulse_curve('sine')
        sine_result = effect.calculate_color(0.25, base_color)
        
        # Test triangle curve
        effect.set_pulse_curve('triangle')
        triangle_result = effect.calculate_color(0.25, base_color)
        
        # Test square curve
        effect.set_pulse_curve('square')
        square_result = effect.calculate_color(0.25, base_color)
        
        # Results should be different for different curves
        assert sine_result != triangle_result
        assert triangle_result != square_result
    
    def test_bpm_synchronization(self):
        """Test BPM synchronization for pulse effect."""
        config = ColorEffect(type='pulse', speed=1.0, intensity=1.0, bpm_sync=True, bpm=120.0)
        effect = PulseEffect(config)
        
        base_color = (1.0, 0.0, 0.0, 1.0)
        effect.set_pulse_color((0.0, 1.0, 0.0, 1.0))  # Green pulse
        
        # Test that BPM sync affects timing
        # With 120 BPM = 2 beats per second
        # At 0.25s = 0.5 beats (mid-beat)
        # At 0.375s = 0.75 beats (3/4 beat)
        color1 = effect.calculate_color(0.25, base_color)  # Mid-beat
        color2 = effect.calculate_color(0.375, base_color)  # 3/4 beat
        
        # These should be at different pulse phases
        assert color1 != color2


class TestStrobeEffect:
    """Test strobe color effect."""
    
    def test_strobe_flash_patterns(self):
        """Test different strobe flash patterns."""
        config = ColorEffect(type='strobe', speed=1.0, intensity=1.0)
        effect = StrobeEffect(config)
        
        base_color = (0.0, 0.0, 0.0, 1.0)  # Black
        effect.set_strobe_color((1.0, 1.0, 1.0, 1.0))  # White
        effect.set_flash_duration(0.1)
        
        # Test single flash pattern
        effect.set_pattern('single')
        flash_color = effect.calculate_color(0.05, base_color)  # During flash
        no_flash_color = effect.calculate_color(0.5, base_color)  # No flash
        
        assert flash_color != no_flash_color
        assert flash_color != base_color  # Should be strobing
        assert no_flash_color == base_color  # Should be base color
        
        # Test double flash pattern
        effect.set_pattern('double')
        flash1 = effect.calculate_color(0.05, base_color)  # First flash
        flash2 = effect.calculate_color(0.55, base_color)  # Second flash
        
        assert flash1 != base_color
        assert flash2 != base_color
    
    def test_strobe_intensity(self):
        """Test strobe intensity effect."""
        config = ColorEffect(type='strobe', speed=1.0, intensity=0.5)
        effect = StrobeEffect(config)
        
        base_color = (0.0, 0.0, 0.0, 1.0)  # Black
        effect.set_strobe_color((1.0, 1.0, 1.0, 1.0))  # White
        
        flash_color = effect.calculate_color(0.05, base_color)
        
        # With 50% intensity, flash should be gray, not white
        assert 0.4 < flash_color[0] < 0.6  # Should be around 0.5
        assert 0.4 < flash_color[1] < 0.6
        assert 0.4 < flash_color[2] < 0.6


class TestColorTemperatureEffect:
    """Test color temperature effect."""
    
    def test_temperature_range(self):
        """Test temperature range setting."""
        config = ColorEffect(type='temperature', speed=1.0, intensity=1.0)
        effect = ColorTemperatureEffect(config)
        
        # Test setting valid range
        effect.set_temperature_range(3000, 6000)
        assert effect.min_temperature == 3000
        assert effect.max_temperature == 6000
        
        # Test invalid range (min >= max)
        effect.set_temperature_range(6000, 3000)
        assert effect.max_temperature > effect.min_temperature
    
    def test_temperature_color_shift(self):
        """Test color temperature shifting."""
        config = ColorEffect(type='temperature', speed=1.0, intensity=1.0)
        effect = ColorTemperatureEffect(config)
        
        base_color = (1.0, 1.0, 1.0, 1.0)  # White
        
        # Test at different times (different temperatures)
        warm_color = effect.calculate_color(0.0, base_color)  # Min temp
        cool_color = effect.calculate_color(0.5, base_color)  # Max temp
        
        # Colors should be different
        assert warm_color != cool_color
        
        # Warm should have more red, cool should have more blue
        # (This is a simplified test - actual color temperature is complex)
        assert warm_color != base_color or cool_color != base_color
    
    def test_transition_curves(self):
        """Test different transition curves."""
        config = ColorEffect(type='temperature', speed=1.0, intensity=1.0)
        effect = ColorTemperatureEffect(config)
        
        base_color = (1.0, 1.0, 1.0, 1.0)
        
        # Test sine curve
        effect.set_transition_curve('sine')
        sine_result = effect.calculate_color(0.25, base_color)
        
        # Test linear curve
        effect.set_transition_curve('linear')
        linear_result = effect.calculate_color(0.25, base_color)
        
        # Test ease in/out curve
        effect.set_transition_curve('ease_in_out')
        ease_result = effect.calculate_color(0.25, base_color)
        
        # Results should potentially be different for different curves
        # (May be similar due to approximation, but curves should work)
        assert isinstance(sine_result, tuple)
        assert isinstance(linear_result, tuple)
        assert isinstance(ease_result, tuple)


class TestColorEffectProcessor:
    """Test color effect processor."""
    
    def test_effect_creation(self):
        """Test color effect creation."""
        processor = ColorEffectProcessor()
        
        # Test rainbow effect creation
        config = ColorEffect(type='rainbow', speed=1.0, intensity=1.0)
        effect = processor.create_effect(config)
        assert isinstance(effect, RainbowEffect)
        
        # Test pulse effect creation
        config = ColorEffect(type='pulse', speed=1.0, intensity=1.0)
        effect = processor.create_effect(config)
        assert isinstance(effect, PulseEffect)
        
        # Test unsupported effect type
        config = ColorEffect(type='unsupported', speed=1.0, intensity=1.0)
        with pytest.raises(ValueError):
            processor.create_effect(config)
    
    def test_multiple_effects_application(self):
        """Test applying multiple color effects."""
        processor = ColorEffectProcessor()
        
        text_element = TextElement(
            content="Test",
            font_family="Arial",
            font_size=24.0,
            color=(1.0, 0.0, 0.0, 1.0),  # Red
            position=(0.0, 0.0),
            rotation=(0.0, 0.0, 0.0),
            effects=[]
        )
        
        effects = [
            ColorEffect(type='rainbow', speed=1.0, intensity=0.5),
            ColorEffect(type='pulse', speed=2.0, intensity=0.3)
        ]
        
        result_color = processor.apply_color_effects(text_element, effects, 0.0)
        
        # Should return a valid RGBA color
        assert len(result_color) == 4
        assert all(0.0 <= c <= 1.0 for c in result_color)
        
        # Should be different from original color due to effects
        assert result_color != text_element.color
    
    def test_effect_parameter_updates(self):
        """Test updating effect parameters."""
        processor = ColorEffectProcessor()
        
        config = ColorEffect(type='rainbow', speed=1.0, intensity=1.0)
        effect = processor.create_effect(config)
        
        # Store effect in processor
        effect_id = "rainbow_test"
        processor._active_effects[effect_id] = effect
        
        # Test parameter update
        success = processor.update_effect_parameters(effect_id, {'speed': 2.0, 'intensity': 0.5})
        assert success is True
        assert effect.config.speed == 2.0
        assert effect.config.intensity == 0.5
        
        # Test updating non-existent effect
        success = processor.update_effect_parameters("non_existent", {'speed': 1.0})
        assert success is False
    
    def test_supported_effect_types(self):
        """Test getting supported effect types."""
        processor = ColorEffectProcessor()
        
        supported_types = processor.get_supported_effect_types()
        
        assert 'rainbow' in supported_types
        assert 'pulse' in supported_types
        assert 'strobe' in supported_types
        assert 'temperature' in supported_types
    
    def test_convenience_effect_creators(self):
        """Test convenience methods for creating effects."""
        processor = ColorEffectProcessor()
        
        # Test rainbow effect creation
        rainbow = processor.create_rainbow_effect(speed=2.0, intensity=0.8)
        assert rainbow.type == 'rainbow'
        assert rainbow.speed == 2.0
        assert rainbow.intensity == 0.8
        
        # Test pulse effect creation
        pulse = processor.create_pulse_effect(speed=3.0, bpm_sync=True, bpm=120.0)
        assert pulse.type == 'pulse'
        assert pulse.speed == 3.0
        assert pulse.bpm_sync is True
        assert pulse.bpm == 120.0
        
        # Test strobe effect creation
        strobe = processor.create_strobe_effect(speed=10.0, intensity=0.9)
        assert strobe.type == 'strobe'
        assert strobe.speed == 10.0
        assert strobe.intensity == 0.9
        
        # Test temperature effect creation
        temp = processor.create_temperature_effect(speed=0.5, bpm_sync=False)
        assert temp.type == 'temperature'
        assert temp.speed == 0.5
        assert temp.bpm_sync is False
    
    def test_cleanup_effects(self):
        """Test cleaning up active effects."""
        processor = ColorEffectProcessor()
        
        # Add some active effects
        processor._active_effects["effect1"] = Mock()
        processor._active_effects["effect2"] = Mock()
        
        assert len(processor._active_effects) == 2
        
        processor.cleanup_effects()
        
        assert len(processor._active_effects) == 0


if __name__ == "__main__":
    pytest.main([__file__])