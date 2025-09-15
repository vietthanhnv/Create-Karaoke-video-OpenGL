"""
Export Progress Dialog - Shows progress during video export.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QTextEdit, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont


class ExportProgressDialog(QDialog):
    """Dialog showing export progress with detailed information."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exporting Video...")
        self.setModal(True)
        self.resize(500, 400)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint)
        
        self._setup_ui()
        self._export_finished = False
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Progress section
        progress_group = QGroupBox("Export Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        # Overall progress
        self.overall_label = QLabel("Preparing export...")
        progress_layout.addWidget(self.overall_label)
        
        self.overall_progress = QProgressBar()
        self.overall_progress.setRange(0, 100)
        progress_layout.addWidget(self.overall_progress)
        
        # Current operation
        self.operation_label = QLabel("Initializing...")
        progress_layout.addWidget(self.operation_label)
        
        # Time information
        time_layout = QHBoxLayout()
        self.elapsed_label = QLabel("Elapsed: 00:00")
        self.eta_label = QLabel("ETA: --:--")
        time_layout.addWidget(self.elapsed_label)
        time_layout.addStretch()
        time_layout.addWidget(self.eta_label)
        progress_layout.addLayout(time_layout)
        
        layout.addWidget(progress_group)
        
        # Details section
        details_group = QGroupBox("Export Details")
        details_layout = QVBoxLayout(details_group)
        
        self.details_text = QTextEdit()
        self.details_text.setMaximumHeight(150)
        self.details_text.setFont(QFont("Consolas", 9))
        details_layout.addWidget(self.details_text)
        
        layout.addWidget(details_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._cancel_export)
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addStretch()
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        self.close_button.setEnabled(False)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        # Timer for elapsed time
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_elapsed_time)
        self.timer.start(1000)  # Update every second
        self.start_time = None
    
    @pyqtSlot(dict)
    def update_progress(self, progress_info: dict):
        """Update progress information."""
        if not self.start_time:
            from time import time
            self.start_time = time()
        
        # Update progress bar
        progress = progress_info.get('progress', 0)
        self.overall_progress.setValue(int(progress))
        
        # Update labels
        operation = progress_info.get('operation', 'Processing...')
        self.operation_label.setText(operation)
        
        frame_info = progress_info.get('frame_info', '')
        if frame_info:
            self.overall_label.setText(f"Frame {frame_info}")
        
        # Update ETA
        if progress > 0:
            from time import time
            elapsed = time() - self.start_time
            total_time = elapsed / (progress / 100.0)
            remaining = total_time - elapsed
            
            eta_minutes = int(remaining // 60)
            eta_seconds = int(remaining % 60)
            self.eta_label.setText(f"ETA: {eta_minutes:02d}:{eta_seconds:02d}")
        
        # Add to details
        details = progress_info.get('details', '')
        if details:
            self.details_text.append(details)
            # Auto-scroll to bottom
            scrollbar = self.details_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    @pyqtSlot()
    def export_finished(self):
        """Handle export completion."""
        self._export_finished = True
        self.overall_progress.setValue(100)
        self.overall_label.setText("Export completed successfully!")
        self.operation_label.setText("Finished")
        self.cancel_button.setEnabled(False)
        self.close_button.setEnabled(True)
        self.timer.stop()
        
        self.details_text.append("Export completed successfully!")
    
    @pyqtSlot(str)
    def export_error(self, error_message: str):
        """Handle export error."""
        self._export_finished = True
        self.overall_label.setText("Export failed!")
        self.operation_label.setText(f"Error: {error_message}")
        self.cancel_button.setText("Close")
        self.close_button.setEnabled(True)
        self.timer.stop()
        
        self.details_text.append(f"ERROR: {error_message}")
    
    def _update_elapsed_time(self):
        """Update elapsed time display."""
        if self.start_time:
            from time import time
            elapsed = time() - self.start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            self.elapsed_label.setText(f"Elapsed: {minutes:02d}:{seconds:02d}")
    
    def _cancel_export(self):
        """Cancel the export process."""
        if self._export_finished:
            self.reject()
        else:
            # TODO: Implement actual export cancellation
            self.reject()
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        if not self._export_finished:
            # Ask for confirmation if export is in progress
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                "Cancel Export",
                "Export is in progress. Are you sure you want to cancel?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()