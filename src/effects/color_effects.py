"""
Color effects implementation for text elements.

This module provides concrete implementations of color effects including:
- Rainbow cycling with HSV color space transitions
- Pulse animations with BPM synchronization
- Strobe effects with configurable flash patterns
- Color temperature shift effects with smooth transitions

All effects support real-time parameter adjustment and can be synchronized
to audio BPM for music-responsive animations.
"""

import math
import colorsys
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass

from ..core.models import ColorEffect, TextElement


@dataclass
class ColorState:
    """Current state of a color effect."""
    current_color: Tuple[float, float, float, float]  # RGBA
    is_active: bool
    progress: float  # 0.0 to 1.0
    cycle_count: int
    parameters: Dict[str, Any]


class BaseColorEffect(ABC):
    """
    Base class for all color effects.
    
    Provides common functionality for color manipulation, timing calculations,
    and BPM synchronization.
    """
    
    def __init__(self, effect_config: ColorEffect):
        """
        Initialize base color effect.
        
        Args:
            effect_config: Color effect configuration
        """
        self.config = effect_config
        self._start_time: Optional[float] = None
        self._last_bpm_beat: float = 0.0
        self._beat_count: int = 0
    
    @abstractmethod
    def calculate_color(self, current_time: float, base_color: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
        """
        Calculate the current color based on effect parameters and timing.
        
        Args:
            current_time: Current timeline time in seconds
            base_color: Base text color (RGBA)
            
        Returns:
            Modified color (RGBA)
        """
        pass
    
    def get_color_state(self, current_time: float, base_color: Tuple[float, float, float, float]) -> ColorState:
        """
        Get current color effect state.
        
        Args:
            current_time: Current timeline time
            base_color: Base text color
            
        Returns:
            Current color state
        """
        if self._start_time is None:
            self._start_time = current_time
        
        elapsed_time = current_time - self._start_time
        current_color = self.calculate_color(current_time, base_color)
        
        # Calculate progress based on effect speed
        cycle_duration = 1.0 / max(0.001, self.config.speed)  # Avoid division by zero
        progress = (elapsed_time % cycle_duration) / cycle_duration
        cycle_count = int(elapsed_time / cycle_duration)
        
        return ColorState(
            current_color=current_color,
            is_active=True,
            progress=progress,
            cycle_count=cycle_count,
            parameters={}
        )
    
    def _get_bpm_time(self, current_time: float) -> float:
        """
        Get BPM-synchronized time if BPM sync is enabled.
        
        Args:
            current_time: Current timeline time
            
        Returns:
            BPM-synchronized time or regular time
        """
        if not self.config.bpm_sync or not self.config.bpm:
            return current_time
        
        # Calculate beats per second
        beats_per_second = self.config.bpm / 60.0
        
        # Calculate current beat
        current_beat = current_time * beats_per_second
        
        # Synchronize to beat boundaries
        beat_progress = current_beat % 1.0
        
        return beat_progress
    
    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[float, float, float]:
        """
        Convert HSV color to RGB.
        
        Args:
            h: Hue (0.0 to 1.0)
            s: Saturation (0.0 to 1.0)
            v: Value/Brightness (0.0 to 1.0)
            
        Returns:
            RGB color tuple (0.0 to 1.0 each)
        """
        return colorsys.hsv_to_rgb(h, s, v)
    
    def _rgb_to_hsv(self, r: float, g: float, b: float) -> Tuple[float, float, float]:
        """
        Convert RGB color to HSV.
        
        Args:
            r: Red (0.0 to 1.0)
            g: Green (0.0 to 1.0)
            b: Blue (0.0 to 1.0)
            
        Returns:
            HSV color tuple (0.0 to 1.0 each)
        """
        return colorsys.rgb_to_hsv(r, g, b)
    
    def _interpolate_color(self, color1: Tuple[float, float, float, float], 
                          color2: Tuple[float, float, float, float], 
                          t: float) -> Tuple[float, float, float, float]:
        """
        Interpolate between two RGBA colors.
        
        Args:
            color1: First color (RGBA)
            color2: Second color (RGBA)
            t: Interpolation factor (0.0 to 1.0)
            
        Returns:
            Interpolated color (RGBA)
        """
        return (
            color1[0] + (color2[0] - color1[0]) * t,
            color1[1] + (color2[1] - color1[1]) * t,
            color1[2] + (color2[2] - color1[2]) * t,
            color1[3] + (color2[3] - color1[3]) * t
        )
    
    def update_parameters(self, parameter_updates: Dict[str, Any]) -> None:
        """
        Update effect parameters in real-time.
        
        Args:
            parameter_updates: Dictionary of parameter updates
        """
        for key, value in parameter_updates.items():
            if key == 'speed':
                self.config.speed = max(0.001, float(value))  # Minimum speed
            elif key == 'intensity':
                self.config.intensity = max(0.0, min(1.0, float(value)))
            elif key == 'bpm_sync':
                self.config.bpm_sync = bool(value)
            elif key == 'bpm':
                if value is not None:
                    self.config.bpm = max(1.0, float(value))  # Minimum BPM
                else:
                    self.config.bpm = None


class RainbowEffect(BaseColorEffect):
    """
    Rainbow cycling color effect.
    
    Cycles through the full HSV hue spectrum while maintaining the original
    saturation and brightness of the base color.
    """
    
    def __init__(self, effect_config: ColorEffect):
        """Initialize rainbow effect."""
        super().__init__(effect_config)
    
    def calculate_color(self, current_time: float, base_color: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
        """Calculate rainbow color at current time."""
        # Get BPM-synchronized time if enabled
        sync_time = self._get_bpm_time(current_time) if self.config.bpm_sync else current_time
        
        # Convert base color to HSV to preserve saturation and brightness
        base_hsv = self._rgb_to_hsv(base_color[0], base_color[1], base_color[2])
        
        # Calculate hue based on time and speed
        hue_cycle = (sync_time * self.config.speed) % 1.0
        
        # For rainbow effect, ensure minimum saturation for visible color changes
        saturation = max(base_hsv[1], 0.8)  # Use at least 80% saturation
        brightness = max(base_hsv[2], 0.5)  # Use at least 50% brightness
        
        # Apply intensity to control how much the hue changes
        if self.config.intensity < 1.0:
            # Blend between original hue and rainbow hue
            original_hue = base_hsv[0]
            rainbow_hue = hue_cycle
            final_hue = original_hue + (rainbow_hue - original_hue) * self.config.intensity
        else:
            final_hue = hue_cycle
        
        # Convert back to RGB with enhanced saturation
        rainbow_rgb = self._hsv_to_rgb(final_hue, saturation, brightness)
        
        # Blend with original color based on intensity
        if self.config.intensity < 1.0:
            return self._interpolate_color(base_color, 
                                         (rainbow_rgb[0], rainbow_rgb[1], rainbow_rgb[2], base_color[3]), 
                                         self.config.intensity)
        else:
            return (rainbow_rgb[0], rainbow_rgb[1], rainbow_rgb[2], base_color[3])


class PulseEffect(BaseColorEffect):
    """
    Pulse color effect.
    
    Pulses between the base color and a target color with configurable
    pulse rate and BPM synchronization.
    """
    
    def __init__(self, effect_config: ColorEffect):
        """Initialize pulse effect."""
        super().__init__(effect_config)
        
        # Default pulse parameters
        self.pulse_color = (1.0, 1.0, 1.0, 1.0)  # White by default
        self.pulse_curve = 'sine'  # 'sine', 'triangle', 'square'
    
    def set_pulse_color(self, color: Tuple[float, float, float, float]) -> None:
        """
        Set the target pulse color.
        
        Args:
            color: Target pulse color (RGBA)
        """
        self.pulse_color = color
    
    def set_pulse_curve(self, curve: str) -> None:
        """
        Set the pulse curve type.
        
        Args:
            curve: Pulse curve ('sine', 'triangle', 'square')
        """
        self.pulse_curve = curve
    
    def calculate_color(self, current_time: float, base_color: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
        """Calculate pulse color at current time."""
        # Get BPM-synchronized time if enabled
        if self.config.bpm_sync and self.config.bpm:
            # Synchronize to BPM beats
            beats_per_second = self.config.bpm / 60.0
            pulse_time = (current_time * beats_per_second * self.config.speed) % 1.0
        else:
            pulse_time = (current_time * self.config.speed) % 1.0
        
        # Calculate pulse factor based on curve type
        if self.pulse_curve == 'sine':
            pulse_factor = (math.sin(pulse_time * 2 * math.pi) + 1.0) / 2.0
        elif self.pulse_curve == 'triangle':
            pulse_factor = 1.0 - abs(pulse_time * 2.0 - 1.0)
        elif self.pulse_curve == 'square':
            pulse_factor = 1.0 if pulse_time < 0.5 else 0.0
        else:
            pulse_factor = pulse_time  # Linear fallback
        
        # Apply intensity
        pulse_factor *= self.config.intensity
        
        # Interpolate between base color and pulse color
        return self._interpolate_color(base_color, self.pulse_color, pulse_factor)


class StrobeEffect(BaseColorEffect):
    """
    Strobe color effect.
    
    Creates rapid flashing between the base color and a strobe color
    with configurable flash patterns and BPM synchronization.
    """
    
    def __init__(self, effect_config: ColorEffect):
        """Initialize strobe effect."""
        super().__init__(effect_config)
        
        # Default strobe parameters
        self.strobe_color = (1.0, 1.0, 1.0, 1.0)  # White by default
        self.flash_duration = 0.1  # Duration of each flash in seconds
        self.pattern = 'single'  # 'single', 'double', 'triple', 'random'
    
    def set_strobe_color(self, color: Tuple[float, float, float, float]) -> None:
        """
        Set the strobe flash color.
        
        Args:
            color: Strobe flash color (RGBA)
        """
        self.strobe_color = color
    
    def set_flash_duration(self, duration: float) -> None:
        """
        Set the flash duration.
        
        Args:
            duration: Flash duration in seconds
        """
        self.flash_duration = max(0.01, duration)
    
    def set_pattern(self, pattern: str) -> None:
        """
        Set the strobe pattern.
        
        Args:
            pattern: Strobe pattern ('single', 'double', 'triple', 'random')
        """
        self.pattern = pattern
    
    def calculate_color(self, current_time: float, base_color: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
        """Calculate strobe color at current time."""
        # Get BPM-synchronized time if enabled
        if self.config.bpm_sync and self.config.bpm:
            beats_per_second = self.config.bpm / 60.0
            cycle_time = (current_time * beats_per_second * self.config.speed) % 1.0
        else:
            cycle_duration = 1.0 / max(0.001, self.config.speed)
            cycle_time = (current_time % cycle_duration) / cycle_duration
        
        # Determine if we should flash based on pattern
        should_flash = self._should_flash(cycle_time)
        
        if should_flash:
            # Apply intensity to strobe color
            strobe_intensity = self.config.intensity
            return self._interpolate_color(base_color, self.strobe_color, strobe_intensity)
        else:
            return base_color
    
    def _should_flash(self, cycle_time: float) -> bool:
        """
        Determine if strobe should flash at given cycle time.
        
        Args:
            cycle_time: Time within current cycle (0.0 to 1.0)
            
        Returns:
            True if should flash, False otherwise
        """
        flash_ratio = self.flash_duration * self.config.speed
        
        if self.pattern == 'single':
            return cycle_time < flash_ratio
        elif self.pattern == 'double':
            return (cycle_time < flash_ratio or 
                   (0.5 <= cycle_time < 0.5 + flash_ratio))
        elif self.pattern == 'triple':
            return (cycle_time < flash_ratio or 
                   (0.33 <= cycle_time < 0.33 + flash_ratio) or
                   (0.66 <= cycle_time < 0.66 + flash_ratio))
        elif self.pattern == 'random':
            # Use cycle_time as seed for pseudo-random flashing
            import random
            random.seed(int(cycle_time * 1000))
            return random.random() < flash_ratio * 2  # Adjust probability
        else:
            return cycle_time < flash_ratio  # Default to single


class ColorTemperatureEffect(BaseColorEffect):
    """
    Color temperature shift effect.
    
    Shifts the color temperature of text between warm and cool tones
    with smooth transitions and configurable temperature range.
    """
    
    def __init__(self, effect_config: ColorEffect):
        """Initialize color temperature effect."""
        super().__init__(effect_config)
        
        # Default temperature parameters
        self.min_temperature = 2000  # Kelvin (warm)
        self.max_temperature = 8000  # Kelvin (cool)
        self.transition_curve = 'sine'  # 'sine', 'linear', 'ease_in_out'
    
    def set_temperature_range(self, min_temp: float, max_temp: float) -> None:
        """
        Set the temperature range for the effect.
        
        Args:
            min_temp: Minimum temperature in Kelvin
            max_temp: Maximum temperature in Kelvin
        """
        self.min_temperature = max(1000, min_temp)
        self.max_temperature = min(20000, max_temp)
        
        if self.min_temperature >= self.max_temperature:
            self.max_temperature = self.min_temperature + 1000
    
    def set_transition_curve(self, curve: str) -> None:
        """
        Set the transition curve type.
        
        Args:
            curve: Transition curve ('sine', 'linear', 'ease_in_out')
        """
        self.transition_curve = curve
    
    def calculate_color(self, current_time: float, base_color: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
        """Calculate color temperature shifted color at current time."""
        # Get BPM-synchronized time if enabled
        sync_time = self._get_bpm_time(current_time) if self.config.bpm_sync else current_time
        
        # Calculate temperature cycle
        cycle_time = (sync_time * self.config.speed) % 1.0
        
        # Apply transition curve
        if self.transition_curve == 'sine':
            temp_factor = (math.sin(cycle_time * 2 * math.pi - math.pi/2) + 1.0) / 2.0
        elif self.transition_curve == 'ease_in_out':
            temp_factor = 0.5 * (1.0 + math.sin((cycle_time - 0.5) * math.pi))
        else:  # linear
            temp_factor = cycle_time
        
        # Calculate current temperature
        current_temp = self.min_temperature + (self.max_temperature - self.min_temperature) * temp_factor
        
        # Convert base color to temperature-shifted color
        temp_color = self._apply_color_temperature(base_color, current_temp)
        
        # Apply intensity
        return self._interpolate_color(base_color, temp_color, self.config.intensity)
    
    def _apply_color_temperature(self, color: Tuple[float, float, float, float], 
                               temperature: float) -> Tuple[float, float, float, float]:
        """
        Apply color temperature shift to a color.
        
        Args:
            color: Original color (RGBA)
            temperature: Color temperature in Kelvin
            
        Returns:
            Temperature-shifted color (RGBA)
        """
        # Simplified color temperature calculation
        # Based on approximation of blackbody radiation
        
        temp = temperature / 100.0
        
        # Calculate red component
        if temp <= 66:
            red = 1.0
        else:
            red = temp - 60
            red = 329.698727446 * (red ** -0.1332047592)
            red = max(0.0, min(1.0, red / 255.0))
        
        # Calculate green component
        if temp <= 66:
            green = temp
            green = 99.4708025861 * math.log(green) - 161.1195681661
        else:
            green = temp - 60
            green = 288.1221695283 * (green ** -0.0755148492)
        green = max(0.0, min(1.0, green / 255.0))
        
        # Calculate blue component
        if temp >= 66:
            blue = 1.0
        elif temp <= 19:
            blue = 0.0
        else:
            blue = temp - 10
            blue = 138.5177312231 * math.log(blue) - 305.0447927307
            blue = max(0.0, min(1.0, blue / 255.0))
        
        # Apply temperature shift to original color
        temp_multiplier = (red, green, blue)
        
        shifted_color = (
            color[0] * temp_multiplier[0],
            color[1] * temp_multiplier[1],
            color[2] * temp_multiplier[2],
            color[3]  # Keep original alpha
        )
        
        return shifted_color


class ColorEffectProcessor:
    """
    Main processor for managing and applying color effects to text elements.
    
    This class coordinates multiple color effects, handles BPM synchronization,
    and provides real-time parameter adjustment and color blending.
    """
    
    def __init__(self):
        """Initialize color effect processor."""
        self._effect_factories = {
            'rainbow': lambda config: RainbowEffect(config),
            'pulse': lambda config: PulseEffect(config),
            'strobe': lambda config: StrobeEffect(config),
            'temperature': lambda config: ColorTemperatureEffect(config)
        }
        self._active_effects: Dict[str, BaseColorEffect] = {}
    
    def create_effect(self, effect_config: ColorEffect) -> BaseColorEffect:
        """
        Create a color effect instance from configuration.
        
        Args:
            effect_config: Color effect configuration
            
        Returns:
            Color effect instance
            
        Raises:
            ValueError: If effect type is not supported
        """
        factory = self._effect_factories.get(effect_config.type)
        if not factory:
            raise ValueError(f"Unsupported color effect type: {effect_config.type}")
        
        return factory(effect_config)
    
    def apply_color_effects(self, text_element: TextElement, effects: List[ColorEffect],
                          current_time: float) -> Tuple[float, float, float, float]:
        """
        Apply multiple color effects to a text element.
        
        Args:
            text_element: Text element to apply effects to
            effects: List of color effects to apply
            current_time: Current timeline time
            
        Returns:
            Final color after applying all effects (RGBA)
        """
        if not effects:
            return text_element.color
        
        current_color = text_element.color
        
        for effect_config in effects:
            try:
                effect = self.create_effect(effect_config)
                current_color = effect.calculate_color(current_time, current_color)
                
                # Store active effect for parameter updates
                effect_id = f"{effect_config.type}_{id(effect_config)}"
                self._active_effects[effect_id] = effect
                
            except Exception as e:
                print(f"Error applying color effect {effect_config.type}: {e}")
                continue
        
        return current_color
    
    def update_effect_parameters(self, effect_id: str, 
                               parameter_updates: Dict[str, Any]) -> bool:
        """
        Update color effect parameters in real-time.
        
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
            print(f"Error updating color effect parameters: {e}")
            return False
    
    def get_supported_effect_types(self) -> List[str]:
        """Get list of supported color effect types."""
        return list(self._effect_factories.keys())
    
    def cleanup_effects(self) -> None:
        """Clean up all active effects."""
        self._active_effects.clear()
    
    def create_rainbow_effect(self, speed: float = 1.0, intensity: float = 1.0,
                            bpm_sync: bool = False, bpm: Optional[float] = None) -> ColorEffect:
        """
        Create a rainbow cycling effect with common parameters.
        
        Args:
            speed: Cycling speed (cycles per second)
            intensity: Effect intensity (0.0 to 1.0)
            bpm_sync: Whether to synchronize to BPM
            bpm: BPM value for synchronization
            
        Returns:
            Configured rainbow effect
        """
        return ColorEffect(
            type='rainbow',
            speed=speed,
            intensity=intensity,
            bpm_sync=bpm_sync,
            bpm=bpm
        )
    
    def create_pulse_effect(self, speed: float = 2.0, intensity: float = 1.0,
                          bpm_sync: bool = False, bpm: Optional[float] = None) -> ColorEffect:
        """
        Create a pulse effect with common parameters.
        
        Args:
            speed: Pulse speed (pulses per second or per beat if BPM synced)
            intensity: Effect intensity (0.0 to 1.0)
            bpm_sync: Whether to synchronize to BPM
            bpm: BPM value for synchronization
            
        Returns:
            Configured pulse effect
        """
        return ColorEffect(
            type='pulse',
            speed=speed,
            intensity=intensity,
            bpm_sync=bpm_sync,
            bpm=bpm
        )
    
    def create_strobe_effect(self, speed: float = 10.0, intensity: float = 1.0,
                           bpm_sync: bool = False, bpm: Optional[float] = None) -> ColorEffect:
        """
        Create a strobe effect with common parameters.
        
        Args:
            speed: Strobe speed (flashes per second or per beat if BPM synced)
            intensity: Effect intensity (0.0 to 1.0)
            bpm_sync: Whether to synchronize to BPM
            bpm: BPM value for synchronization
            
        Returns:
            Configured strobe effect
        """
        return ColorEffect(
            type='strobe',
            speed=speed,
            intensity=intensity,
            bpm_sync=bpm_sync,
            bpm=bpm
        )
    
    def create_temperature_effect(self, speed: float = 0.5, intensity: float = 1.0,
                                bpm_sync: bool = False, bpm: Optional[float] = None) -> ColorEffect:
        """
        Create a color temperature effect with common parameters.
        
        Args:
            speed: Temperature shift speed (cycles per second)
            intensity: Effect intensity (0.0 to 1.0)
            bpm_sync: Whether to synchronize to BPM
            bpm: BPM value for synchronization
            
        Returns:
            Configured temperature effect
        """
        return ColorEffect(
            type='temperature',
            speed=speed,
            intensity=intensity,
            bpm_sync=bpm_sync,
            bpm=bpm
        )