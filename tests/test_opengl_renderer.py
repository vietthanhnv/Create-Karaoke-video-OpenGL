"""
Tests for OpenGL renderer functionality.

These tests verify the OpenGL context initialization, shader loading,
and basic rendering pipeline setup.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

from src.graphics.opengl_renderer import OpenGLRenderer
from src.graphics.shader_manager import ShaderManager, ShaderProgram


class TestOpenGLRenderer:
    """Test cases for OpenGL renderer."""
    
    @pytest.fixture(autouse=True)
    def setup_qt_app(self):
        """Ensure QApplication exists for widget tests."""
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()
        yield
        # Don't quit the app as it might be used by other tests
        
    def test_renderer_initialization(self):
        """Test that renderer can be created without errors."""
        renderer = OpenGLRenderer()
        assert renderer is not None
        assert renderer._viewport_size == (1920, 1080)
        assert renderer._clear_color == (0.0, 0.0, 0.0, 1.0)
        
    def test_surface_format_configuration(self):
        """Test that OpenGL surface format is configured correctly."""
        renderer = OpenGLRenderer()
        format = renderer.format()
        
        # Check OpenGL version requirement
        assert format.majorVersion() >= 3
        if format.majorVersion() == 3:
            assert format.minorVersion() >= 3
            
    @patch('OpenGL.GL.glGetString')
    @patch('OpenGL.GL.glGetProgramiv')
    @patch('OpenGL.GL.glCreateProgram')
    def test_opengl_version_validation(self, mock_create_program, mock_get_program_iv, mock_gl_get_string):
        """Test OpenGL version validation."""
        # Mock OpenGL version string
        mock_gl_get_string.return_value = b"4.6.0 NVIDIA 470.57.02"
        
        renderer = OpenGLRenderer()
        
        # Simulate initializeGL call
        with patch.object(renderer, '_configure_opengl_state'), \
             patch.object(renderer, '_load_basic_shaders'), \
             patch.object(renderer, '_create_basic_geometry'):
            renderer.initializeGL()
            
        assert renderer._opengl_version == (4, 6)
        
    @patch('OpenGL.GL.glGetString')
    def test_insufficient_opengl_version(self, mock_gl_get_string):
        """Test handling of insufficient OpenGL version."""
        # Mock insufficient OpenGL version
        mock_gl_get_string.return_value = b"3.0.0"
        
        renderer = OpenGLRenderer()
        
        # Connect to error signal
        error_messages = []
        renderer.render_error.connect(lambda msg: error_messages.append(msg))
        
        with patch.object(renderer, '_configure_opengl_state'), \
             patch.object(renderer, '_load_basic_shaders'), \
             patch.object(renderer, '_create_basic_geometry'):
            renderer.initializeGL()
            
        assert len(error_messages) > 0
        assert "OpenGL 3.3+ required" in error_messages[0]
        
    def test_fps_monitoring(self):
        """Test FPS monitoring functionality."""
        renderer = OpenGLRenderer()
        
        # Connect to FPS signal
        fps_values = []
        renderer.fps_updated.connect(lambda fps: fps_values.append(fps))
        
        # Simulate some frames
        renderer._frame_count = 60
        renderer._update_fps()
        
        assert len(fps_values) == 1
        assert fps_values[0] == 60
        assert renderer._frame_count == 0  # Should reset after update
        
    def test_viewport_resize(self):
        """Test viewport resize handling."""
        renderer = OpenGLRenderer()
        
        # Mock OpenGL viewport call
        with patch('OpenGL.GL.glViewport') as mock_viewport:
            renderer.resizeGL(1280, 720)
            
            assert renderer._viewport_size == (1280, 720)
            mock_viewport.assert_called_once_with(0, 0, 1280, 720)
            
    def test_opengl_info_retrieval(self):
        """Test OpenGL information retrieval."""
        renderer = OpenGLRenderer()
        renderer._opengl_version = (4, 6)
        renderer._shader_programs = {"test": 123}
        
        with patch('OpenGL.GL.glGetString') as mock_get_string:
            mock_get_string.side_effect = lambda param: {
                0x1F00: b"Test Vendor",  # GL_VENDOR
                0x1F01: b"Test Renderer"  # GL_RENDERER
            }.get(param, b"Unknown")
            
            info = renderer.get_opengl_info()
            
            assert info["version"] == (4, 6)
            assert info["viewport_size"] == (1920, 1080)
            assert "test" in info["shader_programs"]
            
    def test_cleanup(self):
        """Test resource cleanup."""
        renderer = OpenGLRenderer()
        renderer._shader_programs = {"test": 123}
        renderer._vertex_arrays = {"quad": 456}
        renderer._textures = {"test_tex": 789}
        
        with patch('OpenGL.GL.glDeleteProgram') as mock_delete_program, \
             patch('OpenGL.GL.glDeleteVertexArrays') as mock_delete_vao, \
             patch('OpenGL.GL.glDeleteTextures') as mock_delete_tex:
            
            renderer.cleanup()
            
            mock_delete_program.assert_called_once_with(123)
            mock_delete_vao.assert_called_once_with(1, [456])
            mock_delete_tex.assert_called_once_with(1, [789])
            
            assert len(renderer._shader_programs) == 0
            assert len(renderer._vertex_arrays) == 0
            assert len(renderer._textures) == 0


class TestShaderManager:
    """Test cases for shader manager."""
    
    def test_shader_manager_initialization(self):
        """Test shader manager initialization."""
        manager = ShaderManager("test_shaders")
        assert manager.shader_root.name == "test_shaders"
        assert len(manager._programs) == 0
        
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_load_shader_source(self, mock_read_text, mock_exists):
        """Test shader source loading."""
        mock_exists.return_value = True
        mock_read_text.return_value = "#version 330 core\nvoid main() {}"
        
        manager = ShaderManager()
        source = manager._load_shader_source("vertex", "test.glsl")
        
        assert source is not None
        assert "#version 330 core" in source
        
    @patch('pathlib.Path.exists')
    def test_load_nonexistent_shader(self, mock_exists):
        """Test handling of nonexistent shader files."""
        mock_exists.return_value = False
        
        manager = ShaderManager()
        source = manager._load_shader_source("vertex", "nonexistent.glsl")
        
        assert source is None
        
    def test_shader_program_uniform_management(self):
        """Test shader program uniform management."""
        program = ShaderProgram(123, "test_program")
        
        with patch('OpenGL.GL.glGetUniformLocation') as mock_get_location:
            mock_get_location.return_value = 5
            
            location = program.get_uniform_location("test_uniform")
            assert location == 5
            
            # Test caching
            location2 = program.get_uniform_location("test_uniform")
            assert location2 == 5
            assert mock_get_location.call_count == 1  # Should be cached
            
    def test_shader_program_uniform_setting(self):
        """Test setting different types of uniforms."""
        program = ShaderProgram(123, "test_program")
        
        with patch('OpenGL.GL.glGetUniformLocation', return_value=0), \
             patch('OpenGL.GL.glUniform1i') as mock_uniform1i, \
             patch('OpenGL.GL.glUniform1f') as mock_uniform1f, \
             patch('OpenGL.GL.glUniform3f') as mock_uniform3f:
            
            # Test integer uniform
            program.set_uniform("int_uniform", 42)
            mock_uniform1i.assert_called_with(0, 42)
            
            # Test float uniform
            program.set_uniform("float_uniform", 3.14)
            mock_uniform1f.assert_called_with(0, 3.14)
            
            # Test vector uniform
            program.set_uniform("vec3_uniform", [1.0, 2.0, 3.0])
            mock_uniform3f.assert_called_with(0, 1.0, 2.0, 3.0)
            
    def test_shader_program_texture_binding(self):
        """Test texture binding functionality."""
        program = ShaderProgram(123, "test_program")
        
        with patch('OpenGL.GL.glActiveTexture') as mock_active_texture, \
             patch('OpenGL.GL.glBindTexture') as mock_bind_texture, \
             patch.object(program, 'set_uniform') as mock_set_uniform:
            
            program.bind_texture(456, 2, "texture_uniform")
            
            mock_active_texture.assert_called_once()
            mock_bind_texture.assert_called_once()
            mock_set_uniform.assert_called_once_with("texture_uniform", 2)
            
    def test_shader_manager_cleanup(self):
        """Test shader manager cleanup."""
        manager = ShaderManager()
        
        # Create mock programs
        mock_program1 = Mock()
        mock_program2 = Mock()
        manager._programs = {"prog1": mock_program1, "prog2": mock_program2}
        
        manager.cleanup()
        
        mock_program1.cleanup.assert_called_once()
        mock_program2.cleanup.assert_called_once()
        assert len(manager._programs) == 0


if __name__ == "__main__":
    pytest.main([__file__])