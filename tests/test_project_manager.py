"""
Tests for ProjectManager functionality.
"""

import os
import tempfile
import pytest
from pathlib import Path
from datetime import datetime

from src.core.project_manager import ProjectManager
from src.core.validation import ValidationSystem
from src.core.models import Project, VideoAsset, ExportSettings


class TestProjectManager:
    """Test cases for ProjectManager class."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.validation_system = ValidationSystem()
        self.project_manager = ProjectManager(self.validation_system)
        
        # Create a mock video file for testing
        self.test_video_path = os.path.join(self.temp_dir, "test_video.mp4")
        with open(self.test_video_path, 'wb') as f:
            f.write(b"fake video content")  # Minimal file for testing
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_project_with_valid_video(self):
        """Test creating a project with a valid video file."""
        # Create project
        project = self.project_manager.create_project(
            video_path=self.test_video_path,
            project_name="Test Project"
        )
        
        # Verify project properties
        assert project.name == "Test Project"
        assert project.video_asset is not None
        assert project.video_asset.path == os.path.abspath(self.test_video_path)
        assert project.subtitle_tracks == []
        assert isinstance(project.export_settings, ExportSettings)
        assert isinstance(project.created_at, datetime)
        assert isinstance(project.modified_at, datetime)
    
    def test_create_project_auto_name(self):
        """Test creating a project with auto-generated name."""
        project = self.project_manager.create_project(self.test_video_path)
        
        # Should auto-generate name based on video filename
        assert "test_video" in project.name
        assert "Karaoke" in project.name
    
    def test_create_project_invalid_video(self):
        """Test creating a project with invalid video file."""
        invalid_path = os.path.join(self.temp_dir, "nonexistent.mp4")
        
        with pytest.raises(ValueError, match="Invalid video file"):
            self.project_manager.create_project(invalid_path)
    
    def test_save_and_load_project(self):
        """Test saving and loading a project."""
        # Create project
        original_project = self.project_manager.create_project(
            self.test_video_path,
            "Save Test Project"
        )
        
        # Save project
        project_path = os.path.join(self.temp_dir, "test_project.ksp")
        success = self.project_manager.save_project(original_project, project_path)
        assert success
        assert os.path.exists(project_path)
        
        # Load project
        loaded_project = self.project_manager.load_project(project_path)
        
        # Verify loaded project matches original
        assert loaded_project.name == original_project.name
        assert loaded_project.video_asset.path == original_project.video_asset.path
        assert loaded_project.export_settings.format == original_project.export_settings.format
    
    def test_load_nonexistent_project(self):
        """Test loading a project that doesn't exist."""
        nonexistent_path = os.path.join(self.temp_dir, "nonexistent.ksp")
        
        with pytest.raises(FileNotFoundError):
            self.project_manager.load_project(nonexistent_path)
    
    def test_import_video(self):
        """Test importing a video file."""
        video_asset = self.project_manager.import_video(self.test_video_path)
        
        assert isinstance(video_asset, VideoAsset)
        assert video_asset.path == os.path.abspath(self.test_video_path)
        assert video_asset.duration > 0  # Should have default duration
        assert video_asset.fps > 0
        assert len(video_asset.resolution) == 2
    
    def test_import_invalid_video(self):
        """Test importing an invalid video file."""
        invalid_path = os.path.join(self.temp_dir, "nonexistent.mp4")
        
        with pytest.raises(ValueError, match="Invalid video file"):
            self.project_manager.import_video(invalid_path)
    
    def test_recent_projects_tracking(self):
        """Test recent projects tracking functionality."""
        # Initially no recent projects
        recent = self.project_manager.get_recent_projects()
        initial_count = len(recent)
        
        # Create and save a project
        project = self.project_manager.create_project(
            self.test_video_path,
            "Recent Test Project"
        )
        project_path = os.path.join(self.temp_dir, "recent_test.ksp")
        self.project_manager.save_project(project, project_path)
        
        # Should appear in recent projects
        recent = self.project_manager.get_recent_projects()
        assert len(recent) == initial_count + 1
        assert recent[0].name == "Recent Test Project"
        assert recent[0].path == project_path
    
    def test_create_default_subtitle_track(self):
        """Test creating a default subtitle track."""
        project = self.project_manager.create_project(self.test_video_path)
        
        # Create default subtitle track
        track = self.project_manager.create_default_subtitle_track(project)
        
        assert track.id is not None
        assert len(track.elements) == 1
        assert track.elements[0].content == "Sample Karaoke Text"
        assert len(track.keyframes) == 3  # Start, show, hide keyframes
        assert track.start_time == 0.0
        assert track.end_time == project.video_asset.duration
    
    def test_duplicate_project(self):
        """Test duplicating an existing project."""
        # Create and save original project
        original_project = self.project_manager.create_project(
            self.test_video_path,
            "Original Project"
        )
        original_path = os.path.join(self.temp_dir, "original.ksp")
        self.project_manager.save_project(original_project, original_path)
        
        # Duplicate project
        new_path = self.project_manager.duplicate_project(
            original_path,
            "Duplicated Project"
        )
        
        assert os.path.exists(new_path)
        assert new_path != original_path
        
        # Load duplicated project and verify
        duplicated_project = self.project_manager.load_project(new_path)
        assert duplicated_project.name == "Duplicated Project"
        assert duplicated_project.video_asset.path == original_project.video_asset.path
    
    def test_delete_project(self):
        """Test deleting a project."""
        # Create and save project
        project = self.project_manager.create_project(self.test_video_path)
        project_path = os.path.join(self.temp_dir, "delete_test.ksp")
        self.project_manager.save_project(project, project_path)
        
        assert os.path.exists(project_path)
        
        # Delete project
        success = self.project_manager.delete_project(project_path)
        assert success
        assert not os.path.exists(project_path)
    
    def test_get_project_info(self):
        """Test getting project information without full loading."""
        # Create and save project
        project = self.project_manager.create_project(
            self.test_video_path,
            "Info Test Project"
        )
        project_path = os.path.join(self.temp_dir, "info_test.ksp")
        self.project_manager.save_project(project, project_path)
        
        # Get project info
        info = self.project_manager.get_project_info(project_path)
        
        assert info is not None
        assert info.name == "Info Test Project"
        assert info.path == project_path
        assert info.last_modified is not None
    
    def test_projects_directory_management(self):
        """Test projects directory management."""
        # Get current directory
        current_dir = self.project_manager.get_projects_directory()
        assert isinstance(current_dir, Path)
        
        # Set new directory
        new_dir = os.path.join(self.temp_dir, "new_projects")
        success = self.project_manager.set_projects_directory(new_dir)
        assert success
        
        # Verify directory was set
        updated_dir = self.project_manager.get_projects_directory()
        assert str(updated_dir) == new_dir
        assert os.path.exists(new_dir)
    
    def test_validate_project_compatibility(self):
        """Test project compatibility validation."""
        project = self.project_manager.create_project(self.test_video_path)
        
        # Validate compatibility
        result = self.project_manager.validate_project_compatibility(project)
        
        # Should be valid (though may have warnings)
        assert isinstance(result.is_valid, bool)
        assert result.metadata is not None


if __name__ == "__main__":
    pytest.main([__file__])