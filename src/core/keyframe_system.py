"""
Keyframe system for managing keyframe creation, editing, and interpolation.
"""

import math
from typing import Any, Dict, List, Optional, Tuple, Union
from .models import Keyframe, InterpolationType, EasingType


class KeyframeSystem:
    """
    Specialized system for keyframe operations and interpolation calculations.
    
    This class provides advanced keyframe manipulation capabilities including:
    - Keyframe creation with validation
    - Advanced interpolation algorithms
    - Easing curve calculations
    - Keyframe selection and manipulation utilities
    """
    
    def __init__(self):
        """Initialize keyframe system."""
        pass
    
    def create_keyframe(self, time: float, properties: Dict[str, Any], 
                       interpolation_type: InterpolationType = InterpolationType.LINEAR) -> Keyframe:
        """
        Create a new keyframe with validation.
        
        Args:
            time: Time position for the keyframe
            properties: Dictionary of properties to animate
            interpolation_type: Type of interpolation to use
            
        Returns:
            New Keyframe instance
        """
        # Validate time
        if time < 0:
            raise ValueError("Keyframe time cannot be negative")
        
        # Validate properties
        if not properties:
            raise ValueError("Keyframe must have at least one property")
        
        # Create and validate keyframe
        keyframe = Keyframe(
            time=time,
            properties=properties.copy(),
            interpolation_type=interpolation_type
        )
        
        validation = keyframe.validate()
        if not validation.is_valid:
            raise ValueError(f"Invalid keyframe: {validation.error_message}")
        
        return keyframe
    
    def interpolate_between(self, kf1: Keyframe, kf2: Keyframe, t: float, 
                           easing: EasingType = EasingType.LINEAR) -> Dict[str, Any]:
        """
        Interpolate properties between two keyframes with easing.
        
        Args:
            kf1: First keyframe (earlier in time)
            kf2: Second keyframe (later in time)
            t: Interpolation factor (0.0 to 1.0)
            easing: Easing curve to apply
            
        Returns:
            Dictionary of interpolated property values
        """
        if kf1.time == kf2.time:
            return kf2.properties.copy()
        
        # Clamp t to valid range
        t = max(0.0, min(1.0, t))
        
        # Apply easing curve
        eased_t = self._apply_easing(t, easing)
        
        # Handle step interpolation
        if kf2.interpolation_type == InterpolationType.STEP:
            eased_t = 0.0 if eased_t < 1.0 else 1.0
        elif kf2.interpolation_type == InterpolationType.BEZIER:
            # Apply cubic bezier curve
            eased_t = self._cubic_bezier(eased_t)
        
        # Interpolate each property
        result = {}
        all_keys = set(kf1.properties.keys()) | set(kf2.properties.keys())
        
        for key in all_keys:
            val1 = kf1.properties.get(key)
            val2 = kf2.properties.get(key)
            
            if val1 is not None and val2 is not None:
                result[key] = self._interpolate_value(val1, val2, eased_t)
            elif val1 is not None:
                result[key] = val1
            elif val2 is not None:
                result[key] = val2
        
        return result
    
    def _apply_easing(self, t: float, easing: EasingType) -> float:
        """
        Apply easing curve to interpolation factor.
        
        Args:
            t: Input factor (0.0 to 1.0)
            easing: Easing type to apply
            
        Returns:
            Eased interpolation factor
        """
        if easing == EasingType.LINEAR:
            return t
        elif easing == EasingType.EASE_IN:
            return t * t
        elif easing == EasingType.EASE_OUT:
            return 1.0 - (1.0 - t) * (1.0 - t)
        elif easing == EasingType.EASE_IN_OUT:
            if t < 0.5:
                return 2.0 * t * t
            else:
                return 1.0 - 2.0 * (1.0 - t) * (1.0 - t)
        elif easing == EasingType.BOUNCE:
            return self._bounce_easing(t)
        elif easing == EasingType.ELASTIC:
            return self._elastic_easing(t)
        else:
            return t
    
    def _bounce_easing(self, t: float) -> float:
        """Apply bounce easing curve."""
        if t < 1.0 / 2.75:
            return 7.5625 * t * t
        elif t < 2.0 / 2.75:
            t -= 1.5 / 2.75
            return 7.5625 * t * t + 0.75
        elif t < 2.5 / 2.75:
            t -= 2.25 / 2.75
            return 7.5625 * t * t + 0.9375
        else:
            t -= 2.625 / 2.75
            return 7.5625 * t * t + 0.984375
    
    def _elastic_easing(self, t: float) -> float:
        """Apply elastic easing curve."""
        if t == 0.0 or t == 1.0:
            return t
        
        p = 0.3
        s = p / 4.0
        return -(math.pow(2, 10 * (t - 1)) * math.sin((t - 1 - s) * (2 * math.pi) / p))
    
    def _cubic_bezier(self, t: float, p1: float = 0.25, p2: float = 0.75) -> float:
        """
        Apply cubic bezier curve with control points.
        
        Args:
            t: Input factor
            p1: First control point
            p2: Second control point
            
        Returns:
            Bezier-curved factor
        """
        # Simplified cubic bezier calculation
        return 3 * (1 - t) * (1 - t) * t * p1 + 3 * (1 - t) * t * t * p2 + t * t * t
    
    def _interpolate_value(self, val1: Any, val2: Any, t: float) -> Any:
        """
        Interpolate between two values based on their types.
        
        Args:
            val1: First value
            val2: Second value
            t: Interpolation factor (0.0 to 1.0)
            
        Returns:
            Interpolated value
        """
        # Handle numeric types
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            result = val1 + (val2 - val1) * t
            # Preserve integer type if both inputs are integers
            if isinstance(val1, int) and isinstance(val2, int):
                return int(round(result))
            return result
        
        # Handle tuples/lists (colors, positions, rotations, etc.)
        if isinstance(val1, (tuple, list)) and isinstance(val2, (tuple, list)):
            if len(val1) == len(val2):
                result = []
                for v1, v2 in zip(val1, val2):
                    if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                        interpolated = v1 + (v2 - v1) * t
                        # Preserve integer type
                        if isinstance(v1, int) and isinstance(v2, int):
                            result.append(int(round(interpolated)))
                        else:
                            result.append(interpolated)
                    else:
                        # Non-numeric values use step interpolation
                        result.append(v2 if t >= 0.5 else v1)
                return type(val1)(result)
        
        # Handle dictionaries (nested properties)
        if isinstance(val1, dict) and isinstance(val2, dict):
            result = {}
            all_keys = set(val1.keys()) | set(val2.keys())
            for key in all_keys:
                if key in val1 and key in val2:
                    result[key] = self._interpolate_value(val1[key], val2[key], t)
                elif key in val1:
                    result[key] = val1[key]
                else:
                    result[key] = val2[key]
            return result
        
        # Handle boolean and string types (step interpolation)
        if isinstance(val1, bool) and isinstance(val2, bool):
            return bool(val2 if t >= 0.5 else val1)
        elif isinstance(val1, (bool, str)) or isinstance(val2, (bool, str)):
            return val2 if t >= 0.5 else val1
        
        # Default: return second value if t >= 0.5, otherwise first
        return val2 if t >= 0.5 else val1
    
    def copy_keyframes(self, keyframes: List[Keyframe]) -> List[Keyframe]:
        """
        Create deep copies of keyframes.
        
        Args:
            keyframes: List of keyframes to copy
            
        Returns:
            List of copied keyframes
        """
        copied = []
        for kf in keyframes:
            # Deep copy properties
            copied_properties = self._deep_copy_dict(kf.properties)
            
            copied_kf = Keyframe(
                time=kf.time,
                properties=copied_properties,
                interpolation_type=kf.interpolation_type
            )
            copied.append(copied_kf)
        
        return copied
    
    def _deep_copy_dict(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """Create a deep copy of a dictionary."""
        result = {}
        for key, value in d.items():
            if isinstance(value, dict):
                result[key] = self._deep_copy_dict(value)
            elif isinstance(value, (list, tuple)):
                result[key] = type(value)(
                    self._deep_copy_dict(item) if isinstance(item, dict) else item
                    for item in value
                )
            else:
                result[key] = value
        return result
    
    def offset_keyframes(self, keyframes: List[Keyframe], time_offset: float) -> List[Keyframe]:
        """
        Create copies of keyframes with time offset applied.
        
        Args:
            keyframes: List of keyframes to offset
            time_offset: Time offset to apply
            
        Returns:
            List of offset keyframes
        """
        offset_keyframes = []
        for kf in keyframes:
            new_time = max(0.0, kf.time + time_offset)  # Ensure non-negative time
            
            offset_kf = Keyframe(
                time=new_time,
                properties=self._deep_copy_dict(kf.properties),
                interpolation_type=kf.interpolation_type
            )
            offset_keyframes.append(offset_kf)
        
        return offset_keyframes
    
    def scale_keyframes(self, keyframes: List[Keyframe], time_scale: float, 
                       pivot_time: float = 0.0) -> List[Keyframe]:
        """
        Scale keyframe timing around a pivot point.
        
        Args:
            keyframes: List of keyframes to scale
            time_scale: Scale factor for timing
            pivot_time: Pivot point for scaling
            
        Returns:
            List of scaled keyframes
        """
        if time_scale <= 0:
            raise ValueError("Time scale must be positive")
        
        scaled_keyframes = []
        for kf in keyframes:
            # Scale time relative to pivot
            new_time = pivot_time + (kf.time - pivot_time) * time_scale
            new_time = max(0.0, new_time)  # Ensure non-negative time
            
            scaled_kf = Keyframe(
                time=new_time,
                properties=self._deep_copy_dict(kf.properties),
                interpolation_type=kf.interpolation_type
            )
            scaled_keyframes.append(scaled_kf)
        
        return scaled_keyframes
    
    def find_keyframes_in_range(self, keyframes: List[Keyframe], 
                               start_time: float, end_time: float) -> List[Keyframe]:
        """
        Find all keyframes within a time range.
        
        Args:
            keyframes: List of keyframes to search
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            List of keyframes within the range
        """
        if start_time > end_time:
            start_time, end_time = end_time, start_time
        
        return [kf for kf in keyframes if start_time <= kf.time <= end_time]
    
    def get_keyframe_bounds(self, keyframes: List[Keyframe]) -> Tuple[float, float]:
        """
        Get the time bounds of a list of keyframes.
        
        Args:
            keyframes: List of keyframes
            
        Returns:
            Tuple of (min_time, max_time)
        """
        if not keyframes:
            return (0.0, 0.0)
        
        times = [kf.time for kf in keyframes]
        return (min(times), max(times))
    
    def sort_keyframes(self, keyframes: List[Keyframe]) -> List[Keyframe]:
        """
        Sort keyframes by time in ascending order.
        
        Args:
            keyframes: List of keyframes to sort
            
        Returns:
            Sorted list of keyframes
        """
        return sorted(keyframes, key=lambda kf: kf.time)
    
    def remove_duplicate_keyframes(self, keyframes: List[Keyframe], 
                                  tolerance: float = 0.001) -> List[Keyframe]:
        """
        Remove keyframes that are too close in time.
        
        Args:
            keyframes: List of keyframes to process
            tolerance: Time tolerance for considering keyframes duplicates
            
        Returns:
            List with duplicates removed
        """
        if not keyframes:
            return []
        
        # Sort keyframes first
        sorted_kfs = self.sort_keyframes(keyframes)
        
        # Remove duplicates
        unique_kfs = [sorted_kfs[0]]
        
        for kf in sorted_kfs[1:]:
            if kf.time - unique_kfs[-1].time > tolerance:
                unique_kfs.append(kf)
            else:
                # Keep the later keyframe (overwrite behavior)
                unique_kfs[-1] = kf
        
        return unique_kfs