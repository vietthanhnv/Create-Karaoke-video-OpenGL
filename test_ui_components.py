#!/usr/bin/env python3
"""
Test script for UI components - Karaoke Subtitle Creator

Simple test to verify that all UI components can be instantiated and work correctly.
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

def test_ui_components():
    """Test that all UI components can be created and function properly."""
    
    app = QApplication(sys.argv)
    
    try:
        # Test main window creation
        from src.ui.main_window import MainWindow
        main_window = MainWindow()
        print("✓ Main window created successfully")
        
        # Test timeline panel
        from src.ui.timeline_panel import TimelinePanel
        timeline_panel = TimelinePanel()
        print("✓ Timeline panel created successfully")
        
        # Test effect properties panel
        from src.ui.effect_properties_panel import EffectPropertiesPanel
        effects_panel = EffectPropertiesPanel()
        print("✓ Effect properties panel created successfully")
        
        # Test text editor panel
        from src.ui.text_editor_panel import TextEditorPanel
        text_editor = TextEditorPanel()
        print("✓ Text editor panel created successfully")
        
        # Test basic functionality
        print("\nTesting basic functionality:")
        
        # Test timeline controls
        timeline_panel.set_duration(120.0)
        timeline_panel.set_current_time(30.0)
        print("✓ Timeline duration and time setting works")
        
        # Test text editor
        text_editor.set_text_content("Test karaoke text")
        content = text_editor.get_text_content()
        assert content == "Test karaoke text"
        print("✓ Text editor content setting/getting works")
        
        # Test effect parameters
        params = effects_panel.get_effect_parameters("animation")
        print(f"✓ Effect parameters retrieved: {len(params)} parameters")
        
        # Show main window briefly
        main_window.show()
        
        # Close after a short delay
        QTimer.singleShot(1000, app.quit)
        
        print("\n✓ All UI components test passed!")
        print("Main window will be displayed for 1 second...")
        
        return app.exec()
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(test_ui_components())