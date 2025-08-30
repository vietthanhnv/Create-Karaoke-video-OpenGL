#!/usr/bin/env python3
"""
Test UI Integration - Karaoke Subtitle Creator

Test script to verify the integration between UI controls and OpenGL preview.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from src.ui.main_window import MainWindow
from src.core.controller import ApplicationController
from src.core.timeline_engine import TimelineEngine
from src.graphics.opengl_renderer import OpenGLRenderer
from src.core.models import VideoAsset, SubtitleTrack, TextElement


def test_ui_integration():
    """Test the UI integration functionality."""
    app = QApplication(sys.argv)
    
    try:
        # Create main window
        main_window = MainWindow()
        
        # Create and initialize controller
        controller = ApplicationController()
        controller.initialize()
        
        # Create mock components for testing
        video_asset = VideoAsset(
            path="test_video.mp4",
            duration=60.0,
            fps=30.0,
            resolution=(1920, 1080),
            codec="h264"
        )
        
        # Create timeline engine with video asset
        timeline_engine = TimelineEngine(video_asset)
        
        # Create a test subtitle track
        test_track = SubtitleTrack(
            id="test_track_1",
            elements=[
                TextElement(
                    content="Hello, World!",
                    font_family="Arial",
                    font_size=24.0,
                    color=(1.0, 1.0, 1.0, 1.0),
                    position=(0.5, 0.8),
                    rotation=(0.0, 0.0, 0.0),
                    effects=[]
                )
            ],
            keyframes=[],
            start_time=0.0,
            end_time=60.0
        )
        
        timeline_engine.add_subtitle_track(test_track)
        
        # Mock the controller methods to return our test components
        controller._timeline_engine = timeline_engine
        
        # Create a mock renderer (since we can't initialize OpenGL in test)
        class MockRenderer:
            def __init__(self):
                self.text_renderer = MockTextRenderer()
            
            def clear_frame(self):
                pass
            
            def render_video_background(self, frame):
                pass
            
            def render_text_element(self, element, properties):
                print(f"Rendering text: {element.content} with properties: {properties}")
            
            def makeCurrent(self):
                pass
            
            def swapBuffers(self):
                pass
        
        class MockTextRenderer:
            def update_properties(self, properties):
                print(f"Text renderer updated with: {properties}")
        
        controller._render_engine = MockRenderer()
        
        # Set controller in main window
        main_window.set_controller(controller)
        
        # Show the window
        main_window.show()
        
        # Test effect parameter changes
        def test_effect_changes():
            print("Testing effect parameter changes...")
            
            # Simulate effect parameter changes
            main_window._on_effect_parameter_changed("visual", "glow_intensity", 75)
            main_window._on_effect_parameter_changed("animation", "fade_type", "in")
            main_window._on_effect_parameter_changed("transform", "rotation_x", 45)
            
            print("Effect parameters updated successfully")
        
        # Test timeline scrubbing
        def test_timeline_scrubbing():
            print("Testing timeline scrubbing...")
            
            # Simulate timeline position changes
            for time in [0.0, 5.0, 10.0, 15.0]:
                main_window._on_timeline_time_changed(time)
                print(f"Timeline position: {time}s")
        
        # Test text formatting changes
        def test_text_formatting():
            print("Testing text formatting changes...")
            
            formatting = {
                'font_family': 'Arial',
                'font_size': 32,
                'font_bold': True,
                'color': (1.0, 0.0, 0.0, 1.0),  # Red
                'alignment': 'center',
                'position_x': 0.5,
                'position_y': 0.7
            }
            
            main_window._on_text_formatting_changed(formatting)
            print("Text formatting updated successfully")
        
        # Test keyboard shortcuts
        def test_keyboard_shortcuts():
            print("Testing keyboard shortcuts...")
            
            # Test playback toggle
            main_window._toggle_playback_shortcut()
            print("Playback toggled")
            
            # Test frame stepping
            main_window._step_frame_forward()
            main_window._step_frame_backward()
            print("Frame stepping tested")
            
            # Test keyframe operations
            main_window._add_keyframe_shortcut()
            print("Keyframe added")
        
        # Schedule tests to run after window is shown
        QTimer.singleShot(100, test_effect_changes)
        QTimer.singleShot(200, test_timeline_scrubbing)
        QTimer.singleShot(300, test_text_formatting)
        QTimer.singleShot(400, test_keyboard_shortcuts)
        
        # Close after tests
        QTimer.singleShot(1000, main_window.close)
        
        # Run the application
        return app.exec()
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(test_ui_integration())