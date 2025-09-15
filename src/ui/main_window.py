#!/usr/bin/env python3
"""
Main Window - Karaoke Subtitle Creator

Main application window with menu bar, toolbar, and docked panels for
timeline editing, effect properties, and text formatting.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QToolBar, QStatusBar, QDockWidget, QLabel,
    QFileDialog, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QKeySequence, QIcon, QAction, QActionGroup

from .timeline_panel import TimelinePanel
from .effect_properties_panel import EffectPropertiesPanel
from .text_editor_panel import TextEditorPanel
from .preview_system import PreviewSystem


class MainWindow(QMainWindow):
    """
    Main application window providing the primary user interface for the
    Karaoke Subtitle Creator application.
    """
    
    # Signals
    project_opened = pyqtSignal(str)  # project_path
    project_saved = pyqtSignal(str)   # project_path
    project_closed = pyqtSignal()
    
    def __init__(self, controller=None):
        """
        Initialize the main window.
        
        Args:
            controller: Application controller instance
        """
        super().__init__()
        self.controller = controller
        self.current_project_path = None
        
        # Initialize UI components
        self._setup_window()
        self._create_menu_bar()
        self._create_toolbar()
        self._create_central_widget()
        self._create_dock_panels()
        self._create_status_bar()
        self._setup_connections()
        
        # Set up keyboard shortcuts
        self._setup_keyboard_shortcuts()
        
        # Set initial state
        self._update_window_title()
        self._update_ui_state()
    
    def _setup_window(self):
        """Configure main window properties."""
        self.setWindowTitle("Karaoke Subtitle Creator")
        self.setMinimumSize(1200, 800)
        self.resize(1600, 1000)
        
        # Set window icon (placeholder for now)
        # self.setWindowIcon(QIcon("assets/icons/app_icon.png"))
    
    def _create_menu_bar(self):
        """Create the main menu bar."""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("&File")
        
        # New Project
        new_action = QAction("&New Project...", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.setStatusTip("Create a new karaoke project")
        new_action.triggered.connect(self._new_project)
        file_menu.addAction(new_action)
        
        # Open Project
        open_action = QAction("&Open Project...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.setStatusTip("Open an existing project")
        open_action.triggered.connect(self._open_project)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # Save Project
        self.save_action = QAction("&Save Project", self)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_action.setStatusTip("Save the current project")
        self.save_action.triggered.connect(self._save_project)
        file_menu.addAction(self.save_action)
        
        # Save As
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.setStatusTip("Save project with a new name")
        save_as_action.triggered.connect(self._save_project_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # Import Video
        import_video_action = QAction("Import &Video...", self)
        import_video_action.setStatusTip("Import video file for the project")
        import_video_action.triggered.connect(self._import_video)
        file_menu.addAction(import_video_action)
        
        # Import Audio
        import_audio_action = QAction("Import &Audio...", self)
        import_audio_action.setStatusTip("Import audio file for the project")
        import_audio_action.triggered.connect(self._import_audio)
        file_menu.addAction(import_audio_action)
        
        # Import Subtitles
        import_subtitles_action = QAction("Import &Subtitles...", self)
        import_subtitles_action.setStatusTip("Import subtitle file (.ass, .srt, .vtt)")
        import_subtitles_action.triggered.connect(self._import_subtitles)
        file_menu.addAction(import_subtitles_action)
        
        file_menu.addSeparator()
        
        # Export
        export_action = QAction("&Export Video...", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.setStatusTip("Export the project as a video file")
        export_action.triggered.connect(self._export_video)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Exit
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit Menu
        edit_menu = menubar.addMenu("&Edit")
        
        # Undo/Redo
        self.undo_action = QAction("&Undo", self)
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo_action.setEnabled(False)
        edit_menu.addAction(self.undo_action)
        
        self.redo_action = QAction("&Redo", self)
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.redo_action.setEnabled(False)
        edit_menu.addAction(self.redo_action)
        
        edit_menu.addSeparator()
        
        # Copy/Paste Keyframes
        copy_keyframes_action = QAction("&Copy Keyframes", self)
        copy_keyframes_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_keyframes_action.setStatusTip("Copy selected keyframes")
        edit_menu.addAction(copy_keyframes_action)
        
        paste_keyframes_action = QAction("&Paste Keyframes", self)
        paste_keyframes_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_keyframes_action.setStatusTip("Paste keyframes at current position")
        edit_menu.addAction(paste_keyframes_action)
        
        # View Menu
        view_menu = menubar.addMenu("&View")
        
        # Zoom controls
        self.zoom_in_action = QAction("Zoom &In", self)
        self.zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        self.zoom_in_action.setStatusTip("Zoom in on the preview")
        view_menu.addAction(self.zoom_in_action)
        
        self.zoom_out_action = QAction("Zoom &Out", self)
        self.zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        self.zoom_out_action.setStatusTip("Zoom out on the preview")
        view_menu.addAction(self.zoom_out_action)
        
        self.zoom_fit_action = QAction("&Fit to Window", self)
        self.zoom_fit_action.setShortcut(QKeySequence("Ctrl+0"))
        self.zoom_fit_action.setStatusTip("Fit preview to window")
        view_menu.addAction(self.zoom_fit_action)
        
        view_menu.addSeparator()
        
        # Panel visibility toggles (will be connected to dock widgets)
        self.timeline_panel_action = QAction("&Timeline Panel", self)
        self.timeline_panel_action.setCheckable(True)
        self.timeline_panel_action.setChecked(True)
        view_menu.addAction(self.timeline_panel_action)
        
        self.effects_panel_action = QAction("&Effects Panel", self)
        self.effects_panel_action.setCheckable(True)
        self.effects_panel_action.setChecked(True)
        view_menu.addAction(self.effects_panel_action)
        
        self.text_editor_action = QAction("Text &Editor", self)
        self.text_editor_action.setCheckable(True)
        self.text_editor_action.setChecked(True)
        view_menu.addAction(self.text_editor_action)
        
        # Help Menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.setStatusTip("About Karaoke Subtitle Creator")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_toolbar(self):
        """Create the main toolbar."""
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        
        # Playback controls
        self.play_action = QAction("Play", self)
        self.play_action.setStatusTip("Play/Pause video")
        self.play_action.setCheckable(True)
        toolbar.addAction(self.play_action)
        
        self.stop_action = QAction("Stop", self)
        self.stop_action.setStatusTip("Stop playback")
        toolbar.addAction(self.stop_action)
        
        toolbar.addSeparator()
        
        # Timeline controls
        self.add_track_action = QAction("Add Track", self)
        self.add_track_action.setStatusTip("Add new subtitle track")
        toolbar.addAction(self.add_track_action)
        
        self.add_keyframe_action = QAction("Add Keyframe", self)
        self.add_keyframe_action.setStatusTip("Add keyframe at current position")
        toolbar.addAction(self.add_keyframe_action)
        
        toolbar.addSeparator()
        
        # Preview quality
        quality_group = QActionGroup(self)
        
        draft_quality = QAction("Draft", self)
        draft_quality.setCheckable(True)
        draft_quality.setStatusTip("Draft quality preview")
        quality_group.addAction(draft_quality)
        toolbar.addAction(draft_quality)
        
        normal_quality = QAction("Normal", self)
        normal_quality.setCheckable(True)
        normal_quality.setChecked(True)
        normal_quality.setStatusTip("Normal quality preview")
        quality_group.addAction(normal_quality)
        toolbar.addAction(normal_quality)
        
        high_quality = QAction("High", self)
        high_quality.setCheckable(True)
        high_quality.setStatusTip("High quality preview")
        quality_group.addAction(high_quality)
        toolbar.addAction(high_quality)
    
    def _create_central_widget(self):
        """Create the central widget with preview system."""
        # Create central widget with preview system
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create preview widget (placeholder for now)
        self.preview_widget = QWidget()
        self.preview_widget.setStyleSheet("background-color: #2b2b2b; border: 1px solid #555;")
        
        preview_layout = QVBoxLayout(self.preview_widget)
        preview_label = QLabel("OpenGL Preview Area")
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_label.setStyleSheet("color: #888; font-size: 18px;")
        preview_layout.addWidget(preview_label)
        
        layout.addWidget(self.preview_widget)
        
        # Create preview system (non-widget)
        self.preview_system = PreviewSystem()
        
        # Create preview integration (will be initialized when controller is set)
        from .preview_integration import PreviewIntegration
        self.preview_integration = PreviewIntegration(self.preview_widget)
    
    def _create_dock_panels(self):
        """Create dockable panels for timeline, effects, and text editing."""
        # Timeline Panel (bottom dock)
        self.timeline_dock = QDockWidget("Timeline", self)
        self.timeline_panel = TimelinePanel()
        self.timeline_dock.setWidget(self.timeline_panel)
        self.timeline_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.timeline_dock)
        
        # Effect Properties Panel (right dock)
        self.effects_dock = QDockWidget("Effect Properties", self)
        self.effects_panel = EffectPropertiesPanel()
        self.effects_dock.setWidget(self.effects_panel)
        self.effects_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.effects_dock)
        
        # Text Editor Panel (right dock, tabbed with effects)
        self.text_editor_dock = QDockWidget("Text Editor", self)
        self.text_editor_panel = TextEditorPanel()
        self.text_editor_dock.setWidget(self.text_editor_panel)
        self.text_editor_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.text_editor_dock)
        
        # Tab the text editor with effects panel
        self.tabifyDockWidget(self.effects_dock, self.text_editor_dock)
        self.effects_dock.raise_()  # Show effects panel by default
    
    def _create_status_bar(self):
        """Create the status bar."""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
        # Add permanent widgets for frame info, etc.
        # These will be updated by the timeline system
    
    def _setup_connections(self):
        """Set up signal connections between components."""
        # Connect dock widget visibility to menu actions
        self.timeline_dock.visibilityChanged.connect(self.timeline_panel_action.setChecked)
        self.effects_dock.visibilityChanged.connect(self.effects_panel_action.setChecked)
        self.text_editor_dock.visibilityChanged.connect(self.text_editor_action.setChecked)
        
        # Connect menu actions to dock widget visibility
        self.timeline_panel_action.toggled.connect(self.timeline_dock.setVisible)
        self.effects_panel_action.toggled.connect(self.effects_dock.setVisible)
        self.text_editor_action.toggled.connect(self.text_editor_dock.setVisible)
        
        # Connect effect parameter controls to real-time preview updates
        self.effects_panel.effect_parameter_changed.connect(self._on_effect_parameter_changed)
        
        # Connect timeline scrubbing to synchronized preview
        self.timeline_panel.time_changed.connect(self._on_timeline_time_changed)
        self.timeline_panel.keyframe_selected.connect(self._on_keyframe_selected)
        
        # Connect text editor changes to preview updates
        self.text_editor_panel.text_changed.connect(self._on_text_changed)
        self.text_editor_panel.formatting_changed.connect(self._on_text_formatting_changed)
        
        # Connect preview system signals
        self.preview_system.fps_updated.connect(self._on_preview_fps_updated)
        self.preview_system.performance_warning.connect(self._on_performance_warning)
        
        # Connect toolbar actions to preview controls
        self.play_action.toggled.connect(self._on_playback_toggled)
        self.stop_action.triggered.connect(self._on_playback_stopped)
        
        # Connect zoom controls to preview viewport
        self.zoom_in_action.triggered.connect(self.preview_system.zoom_in)
        self.zoom_out_action.triggered.connect(self.preview_system.zoom_out)
        self.zoom_fit_action.triggered.connect(self.preview_system.zoom_to_fit)
    
    def _update_window_title(self):
        """Update window title based on current project."""
        if self.current_project_path:
            project_name = self.current_project_path.split('/')[-1]
            self.setWindowTitle(f"Karaoke Subtitle Creator - {project_name}")
        else:
            self.setWindowTitle("Karaoke Subtitle Creator")
    
    def _update_ui_state(self):
        """Update UI state based on current project and selection."""
        has_project = self.current_project_path is not None
        
        # Enable/disable actions based on project state
        self.save_action.setEnabled(has_project)
        # Add more state updates as needed
    
    def set_controller(self, controller):
        """
        Set the application controller and initialize integration.
        
        Args:
            controller: Application controller instance
        """
        self.controller = controller
        
        # Initialize preview integration if controller has required components
        try:
            if hasattr(controller, 'get_timeline_engine') and hasattr(controller, 'get_render_engine'):
                timeline_engine = controller.get_timeline_engine()
                render_engine = controller.get_render_engine()
                
                # Initialize preview integration
                success = self.preview_integration.initialize(
                    render_engine, timeline_engine, self.preview_system
                )
                
                if success:
                    # Connect integration signals
                    self.preview_integration.render_complete.connect(self._on_render_complete)
                    self.preview_integration.performance_update.connect(self._on_performance_update)
                    self.preview_integration.error_occurred.connect(self._on_integration_error)
                    
                    # Start preview system
                    self.preview_system.start_preview()
                    
        except Exception as e:
            self.status_bar.showMessage(f"Failed to initialize preview: {str(e)}", 5000)
    
    def _on_render_complete(self):
        """Handle render completion from integration."""
        # Could update UI indicators or trigger other actions
        pass
    
    def _on_performance_update(self, metrics: dict):
        """Handle performance updates from integration."""
        fps = metrics.get('fps', 0.0)
        self.status_bar.showMessage(f"FPS: {fps:.1f}", 1000)
    
    def _on_integration_error(self, error: str):
        """Handle integration errors."""
        self.status_bar.showMessage(f"Preview error: {error}", 5000)
    
    # Menu action handlers
    def _new_project(self):
        """Handle new project creation."""
        if self.controller:
            try:
                # Show new project dialog
                from .new_project_dialog import NewProjectDialog
                dialog = NewProjectDialog(self)
                
                if dialog.exec() == dialog.DialogCode.Accepted:
                    project_settings = dialog.get_project_settings()
                    
                    project_manager = self.controller.get_project_manager()
                    project = project_manager.create_project(
                        project_settings['name'],
                        project_settings['resolution'],
                        project_settings['framerate']
                    )
                    
                    self.controller.set_current_project(project)
                    self.current_project_path = None  # New project, not saved yet
                    self._update_window_title()
                    self._update_ui_state()
                    
                    self.status_bar.showMessage("New project created", 3000)
                    
            except ImportError:
                # Fallback for missing dialog
                project_manager = self.controller.get_project_manager()
                project = project_manager.create_project("Untitled Project", (1920, 1080), 30.0)
                self.controller.set_current_project(project)
                self.current_project_path = None
                self._update_window_title()
                self._update_ui_state()
                self.status_bar.showMessage("New project created", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Project Error", f"Error creating project:\n{str(e)}")
        else:
            QMessageBox.information(self, "New Project", "Controller not initialized")
    
    def _open_project(self):
        """Handle project opening."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Project",
            "",
            "Karaoke Projects (*.ksp);;All Files (*)"
        )
        
        if file_path:
            self.current_project_path = file_path
            self.project_opened.emit(file_path)
            self._update_window_title()
            self._update_ui_state()
    
    def _save_project(self):
        """Handle project saving."""
        if self.current_project_path:
            self.project_saved.emit(self.current_project_path)
        else:
            self._save_project_as()
    
    def _save_project_as(self):
        """Handle save as functionality."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Project As",
            "",
            "Karaoke Projects (*.ksp);;All Files (*)"
        )
        
        if file_path:
            self.current_project_path = file_path
            self.project_saved.emit(file_path)
            self._update_window_title()
            self._update_ui_state()
    
    def _import_video(self):
        """Handle video import."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Video",
            "",
            "Video Files (*.mp4 *.mov *.avi *.mkv);;All Files (*)"
        )
        
        if file_path and self.controller:
            try:
                project_manager = self.controller.get_project_manager()
                result = project_manager.import_video(file_path)
                
                if result.is_valid:
                    self.status_bar.showMessage(f"Video imported: {file_path}", 3000)
                    # Update preview with new video
                    if hasattr(self.preview_integration, 'set_video_source'):
                        self.preview_integration.set_video_source(file_path)
                else:
                    QMessageBox.warning(self, "Import Failed", f"Failed to import video:\n{result.error_message}")
                    
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Error importing video:\n{str(e)}")
    
    def _import_audio(self):
        """Handle audio import."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Audio",
            "",
            "Audio Files (*.mp3 *.wav *.aac *.flac);;All Files (*)"
        )
        
        if file_path and self.controller:
            try:
                project_manager = self.controller.get_project_manager()
                audio_asset = project_manager.import_audio(file_path)
                
                # Validate the imported audio asset
                validation_result = audio_asset.validate()
                
                if validation_result.is_valid:
                    self.status_bar.showMessage(f"Audio imported: {file_path}", 3000)
                    # Update timeline with audio waveform
                    if hasattr(self.timeline_panel, 'set_audio_source'):
                        self.timeline_panel.set_audio_source(file_path)
                else:
                    QMessageBox.warning(self, "Import Failed", f"Failed to import audio:\n{validation_result.error_message}")
                    
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Error importing audio:\n{str(e)}")
    
    def _import_subtitles(self):
        """Handle subtitle file import."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Subtitles",
            "",
            "Subtitle Files (*.ass *.srt *.vtt);;ASS Files (*.ass);;SRT Files (*.srt);;WebVTT Files (*.vtt);;All Files (*)"
        )
        
        if file_path:
            try:
                from src.text.subtitle_parser import SubtitleParser
                
                parser = SubtitleParser()
                result = parser.parse_file(file_path)
                
                if result.is_valid:
                    subtitle_track = result.metadata['subtitle_track']
                    entry_count = result.metadata['entry_count']
                    duration = result.metadata['duration']
                    
                    # Show success message
                    QMessageBox.information(
                        self,
                        "Import Successful",
                        f"Successfully imported {entry_count} subtitle entries.\n"
                        f"Duration: {duration:.1f} seconds\n"
                        f"Track ID: {subtitle_track.id}"
                    )
                    
                    # Add to timeline if controller is available
                    if self.controller:
                        try:
                            timeline_engine = self.controller.get_timeline_engine()
                            timeline_engine.add_track(subtitle_track)
                            
                            # Update timeline panel
                            if hasattr(self.timeline_panel, 'add_subtitle_track'):
                                self.timeline_panel.add_subtitle_track(subtitle_track)
                        except Exception as e:
                            self.status_bar.showMessage(f"Error adding to timeline: {str(e)}", 3000)
                    
                    # Update UI
                    self._update_ui_state()
                    
                else:
                    QMessageBox.warning(
                        self,
                        "Import Failed",
                        f"Failed to import subtitles:\n{result.error_message}"
                    )
                    
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Import Error",
                    f"An error occurred while importing subtitles:\n{str(e)}"
                )
    
    def _export_video(self):
        """Handle video export."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Video",
            "",
            "Video Files (*.mp4 *.mov *.avi);;MP4 Files (*.mp4);;MOV Files (*.mov);;AVI Files (*.avi)"
        )
        
        if file_path and self.controller:
            try:
                # Show export dialog for settings
                from .export_dialog import ExportDialog
                export_dialog = ExportDialog(self)
                
                if export_dialog.exec() == export_dialog.DialogCode.Accepted:
                    export_settings = export_dialog.get_export_settings()
                    
                    # Start export process
                    project = self.controller.get_current_project()
                    if project:
                        from ..video.export_pipeline import VideoExportPipeline
                        export_pipeline = VideoExportPipeline()
                        
                        # Show progress dialog
                        from .export_progress_dialog import ExportProgressDialog
                        progress_dialog = ExportProgressDialog(self)
                        
                        # Connect export signals
                        export_pipeline.progress_updated.connect(progress_dialog.update_progress)
                        export_pipeline.export_complete.connect(progress_dialog.export_finished)
                        export_pipeline.export_error.connect(progress_dialog.export_error)
                        
                        # Start export
                        export_pipeline.export_project(project, file_path, export_settings)
                        progress_dialog.exec()
                    else:
                        QMessageBox.warning(self, "Export Failed", "No project loaded to export")
                        
            except ImportError:
                # Fallback for missing export dialogs
                QMessageBox.information(self, "Export", f"Export functionality will save to: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Error during export:\n{str(e)}")
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Karaoke Subtitle Creator",
            "Karaoke Subtitle Creator v1.0.0\n\n"
            "A professional desktop application for creating karaoke videos "
            "with advanced text effects and real-time OpenGL-based preview capabilities."
        )
    
    # Signal handlers for UI integration
    def _on_effect_parameter_changed(self, category: str, parameter: str, value):
        """Handle effect parameter changes and update preview in real-time."""
        if not self.controller:
            return
        
        try:
            # Update effect parameter in preview integration for real-time feedback
            self.preview_integration.update_effect_parameter(category, parameter, value)
            
            # Get current timeline selection
            selected_track = self.timeline_panel.get_selected_track_id()
            current_time = self.timeline_panel.current_time
            
            if selected_track:
                # Update effect parameters in the timeline engine
                timeline_engine = self.controller.get_timeline_engine()
                
                # Create or update keyframe with new effect parameters
                properties = {f"{category}_{parameter}": value}
                timeline_engine.add_keyframe(selected_track, current_time, properties)
                
        except Exception as e:
            self.status_bar.showMessage(f"Error updating effect: {str(e)}", 3000)
    
    def _on_timeline_time_changed(self, time: float):
        """Handle timeline scrubbing and synchronize preview."""
        try:
            # Update preview integration with new timeline position
            self.preview_integration.update_timeline_position(time)
            
            # Update status bar with current time
            minutes = int(time // 60)
            seconds = time % 60
            self.status_bar.showMessage(f"Time: {minutes:02d}:{seconds:05.2f}")
            
        except Exception as e:
            self.status_bar.showMessage(f"Error seeking: {str(e)}", 3000)
    
    def _on_keyframe_selected(self, track_id: str, time: float):
        """Handle keyframe selection and update effect properties panel."""
        try:
            if not self.controller:
                return
            
            timeline_engine = self.controller.get_timeline_engine()
            
            # Get keyframe properties at selected time
            properties = timeline_engine.interpolate_properties(track_id, time)
            
            # Update effect properties panel with keyframe data
            self.effects_panel.update_selection(track_id, time)
            
            # Load effect parameters from keyframe
            for category in ['animation', 'visual', 'transform', 'color', 'particle']:
                category_params = {}
                for key, value in properties.items():
                    if key.startswith(f"{category}_"):
                        param_name = key[len(f"{category}_"):]
                        category_params[param_name] = value
                
                if category_params:
                    self.effects_panel.set_effect_parameters(category, category_params)
            
        except Exception as e:
            self.status_bar.showMessage(f"Error loading keyframe: {str(e)}", 3000)
    
    def _on_text_changed(self, text: str):
        """Handle text content changes and update preview."""
        try:
            # Get current selection
            selected_track = self.timeline_panel.get_selected_track_id()
            current_time = self.timeline_panel.current_time
            
            if selected_track and self.controller:
                timeline_engine = self.controller.get_timeline_engine()
                
                # Update text content in keyframe
                properties = {'text_content': text}
                timeline_engine.add_keyframe(selected_track, current_time, properties)
                
                # Trigger preview update
                self.preview_system.seek(current_time)
                
        except Exception as e:
            self.status_bar.showMessage(f"Error updating text: {str(e)}", 3000)
    
    def _on_text_formatting_changed(self, formatting: dict):
        """Handle text formatting changes and update preview."""
        try:
            # Update text properties in preview integration for real-time feedback
            self.preview_integration.update_text_properties(formatting)
            
            selected_track = self.timeline_panel.get_selected_track_id()
            current_time = self.timeline_panel.current_time
            
            if selected_track and self.controller:
                timeline_engine = self.controller.get_timeline_engine()
                
                # Update formatting properties in keyframe
                properties = {}
                for key, value in formatting.items():
                    properties[f"text_{key}"] = value
                
                timeline_engine.add_keyframe(selected_track, current_time, properties)
                
        except Exception as e:
            self.status_bar.showMessage(f"Error updating formatting: {str(e)}", 3000)
    
    def _on_preview_fps_updated(self, fps: float):
        """Handle preview FPS updates and display in status bar."""
        fps_text = f"FPS: {fps:.1f}"
        # Update a permanent widget in status bar (would need to be created)
        self.status_bar.showMessage(fps_text, 1000)
    
    def _on_performance_warning(self, warning: str):
        """Handle performance warnings from preview system."""
        self.status_bar.showMessage(f"Performance: {warning}", 5000)
    
    def _on_playback_toggled(self, playing: bool):
        """Handle playback toggle from toolbar."""
        try:
            if playing:
                self.preview_system.play()
                self.timeline_panel._start_playback()
                self.play_action.setText("Pause")
            else:
                self.preview_system.pause()
                self.timeline_panel._pause_playback()
                self.play_action.setText("Play")
                
        except Exception as e:
            self.status_bar.showMessage(f"Playback error: {str(e)}", 3000)
    
    def _on_playback_stopped(self):
        """Handle stop button from toolbar."""
        try:
            self.preview_system.stop()
            self.timeline_panel._stop_playback()
            self.play_action.setChecked(False)
            self.play_action.setText("Play")
            
        except Exception as e:
            self.status_bar.showMessage(f"Stop error: {str(e)}", 3000)
    
    def _setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts for common editing operations."""
        from PyQt6.QtGui import QShortcut
        
        # Playback shortcuts
        play_shortcut = QShortcut(QKeySequence("Space"), self)
        play_shortcut.activated.connect(self._toggle_playback_shortcut)
        
        # Timeline navigation shortcuts
        frame_forward = QShortcut(QKeySequence("Right"), self)
        frame_forward.activated.connect(self._step_frame_forward)
        
        frame_backward = QShortcut(QKeySequence("Left"), self)
        frame_backward.activated.connect(self._step_frame_backward)
        
        # Jump shortcuts
        jump_start = QShortcut(QKeySequence("Home"), self)
        jump_start.activated.connect(self._jump_to_start)
        
        jump_end = QShortcut(QKeySequence("End"), self)
        jump_end.activated.connect(self._jump_to_end)
        
        # Keyframe shortcuts
        add_keyframe = QShortcut(QKeySequence("K"), self)
        add_keyframe.activated.connect(self._add_keyframe_shortcut)
        
        delete_keyframe = QShortcut(QKeySequence("Delete"), self)
        delete_keyframe.activated.connect(self._delete_keyframe_shortcut)
        
        # Copy/paste keyframes
        copy_keyframes = QShortcut(QKeySequence.StandardKey.Copy, self)
        copy_keyframes.activated.connect(self._copy_keyframes_shortcut)
        
        paste_keyframes = QShortcut(QKeySequence.StandardKey.Paste, self)
        paste_keyframes.activated.connect(self._paste_keyframes_shortcut)
        
        # Preview quality shortcuts
        quality_draft = QShortcut(QKeySequence("1"), self)
        quality_draft.activated.connect(lambda: self._set_preview_quality("draft"))
        
        quality_normal = QShortcut(QKeySequence("2"), self)
        quality_normal.activated.connect(lambda: self._set_preview_quality("normal"))
        
        quality_high = QShortcut(QKeySequence("3"), self)
        quality_high.activated.connect(lambda: self._set_preview_quality("high"))
        
        # Zoom shortcuts (already handled in menu, but add direct shortcuts)
        zoom_fit = QShortcut(QKeySequence("F"), self)
        zoom_fit.activated.connect(self.preview_system.zoom_to_fit)
        
        zoom_actual = QShortcut(QKeySequence("Ctrl+1"), self)
        zoom_actual.activated.connect(self.preview_system.zoom_to_actual_size)
    
    def _toggle_playback_shortcut(self):
        """Toggle playback via keyboard shortcut."""
        self.play_action.setChecked(not self.play_action.isChecked())
        self._on_playback_toggled(self.play_action.isChecked())
    
    def _step_frame_forward(self):
        """Step one frame forward."""
        if self.controller:
            timeline_engine = self.controller.get_timeline_engine()
            if timeline_engine.video_asset:
                frame_duration = 1.0 / timeline_engine.video_asset.fps
                new_time = self.timeline_panel.current_time + frame_duration
                self.timeline_panel.set_current_time(new_time)
    
    def _step_frame_backward(self):
        """Step one frame backward."""
        if self.controller:
            timeline_engine = self.controller.get_timeline_engine()
            if timeline_engine.video_asset:
                frame_duration = 1.0 / timeline_engine.video_asset.fps
                new_time = self.timeline_panel.current_time - frame_duration
                self.timeline_panel.set_current_time(new_time)
    
    def _jump_to_start(self):
        """Jump to timeline start."""
        self.timeline_panel.set_current_time(0.0)
    
    def _jump_to_end(self):
        """Jump to timeline end."""
        self.timeline_panel.set_current_time(self.timeline_panel.duration)
    
    def _add_keyframe_shortcut(self):
        """Add keyframe at current time via keyboard shortcut."""
        selected_track = self.timeline_panel.get_selected_track_id()
        current_time = self.timeline_panel.current_time
        
        if selected_track:
            # Get current effect parameters from effects panel
            all_params = {}
            for category in ['animation', 'visual', 'transform', 'color', 'particle']:
                params = self.effects_panel.get_effect_parameters(category)
                for key, value in params.items():
                    all_params[f"{category}_{key}"] = value
            
            # Add keyframe to timeline
            self.timeline_panel.add_keyframe_to_track(selected_track, current_time, all_params)
            
            self.status_bar.showMessage(f"Added keyframe at {current_time:.2f}s", 2000)
    
    def _delete_keyframe_shortcut(self):
        """Delete keyframe at current time via keyboard shortcut."""
        selected_track = self.timeline_panel.get_selected_track_id()
        current_time = self.timeline_panel.current_time
        
        if selected_track and self.controller:
            timeline_engine = self.controller.get_timeline_engine()
            if timeline_engine.remove_keyframe(selected_track, current_time):
                self.status_bar.showMessage(f"Deleted keyframe at {current_time:.2f}s", 2000)
            else:
                self.status_bar.showMessage("No keyframe found at current time", 2000)
    
    def _copy_keyframes_shortcut(self):
        """Copy selected keyframes via keyboard shortcut."""
        # This would need to be implemented with keyframe selection in timeline
        self.status_bar.showMessage("Copy keyframes (not yet implemented)", 2000)
    
    def _paste_keyframes_shortcut(self):
        """Paste keyframes at current time via keyboard shortcut."""
        # This would need to be implemented with keyframe clipboard
        self.status_bar.showMessage("Paste keyframes (not yet implemented)", 2000)
    
    def _set_preview_quality(self, quality: str):
        """Set preview quality via keyboard shortcut."""
        from .preview_system import QualityPreset
        
        quality_map = {
            "draft": QualityPreset.DRAFT,
            "normal": QualityPreset.NORMAL,
            "high": QualityPreset.HIGH
        }
        
        if quality in quality_map:
            self.preview_integration.set_preview_quality(quality_map[quality])
            self.status_bar.showMessage(f"Preview quality: {quality}", 2000)

    def closeEvent(self, event):
        """Handle window close event."""
        # Stop preview system and integration before closing
        if hasattr(self, 'preview_integration'):
            self.preview_integration.shutdown()
        
        if hasattr(self, 'preview_system'):
            self.preview_system.stop_preview()
        
        # TODO: Check for unsaved changes and prompt user
        if self.controller:
            self.controller.shutdown()
        event.accept()