"""
OpenGL-based text rendering system with advanced typography support.

This module provides high-performance text rendering using OpenGL with
support for Unicode, text effects, and real-time parameter adjustment.
"""

import logging
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

import numpy as np
import OpenGL.GL as gl

from .font_manager import FontManager, FontAtlas
from ..graphics.shader_manager import ShaderManager, ShaderProgram


logger = logging.getLogger(__name__)


class TextAlignment(Enum):
    """Text alignment options."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


@dataclass
class TextStyle:
    """Text styling parameters."""
    font_path: str
    font_size: int = 48
    color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    alignment: TextAlignment = TextAlignment.LEFT
    line_spacing: float = 1.2
    character_spacing: float = 0.0
    
    # Effects
    outline_width: float = 0.0
    outline_color: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)
    shadow_offset: Tuple[float, float] = (0.0, 0.0)
    shadow_color: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.5)


@dataclass
class TextVertex:
    """Vertex data for text rendering."""
    position: Tuple[float, float, float]
    tex_coord: Tuple[float, float]
    color: Tuple[float, float, float, float]


class TextMesh:
    """
    Mesh data for rendered text with OpenGL buffers.
    
    Manages vertex data, texture coordinates, and OpenGL resources
    for efficient text rendering with batching support.
    """
    
    def __init__(self):
        self.vertices: List[TextVertex] = []
        self.indices: List[int] = []
        
        # OpenGL resources
        self.vao: Optional[int] = None
        self.vbo: Optional[int] = None
        self.ebo: Optional[int] = None
        
        # Mesh properties
        self.vertex_count = 0
        self.index_count = 0
        
    def add_quad(self, x: float, y: float, width: float, height: float,
                 u1: float, v1: float, u2: float, v2: float,
                 color: Tuple[float, float, float, float]) -> None:
        """Add a textured quad to the mesh."""
        base_index = len(self.vertices)
        
        # Add vertices (bottom-left, bottom-right, top-right, top-left)
        self.vertices.extend([
            TextVertex((x, y, 0.0), (u1, v2), color),                    # Bottom-left
            TextVertex((x + width, y, 0.0), (u2, v2), color),           # Bottom-right
            TextVertex((x + width, y + height, 0.0), (u2, v1), color),  # Top-right
            TextVertex((x, y + height, 0.0), (u1, v1), color)           # Top-left
        ])
        
        # Add indices for two triangles
        self.indices.extend([
            base_index, base_index + 1, base_index + 2,  # First triangle
            base_index + 2, base_index + 3, base_index   # Second triangle
        ])
        
    def upload_to_gpu(self) -> None:
        """Upload mesh data to GPU buffers."""
        if not self.vertices:
            return
            
        # Convert vertices to numpy array
        vertex_data = []
        for vertex in self.vertices:
            vertex_data.extend(vertex.position)
            vertex_data.extend(vertex.tex_coord)
            vertex_data.extend(vertex.color)
            
        vertex_array = np.array(vertex_data, dtype=np.float32)
        index_array = np.array(self.indices, dtype=np.uint32)
        
        # Create VAO
        if not self.vao:
            self.vao = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(self.vao)
        
        # Create and upload VBO
        if not self.vbo:
            self.vbo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertex_array.nbytes, vertex_array, gl.GL_DYNAMIC_DRAW)
        
        # Create and upload EBO
        if not self.ebo:
            self.ebo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, index_array.nbytes, index_array, gl.GL_DYNAMIC_DRAW)
        
        # Configure vertex attributes
        stride = 9 * 4  # 3 position + 2 texcoord + 4 color floats
        
        # Position attribute (location 0)
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, None)
        gl.glEnableVertexAttribArray(0)
        
        # Texture coordinate attribute (location 1)
        gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, stride, gl.ctypes.c_void_p(3 * 4))
        gl.glEnableVertexAttribArray(1)
        
        # Color attribute (location 2)
        gl.glVertexAttribPointer(2, 4, gl.GL_FLOAT, gl.GL_FALSE, stride, gl.ctypes.c_void_p(5 * 4))
        gl.glEnableVertexAttribArray(2)
        
        # Store counts
        self.vertex_count = len(self.vertices)
        self.index_count = len(self.indices)
        
        # Unbind
        gl.glBindVertexArray(0)
        
    def render(self) -> None:
        """Render the text mesh."""
        if self.vao and self.index_count > 0:
            gl.glBindVertexArray(self.vao)
            gl.glDrawElements(gl.GL_TRIANGLES, self.index_count, gl.GL_UNSIGNED_INT, None)
            gl.glBindVertexArray(0)
            
    def clear(self) -> None:
        """Clear mesh data."""
        self.vertices.clear()
        self.indices.clear()
        self.vertex_count = 0
        self.index_count = 0
        
    def cleanup(self) -> None:
        """Clean up OpenGL resources."""
        if self.vao:
            gl.glDeleteVertexArrays(1, [self.vao])
            self.vao = None
        if self.vbo:
            gl.glDeleteBuffers(1, [self.vbo])
            self.vbo = None
        if self.ebo:
            gl.glDeleteBuffers(1, [self.ebo])
            self.ebo = None


class TextRenderer:
    """
    High-performance OpenGL text renderer with Unicode support.
    
    Provides advanced text rendering capabilities including multi-language
    support, text effects, and real-time parameter adjustment for karaoke
    subtitle display.
    """
    
    def __init__(self, shader_manager: ShaderManager):
        self.shader_manager = shader_manager
        self.font_manager = FontManager()
        
        # Rendering resources
        self._text_shader: Optional[ShaderProgram] = None
        self._current_mesh = TextMesh()
        
        # Projection matrix for 2D rendering
        self._projection_matrix = np.eye(4, dtype=np.float32)
        
        # Initialize text rendering shader
        self._initialize_text_shader()
        
    def _initialize_text_shader(self) -> None:
        """Initialize the text rendering shader program."""
        # Text vertex shader
        vertex_source = """
        #version 330 core
        
        layout (location = 0) in vec3 position;
        layout (location = 1) in vec2 texCoord;
        layout (location = 2) in vec4 color;
        
        uniform mat4 projection;
        uniform mat4 model;
        
        out vec2 TexCoord;
        out vec4 VertexColor;
        
        void main() {
            gl_Position = projection * model * vec4(position, 1.0);
            TexCoord = texCoord;
            VertexColor = color;
        }
        """
        
        # Text fragment shader with SDF support
        fragment_source = """
        #version 330 core
        
        in vec2 TexCoord;
        in vec4 VertexColor;
        out vec4 FragColor;
        
        uniform sampler2D fontAtlas;
        uniform float outlineWidth;
        uniform vec4 outlineColor;
        uniform vec2 shadowOffset;
        uniform vec4 shadowColor;
        uniform bool enableOutline;
        uniform bool enableShadow;
        
        void main() {
            // Sample the font atlas
            float alpha = texture(fontAtlas, TexCoord).r;
            
            vec4 finalColor = VertexColor;
            finalColor.a *= alpha;
            
            // Simple outline effect (can be enhanced with SDF later)
            if (enableOutline && outlineWidth > 0.0) {
                float outline = alpha;
                if (alpha < 0.5) {
                    // Sample neighboring pixels for outline
                    vec2 texelSize = 1.0 / textureSize(fontAtlas, 0);
                    float maxAlpha = 0.0;
                    
                    for (int x = -1; x <= 1; x++) {
                        for (int y = -1; y <= 1; y++) {
                            vec2 offset = vec2(float(x), float(y)) * texelSize * outlineWidth;
                            maxAlpha = max(maxAlpha, texture(fontAtlas, TexCoord + offset).r);
                        }
                    }
                    
                    if (maxAlpha > 0.1) {
                        finalColor = mix(outlineColor, finalColor, alpha);
                        finalColor.a = max(finalColor.a, maxAlpha * outlineColor.a);
                    }
                }
            }
            
            // Shadow effect
            if (enableShadow && length(shadowOffset) > 0.0) {
                vec2 texelSize = 1.0 / textureSize(fontAtlas, 0);
                vec2 shadowTexCoord = TexCoord + shadowOffset * texelSize;
                float shadowAlpha = texture(fontAtlas, shadowTexCoord).r;
                
                if (shadowAlpha > 0.1 && alpha < 0.1) {
                    finalColor = shadowColor;
                    finalColor.a *= shadowAlpha;
                }
            }
            
            FragColor = finalColor;
        }
        """
        
        # Load shader program
        self._text_shader = self.shader_manager.load_shader_from_source(
            "text_renderer", vertex_source, fragment_source
        )
        
        if not self._text_shader:
            logger.error("Failed to create text rendering shader")
            
    def load_font(self, font_path: str, font_size: int = 48) -> bool:
        """Load a font for text rendering."""
        return self.font_manager.load_font(font_path, font_size)
        
    def load_default_font(self, font_size: int = 48) -> bool:
        """Load default system font."""
        return self.font_manager.load_default_font(font_size)
        
    def set_projection_matrix(self, width: int, height: int) -> None:
        """Set orthographic projection matrix for 2D text rendering."""
        # Create orthographic projection matrix
        self._projection_matrix = np.array([
            [2.0/width, 0.0, 0.0, -1.0],
            [0.0, 2.0/height, 0.0, -1.0],
            [0.0, 0.0, -1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=np.float32)
        
    def render_text(self, text: str, x: float, y: float, style: TextStyle) -> None:
        """
        Render text at specified position with given style.
        
        Args:
            text: Text string to render (supports Unicode)
            x: X position in pixels
            y: Y position in pixels
            style: Text styling parameters
        """
        if not self._text_shader or not text:
            return
            
        # Get font atlas
        atlas = self.font_manager.get_font_atlas(style.font_path, style.font_size)
        if not atlas:
            logger.error(f"Font atlas not found: {style.font_path} at size {style.font_size}")
            return
            
        # Ensure all glyphs are rendered
        self.font_manager.render_text_glyphs(style.font_path, style.font_size, text)
        
        # Clear previous mesh
        self._current_mesh.clear()
        
        # Generate text mesh
        self._generate_text_mesh(text, x, y, style, atlas)
        
        # Upload mesh to GPU
        self._current_mesh.upload_to_gpu()
        
        # Render text
        self._render_text_mesh(atlas, style)
        
    def _generate_text_mesh(self, text: str, x: float, y: float, style: TextStyle, atlas: FontAtlas) -> None:
        """Generate mesh data for text rendering."""
        current_x = x
        current_y = y
        
        # Process each character
        for char in text:
            if char == '\n':
                # Handle line breaks
                current_x = x
                current_y -= style.font_size * style.line_spacing
                continue
                
            codepoint = ord(char)
            glyph = atlas.get_glyph(codepoint)
            
            if not glyph:
                logger.warning(f"Glyph not found for character: {char} (U+{codepoint:04X})")
                continue
                
            # Skip rendering for space characters with no bitmap
            if glyph.width == 0 or glyph.height == 0:
                current_x += glyph.advance + style.character_spacing
                continue
                
            # Calculate glyph position
            glyph_x = current_x + glyph.bearing_x
            glyph_y = current_y - (glyph.height - glyph.bearing_y)
            
            # Get texture coordinates
            tex_coords = atlas.get_texture_coords(codepoint)
            if not tex_coords:
                continue
                
            u1, v1, u2, v2 = tex_coords
            
            # Add quad for this glyph
            self._current_mesh.add_quad(
                glyph_x, glyph_y, glyph.width, glyph.height,
                u1, v1, u2, v2, style.color
            )
            
            # Advance to next character position
            current_x += glyph.advance + style.character_spacing
            
    def _render_text_mesh(self, atlas: FontAtlas, style: TextStyle) -> None:
        """Render the generated text mesh."""
        if not self._text_shader or not atlas.texture_id:
            return
            
        # Enable blending for text transparency
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        
        # Use text shader
        self._text_shader.use()
        
        # Set uniforms
        self._text_shader.set_uniform("projection", self._projection_matrix)
        self._text_shader.set_uniform("model", np.eye(4, dtype=np.float32))
        
        # Bind font atlas texture
        self._text_shader.bind_texture(atlas.texture_id, 0, "fontAtlas")
        
        # Set effect uniforms
        self._text_shader.set_uniform("outlineWidth", style.outline_width)
        self._text_shader.set_uniform("outlineColor", style.outline_color)
        self._text_shader.set_uniform("shadowOffset", style.shadow_offset)
        self._text_shader.set_uniform("shadowColor", style.shadow_color)
        self._text_shader.set_uniform("enableOutline", style.outline_width > 0.0)
        self._text_shader.set_uniform("enableShadow", 
                                    style.shadow_offset[0] != 0.0 or style.shadow_offset[1] != 0.0)
        
        # Render mesh
        self._current_mesh.render()
        
        # Cleanup
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        gl.glUseProgram(0)
        
    def measure_text(self, text: str, style: TextStyle) -> Tuple[int, int]:
        """
        Measure text dimensions.
        
        Args:
            text: Text to measure
            style: Text style parameters
            
        Returns:
            (width, height) in pixels
        """
        return self.font_manager.get_text_metrics(style.font_path, style.font_size, text)
        
    def get_available_fonts(self) -> List[str]:
        """Get list of available loaded fonts."""
        return self.font_manager.get_available_fonts()
        
    def cleanup(self) -> None:
        """Clean up text rendering resources."""
        self._current_mesh.cleanup()
        self.font_manager.cleanup()
        logger.info("Text renderer cleaned up")