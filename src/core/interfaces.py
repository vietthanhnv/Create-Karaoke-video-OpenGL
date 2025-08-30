"""
Base interfaces and abstract classes for core components.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

# Import data models from models module
from .models import (
    TextElement, SubtitleTrack, Keyframe, VideoAsset, AudioAsset, Project,
    ExportSettings, AnimationEffect, ParticleEffect, Transform3D,
    ValidationResult, CapabilityReport
)


class IProjectManager(ABC):
    """Interface for project management operations."""
    
    @abstractmethod
    def create_project(self, video_path: str) -> Project:
        """Create a new project with the specified video file."""
        pass
    
    @abstractmethod
    def load_project(self, project_path: str) -> Project:
        """Load an existing project from file."""
        pass
    
    @abstractmethod
    def save_project(self, project: Project, path: str) -> bool:
        """Save a project to the specified path."""
        pass
    
    @abstractmethod
    def import_video(self, path: str) -> VideoAsset:
        """Import a video file and create a VideoAsset."""
        pass


class ITimelineEngine(ABC):
    """Interface for timeline management and keyframe operations."""
    
    @abstractmethod
    def add_keyframe(self, track_id: str, time: float, properties: Dict[str, Any]) -> None:
        """Add a keyframe to the specified track."""
        pass
    
    @abstractmethod
    def interpolate_properties(self, time: float) -> Dict[str, Any]:
        """Interpolate properties at the given time."""
        pass
    
    @abstractmethod
    def get_waveform_data(self, audio_asset: AudioAsset) -> np.ndarray:
        """Generate waveform data for audio visualization."""
        pass
    
    @abstractmethod
    def sync_to_video_frame(self, frame_number: int) -> float:
        """Convert video frame number to timeline time."""
        pass


class IEffectSystem(ABC):
    """Interface for text effects and visual processing."""
    
    @abstractmethod
    def apply_text_animation(self, text: TextElement, effect: 'AnimationEffect') -> None:
        """Apply animation effect to text element."""
        pass
    
    @abstractmethod
    def render_particle_effect(self, effect: 'ParticleEffect', time: float) -> None:
        """Render particle effect at the specified time."""
        pass
    
    @abstractmethod
    def calculate_3d_transform(self, params: 'Transform3D') -> np.ndarray:
        """Calculate 3D transformation matrix."""
        pass


class IRenderEngine(ABC):
    """Interface for OpenGL rendering operations."""
    
    @abstractmethod
    def initialize_opengl_context(self) -> bool:
        """Initialize OpenGL context and resources."""
        pass
    
    @abstractmethod
    def render_frame(self, time: float, subtitles: List[TextElement]) -> None:
        """Render a frame with subtitles at the specified time."""
        pass
    
    @abstractmethod
    def composite_video_frame(self, video_frame: np.ndarray, overlay: np.ndarray) -> np.ndarray:
        """Composite video frame with subtitle overlay."""
        pass
    
    @abstractmethod
    def export_frame(self, time: float, resolution: Tuple[int, int]) -> np.ndarray:
        """Export a frame at the specified resolution."""
        pass


class IValidationSystem(ABC):
    """Interface for file format and capability validation."""
    
    @abstractmethod
    def validate_video_file(self, path: str) -> 'ValidationResult':
        """Validate if video file is supported."""
        pass
    
    @abstractmethod
    def validate_audio_file(self, path: str) -> 'ValidationResult':
        """Validate if audio file is supported."""
        pass
    
    @abstractmethod
    def validate_subtitle_file(self, path: str) -> 'ValidationResult':
        """Validate if subtitle file is supported."""
        pass
    
    @abstractmethod
    def validate_opengl_capabilities(self) -> 'CapabilityReport':
        """Check OpenGL capabilities and version."""
        pass
    
    @abstractmethod
    def validate_export_settings(self, settings: ExportSettings) -> 'ValidationResult':
        """Validate export settings compatibility."""
        pass


class RendererInterface(ABC):
    """Base interface for OpenGL renderers."""
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up renderer resources."""
        pass