"""
Tests for the GLSL shader framework.

This module tests shader compilation, uniform management, and texture binding
functionality of the ShaderManager and ShaderProgram classes.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from pathlib import Path

from src.graphics.shader_manager import ShaderManager, ShaderProgram


class TestShaderProgram(unittest.TestCase):
    """Test ShaderProgram functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.program = ShaderProgram(123, "test_program")
        
    @patch('src.graphics.shader_manager.gl')
    def test_use_program(self, mock_gl):
        """Test shader program activation."""
        self.program.use()
        mock_gl.glUseProgram.assert_called_once_with(123)
        
    @patch('src.graphics.shader_manager.gl')
    def test_get_uniform_location_cached(self, mock_gl):
        """Test uniform location caching."""
        mock_gl.glGetUniformLocation.return_value = 5
        
        # First call should query OpenGL
        location1 = self.program.get_uniform_location("test_uniform")
        self.assertEqual(location1, 5)
        mock_gl.glGetUniformLocation.assert_called_once_with(123, "test_uniform")
        
        # Second call should use cache
        mock_gl.glGetUniformLocation.reset_mock()
        location2 = self.program.get_uniform_location("test_uniform")
        self.assertEqual(location2, 5)
        mock_gl.glGetUniformLocation.assert_not_called()
        
    @patch('src.graphics.shader_manager.gl')
    def test_set_uniform_types(self, mock_gl):
        """Test setting different uniform types."""
        mock_gl.glGetUniformLocation.return_value = 0
        
        # Test boolean
        self.program.set_uniform("bool_uniform", True)
        mock_gl.glUniform1i.assert_called_with(0, 1)
        
        # Test integer
        self.program.set_uniform("int_uniform", 42)
        mock_gl.glUniform1i.assert_called_with(0, 42)
        
        # Test float
        self.program.set_uniform("float_uniform", 3.14)
        mock_gl.glUniform1f.assert_called_with(0, 3.14)
        
    @patch('src.graphics.shader_manager.gl')
    def test_set_vector_uniforms(self, mock_gl):
        """Test setting vector uniforms."""
        mock_gl.glGetUniformLocation.return_value = 0
        
        # Test vec2
        self.program.set_uniform("vec2_uniform", [1.0, 2.0])
        mock_gl.glUniform2f.assert_called_with(0, 1.0, 2.0)
        
        # Test vec3
        self.program.set_uniform("vec3_uniform", [1.0, 2.0, 3.0])
        mock_gl.glUniform3f.assert_called_with(0, 1.0, 2.0, 3.0)
        
        # Test vec4
        self.program.set_uniform("vec4_uniform", [1.0, 2.0, 3.0, 4.0])
        mock_gl.glUniform4f.assert_called_with(0, 1.0, 2.0, 3.0, 4.0)
        
    @patch('src.graphics.shader_manager.gl')
    def test_set_matrix_uniforms(self, mock_gl):
        """Test setting matrix uniforms."""
        mock_gl.glGetUniformLocation.return_value = 0
        
        # Test 3x3 matrix
        matrix3 = np.eye(3, dtype=np.float32)
        self.program.set_matrix_uniform("mat3_uniform", matrix3)
        mock_gl.glUniformMatrix3fv.assert_called_once()
        
        # Test 4x4 matrix
        matrix4 = np.eye(4, dtype=np.float32)
        self.program.set_matrix_uniform("mat4_uniform", matrix4)
        mock_gl.glUniformMatrix4fv.assert_called_once()
        
    @patch('src.graphics.shader_manager.gl')
    def test_bind_texture(self, mock_gl):
        """Test texture binding."""
        mock_gl.glGetUniformLocation.return_value = 0
        
        self.program.bind_texture(456, 2, "texture_uniform")
        
        mock_gl.glActiveTexture.assert_called_with(mock_gl.GL_TEXTURE0 + 2)
        mock_gl.glBindTexture.assert_called_with(mock_gl.GL_TEXTURE_2D, 456)
        mock_gl.glUniform1i.assert_called_with(0, 2)
        
    @patch('src.graphics.shader_manager.gl')
    def test_bind_multiple_textures(self, mock_gl):
        """Test binding multiple textures."""
        mock_gl.glGetUniformLocation.return_value = 0
        
        textures = {
            "texture1": (100, 0),
            "texture2": (200, 1)
        }
        
        self.program.bind_multiple_textures(textures)
        
        self.assertEqual(mock_gl.glActiveTexture.call_count, 2)
        self.assertEqual(mock_gl.glBindTexture.call_count, 2)
        
    @patch('src.graphics.shader_manager.gl')
    def test_cleanup(self, mock_gl):
        """Test shader program cleanup."""
        self.program.cleanup()
        mock_gl.glDeleteProgram.assert_called_once_with(123)
        self.assertEqual(self.program.program_id, 0)


class TestShaderManager(unittest.TestCase):
    """Test ShaderManager functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.shader_manager = ShaderManager("test_shaders")
        
    @patch('src.graphics.shader_manager.Path')
    def test_initialization(self, mock_path):
        """Test shader manager initialization."""
        manager = ShaderManager("custom_path")
        mock_path.assert_called_with("custom_path")
        
    @patch('src.graphics.shader_manager.gl')
    @patch.object(ShaderManager, '_load_shader_source')
    @patch.object(ShaderManager, '_compile_program')
    def test_load_shader_program_success(self, mock_compile, mock_load_source, mock_gl):
        """Test successful shader program loading."""
        mock_load_source.side_effect = ["vertex_source", "fragment_source"]
        mock_compile.return_value = 789
        
        program = self.shader_manager.load_shader_program("test", "vertex.glsl", "fragment.glsl")
        
        self.assertIsNotNone(program)
        self.assertEqual(program.program_id, 789)
        self.assertEqual(program.name, "test")
        
    @patch('src.graphics.shader_manager.gl')
    @patch.object(ShaderManager, '_load_shader_source')
    def test_load_shader_program_failure(self, mock_load_source, mock_gl):
        """Test shader program loading failure."""
        mock_load_source.side_effect = [None, "fragment_source"]
        
        program = self.shader_manager.load_shader_program("test", "vertex.glsl", "fragment.glsl")
        
        self.assertIsNone(program)
        
    @patch('src.graphics.shader_manager.gl')
    @patch.object(ShaderManager, '_compile_program')
    def test_load_shader_from_source(self, mock_compile, mock_gl):
        """Test loading shader from source strings."""
        mock_compile.return_value = 456
        
        program = self.shader_manager.load_shader_from_source(
            "test", "vertex_source", "fragment_source"
        )
        
        self.assertIsNotNone(program)
        self.assertEqual(program.program_id, 456)
        
    def test_get_program(self):
        """Test getting loaded programs."""
        # Add a mock program
        mock_program = Mock()
        self.shader_manager._programs["test"] = mock_program
        
        result = self.shader_manager.get_program("test")
        self.assertEqual(result, mock_program)
        
        # Test non-existent program
        result = self.shader_manager.get_program("nonexistent")
        self.assertIsNone(result)
        
    def test_texture_unit_allocation(self):
        """Test texture unit allocation."""
        # First allocation
        unit1 = self.shader_manager.allocate_texture_unit("texture1")
        self.assertEqual(unit1, 0)
        
        # Second allocation
        unit2 = self.shader_manager.allocate_texture_unit("texture2")
        self.assertEqual(unit2, 1)
        
        # Same texture should return same unit
        unit1_again = self.shader_manager.allocate_texture_unit("texture1")
        self.assertEqual(unit1_again, 0)
        
    def test_get_texture_unit(self):
        """Test getting texture units."""
        self.shader_manager.allocate_texture_unit("test_texture")
        
        unit = self.shader_manager.get_texture_unit("test_texture")
        self.assertEqual(unit, 0)
        
        # Non-existent texture
        unit = self.shader_manager.get_texture_unit("nonexistent")
        self.assertIsNone(unit)
        
    @patch.object(ShaderManager, 'get_program')
    def test_bind_texture_by_name(self, mock_get_program):
        """Test binding texture by name."""
        mock_program = Mock()
        mock_get_program.return_value = mock_program
        
        result = self.shader_manager.bind_texture_by_name(
            "test_program", 123, "test_texture", "uniform_name"
        )
        
        self.assertTrue(result)
        mock_program.bind_texture.assert_called_once()
        
    @patch.object(ShaderManager, 'get_program')
    def test_set_effect_uniforms(self, mock_get_program):
        """Test setting effect uniforms."""
        mock_program = Mock()
        mock_get_program.return_value = mock_program
        
        params = {
            "intensity": 1.0,
            "color": [1.0, 0.0, 0.0, 1.0]
        }
        
        result = self.shader_manager.set_effect_uniforms("test_program", params)
        
        self.assertTrue(result)
        mock_program.use.assert_called_once()
        self.assertEqual(mock_program.set_uniform.call_count, 2)
        
    @patch.object(ShaderManager, 'load_shader_program')
    def test_load_base_shader_programs(self, mock_load_program):
        """Test loading all base shader programs."""
        mock_load_program.return_value = Mock()
        
        result = self.shader_manager.load_base_shader_programs()
        
        self.assertTrue(result)
        # Should load 9 base programs
        self.assertEqual(mock_load_program.call_count, 9)
        
    @patch('src.graphics.shader_manager.gl')
    def test_validate_program(self, mock_gl):
        """Test shader program validation."""
        mock_program = Mock()
        mock_program.program_id = 123
        self.shader_manager._programs["test"] = mock_program
        
        mock_gl.glIsProgram.return_value = True
        mock_gl.glGetProgramiv.return_value = True
        
        result = self.shader_manager.validate_program("test")
        self.assertTrue(result)
        
        mock_gl.glValidateProgram.assert_called_once_with(123)
        
    def test_cleanup(self):
        """Test shader manager cleanup."""
        mock_program1 = Mock()
        mock_program2 = Mock()
        self.shader_manager._programs = {
            "program1": mock_program1,
            "program2": mock_program2
        }
        
        self.shader_manager.cleanup()
        
        mock_program1.cleanup.assert_called_once()
        mock_program2.cleanup.assert_called_once()
        self.assertEqual(len(self.shader_manager._programs), 0)


if __name__ == '__main__':
    unittest.main()