"""
Data models and enumerations for the Karaoke Subtitle Creator.
"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import json
import os
import re


@dataclass
class ValidationResult:
    """Result of file or capability validation."""
    is_valid: bool
    error_message: Optional[str] = None
    warnings: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize warnings list if None."""
        if self.warnings is None:
            self.warnings = []


@dataclass
class CapabilityReport:
    """OpenGL capability report."""
    opengl_version: str
    glsl_version: str
    max_texture_size: int
    supports_vertex_arrays: bool
    supports_framebuffers: bool
    gpu_vendor: str
    gpu_model: str


class AnimationType(Enum):
    """Animation effect types."""
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    SLIDE_UP = "slide_up"
    SLIDE_DOWN = "slide_down"
    TYPEWRITER = "typewriter"
    BOUNCE = "bounce"


class VisualEffectType(Enum):
    """Visual effect types."""
    GLOW = "glow"
    OUTLINE = "outline"
    SHADOW = "shadow"
    GRADIENT = "gradient"


class ParticleType(Enum):
    """Particle effect types."""
    SPARKLE = "sparkle"
    FIRE = "fire"
    SMOKE = "smoke"


class EasingType(Enum):
    """Easing curve types for animations."""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    BOUNCE = "bounce"
    ELASTIC = "elastic"


class InterpolationType(Enum):
    """Keyframe interpolation types."""
    LINEAR = "linear"
    STEP = "step"
    BEZIER = "bezier"


@dataclass
class ExportSettings:
    """Export configuration settings."""
    resolution: Tuple[int, int]
    fps: float
    format: str  # 'mp4', 'mov', 'avi'
    quality_preset: str  # 'draft', 'normal', 'high', 'custom'
    codec: str
    bitrate: Optional[int] = None
    custom_parameters: Optional[Dict[str, Any]] = None

    def validate(self) -> ValidationResult:
        """Validate export settings."""
        errors = []
        warnings = []

        # Validate resolution
        if len(self.resolution) != 2:
            errors.append("Resolution must have width and height")
        elif self.resolution[0] <= 0 or self.resolution[1] <= 0:
            errors.append("Resolution dimensions must be positive")
        elif self.resolution[0] > 7680 or self.resolution[1] > 4320:
            warnings.append("Very high resolution detected (>8K)")

        # Validate FPS
        if self.fps <= 0:
            errors.append("FPS must be positive")
        elif self.fps > 120:
            warnings.append("Very high FPS detected (>120)")

        # Validate format
        valid_formats = {'mp4', 'mov', 'avi'}
        if self.format.lower() not in valid_formats:
            errors.append(f"Unsupported format: {self.format}")

        # Validate quality preset
        valid_presets = {'draft', 'normal', 'high', 'custom'}
        if self.quality_preset.lower() not in valid_presets:
            errors.append(f"Invalid quality preset: {self.quality_preset}")

        # Validate codec
        if not self.codec:
            errors.append("Codec cannot be empty")

        # Validate bitrate
        if self.bitrate is not None and self.bitrate <= 0:
            errors.append("Bitrate must be positive")

        return ValidationResult(
            is_valid=len(errors) == 0,
            error_message="; ".join(errors) if errors else None,
            warnings=warnings
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'resolution': list(self.resolution),
            'fps': self.fps,
            'format': self.format,
            'quality_preset': self.quality_preset,
            'codec': self.codec,
            'bitrate': self.bitrate,
            'custom_parameters': self.custom_parameters
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExportSettings':
        """Create ExportSettings from dictionary."""
        return cls(
            resolution=tuple(data['resolution']),
            fps=data['fps'],
            format=data['format'],
            quality_preset=data['quality_preset'],
            codec=data['codec'],
            bitrate=data.get('bitrate'),
            custom_parameters=data.get('custom_parameters')
        )


@dataclass
class AnimationEffect:
    """Animation effect configuration."""
    type: AnimationType
    duration: float
    parameters: Dict[str, Any]
    easing_curve: EasingType

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'type': self.type.value,
            'duration': self.duration,
            'parameters': self.parameters,
            'easing_curve': self.easing_curve.value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnimationEffect':
        """Create AnimationEffect from dictionary."""
        return cls(
            type=AnimationType(data['type']),
            duration=data['duration'],
            parameters=data['parameters'],
            easing_curve=EasingType(data['easing_curve'])
        )


@dataclass
class VisualEffect:
    """Visual effect configuration."""
    type: VisualEffectType
    intensity: float
    color: Tuple[float, float, float, float]  # RGBA
    parameters: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'type': self.type.value,
            'intensity': self.intensity,
            'color': list(self.color),
            'parameters': self.parameters
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VisualEffect':
        """Create VisualEffect from dictionary."""
        return cls(
            type=VisualEffectType(data['type']),
            intensity=data['intensity'],
            color=tuple(data['color']),
            parameters=data['parameters']
        )


@dataclass
class ParticleEffect:
    """Particle effect configuration."""
    type: ParticleType
    emission_rate: float
    lifetime: float
    texture_path: Optional[str]
    physics_parameters: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'type': self.type.value,
            'emission_rate': self.emission_rate,
            'lifetime': self.lifetime,
            'texture_path': self.texture_path,
            'physics_parameters': self.physics_parameters
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParticleEffect':
        """Create ParticleEffect from dictionary."""
        return cls(
            type=ParticleType(data['type']),
            emission_rate=data['emission_rate'],
            lifetime=data['lifetime'],
            texture_path=data.get('texture_path'),
            physics_parameters=data['physics_parameters']
        )


@dataclass
class Transform3D:
    """3D transformation parameters."""
    rotation: Tuple[float, float, float]  # XYZ rotation in degrees
    scale: Tuple[float, float, float]     # XYZ scale factors
    translation: Tuple[float, float, float]  # XYZ translation
    perspective: float                    # Perspective factor


@dataclass
class ColorEffect:
    """Color effect configuration."""
    type: str  # 'rainbow', 'pulse', 'strobe'
    speed: float
    intensity: float
    bpm_sync: bool = False
    bpm: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'type': self.type,
            'speed': self.speed,
            'intensity': self.intensity,
            'bpm_sync': self.bpm_sync,
            'bpm': self.bpm
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ColorEffect':
        """Create ColorEffect from dictionary."""
        return cls(
            type=data['type'],
            speed=data['speed'],
            intensity=data['intensity'],
            bpm_sync=data.get('bpm_sync', False),
            bpm=data.get('bpm')
        )


@dataclass
class ProjectInfo:
    """Basic project information for recent projects list."""
    name: str
    path: str
    last_modified: str
    thumbnail_path: Optional[str] = None


@dataclass
class TextElement:
    """Represents a text element with formatting and positioning."""
    content: str
    font_family: str
    font_size: float
    color: Tuple[float, float, float, float]  # RGBA
    position: Tuple[float, float]
    rotation: Tuple[float, float, float]  # XYZ rotation
    effects: List['Effect']

    def validate(self) -> ValidationResult:
        """Validate text element properties."""
        errors = []
        warnings = []

        # Validate content
        if not self.content or not self.content.strip():
            errors.append("Text content cannot be empty")

        # Validate font size
        if self.font_size <= 0:
            errors.append("Font size must be positive")
        elif self.font_size > 1000:
            warnings.append("Font size is very large (>1000)")

        # Validate color values (RGBA 0-1)
        for i, component in enumerate(self.color):
            if not 0 <= component <= 1:
                errors.append(f"Color component {i} must be between 0 and 1")

        # Validate position
        if len(self.position) != 2:
            errors.append("Position must have exactly 2 coordinates")

        # Validate rotation
        if len(self.rotation) != 3:
            errors.append("Rotation must have exactly 3 components (XYZ)")

        return ValidationResult(
            is_valid=len(errors) == 0,
            error_message="; ".join(errors) if errors else None,
            warnings=warnings
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'content': self.content,
            'font_family': self.font_family,
            'font_size': self.font_size,
            'color': list(self.color),
            'position': list(self.position),
            'rotation': list(self.rotation),
            'effects': [effect.to_dict() if hasattr(effect, 'to_dict') else asdict(effect) for effect in self.effects]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TextElement':
        """Create TextElement from dictionary."""
        # Convert effects back to proper objects
        effects = []
        for effect_data in data.get('effects', []):
            if isinstance(effect_data, dict) and 'type' in effect_data:
                effect_type = effect_data['type']
                if effect_type in [e.value for e in AnimationType]:
                    effects.append(AnimationEffect.from_dict(effect_data))
                elif effect_type in [e.value for e in VisualEffectType]:
                    effects.append(VisualEffect.from_dict(effect_data))
                elif effect_type in [e.value for e in ParticleType]:
                    effects.append(ParticleEffect.from_dict(effect_data))
                else:
                    # Assume ColorEffect for other types
                    effects.append(ColorEffect.from_dict(effect_data))
            else:
                effects.append(effect_data)  # Keep as-is if not recognizable
        
        return cls(
            content=data['content'],
            font_family=data['font_family'],
            font_size=data['font_size'],
            color=tuple(data['color']),
            position=tuple(data['position']),
            rotation=tuple(data['rotation']),
            effects=effects
        )


@dataclass
class Keyframe:
    """Represents a keyframe with timing and property data."""
    time: float
    properties: Dict[str, Any]
    interpolation_type: InterpolationType

    def validate(self) -> ValidationResult:
        """Validate keyframe properties."""
        errors = []
        warnings = []

        # Validate time
        if self.time < 0:
            errors.append("Keyframe time cannot be negative")

        # Validate properties
        if not self.properties:
            warnings.append("Keyframe has no properties")

        return ValidationResult(
            is_valid=len(errors) == 0,
            error_message="; ".join(errors) if errors else None,
            warnings=warnings
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'time': self.time,
            'properties': self.properties,
            'interpolation_type': self.interpolation_type.value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Keyframe':
        """Create Keyframe from dictionary."""
        return cls(
            time=data['time'],
            properties=data['properties'],
            interpolation_type=InterpolationType(data['interpolation_type'])
        )


@dataclass
class SubtitleTrack:
    """Represents a subtitle track containing text elements and keyframes."""
    id: str
    elements: List[TextElement]
    keyframes: List[Keyframe]
    start_time: float
    end_time: float

    def validate(self) -> ValidationResult:
        """Validate subtitle track properties."""
        errors = []
        warnings = []

        # Validate ID
        if not self.id or not self.id.strip():
            errors.append("Track ID cannot be empty")

        # Validate timing
        if self.start_time < 0:
            errors.append("Start time cannot be negative")
        if self.end_time <= self.start_time:
            errors.append("End time must be greater than start time")

        # Validate elements
        for i, element in enumerate(self.elements):
            element_validation = element.validate()
            if not element_validation.is_valid:
                errors.append(f"Element {i}: {element_validation.error_message}")

        # Validate keyframes
        for i, keyframe in enumerate(self.keyframes):
            keyframe_validation = keyframe.validate()
            if not keyframe_validation.is_valid:
                errors.append(f"Keyframe {i}: {keyframe_validation.error_message}")
            
            # Check if keyframe time is within track bounds
            if not (self.start_time <= keyframe.time <= self.end_time):
                warnings.append(f"Keyframe {i} time is outside track bounds")

        return ValidationResult(
            is_valid=len(errors) == 0,
            error_message="; ".join(errors) if errors else None,
            warnings=warnings
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'elements': [element.to_dict() for element in self.elements],
            'keyframes': [keyframe.to_dict() for keyframe in self.keyframes],
            'start_time': self.start_time,
            'end_time': self.end_time
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SubtitleTrack':
        """Create SubtitleTrack from dictionary."""
        return cls(
            id=data['id'],
            elements=[TextElement.from_dict(elem) for elem in data['elements']],
            keyframes=[Keyframe.from_dict(kf) for kf in data['keyframes']],
            start_time=data['start_time'],
            end_time=data['end_time']
        )


@dataclass
class VideoAsset:
    """Represents a video file asset with metadata."""
    path: str
    duration: float
    fps: float
    resolution: Tuple[int, int]
    codec: str

    def validate(self) -> ValidationResult:
        """Validate video asset properties."""
        errors = []
        warnings = []

        # Validate file path
        if not self.path:
            errors.append("Video path cannot be empty")
        elif not os.path.exists(self.path):
            errors.append(f"Video file does not exist: {self.path}")
        else:
            # Check file extension
            valid_extensions = {'.mp4', '.mov', '.avi', '.mkv'}
            ext = os.path.splitext(self.path)[1].lower()
            if ext not in valid_extensions:
                warnings.append(f"Video format {ext} may not be supported")

        # Validate duration
        if self.duration <= 0:
            errors.append("Video duration must be positive")

        # Validate FPS
        if self.fps <= 0:
            errors.append("Video FPS must be positive")
        elif self.fps > 120:
            warnings.append("Very high FPS detected (>120)")

        # Validate resolution
        if len(self.resolution) != 2:
            errors.append("Resolution must have width and height")
        elif self.resolution[0] <= 0 or self.resolution[1] <= 0:
            errors.append("Resolution dimensions must be positive")

        # Validate codec
        if not self.codec:
            warnings.append("No codec information available")

        return ValidationResult(
            is_valid=len(errors) == 0,
            error_message="; ".join(errors) if errors else None,
            warnings=warnings
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'path': self.path,
            'duration': self.duration,
            'fps': self.fps,
            'resolution': list(self.resolution),
            'codec': self.codec
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VideoAsset':
        """Create VideoAsset from dictionary."""
        return cls(
            path=data['path'],
            duration=data['duration'],
            fps=data['fps'],
            resolution=tuple(data['resolution']),
            codec=data['codec']
        )


@dataclass
class AudioAsset:
    """Represents an audio file asset with metadata."""
    path: str
    duration: float
    sample_rate: int
    channels: int
    format: str

    def validate(self) -> ValidationResult:
        """Validate audio asset properties."""
        errors = []
        warnings = []

        # Validate file path
        if not self.path:
            errors.append("Audio path cannot be empty")
        elif not os.path.exists(self.path):
            errors.append(f"Audio file does not exist: {self.path}")
        else:
            # Check file extension
            valid_extensions = {'.mp3', '.wav', '.aac', '.flac', '.ogg'}
            ext = os.path.splitext(self.path)[1].lower()
            if ext not in valid_extensions:
                warnings.append(f"Audio format {ext} may not be supported")

        # Validate duration
        if self.duration <= 0:
            errors.append("Audio duration must be positive")

        # Validate sample rate
        if self.sample_rate <= 0:
            errors.append("Sample rate must be positive")
        elif self.sample_rate < 8000:
            warnings.append("Low sample rate detected (<8kHz)")

        # Validate channels
        if self.channels <= 0:
            errors.append("Channel count must be positive")
        elif self.channels > 8:
            warnings.append("High channel count detected (>8)")

        return ValidationResult(
            is_valid=len(errors) == 0,
            error_message="; ".join(errors) if errors else None,
            warnings=warnings
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'path': self.path,
            'duration': self.duration,
            'sample_rate': self.sample_rate,
            'channels': self.channels,
            'format': self.format
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AudioAsset':
        """Create AudioAsset from dictionary."""
        return cls(
            path=data['path'],
            duration=data['duration'],
            sample_rate=data['sample_rate'],
            channels=data['channels'],
            format=data['format']
        )


@dataclass
class Project:
    """Represents a complete karaoke project."""
    name: str
    video_asset: VideoAsset
    audio_asset: Optional[AudioAsset]
    subtitle_tracks: List[SubtitleTrack]
    export_settings: ExportSettings
    created_at: datetime
    modified_at: datetime

    def validate(self) -> ValidationResult:
        """Validate project properties."""
        errors = []
        warnings = []

        # Validate name
        if not self.name or not self.name.strip():
            errors.append("Project name cannot be empty")
        elif len(self.name) > 255:
            errors.append("Project name too long (>255 characters)")

        # Validate video asset
        video_validation = self.video_asset.validate()
        if not video_validation.is_valid:
            errors.append(f"Video asset: {video_validation.error_message}")

        # Validate audio asset if present
        if self.audio_asset:
            audio_validation = self.audio_asset.validate()
            if not audio_validation.is_valid:
                errors.append(f"Audio asset: {audio_validation.error_message}")

        # Validate subtitle tracks
        if not self.subtitle_tracks:
            warnings.append("Project has no subtitle tracks")
        else:
            track_ids = set()
            for i, track in enumerate(self.subtitle_tracks):
                track_validation = track.validate()
                if not track_validation.is_valid:
                    errors.append(f"Track {i}: {track_validation.error_message}")
                
                # Check for duplicate track IDs
                if track.id in track_ids:
                    errors.append(f"Duplicate track ID: {track.id}")
                track_ids.add(track.id)

        # Validate export settings
        export_validation = self.export_settings.validate()
        if not export_validation.is_valid:
            errors.append(f"Export settings: {export_validation.error_message}")

        # Validate timestamps
        if self.created_at > self.modified_at:
            warnings.append("Created date is after modified date")

        return ValidationResult(
            is_valid=len(errors) == 0,
            error_message="; ".join(errors) if errors else None,
            warnings=warnings
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'video_asset': self.video_asset.to_dict(),
            'audio_asset': self.audio_asset.to_dict() if self.audio_asset else None,
            'subtitle_tracks': [track.to_dict() for track in self.subtitle_tracks],
            'export_settings': self.export_settings.to_dict(),
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Create Project from dictionary."""
        return cls(
            name=data['name'],
            video_asset=VideoAsset.from_dict(data['video_asset']),
            audio_asset=AudioAsset.from_dict(data['audio_asset']) if data['audio_asset'] else None,
            subtitle_tracks=[SubtitleTrack.from_dict(track) for track in data['subtitle_tracks']],
            export_settings=ExportSettings.from_dict(data['export_settings']),
            created_at=datetime.fromisoformat(data['created_at']),
            modified_at=datetime.fromisoformat(data['modified_at'])
        )

    def to_json(self) -> str:
        """Serialize project to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'Project':
        """Deserialize project from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def save_to_file(self, filepath: str) -> bool:
        """Save project to JSON file."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.to_json())
            return True
        except Exception:
            return False

    @classmethod
    def load_from_file(cls, filepath: str) -> 'Project':
        """Load project from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            json_str = f.read()
        return cls.from_json(json_str)
# Base Effect class for type hinting
Effect = AnimationEffect | VisualEffect | ParticleEffect | ColorEffect