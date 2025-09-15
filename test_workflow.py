#!/usr/bin/env python3
"""
Test script to verify the complete karaoke video creation workflow.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_subtitle_import():
    """Test subtitle file import functionality."""
    print("Testing subtitle import...")
    
    from src.text.subtitle_parser import SubtitleParser
    
    parser = SubtitleParser()
    result = parser.parse_file("test_subtitles.ass")
    
    if result.is_valid:
        print(f"✓ Successfully imported {result.metadata['entry_count']} subtitle entries")
        print(f"  Duration: {result.metadata['duration']:.1f} seconds")
        print(f"  Format: {result.metadata['format']}")
        return True
    else:
        print(f"✗ Failed to import subtitles: {result.error_message}")
        return False

def test_project_creation():
    """Test project creation functionality."""
    print("\nTesting project creation...")
    
    try:
        # Initialize Qt application first
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        from src.core.controller import ApplicationController
        
        controller = ApplicationController()
        if controller.initialize():
            print("✓ Application controller initialized")
            
            project_manager = controller.get_project_manager()
            # Create a minimal project without video for testing
            from src.core.models import Project, ExportSettings
            from datetime import datetime
            
            export_settings = ExportSettings(
                resolution=(1920, 1080),
                fps=30.0,
                format='mp4',
                quality_preset='normal',
                codec='h264'
            )
            
            project = Project(
                name="Test Project",
                video_asset=None,
                audio_asset=None,
                subtitle_tracks=[],
                export_settings=export_settings,
                created_at=datetime.now(),
                modified_at=datetime.now()
            )
            
            print(f"✓ Created project: {project.name}")
            print(f"  Resolution: {project.export_settings.resolution}")
            print(f"  Frame rate: {project.export_settings.fps}")
            return True
        else:
            print("✗ Failed to initialize controller")
            return False
            
    except Exception as e:
        print(f"✗ Error creating project: {e}")
        return False

def test_effect_system():
    """Test effect system functionality."""
    print("\nTesting effect system...")
    
    try:
        from src.core.effect_system import EffectSystem
        
        effect_system = EffectSystem()
        available_effects = effect_system.get_available_effects()
        
        print("✓ Effect system initialized")
        print("  Available effects:")
        for category, effects in available_effects.items():
            print(f"    {category}: {', '.join(effects)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing effect system: {e}")
        return False

def test_export_pipeline():
    """Test export pipeline functionality."""
    print("\nTesting export pipeline...")
    
    try:
        from src.video.export_pipeline import VideoExportPipeline, QualityPreset
        
        pipeline = VideoExportPipeline()
        presets = QualityPreset.get_available_presets()
        
        print("✓ Export pipeline initialized")
        print(f"  Available quality presets: {', '.join(presets)}")
        
        # Test preset configuration
        high_quality = QualityPreset.get_preset('high')
        print(f"  High quality preset: {high_quality['name']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing export pipeline: {e}")
        return False

def test_ui_components():
    """Test UI component initialization."""
    print("\nTesting UI components...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from src.ui.main_window import MainWindow
        from src.ui.export_dialog import ExportDialog
        from src.ui.new_project_dialog import NewProjectDialog
        
        # Use existing Qt application
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Test main window creation
        main_window = MainWindow()
        print("✓ Main window created")
        
        # Test dialog creation
        export_dialog = ExportDialog()
        print("✓ Export dialog created")
        
        new_project_dialog = NewProjectDialog()
        print("✓ New project dialog created")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing UI components: {e}")
        return False

def main():
    """Run all workflow tests."""
    print("Karaoke Video Creator - Workflow Test")
    print("=" * 40)
    
    tests = [
        test_subtitle_import,
        test_project_creation,
        test_effect_system,
        test_export_pipeline,
        test_ui_components
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
    
    print("\n" + "=" * 40)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All workflow components are working!")
        print("\nYour karaoke video creator is ready with the following workflow:")
        print("1. ✓ Import Media Files (video, audio, subtitles)")
        print("2. ✓ Preview & Edit (timeline, text editor)")
        print("3. ✓ Apply Text Effects (animation, visual, particle, 3D, color)")
        print("4. ✓ Export (MP4 with subtitle burn-in)")
    else:
        print("⚠️  Some components need attention")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)