#!/usr/bin/env python3
"""
Demo script for OpenGL renderer functionality.

This script creates a simple Qt application with the OpenGL renderer
to test context initialization and basic rendering capabilities.
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import QTimer

from src.graphics.opengl_renderer import OpenGLRenderer
from src.graphics.shader_manager import ShaderManager


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OpenGLDemo(QMainWindow):
    """Demo window for OpenGL renderer testing."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Karaoke Subtitle Creator - OpenGL Renderer Demo")
        self.setGeometry(100, 100, 1280, 720)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create info label
        self.info_label = QLabel("Initializing OpenGL renderer...")
        layout.addWidget(self.info_label)
        
        # Create OpenGL renderer widget
        self.renderer = OpenGLRenderer()
        layout.addWidget(self.renderer)
        
        # Connect signals
        self.renderer.render_error.connect(self.on_render_error)
        self.renderer.fps_updated.connect(self.on_fps_updated)
        
        # Timer to update info
        self.info_timer = QTimer()
        self.info_timer.timeout.connect(self.update_info)
        self.info_timer.start(2000)  # Update every 2 seconds
        
    def on_render_error(self, error_message: str):
        """Handle rendering errors."""
        logger.error(f"Render error: {error_message}")
        self.info_label.setText(f"Render Error: {error_message}")
        self.info_label.setStyleSheet("color: red;")
        
    def on_fps_updated(self, fps: float):
        """Handle FPS updates."""
        logger.info(f"FPS: {fps}")
        
    def update_info(self):
        """Update information display."""
        try:
            opengl_info = self.renderer.get_opengl_info()
            if opengl_info:
                version = opengl_info.get("version", "Unknown")
                renderer_name = opengl_info.get("renderer", "Unknown")
                viewport = opengl_info.get("viewport_size", (0, 0))
                shaders = opengl_info.get("shader_programs", [])
                
                info_text = f"""OpenGL Renderer Status:
Version: {version[0]}.{version[1]} 
GPU: {renderer_name}
Viewport: {viewport[0]}x{viewport[1]}
Loaded Shaders: {len(shaders)}
Shader Programs: {', '.join(shaders) if shaders else 'None'}"""
                
                self.info_label.setText(info_text)
                self.info_label.setStyleSheet("color: green;")
            else:
                self.info_label.setText("OpenGL context not yet initialized")
                self.info_label.setStyleSheet("color: orange;")
                
        except Exception as e:
            logger.error(f"Error updating info: {e}")
            self.info_label.setText(f"Info update error: {e}")
            self.info_label.setStyleSheet("color: red;")


def test_shader_manager():
    """Test shader manager functionality."""
    logger.info("Testing shader manager...")
    
    manager = ShaderManager()
    
    # Test loading existing shaders
    text_program = manager.load_shader_program("text", "text_vertex.glsl", "text_fragment.glsl")
    if text_program:
        logger.info("Successfully loaded text shader program")
    else:
        logger.warning("Failed to load text shader program")
        
    quad_program = manager.load_shader_program("quad", "quad_vertex.glsl", "quad_fragment.glsl")
    if quad_program:
        logger.info("Successfully loaded quad shader program")
    else:
        logger.warning("Failed to load quad shader program")
        
    # Test loading from source
    simple_vertex = """
    #version 330 core
    layout (location = 0) in vec3 position;
    void main() {
        gl_Position = vec4(position, 1.0);
    }
    """
    
    simple_fragment = """
    #version 330 core
    out vec4 FragColor;
    void main() {
        FragColor = vec4(1.0, 0.0, 0.0, 1.0);
    }
    """
    
    simple_program = manager.load_shader_from_source("simple", simple_vertex, simple_fragment)
    if simple_program:
        logger.info("Successfully loaded simple shader from source")
    else:
        logger.warning("Failed to load simple shader from source")
        
    # Get loaded programs
    programs = manager.get_loaded_programs()
    logger.info(f"Total loaded programs: {len(programs)}")
    
    return manager


def main():
    """Main demo function."""
    logger.info("Starting OpenGL renderer demo...")
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Test shader manager (without OpenGL context)
    shader_manager = test_shader_manager()
    
    # Create and show demo window
    demo = OpenGLDemo()
    demo.show()
    
    logger.info("Demo window created. OpenGL context will be initialized when widget is shown.")
    logger.info("Close the window to exit the demo.")
    
    # Run application
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    finally:
        # Cleanup
        demo.renderer.cleanup()
        shader_manager.cleanup()
        logger.info("Demo cleanup completed")


if __name__ == "__main__":
    main()