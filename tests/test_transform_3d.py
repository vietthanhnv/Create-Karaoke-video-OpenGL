"""
Tests for 3D Text Transformation System
"""

import pytest
import numpy as np
import math
from src.effects.transform_3d import (
    Transform3D, Transform3DParams, CameraAnimation, CameraMovement, ProjectionType
)


class TestTransform3D:
    """Test cases for Transform3D class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.transform = Transform3D()
        self.default_params = Transform3DParams()
    
    def test_initialization(self):
        """Test Transform3D initialization."""
        assert self.transform.viewport_width == 1920
        assert self.transform.viewport_height == 1080
        assert abs(self.transform.aspect_ratio - (1920/1080)) < 1e-6
    
    def test_set_viewport(self):
        """Test viewport setting."""
        self.transform.set_viewport(800, 600)
        assert self.transform.viewport_width == 800
        assert self.transform.viewport_height == 600
        assert abs(self.transform.aspect_ratio - (800/600)) < 1e-6
    
    def test_rotation_matrix_x(self):
        """Test X-axis rotation matrix creation."""
        matrix = self.transform.create_rotation_matrix_x(90.0)
        
        # Test that it's a valid rotation matrix
        assert matrix.shape == (4, 4)
        assert abs(np.linalg.det(matrix[:3, :3]) - 1.0) < 1e-6
        
        # Test 90-degree rotation around X-axis
        # Point (0, 1, 0) should become (0, 0, 1)
        point = np.array([0, 1, 0, 1])
        rotated = matrix @ point
        expected = np.array([0, 0, 1, 1])
        np.testing.assert_allclose(rotated, expected, atol=1e-6)
    
    def test_rotation_matrix_y(self):
        """Test Y-axis rotation matrix creation."""
        matrix = self.transform.create_rotation_matrix_y(90.0)
        
        # Test 90-degree rotation around Y-axis
        # Point (1, 0, 0) should become (0, 0, -1)
        point = np.array([1, 0, 0, 1])
        rotated = matrix @ point
        expected = np.array([0, 0, -1, 1])
        np.testing.assert_allclose(rotated, expected, atol=1e-6)
    
    def test_rotation_matrix_z(self):
        """Test Z-axis rotation matrix creation."""
        matrix = self.transform.create_rotation_matrix_z(90.0)
        
        # Test 90-degree rotation around Z-axis
        # Point (1, 0, 0) should become (0, 1, 0)
        point = np.array([1, 0, 0, 1])
        rotated = matrix @ point
        expected = np.array([0, 1, 0, 1])
        np.testing.assert_allclose(rotated, expected, atol=1e-6)
    
    def test_translation_matrix(self):
        """Test translation matrix creation."""
        matrix = self.transform.create_translation_matrix(2.0, 3.0, 4.0)
        
        # Test translation
        point = np.array([1, 1, 1, 1])
        translated = matrix @ point
        expected = np.array([3, 4, 5, 1])
        np.testing.assert_allclose(translated, expected, atol=1e-6)
    
    def test_scale_matrix(self):
        """Test scale matrix creation."""
        matrix = self.transform.create_scale_matrix(2.0, 3.0, 4.0)
        
        # Test scaling
        point = np.array([1, 1, 1, 1])
        scaled = matrix @ point
        expected = np.array([2, 3, 4, 1])
        np.testing.assert_allclose(scaled, expected, atol=1e-6)
    
    def test_perspective_matrix(self):
        """Test perspective projection matrix creation."""
        matrix = self.transform.create_perspective_matrix(45.0, 16/9, 0.1, 100.0)
        
        # Test matrix properties
        assert matrix.shape == (4, 4)
        assert matrix[3, 2] == -1.0  # Perspective projection marker
        
        # Test that points in front of camera project correctly
        point = np.array([0, 0, -1, 1])  # Point 1 unit in front
        projected = matrix @ point
        # After perspective divide, should be at origin
        if projected[3] != 0:
            projected = projected / projected[3]
        assert abs(projected[0]) < 1e-6
        assert abs(projected[1]) < 1e-6
    
    def test_orthographic_matrix(self):
        """Test orthographic projection matrix creation."""
        matrix = self.transform.create_orthographic_matrix(-1, 1, -1, 1, 0.1, 100.0)
        
        # Test matrix properties
        assert matrix.shape == (4, 4)
        assert matrix[3, 3] == 1.0  # Orthographic projection marker
        
        # Test that points map correctly
        point = np.array([0.5, 0.5, -1, 1])
        projected = matrix @ point
        assert abs(projected[0] - 0.5) < 1e-6
        assert abs(projected[1] - 0.5) < 1e-6
    
    def test_look_at_matrix(self):
        """Test look-at matrix creation."""
        # Camera at (0, 0, 5) looking at origin
        matrix = self.transform.create_look_at_matrix(
            0, 0, 5,  # eye
            0, 0, 0,  # target
            0, 1, 0   # up
        )
        
        # Test that the origin transforms to (0, 0, -5) in view space
        origin = np.array([0, 0, 0, 1])
        view_pos = matrix @ origin
        expected = np.array([0, 0, -5, 1])
        np.testing.assert_allclose(view_pos, expected, atol=1e-6)
    
    def test_model_matrix_creation(self):
        """Test model matrix creation from parameters."""
        params = Transform3DParams(
            rotation_x=90.0,
            translation_x=2.0,
            scale_x=2.0
        )
        
        matrix = self.transform.create_model_matrix(params)
        
        # Test that transformations are applied in correct order
        # Scale, then rotate, then translate
        point = np.array([1, 0, 0, 1])
        transformed = matrix @ point
        
        # After scale: (2, 0, 0)
        # After X rotation 90°: (2, 0, 0) -> (2, 0, 0) (no change for X-axis point)
        # After translation: (2, 0, 0) -> (4, 0, 0)
        expected = np.array([4, 0, 0, 1])
        np.testing.assert_allclose(transformed, expected, atol=1e-6)
    
    def test_mvp_matrix_creation(self):
        """Test complete MVP matrix creation."""
        params = Transform3DParams(
            camera_z=5.0,
            field_of_view=45.0
        )
        
        mvp_matrix = self.transform.create_mvp_matrix(params)
        
        # Test matrix properties
        assert mvp_matrix.shape == (4, 4)
        
        # Test that a point at origin projects reasonably
        origin = np.array([0, 0, 0, 1])
        projected = mvp_matrix @ origin
        
        # Should have valid homogeneous coordinates
        assert projected[3] != 0
    
    def test_extrusion_vertices_generation(self):
        """Test 3D extrusion vertex generation."""
        # Simple square base
        base_vertices = np.array([
            [0, 0],
            [1, 0],
            [1, 1],
            [0, 1]
        ])
        
        vertices, indices = self.transform.generate_extrusion_vertices(
            base_vertices, extrusion_depth=1.0
        )
        
        # Should have front face + back face + side faces
        expected_vertex_count = 4 + 4 + (4 * 4)  # front + back + sides
        assert len(vertices) == expected_vertex_count
        
        # Check that front face is at z=0
        front_vertices = vertices[:4]
        assert np.allclose(front_vertices[:, 2], 0.0)
        
        # Check that back face is at z=-1
        back_vertices = vertices[4:8]
        assert np.allclose(back_vertices[:, 2], -1.0)
    
    def test_camera_animation_orbit(self):
        """Test orbital camera animation."""
        animation = CameraAnimation(
            movement_type=CameraMovement.ORBIT,
            duration=2.0,
            start_time=0.0,
            orbit_radius=5.0,
            orbit_speed=1.0
        )
        
        # Test at quarter rotation (0.5 seconds)
        animated_params = self.transform.animate_camera(
            animation, 0.5, self.default_params
        )
        
        # Should be at 90 degrees (quarter circle)
        expected_x = 5.0 * math.cos(0.5 * math.pi)  # Should be ~0
        expected_z = 5.0 * math.sin(0.5 * math.pi)  # Should be ~5
        
        assert abs(animated_params.camera_x - expected_x) < 1e-6
        assert abs(animated_params.camera_z - expected_z) < 1e-6
    
    def test_camera_animation_zoom(self):
        """Test zoom camera animation."""
        animation = CameraAnimation(
            movement_type=CameraMovement.ZOOM,
            duration=1.0,
            start_time=0.0,
            zoom_start=10.0,
            zoom_end=2.0
        )
        
        # Test at halfway point
        animated_params = self.transform.animate_camera(
            animation, 0.5, self.default_params
        )
        
        # Should be halfway between start and end
        expected_z = 6.0  # (10 + 2) / 2
        assert abs(animated_params.camera_z - expected_z) < 1e-6
    
    def test_point_transformation(self):
        """Test 3D point transformation."""
        # Create simple transformation
        params = Transform3DParams(translation_x=1.0)
        mvp_matrix = self.transform.create_mvp_matrix(params)
        
        point = np.array([0, 0, 0])
        transformed = self.transform.transform_point(point, mvp_matrix)
        
        # Should be a valid 3D point
        assert len(transformed) == 3
        assert not np.any(np.isnan(transformed))
    
    def test_screen_projection(self):
        """Test 3D to 2D screen projection."""
        params = Transform3DParams(camera_z=5.0)
        mvp_matrix = self.transform.create_mvp_matrix(params)
        
        # Point at origin should project to screen center
        world_point = np.array([0, 0, 0])
        screen_x, screen_y = self.transform.project_to_screen(world_point, mvp_matrix)
        
        # Should be near screen center
        assert 0 <= screen_x <= self.transform.viewport_width
        assert 0 <= screen_y <= self.transform.viewport_height
    
    def test_depth_sorting(self):
        """Test depth sorting of text elements."""
        # Mock text elements with different Z positions
        class MockTextElement:
            def __init__(self, x, y, z):
                self.x = x
                self.y = y
                self.z = z
        
        elements = [
            MockTextElement(0, 0, -1),  # Closest to camera (at z=5)
            MockTextElement(0, 0, -5),  # Farthest from camera
            MockTextElement(0, 0, -3),  # Middle distance
        ]
        
        params = Transform3DParams(camera_z=5.0)  # Camera at z=5
        mvp_matrix = self.transform.create_mvp_matrix(params)
        
        sorted_elements = self.transform.calculate_text_depth_sorting(elements, mvp_matrix)
        
        # Should be sorted back to front (farthest first for proper alpha blending)
        # With camera at z=5, element at z=-5 is farthest (distance=10)
        # element at z=-3 is middle (distance=8), element at z=-1 is closest (distance=6)
        assert sorted_elements[0].z == -5  # Farthest
        assert sorted_elements[1].z == -3  # Middle
        assert sorted_elements[2].z == -1  # Closest
    
    def test_empty_extrusion(self):
        """Test extrusion with empty vertices."""
        vertices, indices = self.transform.generate_extrusion_vertices(
            np.array([]), extrusion_depth=1.0
        )
        
        assert len(vertices) == 0
        assert len(indices) == 0
    
    def test_animation_before_start_time(self):
        """Test camera animation before start time."""
        animation = CameraAnimation(
            movement_type=CameraMovement.ZOOM,
            duration=1.0,
            start_time=5.0,
            zoom_start=10.0,
            zoom_end=2.0
        )
        
        # Test before animation starts
        animated_params = self.transform.animate_camera(
            animation, 2.0, self.default_params
        )
        
        # Should return unchanged parameters
        assert animated_params.camera_z == self.default_params.camera_z
    
    def test_animation_after_end_time(self):
        """Test camera animation after end time."""
        animation = CameraAnimation(
            movement_type=CameraMovement.ZOOM,
            duration=1.0,
            start_time=0.0,
            zoom_start=10.0,
            zoom_end=2.0
        )
        
        # Test after animation ends
        animated_params = self.transform.animate_camera(
            animation, 2.0, self.default_params
        )
        
        # Should be at end position
        assert abs(animated_params.camera_z - 2.0) < 1e-6


class TestTransform3DParams:
    """Test cases for Transform3DParams dataclass."""
    
    def test_default_values(self):
        """Test default parameter values."""
        params = Transform3DParams()
        
        assert params.rotation_x == 0.0
        assert params.rotation_y == 0.0
        assert params.rotation_z == 0.0
        assert params.scale_x == 1.0
        assert params.scale_y == 1.0
        assert params.scale_z == 1.0
        assert params.camera_z == 5.0
        assert params.field_of_view == 45.0
    
    def test_custom_values(self):
        """Test custom parameter values."""
        params = Transform3DParams(
            rotation_x=45.0,
            scale_x=2.0,
            extrusion_depth=1.5
        )
        
        assert params.rotation_x == 45.0
        assert params.scale_x == 2.0
        assert params.extrusion_depth == 1.5
        # Other values should remain default
        assert params.rotation_y == 0.0
        assert params.scale_y == 1.0


class TestCameraAnimation:
    """Test cases for CameraAnimation dataclass."""
    
    def test_default_values(self):
        """Test default animation values."""
        animation = CameraAnimation(
            movement_type=CameraMovement.ORBIT,
            duration=1.0,
            start_time=0.0
        )
        
        assert animation.movement_type == CameraMovement.ORBIT
        assert animation.duration == 1.0
        assert animation.start_time == 0.0
        assert animation.orbit_radius == 5.0
    
    def test_custom_values(self):
        """Test custom animation values."""
        animation = CameraAnimation(
            movement_type=CameraMovement.ZOOM,
            duration=2.0,
            start_time=1.0,
            zoom_start=10.0,
            zoom_end=1.0
        )
        
        assert animation.movement_type == CameraMovement.ZOOM
        assert animation.zoom_start == 10.0
        assert animation.zoom_end == 1.0


if __name__ == "__main__":
    pytest.main([__file__])