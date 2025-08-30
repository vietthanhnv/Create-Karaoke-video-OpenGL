#!/usr/bin/env python3
"""
Karaoke Subtitle Creator - Main Entry Point

A professional desktop application for creating karaoke videos with advanced text effects
and real-time OpenGL-based preview capabilities.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication
from src.core.controller import ApplicationController


def main():
    """Main application entry point."""
    # Set application metadata
    QCoreApplication.setApplicationName("Karaoke Subtitle Creator")
    QCoreApplication.setApplicationVersion("1.0.0")
    QCoreApplication.setOrganizationName("Karaoke Subtitle Creator Team")
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Initialize application controller
    controller = ApplicationController()
    
    if not controller.initialize():
        print("Failed to initialize application")
        return 1
    
    try:
        # Create and show main window
        from src.ui.main_window import MainWindow
        main_window = MainWindow(controller)
        main_window.show()
        
        print("Karaoke Subtitle Creator initialized successfully")
        return app.exec()
        
    except Exception as e:
        print(f"Application error: {e}")
        return 1
    
    finally:
        controller.shutdown()


if __name__ == "__main__":
    sys.exit(main())