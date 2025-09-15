#!/usr/bin/env python3
"""
Detailed test script to identify and fix preview and audio import issues.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_preview_system():
    """Test preview system functionality in detail."""
    print("Testing preview system...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        from src.ui.preview_system import PreviewSystem
        
        # Test preview system creation
        preview_system = PreviewSystem()
        print("✓ Preview system created")
        
        # Test preview system methods
        if hasattr(preview_system, 'start_preview'):
            print("✓ Preview system has start_preview method")
        else:
            print("✗ Preview system missing start_preview method")
            return False
        
        if hasattr(preview_system, 'zoom_in'):
            print("✓ Preview system has zoom controls")
        else:
            print("✗ Preview system missing zoom controls")
            return False
        
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import preview system: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing preview system: {e}")
        return False

def test_preview_integration():
    """Test preview integration functionality."""
    print("\nTesting preview integration...")
    
    try:
        from PyQt6.QtWidgets import QApplication, QWidget
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        from src.ui.preview_integration import PreviewIntegration
        
        # Create a dummy widget for testing
        dummy_widget = QWidget()
        
        # Test preview integration creation
        preview_integration = PreviewIntegration(dummy_widget)
        print("✓ Preview integration created")
        
        # Test required methods
        if hasattr(preview_integration, 'initialize'):
            print("✓ Preview integration has initialize method")
        else:
            print("✗ Preview integration missing initialize method")
            return False
        
        if hasattr(preview_integration, 'set_video_source'):
            print("✓ Preview integration has set_video_source method")
        else:
            print("✗ Preview integration missing set_video_source method")
            return False
        
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import preview integration: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing preview integration: {e}")
        return False

def test_audio_import():
    """Test audio import functionality in detail."""
    print("\nTesting audio import...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        from src.core.controller import ApplicationController
        
        controller = ApplicationController()
        if not controller.initialize():
            print("✗ Failed to initialize controller")
            return False
        
        project_manager = controller.get_project_manager()
        
        # Test if import_audio method exists
        if hasattr(project_manager, 'import_audio'):
            print("✓ Project manager has import_audio method")
        else:
            print("✗ Project manager missing import_audio method")
            return False
        
        # Test audio asset handler
        try:
            from src.audio.asset_handler import AudioAssetHandler
            audio_handler = AudioAssetHandler()
            print("✓ Audio asset handler created")
            
            if hasattr(audio_handler, 'load_audio_file'):
                print("✓ Audio handler has load_audio_file method")
            else:
                print("✗ Audio handler missing load_audio_file method")
                return False
                
        except ImportError as e:
            print(f"✗ Failed to import audio asset handler: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing audio import: {e}")
        return False

def test_opengl_renderer():
    """Test OpenGL renderer functionality."""
    print("\nTesting OpenGL renderer...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        from src.graphics.opengl_renderer import OpenGLRenderer
        
        # Test renderer creation
        renderer = OpenGLRenderer()
        print("✓ OpenGL renderer created")
        
        # Test required methods
        if hasattr(renderer, 'initialize_opengl_context'):
            print("✓ Renderer has initialize_opengl_context method")
        else:
            print("✗ Renderer missing initialize_opengl_context method")
            return False
        
        if hasattr(renderer, 'render_frame'):
            print("✓ Renderer has render_frame method")
        else:
            print("✗ Renderer missing render_frame method")
            return False
        
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import OpenGL renderer: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing OpenGL renderer: {e}")
        return False

def test_timeline_engine():
    """Test timeline engine functionality."""
    print("\nTesting timeline engine...")
    
    try:
        from src.core.timeline_engine import TimelineEngine
        
        # Test timeline engine creation
        timeline = TimelineEngine()
        print("✓ Timeline engine created")
        
        # Test required methods
        if hasattr(timeline, 'add_track'):
            print("✓ Timeline has add_track method")
        else:
            print("✗ Timeline missing add_track method")
            return False
        
        if hasattr(timeline, 'get_current_time'):
            print("✓ Timeline has get_current_time method")
        else:
            print("✗ Timeline missing get_current_time method")
            return False
        
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import timeline engine: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing timeline engine: {e}")
        return False

def test_ui_panels():
    """Test UI panel functionality."""
    print("\nTesting UI panels...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Test timeline panel
        from src.ui.timeline_panel import TimelinePanel
        timeline_panel = TimelinePanel()
        print("✓ Timeline panel created")
        
        # Test effect properties panel
        from src.ui.effect_properties_panel import EffectPropertiesPanel
        effects_panel = EffectPropertiesPanel()
        print("✓ Effect properties panel created")
        
        # Test text editor panel
        from src.ui.text_editor_panel import TextEditorPanel
        text_panel = TextEditorPanel()
        print("✓ Text editor panel created")
        
        # Test required signals
        if hasattr(timeline_panel, 'time_changed'):
            print("✓ Timeline panel has time_changed signal")
        else:
            print("✗ Timeline panel missing time_changed signal")
            return False
        
        if hasattr(effects_panel, 'effect_parameter_changed'):
            print("✓ Effects panel has effect_parameter_changed signal")
        else:
            print("✗ Effects panel missing effect_parameter_changed signal")
            return False
        
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import UI panels: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing UI panels: {e}")
        return False

def test_main_window_integration():
    """Test main window integration with controller."""
    print("\nTesting main window integration...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        from src.ui.main_window import MainWindow
        from src.core.controller import ApplicationController
        
        # Create controller
        controller = ApplicationController()
        if not controller.initialize():
            print("✗ Failed to initialize controller")
            return False
        
        # Create main window
        main_window = MainWindow()
        print("✓ Main window created")
        
        # Test controller integration
        main_window.set_controller(controller)
        print("✓ Controller set on main window")
        
        # Test if preview integration was attempted
        if hasattr(main_window, 'preview_integration'):
            print("✓ Main window has preview integration")
        else:
            print("✗ Main window missing preview integration")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing main window integration: {e}")
        return False

def create_test_audio_file():
    """Create a test audio file for testing."""
    print("\nCreating test audio file...")
    
    try:
        import numpy as np
        import wave
        
        # Generate a simple sine wave
        sample_rate = 44100
        duration = 2.0  # 2 seconds
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = np.sin(2 * np.pi * frequency * t)
        
        # Convert to 16-bit integers
        audio_data = (audio_data * 32767).astype(np.int16)
        
        # Save as WAV file
        with wave.open('test_audio.wav', 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        print("✓ Test audio file created: test_audio.wav")
        return True
        
    except ImportError:
        print("✗ NumPy not available for audio generation")
        return False
    except Exception as e:
        print(f"✗ Error creating test audio file: {e}")
        return False

def test_actual_audio_import():
    """Test actual audio file import."""
    print("\nTesting actual audio file import...")
    
    # First create a test audio file
    if not create_test_audio_file():
        print("✗ Cannot test audio import without test file")
        return False
    
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        from src.core.controller import ApplicationController
        
        controller = ApplicationController()
        if not controller.initialize():
            print("✗ Failed to initialize controller")
            return False
        
        project_manager = controller.get_project_manager()
        
        # Try to import the test audio file
        audio_asset = project_manager.import_audio('test_audio.wav')
        
        # Validate the audio asset
        validation_result = audio_asset.validate()
        
        if validation_result.is_valid:
            print("✓ Audio file imported successfully")
            print(f"  Duration: {audio_asset.duration:.2f} seconds")
            print(f"  Sample rate: {audio_asset.sample_rate} Hz")
            return True
        else:
            print(f"✗ Audio import failed: {validation_result.error_message}")
            return False
        
    except Exception as e:
        print(f"✗ Error during audio import test: {e}")
        return False

def main():
    """Run all detailed tests."""
    print("Karaoke Video Creator - Detailed Issue Testing")
    print("=" * 50)
    
    tests = [
        test_preview_system,
        test_preview_integration,
        test_audio_import,
        test_opengl_renderer,
        test_timeline_engine,
        test_ui_panels,
        test_main_window_integration,
        test_actual_audio_import
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Detailed Test Results: {passed}/{total} tests passed")
    
    if passed < total:
        print("\n🔧 Issues Found:")
        print("The following components need attention:")
        print("- Preview system integration")
        print("- Audio import functionality")
        print("- OpenGL renderer initialization")
        print("- UI panel signal connections")
        
        print("\n📋 Next Steps:")
        print("1. Fix missing preview system components")
        print("2. Implement proper audio import handling")
        print("3. Ensure OpenGL context initialization")
        print("4. Connect UI signals properly")
    else:
        print("🎉 All detailed tests passed!")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)