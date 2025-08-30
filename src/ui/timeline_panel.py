#!/usr/bin/env python3
"""
Timeline Panel - Karaoke Subtitle Creator

Multi-track timeline editor for precise timing control of subtitle tracks
and keyframe management.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QLabel, QPushButton, QSlider, QSpinBox, QComboBox,
    QSplitter, QTreeWidget, QTreeWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRect
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont

from .waveform_display import WaveformDisplay


class TimelineRuler(QWidget):
    """
    Timeline ruler showing time markers and current playhead position.
    """
    
    def __init__(self):
        super().__init__()
        self.setFixedHeight(30)
        self.setMinimumWidth(800)
        
        self.duration = 60.0  # Total timeline duration in seconds
        self.current_time = 0.0  # Current playhead position
        self.zoom_level = 1.0  # Pixels per second
        
    def set_duration(self, duration):
        """Set the total timeline duration."""
        self.duration = duration
        self.update()
    
    def set_current_time(self, time):
        """Set the current playhead position."""
        self.current_time = time
        self.update()
    
    def set_zoom_level(self, zoom):
        """Set the zoom level (pixels per second)."""
        self.zoom_level = zoom
        self.setMinimumWidth(int(self.duration * zoom))
        self.update()
    
    def paintEvent(self, event):
        """Paint the timeline ruler."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(60, 60, 60))
        
        # Calculate time markers
        width = self.width()
        height = self.height()
        
        # Major tick interval (seconds)
        major_interval = max(1, int(10 / self.zoom_level))
        minor_interval = major_interval / 5
        
        # Draw time markers
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        font = QFont("Arial", 8)
        painter.setFont(font)
        
        for i in range(0, int(self.duration) + 1, major_interval):
            x = int(i * self.zoom_level)
            if x <= width:
                # Major tick
                painter.drawLine(x, height - 15, x, height)
                
                # Time label
                minutes = i // 60
                seconds = i % 60
                time_text = f"{minutes:02d}:{seconds:02d}"
                painter.drawText(x + 2, height - 18, time_text)
        
        # Draw minor ticks
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        for i in range(0, int(self.duration * 5) + 1):
            time_pos = i * minor_interval
            x = int(time_pos * self.zoom_level)
            if x <= width and i % 5 != 0:  # Skip major ticks
                painter.drawLine(x, height - 8, x, height)
        
        # Draw playhead
        playhead_x = int(self.current_time * self.zoom_level)
        if 0 <= playhead_x <= width:
            painter.setPen(QPen(QColor(255, 100, 100), 2))
            painter.drawLine(playhead_x, 0, playhead_x, height)


class TrackWidget(QWidget):
    """
    Individual track widget showing keyframes and text elements.
    """
    
    keyframe_selected = pyqtSignal(str, float)  # track_id, time
    keyframe_moved = pyqtSignal(str, float, float)  # track_id, old_time, new_time
    
    def __init__(self, track_id, track_name="Subtitle Track"):
        super().__init__()
        self.track_id = track_id
        self.track_name = track_name
        self.setFixedHeight(60)
        self.setMinimumWidth(800)
        
        self.keyframes = []  # List of (time, properties) tuples
        self.selected_keyframe = None
        self.zoom_level = 1.0
        self.duration = 60.0
        
        # Track colors
        self.track_color = QColor(80, 120, 160)
        self.keyframe_color = QColor(255, 200, 100)
        self.selected_color = QColor(255, 100, 100)
    
    def add_keyframe(self, time, properties=None):
        """Add a keyframe at the specified time."""
        if properties is None:
            properties = {}
        
        # Insert keyframe in chronological order
        inserted = False
        for i, (kf_time, kf_props) in enumerate(self.keyframes):
            if time < kf_time:
                self.keyframes.insert(i, (time, properties))
                inserted = True
                break
        
        if not inserted:
            self.keyframes.append((time, properties))
        
        self.update()
    
    def remove_keyframe(self, time):
        """Remove keyframe at the specified time."""
        self.keyframes = [(t, p) for t, p in self.keyframes if abs(t - time) > 0.01]
        self.update()
    
    def set_zoom_level(self, zoom):
        """Set the zoom level."""
        self.zoom_level = zoom
        self.setMinimumWidth(int(self.duration * zoom))
        self.update()
    
    def set_duration(self, duration):
        """Set the track duration."""
        self.duration = duration
        self.setMinimumWidth(int(duration * self.zoom_level))
        self.update()
    
    def paintEvent(self, event):
        """Paint the track."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(45, 45, 45))
        
        # Track background
        track_rect = QRect(0, 10, self.width(), 40)
        painter.fillRect(track_rect, self.track_color.darker(150))
        
        # Track border
        painter.setPen(QPen(self.track_color, 1))
        painter.drawRect(track_rect)
        
        # Draw keyframes
        for time, properties in self.keyframes:
            x = int(time * self.zoom_level)
            
            # Keyframe diamond
            keyframe_size = 8
            color = self.selected_color if (time, properties) == self.selected_keyframe else self.keyframe_color
            
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color.darker(120), 1))
            
            # Draw diamond shape
            points = [
                (x, 30 - keyframe_size),  # Top
                (x + keyframe_size, 30),  # Right
                (x, 30 + keyframe_size),  # Bottom
                (x - keyframe_size, 30)   # Left
            ]
            
            from PyQt6.QtCore import QPoint
            from PyQt6.QtGui import QPolygon
            
            polygon = QPolygon([QPoint(px, py) for px, py in points])
            painter.drawPolygon(polygon)
        
        # Track label
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        font = QFont("Arial", 9)
        painter.setFont(font)
        painter.drawText(5, 25, self.track_name)
    
    def mousePressEvent(self, event):
        """Handle mouse press for keyframe selection."""
        if event.button() == Qt.MouseButton.LeftButton:
            click_time = event.position().x() / self.zoom_level
            
            # Find closest keyframe
            closest_keyframe = None
            min_distance = float('inf')
            
            for time, properties in self.keyframes:
                distance = abs(time - click_time)
                if distance < min_distance and distance < 0.5:  # 0.5 second tolerance
                    min_distance = distance
                    closest_keyframe = (time, properties)
            
            if closest_keyframe:
                self.selected_keyframe = closest_keyframe
                self.keyframe_selected.emit(self.track_id, closest_keyframe[0])
                self.update()


class TimelinePanel(QWidget):
    """
    Main timeline panel with multi-track editing capabilities.
    """
    
    # Signals
    time_changed = pyqtSignal(float)  # current_time
    keyframe_selected = pyqtSignal(str, float)  # track_id, time
    track_added = pyqtSignal(str)  # track_id
    
    def __init__(self):
        super().__init__()
        self.current_time = 0.0
        self.duration = 60.0
        self.zoom_level = 10.0  # pixels per second
        self.is_playing = False
        
        self.tracks = {}  # track_id -> TrackWidget
        self.waveform_display = None
        
        self._setup_ui()
        self._setup_playback_timer()
    
    def _setup_ui(self):
        """Set up the timeline UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Timeline controls
        controls_layout = QHBoxLayout()
        
        # Playback controls
        self.play_button = QPushButton("Play")
        self.play_button.setCheckable(True)
        self.play_button.clicked.connect(self._toggle_playback)
        controls_layout.addWidget(self.play_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self._stop_playback)
        controls_layout.addWidget(self.stop_button)
        
        controls_layout.addWidget(QLabel("Time:"))
        
        # Time display
        self.time_spinbox = QSpinBox()
        self.time_spinbox.setRange(0, int(self.duration))
        self.time_spinbox.setSuffix(" s")
        self.time_spinbox.valueChanged.connect(self._time_changed)
        controls_layout.addWidget(self.time_spinbox)
        
        controls_layout.addWidget(QLabel("Zoom:"))
        
        # Zoom control
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(1, 50)
        self.zoom_slider.setValue(int(self.zoom_level))
        self.zoom_slider.valueChanged.connect(self._zoom_changed)
        controls_layout.addWidget(self.zoom_slider)
        
        # Add track button
        self.add_track_button = QPushButton("Add Track")
        self.add_track_button.clicked.connect(self._add_track)
        controls_layout.addWidget(self.add_track_button)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Timeline area
        timeline_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Ruler and tracks scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Timeline content widget
        self.timeline_content = QWidget()
        self.timeline_layout = QVBoxLayout(self.timeline_content)
        self.timeline_layout.setContentsMargins(0, 0, 0, 0)
        self.timeline_layout.setSpacing(1)
        
        # Timeline ruler
        self.ruler = TimelineRuler()
        self.ruler.set_duration(self.duration)
        self.ruler.set_zoom_level(self.zoom_level)
        self.timeline_layout.addWidget(self.ruler)
        
        # Waveform display (will be added when audio is imported)
        
        # Add initial subtitle track
        self._add_track()
        
        scroll_area.setWidget(self.timeline_content)
        timeline_splitter.addWidget(scroll_area)
        
        # Set splitter proportions
        timeline_splitter.setSizes([400])
        
        layout.addWidget(timeline_splitter)
    
    def _setup_playback_timer(self):
        """Set up the playback timer."""
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self._update_playback)
        self.playback_timer.setInterval(16)  # ~60 FPS
    
    def _toggle_playback(self):
        """Toggle playback state."""
        if self.is_playing:
            self._pause_playback()
        else:
            self._start_playback()
    
    def _start_playback(self):
        """Start playback."""
        self.is_playing = True
        self.play_button.setText("Pause")
        self.playback_timer.start()
    
    def _pause_playback(self):
        """Pause playback."""
        self.is_playing = False
        self.play_button.setText("Play")
        self.play_button.setChecked(False)
        self.playback_timer.stop()
    
    def _stop_playback(self):
        """Stop playback and reset to beginning."""
        self._pause_playback()
        self.set_current_time(0.0)
    
    def _update_playback(self):
        """Update playback position."""
        if self.is_playing:
            # Advance time by timer interval
            new_time = self.current_time + 0.016  # 16ms
            
            if new_time >= self.duration:
                self._stop_playback()
            else:
                self.set_current_time(new_time)
    
    def _time_changed(self, value):
        """Handle time spinbox change."""
        self.set_current_time(float(value))
    
    def _zoom_changed(self, value):
        """Handle zoom slider change."""
        self.zoom_level = float(value)
        
        # Update ruler and all tracks
        self.ruler.set_zoom_level(self.zoom_level)
        for track in self.tracks.values():
            track.set_zoom_level(self.zoom_level)
    
    def _add_track(self):
        """Add a new subtitle track."""
        track_id = f"track_{len(self.tracks) + 1}"
        track_name = f"Subtitle Track {len(self.tracks) + 1}"
        
        track_widget = TrackWidget(track_id, track_name)
        track_widget.set_duration(self.duration)
        track_widget.set_zoom_level(self.zoom_level)
        
        # Connect signals
        track_widget.keyframe_selected.connect(self.keyframe_selected.emit)
        
        self.tracks[track_id] = track_widget
        self.timeline_layout.addWidget(track_widget)
        
        self.track_added.emit(track_id)
    
    def set_current_time(self, time):
        """Set the current timeline position."""
        self.current_time = max(0.0, min(time, self.duration))
        
        # Update UI
        self.time_spinbox.blockSignals(True)
        self.time_spinbox.setValue(int(self.current_time))
        self.time_spinbox.blockSignals(False)
        
        self.ruler.set_current_time(self.current_time)
        
        self.time_changed.emit(self.current_time)
    
    def set_duration(self, duration):
        """Set the timeline duration."""
        self.duration = duration
        self.time_spinbox.setRange(0, int(duration))
        
        self.ruler.set_duration(duration)
        for track in self.tracks.values():
            track.set_duration(duration)
    
    def add_waveform_display(self, audio_data, sample_rate):
        """Add waveform display for audio reference."""
        if self.waveform_display:
            self.timeline_layout.removeWidget(self.waveform_display)
            self.waveform_display.deleteLater()
        
        self.waveform_display = WaveformDisplay()
        self.waveform_display.set_audio_data(audio_data, sample_rate)
        self.waveform_display.set_zoom_level(self.zoom_level)
        
        # Insert after ruler
        self.timeline_layout.insertWidget(1, self.waveform_display)
    
    def add_keyframe_to_track(self, track_id, time, properties=None):
        """Add a keyframe to the specified track."""
        if track_id in self.tracks:
            self.tracks[track_id].add_keyframe(time, properties)
    
    def get_selected_track_id(self):
        """Get the currently selected track ID."""
        # For now, return the first track
        if self.tracks:
            return list(self.tracks.keys())[0]
        return None