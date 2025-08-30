#!/usr/bin/env python3
"""
Demo script for particle system functionality.

This script demonstrates the particle system foundation including:
- ParticleSystem class with GPU-based particle simulation
- Particle emitters with configurable emission rates and lifetimes
- Physics simulation for particle movement and behavior
- Different particle types: sparkle, fire, and smoke effects
"""

import sys
import time
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel
from PyQt6.QtCore import QTimer
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtGui import QSurfaceFormat

import OpenGL.GL as gl

from src.effects.particle_system import ParticleSystem
from src.graphics.shader_manager import ShaderManager
from src.core.models import ParticleEffect, ParticleType


class ParticleSystemDemo(QOpenGLWidget):
    """OpenGL widget demonstrating particle system functionality."""
    
    def __init__(self):
        super().__init__()
        self.particle_system = None
        self.shader_manager = None
        self.last_time = time.time()
        self.view_matrix = np.eye(4, dtype=np.float32)
        self.projection_matrix = np.eye(4, dtype=np.float32)
        
        # Demo state
        self.demo_effects = {}
        self.effect_positions = {
            'sparkle': (-200.0, 0.0, 0.0),
            'fire': (0.0, -100.0, 0.0),
            'smoke': (200.0, 0.0, 0.0)
        }
        
        # Setup timer for animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)  # ~60 FPS
    
    def initializeGL(self):
        """Initialize OpenGL context and particle system."""
        try:
            # Set up OpenGL state
            gl.glClearColor(0.1, 0.1, 0.2, 1.0)
            gl.glEnable(gl.GL_DEPTH_TEST)
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
            
            # Initialize shader manager
            self.shader_manager = ShaderManager()
            
            # Create basic particle shaders if they don't exist
            self._create_fallback_shaders()
            
            # Initialize particle system
            self.particle_system = ParticleSystem(self.shader_manager)
            
            if not self.particle_system.initialize():
                print("Warning: Particle system initialization failed, using fallback")
                return
            
            # Create demo effects
            self._create_demo_effects()
            
            print("Particle system demo initialized successfully")
            
        except Exception as e:
            print(f"Error initializing particle system demo: {e}")
    
    def _create_fallback_shaders(self):
        """Create fallback shaders if files don't exist."""
        try:
            # Try to load existing shaders first
            shader = self.shader_manager.load_shader_program(
                "particle", "particle_vertex.glsl", "particle_fragment.glsl"
            )
            if shader:
                return
        except:
            pass
        
        # Create fallback shaders from source
        vertex_source = """
        #version 330 core
        layout (location = 0) in vec2 aPosition;
        layout (location = 1) in vec2 aTexCoord;
        layout (location = 2) in vec3 aInstancePos;
        layout (location = 3) in vec4 aInstanceColor;
        layout (location = 4) in float aInstanceSize;
        layout (location = 5) in float aInstanceRotation;
        
        uniform mat4 viewMatrix;
        uniform mat4 projectionMatrix;
        
        out vec2 texCoord;
        out vec4 particleColor;
        
        void main() {
            float cosR = cos(aInstanceRotation);
            float sinR = sin(aInstanceRotation);
            vec2 rotatedPos = vec2(
                aPosition.x * cosR - aPosition.y * sinR,
                aPosition.x * sinR + aPosition.y * cosR
            );
            rotatedPos *= aInstanceSize;
            vec3 worldPos = aInstancePos + vec3(rotatedPos, 0.0);
            gl_Position = projectionMatrix * viewMatrix * vec4(worldPos, 1.0);
            texCoord = aTexCoord;
            particleColor = aInstanceColor;
        }
        """
        
        fragment_source = """
        #version 330 core
        in vec2 texCoord;
        in vec4 particleColor;
        out vec4 fragColor;
        
        void main() {
            vec2 center = vec2(0.5, 0.5);
            float dist = distance(texCoord, center);
            float alpha = 1.0 - smoothstep(0.0, 0.5, dist);
            vec4 color = particleColor;
            color.a *= alpha;
            if (color.a < 0.01) discard;
            fragColor = color;
        }
        """
        
        self.shader_manager.load_shader_from_source("particle", vertex_source, fragment_source)
    
    def _create_demo_effects(self):
        """Create demonstration particle effects."""
        try:
            # Create sparkle effect with texture-based rendering
            sparkle_success = self.particle_system.create_sparkle_effect(
                "demo_sparkle", 
                self.effect_positions['sparkle'],
                emission_rate=40.0,  # Increased for better visibility
                lifetime=3.0
            )
            
            # Create fire effect with realistic behavior and coloring
            fire_success = self.particle_system.create_fire_effect(
                "demo_fire",
                self.effect_positions['fire'],
                emission_rate=120.0,  # Increased for more dramatic effect
                lifetime=1.8
            )
            
            # Create smoke effect with alpha blending and wind simulation
            smoke_success = self.particle_system.create_smoke_effect(
                "demo_smoke",
                self.effect_positions['smoke'],
                emission_rate=35.0,
                lifetime=5.0  # Longer lifetime for smoke trails
            )
            
            self.demo_effects = {
                'sparkle': sparkle_success,
                'fire': fire_success,
                'smoke': smoke_success
            }
            
            effects_created = sum(self.demo_effects.values())
            print(f"Created {effects_created}/3 enhanced particle effects")
            
            # Set up smoke wind for demonstration
            if smoke_success and "demo_smoke" in self.particle_system.emitters:
                smoke_emitter = self.particle_system.emitters["demo_smoke"]
                if hasattr(smoke_emitter, 'set_wind_force'):
                    smoke_emitter.set_wind_force((20.0, 3.0, 0.0))  # Horizontal wind
            
        except Exception as e:
            print(f"Error creating demo effects: {e}")
    
    def resizeGL(self, width, height):
        """Handle window resize."""
        if height == 0:
            height = 1
        
        gl.glViewport(0, 0, width, height)
        
        # Update projection matrix
        aspect = width / height
        fov = 45.0
        near = 0.1
        far = 1000.0
        
        # Simple perspective projection matrix
        f = 1.0 / np.tan(np.radians(fov) / 2.0)
        self.projection_matrix = np.array([
            [f / aspect, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (far + near) / (near - far), (2 * far * near) / (near - far)],
            [0, 0, -1, 0]
        ], dtype=np.float32)
        
        # Simple view matrix (camera looking down negative Z)
        self.view_matrix = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, -500],  # Move camera back
            [0, 0, 0, 1]
        ], dtype=np.float32)
    
    def paintGL(self):
        """Render the particle system."""
        try:
            # Clear buffers
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            
            if not self.particle_system or not self.particle_system._is_initialized:
                return
            
            # Render particles
            self.particle_system.render(self.view_matrix, self.projection_matrix)
            
        except Exception as e:
            print(f"Error in paintGL: {e}")
    
    def update_animation(self):
        """Update particle system animation."""
        try:
            current_time = time.time()
            delta_time = current_time - self.last_time
            self.last_time = current_time
            
            if self.particle_system and self.particle_system._is_initialized:
                # Update particle system
                self.particle_system.update(delta_time)
                
                # Trigger redraw
                self.update()
            
        except Exception as e:
            print(f"Error updating animation: {e}")
    
    def toggle_effect(self, effect_name):
        """Toggle a particle effect on/off."""
        if not self.particle_system:
            return
        
        emitter_id = f"demo_{effect_name}"
        
        # Check if emitter exists and toggle its state
        if emitter_id in self.particle_system.emitters:
            emitter = self.particle_system.emitters[emitter_id]
            emitter.set_active(not emitter.is_active)
            print(f"{effect_name.capitalize()} effect {'enabled' if emitter.is_active else 'disabled'}")
    
    def get_particle_stats(self):
        """Get current particle statistics."""
        if not self.particle_system:
            return "Particle system not initialized"
        
        total_particles = self.particle_system.get_total_particle_count()
        sparkle_count = self.particle_system.get_emitter_particle_count("demo_sparkle")
        fire_count = self.particle_system.get_emitter_particle_count("demo_fire")
        smoke_count = self.particle_system.get_emitter_particle_count("demo_smoke")
        
        return f"Total: {total_particles} | Sparkle: {sparkle_count} | Fire: {fire_count} | Smoke: {smoke_count}"


class ParticleSystemWindow(QMainWindow):
    """Main window for particle system demo."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Particle System Foundation Demo")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Create OpenGL widget
        self.gl_widget = ParticleSystemDemo()
        layout.addWidget(self.gl_widget)
        
        # Create control panel
        control_layout = QHBoxLayout()
        
        # Effect toggle buttons
        self.sparkle_button = QPushButton("Toggle Sparkle")
        self.sparkle_button.clicked.connect(lambda: self.gl_widget.toggle_effect("sparkle"))
        control_layout.addWidget(self.sparkle_button)
        
        self.fire_button = QPushButton("Toggle Fire")
        self.fire_button.clicked.connect(lambda: self.gl_widget.toggle_effect("fire"))
        control_layout.addWidget(self.fire_button)
        
        self.smoke_button = QPushButton("Toggle Smoke")
        self.smoke_button.clicked.connect(lambda: self.gl_widget.toggle_effect("smoke"))
        control_layout.addWidget(self.smoke_button)
        
        # Clear particles button
        clear_button = QPushButton("Clear All Particles")
        clear_button.clicked.connect(self.clear_particles)
        control_layout.addWidget(clear_button)
        
        layout.addLayout(control_layout)
        
        # Stats label
        self.stats_label = QLabel("Particle Stats: Initializing...")
        layout.addWidget(self.stats_label)
        
        # Update stats timer
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(500)  # Update every 500ms
    
    def clear_particles(self):
        """Clear all particles from the system."""
        if self.gl_widget.particle_system:
            self.gl_widget.particle_system.clear_all_particles()
            print("All particles cleared")
    
    def update_stats(self):
        """Update particle statistics display."""
        stats = self.gl_widget.get_particle_stats()
        self.stats_label.setText(f"Particle Stats: {stats}")


def main():
    """Run the particle system demo."""
    # Set up OpenGL format
    format = QSurfaceFormat()
    format.setVersion(3, 3)
    format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    format.setDepthBufferSize(24)
    format.setStencilBufferSize(8)
    format.setSamples(4)  # Anti-aliasing
    QSurfaceFormat.setDefaultFormat(format)
    
    # Create application
    app = QApplication(sys.argv)
    
    # Create and show window
    window = ParticleSystemWindow()
    window.show()
    
    print("Particle System Foundation Demo")
    print("=" * 40)
    print("This demo showcases:")
    print("- GPU-based particle simulation")
    print("- Configurable particle emitters")
    print("- Physics simulation with gravity and wind")
    print("- Three particle types: Sparkle, Fire, and Smoke")
    print()
    print("Controls:")
    print("- Use buttons to toggle different particle effects")
    print("- Clear All Particles button removes all active particles")
    print("- Particle statistics are updated in real-time")
    print()
    print("Implementation Features:")
    print("- BaseParticleEmitter with physics simulation")
    print("- Specialized emitters for different effects")
    print("- GPU-based rendering with instanced drawing")
    print("- Configurable emission rates and lifetimes")
    print("- Real-time particle management and cleanup")
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()