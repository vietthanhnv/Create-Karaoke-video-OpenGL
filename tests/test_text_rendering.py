"""
Tests for text rendering system with FreeType integration.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.text.font_manager import FontManager, FontAtlas, GlyphMetrics
from src.text.text_renderer import TextRenderer, TextStyle, TextAlignment, TextMesh
from src.text.text_layout import TextLayoutEngine, TextBlock, TextLine


class TestFontAtlas:
    """Test font atlas functionality."""
    
    def test_atlas_creation(self):
        """Test font atlas initialization."""
        atlas = FontAtlas(font_size=48, atlas_width=512, atlas_height=512, create_texture=False)
        
        assert atlas.font_size == 48
        assert atlas.atlas_width == 512
        assert atlas.atlas_height == 512
        assert atlas.current_x == 0
        assert atlas.current_y == 0
        assert atlas.row_height == 0
        assert len(atlas.glyphs) == 0
        
    def test_glyph_addition(self):
        """Test adding glyphs to atlas."""
        atlas = FontAtlas(font_size=48, create_texture=False)
        
        # Create mock glyph bitmap
        glyph_bitmap = np.ones((20, 15), dtype=np.uint8) * 255
        metrics = (15, 20, 2, 18, 16)  # width, height, bearing_x, bearing_y, advance
        
        # Add glyph
        success = atlas.add_glyph(ord('A'), glyph_bitmap, metrics)
        
        assert success
        assert ord('A') in atlas.glyphs
        
        glyph = atlas.glyphs[ord('A')]
        assert glyph.width == 15
        assert glyph.height == 20
        assert glyph.atlas_x == 0
        assert glyph.atlas_y == 0


class TestTextStyle:
    """Test text style configuration."""
    
    def test_default_style(self):
        """Test default text style values."""
        style = TextStyle(font_path="test.ttf")
        
        assert style.font_path == "test.ttf"
        assert style.font_size == 48
        assert style.color == (1.0, 1.0, 1.0, 1.0)
        assert style.alignment == TextAlignment.LEFT
        assert style.line_spacing == 1.2
        assert style.character_spacing == 0.0


class TestTextMesh:
    """Test text mesh functionality."""
    
    def test_mesh_creation(self):
        """Test text mesh initialization."""
        mesh = TextMesh()
        
        assert len(mesh.vertices) == 0
        assert len(mesh.indices) == 0
        assert mesh.vertex_count == 0
        assert mesh.index_count == 0
        
    def test_quad_addition(self):
        """Test adding quads to mesh."""
        mesh = TextMesh()
        
        # Add a quad
        mesh.add_quad(10, 20, 30, 40, 0.0, 0.0, 1.0, 1.0, (1.0, 1.0, 1.0, 1.0))
        
        assert len(mesh.vertices) == 4  # 4 vertices per quad
        assert len(mesh.indices) == 6   # 6 indices per quad (2 triangles)
        
        # Check vertex positions
        assert mesh.vertices[0].position == (10, 20, 0.0)      # Bottom-left
        assert mesh.vertices[1].position == (40, 20, 0.0)      # Bottom-right
        assert mesh.vertices[2].position == (40, 60, 0.0)      # Top-right
        assert mesh.vertices[3].position == (10, 60, 0.0)      # Top-left