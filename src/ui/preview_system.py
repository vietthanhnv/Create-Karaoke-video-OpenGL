"""
Real-time preview system for karaoke subtitle creator.

This module provides 60fps preview rendering with automatic quality adjustment,
video synchronization, and performance monitoring.
"""

import logging
import time
from typing import Optional, Dict, Any, Callable, List, Tuple
from enum import Enum
from dataclasses import dataclass

from PyQt6.QtCore import QTimer, QObject, pyqtSignal, QThread, QPointF, QRectF, Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel, QComboBox, QCheckBox, QGroupBox
from PyQt6.QtGui import QPainter, QPen, QColor
import numpy as np

# Note: These imports will be connected when the modules are integrated
# from core.interfaces import ITimelineEngine, IRenderEngine
# from core.models import VideoAsset, SubtitleTrack, TextElement
# from graphics.opengl_renderer import OpenGLRenderer


logger = logging.getLogger(__name__)


class QualityPreset(Enum):
    """Quality presets for preview rendering."""
    DRAFT = "draft"
    NORMAL = "normal"
    HIGH = "high"


@dataclass
class PerformanceMetrics:
    """Performance metrics for preview rendering."""
    current_fps: float = 0.0
    target_fps: float = 60.0
    frame_time_ms: float = 0.0
    dropped_frames: int = 0
    quality_preset: QualityPreset = QualityPreset.NORMAL
    gpu_memory_usage: float = 0.0
    render_time_ms: float = 0.0


@dataclass
class ViewportTransform:
    """Viewport transformation parameters for zoom and pan."""
    zoom: float = 1.0
    pan_x: float = 0.0
    pan_y: float = 0.0
    min_zoom: float = 0.1
    max_zoom: float = 10.0


class SafeAreaType(Enum):
    """Types of safe area guides."""
    NONE = "none"
    ACTION_SAFE = "action_safe"  # 90% of screen
    TITLE_SAFE = "title_safe"    # 80% of screen
    BOTH = "both"


class PreviewSystem(QObject):
    """
    Real-time preview system with 60fps targeting and automatic quality adjustment.
    
    Manages the preview rendering loop, video synchronization, and performance
    monitoring for the karaoke subtitle creator.
    """
    
    # Signals for UI communication
    fps_updated = pyqtSignal(float)
    quality_changed = pyqtSignal(QualityPreset)
    performance_warning = pyqtSignal(str)
    frame_rendered = pyqtSignal()
    viewport_changed = pyqtSignal(ViewportTransform)
    safe_area_changed = pyqtSignal(SafeAreaType)
    
    def __init__(self, renderer=None, timeline_engine=None):
        super().__init__()
        
        self._renderer = renderer
        self._timeline_engine = timeline_engine
        
        # Rendering state
        self._is_active = False
        self._is_playing = False
        self._current_quality = QualityPreset.NORMAL
        
        # Performance monitoring
        self._metrics = PerformanceMetrics()
        self._frame_times: List[float] = []
        self._last_frame_time = 0.0
        self._performance_check_interval = 1.0  # Check performance every second
        self._last_performance_check = 0.0
        
        # Rendering timer for 60fps targeting
        self._render_timer = QTimer()
        self._render_timer.timeout.connect(self._render_frame)
        
        # Target frame interval for FPS calculation
        self._target_frame_interval = 1000 / self._metrics.target_fps  # milliseconds
        
        # Viewport transformation
        self._viewport_transform = ViewportTransform()
        
        # Safe area settings
        self._safe_area_type = SafeAreaType.NONE
        
        # Video source
        self._video_source = None
    
    def start_preview(self) -> None:
        """Start the preview rendering loop."""
        if not self._is_active:
            self._is_active = True
            target_interval = int(1000 / self._metrics.target_fps)  # Convert to milliseconds
            self._render_timer.start(target_interval)
            logger.info("Preview system started")
    
    def stop_preview(self) -> None:
        """Stop the preview rendering loop."""
        if self._is_active:
            self._is_active = False
            self._render_timer.stop()
            logger.info("Preview system stopped")
    
    def play(self) -> None:
        """Start playback."""
        self._is_playing = True
        if not self._is_active:
            self.start_preview()
    
    def pause(self) -> None:
        """Pause playback."""
        self._is_playing = False
    
    def seek(self, time: float) -> None:
        """
        Seek to specific time position.
        
        Args:
            time: Time position in seconds
        """
        if self._timeline_engine:
            self._timeline_engine.current_time = time
        self._render_frame()
    
    def zoom_in(self) -> None:
        """Zoom in on the preview."""
        self._viewport_transform.zoom = min(
            self._viewport_transform.zoom * 1.2,
            self._viewport_transform.max_zoom
        )
        self.viewport_changed.emit(self._viewport_transform)
        self._render_frame()
    
    def zoom_out(self) -> None:
        """Zoom out on the preview."""
        self._viewport_transform.zoom = max(
            self._viewport_transform.zoom / 1.2,
            self._viewport_transform.min_zoom
        )
        self.viewport_changed.emit(self._viewport_transform)
        self._render_frame()
    
    def zoom_to_fit(self) -> None:
        """Reset zoom to fit the entire preview."""
        self._viewport_transform.zoom = 1.0
        self._viewport_transform.pan_x = 0.0
        self._viewport_transform.pan_y = 0.0
        self.viewport_changed.emit(self._viewport_transform)
        self._render_frame()
    
    def set_quality_preset(self, quality: QualityPreset) -> None:
        """
        Set preview quality preset.
        
        Args:
            quality: Quality preset to use
        """
        if self._current_quality != quality:
            self._current_quality = quality
            self._metrics.quality_preset = quality
            self.quality_changed.emit(quality)
            
            # Adjust target FPS based on quality
            if quality == QualityPreset.DRAFT:
                self._metrics.target_fps = 30.0
            elif quality == QualityPreset.NORMAL:
                self._metrics.target_fps = 60.0
            elif quality == QualityPreset.HIGH:
                self._metrics.target_fps = 60.0
            
            # Update timer interval
            if self._is_active:
                target_interval = int(1000 / self._metrics.target_fps)
                self._render_timer.setInterval(target_interval)
    
    def set_video_source(self, video_path: str) -> None:
        """
        Set video source for background.
        
        Args:
            video_path: Path to video file
        """
        self._video_source = video_path
        logger.info(f"Video source set: {video_path}")
        self._render_frame()
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """
        Get current performance metrics.
        
        Returns:
            Current performance metrics
        """
        return self._metrics
    
    def _render_frame(self) -> None:
        """Render a single frame."""
        if not self._is_active:
            return
        
        start_time = time.time()
        
        try:
            # Update performance metrics
            self._update_frame_timing(start_time)
            
            # Render frame using renderer if available
            if self._renderer:
                self._renderer.render_frame()
            
            # Emit frame rendered signal
            self.frame_rendered.emit()
            
        except Exception as e:
            logger.error(f"Error rendering frame: {e}")
            self.performance_warning.emit(f"Render error: {str(e)}")
        
        # Calculate render time
        render_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        self._metrics.render_time_ms = render_time
    
    def _update_frame_timing(self, current_time: float) -> None:
        """Update frame timing metrics."""
        if self._last_frame_time > 0:
            frame_time = current_time - self._last_frame_time
            self._frame_times.append(frame_time)
            
            # Keep only recent frame times (last 60 frames)
            if len(self._frame_times) > 60:
                self._frame_times.pop(0)
            
            # Calculate current FPS
            if self._frame_times:
                avg_frame_time = sum(self._frame_times) / len(self._frame_times)
                self._metrics.current_fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0.0
                self._metrics.frame_time_ms = avg_frame_time * 1000
            
            # Check performance periodically
            if current_time - self._last_performance_check > self._performance_check_interval:
                self._check_performance()
                self._last_performance_check = current_time
        
        self._last_frame_time = current_time
    
    def _check_performance(self) -> None:
        """Check performance and emit warnings if needed."""
        target_fps = self._metrics.target_fps
        current_fps = self._metrics.current_fps
        
        # Emit FPS update
        self.fps_updated.emit(current_fps)
        
        # Check for performance issues
        if current_fps < target_fps * 0.8:  # If FPS drops below 80% of target
            warning = f"Low FPS: {current_fps:.1f}/{target_fps:.1f}"
            self.performance_warning.emit(warning)
            
            # Auto-adjust quality if performance is poor
            if self._current_quality == QualityPreset.HIGH and current_fps < target_fps * 0.6:
                self.set_quality_preset(QualityPreset.NORMAL)
            elif self._current_quality == QualityPreset.NORMAL and current_fps < target_fps * 0.4:
                self.set_quality_preset(QualityPreset.DRAFT)
        self._render_timer.timeout.connect(self._render_frame)
        self._target_frame_interval = 1000 / 60  # 16.67ms for 60fps
        
        # Video synchronization
        self._video_start_time = 0.0
        self._playback_start_time = 0.0
        self._video_frame_cache: Dict[int, np.ndarray] = {}
        self._max_cache_size = 30  # Cache 30 frames (0.5 seconds at 60fps)
        
        # Quality adjustment thresholds
        self._fps_threshold_low = 45.0  # Drop quality below 45fps
        self._fps_threshold_high = 55.0  # Raise quality above 55fps
        self._quality_adjustment_cooldown = 2.0  # Wait 2 seconds between adjustments
        self._last_quality_adjustment = 0.0
        
        # Viewport controls
        self._viewport_transform = ViewportTransform()
        self._safe_area_type = SafeAreaType.NONE
        
        # Connect to timeline engine signals
        if hasattr(timeline_engine, 'playback_state_changed'):
            timeline_engine.playback_state_changed.connect(self._on_playback_state_changed)
        
        # Connect to renderer signals (if renderer is available)
        if self._renderer:
            self._renderer.fps_updated.connect(self._on_renderer_fps_updated)
        
    def start_preview(self) -> bool:
        """
        Start the preview system.
        
        Returns:
            True if preview started successfully, False otherwise
        """
        if self._is_active:
            return True
        
        try:
            # Initialize performance tracking
            self._reset_performance_metrics()
            
            # Start the rendering timer
            self._render_timer.start(int(self._target_frame_interval))
            
            self._is_active = True
            logger.info("Preview system started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start preview system: {e}")
            return False
    
    def stop_preview(self) -> None:
        """Stop the preview system."""
        if not self._is_active:
            return
        
        self._render_timer.stop()
        self._is_active = False
        self._is_playing = False
        
        # Clear video frame cache
        self._video_frame_cache.clear()
        
        logger.info("Preview system stopped")
    
    def set_quality_preset(self, quality: QualityPreset) -> None:
        """
        Set the quality preset for preview rendering.
        
        Args:
            quality: Quality preset to use
        """
        if quality != self._current_quality:
            self._current_quality = quality
            self._apply_quality_settings(quality)
            self.quality_changed.emit(quality)
            logger.info(f"Quality preset changed to {quality.value}")
    
    def get_quality_preset(self) -> QualityPreset:
        """Get the current quality preset."""
        return self._current_quality
    
    def play(self) -> None:
        """Start video playback in preview."""
        if not self._is_active:
            return
        
        self._is_playing = True
        self._playback_start_time = time.time()
        self._video_start_time = self._timeline_engine.current_time
        
        # Start timeline playback
        self._timeline_engine.play()
        
        logger.debug("Preview playback started")
    
    def pause(self) -> None:
        """Pause video playback in preview."""
        self._is_playing = False
        self._timeline_engine.pause()
        logger.debug("Preview playback paused")
    
    def stop(self) -> None:
        """Stop video playback and reset to beginning."""
        self._is_playing = False
        self._timeline_engine.stop()
        self._video_frame_cache.clear()
        logger.debug("Preview playback stopped")
    
    def seek(self, time: float) -> None:
        """
        Seek to a specific time position.
        
        Args:
            time: Target time in seconds
        """
        self._timeline_engine.seek(time)
        
        # Clear cache when seeking to avoid stale frames
        self._video_frame_cache.clear()
        
        # Update playback timing if currently playing
        if self._is_playing:
            self._playback_start_time = time.time()
            self._video_start_time = time
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics."""
        return self._metrics
    
    # Viewport Control Methods
    
    def set_zoom(self, zoom: float) -> None:
        """
        Set the zoom level for the preview.
        
        Args:
            zoom: Zoom factor (1.0 = 100%, 2.0 = 200%, etc.)
        """
        zoom = max(self._viewport_transform.min_zoom, 
                  min(self._viewport_transform.max_zoom, zoom))
        
        if zoom != self._viewport_transform.zoom:
            self._viewport_transform.zoom = zoom
            self._update_viewport_transform()
            self.viewport_changed.emit(self._viewport_transform)
            logger.debug(f"Zoom set to {zoom:.2f}")
    
    def get_zoom(self) -> float:
        """Get the current zoom level."""
        return self._viewport_transform.zoom
    
    def zoom_in(self, factor: float = 1.2) -> None:
        """
        Zoom in by the specified factor.
        
        Args:
            factor: Zoom multiplication factor
        """
        self.set_zoom(self._viewport_transform.zoom * factor)
    
    def zoom_out(self, factor: float = 1.2) -> None:
        """
        Zoom out by the specified factor.
        
        Args:
            factor: Zoom division factor
        """
        self.set_zoom(self._viewport_transform.zoom / factor)
    
    def zoom_to_fit(self) -> None:
        """Zoom to fit the entire video in the preview area."""
        # Calculate zoom to fit based on renderer size and video resolution
        if hasattr(self._renderer, 'width') and hasattr(self._renderer, 'height'):
            renderer_aspect = self._renderer.width() / self._renderer.height()
            
            video_asset = self._timeline_engine.video_asset
            if video_asset:
                video_width, video_height = video_asset.resolution
                video_aspect = video_width / video_height
                
                if video_aspect > renderer_aspect:
                    # Video is wider, fit to width
                    zoom = self._renderer.width() / video_width
                else:
                    # Video is taller, fit to height
                    zoom = self._renderer.height() / video_height
                
                self.set_zoom(zoom)
                self.set_pan(0.0, 0.0)  # Center the view
    
    def zoom_to_actual_size(self) -> None:
        """Zoom to 100% (actual pixel size)."""
        self.set_zoom(1.0)
        self.set_pan(0.0, 0.0)
    
    def set_pan(self, pan_x: float, pan_y: float) -> None:
        """
        Set the pan offset for the preview.
        
        Args:
            pan_x: Horizontal pan offset in pixels
            pan_y: Vertical pan offset in pixels
        """
        if (pan_x != self._viewport_transform.pan_x or 
            pan_y != self._viewport_transform.pan_y):
            
            self._viewport_transform.pan_x = pan_x
            self._viewport_transform.pan_y = pan_y
            self._update_viewport_transform()
            self.viewport_changed.emit(self._viewport_transform)
            logger.debug(f"Pan set to ({pan_x:.1f}, {pan_y:.1f})")
    
    def get_pan(self) -> Tuple[float, float]:
        """Get the current pan offset."""
        return (self._viewport_transform.pan_x, self._viewport_transform.pan_y)
    
    def pan_by(self, delta_x: float, delta_y: float) -> None:
        """
        Pan by the specified delta amounts.
        
        Args:
            delta_x: Horizontal pan delta in pixels
            delta_y: Vertical pan delta in pixels
        """
        new_x = self._viewport_transform.pan_x + delta_x
        new_y = self._viewport_transform.pan_y + delta_y
        self.set_pan(new_x, new_y)
    
    def reset_viewport(self) -> None:
        """Reset viewport to default zoom and pan."""
        self.set_zoom(1.0)
        self.set_pan(0.0, 0.0)
    
    def get_viewport_transform(self) -> ViewportTransform:
        """Get the current viewport transformation."""
        return self._viewport_transform
    
    # Safe Area Guide Methods
    
    def set_safe_area_guides(self, safe_area_type: SafeAreaType) -> None:
        """
        Set the type of safe area guides to display.
        
        Args:
            safe_area_type: Type of safe area guides to show
        """
        if safe_area_type != self._safe_area_type:
            self._safe_area_type = safe_area_type
            self.safe_area_changed.emit(safe_area_type)
            logger.debug(f"Safe area guides set to {safe_area_type.value}")
    
    def get_safe_area_guides(self) -> SafeAreaType:
        """Get the current safe area guide type."""
        return self._safe_area_type
    
    def get_safe_area_bounds(self, area_type: SafeAreaType, 
                           viewport_width: int, viewport_height: int) -> Optional[QRectF]:
        """
        Calculate safe area bounds for the given viewport size.
        
        Args:
            area_type: Type of safe area to calculate
            viewport_width: Width of the viewport in pixels
            viewport_height: Height of the viewport in pixels
            
        Returns:
            QRectF representing the safe area bounds, or None if no safe area
        """
        if area_type == SafeAreaType.NONE:
            return None
        
        # Calculate safe area percentages
        if area_type == SafeAreaType.ACTION_SAFE:
            safe_percent = 0.9  # 90% of screen
        elif area_type == SafeAreaType.TITLE_SAFE:
            safe_percent = 0.8  # 80% of screen
        else:
            return None
        
        # Calculate safe area dimensions
        safe_width = viewport_width * safe_percent
        safe_height = viewport_height * safe_percent
        
        # Center the safe area
        x = (viewport_width - safe_width) / 2
        y = (viewport_height - safe_height) / 2
        
        return QRectF(x, y, safe_width, safe_height)
    
    def _render_frame(self) -> None:
        """Render a single frame of the preview."""
        if not self._is_active:
            return
        
        frame_start_time = time.time()
        
        try:
            # Update timeline if playing
            if self._is_playing:
                self._update_timeline_time()
            
            # Get current timeline time
            current_time = self._timeline_engine.current_time
            
            # Get active subtitle elements at current time
            active_elements = self._timeline_engine.get_active_elements_at_time(current_time)
            
            # Render the frame
            self._render_preview_frame(current_time, active_elements)
            
            # Update performance metrics
            frame_end_time = time.time()
            frame_time = (frame_end_time - frame_start_time) * 1000  # Convert to ms
            self._update_performance_metrics(frame_time)
            
            # Check for automatic quality adjustment
            self._check_performance_adjustment()
            
            # Emit frame rendered signal
            self.frame_rendered.emit()
            
        except Exception as e:
            logger.error(f"Error rendering preview frame: {e}")
            self.performance_warning.emit(f"Render error: {str(e)}")
    
    def _update_timeline_time(self) -> None:
        """Update timeline time based on real-time playback."""
        current_real_time = time.time()
        elapsed_time = current_real_time - self._playback_start_time
        
        # Apply playback speed
        playback_speed = self._timeline_engine.get_playback_speed()
        video_time = self._video_start_time + (elapsed_time * playback_speed)
        
        # Check if we've reached the end
        if video_time >= self._timeline_engine.duration:
            self.pause()
            video_time = self._timeline_engine.duration
        
        # Update timeline
        self._timeline_engine.current_time = video_time
    
    def _render_preview_frame(self, time: float, active_elements: List[Tuple[str, List[Any]]]) -> None:
        """
        Render a preview frame with video and subtitle overlay.
        
        Args:
            time: Current timeline time
            active_elements: List of active subtitle elements
        """
        render_start = time.time()
        
        # Get video frame if available
        video_frame = self._get_video_frame(time)
        
        # Prepare subtitle data for rendering
        subtitle_data = self._prepare_subtitle_data(active_elements)
        
        # Render through OpenGL renderer
        self._renderer.makeCurrent()
        
        # Clear the frame
        self._renderer.paintGL()
        
        # Render video background if available
        if video_frame is not None:
            self._render_video_background(video_frame)
        
        # Render subtitle overlays
        if subtitle_data:
            self._render_subtitle_overlays(subtitle_data)
        
        # Render safe area guides if enabled
        if self._safe_area_type != SafeAreaType.NONE:
            self._render_safe_area_guides()
        
        # Swap buffers to display the frame
        self._renderer.swapBuffers()
        
        render_end = time.time()
        self._metrics.render_time_ms = (render_end - render_start) * 1000
    
    def _get_video_frame(self, time: float) -> Optional[np.ndarray]:
        """
        Get video frame for the specified time.
        
        Args:
            time: Timeline time in seconds
            
        Returns:
            Video frame as numpy array or None if no video
        """
        video_asset = self._timeline_engine.video_asset
        if not video_asset:
            return None
        
        # Calculate frame number
        frame_number = self._timeline_engine.get_frame_from_time(time)
        
        # Check cache first
        if frame_number in self._video_frame_cache:
            return self._video_frame_cache[frame_number]
        
        # For now, return a placeholder frame
        # In a real implementation, this would decode the actual video frame
        width, height = video_asset.resolution
        placeholder_frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Cache the frame (with size limit)
        if len(self._video_frame_cache) >= self._max_cache_size:
            # Remove oldest frame
            oldest_frame = min(self._video_frame_cache.keys())
            del self._video_frame_cache[oldest_frame]
        
        self._video_frame_cache[frame_number] = placeholder_frame
        return placeholder_frame
    
    def _prepare_subtitle_data(self, active_elements: List[Tuple[str, List[Any]]]) -> List[Dict[str, Any]]:
        """
        Prepare subtitle data for rendering.
        
        Args:
            active_elements: List of active subtitle elements from timeline
            
        Returns:
            List of subtitle render data dictionaries
        """
        subtitle_data = []
        
        for track_id, elements in active_elements:
            for element in elements:
                if isinstance(element, TextElement):
                    render_data = {
                        'text': element.content,
                        'position': element.position,
                        'font_family': element.font_family,
                        'font_size': element.font_size,
                        'color': element.color,
                        'rotation': element.rotation,
                        'effects': element.effects
                    }
                    subtitle_data.append(render_data)
        
        return subtitle_data
    
    def _render_video_background(self, video_frame: np.ndarray) -> None:
        """
        Render video frame as background.
        
        Args:
            video_frame: Video frame data
        """
        # This would be implemented with OpenGL texture rendering
        # For now, just a placeholder
        pass
    
    def _render_subtitle_overlays(self, subtitle_data: List[Dict[str, Any]]) -> None:
        """
        Render subtitle overlays on top of video.
        
        Args:
            subtitle_data: List of subtitle render data
        """
        # Apply viewport transformation to subtitle positions
        for subtitle in subtitle_data:
            # Transform position based on zoom and pan
            original_pos = subtitle['position']
            transformed_pos = self._transform_position(original_pos)
            subtitle['position'] = transformed_pos
            
            # Scale font size based on zoom
            subtitle['font_size'] *= self._viewport_transform.zoom
        
        # This would use the text renderer and effect system
        # For now, just a placeholder
        pass
    
    def _render_safe_area_guides(self) -> None:
        """Render safe area guide overlays."""
        if not hasattr(self._renderer, 'width') or not hasattr(self._renderer, 'height'):
            return
        
        viewport_width = self._renderer.width()
        viewport_height = self._renderer.height()
        
        # Get safe area bounds
        if self._safe_area_type == SafeAreaType.BOTH:
            # Render both action safe and title safe
            action_bounds = self.get_safe_area_bounds(
                SafeAreaType.ACTION_SAFE, viewport_width, viewport_height)
            title_bounds = self.get_safe_area_bounds(
                SafeAreaType.TITLE_SAFE, viewport_width, viewport_height)
            
            if action_bounds:
                self._draw_safe_area_rectangle(action_bounds, QColor(255, 255, 0, 128))  # Yellow
            if title_bounds:
                self._draw_safe_area_rectangle(title_bounds, QColor(255, 0, 0, 128))    # Red
        else:
            bounds = self.get_safe_area_bounds(
                self._safe_area_type, viewport_width, viewport_height)
            if bounds:
                color = QColor(255, 255, 0, 128) if self._safe_area_type == SafeAreaType.ACTION_SAFE else QColor(255, 0, 0, 128)
                self._draw_safe_area_rectangle(bounds, color)
    
    def _draw_safe_area_rectangle(self, bounds: QRectF, color: QColor) -> None:
        """
        Draw a safe area rectangle overlay.
        
        Args:
            bounds: Rectangle bounds to draw
            color: Color for the rectangle outline
        """
        # This would be implemented with OpenGL line rendering
        # For now, just a placeholder that would draw the rectangle outline
        pass
    
    def _transform_position(self, position: Tuple[float, float]) -> Tuple[float, float]:
        """
        Transform a position based on current viewport settings.
        
        Args:
            position: Original position (x, y)
            
        Returns:
            Transformed position accounting for zoom and pan
        """
        x, y = position
        
        # Apply zoom and pan transformation
        transformed_x = (x * self._viewport_transform.zoom) + self._viewport_transform.pan_x
        transformed_y = (y * self._viewport_transform.zoom) + self._viewport_transform.pan_y
        
        return (transformed_x, transformed_y)
    
    def _update_viewport_transform(self) -> None:
        """Update the renderer with current viewport transformation."""
        # This would update OpenGL transformation matrices
        # For now, just a placeholder
        pass
    
    def _update_performance_metrics(self, frame_time_ms: float) -> None:
        """
        Update performance metrics with latest frame timing.
        
        Args:
            frame_time_ms: Frame render time in milliseconds
        """
        current_time = time.time()
        
        # Update frame time
        self._metrics.frame_time_ms = frame_time_ms
        
        # Track frame times for FPS calculation
        self._frame_times.append(current_time)
        
        # Keep only last second of frame times
        cutoff_time = current_time - 1.0
        self._frame_times = [t for t in self._frame_times if t > cutoff_time]
        
        # Calculate current FPS
        if len(self._frame_times) > 1:
            time_span = self._frame_times[-1] - self._frame_times[0]
            if time_span > 0:
                self._metrics.current_fps = (len(self._frame_times) - 1) / time_span
        
        # Check for dropped frames
        if frame_time_ms > (self._target_frame_interval * 1.5):
            self._metrics.dropped_frames += 1
        
        # Emit FPS update periodically
        if current_time - self._last_performance_check >= self._performance_check_interval:
            self.fps_updated.emit(self._metrics.current_fps)
            self._last_performance_check = current_time
    
    def _check_performance_adjustment(self) -> None:
        """Check if automatic quality adjustment is needed."""
        current_time = time.time()
        
        # Only adjust if enough time has passed since last adjustment
        if current_time - self._last_quality_adjustment < self._quality_adjustment_cooldown:
            return
        
        current_fps = self._metrics.current_fps
        
        # Check if we need to lower quality
        if (current_fps < self._fps_threshold_low and 
            self._current_quality != QualityPreset.DRAFT):
            
            if self._current_quality == QualityPreset.HIGH:
                new_quality = QualityPreset.NORMAL
            else:
                new_quality = QualityPreset.DRAFT
            
            self.set_quality_preset(new_quality)
            self._last_quality_adjustment = current_time
            self.performance_warning.emit(
                f"Lowered quality to {new_quality.value} due to low FPS ({current_fps:.1f})"
            )
        
        # Check if we can raise quality
        elif (current_fps > self._fps_threshold_high and 
              self._current_quality != QualityPreset.HIGH):
            
            if self._current_quality == QualityPreset.DRAFT:
                new_quality = QualityPreset.NORMAL
            else:
                new_quality = QualityPreset.HIGH
            
            self.set_quality_preset(new_quality)
            self._last_quality_adjustment = current_time
            logger.info(f"Raised quality to {new_quality.value} due to good performance")
    
    def _apply_quality_settings(self, quality: QualityPreset) -> None:
        """
        Apply quality-specific rendering settings.
        
        Args:
            quality: Quality preset to apply
        """
        self._metrics.quality_preset = quality
        
        if quality == QualityPreset.DRAFT:
            # Lower quality settings for better performance
            self._target_frame_interval = 1000 / 30  # 30fps for draft
            # Reduce effect quality, disable anti-aliasing, etc.
            
        elif quality == QualityPreset.NORMAL:
            # Balanced settings
            self._target_frame_interval = 1000 / 60  # 60fps
            # Standard effect quality
            
        elif quality == QualityPreset.HIGH:
            # High quality settings
            self._target_frame_interval = 1000 / 60  # 60fps with high quality
            # Maximum effect quality, enhanced anti-aliasing, etc.
        
        # Update timer interval
        if self._render_timer.isActive():
            self._render_timer.setInterval(int(self._target_frame_interval))
    
    def _reset_performance_metrics(self) -> None:
        """Reset performance metrics to initial state."""
        self._metrics = PerformanceMetrics()
        self._metrics.target_fps = 60.0
        self._metrics.quality_preset = self._current_quality
        self._frame_times.clear()
        self._last_frame_time = time.time()
    
    def _on_playback_state_changed(self, is_playing: bool) -> None:
        """Handle timeline playback state changes."""
        if is_playing:
            self.play()
        else:
            self.pause()
    
    def _on_renderer_fps_updated(self, fps: float) -> None:
        """Handle FPS updates from the renderer."""
        # This can be used for additional FPS monitoring if needed
        pass
    
    def set_video_synchronization(self, enabled: bool) -> None:
        """
        Enable or disable video synchronization.
        
        Args:
            enabled: Whether to synchronize with video playback
        """
        # This would control whether preview follows real-time or manual scrubbing
        pass
    
    def get_frame_at_time(self, time: float) -> Optional[np.ndarray]:
        """
        Get a rendered frame at a specific time (for export or thumbnails).
        
        Args:
            time: Timeline time in seconds
            
        Returns:
            Rendered frame as numpy array or None if failed
        """
        # Save current state
        was_playing = self._is_playing
        original_time = self._timeline_engine.current_time
        
        try:
            # Temporarily seek to target time
            self._timeline_engine.current_time = time
            
            # Get active elements at this time
            active_elements = self._timeline_engine.get_active_elements_at_time(time)
            
            # Render frame (this would need to be implemented to return frame data)
            self._render_preview_frame(time, active_elements)
            
            # For now, return placeholder
            # In real implementation, this would capture the rendered frame
            return None
            
        finally:
            # Restore original state
            self._timeline_engine.current_time = original_time
            if was_playing:
                self.play()


class PreviewControlsWidget(QWidget):
    """
    UI widget providing preview controls for zoom, pan, quality, and safe areas.
    """
    
    def __init__(self, preview_system: PreviewSystem, parent=None):
        super().__init__(parent)
        self._preview_system = preview_system
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Zoom controls group
        zoom_group = QGroupBox("Zoom Controls")
        zoom_layout = QHBoxLayout(zoom_group)
        
        # Zoom slider
        self._zoom_slider = QSlider()
        self._zoom_slider.setOrientation(Qt.Orientation.Horizontal)
        self._zoom_slider.setMinimum(10)  # 0.1x zoom
        self._zoom_slider.setMaximum(1000)  # 10.0x zoom
        self._zoom_slider.setValue(100)  # 1.0x zoom
        self._zoom_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._zoom_slider.setTickInterval(100)
        
        # Zoom label
        self._zoom_label = QLabel("100%")
        self._zoom_label.setMinimumWidth(50)
        
        # Zoom buttons
        zoom_in_btn = QPushButton("Zoom In")
        zoom_out_btn = QPushButton("Zoom Out")
        zoom_fit_btn = QPushButton("Fit")
        zoom_actual_btn = QPushButton("100%")
        
        zoom_layout.addWidget(QLabel("Zoom:"))
        zoom_layout.addWidget(self._zoom_slider)
        zoom_layout.addWidget(self._zoom_label)
        zoom_layout.addWidget(zoom_in_btn)
        zoom_layout.addWidget(zoom_out_btn)
        zoom_layout.addWidget(zoom_fit_btn)
        zoom_layout.addWidget(zoom_actual_btn)
        
        # Pan controls group
        pan_group = QGroupBox("Pan Controls")
        pan_layout = QHBoxLayout(pan_group)
        
        # Pan reset button
        pan_reset_btn = QPushButton("Reset Pan")
        
        # Pan position labels
        self._pan_label = QLabel("Pan: (0, 0)")
        
        pan_layout.addWidget(self._pan_label)
        pan_layout.addWidget(pan_reset_btn)
        pan_layout.addStretch()
        
        # Quality controls group
        quality_group = QGroupBox("Quality Settings")
        quality_layout = QHBoxLayout(quality_group)
        
        # Quality preset combo box
        self._quality_combo = QComboBox()
        self._quality_combo.addItem("Draft", QualityPreset.DRAFT)
        self._quality_combo.addItem("Normal", QualityPreset.NORMAL)
        self._quality_combo.addItem("High", QualityPreset.HIGH)
        self._quality_combo.setCurrentIndex(1)  # Normal by default
        
        quality_layout.addWidget(QLabel("Quality:"))
        quality_layout.addWidget(self._quality_combo)
        quality_layout.addStretch()
        
        # Safe area controls group
        safe_area_group = QGroupBox("Safe Area Guides")
        safe_area_layout = QHBoxLayout(safe_area_group)
        
        # Safe area combo box
        self._safe_area_combo = QComboBox()
        self._safe_area_combo.addItem("None", SafeAreaType.NONE)
        self._safe_area_combo.addItem("Action Safe (90%)", SafeAreaType.ACTION_SAFE)
        self._safe_area_combo.addItem("Title Safe (80%)", SafeAreaType.TITLE_SAFE)
        self._safe_area_combo.addItem("Both", SafeAreaType.BOTH)
        
        safe_area_layout.addWidget(QLabel("Safe Areas:"))
        safe_area_layout.addWidget(self._safe_area_combo)
        safe_area_layout.addStretch()
        
        # Performance info group
        perf_group = QGroupBox("Performance")
        perf_layout = QHBoxLayout(perf_group)
        
        self._fps_label = QLabel("FPS: --")
        self._quality_status_label = QLabel("Quality: Normal")
        
        perf_layout.addWidget(self._fps_label)
        perf_layout.addWidget(self._quality_status_label)
        perf_layout.addStretch()
        
        # Add all groups to main layout
        layout.addWidget(zoom_group)
        layout.addWidget(pan_group)
        layout.addWidget(quality_group)
        layout.addWidget(safe_area_group)
        layout.addWidget(perf_group)
        layout.addStretch()
        
        # Connect button signals
        zoom_in_btn.clicked.connect(lambda: self._preview_system.zoom_in())
        zoom_out_btn.clicked.connect(lambda: self._preview_system.zoom_out())
        zoom_fit_btn.clicked.connect(lambda: self._preview_system.zoom_to_fit())
        zoom_actual_btn.clicked.connect(lambda: self._preview_system.zoom_to_actual_size())
        pan_reset_btn.clicked.connect(lambda: self._preview_system.set_pan(0.0, 0.0))
        
        # Connect slider and combo signals
        self._zoom_slider.valueChanged.connect(self._on_zoom_slider_changed)
        self._quality_combo.currentIndexChanged.connect(self._on_quality_changed)
        self._safe_area_combo.currentIndexChanged.connect(self._on_safe_area_changed)
    
    def _connect_signals(self) -> None:
        """Connect to preview system signals."""
        self._preview_system.viewport_changed.connect(self._on_viewport_changed)
        self._preview_system.fps_updated.connect(self._on_fps_updated)
        self._preview_system.quality_changed.connect(self._on_quality_changed_signal)
        self._preview_system.safe_area_changed.connect(self._on_safe_area_changed_signal)
    
    def _on_zoom_slider_changed(self, value: int) -> None:
        """Handle zoom slider changes."""
        zoom = value / 100.0  # Convert to zoom factor
        self._preview_system.set_zoom(zoom)
    
    def _on_quality_changed(self, index: int) -> None:
        """Handle quality preset changes."""
        quality = self._quality_combo.itemData(index)
        if quality:
            self._preview_system.set_quality_preset(quality)
    
    def _on_safe_area_changed(self, index: int) -> None:
        """Handle safe area guide changes."""
        safe_area_type = self._safe_area_combo.itemData(index)
        if safe_area_type:
            self._preview_system.set_safe_area_guides(safe_area_type)
    
    def _on_viewport_changed(self, transform: ViewportTransform) -> None:
        """Handle viewport transformation changes."""
        # Update zoom slider and label
        zoom_percent = int(transform.zoom * 100)
        self._zoom_slider.blockSignals(True)
        self._zoom_slider.setValue(zoom_percent)
        self._zoom_slider.blockSignals(False)
        
        self._zoom_label.setText(f"{zoom_percent}%")
        
        # Update pan label
        self._pan_label.setText(f"Pan: ({transform.pan_x:.0f}, {transform.pan_y:.0f})")
    
    def _on_fps_updated(self, fps: float) -> None:
        """Handle FPS updates."""
        self._fps_label.setText(f"FPS: {fps:.1f}")
    
    def _on_quality_changed_signal(self, quality: QualityPreset) -> None:
        """Handle quality preset changes from the preview system."""
        # Update combo box
        for i in range(self._quality_combo.count()):
            if self._quality_combo.itemData(i) == quality:
                self._quality_combo.blockSignals(True)
                self._quality_combo.setCurrentIndex(i)
                self._quality_combo.blockSignals(False)
                break
        
        # Update status label
        self._quality_status_label.setText(f"Quality: {quality.value.title()}")
    
    def _on_safe_area_changed_signal(self, safe_area_type: SafeAreaType) -> None:
        """Handle safe area guide changes from the preview system."""
        # Update combo box
        for i in range(self._safe_area_combo.count()):
            if self._safe_area_combo.itemData(i) == safe_area_type:
                self._safe_area_combo.blockSignals(True)
                self._safe_area_combo.setCurrentIndex(i)
                self._safe_area_combo.blockSignals(False)
                break