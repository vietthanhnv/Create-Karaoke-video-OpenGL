#!/usr/bin/env python3
"""
Simple test to verify FreeType integration is working correctly.
"""

import sys
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    import freetype
    print("✓ FreeType-py imported successfully")
except ImportError as e:
    print(f"✗ Failed to import FreeType-py: {e}")
    sys.exit(1)

try:
    from src.text.font_manager import FontManager, FontAtlas
    from src.text.text_renderer import TextRenderer, TextStyle
    print("✓ Text rendering modules imported successfully")
except ImportError as e:
    print(f"✗ Failed to import text modules: {e}")
    sys.exit(1)

def test_font_manager():
    """Test basic font manager functionality."""
    print("\n--- Testing FontManager ---")
    
    manager = FontManager()
    
    # Test default font loading
    success = manager.load_default_font(48)
    if success:
        print("✓ Default font loaded successfully")
    else:
        print("✗ Failed to load default font")
        return False
        
    # Test glyph rendering for basic ASCII
    test_chars = "Hello, World! 123"
    available_fonts = manager.get_available_fonts()
    if available_fonts:
        font_key = available_fonts[0]
        try:
            parts = font_key.split(':')
            if len(parts) >= 2:
                font_path = ':'.join(parts[:-1])  # Handle Windows paths with colons
                font_size = int(parts[-1])
            else:
                print(f"✗ Invalid font key format: {font_key}")
                return False
                
            success = manager.render_text_glyphs(font_path, font_size, test_chars)
            if success:
                print(f"✓ Rendered glyphs for: {test_chars}")
            else:
                print(f"✗ Failed to render glyphs for: {test_chars}")
                return False
                
            # Test text metrics
            width, height = manager.get_text_metrics(font_path, font_size, test_chars)
            print(f"✓ Text metrics: {width}x{height} pixels")
        except Exception as e:
            print(f"✗ Error processing font {font_key}: {e}")
            return False
    else:
        print("✗ No fonts available for testing")
        return False
        
    return True

def test_unicode_support():
    """Test Unicode character support."""
    print("\n--- Testing Unicode Support ---")
    
    manager = FontManager()
    
    if not manager.load_default_font(48):
        print("✗ Cannot test Unicode - no font loaded")
        return False
        
    # Test various Unicode characters
    unicode_tests = [
        ("Basic Latin", "Hello World"),
        ("Latin Extended", "café résumé naïve"),
        ("Symbols", "★☆♪♫♬"),
        ("Emoji", "😀😃😄"),  # May not render depending on font
        ("CJK", "你好世界"),   # Chinese characters
        ("Arabic", "مرحبا"),   # Arabic text
    ]
    
    for test_name, test_text in unicode_tests:
        try:
            available_fonts = manager.get_available_fonts()
            if available_fonts:
                font_key = available_fonts[0]
                parts = font_key.split(':')
                if len(parts) >= 2:
                    font_path = ':'.join(parts[:-1])  # Handle Windows paths with colons
                    font_size = int(parts[-1])
                    
                    success = manager.render_text_glyphs(font_path, font_size, test_text)
                    if success:
                        width, height = manager.get_text_metrics(font_path, font_size, test_text)
                        print(f"✓ {test_name}: '{test_text}' -> {width}x{height}")
                    else:
                        print(f"⚠ {test_name}: '{test_text}' -> Some glyphs missing")
                else:
                    print(f"✗ {test_name}: Invalid font key format")
            else:
                print(f"✗ {test_name}: No fonts available")
        except Exception as e:
            print(f"✗ {test_name}: '{test_text}' -> Error: {e}")
            
    return True

def test_atlas_management():
    """Test font atlas texture management."""
    print("\n--- Testing Atlas Management ---")
    
    # Create atlas without OpenGL texture
    atlas = FontAtlas(font_size=48, atlas_width=512, atlas_height=512, create_texture=False)
    
    # Test adding multiple glyphs
    test_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    
    for i, char in enumerate(test_chars):
        # Create mock glyph bitmap
        glyph_size = 20 + (i % 10)  # Varying sizes
        bitmap = np.random.randint(0, 255, (glyph_size, glyph_size), dtype=np.uint8)
        metrics = (glyph_size, glyph_size, 0, glyph_size, glyph_size + 2)
        
        success = atlas.add_glyph(ord(char), bitmap, metrics)
        if not success:
            print(f"⚠ Atlas full at character '{char}' (index {i})")
            break
            
    print(f"✓ Added {len(atlas.glyphs)} glyphs to atlas")
    
    # Test texture coordinate calculation
    for char in "ABC":
        coords = atlas.get_texture_coords(ord(char))
        if coords:
            print(f"✓ Texture coords for '{char}': {coords}")
        else:
            print(f"✗ No texture coords for '{char}'")
            
    return True

if __name__ == "__main__":
    print("Testing FreeType Integration for Karaoke Subtitle Creator")
    print("=" * 60)
    
    success = True
    
    success &= test_font_manager()
    success &= test_unicode_support()
    success &= test_atlas_management()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ All tests passed! FreeType integration is working.")
    else:
        print("✗ Some tests failed. Check the output above.")
        
    print("\nNext steps:")
    print("- Run the full test suite: python -m pytest tests/")
    print("- Test with OpenGL context: python demo_text_rendering.py")