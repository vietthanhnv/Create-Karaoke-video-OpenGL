#!/usr/bin/env python3
"""
Demo script for preview system controls including zoom, pan, and safe area guides.

This script demonstrates the new preview control features:
- Zoom controls (zoom in/out, fit to screen, actual size)
- Pan controls for detailed editing
- Quality preset system
- Safe area guides for TV compatibility
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QWidget, QPushButton, QLabel, QSlider, QComboBox,
    QGroupBox, QCheckBox, QSpinBox
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont

from ui.preview_system import (
    PreviewSystem, QualityPreset, ViewportTransform, 
    SafeAreaType, PreviewControlsWidget
)
from graphics.opengl_renderer import OpenGLRenderer
from core.timeline_engine import TimelineEngine
from core.models import VideoAsset, SubtitleTrack, TextElement


class PreviewControlsDemo(QMainWindow):
    """Demo application for preview controls."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Preview Controls Demo - Karaoke Subtitle Creator")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create demo data
        self._setup_demo_data()
        
        # Create UI
        self._setup_ui()
        
        # Start demo
        self._start_demo()
    
    def _setup_demo_data(self):
        """Set up demo video and subtitle data."""
        # Create demo video asset
        self.video_asset = VideoAsset(
            path="demo_video.mp4",
            duration=30.0,
            fps=30.0,
            resolution=(1920, 1080),
            codec="h264"
        )
        
        # Create timeline engine
        self.timeline_engine = TimelineEngine(self.video_asset)
        
        # Create demo subtitle track
        subtitle_track = SubtitleTrack(
            id="demo_track",
            elements=[
                TextElement(
                    content="Welcome to Karaoke Creator!",
                    font_family="Arial",
                    font_size=48.0,
                    color=(1.0, 1.0, 1.0, 1.0),
                    position=(0.5, 0.8),  # Bottom center
                    rotation=(0.0, 0.0, 0.0),
                    effects=[]
                ),
                TextElement(
                    content="🎵 Sing along with the music 🎵",
                    font_family="Arial",
                    font_size=36.0,
                    color=(1.0, 0.8, 0.2, 1.0),  # Golden color
                    position=(0.5, 0.2),  # Top center
                    rotation=(0.0, 0.0, 0.0),
                    effects=[]
                )
            ],
            keyframes=[],
            start_time=0.0,
            end_time=30.0
        )
        
        self.timeline_engine.add_subtitle_track(subtitle_track)
        
        # Add some keyframes for animation
        self.timeline_engine.add_keyframe("demo_track", 0.0, {"opacity": 0.0})
        self.timeline_engine.add_keyframe("demo_track", 2.0, {"opacity": 1.0})
        self.timeline_engine.add_keyframe("demo_track", 28.0, {"opacity": 1.0})
        self.timeline_engine.add_keyframe("demo_track", 30.0, {"opacity": 0.0})
    
    def _setup_ui(self):
        """Set up the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # Left side - Preview area
        preview_layout = QVBoxLayout()
        
        # Mock OpenGL renderer (placeholder)
        self.preview_area = QWidget()
        self.preview_area.setMinimumSize(800, 600)
        self.preview_area.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border: 2px solid #555;
                border-radius: 5px;
            }
        """)
        
        # Preview info label
        self.preview_info = QLabel("OpenGL Preview Area\n(Mock renderer for demo)")
        self.preview_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_info.setStyleSheet("color: #ccc; font-size: 14px;")
        
        preview_layout.addWidget(self.preview_area)
        preview_layout.addWidget(self.preview_info)
        
        # Right side - Controls
        controls_layout = QVBoxLayout()
        
        # Create preview system (with mock renderer)
        mock_renderer = MockOpenGLRenderer()
        self.preview_system = PreviewSystem(mock_renderer, self.timeline_engine)
        
        # Create controls widget
        self.controls_widget = PreviewControlsWidget(self.preview_system)
        controls_layout.addWidget(self.controls_widget)
        
        # Add demo controls
        demo_group = self._create_demo_controls()
        controls_layout.addWidget(demo_group)
        
        # Add layouts to main layout
        main_layout.addLayout(preview_layout, 2)  # 2/3 of space
        main_layout.addLayout(controls_layout, 1)  # 1/3 of space
        
        # Connect signals for demo feedback
        self._connect_demo_signals()
    
    def _create_demo_controls(self):
        """Create additional demo controls."""
        demo_group = QGroupBox("Demo Controls")
        layout = QVBoxLayout(demo_group)
        
        # Demo scenario buttons
        scenario_layout = QHBoxLayout()
        
        btn_zoom_demo = QPushButton("Zoom Demo")
        btn_pan_demo = QPushButton("Pan Demo")
        btn_safe_area_demo = QPushButton("Safe Area Demo")
        btn_quality_demo = QPushButton("Quality Demo")
        
        scenario_layout.addWidget(btn_zoom_demo)
        scenario_layout.addWidget(btn_pan_demo)
        scenario_layout.addWidget(btn_safe_area_demo)
        scenario_layout.addWidget(btn_quality_demo)
        
        # Demo info display
        self.demo_info = QLabel("Click demo buttons to see preview controls in action!")
        self.demo_info.setWordWrap(True)
        self.demo_info.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        
        # Performance display
        self.performance_info = QLabel("Performance: Ready")
        self.performance_info.setStyleSheet("font-family: monospace; padding: 5px;")
        
        layout.addLayout(scenario_layout)
        layout.addWidget(self.demo_info)
        layout.addWidget(self.performance_info)
        
        # Connect demo buttons
        btn_zoom_demo.clicked.connect(self._run_zoom_demo)
        btn_pan_demo.clicked.connect(self._run_pan_demo)
        btn_safe_area_demo.clicked.connect(self._run_safe_area_demo)
        btn_quality_demo.clicked.connect(self._run_quality_demo)
        
        return demo_group
    
    def _connect_demo_signals(self):
        """Connect preview system signals for demo feedback."""
        self.preview_system.viewport_changed.connect(self._on_viewport_changed)
        self.preview_system.fps_updated.connect(self._on_fps_updated)
        self.preview_system.quality_changed.connect(self._on_quality_changed)
        self.preview_system.safe_area_changed.connect(self._on_safe_area_changed)
        self.preview_system.performance_warning.connect(self._on_performance_warning)
    
    def _start_demo(self):
        """Start the demo preview system."""
        success = self.preview_system.start_preview()
        if success:
            self.demo_info.setText("✓ Preview system started successfully!\nTry the demo buttons to explore features.")
        else:
            self.demo_info.setText("⚠ Failed to start preview system.")
    
    def _run_zoom_demo(self):
        """Demonstrate zoom controls."""
        self.demo_info.setText("🔍 Zoom Demo Running...\nWatch the zoom controls change automatically!")
        
        # Create a timer for the demo sequence
        self.demo_timer = QTimer()
        self.demo_step = 0
        self.zoom_steps = [0.5, 1.0, 2.0, 4.0, 1.0]  # Zoom sequence
        
        def zoom_step():
            if self.demo_step < len(self.zoom_steps):
                zoom = self.zoom_steps[self.demo_step]
                self.preview_system.set_zoom(zoom)
                self.demo_info.setText(f"🔍 Zoom Demo: Step {self.demo_step + 1}/{len(self.zoom_steps)}\nZoom: {zoom:.1f}x")
                self.demo_step += 1
            else:
                self.demo_timer.stop()
                self.demo_info.setText("✓ Zoom demo completed!\nTry manual zoom controls now.")
        
        self.demo_timer.timeout.connect(zoom_step)
        self.demo_timer.start(1500)  # 1.5 seconds between steps
    
    def _run_pan_demo(self):
        """Demonstrate pan controls."""
        self.demo_info.setText("↔️ Pan Demo Running...\nWatch the pan values change!")
        
        # Set zoom for better pan visibility
        self.preview_system.set_zoom(2.0)
        
        self.demo_timer = QTimer()
        self.demo_step = 0
        self.pan_steps = [
            (0, 0), (100, 0), (100, 100), (0, 100), 
            (-100, 100), (-100, -100), (0, -100), (0, 0)
        ]
        
        def pan_step():
            if self.demo_step < len(self.pan_steps):
                pan_x, pan_y = self.pan_steps[self.demo_step]
                self.preview_system.set_pan(pan_x, pan_y)
                self.demo_info.setText(f"↔️ Pan Demo: Step {self.demo_step + 1}/{len(self.pan_steps)}\nPan: ({pan_x}, {pan_y})")
                self.demo_step += 1
            else:
                self.demo_timer.stop()
                self.preview_system.reset_viewport()
                self.demo_info.setText("✓ Pan demo completed!\nViewport reset to default.")
        
        self.demo_timer.timeout.connect(pan_step)
        self.demo_timer.start(1000)  # 1 second between steps
    
    def _run_safe_area_demo(self):
        """Demonstrate safe area guides."""
        self.demo_info.setText("📺 Safe Area Demo Running...\nCycling through different safe area guides!")
        
        self.demo_timer = QTimer()
        self.demo_step = 0
        self.safe_area_steps = [
            (SafeAreaType.NONE, "No guides"),
            (SafeAreaType.ACTION_SAFE, "Action Safe (90%)"),
            (SafeAreaType.TITLE_SAFE, "Title Safe (80%)"),
            (SafeAreaType.BOTH, "Both guides"),
            (SafeAreaType.NONE, "Back to none")
        ]
        
        def safe_area_step():
            if self.demo_step < len(self.safe_area_steps):
                safe_area_type, description = self.safe_area_steps[self.demo_step]
                self.preview_system.set_safe_area_guides(safe_area_type)
                self.demo_info.setText(f"📺 Safe Area Demo: {description}\nStep {self.demo_step + 1}/{len(self.safe_area_steps)}")
                self.demo_step += 1
            else:
                self.demo_timer.stop()
                self.demo_info.setText("✓ Safe area demo completed!\nSafe areas help ensure TV compatibility.")
        
        self.demo_timer.timeout.connect(safe_area_step)
        self.demo_timer.start(2000)  # 2 seconds between steps
    
    def _run_quality_demo(self):
        """Demonstrate quality presets."""
        self.demo_info.setText("⚙️ Quality Demo Running...\nCycling through quality presets!")
        
        self.demo_timer = QTimer()
        self.demo_step = 0
        self.quality_steps = [
            (QualityPreset.DRAFT, "Draft - 30fps, lower quality"),
            (QualityPreset.NORMAL, "Normal - 60fps, balanced"),
            (QualityPreset.HIGH, "High - 60fps, maximum quality"),
            (QualityPreset.NORMAL, "Back to normal")
        ]
        
        def quality_step():
            if self.demo_step < len(self.quality_steps):
                quality, description = self.quality_steps[self.demo_step]
                self.preview_system.set_quality_preset(quality)
                self.demo_info.setText(f"⚙️ Quality Demo: {description}\nStep {self.demo_step + 1}/{len(self.quality_steps)}")
                self.demo_step += 1
            else:
                self.demo_timer.stop()
                self.demo_info.setText("✓ Quality demo completed!\nQuality adjusts automatically based on performance.")
        
        self.demo_timer.timeout.connect(quality_step)
        self.demo_timer.start(2000)  # 2 seconds between steps
    
    def _on_viewport_changed(self, transform):
        """Handle viewport changes."""
        zoom_percent = int(transform.zoom * 100)
        self.preview_info.setText(
            f"OpenGL Preview Area\n"
            f"Zoom: {zoom_percent}% | Pan: ({transform.pan_x:.0f}, {transform.pan_y:.0f})"
        )
    
    def _on_fps_updated(self, fps):
        """Handle FPS updates."""
        self.performance_info.setText(f"Performance: {fps:.1f} FPS")
    
    def _on_quality_changed(self, quality):
        """Handle quality changes."""
        quality_info = {
            QualityPreset.DRAFT: "Draft (30fps)",
            QualityPreset.NORMAL: "Normal (60fps)",
            QualityPreset.HIGH: "High (60fps+)"
        }
        info = quality_info.get(quality, "Unknown")
        self.performance_info.setText(f"Performance: Quality = {info}")
    
    def _on_safe_area_changed(self, safe_area_type):
        """Handle safe area changes."""
        area_info = {
            SafeAreaType.NONE: "No safe areas",
            SafeAreaType.ACTION_SAFE: "Action safe (90%)",
            SafeAreaType.TITLE_SAFE: "Title safe (80%)",
            SafeAreaType.BOTH: "Both safe areas"
        }
        info = area_info.get(safe_area_type, "Unknown")
        self.preview_info.setText(f"OpenGL Preview Area\nSafe Areas: {info}")
    
    def _on_performance_warning(self, warning):
        """Handle performance warnings."""
        self.performance_info.setText(f"Performance: ⚠ {warning}")
    
    def closeEvent(self, event):
        """Handle application close."""
        if hasattr(self, 'demo_timer'):
            self.demo_timer.stop()
        self.preview_system.stop_preview()
        event.accept()


class MockOpenGLRenderer:
    """Mock OpenGL renderer for demo purposes."""
    
    def __init__(self):
        self.fps_updated = MockSignal()
        self._width = 1920
        self._height = 1080
    
    def width(self):
        return self._width
    
    def height(self):
        return self._height
    
    def makeCurrent(self):
        pass
    
    def paintGL(self):
        pass
    
    def swapBuffers(self):
        pass


class MockSignal:
    """Mock PyQt signal for demo purposes."""
    
    def __init__(self):
        self._connections = []
    
    def connect(self, slot):
        self._connections.append(slot)
    
    def emit(self, *args):
        for slot in self._connections:
            slot(*args)


def main():
    """Run the preview controls demo."""
    print("Preview Controls Demo - Karaoke Subtitle Creator")
    print("=" * 50)
    print()
    print("This demo showcases the new preview control features:")
    print("• Zoom controls (zoom in/out, fit to screen, actual size)")
    print("• Pan controls for detailed editing")
    print("• Quality preset system (draft, normal, high)")
    print("• Safe area guides for TV compatibility")
    print()
    print("Use the controls on the right to interact with the preview,")
    print("or click the demo buttons to see automated demonstrations.")
    print()
    
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show demo window
    demo = PreviewControlsDemo()
    demo.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == '__main__':
    main()