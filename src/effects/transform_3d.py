"""
3D Text Transformation System

This module provides 3D transformation capabilities for text rendering including
rotation, extrusion, perspective projection, and camera movement simulation.
"""

import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import math


class ProjectionType(Enum):
    """Types of 3D projection."""
    PERSPECTIVE = "perspective"
    ORTHOGRAPHIC = "orthographic"


class CameraMovement(Enum):
    """Types of camera movement animations."""
    ORBIT = "orbit"
    ZOOM = "zoom"
    PAN = "pan"
    TILT = "tilt"
    ROLL = "roll"


@dataclass
class Transform3DParams:
    """Parameters for 3D text transformation."""
    # Rotation (in degrees)
    rotation_x: float = 0.0
    rotation_y: float = 0.0
    rotation_z: float = 0.0
    
    # Translation
    translation_x: float = 0.0
    translation_y: float = 0.0
    translation_z: float = 0.0
    
    # Scale
    scale_x: float = 1.0
    scale_y: float = 1.0
    scale_z: float = 1.0
    
    # Extrusion
    extrusion_depth: float = 0.0
    extrusion_bevel: float = 0.0
    
    # Perspective
    field_of_view: float = 45.0
    near_plane: float = 0.1
    far_plane: float = 100.0
    
    # Camera position
    camera_x: float = 0.0
    camera_y: float = 0.0
    camera_z: float = 5.0
    
    # Camera target (look-at point)
    target_x: float = 0.0
    target_y: float = 0.0
    target_z: float = 0.0
    
    # Camera up vector
    up_x: float = 0.0
    up_y: float = 1.0
    up_z: float = 0.0


@dataclass
class CameraAnimation:
    """Parameters for animated camera movement."""
    movement_type: CameraMovement
    duration: float
    start_time: float
    
    # Movement-specific parameters
    orbit_radius: float = 5.0
    orbit_speed: float = 1.0
    zoom_start: float = 5.0
    zoom_end: float = 2.0
    pan_start_x: float = 0.0
    pan_end_x: float = 2.0
    pan_start_y: float = 0.0
    pan_end_y: float = 1.0
    tilt_start: float = 0.0
    tilt_end: float = 30.0
    roll_start: float = 0.0
    roll_end: float = 45.0


class Transform3D:
    """
    3D transformation system for text rendering with support for rotation,
    extrusion, perspective projection, and camera animations.
    """
    
    def __init__(self):
        """Initialize the 3D transformation system."""
        self.viewport_width = 1920
        self.viewport_height = 1080
        self.aspect_ratio = self.viewport_width / self.viewport_height
        
    def set_viewport(self, width: int, height: int):
        """Set the viewport dimensions."""
        self.viewport_width = width
        self.viewport_height = height
        self.aspect_ratio = width / height
    
    def create_rotation_matrix_x(self, angle_degrees: float) -> np.ndarray:
        """Create rotation matrix around X-axis."""
        angle = math.radians(angle_degrees)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        
        return np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, cos_a, -sin_a, 0.0],
            [0.0, sin_a, cos_a, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=np.float32)
    
    def create_rotation_matrix_y(self, angle_degrees: float) -> np.ndarray:
        """Create rotation matrix around Y-axis."""
        angle = math.radians(angle_degrees)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        
        return np.array([
            [cos_a, 0.0, sin_a, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [-sin_a, 0.0, cos_a, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=np.float32)
    
    def create_rotation_matrix_z(self, angle_degrees: float) -> np.ndarray:
        """Create rotation matrix around Z-axis."""
        angle = math.radians(angle_degrees)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        
        return np.array([
            [cos_a, -sin_a, 0.0, 0.0],
            [sin_a, cos_a, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=np.float32)
    
    def create_translation_matrix(self, x: float, y: float, z: float) -> np.ndarray:
        """Create translation matrix."""
        return np.array([
            [1.0, 0.0, 0.0, x],
            [0.0, 1.0, 0.0, y],
            [0.0, 0.0, 1.0, z],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=np.float32)
    
    def create_scale_matrix(self, x: float, y: float, z: float) -> np.ndarray:
        """Create scale matrix."""
        return np.array([
            [x, 0.0, 0.0, 0.0],
            [0.0, y, 0.0, 0.0],
            [0.0, 0.0, z, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=np.float32)
    
    def create_perspective_matrix(self, fov_degrees: float, aspect: float, 
                                near: float, far: float) -> np.ndarray:
        """Create perspective projection matrix."""
        fov_rad = math.radians(fov_degrees)
        f = 1.0 / math.tan(fov_rad / 2.0)
        
        return np.array([
            [f / aspect, 0.0, 0.0, 0.0],
            [0.0, f, 0.0, 0.0],
            [0.0, 0.0, (far + near) / (near - far), (2.0 * far * near) / (near - far)],
            [0.0, 0.0, -1.0, 0.0]
        ], dtype=np.float32)
    
    def create_orthographic_matrix(self, left: float, right: float, bottom: float,
                                 top: float, near: float, far: float) -> np.ndarray:
        """Create orthographic projection matrix."""
        return np.array([
            [2.0 / (right - left), 0.0, 0.0, -(right + left) / (right - left)],
            [0.0, 2.0 / (top - bottom), 0.0, -(top + bottom) / (top - bottom)],
            [0.0, 0.0, -2.0 / (far - near), -(far + near) / (far - near)],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=np.float32)
    
    def create_look_at_matrix(self, eye_x: float, eye_y: float, eye_z: float,
                            target_x: float, target_y: float, target_z: float,
                            up_x: float, up_y: float, up_z: float) -> np.ndarray:
        """Create look-at (view) matrix."""
        # Calculate forward vector (from eye to target)
        forward = np.array([target_x - eye_x, target_y - eye_y, target_z - eye_z])
        forward_length = np.linalg.norm(forward)
        
        # Handle case where eye and target are the same
        if forward_length < 1e-6:
            forward = np.array([0.0, 0.0, -1.0])  # Default forward direction
        else:
            forward = forward / forward_length
        
        # Calculate right vector
        up = np.array([up_x, up_y, up_z])
        right = np.cross(forward, up)
        right_length = np.linalg.norm(right)
        
        # Handle case where forward and up are parallel
        if right_length < 1e-6:
            # Use a different up vector
            if abs(forward[1]) < 0.9:
                up = np.array([0.0, 1.0, 0.0])
            else:
                up = np.array([1.0, 0.0, 0.0])
            right = np.cross(forward, up)
            right_length = np.linalg.norm(right)
        
        right = right / right_length
        
        # Recalculate up vector
        up = np.cross(right, forward)
        
        # Create view matrix
        view_matrix = np.array([
            [right[0], up[0], -forward[0], 0.0],
            [right[1], up[1], -forward[1], 0.0],
            [right[2], up[2], -forward[2], 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=np.float32)
        
        # Apply translation
        translation = np.array([
            [1.0, 0.0, 0.0, -eye_x],
            [0.0, 1.0, 0.0, -eye_y],
            [0.0, 0.0, 1.0, -eye_z],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=np.float32)
        
        return view_matrix @ translation
    
    def create_model_matrix(self, params: Transform3DParams) -> np.ndarray:
        """Create model transformation matrix from parameters."""
        # Create individual transformation matrices
        scale_matrix = self.create_scale_matrix(params.scale_x, params.scale_y, params.scale_z)
        
        rotation_x = self.create_rotation_matrix_x(params.rotation_x)
        rotation_y = self.create_rotation_matrix_y(params.rotation_y)
        rotation_z = self.create_rotation_matrix_z(params.rotation_z)
        
        translation_matrix = self.create_translation_matrix(
            params.translation_x, params.translation_y, params.translation_z
        )
        
        # Combine transformations: Translation * Rotation * Scale
        rotation_matrix = rotation_z @ rotation_y @ rotation_x
        model_matrix = translation_matrix @ rotation_matrix @ scale_matrix
        
        return model_matrix
    
    def create_view_matrix(self, params: Transform3DParams) -> np.ndarray:
        """Create view matrix from camera parameters."""
        return self.create_look_at_matrix(
            params.camera_x, params.camera_y, params.camera_z,
            params.target_x, params.target_y, params.target_z,
            params.up_x, params.up_y, params.up_z
        )
    
    def create_projection_matrix(self, params: Transform3DParams, 
                               projection_type: ProjectionType = ProjectionType.PERSPECTIVE) -> np.ndarray:
        """Create projection matrix."""
        if projection_type == ProjectionType.PERSPECTIVE:
            return self.create_perspective_matrix(
                params.field_of_view, self.aspect_ratio, 
                params.near_plane, params.far_plane
            )
        else:
            # Orthographic projection
            half_width = 5.0
            half_height = half_width / self.aspect_ratio
            return self.create_orthographic_matrix(
                -half_width, half_width, -half_height, half_height,
                params.near_plane, params.far_plane
            )
    
    def create_mvp_matrix(self, params: Transform3DParams, 
                         projection_type: ProjectionType = ProjectionType.PERSPECTIVE) -> np.ndarray:
        """Create complete Model-View-Projection matrix."""
        model_matrix = self.create_model_matrix(params)
        view_matrix = self.create_view_matrix(params)
        projection_matrix = self.create_projection_matrix(params, projection_type)
        
        # MVP = Projection * View * Model
        mvp_matrix = projection_matrix @ view_matrix @ model_matrix
        return mvp_matrix
    
    def generate_extrusion_vertices(self, base_vertices: np.ndarray, 
                                  extrusion_depth: float, 
                                  bevel_size: float = 0.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate 3D extruded vertices from 2D base vertices.
        
        Args:
            base_vertices: 2D vertices of the text outline
            extrusion_depth: Depth of extrusion
            bevel_size: Size of bevel edges
            
        Returns:
            Tuple of (vertices, indices) for 3D mesh
        """
        if len(base_vertices) == 0:
            return np.array([]), np.array([])
        
        num_base_vertices = len(base_vertices)
        
        # Create front and back faces
        front_vertices = np.column_stack([base_vertices, np.zeros(num_base_vertices)])
        back_vertices = np.column_stack([base_vertices, np.full(num_base_vertices, -extrusion_depth)])
        
        # Create side faces
        side_vertices = []
        side_indices = []
        
        for i in range(num_base_vertices):
            next_i = (i + 1) % num_base_vertices
            
            # Create quad for side face
            v1 = front_vertices[i]
            v2 = front_vertices[next_i]
            v3 = back_vertices[next_i]
            v4 = back_vertices[i]
            
            base_idx = len(side_vertices)
            side_vertices.extend([v1, v2, v3, v4])
            
            # Two triangles for the quad
            side_indices.extend([
                base_idx, base_idx + 1, base_idx + 2,
                base_idx, base_idx + 2, base_idx + 3
            ])
        
        # Combine all vertices
        all_vertices = np.vstack([front_vertices, back_vertices, np.array(side_vertices)])
        
        # Create indices for front and back faces (assuming triangulated)
        front_indices = list(range(num_base_vertices))
        back_indices = list(range(num_base_vertices, 2 * num_base_vertices))
        back_indices.reverse()  # Reverse winding for back face
        
        all_indices = np.array(front_indices + back_indices + side_indices, dtype=np.uint32)
        
        return all_vertices.astype(np.float32), all_indices
    
    def animate_camera(self, animation: CameraAnimation, current_time: float, 
                      base_params: Transform3DParams) -> Transform3DParams:
        """
        Animate camera movement based on animation parameters.
        
        Args:
            animation: Camera animation parameters
            current_time: Current time in seconds
            base_params: Base transformation parameters
            
        Returns:
            Updated transformation parameters with animated camera
        """
        # Calculate animation progress (0.0 to 1.0)
        elapsed_time = current_time - animation.start_time
        if elapsed_time < 0:
            return base_params
        
        progress = min(elapsed_time / animation.duration, 1.0)
        
        # Create a copy of base parameters
        animated_params = Transform3DParams(
            rotation_x=base_params.rotation_x,
            rotation_y=base_params.rotation_y,
            rotation_z=base_params.rotation_z,
            translation_x=base_params.translation_x,
            translation_y=base_params.translation_y,
            translation_z=base_params.translation_z,
            scale_x=base_params.scale_x,
            scale_y=base_params.scale_y,
            scale_z=base_params.scale_z,
            extrusion_depth=base_params.extrusion_depth,
            extrusion_bevel=base_params.extrusion_bevel,
            field_of_view=base_params.field_of_view,
            near_plane=base_params.near_plane,
            far_plane=base_params.far_plane,
            camera_x=base_params.camera_x,
            camera_y=base_params.camera_y,
            camera_z=base_params.camera_z,
            target_x=base_params.target_x,
            target_y=base_params.target_y,
            target_z=base_params.target_z,
            up_x=base_params.up_x,
            up_y=base_params.up_y,
            up_z=base_params.up_z
        )
        
        # Apply animation based on type
        if animation.movement_type == CameraMovement.ORBIT:
            angle = progress * animation.orbit_speed * 2 * math.pi
            animated_params.camera_x = animation.orbit_radius * math.cos(angle)
            animated_params.camera_z = animation.orbit_radius * math.sin(angle)
            
        elif animation.movement_type == CameraMovement.ZOOM:
            animated_params.camera_z = self._lerp(animation.zoom_start, animation.zoom_end, progress)
            
        elif animation.movement_type == CameraMovement.PAN:
            animated_params.camera_x = self._lerp(animation.pan_start_x, animation.pan_end_x, progress)
            animated_params.camera_y = self._lerp(animation.pan_start_y, animation.pan_end_y, progress)
            
        elif animation.movement_type == CameraMovement.TILT:
            tilt_angle = self._lerp(animation.tilt_start, animation.tilt_end, progress)
            # Apply tilt by rotating around X-axis
            animated_params.camera_y = animation.orbit_radius * math.sin(math.radians(tilt_angle))
            animated_params.camera_z = animation.orbit_radius * math.cos(math.radians(tilt_angle))
            
        elif animation.movement_type == CameraMovement.ROLL:
            roll_angle = self._lerp(animation.roll_start, animation.roll_end, progress)
            # Apply roll by rotating the up vector
            animated_params.up_x = math.sin(math.radians(roll_angle))
            animated_params.up_y = math.cos(math.radians(roll_angle))
        
        return animated_params
    
    def _lerp(self, start: float, end: float, t: float) -> float:
        """Linear interpolation between two values."""
        return start + (end - start) * t
    
    def transform_point(self, point: np.ndarray, mvp_matrix: np.ndarray) -> np.ndarray:
        """Transform a 3D point using the MVP matrix."""
        # Convert to homogeneous coordinates
        if len(point) == 3:
            homogeneous_point = np.append(point, 1.0)
        else:
            homogeneous_point = point
        
        # Apply transformation
        transformed = mvp_matrix @ homogeneous_point
        
        # Perspective divide
        if transformed[3] != 0:
            transformed = transformed / transformed[3]
        
        return transformed[:3]
    
    def project_to_screen(self, world_point: np.ndarray, mvp_matrix: np.ndarray) -> Tuple[float, float]:
        """
        Project a 3D world point to 2D screen coordinates.
        
        Args:
            world_point: 3D point in world coordinates
            mvp_matrix: Model-View-Projection matrix
            
        Returns:
            Tuple of (screen_x, screen_y) coordinates
        """
        # Transform to clip space
        clip_point = self.transform_point(world_point, mvp_matrix)
        
        # Convert from NDC (-1 to 1) to screen coordinates
        screen_x = (clip_point[0] + 1.0) * 0.5 * self.viewport_width
        screen_y = (1.0 - clip_point[1]) * 0.5 * self.viewport_height  # Flip Y
        
        return screen_x, screen_y
    
    def calculate_text_depth_sorting(self, text_elements: list, mvp_matrix: np.ndarray) -> list:
        """
        Sort text elements by depth for proper rendering order.
        
        Args:
            text_elements: List of text elements with position data
            mvp_matrix: Model-View-Projection matrix
            
        Returns:
            List of text elements sorted by depth (back to front)
        """
        elements_with_depth = []
        
        for element in text_elements:
            # Get element position (assuming it has x, y, z attributes)
            world_pos = np.array([
                getattr(element, 'x', 0.0),
                getattr(element, 'y', 0.0), 
                getattr(element, 'z', 0.0)
            ])
            
            # Use just the view matrix part to get view-space depth
            # Create view matrix from MVP parameters
            params = Transform3DParams()  # Use default camera position
            view_matrix = self.create_view_matrix(params)
            
            # Transform to view space
            homogeneous_pos = np.append(world_pos, 1.0)
            view_pos = view_matrix @ homogeneous_pos
            depth = view_pos[2]  # Z coordinate in view space (negative values are in front)
            
            elements_with_depth.append((element, depth))
        
        # Sort by depth (more negative Z values are closer, should render last)
        elements_with_depth.sort(key=lambda x: x[1])
        
        return [element for element, depth in elements_with_depth]