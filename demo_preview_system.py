#!/usr/bin/env python3
"""
Demo script for the preview system with 60fps rendering.

This script demonstrates the real-time preview system capabilities including:
- 60fps preview rendering with automatic quality adjustment
- Video synchronization with subtitle overlay rendering
- Performance monitoring and frame rate adjustment
"""

import sys
import time
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QSlider
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from graphics.opengl_renderer import OpenGLRenderer
from core.timeline_engine import TimelineEngine
from core.models import VideoAsset, AudioAsset, SubtitleTrack, TextElement
from ui.preview_system import PreviewSystem, QualityPreset


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PreviewDemoWindow(QMainWindow):
    """Main window for preview system demo."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Preview System Demo - 60fps Rendering")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create OpenGL renderer
        self.renderer = OpenGLRenderer()
        self.renderer.setMinimumSize(800, 450)  # 16:9 aspect ratio
        layout.addWidget(self.renderer)
        
        # Create timeline engine with sample data
        self.timeline_engine = self._create_sample_timeline()
        
        # Create preview system
        self.preview_system = PreviewSystem(self.renderer, self.timeline_engine)
        
        # Connect signals
        self.preview_system.fps_updated.connect(self._on_fps_updated)
        self.preview_system.quality_changed.connect(self._on_quality_changed)
        self.preview_system.performance_warning.connect(self._on_performance_warning)
        
        # Create controls
        self._create_controls(layout)
        
        # Status display
        self._create_status_display(layout)
        
        # Start preview system
        self.preview_system.start_preview()
        
        logger.info("Preview demo window initialized")
    
    def _create_sample_timeline(self) -> TimelineEngine:
        """Create a sample timeline with test data."""
        # Create sample video asset
        video_asset = VideoAsset(
            path="test_video.mp4",
            duration=30.0,  # 30 seconds
            fps=30.0,
            resolution=(1920, 1080),
            codec="h264"
        )
        
        # Create timeline engine
        timeline = TimelineEngine(video_asset)
        
        # Create sample subtitle track
        subtitle_track = SubtitleTrack(
            id="main_track",
            elements=[],
            keyframes=[],
            start_time=0.0,
            end_time=30.0
        )
        
        # Add sample text elements
        text_elements = [
            TextElement(
                content="Welcome to the karaoke demo!",
                font_family="Arial",
                font_size=48.0,
                color=(1.0, 1.0, 1.0, 1.0),  # White
                position=(0.5, 0.8),  # Center horizontally, near bottom
                rotation=(0.0, 0.0, 0.0),
                effects=[]
            ),
            TextElement(
                content="This text will animate and change colors",
                font_family="Arial",
                font_size=36.0,
                color=(1.0, 0.5, 0.0, 1.0),  # Orange
                position=(0.5, 0.6),
                rotation=(0.0, 0.0, 0.0),
                effects=[]
            ),
            TextElement(
                content="60fps real-time preview rendering",
                font_family="Arial",
                font_size=32.0,
                color=(0.0, 1.0, 0.5, 1.0),  # Green
                position=(0.5, 0.4),
                rotation=(0.0, 0.0, 0.0),
                effects=[]
            )
        ]
        
        subtitle_track.elements = text_elements
        
        # Add keyframes for animation
        timeline.add_keyframe("main_track", 0.0, {
            "opacity": 0.0,
            "scale": 0.5,
            "color_intensity": 0.0
        })
        
        timeline.add_keyframe("main_track", 2.0, {
            "opacity": 1.0,
            "scale": 1.0,
            "color_intensity": 1.0
        })
        
        timeline.add_keyframe("main_track", 15.0, {
            "opacity": 1.0,
            "scale": 1.2,
            "color_intensity": 1.5
        })
        
        timeline.add_keyframe("main_track", 28.0, {
            "opacity": 1.0,
            "scale": 1.0,
            "color_intensity": 1.0
        })
        
        timeline.add_keyframe("main_track", 30.0, {
            "opacity": 0.0,
            "scale": 0.8,
            "color_intensity": 0.0
        })
        
        # Add track to timeline
        timeline.add_subtitle_track(subtitle_track)
        
        return timeline
    
    def _create_controls(self, layout: QVBoxLayout) -> None:
        """Create playback and quality controls."""
        controls_layout = QHBoxLayout()
        
        # Playback controls
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self._toggle_playback)
        controls_layout.addWidget(self.play_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self._stop_playback)
        controls_layout.addWidget(self.stop_button)
        
        # Timeline scrubber
        controls_layout.addWidget(QLabel("Time:"))
        self.time_slider = QSlider(Qt.Orientation.Horizontal)
        self.time_slider.setMinimum(0)
        self.time_slider.setMaximum(int(self.timeline_engine.duration * 10))  # 0.1s precision
        self.time_slider.valueChanged.connect(self._on_time_changed)
        controls_layout.addWidget(self.time_slider)
        
        # Quality controls
        controls_layout.addWidget(QLabel("Quality:"))
        
        self.draft_button = QPushButton("Draft")
        self.draft_button.clicked.connect(lambda: self.preview_system.set_quality_preset(QualityPreset.DRAFT))
        controls_layout.addWidget(self.draft_button)
        
        self.normal_button = QPushButton("Normal")
        self.normal_button.clicked.connect(lambda: self.preview_system.set_quality_preset(QualityPreset.NORMAL))
        controls_layout.addWidget(self.normal_button)
        
        self.high_button = QPushButton("High")
        self.high_button.clicked.connect(lambda: self.preview_system.set_quality_preset(QualityPreset.HIGH))
        controls_layout.addWidget(self.high_button)
        
        layout.addLayout(controls_layout)
    
    def _create_status_display(self, layout: QVBoxLayout) -> None:
        """Create status display for performance metrics."""
        status_layout = QHBoxLayout()
        
        # FPS display
        self.fps_label = QLabel("FPS: 0.0")
        self.fps_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        status_layout.addWidget(self.fps_label)
        
        # Quality display
        self.quality_label = QLabel("Quality: Normal")
        status_layout.addWidget(self.quality_label)
        
        # Performance warning display
        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet("color: red;")
        status_layout.addWidget(self.warning_label)
        
        # Timeline time display
        self.time_label = QLabel("Time: 0.0s")
        status_layout.addWidget(self.time_label)
        
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        # Update timer for status display
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status_display)
        self.status_timer.start(100)  # Update every 100ms
    
    def _toggle_playback(self) -> None:
        """Toggle between play and pause."""
        if self.timeline_engine.is_playing():
            self.preview_system.pause()
            self.play_button.setText("Play")
        else:
            self.preview_system.play()
            self.play_button.setText("Pause")
    
    def _stop_playback(self) -> None:
        """Stop playback and reset to beginning."""
        self.preview_system.stop()
        self.play_button.setText("Play")
        self.time_slider.setValue(0)
    
    def _on_time_changed(self, value: int) -> None:
        """Handle timeline scrubber changes."""
        time_seconds = value / 10.0  # Convert from slider value to seconds
        self.preview_system.seek(time_seconds)
    
    def _on_fps_updated(self, fps: float) -> None:
        """Handle FPS updates from preview system."""
        self.fps_label.setText(f"FPS: {fps:.1f}")
        
        # Color code FPS display
        if fps >= 55.0:
            self.fps_label.setStyleSheet("color: green;")
        elif fps >= 45.0:
            self.fps_label.setStyleSheet("color: orange;")
        else:
            self.fps_label.setStyleSheet("color: red;")
    
    def _on_quality_changed(self, quality: QualityPreset) -> None:
        """Handle quality preset changes."""
        self.quality_label.setText(f"Quality: {quality.value.title()}")
        
        # Update button states
        self.draft_button.setEnabled(quality != QualityPreset.DRAFT)
        self.normal_button.setEnabled(quality != QualityPreset.NORMAL)
        self.high_button.setEnabled(quality != QualityPreset.HIGH)
    
    def _on_performance_warning(self, message: str) -> None:
        """Handle performance warnings."""
        self.warning_label.setText(message)
        logger.warning(f"Performance warning: {message}")
        
        # Clear warning after 3 seconds
        QTimer.singleShot(3000, lambda: self.warning_label.setText(""))
    
    def _update_status_display(self) -> None:
        """Update status display with current information."""
        # Update time display
        current_time = self.timeline_engine.current_time
        self.time_label.setText(f"Time: {current_time:.1f}s")
        
        # Update slider position (avoid feedback loop)
        if not self.time_slider.isSliderDown():
            slider_value = int(current_time * 10)
            self.time_slider.setValue(slider_value)
        
        # Update performance metrics display
        metrics = self.preview_system.get_performance_metrics()
        
        # You could add more detailed metrics display here
        # For example: frame time, dropped frames, etc.
    
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        logger.info("Shutting down preview demo")
        
        # Stop preview system
        self.preview_system.stop_preview()
        
        # Cleanup OpenGL resources
        self.renderer.cleanup()
        
        event.accept()


def main():
    """Main function to run the preview system demo."""
    print("Preview System Demo - 60fps Rendering")
    print("=" * 50)
    print()
    print("This demo showcases the real-time preview system with:")
    print("- 60fps target rendering with automatic quality adjustment")
    print("- Video synchronization with subtitle overlay rendering")
    print("- Performance monitoring and frame rate tracking")
    print("- Quality presets (Draft, Normal, High)")
    print()
    print("Controls:")
    print("- Play/Pause: Toggle video playback")
    print("- Stop: Stop playback and reset to beginning")
    print("- Time slider: Scrub through timeline")
    print("- Quality buttons: Change rendering quality preset")
    print()
    print("The system will automatically adjust quality if performance drops below 45fps")
    print("and raise quality if performance is consistently above 55fps.")
    print()
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    try:
        # Create and show demo window
        window = PreviewDemoWindow()
        window.show()
        
        logger.info("Starting preview system demo")
        
        # Run application
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Error running demo: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()