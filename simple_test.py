#!/usr/bin/env python3
"""
Simple test runner to verify text rendering functionality.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import and test directly
from src.text.font_manager import FontAtlas, GlyphMetrics
from src.text.text_renderer import TextStyle, TextAlignment, TextMesh
import numpy as np

def test_font_atlas():
    """Test font atlas functionality."""
    print("Testing FontAtlas...")
    
    # Test creation
    atlas = FontAtlas(font_size=48, atlas_width=512, atlas_height=512, create_texture=False)
    assert atlas.font_size == 48
    assert atlas.atlas_width == 512
    assert atlas.atlas_height == 512
    print("✓ Atlas creation")
    
    # Test glyph addition
    glyph_bitmap = np.ones((20, 15), dtype=np.uint8) * 255
    metrics = (15, 20, 2, 18, 16)
    success = atlas.add_glyph(ord('A'), glyph_bitmap, metrics)
    assert success
    assert ord('A') in atlas.glyphs
    print("✓ Glyph addition")
    
    # Test texture coordinates
    coords = atlas.get_texture_coords(ord('A'))
    assert coords is not None
    print("✓ Texture coordinates")

def test_text_style():
    """Test text style functionality."""
    print("Testing TextStyle...")
    
    style = TextStyle(font_path="test.ttf")
    assert style.font_path == "test.ttf"
    assert style.font_size == 48
    assert style.color == (1.0, 1.0, 1.0, 1.0)
    print("✓ Text style creation")

def test_text_mesh():
    """Test text mesh functionality."""
    print("Testing TextMesh...")
    
    mesh = TextMesh()
    assert len(mesh.vertices) == 0
    assert len(mesh.indices) == 0
    print("✓ Mesh creation")
    
    # Add a quad
    mesh.add_quad(10, 20, 30, 40, 0.0, 0.0, 1.0, 1.0, (1.0, 1.0, 1.0, 1.0))
    assert len(mesh.vertices) == 4
    assert len(mesh.indices) == 6
    print("✓ Quad addition")

if __name__ == "__main__":
    print("Running Text Rendering Tests")
    print("=" * 30)
    
    try:
        test_font_atlas()
        test_text_style()
        test_text_mesh()
        print("\n✓ All tests passed!")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()