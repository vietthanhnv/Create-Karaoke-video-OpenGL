#!/usr/bin/env python3
"""
Test SDF (Signed Distance Field) integration for text rendering.
"""

import sys
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from src.text.sdf_generator import SDFGenerator, SDFTextRenderer, create_sdf_atlas_from_glyphs
    print("✓ SDF modules imported successfully")
except ImportError as e:
    print(f"✗ Failed to import SDF modules: {e}")
    sys.exit(1)

def test_sdf_generation():
    """Test SDF generation from bitmap."""
    print("\n--- Testing SDF Generation ---")
    
    generator = SDFGenerator(spread=8)
    
    # Create a simple test bitmap (circle)
    size = 32
    bitmap = np.zeros((size, size), dtype=np.uint8)
    center = size // 2
    radius = size // 4
    
    # Draw a filled circle
    for y in range(size):
        for x in range(size):
            dist = np.sqrt((x - center)**2 + (y - center)**2)
            if dist <= radius:
                bitmap[y, x] = 255
                
    print(f"✓ Created test bitmap: {bitmap.shape}")
    
    # Generate SDF
    sdf = generator.generate_sdf(bitmap)
    
    print(f"✓ Generated SDF: {sdf.shape}, dtype: {sdf.dtype}")
    print(f"✓ SDF value range: {sdf.min():.3f} to {sdf.max():.3f}")
    
    # Check that SDF has expected properties
    assert sdf.dtype == np.float32
    assert 0.0 <= sdf.min() <= sdf.max() <= 1.0
    
    # Center should be close to 1.0 (inside) - account for padding
    padding = generator.spread
    center_value = sdf[center + padding, center + padding]
    print(f"✓ Center SDF value: {center_value:.3f} (should be > 0.5)")
    assert center_value > 0.5
    
    # Corners should be close to 0.0 (outside)
    corner_value = sdf[0, 0]
    print(f"✓ Corner SDF value: {corner_value:.3f} (should be < 0.5)")
    assert corner_value < 0.5
    
    return True

def test_sdf_atlas_creation():
    """Test SDF atlas creation from multiple glyphs."""
    print("\n--- Testing SDF Atlas Creation ---")
    
    # Create test glyphs (simple shapes)
    glyphs = {}
    
    # Square glyph
    square = np.zeros((20, 20), dtype=np.uint8)
    square[5:15, 5:15] = 255
    glyphs[ord('A')] = square
    
    # Circle glyph
    circle = np.zeros((20, 20), dtype=np.uint8)
    center = 10
    radius = 7
    for y in range(20):
        for x in range(20):
            if np.sqrt((x - center)**2 + (y - center)**2) <= radius:
                circle[y, x] = 255
    glyphs[ord('B')] = circle
    
    # Triangle glyph
    triangle = np.zeros((20, 20), dtype=np.uint8)
    for y in range(20):
        for x in range(20):
            if y > 5 and x > y - 5 and x < 25 - y:
                triangle[y, x] = 255
    glyphs[ord('C')] = triangle
    
    print(f"✓ Created {len(glyphs)} test glyphs")
    
    # Create SDF atlas
    atlas, coords = create_sdf_atlas_from_glyphs(glyphs, atlas_size=(256, 256))
    
    print(f"✓ Created SDF atlas: {atlas.shape}, dtype: {atlas.dtype}")
    print(f"✓ Glyph coordinates: {len(coords)} entries")
    
    # Verify atlas properties
    assert atlas.dtype == np.float32
    assert atlas.shape == (256, 256)
    assert len(coords) == len(glyphs)
    
    # Check that all glyphs have coordinates
    for glyph_id in glyphs.keys():
        assert glyph_id in coords
        coord = coords[glyph_id]
        assert 0.0 <= coord['x'] <= 1.0
        assert 0.0 <= coord['y'] <= 1.0
        assert coord['width'] > 0
        assert coord['height'] > 0
        print(f"✓ Glyph {chr(glyph_id)}: {coord['width']:.3f}x{coord['height']:.3f}")
    
    return True

def test_sdf_text_renderer():
    """Test SDF text renderer functionality."""
    print("\n--- Testing SDF Text Renderer ---")
    
    generator = SDFGenerator(spread=4)
    renderer = SDFTextRenderer(generator)
    
    # Test shader uniforms
    uniforms = renderer.get_sdf_shader_uniforms(outline_width=0.1, smoothing=0.05)
    
    print(f"✓ SDF shader uniforms: {len(uniforms)} entries")
    assert 'sdf_threshold' in uniforms
    assert 'sdf_smoothing' in uniforms
    assert 'sdf_outline_width' in uniforms
    
    # Test shader code generation
    shader_code = renderer.get_sdf_fragment_shader()
    
    print(f"✓ Generated SDF fragment shader: {len(shader_code)} characters")
    assert '#version 330 core' in shader_code
    assert 'smoothstep' in shader_code
    assert 'sdf_threshold' in shader_code
    
    # Test glyph SDF generation
    test_bitmap = np.random.randint(0, 255, (16, 16), dtype=np.uint8)
    sdf = renderer.generate_glyph_sdf(test_bitmap, glyph_id=65)  # 'A'
    
    print(f"✓ Generated glyph SDF: {sdf.shape}")
    assert sdf.dtype == np.float32
    
    # Test caching
    cache_size = renderer.get_cache_size()
    print(f"✓ SDF cache size: {cache_size}")
    assert cache_size == 1  # Should have cached one glyph
    
    return True

def test_sdf_quality_metrics():
    """Test SDF quality at different scales."""
    print("\n--- Testing SDF Quality Metrics ---")
    
    generator = SDFGenerator(spread=8)
    
    # Create a test glyph with sharp edges
    size = 64
    bitmap = np.zeros((size, size), dtype=np.uint8)
    
    # Create a letter-like shape
    bitmap[10:54, 10:20] = 255  # Vertical stroke
    bitmap[10:20, 10:40] = 255  # Top horizontal
    bitmap[30:40, 10:35] = 255  # Middle horizontal
    bitmap[44:54, 10:40] = 255  # Bottom horizontal
    
    print(f"✓ Created test letter bitmap: {bitmap.shape}")
    
    # Generate SDF
    sdf = generator.generate_sdf(bitmap)
    
    # Test edge sharpness (gradient should be smooth)
    # Find edge pixels (around 0.5 threshold)
    edge_mask = np.abs(sdf - 0.5) < 0.1
    edge_pixels = np.sum(edge_mask)
    
    print(f"✓ Edge pixels found: {edge_pixels}")
    assert edge_pixels > 0  # Should have some edge pixels
    
    # Test distance field properties
    # Values should transition smoothly from 0 to 1
    gradient_x = np.gradient(sdf, axis=1)
    gradient_y = np.gradient(sdf, axis=0)
    gradient_magnitude = np.sqrt(gradient_x**2 + gradient_y**2)
    
    max_gradient = np.max(gradient_magnitude)
    print(f"✓ Maximum gradient magnitude: {max_gradient:.3f}")
    
    # Gradient should be reasonable (not too steep)
    assert max_gradient < 1.0  # Should be smooth
    
    return True

if __name__ == "__main__":
    print("Testing SDF Integration for Text Rendering")
    print("=" * 50)
    
    success = True
    
    try:
        success &= test_sdf_generation()
        success &= test_sdf_atlas_creation()
        success &= test_sdf_text_renderer()
        success &= test_sdf_quality_metrics()
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✓ All SDF tests passed! Enhanced text rendering is ready.")
    else:
        print("✗ Some SDF tests failed. Check the output above.")
        
    print("\nSDF Features tested:")
    print("- Signed distance field generation from bitmaps")
    print("- Multi-glyph SDF atlas creation")
    print("- SDF shader uniform management")
    print("- Quality metrics and edge smoothness")
    print("- Caching system for performance")