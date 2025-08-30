#!/usr/bin/env python3
"""
Direct test runner for text rendering tests.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import test classes
from tests.test_text_rendering import TestFontAtlas, TestFontManager, TestTextStyle, TestTextMesh

def run_tests():
    """Run text rendering tests directly."""
    print("Running Text Rendering Tests")
    print("=" * 40)
    
    # Test FontAtlas
    print("\n--- Testing FontAtlas ---")
    atlas_test = TestFontAtlas()
    
    try:
        atlas_test.test_atlas_creation()
        print("✓ test_atlas_creation")
    except Exception as e:
        print(f"✗ test_atlas_creation: {e}")
        
    try:
        atlas_test.test_glyph_addition()
        print("✓ test_glyph_addition")
    except Exception as e:
        print(f"✗ test_glyph_addition: {e}")
        
    try:
        atlas_test.test_texture_coordinates()
        print("✓ test_texture_coordinates")
    except Exception as e:
        print(f"✗ test_texture_coordinates: {e}")
        
    try:
        atlas_test.test_atlas_overflow()
        print("✓ test_atlas_overflow")
    except Exception as e:
        print(f"✗ test_atlas_overflow: {e}")
        
    try:
        atlas_test.test_row_wrapping()
        print("✓ test_row_wrapping")
    except Exception as e:
        print(f"✗ test_row_wrapping: {e}")
    
    # Test TextStyle
    print("\n--- Testing TextStyle ---")
    style_test = TestTextStyle()
    
    try:
        style_test.test_default_style()
        print("✓ test_default_style")
    except Exception as e:
        print(f"✗ test_default_style: {e}")
        
    try:
        style_test.test_style_with_effects()
        print("✓ test_style_with_effects")
    except Exception as e:
        print(f"✗ test_style_with_effects: {e}")
    
    # Test TextMesh
    print("\n--- Testing TextMesh ---")
    mesh_test = TestTextMesh()
    
    try:
        mesh_test.test_mesh_creation()
        print("✓ test_mesh_creation")
    except Exception as e:
        print(f"✗ test_mesh_creation: {e}")
        
    try:
        mesh_test.test_quad_addition()
        print("✓ test_quad_addition")
    except Exception as e:
        print(f"✗ test_quad_addition: {e}")
        
    try:
        mesh_test.test_multiple_quads()
        print("✓ test_multiple_quads")
    except Exception as e:
        print(f"✗ test_multiple_quads: {e}")
    
    print("\n" + "=" * 40)
    print("Text rendering tests completed!")

if __name__ == "__main__":
    run_tests()