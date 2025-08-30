#!/usr/bin/env python3
"""
Debug SDF generation to understand the issue.
"""

import sys
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.text.sdf_generator import SDFGenerator

def debug_sdf_generation():
    """Debug SDF generation step by step."""
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
                
    print(f"Original bitmap shape: {bitmap.shape}")
    print(f"Center pixel value: {bitmap[center, center]}")
    print(f"Corner pixel value: {bitmap[0, 0]}")
    
    # Add padding
    padding = generator.spread
    padded_bitmap = np.pad(bitmap, padding, mode='constant', constant_values=0)
    print(f"Padded bitmap shape: {padded_bitmap.shape}")
    
    # Convert to binary
    binary = padded_bitmap > 128
    print(f"Binary shape: {binary.shape}")
    print(f"Binary center value: {binary[center + padding, center + padding]}")
    print(f"Binary corner value: {binary[padding, padding]}")
    
    # Calculate distance transforms
    from scipy.ndimage import distance_transform_edt
    inside_distance = distance_transform_edt(binary)
    outside_distance = distance_transform_edt(~binary)
    
    print(f"Inside distance at center: {inside_distance[center + padding, center + padding]}")
    print(f"Outside distance at center: {outside_distance[center + padding, center + padding]}")
    print(f"Inside distance at corner: {inside_distance[padding, padding]}")
    print(f"Outside distance at corner: {outside_distance[padding, padding]}")
    
    # Combine into signed distance field
    sdf = np.where(binary, inside_distance, -outside_distance)
    
    print(f"Raw SDF at center: {sdf[center + padding, center + padding]}")
    print(f"Raw SDF at corner: {sdf[padding, padding]}")
    print(f"Raw SDF range: {sdf.min()} to {sdf.max()}")
    
    # Normalize
    sdf_normalized = (sdf + generator.spread) / (2 * generator.spread)
    sdf_normalized = np.clip(sdf_normalized, 0.0, 1.0)
    
    print(f"Normalized SDF at center: {sdf_normalized[center + padding, center + padding]}")
    print(f"Normalized SDF at corner: {sdf_normalized[padding, padding]}")
    print(f"Normalized SDF range: {sdf_normalized.min()} to {sdf_normalized.max()}")
    
    # The issue might be that the center is too close to the edge
    # Let's check the actual distance from center to edge
    actual_distance_to_edge = radius
    print(f"Actual distance from center to edge: {actual_distance_to_edge}")
    print(f"Spread parameter: {generator.spread}")
    
    if actual_distance_to_edge < generator.spread:
        print("Issue: The shape is smaller than the spread parameter!")
        print("This means the center is closer to the edge than the spread distance.")
        print("Solution: Use a smaller spread or larger test shape.")

if __name__ == "__main__":
    debug_sdf_generation()