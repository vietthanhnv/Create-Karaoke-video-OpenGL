"""
Shader management system for OpenGL rendering.

This module provides utilities for loading, compiling, and managing
GLSL shader programs with error handling and uniform management.
"""

import logging
from typing import Dict, Any, Optional, Union, Tuple
from pathlib import Path

import numpy as np
import OpenGL.GL as gl
from OpenGL.GL import shaders


logger = logging.getLogger(__name__)


class ShaderProgram:
    """Wrapper class for OpenGL shader programs with uniform management."""
    
    def __init__(self, program_id: int, name: str):
        self.program_id = program_id
        self.name = name
        self._uniform_locations: Dict[str, int] = {}
        
    def use(self) -> None:
        """Activate this shader program."""
        gl.glUseProgram(self.program_id)
        
    def get_uniform_location(self, name: str) -> int:
        """Get uniform location, caching for performance."""
        if name not in self._uniform_locations:
            location = gl.glGetUniformLocation(self.program_id, name)
            if location == -1:
                logger.warning(f"Uniform '{name}' not found in shader '{self.name}'")
            self._uniform_locations[name] = location
        return self._uniform_locations[name]
        
    def set_uniform(self, name: str, value: Any) -> None:
        """Set uniform value with automatic type detection."""
        location = self.get_uniform_location(name)
        if location == -1:
            return
            
        # Determine uniform type and set value
        if isinstance(value, bool):
            gl.glUniform1i(location, int(value))
        elif isinstance(value, int):
            gl.glUniform1i(location, value)
        elif isinstance(value, float):
            gl.glUniform1f(location, value)
        elif isinstance(value, (list, tuple, np.ndarray)):
            self._set_vector_uniform(location, value)
        else:
            logger.error(f"Unsupported uniform type: {type(value)}")
            
    def _set_vector_uniform(self, location: int, value: Union[list, tuple, np.ndarray]) -> None:
        """Set vector or matrix uniform values."""
        if isinstance(value, np.ndarray):
            value = value.flatten()
        
        length = len(value)
        
        if length == 2:
            gl.glUniform2f(location, *value)
        elif length == 3:
            gl.glUniform3f(location, *value)
        elif length == 4:
            gl.glUniform4f(location, *value)
        elif length == 9:
            # 3x3 matrix
            gl.glUniformMatrix3fv(location, 1, gl.GL_FALSE, value)
        elif length == 16:
            # 4x4 matrix
            gl.glUniformMatrix4fv(location, 1, gl.GL_FALSE, value)
        else:
            logger.error(f"Unsupported vector/matrix size: {length}")
            
    def bind_texture(self, texture_id: int, unit: int, uniform_name: str) -> None:
        """Bind texture to specified unit and set uniform."""
        gl.glActiveTexture(gl.GL_TEXTURE0 + unit)
        gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)
        self.set_uniform(uniform_name, unit)
        
    def bind_multiple_textures(self, textures: Dict[str, Tuple[int, int]]) -> None:
        """Bind multiple textures at once. Format: {uniform_name: (texture_id, unit)}"""
        for uniform_name, (texture_id, unit) in textures.items():
            self.bind_texture(texture_id, unit, uniform_name)
            
    def set_matrix_uniform(self, name: str, matrix: np.ndarray, transpose: bool = False) -> None:
        """Set matrix uniform with explicit transpose control."""
        location = self.get_uniform_location(name)
        if location == -1:
            return
            
        matrix_flat = matrix.flatten().astype(np.float32)
        
        if matrix.shape == (3, 3) or len(matrix_flat) == 9:
            gl.glUniformMatrix3fv(location, 1, transpose, matrix_flat)
        elif matrix.shape == (4, 4) or len(matrix_flat) == 16:
            gl.glUniformMatrix4fv(location, 1, transpose, matrix_flat)
        else:
            logger.error(f"Unsupported matrix size for uniform '{name}': {matrix.shape}")
            
    def set_effect_parameters(self, params: Dict[str, Any]) -> None:
        """Set multiple effect parameters at once."""
        for name, value in params.items():
            self.set_uniform(name, value)
        
    def cleanup(self) -> None:
        """Clean up shader program resources."""
        if self.program_id:
            gl.glDeleteProgram(self.program_id)
            self.program_id = 0


class ShaderManager:
    """
    Manages loading, compilation, and caching of shader programs.
    
    Provides a centralized system for shader management with automatic
    reloading, error handling, and performance optimization.
    """
    
    def __init__(self, shader_root: str = "shaders"):
        self.shader_root = Path(shader_root)
        self._programs: Dict[str, ShaderProgram] = {}
        self._shader_sources: Dict[str, str] = {}
        self._texture_units: Dict[str, int] = {}
        self._next_texture_unit = 0
        
    def load_shader_program(self, name: str, vertex_file: str, fragment_file: str) -> Optional[ShaderProgram]:
        """
        Load and compile a shader program from files.
        
        Args:
            name: Unique name for the shader program
            vertex_file: Path to vertex shader file (relative to shader_root/vertex/)
            fragment_file: Path to fragment shader file (relative to shader_root/fragment/)
            
        Returns:
            ShaderProgram instance or None if compilation failed
        """
        try:
            # Load shader source code
            vertex_source = self._load_shader_source("vertex", vertex_file)
            fragment_source = self._load_shader_source("fragment", fragment_file)
            
            if not vertex_source or not fragment_source:
                return None
                
            # Compile and link program
            program_id = self._compile_program(vertex_source, fragment_source)
            if program_id == 0:
                return None
                
            # Create shader program wrapper
            program = ShaderProgram(program_id, name)
            self._programs[name] = program
            
            logger.info(f"Loaded shader program: {name}")
            return program
            
        except Exception as e:
            logger.error(f"Failed to load shader program '{name}': {e}")
            return None
            
    def load_shader_from_source(self, name: str, vertex_source: str, fragment_source: str) -> Optional[ShaderProgram]:
        """
        Load and compile a shader program from source strings.
        
        Args:
            name: Unique name for the shader program
            vertex_source: Vertex shader source code
            fragment_source: Fragment shader source code
            
        Returns:
            ShaderProgram instance or None if compilation failed
        """
        try:
            program_id = self._compile_program(vertex_source, fragment_source)
            if program_id == 0:
                return None
                
            program = ShaderProgram(program_id, name)
            self._programs[name] = program
            
            logger.info(f"Loaded shader program from source: {name}")
            return program
            
        except Exception as e:
            logger.error(f"Failed to load shader program '{name}' from source: {e}")
            return None
            
    def get_program(self, name: str) -> Optional[ShaderProgram]:
        """Get a loaded shader program by name."""
        return self._programs.get(name)
        
    def reload_program(self, name: str) -> bool:
        """Reload a shader program from disk."""
        if name not in self._programs:
            logger.error(f"Shader program '{name}' not found for reload")
            return False
            
        # TODO: Store original file paths for reloading
        logger.warning(f"Shader reloading not yet implemented for '{name}'")
        return False
        
    def _load_shader_source(self, shader_type: str, filename: str) -> Optional[str]:
        """Load shader source code from file."""
        shader_path = self.shader_root / shader_type / filename
        
        if not shader_path.exists():
            logger.error(f"Shader file not found: {shader_path}")
            return None
            
        try:
            source = shader_path.read_text(encoding='utf-8')
            self._shader_sources[str(shader_path)] = source
            return source
        except Exception as e:
            logger.error(f"Failed to read shader file {shader_path}: {e}")
            return None
            
    def _compile_program(self, vertex_source: str, fragment_source: str) -> int:
        """Compile and link a shader program."""
        try:
            # Compile vertex shader
            vertex_shader = self._compile_shader(vertex_source, gl.GL_VERTEX_SHADER)
            if vertex_shader == 0:
                return 0
                
            # Compile fragment shader
            fragment_shader = self._compile_shader(fragment_source, gl.GL_FRAGMENT_SHADER)
            if fragment_shader == 0:
                gl.glDeleteShader(vertex_shader)
                return 0
                
            # Create and link program
            program = gl.glCreateProgram()
            gl.glAttachShader(program, vertex_shader)
            gl.glAttachShader(program, fragment_shader)
            gl.glLinkProgram(program)
            
            # Check linking status
            link_status = gl.glGetProgramiv(program, gl.GL_LINK_STATUS)
            if not link_status:
                error_log = gl.glGetProgramInfoLog(program).decode('utf-8')
                logger.error(f"Shader program linking failed: {error_log}")
                gl.glDeleteProgram(program)
                program = 0
                
            # Clean up individual shaders
            gl.glDeleteShader(vertex_shader)
            gl.glDeleteShader(fragment_shader)
            
            return program
            
        except Exception as e:
            logger.error(f"Shader program compilation failed: {e}")
            return 0
            
    def _compile_shader(self, source: str, shader_type: int) -> int:
        """Compile an individual shader."""
        try:
            shader = gl.glCreateShader(shader_type)
            gl.glShaderSource(shader, source)
            gl.glCompileShader(shader)
            
            # Check compilation status
            compile_status = gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS)
            if not compile_status:
                error_log = gl.glGetShaderInfoLog(shader).decode('utf-8')
                shader_type_name = "vertex" if shader_type == gl.GL_VERTEX_SHADER else "fragment"
                logger.error(f"{shader_type_name.capitalize()} shader compilation failed: {error_log}")
                gl.glDeleteShader(shader)
                return 0
                
            return shader
            
        except Exception as e:
            logger.error(f"Shader compilation error: {e}")
            return 0
            
    def cleanup(self) -> None:
        """Clean up all shader programs."""
        for program in self._programs.values():
            program.cleanup()
        self._programs.clear()
        self._shader_sources.clear()
        logger.info("Shader manager cleaned up")
        
    def get_loaded_programs(self) -> Dict[str, ShaderProgram]:
        """Get all loaded shader programs."""
        return self._programs.copy()
        
    def validate_program(self, name: str) -> bool:
        """Validate that a shader program is properly loaded and functional."""
        program = self.get_program(name)
        if not program:
            return False
            
        try:
            # Check if program ID is valid
            if not gl.glIsProgram(program.program_id):
                return False
                
            # Validate program
            gl.glValidateProgram(program.program_id)
            validate_status = gl.glGetProgramiv(program.program_id, gl.GL_VALIDATE_STATUS)
            
            if not validate_status:
                error_log = gl.glGetProgramInfoLog(program.program_id).decode('utf-8')
                logger.warning(f"Shader program '{name}' validation failed: {error_log}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating shader program '{name}': {e}")
            return False
            
    def load_base_shader_programs(self) -> bool:
        """Load all base shader programs for text rendering and effects."""
        base_programs = [
            ("text", "text_vertex.glsl", "text_fragment.glsl"),
            ("quad", "quad_vertex.glsl", "quad_fragment.glsl"),
            ("glow", "glow_vertex.glsl", "glow_fragment.glsl"),
            ("outline", "outline_vertex.glsl", "outline_fragment.glsl"),
            ("shadow", "shadow_vertex.glsl", "shadow_fragment.glsl"),
            ("gradient", "gradient_vertex.glsl", "gradient_fragment.glsl"),
            ("transform3d", "transform3d_vertex.glsl", "transform3d_fragment.glsl"),
            ("particle", "particle_vertex.glsl", "particle_fragment.glsl"),
            ("color_animation", "color_animation_vertex.glsl", "color_animation_fragment.glsl")
        ]
        
        success_count = 0
        for name, vertex_file, fragment_file in base_programs:
            program = self.load_shader_program(name, vertex_file, fragment_file)
            if program:
                success_count += 1
            else:
                logger.error(f"Failed to load base shader program: {name}")
                
        logger.info(f"Loaded {success_count}/{len(base_programs)} base shader programs")
        return success_count == len(base_programs)
        
    def allocate_texture_unit(self, name: str) -> int:
        """Allocate a texture unit for a named texture."""
        if name in self._texture_units:
            return self._texture_units[name]
            
        unit = self._next_texture_unit
        self._texture_units[name] = unit
        self._next_texture_unit += 1
        
        logger.debug(f"Allocated texture unit {unit} for '{name}'")
        return unit
        
    def get_texture_unit(self, name: str) -> Optional[int]:
        """Get the texture unit for a named texture."""
        return self._texture_units.get(name)
        
    def bind_texture_by_name(self, program_name: str, texture_id: int, texture_name: str, uniform_name: str) -> bool:
        """Bind a texture by name to a shader program."""
        program = self.get_program(program_name)
        if not program:
            logger.error(f"Shader program '{program_name}' not found")
            return False
            
        unit = self.allocate_texture_unit(texture_name)
        program.bind_texture(texture_id, unit, uniform_name)
        return True
        
    def set_effect_uniforms(self, program_name: str, effect_params: Dict[str, Any]) -> bool:
        """Set multiple uniforms for effect parameters."""
        program = self.get_program(program_name)
        if not program:
            logger.error(f"Shader program '{program_name}' not found")
            return False
            
        program.use()
        
        try:
            for param_name, value in effect_params.items():
                program.set_uniform(param_name, value)
            return True
        except Exception as e:
            logger.error(f"Failed to set effect uniforms for '{program_name}': {e}")
            return False
            
    def create_effect_variant(self, base_name: str, variant_name: str, defines: Dict[str, str]) -> Optional[ShaderProgram]:
        """Create a shader variant with preprocessor defines."""
        # Load base shader sources
        vertex_source = self._load_shader_source("vertex", f"{base_name}_vertex.glsl")
        fragment_source = self._load_shader_source("fragment", f"{base_name}_fragment.glsl")
        
        if not vertex_source or not fragment_source:
            return None
            
        # Add defines to shader sources
        define_string = "\n".join([f"#define {key} {value}" for key, value in defines.items()])
        
        vertex_with_defines = f"#version 330 core\n{define_string}\n" + vertex_source.split('\n', 1)[1]
        fragment_with_defines = f"#version 330 core\n{define_string}\n" + fragment_source.split('\n', 1)[1]
        
        return self.load_shader_from_source(variant_name, vertex_with_defines, fragment_with_defines)