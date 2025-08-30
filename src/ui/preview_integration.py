#!/usr/bin/env python3
"""
Preview Integration - Karaoke Subtitle Creator

Integration layer between the preview system and OpenGL renderer,
handling real-time updates and synchronization.
"""

from typing import Optional, Dict, Any, List
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtOpenGLWidgets import QOpenGLWidget

from ..graphics.opengl_renderer import OpenGLRenderer
from ..core.timeline_engine import TimelineEngine
from ..effects.animation_effects import AnimationEffectProcessor
from ..effects.visual_effects import VisualEffectProcessor
from ..effects.color_effects import ColorEffectProcessor
from ..effects.particle_system import ParticleSystem
from ..effects.transform_3d import Transform3D
from .preview_system import PreviewSystem, QualityPreset


class MockEffectProcessor:
    """Mock effect processor for testing without OpenGL."""
    
    def __init__(self):
        pass
    
    def update_parameter(self, parameter: str, value):
        print(f"Mock processor: {parameter} = {value}")
    
    def apply_effects(self, element, *args):
        return {}
    
    def set_quality_settings(self, settings):
        pass
    
    def cleanup(self):
        pass


class PreviewIntegration(QObject):
    """
    Integration layer that connects UI controls with OpenGL preview rendering.
    
    This class handles:
    - Real-time effect parameter updates
    - Timeline synchronization with preview
    - OpenGL renderer coordination
    - Performance monitoring and optimization
    """
    
    # Signals for UI feedback
    render_complete = pyqtSignal()
    performance_update = pyqtSignal(dict)  # Performance metrics
    error_occurred = pyqtSignal(str)  # Error message
    
    def __init__(self, opengl_widget: QOpenGLWidget):
        """
        Initialize preview integration.
        
        Args:
            opengl_widget: OpenGL widget for rendering
        """
        super().__init__()
        
        # Core components
        self.opengl_widget = opengl_widget
        self.renderer: Optional[OpenGLRenderer] = None
        self.timeline_engine: Optional[TimelineEngine] = None
        self.preview_system: Optional[PreviewSystem] = None
        
        # Effect processors (will be initialized when renderer is available)
        self.animation_processor = None
        self.visual_processor = None
        self.color_processor = None
        self.particle_system = None
        self.transform_3d = None
        
        # Current state
        self.current_effects: Dict[str, Any] = {}
        self.current_text_properties: Dict[str, Any] = {}
        self.is_initialized = False
        
        # Performance tracking
        self.performance_timer = QTimer()
        self.performance_timer.timeout.connect(self._update_performance_metrics)
        self.performance_timer.start(1000)  # Update every second
    
    def initialize(self, renderer: OpenGLRenderer, timeline_engine: TimelineEngine, 
                  preview_system: PreviewSystem) -> bool:
        """
        Initialize the integration with core components.
        
        Args:
            renderer: OpenGL renderer instance
            timeline_engine: Timeline engine instance
            preview_system: Preview system instance
            
        Returns:
            True if initialization successful
        """
        try:
            self.renderer = renderer
            self.timeline_engine = timeline_engine
            self.preview_system = preview_system
            
            # Connect preview system signals
            self.preview_system.frame_rendered.connect(self._on_frame_rendered)
            self.preview_system.quality_changed.connect(self._on_quality_changed)
            self.preview_system.performance_warning.connect(self._on_performance_warning)
            
            # Initialize effect processors with renderer
            self._initialize_effect_processors()
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to initialize preview integration: {str(e)}")
            return False
    
    def _initialize_effect_processors(self):
        """Initialize effect processors with renderer context."""
        if not self.renderer:
            return
        
        # Initialize each effect processor with required dependencies
        try:
            # Get shader manager from renderer
            shader_manager = getattr(self.renderer, 'shader_manager', None)
            
            # Initialize effect processors
            self.animation_processor = AnimationEffectProcessor()
            
            if shader_manager:
                self.visual_processor = VisualEffectProcessor(shader_manager)
                self.color_processor = ColorEffectProcessor(shader_manager)
                self.particle_system = ParticleSystem(shader_manager)
                self.transform_3d = Transform3D(shader_manager)
            else:
                # Create mock processors for testing
                self.visual_processor = MockEffectProcessor()
                self.color_processor = MockEffectProcessor()
                self.particle_system = MockEffectProcessor()
                self.transform_3d = MockEffectProcessor()
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to initialize effect processors: {str(e)}")
    
    def update_effect_parameter(self, category: str, parameter: str, value: Any) -> None:
        """
        Update an effect parameter and trigger preview refresh.
        
        Args:
            category: Effect category (animation, visual, transform, color, particle)
            parameter: Parameter name
            value: New parameter value
        """
        if not self.is_initialized:
            return
        
        try:
            # Store the parameter update
            if category not in self.current_effects:
                self.current_effects[category] = {}
            
            self.current_effects[category][parameter] = value
            
            # Apply the effect update based on category
            if category == "animation":
                self._update_animation_effect(parameter, value)
            elif category == "visual":
                self._update_visual_effect(parameter, value)
            elif category == "transform":
                self._update_transform_effect(parameter, value)
            elif category == "color":
                self._update_color_effect(parameter, value)
            elif category == "particle":
                self._update_particle_effect(parameter, value)
            
            # Trigger preview update
            self._refresh_preview()
            
        except Exception as e:
            self.error_occurred.emit(f"Error updating effect parameter: {str(e)}")
    
    def _update_animation_effect(self, parameter: str, value: Any) -> None:
        """Update animation effect parameter."""
        if self.animation_processor:
            self.animation_processor.update_parameter(parameter, value)
    
    def _update_visual_effect(self, parameter: str, value: Any) -> None:
        """Update visual effect parameter."""
        if self.visual_processor:
            self.visual_processor.update_parameter(parameter, value)
    
    def _update_transform_effect(self, parameter: str, value: Any) -> None:
        """Update 3D transform effect parameter."""
        if self.transform_3d:
            self.transform_3d.update_parameter(parameter, value)
    
    def _update_color_effect(self, parameter: str, value: Any) -> None:
        """Update color effect parameter."""
        if self.color_processor:
            self.color_processor.update_parameter(parameter, value)
    
    def _update_particle_effect(self, parameter: str, value: Any) -> None:
        """Update particle effect parameter."""
        if self.particle_system:
            self.particle_system.update_parameter(parameter, value)
    
    def update_text_properties(self, properties: Dict[str, Any]) -> None:
        """
        Update text properties and refresh preview.
        
        Args:
            properties: Dictionary of text properties (font, color, position, etc.)
        """
        if not self.is_initialized:
            return
        
        try:
            # Store text properties
            self.current_text_properties.update(properties)
            
            # Update text renderer with new properties
            if self.renderer and hasattr(self.renderer, 'text_renderer'):
                self.renderer.text_renderer.update_properties(properties)
            
            # Trigger preview update
            self._refresh_preview()
            
        except Exception as e:
            self.error_occurred.emit(f"Error updating text properties: {str(e)}")
    
    def update_timeline_position(self, time: float) -> None:
        """
        Update timeline position and synchronize preview.
        
        Args:
            time: New timeline position in seconds
        """
        if not self.is_initialized or not self.timeline_engine:
            return
        
        try:
            # Update timeline engine
            self.timeline_engine.current_time = time
            
            # Get active elements at current time
            active_elements = self.timeline_engine.get_active_elements_at_time(time)
            
            # Update preview system
            if self.preview_system:
                self.preview_system.seek(time)
            
            # Render frame at new position
            self._render_frame_at_time(time, active_elements)
            
        except Exception as e:
            self.error_occurred.emit(f"Error updating timeline position: {str(e)}")
    
    def _render_frame_at_time(self, time: float, active_elements: List) -> None:
        """
        Render a frame at the specified time with active elements.
        
        Args:
            time: Timeline time
            active_elements: List of active subtitle elements
        """
        if not self.renderer:
            return
        
        try:
            # Make OpenGL context current
            self.opengl_widget.makeCurrent()
            
            # Clear the frame
            self.renderer.clear_frame()
            
            # Render video background if available
            if self.timeline_engine.video_asset:
                video_frame = self._get_video_frame_at_time(time)
                if video_frame is not None:
                    self.renderer.render_video_background(video_frame)
            
            # Render subtitle elements with effects
            for track_id, elements in active_elements:
                for element in elements:
                    self._render_text_element_with_effects(element, time)
            
            # Render particle effects
            self._render_particle_effects(time)
            
            # Swap buffers to display
            self.opengl_widget.swapBuffers()
            
        except Exception as e:
            self.error_occurred.emit(f"Error rendering frame: {str(e)}")
    
    def _render_text_element_with_effects(self, element, time: float) -> None:
        """
        Render a text element with all applied effects.
        
        Args:
            element: Text element to render
            time: Current timeline time
        """
        if not self.renderer:
            return
        
        # Apply animation effects
        animated_properties = {}
        if 'animation' in self.current_effects and self.animation_processor:
            animated_properties.update(
                self.animation_processor.apply_effects(element, time, self.current_effects['animation'])
            )
        
        # Apply visual effects
        if 'visual' in self.current_effects and self.visual_processor:
            visual_properties = self.visual_processor.apply_effects(
                element, self.current_effects['visual']
            )
            animated_properties.update(visual_properties)
        
        # Apply 3D transform
        if 'transform' in self.current_effects and self.transform_3d:
            if hasattr(self.transform_3d, 'calculate_transform_matrix'):
                transform_matrix = self.transform_3d.calculate_transform_matrix(
                    self.current_effects['transform']
                )
                animated_properties['transform_matrix'] = transform_matrix
        
        # Apply color effects
        if 'color' in self.current_effects and self.color_processor:
            color_properties = self.color_processor.apply_effects(
                element, time, self.current_effects['color']
            )
            animated_properties.update(color_properties)
        
        # Combine with text properties
        final_properties = {**self.current_text_properties, **animated_properties}
        
        # Render the text element
        self.renderer.render_text_element(element, final_properties)
    
    def _render_particle_effects(self, time: float) -> None:
        """
        Render particle effects at the current time.
        
        Args:
            time: Current timeline time
        """
        if 'particle' in self.current_effects and self.particle_system:
            if hasattr(self.particle_system, 'update'):
                self.particle_system.update(time)
            if hasattr(self.particle_system, 'render'):
                self.particle_system.render(self.renderer)
    
    def _get_video_frame_at_time(self, time: float):
        """
        Get video frame at specified time.
        
        Args:
            time: Timeline time in seconds
            
        Returns:
            Video frame data or None
        """
        # This would interface with video decoder
        # For now, return None (no video background)
        return None
    
    def _refresh_preview(self) -> None:
        """Trigger a preview refresh."""
        if self.preview_system and self.timeline_engine:
            current_time = self.timeline_engine.current_time
            self.update_timeline_position(current_time)
    
    def set_preview_quality(self, quality: QualityPreset) -> None:
        """
        Set preview quality and update effect processors.
        
        Args:
            quality: Preview quality preset
        """
        if self.preview_system:
            self.preview_system.set_quality_preset(quality)
            
            # Update effect processors based on quality
            self._update_effect_quality(quality)
    
    def _update_effect_quality(self, quality: QualityPreset) -> None:
        """
        Update effect processor quality settings.
        
        Args:
            quality: Quality preset
        """
        quality_settings = {
            QualityPreset.DRAFT: {'antialiasing': False, 'particle_count': 0.3},
            QualityPreset.NORMAL: {'antialiasing': True, 'particle_count': 0.7},
            QualityPreset.HIGH: {'antialiasing': True, 'particle_count': 1.0}
        }
        
        settings = quality_settings.get(quality, quality_settings[QualityPreset.NORMAL])
        
        # Apply settings to effect processors
        if self.visual_processor:
            self.visual_processor.set_quality_settings(settings)
        if self.particle_system:
            self.particle_system.set_quality_settings(settings)
    
    def _on_frame_rendered(self) -> None:
        """Handle frame rendered signal from preview system."""
        self.render_complete.emit()
    
    def _on_quality_changed(self, quality: QualityPreset) -> None:
        """Handle quality change from preview system."""
        self._update_effect_quality(quality)
    
    def _on_performance_warning(self, warning: str) -> None:
        """Handle performance warning from preview system."""
        # Could trigger automatic quality reduction or other optimizations
        pass
    
    def _update_performance_metrics(self) -> None:
        """Update and emit performance metrics."""
        if not self.preview_system:
            return
        
        metrics = self.preview_system.get_performance_metrics()
        
        performance_data = {
            'fps': metrics.current_fps,
            'frame_time_ms': metrics.frame_time_ms,
            'dropped_frames': metrics.dropped_frames,
            'quality': metrics.quality_preset.value,
            'gpu_memory_usage': metrics.gpu_memory_usage,
            'render_time_ms': metrics.render_time_ms
        }
        
        self.performance_update.emit(performance_data)
    
    def shutdown(self) -> None:
        """Shutdown the integration and cleanup resources."""
        if self.performance_timer.isActive():
            self.performance_timer.stop()
        
        # Cleanup effect processors
        if self.animation_processor and hasattr(self.animation_processor, 'cleanup'):
            self.animation_processor.cleanup()
        if self.visual_processor and hasattr(self.visual_processor, 'cleanup'):
            self.visual_processor.cleanup()
        if self.color_processor and hasattr(self.color_processor, 'cleanup'):
            self.color_processor.cleanup()
        if self.particle_system and hasattr(self.particle_system, 'cleanup'):
            self.particle_system.cleanup()
        if self.transform_3d and hasattr(self.transform_3d, 'cleanup'):
            self.transform_3d.cleanup()
        
        self.is_initialized = False