#!/usr/bin/env python3
"""
Effect Properties Panel - Karaoke Subtitle Creator

Real-time parameter controls for text effects, animations, and visual enhancements.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QSlider, QSpinBox, QDoubleSpinBox, QComboBox, QPushButton,
    QColorDialog, QCheckBox, QScrollArea, QFrame, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPalette


class ColorButton(QPushButton):
    """
    Custom button for color selection with color preview.
    """
    
    color_changed = pyqtSignal(QColor)
    
    def __init__(self, initial_color=QColor(255, 255, 255)):
        super().__init__()
        self.current_color = initial_color
        self.setFixedSize(40, 25)
        self._update_color_display()
        self.clicked.connect(self._select_color)
    
    def _update_color_display(self):
        """Update button appearance to show current color."""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgb({self.current_color.red()}, 
                                    {self.current_color.green()}, 
                                    {self.current_color.blue()});
                border: 1px solid #666;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                border: 2px solid #999;
            }}
        """)
    
    def _select_color(self):
        """Open color dialog for color selection."""
        color = QColorDialog.getColor(self.current_color, self, "Select Color")
        if color.isValid():
            self.current_color = color
            self._update_color_display()
            self.color_changed.emit(color)
    
    def set_color(self, color):
        """Set the current color."""
        self.current_color = color
        self._update_color_display()
    
    def get_color(self):
        """Get the current color."""
        return self.current_color


class ParameterGroup(QGroupBox):
    """
    Base class for parameter control groups.
    """
    
    parameter_changed = pyqtSignal(str, object)  # parameter_name, value
    
    def __init__(self, title):
        super().__init__(title)
        self.parameters = {}
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(5)
    
    def add_slider_parameter(self, name, label, min_val, max_val, default_val, decimals=0):
        """Add a slider parameter control."""
        param_layout = QHBoxLayout()
        
        param_layout.addWidget(QLabel(f"{label}:"))
        
        if decimals > 0:
            spinbox = QDoubleSpinBox()
            spinbox.setDecimals(decimals)
            spinbox.setSingleStep(0.1 if decimals == 1 else 0.01)
        else:
            spinbox = QSpinBox()
        
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(default_val)
        spinbox.setFixedWidth(80)
        
        slider = QSlider(Qt.Orientation.Horizontal)
        if decimals > 0:
            # Scale for decimal values
            scale = 10 ** decimals
            slider.setRange(int(min_val * scale), int(max_val * scale))
            slider.setValue(int(default_val * scale))
        else:
            slider.setRange(min_val, max_val)
            slider.setValue(default_val)
        
        # Connect signals
        if decimals > 0:
            spinbox.valueChanged.connect(
                lambda v: slider.setValue(int(v * scale))
            )
            slider.valueChanged.connect(
                lambda v: spinbox.setValue(v / scale)
            )
            spinbox.valueChanged.connect(
                lambda v: self.parameter_changed.emit(name, v)
            )
        else:
            spinbox.valueChanged.connect(slider.setValue)
            slider.valueChanged.connect(spinbox.setValue)
            spinbox.valueChanged.connect(
                lambda v: self.parameter_changed.emit(name, v)
            )
        
        param_layout.addWidget(slider)
        param_layout.addWidget(spinbox)
        
        self.layout.addLayout(param_layout)
        self.parameters[name] = (slider, spinbox)
        
        return slider, spinbox
    
    def add_color_parameter(self, name, label, default_color=QColor(255, 255, 255)):
        """Add a color parameter control."""
        param_layout = QHBoxLayout()
        
        param_layout.addWidget(QLabel(f"{label}:"))
        
        color_button = ColorButton(default_color)
        color_button.color_changed.connect(
            lambda c: self.parameter_changed.emit(name, c)
        )
        
        param_layout.addWidget(color_button)
        param_layout.addStretch()
        
        self.layout.addLayout(param_layout)
        self.parameters[name] = color_button
        
        return color_button
    
    def add_combo_parameter(self, name, label, options, default_index=0):
        """Add a combo box parameter control."""
        param_layout = QHBoxLayout()
        
        param_layout.addWidget(QLabel(f"{label}:"))
        
        combo = QComboBox()
        combo.addItems(options)
        combo.setCurrentIndex(default_index)
        combo.currentTextChanged.connect(
            lambda text: self.parameter_changed.emit(name, text)
        )
        
        param_layout.addWidget(combo)
        
        self.layout.addLayout(param_layout)
        self.parameters[name] = combo
        
        return combo
    
    def add_checkbox_parameter(self, name, label, default_checked=False):
        """Add a checkbox parameter control."""
        checkbox = QCheckBox(label)
        checkbox.setChecked(default_checked)
        checkbox.toggled.connect(
            lambda checked: self.parameter_changed.emit(name, checked)
        )
        
        self.layout.addWidget(checkbox)
        self.parameters[name] = checkbox
        
        return checkbox
    
    def get_parameter_value(self, name):
        """Get the current value of a parameter."""
        if name in self.parameters:
            control = self.parameters[name]
            if isinstance(control, tuple):  # Slider/spinbox pair
                return control[1].value()
            elif isinstance(control, ColorButton):
                return control.get_color()
            elif isinstance(control, QComboBox):
                return control.currentText()
            elif isinstance(control, QCheckBox):
                return control.isChecked()
        return None
    
    def set_parameter_value(self, name, value):
        """Set the value of a parameter."""
        if name in self.parameters:
            control = self.parameters[name]
            if isinstance(control, tuple):  # Slider/spinbox pair
                control[1].setValue(value)
            elif isinstance(control, ColorButton):
                control.set_color(value)
            elif isinstance(control, QComboBox):
                control.setCurrentText(str(value))
            elif isinstance(control, QCheckBox):
                control.setChecked(bool(value))


class AnimationEffectsGroup(ParameterGroup):
    """
    Parameter controls for animation effects.
    """
    
    def __init__(self):
        super().__init__("Animation Effects")
        self._setup_controls()
    
    def _setup_controls(self):
        """Set up animation effect controls."""
        # Animation type
        self.add_combo_parameter(
            "animation_type",
            "Type",
            ["None", "Fade In", "Fade Out", "Slide Left", "Slide Right", 
             "Slide Up", "Slide Down", "Typewriter", "Bounce"]
        )
        
        # Duration
        self.add_slider_parameter("duration", "Duration", 0.1, 5.0, 1.0, decimals=1)
        
        # Easing
        self.add_combo_parameter(
            "easing",
            "Easing",
            ["Linear", "Ease In", "Ease Out", "Ease In Out", "Bounce", "Elastic"]
        )
        
        # Delay
        self.add_slider_parameter("delay", "Delay", 0.0, 2.0, 0.0, decimals=1)


class VisualEffectsGroup(ParameterGroup):
    """
    Parameter controls for visual effects.
    """
    
    def __init__(self):
        super().__init__("Visual Effects")
        self._setup_controls()
    
    def _setup_controls(self):
        """Set up visual effect controls."""
        # Glow effect
        self.add_checkbox_parameter("glow_enabled", "Enable Glow")
        self.add_slider_parameter("glow_intensity", "Glow Intensity", 0, 100, 50)
        self.add_slider_parameter("glow_radius", "Glow Radius", 1, 20, 5)
        self.add_color_parameter("glow_color", "Glow Color", QColor(255, 255, 100))
        
        # Outline effect
        self.add_checkbox_parameter("outline_enabled", "Enable Outline")
        self.add_slider_parameter("outline_width", "Outline Width", 1, 10, 2)
        self.add_color_parameter("outline_color", "Outline Color", QColor(0, 0, 0))
        
        # Shadow effect
        self.add_checkbox_parameter("shadow_enabled", "Enable Shadow")
        self.add_slider_parameter("shadow_offset_x", "Shadow X", -20, 20, 3)
        self.add_slider_parameter("shadow_offset_y", "Shadow Y", -20, 20, 3)
        self.add_slider_parameter("shadow_blur", "Shadow Blur", 0, 20, 5)
        self.add_color_parameter("shadow_color", "Shadow Color", QColor(0, 0, 0, 128))


class Transform3DGroup(ParameterGroup):
    """
    Parameter controls for 3D transformations.
    """
    
    def __init__(self):
        super().__init__("3D Transform")
        self._setup_controls()
    
    def _setup_controls(self):
        """Set up 3D transform controls."""
        # Rotation
        self.add_slider_parameter("rotation_x", "Rotation X", -180, 180, 0)
        self.add_slider_parameter("rotation_y", "Rotation Y", -180, 180, 0)
        self.add_slider_parameter("rotation_z", "Rotation Z", -180, 180, 0)
        
        # Scale
        self.add_slider_parameter("scale_x", "Scale X", 0.1, 3.0, 1.0, decimals=1)
        self.add_slider_parameter("scale_y", "Scale Y", 0.1, 3.0, 1.0, decimals=1)
        
        # Perspective
        self.add_slider_parameter("perspective", "Perspective", 0.0, 2.0, 0.0, decimals=2)
        
        # Extrusion
        self.add_slider_parameter("extrusion", "Extrusion", 0.0, 10.0, 0.0, decimals=1)


class ColorEffectsGroup(ParameterGroup):
    """
    Parameter controls for color effects.
    """
    
    def __init__(self):
        super().__init__("Color Effects")
        self._setup_controls()
    
    def _setup_controls(self):
        """Set up color effect controls."""
        # Rainbow effect
        self.add_checkbox_parameter("rainbow_enabled", "Enable Rainbow")
        self.add_slider_parameter("rainbow_speed", "Rainbow Speed", 0.1, 5.0, 1.0, decimals=1)
        
        # Pulse effect
        self.add_checkbox_parameter("pulse_enabled", "Enable Pulse")
        self.add_slider_parameter("pulse_speed", "Pulse Speed", 0.1, 5.0, 1.0, decimals=1)
        self.add_slider_parameter("pulse_intensity", "Pulse Intensity", 0, 100, 50)
        
        # Strobe effect
        self.add_checkbox_parameter("strobe_enabled", "Enable Strobe")
        self.add_slider_parameter("strobe_frequency", "Strobe Frequency", 1, 20, 5)


class ParticleEffectsGroup(ParameterGroup):
    """
    Parameter controls for particle effects.
    """
    
    def __init__(self):
        super().__init__("Particle Effects")
        self._setup_controls()
    
    def _setup_controls(self):
        """Set up particle effect controls."""
        # Particle type
        self.add_combo_parameter(
            "particle_type",
            "Type",
            ["None", "Sparkle", "Fire", "Smoke", "Snow", "Hearts"]
        )
        
        # Emission rate
        self.add_slider_parameter("emission_rate", "Emission Rate", 1, 100, 20)
        
        # Particle lifetime
        self.add_slider_parameter("particle_lifetime", "Lifetime", 0.5, 5.0, 2.0, decimals=1)
        
        # Particle size
        self.add_slider_parameter("particle_size", "Size", 1, 20, 5)
        
        # Gravity
        self.add_slider_parameter("gravity", "Gravity", -10.0, 10.0, -2.0, decimals=1)


class EffectPropertiesPanel(QWidget):
    """
    Main effect properties panel with tabbed interface for different effect categories.
    """
    
    # Signals
    effect_parameter_changed = pyqtSignal(str, str, object)  # category, parameter, value
    
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(300)
        self.setMaximumWidth(400)
        
        self.effect_groups = {}
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the effect properties UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        title_label = QLabel("Effect Properties")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        layout.addWidget(title_label)
        
        # Create scroll area for effect controls
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Create tabbed interface
        tab_widget = QTabWidget()
        
        # Animation Effects Tab
        self.animation_group = AnimationEffectsGroup()
        self.animation_group.parameter_changed.connect(
            lambda param, value: self.effect_parameter_changed.emit("animation", param, value)
        )
        tab_widget.addTab(self.animation_group, "Animation")
        self.effect_groups["animation"] = self.animation_group
        
        # Visual Effects Tab
        self.visual_group = VisualEffectsGroup()
        self.visual_group.parameter_changed.connect(
            lambda param, value: self.effect_parameter_changed.emit("visual", param, value)
        )
        tab_widget.addTab(self.visual_group, "Visual")
        self.effect_groups["visual"] = self.visual_group
        
        # 3D Transform Tab
        self.transform_group = Transform3DGroup()
        self.transform_group.parameter_changed.connect(
            lambda param, value: self.effect_parameter_changed.emit("transform", param, value)
        )
        tab_widget.addTab(self.transform_group, "3D")
        self.effect_groups["transform"] = self.transform_group
        
        # Color Effects Tab
        self.color_group = ColorEffectsGroup()
        self.color_group.parameter_changed.connect(
            lambda param, value: self.effect_parameter_changed.emit("color", param, value)
        )
        tab_widget.addTab(self.color_group, "Color")
        self.effect_groups["color"] = self.color_group
        
        # Particle Effects Tab
        self.particle_group = ParticleEffectsGroup()
        self.particle_group.parameter_changed.connect(
            lambda param, value: self.effect_parameter_changed.emit("particle", param, value)
        )
        tab_widget.addTab(self.particle_group, "Particles")
        self.effect_groups["particle"] = self.particle_group
        
        scroll_area.setWidget(tab_widget)
        layout.addWidget(scroll_area)
        
        # Preset controls
        preset_layout = QHBoxLayout()
        
        save_preset_button = QPushButton("Save Preset")
        save_preset_button.clicked.connect(self._save_preset)
        preset_layout.addWidget(save_preset_button)
        
        load_preset_button = QPushButton("Load Preset")
        load_preset_button.clicked.connect(self._load_preset)
        preset_layout.addWidget(load_preset_button)
        
        layout.addLayout(preset_layout)
        
        # Reset button
        reset_button = QPushButton("Reset All Effects")
        reset_button.clicked.connect(self._reset_all_effects)
        layout.addWidget(reset_button)
    
    def _save_preset(self):
        """Save current effect settings as a preset."""
        # TODO: Implement preset saving
        pass
    
    def _load_preset(self):
        """Load effect settings from a preset."""
        # TODO: Implement preset loading
        pass
    
    def _reset_all_effects(self):
        """Reset all effect parameters to default values."""
        for group in self.effect_groups.values():
            # Reset each parameter group to defaults
            # This would need to be implemented in each group
            pass
    
    def get_effect_parameters(self, category):
        """Get all parameters for a specific effect category."""
        if category in self.effect_groups:
            group = self.effect_groups[category]
            parameters = {}
            for param_name in group.parameters:
                parameters[param_name] = group.get_parameter_value(param_name)
            return parameters
        return {}
    
    def set_effect_parameters(self, category, parameters):
        """Set parameters for a specific effect category."""
        if category in self.effect_groups:
            group = self.effect_groups[category]
            for param_name, value in parameters.items():
                group.set_parameter_value(param_name, value)
    
    def update_selection(self, track_id, keyframe_time):
        """Update the panel based on timeline selection."""
        # TODO: Load effect parameters from selected keyframe
        # This will be implemented when timeline integration is complete
        pass