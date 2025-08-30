"""
Waveform display widget for timeline visualization.
"""

from typing import Optional, Tuple, List
import numpy as np
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QPixmap
from PyQt6.QtOpenGLWidgets import QOpenGLWidget

# Note: These imports will be connected when the modules are integrated
# from ..audio.waveform_generator import WaveformData, WaveformRenderer
# from ..core.timeline_engine import TimelineEngine


class WaveformDisplayWidget(QWidget):
    """
    Widget for displaying audio waveform in timeline interface.
    
    This widget provides:
    - Real-time waveform visualization
    - Zoom and pan controls
    - Time-based navigation
    - Integration with timeline engine
    """
    
    # Signals
    time_clicked = pyqtSignal(float)  # Emitted when user clicks on waveform
    zoom_changed = pyqtSignal(float)  # Emitted when zoom level changes
    
    def __init__(self, timeline_engine=None, parent=None):
        """
        Initialize waveform display widget.
        
        Args:
            timeline_engine: Timeline engine for waveform data
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._timeline_engine = timeline_engine
        self._waveform_data = None
        self._waveform_renderer = None  # Will be initialized when integrated
        
        # Display properties
        self._zoom_level = 1.0  # Zoom factor (1.0 = fit to widget)
        self._scroll_offset = 0.0  # Horizontal scroll offset in seconds
        self._visible_duration = 10.0  # Visible time range in seconds
        
        # Playback cursor
        self._current_time = 0.0
        self._show_cursor = True
        self._cursor_color = QColor(255, 255, 0, 200)  # Yellow cursor
        
        # Cached waveform image
        self._waveform_pixmap: Optional[QPixmap] = None
        self._pixmap_dirty = True
        
        # Update timer for real-time display
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_display)
        self._update_timer.start(33)  # ~30 FPS
        
        # Widget properties
        self.setMinimumHeight(80)
        self.setMaximumHeight(200)
        self.setMouseTracking(True)
        
        # Colors
        self._background_color = QColor(30, 30, 30)
        self._grid_color = QColor(60, 60, 60)
        self._text_color = QColor(200, 200, 200)
    
    def set_timeline_engine(self, timeline_engine) -> None:
        """
        Set the timeline engine for waveform data.
        
        Args:
            timeline_engine: Timeline engine instance
        """
        self._timeline_engine = timeline_engine
        self._refresh_waveform_data()
    
    def set_waveform_data(self, waveform_data) -> None:
        """
        Set waveform data directly.
        
        Args:
            waveform_data: Waveform data to display
        """
        self._waveform_data = waveform_data
        self._pixmap_dirty = True
        self.update()
    
    def set_zoom_level(self, zoom: float) -> None:
        """
        Set zoom level for waveform display.
        
        Args:
            zoom: Zoom factor (1.0 = fit to widget, >1.0 = zoomed in)
        """
        zoom = max(0.1, min(zoom, 100.0))  # Clamp to reasonable range
        if zoom != self._zoom_level:
            self._zoom_level = zoom
            self._pixmap_dirty = True
            self.zoom_changed.emit(zoom)
            self.update()
    
    def set_scroll_offset(self, offset: float) -> None:
        """
        Set horizontal scroll offset.
        
        Args:
            offset: Scroll offset in seconds
        """
        if self._waveform_data:
            max_offset = max(0.0, self._waveform_data.duration - self._visible_duration)
            offset = max(0.0, min(offset, max_offset))
        else:
            offset = max(0.0, offset)
        
        if offset != self._scroll_offset:
            self._scroll_offset = offset
            self._pixmap_dirty = True
            self.update()
    
    def set_current_time(self, time: float) -> None:
        """
        Set current playback time for cursor display.
        
        Args:
            time: Current time in seconds
        """
        if time != self._current_time:
            self._current_time = time
            self.update()
    
    def set_visible_duration(self, duration: float) -> None:
        """
        Set visible time duration.
        
        Args:
            duration: Visible duration in seconds
        """
        duration = max(0.1, duration)
        if duration != self._visible_duration:
            self._visible_duration = duration
            self._pixmap_dirty = True
            self.update()
    
    def zoom_in(self, factor: float = 2.0) -> None:
        """Zoom in by the specified factor."""
        self.set_zoom_level(self._zoom_level * factor)
    
    def zoom_out(self, factor: float = 2.0) -> None:
        """Zoom out by the specified factor."""
        self.set_zoom_level(self._zoom_level / factor)
    
    def zoom_to_fit(self) -> None:
        """Zoom to fit entire waveform in widget."""
        self.set_zoom_level(1.0)
        self.set_scroll_offset(0.0)
    
    def scroll_to_time(self, time: float) -> None:
        """
        Scroll to center the specified time.
        
        Args:
            time: Time to center in seconds
        """
        center_offset = time - (self._visible_duration / 2.0)
        self.set_scroll_offset(center_offset)
    
    def time_to_pixel(self, time: float) -> int:
        """
        Convert time to pixel coordinate.
        
        Args:
            time: Time in seconds
            
        Returns:
            Pixel x-coordinate
        """
        if self._visible_duration <= 0:
            return 0
        
        relative_time = time - self._scroll_offset
        return int((relative_time / self._visible_duration) * self.width())
    
    def pixel_to_time(self, x: int) -> float:
        """
        Convert pixel coordinate to time.
        
        Args:
            x: Pixel x-coordinate
            
        Returns:
            Time in seconds
        """
        if self.width() <= 0:
            return 0.0
        
        relative_time = (x / self.width()) * self._visible_duration
        return self._scroll_offset + relative_time
    
    def paintEvent(self, event):
        """Handle paint events to draw waveform."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fill background
        painter.fillRect(self.rect(), self._background_color)
        
        # Draw waveform if available
        if self._waveform_data:
            self._draw_waveform(painter)
        else:
            self._draw_no_audio_message(painter)
        
        # Draw time grid
        self._draw_time_grid(painter)
        
        # Draw playback cursor
        if self._show_cursor:
            self._draw_cursor(painter)
    
    def mousePressEvent(self, event):
        """Handle mouse press events for time navigation."""
        if event.button() == Qt.MouseButton.LeftButton:
            clicked_time = self.pixel_to_time(event.position().x())
            self.time_clicked.emit(clicked_time)
    
    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming."""
        # Zoom in/out based on wheel direction
        zoom_factor = 1.2
        if event.angleDelta().y() > 0:
            self.zoom_in(zoom_factor)
        else:
            self.zoom_out(zoom_factor)
    
    def resizeEvent(self, event):
        """Handle resize events to invalidate cached pixmap."""
        self._pixmap_dirty = True
        super().resizeEvent(event)
    
    def _refresh_waveform_data(self) -> None:
        """Refresh waveform data from timeline engine."""
        if not self._timeline_engine:
            return
        
        # Calculate resolution based on widget width and zoom
        target_resolution = max(100, int(self.width() * self._zoom_level))
        
        # Get waveform data from timeline engine
        waveform_data = self._timeline_engine.get_waveform_data(resolution=target_resolution)
        
        if waveform_data != self._waveform_data:
            self._waveform_data = waveform_data
            self._pixmap_dirty = True
    
    def _update_display(self) -> None:
        """Update display based on timeline engine state."""
        if not self._timeline_engine:
            return
        
        # Update current time from timeline
        current_time = self._timeline_engine.current_time
        if current_time != self._current_time:
            self.set_current_time(current_time)
        
        # Refresh waveform data if needed
        if not self._waveform_data or self._pixmap_dirty:
            self._refresh_waveform_data()
    
    def _draw_waveform(self, painter: QPainter) -> None:
        """
        Draw the waveform visualization.
        
        Args:
            painter: QPainter instance for drawing
        """
        if not self._waveform_data:
            return
        
        # Generate or use cached waveform pixmap
        if self._pixmap_dirty or not self._waveform_pixmap:
            self._generate_waveform_pixmap()
        
        if self._waveform_pixmap:
            painter.drawPixmap(0, 0, self._waveform_pixmap)
    
    def _generate_waveform_pixmap(self) -> None:
        """Generate cached pixmap of waveform visualization."""
        if not self._waveform_data:
            return
        
        width = self.width()
        height = self.height()
        
        if width <= 0 or height <= 0:
            return
        
        # Calculate visible time range
        end_time = self._scroll_offset + self._visible_duration
        
        # Render waveform to numpy array
        waveform_image = self._waveform_renderer.render_waveform_data(
            self._waveform_data, width, height, self._scroll_offset, end_time
        )
        
        # Convert numpy array to QPixmap
        # Convert float RGBA to uint8 RGBA
        image_uint8 = (waveform_image * 255).astype(np.uint8)
        
        # Create QPixmap from numpy array
        from PyQt6.QtGui import QImage
        
        # Convert RGBA to RGB (Qt expects RGB format)
        rgb_image = image_uint8[:, :, :3]  # Drop alpha channel
        
        # Create QImage
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        
        qimage = QImage(
            rgb_image.data.tobytes(),
            w, h,
            bytes_per_line,
            QImage.Format.Format_RGB888
        )
        
        # Convert to pixmap
        self._waveform_pixmap = QPixmap.fromImage(qimage)
        self._pixmap_dirty = False
    
    def _draw_no_audio_message(self, painter: QPainter) -> None:
        """
        Draw message when no audio is available.
        
        Args:
            painter: QPainter instance for drawing
        """
        painter.setPen(QPen(self._text_color))
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            "No audio loaded"
        )
    
    def _draw_time_grid(self, painter: QPainter) -> None:
        """
        Draw time grid lines and labels.
        
        Args:
            painter: QPainter instance for drawing
        """
        if self._visible_duration <= 0:
            return
        
        painter.setPen(QPen(self._grid_color, 1))
        
        # Calculate grid interval
        grid_interval = self._calculate_grid_interval()
        
        # Draw vertical grid lines
        start_time = int(self._scroll_offset / grid_interval) * grid_interval
        time = start_time
        
        while time <= self._scroll_offset + self._visible_duration:
            x = self.time_to_pixel(time)
            if 0 <= x <= self.width():
                painter.drawLine(x, 0, x, self.height())
                
                # Draw time label
                painter.setPen(QPen(self._text_color))
                time_str = self._format_time(time)
                painter.drawText(x + 2, 15, time_str)
                painter.setPen(QPen(self._grid_color, 1))
            
            time += grid_interval
    
    def _draw_cursor(self, painter: QPainter) -> None:
        """
        Draw playback cursor.
        
        Args:
            painter: QPainter instance for drawing
        """
        cursor_x = self.time_to_pixel(self._current_time)
        
        if 0 <= cursor_x <= self.width():
            painter.setPen(QPen(self._cursor_color, 2))
            painter.drawLine(cursor_x, 0, cursor_x, self.height())
    
    def _calculate_grid_interval(self) -> float:
        """
        Calculate appropriate grid interval based on zoom level.
        
        Returns:
            Grid interval in seconds
        """
        # Target about 5-10 grid lines across the visible area
        target_lines = 8
        base_interval = self._visible_duration / target_lines
        
        # Round to nice intervals
        intervals = [0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
        
        for interval in intervals:
            if interval >= base_interval:
                return interval
        
        return intervals[-1]
    
    def _format_time(self, time: float) -> str:
        """
        Format time for display.
        
        Args:
            time: Time in seconds
            
        Returns:
            Formatted time string
        """
        if time < 60:
            return f"{time:.1f}s"
        else:
            minutes = int(time // 60)
            seconds = time % 60
            return f"{minutes}:{seconds:04.1f}"
    
    def set_waveform_colors(self, background: Tuple[int, int, int] = None,
                           waveform: Tuple[int, int, int, int] = None,
                           cursor: Tuple[int, int, int, int] = None) -> None:
        """
        Set custom colors for waveform display.
        
        Args:
            background: Background color (R, G, B)
            waveform: Waveform color (R, G, B, A)
            cursor: Cursor color (R, G, B, A)
        """
        if background is not None:
            self._background_color = QColor(*background)
        
        if waveform is not None:
            # Convert to float values for renderer
            waveform_float = tuple(c / 255.0 for c in waveform)
            self._waveform_renderer.set_colors(waveform=waveform_float)
            self._pixmap_dirty = True
        
        if cursor is not None:
            self._cursor_color = QColor(*cursor)
        
        self.update()
    
    def get_zoom_level(self) -> float:
        """Get current zoom level."""
        return self._zoom_level
    
    def get_scroll_offset(self) -> float:
        """Get current scroll offset."""
        return self._scroll_offset
    
    def get_visible_duration(self) -> float:
        """Get visible duration."""
        return self._visible_duration
# Alias for compatibility
WaveformDisplay = WaveformDisplayWidget