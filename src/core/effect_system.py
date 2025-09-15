"""
Effect System - Coordinates all effect types and manages their application.
"""

from typing import Dict, List, Any, Optional
from .interfaces import IEffectSystem


class EffectSystem(IEffectSystem):
    """
    Coordinates all effect subsystems and manages their application to text elements.
    """
    
    def __init__(self):
        # Initialize with minimal functionality for now
        # Full initialization will happen when renderer is available
        self.animation_system = None
        self.visual_system = None
        self.particle_system = None
        self.transform_system = None
        self.color_system = None
        
        self._effect_registry = {}
    
    def apply_effects(self, text_element, effects: List[Dict[str, Any]], time: float) -> Dict[str, Any]:
        """Apply all effects to a text element at given time."""
        result = {
            'position': text_element.position,
            'rotation': text_element.rotation,
            'color': text_element.color,
            'scale': (1.0, 1.0, 1.0),
            'opacity': 1.0
        }
        
        for effect in effects:
            effect_type = effect.get('type', '')
            category = effect_type.split('_')[0] if '_' in effect_type else effect_type
            
            if category in self._effect_registry:
                system = self._effect_registry[category]
                system_result = system.apply_effect(effect, time)
                
                # Merge results
                for key, value in system_result.items():
                    if key in result:
                        result[key] = value
        
        return result
    
    def get_available_effects(self) -> Dict[str, List[str]]:
        """Get list of available effects by category."""
        return {
            'animation': ['fade', 'slide', 'typewriter', 'bounce'],
            'visual': ['glow', 'outline', 'shadow', 'gradient'],
            'particle': ['sparkle', 'fire', 'smoke'],
            'transform': ['rotation', 'extrusion', 'perspective'],
            'color': ['rainbow', 'pulse', 'strobe', 'temperature']
        }
    
    def get_effect_parameters(self, effect_type: str) -> Dict[str, Any]:
        """Get available parameters for an effect type."""
        category = effect_type.split('_')[0] if '_' in effect_type else effect_type
        
        if category in self._effect_registry:
            system = self._effect_registry[category]
            if hasattr(system, 'get_effect_parameters'):
                return system.get_effect_parameters(effect_type)
        
        return {}
    
    def apply_text_animation(self, text, effect) -> None:
        """Apply animation effect to text element."""
        # Placeholder implementation
        pass
    
    def render_particle_effect(self, effect, time: float) -> None:
        """Render particle effect at the specified time."""
        # Placeholder implementation
        pass
    
    def calculate_3d_transform(self, params) -> Any:
        """Calculate 3D transformation matrix."""
        # Placeholder implementation
        import numpy as np
        return np.identity(4)