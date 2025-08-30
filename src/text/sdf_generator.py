"""
Signed Distance Field (SDF) generator for high-quality text rendering.

This module provides SDF generation from glyph bitmaps for improved
text rendering quality at various scales and effects.
"""

import logging
from typing import Tuple, Optional
import numpy as np
from scipy.ndimage import distance_transform_edt


logger = logging.getLogger(__name__)


class SDFGenerator:
    """
    Generates signed distance fields from glyph bitmaps.
    
    SDF rendering provides better quality text at different scales
    and enables advanced effects like smooth outlines and shadows.
    """
    
    def __init__(self, spread: int = 8):
        """
        Initialize SDF generator.
        
        Args:
            spread: Distance field spread in pixels (higher = smoother but larger)
        """
        self.spread = spread
        
    def generate_sdf(self, bitmap: np.ndarray, padding: Optional[int] = None) -> np.ndarray:
        """
        Generate signed distance field from a glyph bitmap.
        
        Args:
            bitmap: Input glyph bitmap (0-255 grayscale)
            padding: Padding around the glyph (defaults to spread)
            
        Returns:
            SDF as float array with values in range [0, 1]
        """
        if padding is None:
            padding = self.spread
            
        # Ensure bitmap is in correct format
        if bitmap.dtype != np.uint8:
            bitmap = bitmap.astype(np.uint8)
            
        # Add padding around the bitmap
        padded_bitmap = np.pad(bitmap, padding, mode='constant', constant_values=0)
        
        # Convert to binary (threshold at 128)
        binary = padded_bitmap > 128
        
        # Calculate distance transforms
        inside_distance = distance_transform_edt(binary)
        outside_distance = distance_transform_edt(~binary)
        
        # Combine into signed distance field
        # Inside pixels get positive distance, outside pixels get negative distance
        sdf = np.where(binary, inside_distance, -outside_distance)
        
        # Normalize to [0, 1] range
        # Values > 0 are inside the glyph (should map to > 0.5)
        # Values < 0 are outside the glyph (should map to < 0.5)
        sdf_normalized = (sdf + self.spread) / (2 * self.spread)
        sdf_normalized = np.clip(sdf_normalized, 0.0, 1.0)
        
        return sdf_normalized.astype(np.float32)
        
    def generate_msdf(self, bitmap: np.ndarray, padding: Optional[int] = None) -> np.ndarray:
        """
        Generate multi-channel signed distance field (MSDF) for even better quality.
        
        Args:
            bitmap: Input glyph bitmap (0-255 grayscale)
            padding: Padding around the glyph
            
        Returns:
            MSDF as 3-channel float array (RGB channels contain different distance info)
        """
        if padding is None:
            padding = self.spread
            
        # For now, implement a simplified MSDF by using the same SDF in all channels
        # A full MSDF implementation would analyze glyph contours and generate
        # different distance fields for different edge orientations
        sdf = self.generate_sdf(bitmap, padding)
        
        # Create 3-channel MSDF (simplified version)
        msdf = np.stack([sdf, sdf, sdf], axis=-1)
        
        return msdf
        
    def calculate_optimal_size(self, original_size: Tuple[int, int], target_size: int) -> Tuple[int, int]:
        """
        Calculate optimal SDF texture size for a given glyph.
        
        Args:
            original_size: Original glyph bitmap size (width, height)
            target_size: Target maximum dimension
            
        Returns:
            Optimal SDF texture size (width, height)
        """
        width, height = original_size
        max_dim = max(width, height)
        
        if max_dim == 0:
            return (target_size, target_size)
            
        # Calculate scale factor
        scale = target_size / max_dim
        
        # Calculate new dimensions with padding
        new_width = int(width * scale) + 2 * self.spread
        new_height = int(height * scale) + 2 * self.spread
        
        return (new_width, new_height)
        
    def resize_bitmap_for_sdf(self, bitmap: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
        """
        Resize bitmap to optimal size for SDF generation.
        
        Args:
            bitmap: Input bitmap
            target_size: Target size (width, height)
            
        Returns:
            Resized bitmap
        """
        from PIL import Image
        
        # Convert to PIL Image for high-quality resizing
        if len(bitmap.shape) == 2:
            pil_image = Image.fromarray(bitmap, mode='L')
        else:
            pil_image = Image.fromarray(bitmap)
            
        # Resize with high-quality resampling
        resized = pil_image.resize(target_size, Image.Resampling.LANCZOS)
        
        return np.array(resized)


class SDFTextRenderer:
    """
    Text renderer that uses SDF textures for high-quality rendering.
    
    Provides improved text quality at different scales and enables
    advanced effects like smooth outlines and drop shadows.
    """
    
    def __init__(self, sdf_generator: SDFGenerator):
        self.sdf_generator = sdf_generator
        self._sdf_cache = {}  # Cache for generated SDFs
        
    def generate_glyph_sdf(self, glyph_bitmap: np.ndarray, glyph_id: int, 
                          cache: bool = True) -> np.ndarray:
        """
        Generate SDF for a glyph bitmap.
        
        Args:
            glyph_bitmap: Glyph bitmap data
            glyph_id: Unique identifier for caching
            cache: Whether to cache the result
            
        Returns:
            SDF texture data
        """
        if cache and glyph_id in self._sdf_cache:
            return self._sdf_cache[glyph_id]
            
        # Generate SDF
        sdf = self.sdf_generator.generate_sdf(glyph_bitmap)
        
        if cache:
            self._sdf_cache[glyph_id] = sdf
            
        return sdf
        
    def get_sdf_shader_uniforms(self, outline_width: float = 0.0, 
                               smoothing: float = 0.1) -> dict:
        """
        Get shader uniforms for SDF text rendering.
        
        Args:
            outline_width: Outline width (0.0 to 0.5)
            smoothing: Edge smoothing amount
            
        Returns:
            Dictionary of shader uniforms
        """
        return {
            'sdf_threshold': 0.5,
            'sdf_smoothing': smoothing,
            'sdf_outline_width': outline_width,
            'sdf_outline_threshold': 0.5 - outline_width
        }
        
    def get_sdf_fragment_shader(self) -> str:
        """
        Get fragment shader code for SDF text rendering.
        
        Returns:
            GLSL fragment shader source code
        """
        return """
        #version 330 core
        
        in vec2 TexCoord;
        in vec4 VertexColor;
        out vec4 FragColor;
        
        uniform sampler2D fontAtlas;
        uniform float sdf_threshold;
        uniform float sdf_smoothing;
        uniform float sdf_outline_width;
        uniform float sdf_outline_threshold;
        uniform vec4 outlineColor;
        uniform bool enableOutline;
        
        void main() {
            // Sample the SDF
            float sdf = texture(fontAtlas, TexCoord).r;
            
            // Calculate main text alpha
            float alpha = smoothstep(sdf_threshold - sdf_smoothing, 
                                   sdf_threshold + sdf_smoothing, sdf);
            
            vec4 finalColor = VertexColor;
            finalColor.a *= alpha;
            
            // Add outline if enabled
            if (enableOutline && sdf_outline_width > 0.0) {
                float outline_alpha = smoothstep(sdf_outline_threshold - sdf_smoothing,
                                               sdf_outline_threshold + sdf_smoothing, sdf);
                
                // Blend outline with main text
                if (alpha < 0.5 && outline_alpha > 0.1) {
                    finalColor = mix(outlineColor, finalColor, alpha);
                    finalColor.a = max(finalColor.a, outline_alpha * outlineColor.a);
                }
            }
            
            FragColor = finalColor;
        }
        """
        
    def clear_cache(self) -> None:
        """Clear the SDF cache."""
        self._sdf_cache.clear()
        logger.info("SDF cache cleared")
        
    def get_cache_size(self) -> int:
        """Get the number of cached SDFs."""
        return len(self._sdf_cache)


def create_sdf_atlas_from_glyphs(glyphs: dict, atlas_size: Tuple[int, int] = (1024, 1024),
                                sdf_generator: Optional[SDFGenerator] = None) -> Tuple[np.ndarray, dict]:
    """
    Create an SDF atlas from a collection of glyph bitmaps.
    
    Args:
        glyphs: Dictionary mapping glyph IDs to bitmap arrays
        atlas_size: Size of the output atlas texture
        sdf_generator: SDF generator instance (creates default if None)
        
    Returns:
        Tuple of (atlas_texture, glyph_coordinates)
    """
    if sdf_generator is None:
        sdf_generator = SDFGenerator()
        
    atlas_width, atlas_height = atlas_size
    atlas = np.zeros((atlas_height, atlas_width), dtype=np.float32)
    glyph_coords = {}
    
    # Simple packing algorithm (can be improved with better bin packing)
    current_x = 0
    current_y = 0
    row_height = 0
    
    for glyph_id, bitmap in glyphs.items():
        if bitmap.size == 0:
            continue
            
        # Generate SDF
        sdf = sdf_generator.generate_sdf(bitmap)
        sdf_height, sdf_width = sdf.shape
        
        # Check if we need to move to next row
        if current_x + sdf_width > atlas_width:
            current_x = 0
            current_y += row_height
            row_height = 0
            
        # Check if we have space
        if current_y + sdf_height > atlas_height:
            logger.warning(f"SDF atlas full, cannot add glyph {glyph_id}")
            continue
            
        # Copy SDF to atlas
        atlas[current_y:current_y + sdf_height, current_x:current_x + sdf_width] = sdf
        
        # Store coordinates (normalized)
        glyph_coords[glyph_id] = {
            'x': current_x / atlas_width,
            'y': current_y / atlas_height,
            'width': sdf_width / atlas_width,
            'height': sdf_height / atlas_height,
            'pixel_width': sdf_width,
            'pixel_height': sdf_height
        }
        
        # Update position
        current_x += sdf_width
        row_height = max(row_height, sdf_height)
        
    return atlas, glyph_coords