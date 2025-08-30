#!/usr/bin/env python3
"""
Demo: 3D Text Transformation System

This demo showcases the 3D transformation capabilities including:
- 3D rotations and transformations
- Text extrusion with depth
- Perspective and orthographic projections
- Animated camera movements
- Matrix calculations for 3D positioning
"""

import sys
import numpy as np
import time
import math
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.effects.transform_3d import (
    Transform3D, Transform3DParams, CameraAnimation, CameraMovement, ProjectionType
)


def demo_basic_transformations():
    """Demonstrate basic 3D transformations."""
    print("=== Basic 3D Transformations Demo ===")
    
    transform = Transform3D()
    
    # Test rotation matrices
    print("\n1. Rotation Matrices:")
    
    # 90-degree rotation around X-axis
    rot_x = transform.create_rotation_matrix_x(90.0)
    point = np.array([0, 1, 0, 1])
    rotated = rot_x @ point
    print(f"Point (0,1,0) rotated 90° around X-axis: ({rotated[0]:.3f}, {rotated[1]:.3f}, {rotated[2]:.3f})")
    
    # 90-degree rotation around Y-axis
    rot_y = transform.create_rotation_matrix_y(90.0)
    point = np.array([1, 0, 0, 1])
    rotated = rot_y @ point
    print(f"Point (1,0,0) rotated 90° around Y-axis: ({rotated[0]:.3f}, {rotated[1]:.3f}, {rotated[2]:.3f})")
    
    # 90-degree rotation around Z-axis
    rot_z = transform.create_rotation_matrix_z(90.0)
    point = np.array([1, 0, 0, 1])
    rotated = rot_z @ point
    print(f"Point (1,0,0) rotated 90° around Z-axis: ({rotated[0]:.3f}, {rotated[1]:.3f}, {rotated[2]:.3f})")
    
    # Test combined transformations
    print("\n2. Combined Transformations:")
    params = Transform3DParams(
        rotation_x=45.0,
        rotation_y=30.0,
        translation_x=2.0,
        translation_y=1.0,
        scale_x=1.5,
        scale_y=1.5
    )
    
    model_matrix = transform.create_model_matrix(params)
    test_point = np.array([1, 1, 0, 1])
    transformed = model_matrix @ test_point
    print(f"Point (1,1,0) after scale(1.5,1.5,1), rotate(45°,30°,0°), translate(2,1,0):")
    print(f"  Result: ({transformed[0]:.3f}, {transformed[1]:.3f}, {transformed[2]:.3f})")


def demo_projection_matrices():
    """Demonstrate projection matrix calculations."""
    print("\n=== Projection Matrices Demo ===")
    
    transform = Transform3D()
    
    # Perspective projection
    print("\n1. Perspective Projection:")
    perspective = transform.create_perspective_matrix(45.0, 16/9, 0.1, 100.0)
    
    # Test points at different depths
    points = [
        np.array([0, 0, -1, 1]),   # 1 unit away
        np.array([0, 0, -5, 1]),   # 5 units away
        np.array([1, 1, -2, 1]),   # Off-center, 2 units away
    ]
    
    for i, point in enumerate(points):
        projected = perspective @ point
        if projected[3] != 0:
            ndc = projected / projected[3]
            print(f"Point {i+1} ({point[0]}, {point[1]}, {point[2]}) -> NDC ({ndc[0]:.3f}, {ndc[1]:.3f}, {ndc[2]:.3f})")
    
    # Orthographic projection
    print("\n2. Orthographic Projection:")
    orthographic = transform.create_orthographic_matrix(-2, 2, -2, 2, 0.1, 100.0)
    
    for i, point in enumerate(points):
        projected = orthographic @ point
        print(f"Point {i+1} ({point[0]}, {point[1]}, {point[2]}) -> NDC ({projected[0]:.3f}, {projected[1]:.3f}, {projected[2]:.3f})")


def demo_camera_system():
    """Demonstrate camera positioning and look-at matrix."""
    print("\n=== Camera System Demo ===")
    
    transform = Transform3D()
    
    # Different camera positions
    camera_positions = [
        (0, 0, 5, "Front view"),
        (5, 0, 0, "Right side view"),
        (0, 5, 0, "Top view"),
        (3, 3, 3, "Diagonal view"),
    ]
    
    target = np.array([0, 0, 0, 1])  # Looking at origin
    
    for cam_x, cam_y, cam_z, description in camera_positions:
        view_matrix = transform.create_look_at_matrix(
            cam_x, cam_y, cam_z,  # camera position
            0, 0, 0,              # target
            0, 1, 0               # up vector
        )
        
        # Transform the origin to see where it appears in view space
        view_pos = view_matrix @ target
        print(f"{description}: Camera at ({cam_x}, {cam_y}, {cam_z})")
        print(f"  Origin in view space: ({view_pos[0]:.3f}, {view_pos[1]:.3f}, {view_pos[2]:.3f})")


def demo_text_extrusion():
    """Demonstrate 3D text extrusion."""
    print("\n=== Text Extrusion Demo ===")
    
    transform = Transform3D()
    
    # Simple letter "L" shape
    letter_l_vertices = np.array([
        [0, 0],    # Bottom-left
        [0, 3],    # Top-left
        [0.5, 3],  # Top-left inner
        [0.5, 0.5], # Inner corner
        [2, 0.5],  # Bottom-right inner
        [2, 0],    # Bottom-right
    ])
    
    print(f"Original 2D vertices for letter 'L': {len(letter_l_vertices)} points")
    
    # Generate 3D extruded mesh
    vertices_3d, indices = transform.generate_extrusion_vertices(
        letter_l_vertices, 
        extrusion_depth=1.0
    )
    
    print(f"3D extruded mesh: {len(vertices_3d)} vertices, {len(indices)} indices")
    print(f"Front face vertices (z=0):")
    for i in range(len(letter_l_vertices)):
        v = vertices_3d[i]
        print(f"  Vertex {i}: ({v[0]:.1f}, {v[1]:.1f}, {v[2]:.1f})")
    
    print(f"Back face vertices (z=-1.0):")
    for i in range(len(letter_l_vertices)):
        v = vertices_3d[i + len(letter_l_vertices)]
        print(f"  Vertex {i}: ({v[0]:.1f}, {v[1]:.1f}, {v[2]:.1f})")


def demo_camera_animations():
    """Demonstrate animated camera movements."""
    print("\n=== Camera Animation Demo ===")
    
    transform = Transform3D()
    base_params = Transform3DParams()
    
    # Orbital animation
    print("\n1. Orbital Camera Animation:")
    orbit_animation = CameraAnimation(
        movement_type=CameraMovement.ORBIT,
        duration=4.0,
        start_time=0.0,
        orbit_radius=5.0,
        orbit_speed=1.0
    )
    
    for t in [0.0, 1.0, 2.0, 3.0, 4.0]:
        animated_params = transform.animate_camera(orbit_animation, t, base_params)
        print(f"  Time {t:.1f}s: Camera at ({animated_params.camera_x:.2f}, {animated_params.camera_y:.2f}, {animated_params.camera_z:.2f})")
    
    # Zoom animation
    print("\n2. Zoom Camera Animation:")
    zoom_animation = CameraAnimation(
        movement_type=CameraMovement.ZOOM,
        duration=2.0,
        start_time=0.0,
        zoom_start=10.0,
        zoom_end=2.0
    )
    
    for t in [0.0, 0.5, 1.0, 1.5, 2.0]:
        animated_params = transform.animate_camera(zoom_animation, t, base_params)
        print(f"  Time {t:.1f}s: Camera Z = {animated_params.camera_z:.2f}")
    
    # Pan animation
    print("\n3. Pan Camera Animation:")
    pan_animation = CameraAnimation(
        movement_type=CameraMovement.PAN,
        duration=3.0,
        start_time=0.0,
        pan_start_x=-2.0,
        pan_end_x=2.0,
        pan_start_y=0.0,
        pan_end_y=1.0
    )
    
    for t in [0.0, 1.0, 2.0, 3.0]:
        animated_params = transform.animate_camera(pan_animation, t, base_params)
        print(f"  Time {t:.1f}s: Camera at ({animated_params.camera_x:.2f}, {animated_params.camera_y:.2f})")


def demo_mvp_pipeline():
    """Demonstrate complete Model-View-Projection pipeline."""
    print("\n=== Complete MVP Pipeline Demo ===")
    
    transform = Transform3D()
    
    # Create a text element with 3D transformation
    params = Transform3DParams(
        rotation_x=30.0,
        rotation_y=45.0,
        translation_x=1.0,
        translation_y=0.5,
        scale_x=1.2,
        scale_y=1.2,
        camera_x=3.0,
        camera_y=2.0,
        camera_z=5.0,
        field_of_view=60.0
    )
    
    # Generate MVP matrix
    mvp_matrix = transform.create_mvp_matrix(params, ProjectionType.PERSPECTIVE)
    
    print("Text transformation parameters:")
    print(f"  Rotation: ({params.rotation_x}°, {params.rotation_y}°, {params.rotation_z}°)")
    print(f"  Translation: ({params.translation_x}, {params.translation_y}, {params.translation_z})")
    print(f"  Scale: ({params.scale_x}, {params.scale_y}, {params.scale_z})")
    print(f"  Camera: ({params.camera_x}, {params.camera_y}, {params.camera_z})")
    
    # Test points representing text corners
    text_corners = [
        np.array([0, 0, 0]),    # Bottom-left
        np.array([2, 0, 0]),    # Bottom-right
        np.array([2, 1, 0]),    # Top-right
        np.array([0, 1, 0]),    # Top-left
    ]
    
    print("\nText corner projections to screen:")
    for i, corner in enumerate(text_corners):
        screen_x, screen_y = transform.project_to_screen(corner, mvp_matrix)
        print(f"  Corner {i+1}: 3D({corner[0]}, {corner[1]}, {corner[2]}) -> Screen({screen_x:.1f}, {screen_y:.1f})")


def demo_depth_sorting():
    """Demonstrate depth sorting for proper rendering order."""
    print("\n=== Depth Sorting Demo ===")
    
    transform = Transform3D()
    
    # Mock text elements at different depths
    class MockTextElement:
        def __init__(self, name, x, y, z):
            self.name = name
            self.x = x
            self.y = y
            self.z = z
        
        def __repr__(self):
            return f"{self.name}({self.x}, {self.y}, {self.z})"
    
    text_elements = [
        MockTextElement("Text A", 0, 0, -2),   # Middle depth
        MockTextElement("Text B", 1, 0, -1),   # Closest
        MockTextElement("Text C", -1, 0, -5),  # Farthest
        MockTextElement("Text D", 0, 1, -3),   # Far
    ]
    
    params = Transform3DParams(camera_z=0.0)
    mvp_matrix = transform.create_mvp_matrix(params)
    
    print("Original text elements:")
    for element in text_elements:
        print(f"  {element}")
    
    sorted_elements = transform.calculate_text_depth_sorting(text_elements, mvp_matrix)
    
    print("\nDepth-sorted elements (back to front):")
    for i, element in enumerate(sorted_elements):
        print(f"  {i+1}. {element}")


def demo_performance_test():
    """Demonstrate performance of matrix calculations."""
    print("\n=== Performance Test ===")
    
    transform = Transform3D()
    
    # Test matrix multiplication performance
    num_iterations = 10000
    
    params = Transform3DParams(
        rotation_x=45.0,
        rotation_y=30.0,
        rotation_z=15.0,
        translation_x=1.0,
        translation_y=2.0,
        translation_z=3.0
    )
    
    start_time = time.time()
    
    for _ in range(num_iterations):
        mvp_matrix = transform.create_mvp_matrix(params)
        # Transform a point
        point = np.array([1, 1, 1])
        transformed = transform.transform_point(point, mvp_matrix)
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    print(f"Performance test: {num_iterations} MVP matrix calculations + point transformations")
    print(f"Total time: {elapsed:.3f} seconds")
    print(f"Average time per operation: {(elapsed/num_iterations)*1000:.3f} ms")
    print(f"Operations per second: {num_iterations/elapsed:.0f}")


def main():
    """Run all 3D transformation demos."""
    print("3D Text Transformation System Demo")
    print("=" * 50)
    
    try:
        demo_basic_transformations()
        demo_projection_matrices()
        demo_camera_system()
        demo_text_extrusion()
        demo_camera_animations()
        demo_mvp_pipeline()
        demo_depth_sorting()
        demo_performance_test()
        
        print("\n" + "=" * 50)
        print("All demos completed successfully!")
        print("\nKey features demonstrated:")
        print("✓ 3D rotation matrices (X, Y, Z axes)")
        print("✓ Translation and scaling transformations")
        print("✓ Perspective and orthographic projections")
        print("✓ Camera positioning and look-at matrices")
        print("✓ Text extrusion for 3D depth effects")
        print("✓ Animated camera movements (orbit, zoom, pan)")
        print("✓ Complete MVP pipeline for 3D rendering")
        print("✓ Depth sorting for proper rendering order")
        print("✓ Performance optimization for real-time use")
        
    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())