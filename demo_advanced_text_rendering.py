#!/usr/bin/env python3
"""
Advanced text rendering demo showcasing FreeType integration with SDF support.

This demo demonstrates:
- Unicode text support
- Signed Distance Field (SDF) rendering for crisp text at any scale
- Advanced text effects (outline, shadow, glow)
- Real-time parameter adjustment
- Multi-language text rendering
"""

import sys
import math
import time
from pathlib import Path
from typing import Optional

import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QSlider, QLabel, QComboBox, QPushButton, 
                            QTextEdit, QGroupBox, QCheckBox, QSpinBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtOpenGL import QOpenGLWidget
import OpenGL.GL as gl

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.text.text_renderer import TextRenderer, TextStyle, TextAlignment
from src.text.font_manager import FontManager
from src.text.sdf_generator import SDFGenerator, SDFTextRenderer
from src.graphics.shader_manager import ShaderManager


class AdvancedTextRenderingWidget(QOpenGLWidget):
    """OpenGL widget for advanced text rendering demonstration."""
    
    def __init__(self):
        super().__init__()
        self.text_renderer: Optional[TextRenderer] = None
        self.shader_manager: Optional[ShaderManager] = None
        self.sdf_renderer: Optional[SDFTextRenderer] = None
        
        # Demo parameters
        self.demo_text = "Advanced Text Rendering\n高品质文本渲染\nنص عالي الجودة"
        self.font_size = 48
        self.text_color = (1.0, 1.0, 1.0, 1.0)
        self.outline_width = 0.1
        self.outline_color = (0.0, 0.0, 0.0, 1.0)
        self.shadow_offset = (3.0, 3.0)
        self.shadow_color = (0.0, 0.0, 0.0, 0.7)
        self.use_sdf = True
        self.sdf_smoothing = 0.1
        
        # Animation and effects
        self.animation_time = 0.0
        self.animate_colors = False
        self.animate_scale = False
        self.scale_factor = 1.0
        
        # Timer for animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)  # ~60 FPS
        
    def initializeGL(self):
        """Initialize OpenGL context and text rendering."""
        # Initialize OpenGL
        gl.glClearColor(0.05, 0.05, 0.1, 1.0)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        
        # Initialize shader manager and text renderer
        self.shader_manager = ShaderManager()
        self.text_renderer = TextRenderer(self.shader_manager)
        
        # Initialize SDF renderer
        sdf_generator = SDFGenerator(spread=8)
        self.sdf_renderer = SDFTextRenderer(sdf_generator)
        
        # Load default font
        success = self.text_renderer.load_default_font(self.font_size)
        if not success:
            print("Warning: Failed to load default font")
            
        # Initialize OpenGL textures for font atlases
        self.text_renderer.font_manager.initialize_opengl_textures()
        
        print("✓ Advanced text rendering initialized")
        
    def resizeGL(self, width: int, height: int):
        """Handle window resize."""
        gl.glViewport(0, 0, width, height)
        if self.text_renderer:
            self.text_renderer.set_projection_matrix(width, height)
            
    def paintGL(self):
        """Render the scene."""
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        
        if not self.text_renderer:
            return
            
        # Create text style with current parameters
        style = TextStyle(
            font_path=self._get_current_font_path(),
            font_size=int(self.font_size * self.scale_factor),
            color=self.text_color,
            alignment=TextAlignment.CENTER,
            line_spacing=1.2,
            character_spacing=0.0,
            outline_width=self.outline_width,
            outline_color=self.outline_color,
            shadow_offset=self.shadow_offset,
            shadow_color=self.shadow_color
        )
        
        # Apply color animation if enabled
        if self.animate_colors:
            hue = (self.animation_time * 0.3) % 1.0
            r = 0.5 + 0.5 * math.sin(hue * 2 * math.pi)
            g = 0.5 + 0.5 * math.sin((hue + 0.33) * 2 * math.pi)
            b = 0.5 + 0.5 * math.sin((hue + 0.66) * 2 * math.pi)
            style.color = (r, g, b, 1.0)
            
        # Calculate text position (centered)
        width = self.width()
        height = self.height()
        
        # Measure text to center it
        text_width, text_height = self.text_renderer.measure_text(self.demo_text, style)
        x = (width - text_width) / 2
        y = (height + text_height) / 2
        
        # Render text
        self.text_renderer.render_text(self.demo_text, x, y, style)
        
        # Render additional demo text at different scales if SDF is enabled
        if self.use_sdf:
            self._render_scale_demo(width, height)
            
    def _render_scale_demo(self, width: int, height: int):
        """Render text at different scales to demonstrate SDF quality."""
        demo_scales = [0.5, 0.75, 1.0, 1.5, 2.0]
        demo_text = "SDF Quality Test"
        
        for i, scale in enumerate(demo_scales):
            style = TextStyle(
                font_path=self._get_current_font_path(),
                font_size=int(24 * scale),
                color=(0.8, 0.8, 1.0, 0.8),
                alignment=TextAlignment.LEFT
            )
            
            x = 20
            y = height - 50 - (i * 40)
            
            # Add scale label
            label_text = f"{scale}x: {demo_text}"
            self.text_renderer.render_text(label_text, x, y, style)
        
    def _get_current_font_path(self) -> str:
        """Get the current font path."""
        if self.text_renderer:
            fonts = self.text_renderer.get_available_fonts()
            if fonts:
                # Parse font key to get path
                font_key = fonts[0]
                parts = font_key.split(':')
                if len(parts) >= 2:
                    return ':'.join(parts[:-1])
        return ""
        
    def update_animation(self):
        """Update animation time and effects."""
        self.animation_time += 0.016  # 16ms
        
        # Update scale animation
        if self.animate_scale:
            self.scale_factor = 1.0 + 0.3 * math.sin(self.animation_time * 2.0)
            
        if self.animate_colors or self.animate_scale:
            self.update()
            
    def set_demo_text(self, text: str):
        """Set the demo text."""
        self.demo_text = text
        self.update()
        
    def set_font_size(self, size: int):
        """Set font size."""
        self.font_size = size
        if self.text_renderer:
            # Reload font with new size
            font_path = self._get_current_font_path()
            if font_path:
                self.text_renderer.load_font(font_path, size)
        self.update()
        
    def set_text_color(self, r: float, g: float, b: float):
        """Set text color."""
        self.text_color = (r, g, b, 1.0)
        self.update()
        
    def set_outline_width(self, width: float):
        """Set outline width."""
        self.outline_width = width
        self.update()
        
    def set_shadow_offset(self, x: float, y: float):
        """Set shadow offset."""
        self.shadow_offset = (x, y)
        self.update()
        
    def set_sdf_smoothing(self, smoothing: float):
        """Set SDF smoothing amount."""
        self.sdf_smoothing = smoothing
        self.update()
        
    def set_use_sdf(self, use_sdf: bool):
        """Enable/disable SDF rendering."""
        self.use_sdf = use_sdf
        self.update()
        
    def set_animate_colors(self, animate: bool):
        """Enable/disable color animation."""
        self.animate_colors = animate
        if not animate:
            self.update()
            
    def set_animate_scale(self, animate: bool):
        """Enable/disable scale animation."""
        self.animate_scale = animate
        if not animate:
            self.scale_factor = 1.0
            self.update()


class AdvancedTextRenderingDemo(QMainWindow):
    """Main demo window with advanced controls."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced Text Rendering Demo - FreeType + SDF")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QHBoxLayout(central_widget)
        
        # Create OpenGL widget
        self.gl_widget = AdvancedTextRenderingWidget()
        layout.addWidget(self.gl_widget, 2)
        
        # Create controls
        controls = self.create_controls()
        layout.addWidget(controls, 1)
        
    def create_controls(self) -> QWidget:
        """Create advanced control panel."""
        controls = QWidget()
        layout = QVBoxLayout(controls)
        
        # Text input
        text_group = QGroupBox("Text Content")
        text_layout = QVBoxLayout(text_group)
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(self.gl_widget.demo_text)
        self.text_edit.textChanged.connect(self.on_text_changed)
        text_layout.addWidget(self.text_edit)
        
        layout.addWidget(text_group)
        
        # Font controls
        font_group = QGroupBox("Font Settings")
        font_layout = QVBoxLayout(font_group)
        
        # Font size
        font_layout.addWidget(QLabel("Font Size:"))
        self.font_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_size_slider.setRange(12, 120)
        self.font_size_slider.setValue(48)
        self.font_size_slider.valueChanged.connect(self.on_font_size_changed)
        font_layout.addWidget(self.font_size_slider)
        
        self.font_size_label = QLabel("48")
        font_layout.addWidget(self.font_size_label)
        
        layout.addWidget(font_group)
        
        # SDF controls
        sdf_group = QGroupBox("SDF Settings")
        sdf_layout = QVBoxLayout(sdf_group)
        
        self.sdf_checkbox = QCheckBox("Enable SDF Rendering")
        self.sdf_checkbox.setChecked(True)
        self.sdf_checkbox.toggled.connect(self.on_sdf_toggled)
        sdf_layout.addWidget(self.sdf_checkbox)
        
        sdf_layout.addWidget(QLabel("SDF Smoothing:"))
        self.sdf_smoothing_slider = QSlider(Qt.Orientation.Horizontal)
        self.sdf_smoothing_slider.setRange(1, 50)
        self.sdf_smoothing_slider.setValue(10)
        self.sdf_smoothing_slider.valueChanged.connect(self.on_sdf_smoothing_changed)
        sdf_layout.addWidget(self.sdf_smoothing_slider)
        
        layout.addWidget(sdf_group)
        
        # Color controls
        color_group = QGroupBox("Colors")
        color_layout = QVBoxLayout(color_group)
        
        # Text color
        color_layout.addWidget(QLabel("Text Color (RGB):"))
        
        self.red_slider = QSlider(Qt.Orientation.Horizontal)
        self.red_slider.setRange(0, 100)
        self.red_slider.setValue(100)
        self.red_slider.valueChanged.connect(self.on_color_changed)
        color_layout.addWidget(QLabel("Red:"))
        color_layout.addWidget(self.red_slider)
        
        self.green_slider = QSlider(Qt.Orientation.Horizontal)
        self.green_slider.setRange(0, 100)
        self.green_slider.setValue(100)
        self.green_slider.valueChanged.connect(self.on_color_changed)
        color_layout.addWidget(QLabel("Green:"))
        color_layout.addWidget(self.green_slider)
        
        self.blue_slider = QSlider(Qt.Orientation.Horizontal)
        self.blue_slider.setRange(0, 100)
        self.blue_slider.setValue(100)
        self.blue_slider.valueChanged.connect(self.on_color_changed)
        color_layout.addWidget(QLabel("Blue:"))
        color_layout.addWidget(self.blue_slider)
        
        layout.addWidget(color_group)
        
        # Effects controls
        effects_group = QGroupBox("Text Effects")
        effects_layout = QVBoxLayout(effects_group)
        
        # Outline width
        effects_layout.addWidget(QLabel("Outline Width:"))
        self.outline_slider = QSlider(Qt.Orientation.Horizontal)
        self.outline_slider.setRange(0, 50)
        self.outline_slider.setValue(10)
        self.outline_slider.valueChanged.connect(self.on_outline_changed)
        effects_layout.addWidget(self.outline_slider)
        
        # Shadow offset
        effects_layout.addWidget(QLabel("Shadow Offset X:"))
        self.shadow_x_slider = QSlider(Qt.Orientation.Horizontal)
        self.shadow_x_slider.setRange(-20, 20)
        self.shadow_x_slider.setValue(3)
        self.shadow_x_slider.valueChanged.connect(self.on_shadow_changed)
        effects_layout.addWidget(self.shadow_x_slider)
        
        effects_layout.addWidget(QLabel("Shadow Offset Y:"))
        self.shadow_y_slider = QSlider(Qt.Orientation.Horizontal)
        self.shadow_y_slider.setRange(-20, 20)
        self.shadow_y_slider.setValue(3)
        self.shadow_y_slider.valueChanged.connect(self.on_shadow_changed)
        effects_layout.addWidget(self.shadow_y_slider)
        
        layout.addWidget(effects_group)
        
        # Animation controls
        animation_group = QGroupBox("Animations")
        animation_layout = QVBoxLayout(animation_group)
        
        self.color_animation_checkbox = QCheckBox("Animate Colors")
        self.color_animation_checkbox.toggled.connect(self.on_color_animation_toggled)
        animation_layout.addWidget(self.color_animation_checkbox)
        
        self.scale_animation_checkbox = QCheckBox("Animate Scale")
        self.scale_animation_checkbox.toggled.connect(self.on_scale_animation_toggled)
        animation_layout.addWidget(self.scale_animation_checkbox)
        
        layout.addWidget(animation_group)
        
        # Preset buttons
        presets_group = QGroupBox("Text Presets")
        presets_layout = QVBoxLayout(presets_group)
        
        preset_texts = [
            ("English", "Advanced Text Rendering\nHigh Quality Typography"),
            ("Unicode Mix", "Unicode Support ✓\n你好世界 مرحبا\nCafé résumé naïve"),
            ("Technical", "OpenGL + FreeType\nSDF Rendering\n60 FPS Real-time"),
            ("Symbols", "★☆♪♫♬♩♭♯\n♠♣♥♦\n←↑→↓⟲⟳"),
            ("Karaoke", "🎤 Karaoke Subtitle Creator\n高品质卡拉OK字幕\nReal-time Effects"),
        ]
        
        for name, text in preset_texts:
            button = QPushButton(name)
            button.clicked.connect(lambda checked, t=text: self.set_preset_text(t))
            presets_layout.addWidget(button)
            
        layout.addWidget(presets_group)
        
        layout.addStretch()
        
        return controls
        
    def on_text_changed(self):
        """Handle text change."""
        text = self.text_edit.toPlainText()
        self.gl_widget.set_demo_text(text)
        
    def on_font_size_changed(self, value: int):
        """Handle font size change."""
        self.font_size_label.setText(str(value))
        self.gl_widget.set_font_size(value)
        
    def on_color_changed(self):
        """Handle color change."""
        r = self.red_slider.value() / 100.0
        g = self.green_slider.value() / 100.0
        b = self.blue_slider.value() / 100.0
        self.gl_widget.set_text_color(r, g, b)
        
    def on_outline_changed(self, value: int):
        """Handle outline width change."""
        self.gl_widget.set_outline_width(value / 100.0)
        
    def on_shadow_changed(self):
        """Handle shadow offset change."""
        x = float(self.shadow_x_slider.value())
        y = float(self.shadow_y_slider.value())
        self.gl_widget.set_shadow_offset(x, y)
        
    def on_sdf_toggled(self, checked: bool):
        """Handle SDF toggle."""
        self.gl_widget.set_use_sdf(checked)
        
    def on_sdf_smoothing_changed(self, value: int):
        """Handle SDF smoothing change."""
        self.gl_widget.set_sdf_smoothing(value / 100.0)
        
    def on_color_animation_toggled(self, checked: bool):
        """Handle color animation toggle."""
        self.gl_widget.set_animate_colors(checked)
        
    def on_scale_animation_toggled(self, checked: bool):
        """Handle scale animation toggle."""
        self.gl_widget.set_animate_scale(checked)
        
    def set_preset_text(self, text: str):
        """Set preset text."""
        self.text_edit.setPlainText(text)
        self.gl_widget.set_demo_text(text)


def main():
    """Run the advanced text rendering demo."""
    app = QApplication(sys.argv)
    
    # Create and show demo window
    demo = AdvancedTextRenderingDemo()
    demo.show()
    
    print("Advanced Text Rendering Demo")
    print("=" * 40)
    print("Features demonstrated:")
    print("- FreeType font loading and glyph rendering")
    print("- Unicode text support (multi-language)")
    print("- Signed Distance Field (SDF) rendering")
    print("- Real-time text effects (outline, shadow)")
    print("- Font size and color adjustment")
    print("- Animation effects")
    print("- High-quality text at any scale")
    print()
    print("Use the controls on the right to adjust parameters.")
    print("Try different text presets to see Unicode support.")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()