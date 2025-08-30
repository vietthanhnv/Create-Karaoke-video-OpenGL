"""
Font management system using FreeType for text rendering.

This module provides font loading, glyph extraction, and texture atlas
generation for OpenGL-based text rendering with Unicode support.
"""

import logging
from typing import Dict, Optional, Tuple, List, NamedTuple
from pathlib import Path
import struct

import numpy as np
import freetype
from PIL import Image
import OpenGL.GL as gl

from .sdf_generator import SDFGenerator, SDFTextRenderer


logger = logging.getLogger(__name__)


class GlyphMetrics(NamedTuple):
    """Glyph metrics for positioning and rendering."""
    width: int
    height: int
    bearing_x: int
    bearing_y: int
    advance: int
    atlas_x: int
    atlas_y: int


class FontAtlas:
    """
    Texture atlas containing rendered glyphs for a specific font and size.
    
    Manages glyph textures in a single OpenGL texture for efficient rendering
    with support for dynamic glyph loading and Unicode characters.
    """
    
    def __init__(self, font_size: int, atlas_width: int = 1024, atlas_height: int = 1024, 
                 create_texture: bool = True, use_sdf: bool = False):
        self.font_size = font_size
        self.atlas_width = atlas_width
        self.atlas_height = atlas_height
        self.use_sdf = use_sdf
        
        # OpenGL texture
        self.texture_id: Optional[int] = None
        self._texture_created = False
        
        # Atlas management
        self.current_x = 0
        self.current_y = 0
        self.row_height = 0
        
        # Glyph storage
        self.glyphs: Dict[int, GlyphMetrics] = {}  # codepoint -> metrics
        
        # Atlas bitmap data (float32 for SDF, uint8 for regular)
        if use_sdf:
            self.atlas_data = np.zeros((atlas_height, atlas_width), dtype=np.float32)
            self.sdf_generator = SDFGenerator()
        else:
            self.atlas_data = np.zeros((atlas_height, atlas_width), dtype=np.uint8)
            self.sdf_generator = None
        
        # Initialize OpenGL texture if requested and context is available
        if create_texture:
            self._create_texture()
        
    def _create_texture(self) -> None:
        """Create OpenGL texture for the atlas."""
        try:
            self.texture_id = gl.glGenTextures(1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_id)
            
            # Set texture parameters
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            
            # Initialize with empty data (format depends on SDF usage)
            if self.use_sdf:
                gl.glTexImage2D(
                    gl.GL_TEXTURE_2D, 0, gl.GL_R32F,
                    self.atlas_width, self.atlas_height, 0,
                    gl.GL_RED, gl.GL_FLOAT, self.atlas_data
                )
            else:
                gl.glTexImage2D(
                    gl.GL_TEXTURE_2D, 0, gl.GL_RED,
                    self.atlas_width, self.atlas_height, 0,
                    gl.GL_RED, gl.GL_UNSIGNED_BYTE, self.atlas_data
                )
            
            gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
            self._texture_created = True
            
        except Exception as e:
            logger.warning(f"Failed to create OpenGL texture for font atlas: {e}")
            self.texture_id = None
            self._texture_created = False
        
    def add_glyph(self, codepoint: int, glyph_bitmap: np.ndarray, metrics: Tuple[int, int, int, int, int]) -> bool:
        """
        Add a glyph to the atlas.
        
        Args:
            codepoint: Unicode codepoint
            glyph_bitmap: Glyph bitmap data (height x width)
            metrics: (width, height, bearing_x, bearing_y, advance)
            
        Returns:
            True if glyph was added successfully, False if no space
        """
        if codepoint in self.glyphs:
            return True  # Already exists
            
        width, height, bearing_x, bearing_y, advance = metrics
        
        # Check if we need to move to next row
        if self.current_x + width > self.atlas_width:
            self.current_x = 0
            self.current_y += self.row_height
            self.row_height = 0
            
        # Check if we have vertical space
        if self.current_y + height > self.atlas_height:
            logger.warning(f"Font atlas full, cannot add glyph {codepoint}")
            return False
            
        # Store glyph position
        atlas_x = self.current_x
        atlas_y = self.current_y
        
        # Copy glyph data to atlas (with SDF generation if enabled)
        if glyph_bitmap.size > 0:
            if self.use_sdf and self.sdf_generator:
                # Generate SDF from bitmap
                sdf_data = self.sdf_generator.generate_sdf(glyph_bitmap)
                sdf_height, sdf_width = sdf_data.shape
                
                # Update atlas position and size for SDF
                end_y = atlas_y + sdf_height
                end_x = atlas_x + sdf_width
                
                # Ensure we have space for SDF
                if end_x <= self.atlas_width and end_y <= self.atlas_height:
                    self.atlas_data[atlas_y:end_y, atlas_x:end_x] = sdf_data
                    # Update metrics to reflect SDF size
                    width, height = sdf_width, sdf_height
                else:
                    logger.warning(f"Not enough space for SDF glyph {codepoint}")
                    return False
            else:
                # Regular bitmap copy
                end_y = atlas_y + height
                end_x = atlas_x + width
                self.atlas_data[atlas_y:end_y, atlas_x:end_x] = glyph_bitmap
            
        # Store glyph metrics
        self.glyphs[codepoint] = GlyphMetrics(
            width=width,
            height=height,
            bearing_x=bearing_x,
            bearing_y=bearing_y,
            advance=advance,
            atlas_x=atlas_x,
            atlas_y=atlas_y
        )
        
        # Update position for next glyph
        self.current_x += width
        self.row_height = max(self.row_height, height)
        
        return True
        
    def update_texture(self) -> None:
        """Update the OpenGL texture with current atlas data."""
        if self.texture_id and self._texture_created:
            try:
                gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_id)
                if self.use_sdf:
                    gl.glTexSubImage2D(
                        gl.GL_TEXTURE_2D, 0, 0, 0,
                        self.atlas_width, self.atlas_height,
                        gl.GL_RED, gl.GL_FLOAT, self.atlas_data
                    )
                else:
                    gl.glTexSubImage2D(
                        gl.GL_TEXTURE_2D, 0, 0, 0,
                        self.atlas_width, self.atlas_height,
                        gl.GL_RED, gl.GL_UNSIGNED_BYTE, self.atlas_data
                    )
                gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
            except Exception as e:
                logger.warning(f"Failed to update texture: {e}")
                
    def ensure_texture_created(self) -> bool:
        """Ensure OpenGL texture is created. Call this when OpenGL context is available."""
        if not self._texture_created:
            self._create_texture()
        return self._texture_created
            
    def get_glyph(self, codepoint: int) -> Optional[GlyphMetrics]:
        """Get glyph metrics by codepoint."""
        return self.glyphs.get(codepoint)
        
    def get_texture_coords(self, codepoint: int) -> Optional[Tuple[float, float, float, float]]:
        """
        Get normalized texture coordinates for a glyph.
        
        Returns:
            (u1, v1, u2, v2) texture coordinates or None if glyph not found
        """
        glyph = self.get_glyph(codepoint)
        if not glyph:
            return None
            
        u1 = glyph.atlas_x / self.atlas_width
        v1 = glyph.atlas_y / self.atlas_height
        u2 = (glyph.atlas_x + glyph.width) / self.atlas_width
        v2 = (glyph.atlas_y + glyph.height) / self.atlas_height
        
        return (u1, v1, u2, v2)
        
    def cleanup(self) -> None:
        """Clean up OpenGL resources."""
        if self.texture_id:
            gl.glDeleteTextures(1, [self.texture_id])
            self.texture_id = None


class FontManager:
    """
    Manages font loading and glyph rendering using FreeType.
    
    Provides high-level interface for text rendering with automatic
    atlas management, Unicode support, and efficient glyph caching.
    """
    
    def __init__(self):
        self._fonts: Dict[str, freetype.Face] = {}
        self._atlases: Dict[Tuple[str, int], FontAtlas] = {}  # (font_path, size) -> atlas
        self._default_font_paths = self._get_default_font_paths()
        
    def _get_default_font_paths(self) -> List[str]:
        """Get list of default system font paths."""
        import platform
        system = platform.system()
        
        if system == "Windows":
            return [
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/calibri.ttf",
                "C:/Windows/Fonts/tahoma.ttf",
                "C:/Windows/Fonts/verdana.ttf"
            ]
        elif system == "Darwin":  # macOS
            return [
                "/System/Library/Fonts/Arial.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
                "/Library/Fonts/Arial.ttf"
            ]
        else:  # Linux
            return [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "/usr/share/fonts/TTF/arial.ttf"
            ]
            
    def load_font(self, font_path: str, font_size: int = 48) -> bool:
        """
        Load a font from file.
        
        Args:
            font_path: Path to font file (TTF, OTF)
            font_size: Font size in pixels
            
        Returns:
            True if font loaded successfully
        """
        try:
            # Check if font file exists
            if not Path(font_path).exists():
                logger.error(f"Font file not found: {font_path}")
                return False
                
            # Load font face
            face = freetype.Face(font_path)
            face.set_pixel_sizes(0, font_size)
            
            # Store font
            font_key = f"{font_path}:{font_size}"
            self._fonts[font_key] = face
            
            # Create atlas for this font/size combination (without OpenGL texture initially)
            atlas_key = (font_path, font_size)
            # Use SDF for larger font sizes for better quality
            use_sdf = font_size >= 32
            self._atlases[atlas_key] = FontAtlas(font_size, create_texture=False, use_sdf=use_sdf)
            
            logger.info(f"Loaded font: {font_path} at size {font_size}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load font {font_path}: {e}")
            return False
            
    def load_default_font(self, font_size: int = 48) -> bool:
        """Load the first available default system font."""
        for font_path in self._default_font_paths:
            if self.load_font(font_path, font_size):
                return True
                
        logger.error("No default fonts could be loaded")
        return False
        
    def get_font_atlas(self, font_path: str, font_size: int) -> Optional[FontAtlas]:
        """Get font atlas for specified font and size."""
        atlas_key = (font_path, font_size)
        return self._atlases.get(atlas_key)
        
    def render_glyph(self, font_path: str, font_size: int, codepoint: int) -> bool:
        """
        Render a glyph and add it to the font atlas.
        
        Args:
            font_path: Path to font file
            font_size: Font size in pixels
            codepoint: Unicode codepoint to render
            
        Returns:
            True if glyph was rendered successfully
        """
        font_key = f"{font_path}:{font_size}"
        atlas_key = (font_path, font_size)
        
        # Check if font and atlas exist
        if font_key not in self._fonts or atlas_key not in self._atlases:
            logger.error(f"Font not loaded: {font_path} at size {font_size}")
            return False
            
        face = self._fonts[font_key]
        atlas = self._atlases[atlas_key]
        
        # Check if glyph already exists
        if atlas.get_glyph(codepoint):
            return True
            
        try:
            # Load glyph
            face.load_char(chr(codepoint), freetype.FT_LOAD_RENDER)
            glyph = face.glyph
            bitmap = glyph.bitmap
            
            # Convert bitmap to numpy array
            if bitmap.width > 0 and bitmap.rows > 0:
                # Create numpy array from bitmap buffer
                bitmap_data = np.array(bitmap.buffer, dtype=np.uint8)
                bitmap_array = bitmap_data.reshape((bitmap.rows, bitmap.width))
            else:
                # Empty glyph (like space)
                bitmap_array = np.zeros((0, 0), dtype=np.uint8)
                
            # Get glyph metrics
            metrics = (
                bitmap.width,
                bitmap.rows,
                glyph.bitmap_left,
                glyph.bitmap_top,
                glyph.advance.x >> 6  # Convert from 26.6 fixed point
            )
            
            # Add glyph to atlas
            success = atlas.add_glyph(codepoint, bitmap_array, metrics)
            if success:
                atlas.update_texture()
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to render glyph {codepoint}: {e}")
            return False
            
    def render_text_glyphs(self, font_path: str, font_size: int, text: str) -> bool:
        """
        Render all glyphs needed for a text string.
        
        Args:
            font_path: Path to font file
            font_size: Font size in pixels
            text: Text string to prepare glyphs for
            
        Returns:
            True if all glyphs were rendered successfully
        """
        success = True
        
        for char in text:
            codepoint = ord(char)
            if not self.render_glyph(font_path, font_size, codepoint):
                success = False
                
        return success
        
    def get_text_metrics(self, font_path: str, font_size: int, text: str) -> Tuple[int, int]:
        """
        Calculate text dimensions.
        
        Args:
            font_path: Path to font file
            font_size: Font size in pixels
            text: Text to measure
            
        Returns:
            (width, height) in pixels
        """
        atlas = self.get_font_atlas(font_path, font_size)
        if not atlas:
            return (0, 0)
            
        # Ensure all glyphs are rendered
        self.render_text_glyphs(font_path, font_size, text)
        
        total_width = 0
        max_height = 0
        
        for char in text:
            codepoint = ord(char)
            glyph = atlas.get_glyph(codepoint)
            
            if glyph:
                total_width += glyph.advance
                max_height = max(max_height, glyph.height)
                
        return (total_width, max_height)
        
    def get_available_fonts(self) -> List[str]:
        """Get list of loaded font keys."""
        return list(self._fonts.keys())
        
    def initialize_opengl_textures(self) -> bool:
        """Initialize OpenGL textures for all loaded atlases. Call when OpenGL context is available."""
        success = True
        for atlas in self._atlases.values():
            if not atlas.ensure_texture_created():
                success = False
        return success
        
    def cleanup(self) -> None:
        """Clean up all font resources."""
        # Clean up atlases
        for atlas in self._atlases.values():
            atlas.cleanup()
        self._atlases.clear()
        
        # Clean up font faces
        self._fonts.clear()
        
        logger.info("Font manager cleaned up")