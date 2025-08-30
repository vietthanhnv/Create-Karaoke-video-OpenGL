"""
OpenGL renderer implementation for karaoke subtitle creator.

This module provides the core OpenGL rendering functionality including
context initialization, shader management, and basic rendering pipeline.
"""

import logging
from typing import Optional, Tuple, Dict, Any
from pathlib import Path

import numpy as np
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtGui import QSurfaceFormat
from PyQt6.QtWidgets import QWidget
import OpenGL.GL as gl
from OpenGL.GL import shaders

# Note: Implements rendering functionality as concrete class


logger = logging.getLogger(__name__)


class OpenGLRenderer(QOpenGLWidget):
    """
    OpenGL-based renderer for real-time karaoke subtitle preview.
    
    Extends QOpenGLWidget to provide hardware-accelerated rendering
    with support for text effects, animations, and video composition.
    """
    
    # Signals for UI communication
    render_error = pyqtSignal(str)
    fps_updated = pyqtSignal(float)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # OpenGL context and capabilities
        self._opengl_version: Optional[Tuple[int, int]] = None
        self._shader_programs: Dict[str, int] = {}
        self._vertex_arrays: Dict[str, int] = {}
        self._textures: Dict[str, int] = {}
        
        # Rendering state
        self._viewport_size: Tuple[int, int] = (1920, 1080)
        self._clear_color: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)
        
        # Performance monitoring
        self._frame_count = 0
        self._fps_timer = QTimer()
        self._fps_timer.timeout.connect(self._update_fps)
        self._fps_timer.start(1000)  # Update FPS every second
        
        # Configure OpenGL surface format
        self._configure_surface_format()
        
    def _configure_surface_format(self) -> None:
        """Configure OpenGL surface format with required capabilities."""
        format = QSurfaceFormat()
        format.setVersion(3, 3)  # Require OpenGL 3.3+
        format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
        format.setDepthBufferSize(24)
        format.setStencilBufferSize(8)
        format.setSamples(4)  # 4x MSAA for anti-aliasing
        format.setSwapBehavior(QSurfaceFormat.SwapBehavior.DoubleBuffer)
        
        self.setFormat(format)
        
    def initializeGL(self) -> None:
        """Initialize OpenGL context and validate capabilities."""
        try:
            # Check OpenGL version
            version_string = gl.glGetString(gl.GL_VERSION).decode('utf-8')
            logger.info(f"OpenGL Version: {version_string}")
            
            # Extract version numbers
            version_parts = version_string.split('.')
            major = int(version_parts[0])
            minor = int(version_parts[1].split()[0])
            self._opengl_version = (major, minor)
            
            # Validate minimum version requirement
            if not self._validate_opengl_version():
                error_msg = f"OpenGL 3.3+ required, found {major}.{minor}"
                logger.error(error_msg)
                self.render_error.emit(error_msg)
                return
                
            # Log GPU information
            renderer = gl.glGetString(gl.GL_RENDERER).decode('utf-8')
            vendor = gl.glGetString(gl.GL_VENDOR).decode('utf-8')
            logger.info(f"GPU: {renderer} ({vendor})")
            
            # Configure OpenGL state
            self._configure_opengl_state()
            
            # Load basic shaders
            self._load_basic_shaders()
            
            # Create basic geometry
            self._create_basic_geometry()
            
            logger.info("OpenGL renderer initialized successfully")
            
        except Exception as e:
            error_msg = f"Failed to initialize OpenGL: {str(e)}"
            logger.error(error_msg)
            self.render_error.emit(error_msg)
            
    def _validate_opengl_version(self) -> bool:
        """Validate that OpenGL version meets minimum requirements."""
        if not self._opengl_version:
            return False
            
        major, minor = self._opengl_version
        return major > 3 or (major == 3 and minor >= 3)
        
    def _configure_opengl_state(self) -> None:
        """Configure basic OpenGL rendering state."""
        # Enable depth testing
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glDepthFunc(gl.GL_LEQUAL)
        
        # Enable blending for transparency
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        
        # Enable multisampling for anti-aliasing
        gl.glEnable(gl.GL_MULTISAMPLE)
        
        # Set clear color
        gl.glClearColor(*self._clear_color)
        
    def _load_basic_shaders(self) -> None:
        """Load basic vertex and fragment shaders."""
        try:
            # Load basic text rendering shader
            text_vertex_shader = self._load_shader_source("text_vertex.glsl")
            text_fragment_shader = self._load_shader_source("text_fragment.glsl")
            
            if text_vertex_shader and text_fragment_shader:
                self._shader_programs["text"] = self._compile_shader_program(
                    text_vertex_shader, text_fragment_shader
                )
                
            # Load basic quad rendering shader for backgrounds/effects
            quad_vertex_shader = self._load_shader_source("quad_vertex.glsl")
            quad_fragment_shader = self._load_shader_source("quad_fragment.glsl")
            
            if quad_vertex_shader and quad_fragment_shader:
                self._shader_programs["quad"] = self._compile_shader_program(
                    quad_vertex_shader, quad_fragment_shader
                )
                
        except Exception as e:
            logger.warning(f"Failed to load some shaders: {e}")
            # Create fallback shaders if files don't exist
            self._create_fallback_shaders()
            
    def _load_shader_source(self, filename: str) -> Optional[str]:
        """Load shader source code from file."""
        # Determine shader type from filename
        if "vertex" in filename:
            shader_dir = Path("shaders/vertex")
        elif "fragment" in filename:
            shader_dir = Path("shaders/fragment")
        else:
            logger.error(f"Unknown shader type for {filename}")
            return None
            
        shader_path = shader_dir / filename
        
        if shader_path.exists():
            try:
                return shader_path.read_text(encoding='utf-8')
            except Exception as e:
                logger.error(f"Failed to read shader {shader_path}: {e}")
                return None
        else:
            logger.warning(f"Shader file not found: {shader_path}")
            return None
            
    def _compile_shader_program(self, vertex_source: str, fragment_source: str) -> int:
        """Compile and link a shader program."""
        try:
            # Compile vertex shader
            vertex_shader = shaders.compileShader(vertex_source, gl.GL_VERTEX_SHADER)
            
            # Compile fragment shader
            fragment_shader = shaders.compileShader(fragment_source, gl.GL_FRAGMENT_SHADER)
            
            # Link shader program
            program = shaders.compileProgram(vertex_shader, fragment_shader)
            
            # Clean up individual shaders
            gl.glDeleteShader(vertex_shader)
            gl.glDeleteShader(fragment_shader)
            
            return program
            
        except Exception as e:
            logger.error(f"Shader compilation failed: {e}")
            raise
            
    def _create_fallback_shaders(self) -> None:
        """Create basic fallback shaders if shader files are not available."""
        # Basic vertex shader for text rendering
        text_vertex_source = """
        #version 330 core
        
        layout (location = 0) in vec3 position;
        layout (location = 1) in vec2 texCoord;
        
        uniform mat4 projection;
        uniform mat4 model;
        
        out vec2 TexCoord;
        
        void main() {
            gl_Position = projection * model * vec4(position, 1.0);
            TexCoord = texCoord;
        }
        """
        
        # Basic fragment shader for text rendering
        text_fragment_source = """
        #version 330 core
        
        in vec2 TexCoord;
        out vec4 FragColor;
        
        uniform sampler2D textTexture;
        uniform vec4 textColor;
        
        void main() {
            vec4 sampled = vec4(1.0, 1.0, 1.0, texture(textTexture, TexCoord).r);
            FragColor = textColor * sampled;
        }
        """
        
        # Basic quad vertex shader
        quad_vertex_source = """
        #version 330 core
        
        layout (location = 0) in vec3 position;
        layout (location = 1) in vec2 texCoord;
        
        uniform mat4 projection;
        
        out vec2 TexCoord;
        
        void main() {
            gl_Position = projection * vec4(position, 1.0);
            TexCoord = texCoord;
        }
        """
        
        # Basic quad fragment shader
        quad_fragment_source = """
        #version 330 core
        
        in vec2 TexCoord;
        out vec4 FragColor;
        
        uniform vec4 color;
        
        void main() {
            FragColor = color;
        }
        """
        
        try:
            self._shader_programs["text"] = self._compile_shader_program(
                text_vertex_source, text_fragment_source
            )
            self._shader_programs["quad"] = self._compile_shader_program(
                quad_vertex_source, quad_fragment_source
            )
            logger.info("Fallback shaders created successfully")
        except Exception as e:
            logger.error(f"Failed to create fallback shaders: {e}")
            
    def _create_basic_geometry(self) -> None:
        """Create basic geometry for rendering (quad for text/effects)."""
        # Define quad vertices (position + texture coordinates)
        quad_vertices = np.array([
            # Positions    # Texture Coords
            -1.0, -1.0, 0.0,  0.0, 0.0,  # Bottom-left
             1.0, -1.0, 0.0,  1.0, 0.0,  # Bottom-right
             1.0,  1.0, 0.0,  1.0, 1.0,  # Top-right
            -1.0,  1.0, 0.0,  0.0, 1.0   # Top-left
        ], dtype=np.float32)
        
        # Define indices for quad
        quad_indices = np.array([
            0, 1, 2,  # First triangle
            2, 3, 0   # Second triangle
        ], dtype=np.uint32)
        
        # Create and bind VAO
        vao = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(vao)
        
        # Create and bind VBO
        vbo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, quad_vertices.nbytes, quad_vertices, gl.GL_STATIC_DRAW)
        
        # Create and bind EBO
        ebo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, ebo)
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, quad_indices.nbytes, quad_indices, gl.GL_STATIC_DRAW)
        
        # Configure vertex attributes
        # Position attribute
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 5 * 4, None)
        gl.glEnableVertexAttribArray(0)
        
        # Texture coordinate attribute
        gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, 5 * 4, gl.ctypes.c_void_p(3 * 4))
        gl.glEnableVertexAttribArray(1)
        
        # Store VAO for later use
        self._vertex_arrays["quad"] = vao
        
        # Unbind
        gl.glBindVertexArray(0)
        
    def paintGL(self) -> None:
        """Render the current frame."""
        try:
            # Clear buffers
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            
            # Update frame count for FPS calculation
            self._frame_count += 1
            
            # Basic rendering - just clear for now
            # TODO: Add actual subtitle rendering in future tasks
            
        except Exception as e:
            logger.error(f"Render error: {e}")
            
    def resizeGL(self, width: int, height: int) -> None:
        """Handle viewport resize."""
        self._viewport_size = (width, height)
        gl.glViewport(0, 0, width, height)
        
    def _update_fps(self) -> None:
        """Update FPS counter."""
        fps = self._frame_count
        self._frame_count = 0
        self.fps_updated.emit(fps)
        
    def get_opengl_info(self) -> Dict[str, Any]:
        """Get OpenGL context information."""
        if not self._opengl_version:
            return {}
            
        return {
            "version": self._opengl_version,
            "renderer": gl.glGetString(gl.GL_RENDERER).decode('utf-8'),
            "vendor": gl.glGetString(gl.GL_VENDOR).decode('utf-8'),
            "viewport_size": self._viewport_size,
            "shader_programs": list(self._shader_programs.keys())
        }
        
    def cleanup(self) -> None:
        """Clean up OpenGL resources."""
        try:
            # Delete shader programs
            for program in self._shader_programs.values():
                gl.glDeleteProgram(program)
            self._shader_programs.clear()
            
            # Delete vertex arrays
            for vao in self._vertex_arrays.values():
                gl.glDeleteVertexArrays(1, [vao])
            self._vertex_arrays.clear()
            
            # Delete textures
            for texture in self._textures.values():
                gl.glDeleteTextures(1, [texture])
            self._textures.clear()
            
            logger.info("OpenGL resources cleaned up")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")