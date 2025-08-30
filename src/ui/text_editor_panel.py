#!/usr/bin/env python3
"""
Text Editor Panel - Karaoke Subtitle Creator

Text editing panel with formatting controls for subtitle content creation.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel,
    QFontComboBox, QSpinBox, QPushButton, QComboBox,
    QGroupBox, QSlider, QCheckBox, QButtonGroup,
    QToolButton, QColorDialog, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import (
    QFont, QTextCharFormat, QColor, QTextCursor,
    QIcon, QPalette
)

from .effect_properties_panel import ColorButton


class FontControlsGroup(QGroupBox):
    """
    Font and basic text formatting controls.
    """
    
    font_changed = pyqtSignal(QFont)
    color_changed = pyqtSignal(QColor)
    
    def __init__(self):
        super().__init__("Font & Style")
        self.current_font = QFont("Arial", 24)
        self.current_color = QColor(255, 255, 255)
        self._setup_controls()
    
    def _setup_controls(self):
        """Set up font control widgets."""
        layout = QVBoxLayout(self)
        
        # Font family and size row
        font_row = QHBoxLayout()
        
        font_row.addWidget(QLabel("Font:"))
        
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(self.current_font)
        self.font_combo.currentFontChanged.connect(self._font_family_changed)
        font_row.addWidget(self.font_combo)
        
        font_row.addWidget(QLabel("Size:"))
        
        self.size_spinbox = QSpinBox()
        self.size_spinbox.setRange(8, 200)
        self.size_spinbox.setValue(self.current_font.pointSize())
        self.size_spinbox.valueChanged.connect(self._font_size_changed)
        font_row.addWidget(self.size_spinbox)
        
        layout.addLayout(font_row)
        
        # Style buttons row
        style_row = QHBoxLayout()
        
        self.bold_button = QPushButton("B")
        self.bold_button.setCheckable(True)
        self.bold_button.setFixedSize(30, 30)
        self.bold_button.setStyleSheet("font-weight: bold;")
        self.bold_button.toggled.connect(self._style_changed)
        style_row.addWidget(self.bold_button)
        
        self.italic_button = QPushButton("I")
        self.italic_button.setCheckable(True)
        self.italic_button.setFixedSize(30, 30)
        self.italic_button.setStyleSheet("font-style: italic;")
        self.italic_button.toggled.connect(self._style_changed)
        style_row.addWidget(self.italic_button)
        
        self.underline_button = QPushButton("U")
        self.underline_button.setCheckable(True)
        self.underline_button.setFixedSize(30, 30)
        self.underline_button.setStyleSheet("text-decoration: underline;")
        self.underline_button.toggled.connect(self._style_changed)
        style_row.addWidget(self.underline_button)
        
        style_row.addStretch()
        
        # Text color
        style_row.addWidget(QLabel("Color:"))
        self.color_button = ColorButton(self.current_color)
        self.color_button.color_changed.connect(self._color_changed)
        style_row.addWidget(self.color_button)
        
        layout.addLayout(style_row)
    
    def _font_family_changed(self, font):
        """Handle font family change."""
        self.current_font.setFamily(font.family())
        self.font_changed.emit(self.current_font)
    
    def _font_size_changed(self, size):
        """Handle font size change."""
        self.current_font.setPointSize(size)
        self.font_changed.emit(self.current_font)
    
    def _style_changed(self):
        """Handle font style changes."""
        self.current_font.setBold(self.bold_button.isChecked())
        self.current_font.setItalic(self.italic_button.isChecked())
        self.current_font.setUnderline(self.underline_button.isChecked())
        self.font_changed.emit(self.current_font)
    
    def _color_changed(self, color):
        """Handle text color change."""
        self.current_color = color
        self.color_changed.emit(color)
    
    def set_font(self, font):
        """Set the current font."""
        self.current_font = font
        
        # Update controls
        self.font_combo.setCurrentFont(font)
        self.size_spinbox.setValue(font.pointSize())
        self.bold_button.setChecked(font.bold())
        self.italic_button.setChecked(font.italic())
        self.underline_button.setChecked(font.underline())
    
    def get_font(self):
        """Get the current font."""
        return self.current_font
    
    def get_color(self):
        """Get the current text color."""
        return self.current_color


class AlignmentControlsGroup(QGroupBox):
    """
    Text alignment and positioning controls.
    """
    
    alignment_changed = pyqtSignal(str)  # "left", "center", "right"
    position_changed = pyqtSignal(float, float)  # x, y (0.0-1.0 normalized)
    
    def __init__(self):
        super().__init__("Alignment & Position")
        self.current_alignment = "center"
        self.current_x = 0.5  # Center
        self.current_y = 0.8  # Bottom area
        self._setup_controls()
    
    def _setup_controls(self):
        """Set up alignment and position controls."""
        layout = QVBoxLayout(self)
        
        # Alignment buttons
        align_row = QHBoxLayout()
        align_row.addWidget(QLabel("Alignment:"))
        
        self.alignment_group = QButtonGroup()
        
        self.left_align = QPushButton("Left")
        self.left_align.setCheckable(True)
        self.left_align.clicked.connect(lambda: self._alignment_changed("left"))
        self.alignment_group.addButton(self.left_align)
        align_row.addWidget(self.left_align)
        
        self.center_align = QPushButton("Center")
        self.center_align.setCheckable(True)
        self.center_align.setChecked(True)
        self.center_align.clicked.connect(lambda: self._alignment_changed("center"))
        self.alignment_group.addButton(self.center_align)
        align_row.addWidget(self.center_align)
        
        self.right_align = QPushButton("Right")
        self.right_align.setCheckable(True)
        self.right_align.clicked.connect(lambda: self._alignment_changed("right"))
        self.alignment_group.addButton(self.right_align)
        align_row.addWidget(self.right_align)
        
        layout.addLayout(align_row)
        
        # Position controls
        pos_layout = QVBoxLayout()
        
        # X Position
        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel("X Position:"))
        
        self.x_slider = QSlider(Qt.Orientation.Horizontal)
        self.x_slider.setRange(0, 100)
        self.x_slider.setValue(int(self.current_x * 100))
        self.x_slider.valueChanged.connect(self._x_position_changed)
        x_layout.addWidget(self.x_slider)
        
        self.x_spinbox = QSpinBox()
        self.x_spinbox.setRange(0, 100)
        self.x_spinbox.setValue(int(self.current_x * 100))
        self.x_spinbox.setSuffix("%")
        self.x_spinbox.valueChanged.connect(self._x_position_changed)
        x_layout.addWidget(self.x_spinbox)
        
        pos_layout.addLayout(x_layout)
        
        # Y Position
        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel("Y Position:"))
        
        self.y_slider = QSlider(Qt.Orientation.Horizontal)
        self.y_slider.setRange(0, 100)
        self.y_slider.setValue(int(self.current_y * 100))
        self.y_slider.valueChanged.connect(self._y_position_changed)
        y_layout.addWidget(self.y_slider)
        
        self.y_spinbox = QSpinBox()
        self.y_spinbox.setRange(0, 100)
        self.y_spinbox.setValue(int(self.current_y * 100))
        self.y_spinbox.setSuffix("%")
        self.y_spinbox.valueChanged.connect(self._y_position_changed)
        y_layout.addWidget(self.y_spinbox)
        
        pos_layout.addLayout(y_layout)
        
        layout.addLayout(pos_layout)
        
        # Connect sliders and spinboxes
        self.x_slider.valueChanged.connect(self.x_spinbox.setValue)
        self.x_spinbox.valueChanged.connect(self.x_slider.setValue)
        self.y_slider.valueChanged.connect(self.y_spinbox.setValue)
        self.y_spinbox.valueChanged.connect(self.y_slider.setValue)
    
    def _alignment_changed(self, alignment):
        """Handle alignment change."""
        self.current_alignment = alignment
        self.alignment_changed.emit(alignment)
    
    def _x_position_changed(self, value):
        """Handle X position change."""
        self.current_x = value / 100.0
        self.position_changed.emit(self.current_x, self.current_y)
    
    def _y_position_changed(self, value):
        """Handle Y position change."""
        self.current_y = value / 100.0
        self.position_changed.emit(self.current_x, self.current_y)
    
    def get_alignment(self):
        """Get current alignment."""
        return self.current_alignment
    
    def get_position(self):
        """Get current position as (x, y) tuple."""
        return (self.current_x, self.current_y)
    
    def set_alignment(self, alignment):
        """Set text alignment."""
        self.current_alignment = alignment
        if alignment == "left":
            self.left_align.setChecked(True)
        elif alignment == "center":
            self.center_align.setChecked(True)
        elif alignment == "right":
            self.right_align.setChecked(True)
    
    def set_position(self, x, y):
        """Set text position."""
        self.current_x = x
        self.current_y = y
        self.x_slider.setValue(int(x * 100))
        self.y_slider.setValue(int(y * 100))


class TextSpacingGroup(QGroupBox):
    """
    Text spacing and layout controls.
    """
    
    spacing_changed = pyqtSignal(str, float)  # spacing_type, value
    
    def __init__(self):
        super().__init__("Spacing & Layout")
        self._setup_controls()
    
    def _setup_controls(self):
        """Set up spacing controls."""
        layout = QVBoxLayout(self)
        
        # Line spacing
        line_layout = QHBoxLayout()
        line_layout.addWidget(QLabel("Line Spacing:"))
        
        self.line_spacing_spinbox = QSpinBox()
        self.line_spacing_spinbox.setRange(50, 300)
        self.line_spacing_spinbox.setValue(100)
        self.line_spacing_spinbox.setSuffix("%")
        self.line_spacing_spinbox.valueChanged.connect(
            lambda v: self.spacing_changed.emit("line_spacing", v / 100.0)
        )
        line_layout.addWidget(self.line_spacing_spinbox)
        
        layout.addLayout(line_layout)
        
        # Character spacing
        char_layout = QHBoxLayout()
        char_layout.addWidget(QLabel("Character Spacing:"))
        
        self.char_spacing_spinbox = QSpinBox()
        self.char_spacing_spinbox.setRange(-50, 200)
        self.char_spacing_spinbox.setValue(0)
        self.char_spacing_spinbox.setSuffix("%")
        self.char_spacing_spinbox.valueChanged.connect(
            lambda v: self.spacing_changed.emit("char_spacing", v / 100.0)
        )
        char_layout.addWidget(self.char_spacing_spinbox)
        
        layout.addLayout(char_layout)
        
        # Word spacing
        word_layout = QHBoxLayout()
        word_layout.addWidget(QLabel("Word Spacing:"))
        
        self.word_spacing_spinbox = QSpinBox()
        self.word_spacing_spinbox.setRange(-50, 200)
        self.word_spacing_spinbox.setValue(0)
        self.word_spacing_spinbox.setSuffix("%")
        self.word_spacing_spinbox.valueChanged.connect(
            lambda v: self.spacing_changed.emit("word_spacing", v / 100.0)
        )
        word_layout.addWidget(self.word_spacing_spinbox)
        
        layout.addLayout(word_layout)


class TextEditorPanel(QWidget):
    """
    Main text editor panel with text input and formatting controls.
    """
    
    # Signals
    text_changed = pyqtSignal(str)
    font_changed = pyqtSignal(QFont)
    color_changed = pyqtSignal(QColor)
    alignment_changed = pyqtSignal(str)
    position_changed = pyqtSignal(float, float)
    spacing_changed = pyqtSignal(str, float)
    formatting_changed = pyqtSignal(dict)  # Combined formatting changes
    
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(300)
        self.setMaximumWidth(400)
        
        self._setup_ui()
        self._setup_connections()
    
    def _setup_ui(self):
        """Set up the text editor UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        title_label = QLabel("Text Editor")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        layout.addWidget(title_label)
        
        # Text input area
        text_group = QGroupBox("Text Content")
        text_layout = QVBoxLayout(text_group)
        
        self.text_edit = QTextEdit()
        self.text_edit.setMaximumHeight(120)
        self.text_edit.setPlaceholderText("Enter subtitle text here...")
        text_layout.addWidget(self.text_edit)
        
        # Character count
        self.char_count_label = QLabel("Characters: 0")
        self.char_count_label.setStyleSheet("color: #666; font-size: 10px;")
        text_layout.addWidget(self.char_count_label)
        
        layout.addWidget(text_group)
        
        # Font controls
        self.font_controls = FontControlsGroup()
        layout.addWidget(self.font_controls)
        
        # Alignment controls
        self.alignment_controls = AlignmentControlsGroup()
        layout.addWidget(self.alignment_controls)
        
        # Spacing controls
        self.spacing_controls = TextSpacingGroup()
        layout.addWidget(self.spacing_controls)
        
        # Quick presets
        presets_group = QGroupBox("Quick Presets")
        presets_layout = QVBoxLayout(presets_group)
        
        preset_buttons_layout = QHBoxLayout()
        
        title_preset = QPushButton("Title")
        title_preset.clicked.connect(self._apply_title_preset)
        preset_buttons_layout.addWidget(title_preset)
        
        subtitle_preset = QPushButton("Subtitle")
        subtitle_preset.clicked.connect(self._apply_subtitle_preset)
        preset_buttons_layout.addWidget(subtitle_preset)
        
        karaoke_preset = QPushButton("Karaoke")
        karaoke_preset.clicked.connect(self._apply_karaoke_preset)
        preset_buttons_layout.addWidget(karaoke_preset)
        
        presets_layout.addLayout(preset_buttons_layout)
        layout.addWidget(presets_group)
        
        layout.addStretch()
    
    def _setup_connections(self):
        """Set up signal connections."""
        # Text content changes
        self.text_edit.textChanged.connect(self._text_content_changed)
        
        # Font and formatting changes
        self.font_controls.font_changed.connect(self._on_font_changed)
        self.font_controls.color_changed.connect(self._on_color_changed)
        
        # Alignment and position changes
        self.alignment_controls.alignment_changed.connect(self._on_alignment_changed)
        self.alignment_controls.position_changed.connect(self._on_position_changed)
        
        # Spacing changes
        self.spacing_controls.spacing_changed.connect(self._on_spacing_changed)
    
    def _on_font_changed(self, font):
        """Handle font changes and emit combined formatting signal."""
        self.font_changed.emit(font)
        self._emit_formatting_changed()
    
    def _on_color_changed(self, color):
        """Handle color changes and emit combined formatting signal."""
        self.color_changed.emit(color)
        self._emit_formatting_changed()
    
    def _on_alignment_changed(self, alignment):
        """Handle alignment changes and emit combined formatting signal."""
        self.alignment_changed.emit(alignment)
        self._emit_formatting_changed()
    
    def _on_position_changed(self, x, y):
        """Handle position changes and emit combined formatting signal."""
        self.position_changed.emit(x, y)
        self._emit_formatting_changed()
    
    def _on_spacing_changed(self, spacing_type, value):
        """Handle spacing changes and emit combined formatting signal."""
        self.spacing_changed.emit(spacing_type, value)
        self._emit_formatting_changed()
    
    def _emit_formatting_changed(self):
        """Emit combined formatting changes signal."""
        formatting = {
            'font_family': self.font_controls.get_font().family(),
            'font_size': self.font_controls.get_font().pointSize(),
            'font_bold': self.font_controls.get_font().bold(),
            'font_italic': self.font_controls.get_font().italic(),
            'font_underline': self.font_controls.get_font().underline(),
            'color': self.font_controls.get_color(),
            'alignment': self.alignment_controls.get_alignment(),
            'position_x': self.alignment_controls.get_position()[0],
            'position_y': self.alignment_controls.get_position()[1],
        }
        self.formatting_changed.emit(formatting)
    
    def _text_content_changed(self):
        """Handle text content changes."""
        text = self.text_edit.toPlainText()
        self.text_changed.emit(text)
        
        # Update character count
        char_count = len(text)
        self.char_count_label.setText(f"Characters: {char_count}")
    
    def _apply_title_preset(self):
        """Apply title text preset."""
        font = QFont("Arial", 36, QFont.Weight.Bold)
        self.font_controls.set_font(font)
        self.alignment_controls.set_alignment("center")
        self.alignment_controls.set_position(0.5, 0.2)  # Top center
    
    def _apply_subtitle_preset(self):
        """Apply subtitle text preset."""
        font = QFont("Arial", 24)
        self.font_controls.set_font(font)
        self.alignment_controls.set_alignment("center")
        self.alignment_controls.set_position(0.5, 0.8)  # Bottom center
    
    def _apply_karaoke_preset(self):
        """Apply karaoke text preset."""
        font = QFont("Arial", 28, QFont.Weight.Bold)
        self.font_controls.set_font(font)
        self.alignment_controls.set_alignment("center")
        self.alignment_controls.set_position(0.5, 0.75)  # Lower center
    
    def get_text_content(self):
        """Get the current text content."""
        return self.text_edit.toPlainText()
    
    def set_text_content(self, text):
        """Set the text content."""
        self.text_edit.setPlainText(text)
    
    def get_current_font(self):
        """Get the current font settings."""
        return self.font_controls.get_font()
    
    def get_current_color(self):
        """Get the current text color."""
        return self.font_controls.get_color()
    
    def get_current_alignment(self):
        """Get the current text alignment."""
        return self.alignment_controls.get_alignment()
    
    def get_current_position(self):
        """Get the current text position."""
        return self.alignment_controls.get_position()
    
    def clear_text(self):
        """Clear the text editor."""
        self.text_edit.clear()
    
    def update_from_selection(self, text_element):
        """Update the editor based on selected text element."""
        # TODO: Load text element properties into the editor
        # This will be implemented when text element integration is complete
        pass