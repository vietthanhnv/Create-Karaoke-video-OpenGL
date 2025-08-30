"""
Integration tests for ProjectManager with ApplicationController.
"""

import os
import tempfile
import pytest
from pathlib import Path

from src.core.controller import ApplicationController


class TestProjectManagerIntegration:
    """Integration test cases for ProjectManager through ApplicationController."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.controller = ApplicationController()
        
        # Create a mock video file for testing
        self.test_video_path = os.path.join(self.temp_dir, "test_video.mp4")
        with open(self.test_video_path, 'wb') as f:
            f.write(b"fake video content")
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        if hasattr(self, 'controller'):
            self.controller.shutdown()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_controller_initialization_with_project_manager(self):
        """Test that controller initializes ProjectManager correctly."""
        # Initialize controller
        success = self.controller.initialize()
        assert success
        
        # Should be able to get project manager
        project_manager = self.controller.get_project_manager()
        assert project_manager is not None
        
        # Should be able to get validation system
        validation_system = self.controller.get_validation_system()
        assert validation_system is not None
    
    def test_create_project_through_controller(self):
        """Test creating a project through the controller."""
        # Initialize controller
        self.controller.initialize()
        
        # Get project manager
        project_manager = self.controller.get_project_manager()
        
        # Create project
        project = project_manager.create_project(
            self.test_video_path,
            "Controller Test Project"
        )
        
        # Set as current project
        self.controller.set_current_project(project)
        
        # Verify current project
        current_project = self.controller.get_current_project()
        assert current_project is not None
        assert current_project.name == "Controller Test Project"
    
    def test_project_workflow_through_controller(self):
        """Test complete project workflow through controller."""
        # Initialize controller
        self.controller.initialize()
        project_manager = self.controller.get_project_manager()
        
        # Create project
        project = project_manager.create_project(self.test_video_path)
        
        # Add default subtitle track
        subtitle_track = project_manager.create_default_subtitle_track(project)
        project.subtitle_tracks.append(subtitle_track)
        
        # Save project
        project_path = os.path.join(self.temp_dir, "workflow_test.ksp")
        success = project_manager.save_project(project, project_path)
        assert success
        
        # Load project back
        loaded_project = project_manager.load_project(project_path)
        assert loaded_project.name == project.name
        assert len(loaded_project.subtitle_tracks) == 1
        
        # Set as current project
        self.controller.set_current_project(loaded_project)
        
        # Verify everything is working
        current = self.controller.get_current_project()
        assert current is not None
        assert len(current.subtitle_tracks) == 1
        assert current.subtitle_tracks[0].elements[0].content == "Sample Karaoke Text"


if __name__ == "__main__":
    pytest.main([__file__])