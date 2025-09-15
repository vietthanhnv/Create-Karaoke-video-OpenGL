"""
New Project Dialog - Configure new project settings.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QComboBox, QSpinBox, QDialogButtonBox, QLabel
)
from PyQt6.QtCore import Qt


class NewProjectDialog(QDialog):
    """Dialog for creating a new project with initial settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Project")
        self.setModal(True)
        self.resize(400, 300)
        
        self._setup_ui()
        self._set_defaults()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Project info group
        info_group = QGroupBox("Project Information")
        info_layout = QFormLayout(info_group)
        
        # Project name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter project name...")
        info_layout.addRow("Project Name:", self.name_edit)
        
        layout.addWidget(info_group)
        
        # Video settings group
        video_group = QGroupBox("Video Settings")
        video_layout = QFormLayout(video_group)
        
        # Resolution
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems([
            "1920x1080 (Full HD)",
            "1280x720 (HD)",
            "3840x2160 (4K)",
            "2560x1440 (2K)",
            "854x480 (SD)"
        ])
        video_layout.addRow("Resolution:", self.resolution_combo)
        
        # Frame rate
        self.framerate_combo = QComboBox()
        self.framerate_combo.addItems(["24", "25", "30", "50", "60"])
        video_layout.addRow("Frame Rate:", self.framerate_combo)
        
        layout.addWidget(video_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _set_defaults(self):
        """Set default values."""
        self.name_edit.setText("Untitled Project")
        self.resolution_combo.setCurrentText("1920x1080 (Full HD)")
        self.framerate_combo.setCurrentText("30")
    
    def _validate_and_accept(self):
        """Validate input and accept dialog."""
        if not self.name_edit.text().strip():
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Invalid Input", "Please enter a project name.")
            return
        
        self.accept()
    
    def get_project_settings(self) -> dict:
        """Get the configured project settings."""
        resolution_text = self.resolution_combo.currentText()
        resolution = self._parse_resolution(resolution_text)
        
        return {
            'name': self.name_edit.text().strip(),
            'resolution': resolution,
            'framerate': float(self.framerate_combo.currentText())
        }
    
    def _parse_resolution(self, resolution_text: str) -> tuple:
        """Parse resolution from combo box text."""
        if "1920x1080" in resolution_text:
            return (1920, 1080)
        elif "1280x720" in resolution_text:
            return (1280, 720)
        elif "3840x2160" in resolution_text:
            return (3840, 2160)
        elif "2560x1440" in resolution_text:
            return (2560, 1440)
        elif "854x480" in resolution_text:
            return (854, 480)
        else:
            return (1920, 1080)  # Default