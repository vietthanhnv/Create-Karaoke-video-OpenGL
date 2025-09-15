"""
Export Dialog - Configure video export settings.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton,
    QLabel, QSlider, QDialogButtonBox
)
from PyQt6.QtCore import Qt


class ExportDialog(QDialog):
    """Dialog for configuring video export settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Video")
        self.setModal(True)
        self.resize(400, 500)
        
        self._setup_ui()
        self._set_defaults()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
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
        
        # Bitrate
        self.bitrate_spin = QSpinBox()
        self.bitrate_spin.setRange(1, 100)
        self.bitrate_spin.setSuffix(" Mbps")
        video_layout.addRow("Bitrate:", self.bitrate_spin)
        
        layout.addWidget(video_group)
        
        # Quality settings group
        quality_group = QGroupBox("Quality Settings")
        quality_layout = QFormLayout(quality_group)
        
        # Quality preset
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Draft", "Good", "High", "Best"])
        quality_layout.addRow("Quality Preset:", self.quality_combo)
        
        # Hardware acceleration
        self.hardware_accel = QCheckBox("Use hardware acceleration")
        quality_layout.addRow("", self.hardware_accel)
        
        layout.addWidget(quality_group)
        
        # Audio settings group
        audio_group = QGroupBox("Audio Settings")
        audio_layout = QFormLayout(audio_group)
        
        # Audio codec
        self.audio_codec_combo = QComboBox()
        self.audio_codec_combo.addItems(["AAC", "MP3", "PCM"])
        audio_layout.addRow("Audio Codec:", self.audio_codec_combo)
        
        # Audio bitrate
        self.audio_bitrate_combo = QComboBox()
        self.audio_bitrate_combo.addItems(["128 kbps", "192 kbps", "256 kbps", "320 kbps"])
        audio_layout.addRow("Audio Bitrate:", self.audio_bitrate_combo)
        
        layout.addWidget(audio_group)
        
        # Subtitle settings group
        subtitle_group = QGroupBox("Subtitle Settings")
        subtitle_layout = QFormLayout(subtitle_group)
        
        # Burn-in subtitles
        self.burn_subtitles = QCheckBox("Burn subtitles into video")
        self.burn_subtitles.setChecked(True)
        subtitle_layout.addRow("", self.burn_subtitles)
        
        # Anti-aliasing
        self.antialiasing = QCheckBox("Enable text anti-aliasing")
        self.antialiasing.setChecked(True)
        subtitle_layout.addRow("", self.antialiasing)
        
        layout.addWidget(subtitle_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _set_defaults(self):
        """Set default values."""
        self.resolution_combo.setCurrentText("1920x1080 (Full HD)")
        self.framerate_combo.setCurrentText("30")
        self.bitrate_spin.setValue(8)
        self.quality_combo.setCurrentText("High")
        self.hardware_accel.setChecked(True)
        self.audio_codec_combo.setCurrentText("AAC")
        self.audio_bitrate_combo.setCurrentText("192 kbps")
    
    def get_export_settings(self) -> dict:
        """Get the configured export settings."""
        resolution_text = self.resolution_combo.currentText()
        resolution = self._parse_resolution(resolution_text)
        
        return {
            'resolution': resolution,
            'framerate': float(self.framerate_combo.currentText()),
            'video_bitrate': self.bitrate_spin.value() * 1000000,  # Convert to bps
            'quality_preset': self.quality_combo.currentText().lower(),
            'hardware_acceleration': self.hardware_accel.isChecked(),
            'audio_codec': self.audio_codec_combo.currentText().lower(),
            'audio_bitrate': self._parse_audio_bitrate(self.audio_bitrate_combo.currentText()),
            'burn_subtitles': self.burn_subtitles.isChecked(),
            'antialiasing': self.antialiasing.isChecked()
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
    
    def _parse_audio_bitrate(self, bitrate_text: str) -> int:
        """Parse audio bitrate from combo box text."""
        if "128" in bitrate_text:
            return 128000
        elif "192" in bitrate_text:
            return 192000
        elif "256" in bitrate_text:
            return 256000
        elif "320" in bitrate_text:
            return 320000
        else:
            return 192000  # Default