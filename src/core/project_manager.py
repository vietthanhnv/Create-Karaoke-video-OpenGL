"""
Project management system for creating, loading, and saving karaoke projects.
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import shutil

from .interfaces import IProjectManager
from .models import (
    Project, VideoAsset, AudioAsset, ProjectInfo, ExportSettings,
    ValidationResult, SubtitleTrack, TextElement, Keyframe, InterpolationType
)
from .validation import ValidationSystem


class ProjectManager(IProjectManager):
    """Concrete implementation of project management operations."""
    
    def __init__(self, validation_system: Optional[ValidationSystem] = None):
        """
        Initialize project manager.
        
        Args:
            validation_system: Optional validation system instance
        """
        self._validation_system = validation_system or ValidationSystem()
        self._recent_projects: List[ProjectInfo] = []
        self._projects_directory = Path.home() / "Documents" / "Karaoke Projects"
        self._recent_projects_file = self._projects_directory / ".recent_projects.json"
        
        # Ensure projects directory exists
        self._projects_directory.mkdir(parents=True, exist_ok=True)
        
        # Load recent projects list
        self._load_recent_projects()
    
    def create_project(self, video_path: str, project_name: Optional[str] = None) -> Project:
        """
        Create a new project with the specified video file.
        
        Args:
            video_path: Path to the video file
            project_name: Optional project name (auto-generated if not provided)
            
        Returns:
            New Project instance
            
        Raises:
            ValueError: If video file is invalid or unsupported
            FileNotFoundError: If video file doesn't exist
        """
        # Validate video file
        validation_result = self._validation_system.validate_video_file(video_path)
        if not validation_result.is_valid:
            raise ValueError(f"Invalid video file: {validation_result.error_message}")
        
        # Import video asset
        video_asset = self.import_video(video_path)
        
        # Generate project name if not provided
        if not project_name:
            video_filename = Path(video_path).stem
            project_name = f"Karaoke - {video_filename}"
        
        # Create default export settings
        export_settings = ExportSettings(
            resolution=video_asset.resolution,
            fps=video_asset.fps,
            format='mp4',
            quality_preset='normal',
            codec='h264'
        )
        
        # Create project
        now = datetime.now()
        project = Project(
            name=project_name,
            video_asset=video_asset,
            audio_asset=None,
            subtitle_tracks=[],
            export_settings=export_settings,
            created_at=now,
            modified_at=now
        )
        
        # Validate project
        project_validation = project.validate()
        if not project_validation.is_valid:
            raise ValueError(f"Project validation failed: {project_validation.error_message}")
        
        return project
    
    def load_project(self, project_path: str) -> Project:
        """
        Load an existing project from file.
        
        Args:
            project_path: Path to the project file (.ksp)
            
        Returns:
            Loaded Project instance
            
        Raises:
            FileNotFoundError: If project file doesn't exist
            ValueError: If project file is corrupted or invalid
        """
        if not os.path.exists(project_path):
            raise FileNotFoundError(f"Project file not found: {project_path}")
        
        try:
            # Load project from JSON file
            project = Project.load_from_file(project_path)
            
            # Validate loaded project
            validation_result = project.validate()
            if not validation_result.is_valid:
                raise ValueError(f"Invalid project file: {validation_result.error_message}")
            
            # Update recent projects
            self._add_to_recent_projects(project_path, project.name)
            
            return project
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Corrupted project file: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load project: {e}")
    
    def save_project(self, project: Project, path: str) -> bool:
        """
        Save a project to the specified path.
        
        Args:
            project: Project instance to save
            path: File path to save to (.ksp extension recommended)
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            # Validate project before saving
            validation_result = project.validate()
            if not validation_result.is_valid:
                print(f"Warning: Saving invalid project: {validation_result.error_message}")
            
            # Update modified timestamp
            project.modified_at = datetime.now()
            
            # Ensure directory exists
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            
            # Save project to file
            success = project.save_to_file(path)
            
            if success:
                # Update recent projects
                self._add_to_recent_projects(path, project.name)
            
            return success
            
        except Exception as e:
            print(f"Failed to save project: {e}")
            return False
    
    def import_video(self, path: str) -> VideoAsset:
        """
        Import a video file and create a VideoAsset.
        
        Args:
            path: Path to the video file
            
        Returns:
            VideoAsset instance with metadata
            
        Raises:
            ValueError: If video file is invalid
            FileNotFoundError: If video file doesn't exist
        """
        from ..video.asset_handler import VideoAssetHandler
        
        try:
            # Use the dedicated video asset handler
            video_handler = VideoAssetHandler()
            return video_handler.create_video_asset(path)
        except FileNotFoundError as e:
            raise ValueError(f"Invalid video file: {e}")
        except Exception as e:
            raise ValueError(f"Invalid video file: {e}")
    
    def import_audio(self, path: str) -> AudioAsset:
        """
        Import an audio file and create an AudioAsset.
        
        Args:
            path: Path to the audio file
            
        Returns:
            AudioAsset instance with metadata
            
        Raises:
            ValueError: If audio file is invalid
            FileNotFoundError: If audio file doesn't exist
        """
        from ..audio.asset_handler import AudioAssetHandler
        
        try:
            # Use the dedicated audio asset handler
            audio_handler = AudioAssetHandler()
            return audio_handler.create_audio_asset(path)
        except FileNotFoundError as e:
            raise ValueError(f"Invalid audio file: {e}")
        except Exception as e:
            raise ValueError(f"Invalid audio file: {e}")
    
    def get_recent_projects(self) -> List[ProjectInfo]:
        """
        Get list of recent projects.
        
        Returns:
            List of ProjectInfo objects for recent projects
        """
        # Filter out projects that no longer exist
        existing_projects = []
        for project_info in self._recent_projects:
            if os.path.exists(project_info.path):
                existing_projects.append(project_info)
        
        # Update the list if any projects were removed
        if len(existing_projects) != len(self._recent_projects):
            self._recent_projects = existing_projects
            self._save_recent_projects()
        
        return self._recent_projects.copy()
    
    def create_default_subtitle_track(self, project: Project) -> SubtitleTrack:
        """
        Create a default subtitle track for the project.
        
        Args:
            project: Project to create track for
            
        Returns:
            New SubtitleTrack instance
        """
        track_id = str(uuid.uuid4())
        
        # Create a sample text element
        sample_text = TextElement(
            content="Sample Karaoke Text",
            font_family="Arial",
            font_size=48.0,
            color=(1.0, 1.0, 1.0, 1.0),  # White
            position=(0.5, 0.8),  # Center horizontally, near bottom
            rotation=(0.0, 0.0, 0.0),
            effects=[]
        )
        
        # Create keyframes for the sample text
        start_keyframe = Keyframe(
            time=0.0,
            properties={"opacity": 0.0},
            interpolation_type=InterpolationType.LINEAR
        )
        
        show_keyframe = Keyframe(
            time=1.0,
            properties={"opacity": 1.0},
            interpolation_type=InterpolationType.LINEAR
        )
        
        hide_keyframe = Keyframe(
            time=project.video_asset.duration - 1.0,
            properties={"opacity": 0.0},
            interpolation_type=InterpolationType.LINEAR
        )
        
        # Create subtitle track
        subtitle_track = SubtitleTrack(
            id=track_id,
            elements=[sample_text],
            keyframes=[start_keyframe, show_keyframe, hide_keyframe],
            start_time=0.0,
            end_time=project.video_asset.duration
        )
        
        return subtitle_track
    
    def duplicate_project(self, source_path: str, new_name: str) -> str:
        """
        Create a duplicate of an existing project.
        
        Args:
            source_path: Path to the source project file
            new_name: Name for the new project
            
        Returns:
            Path to the new project file
            
        Raises:
            FileNotFoundError: If source project doesn't exist
            ValueError: If duplication fails
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source project not found: {source_path}")
        
        try:
            # Load source project
            source_project = self.load_project(source_path)
            
            # Create new project with updated name and timestamps
            now = datetime.now()
            new_project = Project(
                name=new_name,
                video_asset=source_project.video_asset,
                audio_asset=source_project.audio_asset,
                subtitle_tracks=source_project.subtitle_tracks.copy(),
                export_settings=source_project.export_settings,
                created_at=now,
                modified_at=now
            )
            
            # Generate new file path
            safe_name = "".join(c for c in new_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            new_filename = f"{safe_name}.ksp"
            new_path = str(self._projects_directory / new_filename)
            
            # Ensure unique filename
            counter = 1
            while os.path.exists(new_path):
                new_filename = f"{safe_name} ({counter}).ksp"
                new_path = str(self._projects_directory / new_filename)
                counter += 1
            
            # Save new project
            if not self.save_project(new_project, new_path):
                raise ValueError("Failed to save duplicated project")
            
            return new_path
            
        except Exception as e:
            raise ValueError(f"Failed to duplicate project: {e}")
    
    def delete_project(self, project_path: str) -> bool:
        """
        Delete a project file and remove from recent projects.
        
        Args:
            project_path: Path to the project file to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # Remove from recent projects first
            self._remove_from_recent_projects(project_path)
            
            # Delete the file
            if os.path.exists(project_path):
                os.remove(project_path)
            
            return True
            
        except Exception as e:
            print(f"Failed to delete project: {e}")
            return False
    
    def get_project_info(self, project_path: str) -> Optional[ProjectInfo]:
        """
        Get basic information about a project without fully loading it.
        
        Args:
            project_path: Path to the project file
            
        Returns:
            ProjectInfo instance or None if file is invalid
        """
        if not os.path.exists(project_path):
            return None
        
        try:
            # Get file modification time
            mtime = os.path.getmtime(project_path)
            last_modified = datetime.fromtimestamp(mtime).isoformat()
            
            # Try to extract project name from file
            with open(project_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                project_name = data.get('name', Path(project_path).stem)
            
            return ProjectInfo(
                name=project_name,
                path=project_path,
                last_modified=last_modified,
                thumbnail_path=None  # TODO: Implement thumbnail generation in later tasks
            )
            
        except Exception:
            return None
    
    def _load_recent_projects(self) -> None:
        """Load recent projects list from file."""
        if not self._recent_projects_file.exists():
            return
        
        try:
            with open(self._recent_projects_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._recent_projects = [
                    ProjectInfo(**item) for item in data.get('recent_projects', [])
                ]
        except Exception:
            # If loading fails, start with empty list
            self._recent_projects = []
    
    def _save_recent_projects(self) -> None:
        """Save recent projects list to file."""
        try:
            data = {
                'recent_projects': [
                    {
                        'name': p.name,
                        'path': p.path,
                        'last_modified': p.last_modified,
                        'thumbnail_path': p.thumbnail_path
                    }
                    for p in self._recent_projects
                ]
            }
            
            with open(self._recent_projects_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to save recent projects: {e}")
    
    def _add_to_recent_projects(self, project_path: str, project_name: str) -> None:
        """Add or update a project in the recent projects list."""
        project_path = os.path.abspath(project_path)
        
        # Remove existing entry if present
        self._recent_projects = [p for p in self._recent_projects if p.path != project_path]
        
        # Add to beginning of list
        project_info = ProjectInfo(
            name=project_name,
            path=project_path,
            last_modified=datetime.now().isoformat(),
            thumbnail_path=None
        )
        self._recent_projects.insert(0, project_info)
        
        # Limit to 10 recent projects
        self._recent_projects = self._recent_projects[:10]
        
        # Save updated list
        self._save_recent_projects()
    
    def _remove_from_recent_projects(self, project_path: str) -> None:
        """Remove a project from the recent projects list."""
        project_path = os.path.abspath(project_path)
        self._recent_projects = [p for p in self._recent_projects if p.path != project_path]
        self._save_recent_projects()
    
    def get_projects_directory(self) -> Path:
        """
        Get the default projects directory.
        
        Returns:
            Path to the projects directory
        """
        return self._projects_directory
    
    def set_projects_directory(self, directory: str) -> bool:
        """
        Set a new default projects directory.
        
        Args:
            directory: Path to the new projects directory
            
        Returns:
            True if directory was set successfully, False otherwise
        """
        try:
            new_dir = Path(directory)
            new_dir.mkdir(parents=True, exist_ok=True)
            
            self._projects_directory = new_dir
            self._recent_projects_file = new_dir / ".recent_projects.json"
            
            # Reload recent projects from new location
            self._load_recent_projects()
            
            return True
            
        except Exception as e:
            print(f"Failed to set projects directory: {e}")
            return False
    
    def validate_project_compatibility(self, project: Project) -> ValidationResult:
        """
        Validate that a project is compatible with current system capabilities.
        
        Args:
            project: Project to validate
            
        Returns:
            ValidationResult with compatibility information
        """
        errors = []
        warnings = []
        metadata = {}
        
        # Validate video asset
        if project.video_asset:
            video_validation = self._validation_system.validate_video_file(project.video_asset.path)
            if not video_validation.is_valid:
                errors.append(f"Video file issue: {video_validation.error_message}")
            if video_validation.warnings:
                warnings.extend([f"Video: {w}" for w in video_validation.warnings])
        
        # Validate audio asset if present
        if project.audio_asset:
            audio_validation = self._validation_system.validate_audio_file(project.audio_asset.path)
            if not audio_validation.is_valid:
                errors.append(f"Audio file issue: {audio_validation.error_message}")
            if audio_validation.warnings:
                warnings.extend([f"Audio: {w}" for w in audio_validation.warnings])
        
        # Validate export settings
        export_validation = self._validation_system.validate_export_settings(project.export_settings)
        if not export_validation.is_valid:
            errors.append(f"Export settings issue: {export_validation.error_message}")
        if export_validation.warnings:
            warnings.extend([f"Export: {w}" for w in export_validation.warnings])
        
        # Check system requirements
        system_validation = self._validation_system.validate_system_requirements()
        if not system_validation.is_valid:
            warnings.append(f"System requirements: {system_validation.error_message}")
        
        metadata['project_validation'] = project.validate()
        metadata['system_validation'] = system_validation
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            error_message="; ".join(errors) if errors else None,
            warnings=warnings,
            metadata=metadata
        )