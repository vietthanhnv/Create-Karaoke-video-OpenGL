"""
Enhanced particle system implementation with specific particle effects.
Implements sparkle, fire, and smoke effects with texture-based rendering.
"""

import math
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

try:
    import OpenGL.GL as gl
except ImportError:
    # Fallback for testing without OpenGL
    class MockGL:
        GL_ARRAY_BUFFER = 0x8892
        GL_STATIC_DRAW = 0x88E4
        GL_DYNAMIC_DRAW = 0x88E8
        GL_TRIANGLES = 0x0004
        GL_FLOAT = 0x1406
        GL_FALSE = 0
        GL_BLEND = 0x0BE2
        GL_SRC_ALPHA = 0x0302
        GL_ONE_MINUS_SRC_ALPHA = 0x0303
        GL_DEPTH_TEST = 0x0B71
        GL_TRUE = 1
        GL_TEXTURE_2D = 0x0DE1
        GL_RGBA = 0x1908
        GL_UNSIGNED_BYTE = 0x1401
        GL_TEXTURE_MIN_FILTER = 0x2801
        GL_TEXTURE_MAG_FILTER = 0x2800
        GL_LINEAR = 0x2601
        GL_TEXTURE_WRAP_S = 0x2802
        GL_TEXTURE_WRAP_T = 0x2803
        GL_CLAMP_TO_EDGE = 0x812F
        GL_TEXTURE0 = 0x84C0
        
        @staticmethod
        def glGenVertexArrays(n): return 1
        @staticmethod
        def glGenBuffers(n): return 1
        @staticmethod
        def glGenTextures(n): return 1
        @staticmethod
        def glBindVertexArray(vao): pass
        @staticmethod
        def glBindBuffer(target, buffer): pass
        @staticmethod
        def glBindTexture(target, texture): pass
        @staticmethod
        def glBufferData(target, size, data, usage): pass
        @staticmethod
        def glVertexAttribPointer(index, size, type, normalized, stride, pointer): pass
        @staticmethod
        def glEnableVertexAttribArray(index): pass
        @staticmethod
        def glVertexAttribDivisor(index, divisor): pass
        @staticmethod
        def glBufferSubData(target, offset, size, data): pass
        @staticmethod
        def glEnable(cap): pass
        @staticmethod
        def glDisable(cap): pass
        @staticmethod
        def glBlendFunc(sfactor, dfactor): pass
        @staticmethod
        def glDepthMask(flag): pass
        @staticmethod
        def glDrawArraysInstanced(mode, first, count, instancecount): pass
        @staticmethod
        def glDeleteVertexArrays(n, arrays): pass
        @staticmethod
        def glDeleteBuffers(n, buffers): pass
        @staticmethod
        def glDeleteTextures(n, textures): pass
        @staticmethod
        def glTexImage2D(target, level, internalformat, width, height, border, format, type, data): pass
        @staticmethod
        def glTexParameteri(target, pname, param): pass
        @staticmethod
        def glActiveTexture(texture): pass
    
    gl = MockGL()

from ..core.models import ParticleEffect, ParticleType, TextElement
from ..graphics.shader_manager import ShaderManager


@dataclass
class Particle:
    """Individual particle data structure with physics properties."""
    position: Tuple[float, float, float]
    velocity: Tuple[float, float, float]
    acceleration: Tuple[float, float, float]
    color: Tuple[float, float, float, float]
    size: float
    life: float
    max_life: float
    rotation: float
    angular_velocity: float
    texture_index: int
    
    def is_alive(self) -> bool:
        """Check if particle is still alive."""
        return self.life > 0.0
    
    def update(self, delta_time: float) -> None:
        """Update particle physics and lifetime."""
        # Update lifetime
        self.life -= delta_time / self.max_life
        
        # Update velocity with acceleration
        self.velocity = (
            self.velocity[0] + self.acceleration[0] * delta_time,
            self.velocity[1] + self.acceleration[1] * delta_time,
            self.velocity[2] + self.acceleration[2] * delta_time
        )
        
        # Update position with velocity
        self.position = (
            self.position[0] + self.velocity[0] * delta_time,
            self.position[1] + self.velocity[1] * delta_time,
            self.position[2] + self.velocity[2] * delta_time
        )
        
        # Update rotation
        self.rotation += self.angular_velocity * delta_time


@dataclass
class ParticleEmitterConfig:
    """Configuration for particle emitters with physics parameters."""
    emission_rate: float
    max_particles: int
    lifetime_min: float
    lifetime_max: float
    position: Tuple[float, float, float]
    position_variance: Tuple[float, float, float]
    velocity_min: Tuple[float, float, float]
    velocity_max: Tuple[float, float, float]
    acceleration: Tuple[float, float, float]
    size_min: float
    size_max: float
    color_start: Tuple[float, float, float, float]
    color_end: Tuple[float, float, float, float]
    texture_path: Optional[str] = None
    blend_mode: str = "alpha"


class BaseParticleEmitter(ABC):
    """Base class for particle emitters with configurable emission and physics."""
    
    def __init__(self, config: ParticleEmitterConfig):
        self.config = config
        self.particles: List[Particle] = []
        self.emission_accumulator = 0.0
        self.is_active = True
        self.texture_id = 0
    
    @abstractmethod
    def create_particle(self) -> Particle:
        """Create a new particle with emitter-specific properties."""
        pass
    
    def update(self, delta_time: float) -> None:
        """Update emitter and all particles with physics simulation."""
        if not self.is_active:
            return
        
        # Update existing particles with physics
        alive_particles = []
        for particle in self.particles:
            particle.update(delta_time)
            if particle.is_alive():
                alive_particles.append(particle)
        
        self.particles = alive_particles
        
        # Emit new particles based on emission rate
        if len(self.particles) < self.config.max_particles:
            self._emit_particles(delta_time)
    
    def _emit_particles(self, delta_time: float) -> None:
        """Emit new particles based on configurable emission rate."""
        self.emission_accumulator += self.config.emission_rate * delta_time
        
        particles_to_emit = int(self.emission_accumulator)
        self.emission_accumulator -= particles_to_emit
        
        for _ in range(particles_to_emit):
            if len(self.particles) >= self.config.max_particles:
                break
            
            particle = self.create_particle()
            self.particles.append(particle)
    
    def _random_in_range(self, min_val: float, max_val: float) -> float:
        """Generate random value in range for physics variation."""
        return min_val + np.random.random() * (max_val - min_val)
    
    def _random_vector_in_range(self, min_vec: Tuple[float, float, float],
                               max_vec: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """Generate random vector with components in specified ranges."""
        return (
            self._random_in_range(min_vec[0], max_vec[0]),
            self._random_in_range(min_vec[1], max_vec[1]),
            self._random_in_range(min_vec[2], max_vec[2])
        )
    
    def get_particle_count(self) -> int:
        """Get current number of active particles."""
        return len(self.particles)
    
    def clear_particles(self) -> None:
        """Remove all particles."""
        self.particles.clear()
    
    def set_position(self, position: Tuple[float, float, float]) -> None:
        """Update emitter position."""
        self.config.position = position
    
    def set_active(self, active: bool) -> None:
        """Enable or disable particle emission."""
        self.is_active = active


class SparkleEmitter(BaseParticleEmitter):
    """Sparkle particle emitter with texture-based rendering and twinkling behavior."""
    
    def __init__(self, config: ParticleEmitterConfig):
        super().__init__(config)
        self.twinkle_frequency = 3.0  # Twinkles per second
        self.brightness_variation = 0.4  # How much brightness varies
    
    def create_particle(self) -> Particle:
        """Create a sparkle particle with texture-based rendering and twinkling."""
        pos_variance = self.config.position_variance
        position = (
            self.config.position[0] + self._random_in_range(-pos_variance[0], pos_variance[0]),
            self.config.position[1] + self._random_in_range(-pos_variance[1], pos_variance[1]),
            self.config.position[2] + self._random_in_range(-pos_variance[2], pos_variance[2])
        )
        
        # Sparkle particles have gentle, floating movement
        velocity = self._random_vector_in_range(
            self.config.velocity_min,
            self.config.velocity_max
        )
        
        # Add slight upward bias for magical floating effect
        velocity = (velocity[0] * 0.7, velocity[1] + 5.0, velocity[2] * 0.7)
        
        lifetime = self._random_in_range(
            self.config.lifetime_min,
            self.config.lifetime_max
        )
        
        # Sparkles vary in size for visual interest
        size = self._random_in_range(
            self.config.size_min,
            self.config.size_max
        )
        
        # Random rotation for sparkle orientation
        rotation = self._random_in_range(0, 2 * math.pi)
        angular_velocity = self._random_in_range(-1.5, 1.5)
        
        # Sparkle color with slight variation
        base_color = self.config.color_start
        color_variation = 0.2
        color = (
            max(0.0, min(1.0, base_color[0] + self._random_in_range(-color_variation, color_variation))),
            max(0.0, min(1.0, base_color[1] + self._random_in_range(-color_variation, color_variation))),
            max(0.0, min(1.0, base_color[2] + self._random_in_range(-color_variation, color_variation))),
            base_color[3]
        )
        
        return Particle(
            position=position,
            velocity=velocity,
            acceleration=self.config.acceleration,
            color=color,
            size=size,
            life=1.0,
            max_life=lifetime,
            rotation=rotation,
            angular_velocity=angular_velocity,
            texture_index=0  # Sparkle texture index
        )
    
    def update(self, delta_time: float) -> None:
        """Update sparkle particles with twinkling effect."""
        super().update(delta_time)
        
        # Apply twinkling effect to existing particles
        current_time = time.time()
        for particle in self.particles:
            # Create twinkling brightness variation
            twinkle_phase = current_time * self.twinkle_frequency + particle.rotation
            brightness_factor = 1.0 + self.brightness_variation * math.sin(twinkle_phase)
            
            # Apply brightness to alpha channel
            original_alpha = self.config.color_start[3]
            particle.color = (
                particle.color[0],
                particle.color[1], 
                particle.color[2],
                original_alpha * brightness_factor * particle.life
            )


class FireEmitter(BaseParticleEmitter):
    """Fire particle emitter with realistic particle behavior and coloring."""
    
    def __init__(self, config: ParticleEmitterConfig):
        super().__init__(config)
        self.heat_dissipation = 0.8  # How quickly fire cools
        self.flicker_intensity = 0.3  # Fire flicker strength
    
    def create_particle(self) -> Particle:
        """Create a fire particle with realistic behavior and coloring."""
        pos_variance = self.config.position_variance
        position = (
            self.config.position[0] + self._random_in_range(-pos_variance[0], pos_variance[0]),
            self.config.position[1],
            self.config.position[2] + self._random_in_range(-pos_variance[2], pos_variance[2])
        )
        
        base_velocity = self._random_vector_in_range(
            self.config.velocity_min,
            self.config.velocity_max
        )
        
        # Fire particles have strong upward movement with slight horizontal drift
        velocity = (
            base_velocity[0] * 0.4,  # Slight horizontal drift
            abs(base_velocity[1]) + 20.0,  # Strong upward movement
            base_velocity[2] * 0.4
        )
        
        lifetime = self._random_in_range(
            self.config.lifetime_min,
            self.config.lifetime_max
        )
        
        # Fire particles start larger and shrink as they cool
        size = self._random_in_range(
            self.config.size_min,
            self.config.size_max
        )
        
        rotation = self._random_in_range(0, 2 * math.pi)
        angular_velocity = self._random_in_range(-1.0, 1.0)
        
        # Fire starts hot (red/orange) and cools to yellow/white
        heat_factor = self._random_in_range(0.7, 1.0)
        color = (
            1.0,  # Red component always high
            0.2 + 0.6 * heat_factor,  # Green increases with heat
            0.0 + 0.3 * heat_factor,  # Blue only at very high heat
            self.config.color_start[3]
        )
        
        return Particle(
            position=position,
            velocity=velocity,
            acceleration=self.config.acceleration,
            color=color,
            size=size,
            life=1.0,
            max_life=lifetime,
            rotation=rotation,
            angular_velocity=angular_velocity,
            texture_index=1  # Fire texture index
        )
    
    def update(self, delta_time: float) -> None:
        """Update fire particles with realistic cooling and flickering."""
        super().update(delta_time)
        
        # Apply fire-specific effects to existing particles
        current_time = time.time()
        for particle in self.particles:
            # Calculate cooling effect (particles get cooler as they age)
            age_factor = 1.0 - particle.life
            cooling = age_factor * self.heat_dissipation
            
            # Fire color transition: Red -> Orange -> Yellow -> White (as it cools)
            heat_level = particle.life * (1.0 - cooling)
            
            # Add flickering effect
            flicker_phase = current_time * 8.0 + particle.rotation * 2.0
            flicker = 1.0 + self.flicker_intensity * math.sin(flicker_phase)
            
            # Update color based on heat level and flickering
            red = 1.0 * flicker
            green = (0.2 + 0.8 * heat_level) * flicker
            blue = max(0.0, heat_level - 0.5) * 2.0 * flicker
            
            particle.color = (
                min(1.0, red),
                min(1.0, green),
                min(1.0, blue),
                particle.life * self.config.color_start[3]
            )
            
            # Particles shrink as they cool
            size_factor = 0.5 + 0.5 * heat_level
            original_size = self.config.size_min + (self.config.size_max - self.config.size_min) * 0.5
            particle.size = original_size * size_factor


class SmokeEmitter(BaseParticleEmitter):
    """Smoke particle emitter with alpha blending and wind simulation."""
    
    def __init__(self, config: ParticleEmitterConfig):
        super().__init__(config)
        self.wind_force = (15.0, 2.0, 0.0)  # Stronger horizontal wind
        self.turbulence_strength = 0.4  # Increased turbulence
        self.expansion_rate = 1.5  # How quickly smoke expands
        self.density_variation = 0.3  # Smoke density variation
    
    def create_particle(self) -> Particle:
        """Create a smoke particle with alpha blending and wind simulation."""
        pos_variance = self.config.position_variance
        position = (
            self.config.position[0] + self._random_in_range(-pos_variance[0], pos_variance[0]),
            self.config.position[1],
            self.config.position[2] + self._random_in_range(-pos_variance[2], pos_variance[2])
        )
        
        velocity = self._random_vector_in_range(
            self.config.velocity_min,
            self.config.velocity_max
        )
        
        # Add stronger turbulence for realistic smoke behavior
        turbulence = (
            self._random_in_range(-self.turbulence_strength, self.turbulence_strength) * 20.0,
            self._random_in_range(-self.turbulence_strength, self.turbulence_strength) * 10.0,
            self._random_in_range(-self.turbulence_strength, self.turbulence_strength) * 20.0
        )
        
        # Combine base acceleration with wind and turbulence
        acceleration = (
            self.config.acceleration[0] + self.wind_force[0] + turbulence[0],
            self.config.acceleration[1] + self.wind_force[1] + turbulence[1],
            self.config.acceleration[2] + self.wind_force[2] + turbulence[2]
        )
        
        lifetime = self._random_in_range(
            self.config.lifetime_min,
            self.config.lifetime_max
        )
        
        # Smoke starts small and expands
        size = self._random_in_range(
            self.config.size_min,
            self.config.size_max
        ) * 0.5  # Start smaller
        
        rotation = self._random_in_range(0, 2 * math.pi)
        angular_velocity = self._random_in_range(-0.8, 0.8)
        
        # Smoke color with density variation
        density = self._random_in_range(
            1.0 - self.density_variation,
            1.0 + self.density_variation
        )
        
        base_color = self.config.color_start
        color = (
            base_color[0] * density,
            base_color[1] * density,
            base_color[2] * density,
            base_color[3] * density
        )
        
        return Particle(
            position=position,
            velocity=velocity,
            acceleration=acceleration,
            color=color,
            size=size,
            life=1.0,
            max_life=lifetime,
            rotation=rotation,
            angular_velocity=angular_velocity,
            texture_index=2  # Smoke texture index
        )
    
    def update(self, delta_time: float) -> None:
        """Update smoke particles with expansion and wind effects."""
        super().update(delta_time)
        
        # Apply smoke-specific effects to existing particles
        for particle in self.particles:
            # Smoke expands as it ages
            age_factor = 1.0 - particle.life
            expansion_factor = 1.0 + age_factor * self.expansion_rate
            
            # Calculate original size
            original_size = self.config.size_min + (self.config.size_max - self.config.size_min) * 0.5
            particle.size = original_size * expansion_factor * 0.5
            
            # Smoke becomes more transparent as it expands and ages
            alpha_factor = particle.life * (1.0 - age_factor * 0.5)
            
            particle.color = (
                particle.color[0],
                particle.color[1],
                particle.color[2],
                self.config.color_start[3] * alpha_factor
            )
            
            # Add continuous turbulence to existing particles
            if np.random.random() < 0.1:  # 10% chance per frame
                turbulence_force = (
                    self._random_in_range(-5.0, 5.0),
                    self._random_in_range(-2.0, 2.0),
                    self._random_in_range(-5.0, 5.0)
                )
                
                particle.velocity = (
                    particle.velocity[0] + turbulence_force[0] * delta_time,
                    particle.velocity[1] + turbulence_force[1] * delta_time,
                    particle.velocity[2] + turbulence_force[2] * delta_time
                )
    
    def set_wind_force(self, wind: Tuple[float, float, float]) -> None:
        """Set wind force affecting smoke particles."""
        self.wind_force = wind
    
    def set_turbulence(self, strength: float) -> None:
        """Set turbulence strength for smoke movement."""
        self.turbulence_strength = strength


class ParticleRenderer:
    """GPU-based particle renderer with instanced drawing and texture support."""
    
    def __init__(self, shader_manager: ShaderManager):
        self.shader_manager = shader_manager
        self.max_particles = 10000
        self.particle_shader = None
        self.vao = 0
        self.vbo_vertices = 0
        self.vbo_instances = 0
        self.particle_textures = []
        self.texture_paths = [
            "assets/textures/sparkle.png",
            "assets/textures/fire.png", 
            "assets/textures/smoke.png"
        ]
        self._is_initialized = False
    
    def initialize(self) -> bool:
        """Initialize GPU resources for particle rendering."""
        try:
            # Load particle shader
            self.particle_shader = self.shader_manager.load_shader_program(
                "particle", "particle_vertex.glsl", "particle_fragment.glsl"
            )
            
            if not self.particle_shader:
                print("Warning: Could not load particle shader, using fallback")
                return False
            
            # Create vertex array and buffers
            self.vao = gl.glGenVertexArrays(1)
            self.vbo_vertices = gl.glGenBuffers(1)
            self.vbo_instances = gl.glGenBuffers(1)
            
            # Set up vertex data for quad
            vertices = np.array([
                # Position  # TexCoord
                -0.5, -0.5,  0.0, 0.0,
                 0.5, -0.5,  1.0, 0.0,
                 0.5,  0.5,  1.0, 1.0,
                -0.5, -0.5,  0.0, 0.0,
                 0.5,  0.5,  1.0, 1.0,
                -0.5,  0.5,  0.0, 1.0
            ], dtype=np.float32)
            
            gl.glBindVertexArray(self.vao)
            
            # Upload vertex data
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo_vertices)
            gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)
            
            # Position attribute
            gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 4 * 4, None)
            gl.glEnableVertexAttribArray(0)
            
            # Texture coordinate attribute
            gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, 4 * 4, gl.ctypes.c_void_p(2 * 4))
            gl.glEnableVertexAttribArray(1)
            
            # Set up instance buffer
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo_instances)
            gl.glBufferData(gl.GL_ARRAY_BUFFER, self.max_particles * 9 * 4, None, gl.GL_DYNAMIC_DRAW)
            
            # Instance position (3 floats)
            gl.glVertexAttribPointer(2, 3, gl.GL_FLOAT, gl.GL_FALSE, 9 * 4, None)
            gl.glEnableVertexAttribArray(2)
            gl.glVertexAttribDivisor(2, 1)
            
            # Instance color (4 floats)
            gl.glVertexAttribPointer(3, 4, gl.GL_FLOAT, gl.GL_FALSE, 9 * 4, gl.ctypes.c_void_p(3 * 4))
            gl.glEnableVertexAttribArray(3)
            gl.glVertexAttribDivisor(3, 1)
            
            # Instance size (1 float)
            gl.glVertexAttribPointer(4, 1, gl.GL_FLOAT, gl.GL_FALSE, 9 * 4, gl.ctypes.c_void_p(7 * 4))
            gl.glEnableVertexAttribArray(4)
            gl.glVertexAttribDivisor(4, 1)
            
            # Instance rotation (1 float)
            gl.glVertexAttribPointer(5, 1, gl.GL_FLOAT, gl.GL_FALSE, 9 * 4, gl.ctypes.c_void_p(8 * 4))
            gl.glEnableVertexAttribArray(5)
            gl.glVertexAttribDivisor(5, 1)
            
            # Create particle textures
            self._create_particle_textures()
            
            self._is_initialized = True
            return True
            
        except Exception as e:
            print(f"Failed to initialize particle renderer: {e}")
            return False
    
    def _create_particle_textures(self):
        """Create procedural textures for different particle types."""
        self.particle_textures = []
        
        for i, texture_path in enumerate(self.texture_paths):
            texture_id = gl.glGenTextures(1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)
            
            # Create procedural texture based on type
            if i == 0:  # Sparkle
                texture_data = self._create_sparkle_texture()
            elif i == 1:  # Fire
                texture_data = self._create_fire_texture()
            else:  # Smoke
                texture_data = self._create_smoke_texture()
            
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, 64, 64, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, texture_data)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
            
            self.particle_textures.append(texture_id)
    
    def _create_sparkle_texture(self) -> np.ndarray:
        """Create sparkle texture with star pattern."""
        size = 64
        texture = np.zeros((size, size, 4), dtype=np.uint8)
        center = size // 2
        
        for y in range(size):
            for x in range(size):
                dx = x - center
                dy = y - center
                dist = np.sqrt(dx*dx + dy*dy)
                
                # Create star pattern
                angle = np.arctan2(dy, dx)
                star_intensity = abs(np.cos(4 * angle)) * 0.7 + 0.3
                
                # Radial falloff
                if dist < center:
                    alpha = (1.0 - dist / center) * star_intensity
                    texture[y, x] = [255, 255, 255, int(alpha * 255)]
        
        return texture
    
    def _create_fire_texture(self) -> np.ndarray:
        """Create fire texture with flame pattern."""
        size = 64
        texture = np.zeros((size, size, 4), dtype=np.uint8)
        center = size // 2
        
        for y in range(size):
            for x in range(size):
                dx = x - center
                dy = y - center
                dist = np.sqrt(dx*dx + dy*dy)
                
                # Create flame shape (wider at bottom, narrower at top)
                flame_width = center * (1.0 - y / size) * 0.8 + center * 0.2
                
                if dist < flame_width and dist < center:
                    alpha = (1.0 - dist / flame_width) * (1.0 - y / size * 0.5)
                    texture[y, x] = [255, 128, 0, int(alpha * 255)]
        
        return texture
    
    def _create_smoke_texture(self) -> np.ndarray:
        """Create smoke texture with soft circular gradient."""
        size = 64
        texture = np.zeros((size, size, 4), dtype=np.uint8)
        center = size // 2
        
        for y in range(size):
            for x in range(size):
                dx = x - center
                dy = y - center
                dist = np.sqrt(dx*dx + dy*dy)
                
                # Soft circular gradient
                if dist < center:
                    alpha = (1.0 - dist / center) ** 2
                    texture[y, x] = [128, 128, 128, int(alpha * 255)]
        
        return texture
    
    def render_particles(self, particles: List[Particle], view_matrix: np.ndarray, projection_matrix: np.ndarray):
        """Render particles using instanced drawing."""
        if not self._is_initialized or not particles:
            return
        
        # Prepare instance data
        instance_data = []
        for particle in particles:
            instance_data.extend([
                particle.position[0], particle.position[1], particle.position[2],  # Position
                particle.color[0], particle.color[1], particle.color[2], particle.color[3],  # Color
                particle.size,  # Size
                particle.rotation  # Rotation
            ])
        
        if not instance_data:
            return
        
        instance_array = np.array(instance_data, dtype=np.float32)
        
        # Upload instance data
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo_instances)
        gl.glBufferSubData(gl.GL_ARRAY_BUFFER, 0, instance_array.nbytes, instance_array)
        
        # Set up rendering state
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glDepthMask(gl.GL_FALSE)
        
        # Use shader program
        shader_program = self.shader_manager.get_program("particle")
        if shader_program:
            shader_program.use()
            
            # Set uniforms
            shader_program.set_uniform("viewMatrix", view_matrix)
            shader_program.set_uniform("projectionMatrix", projection_matrix)
        
            # Bind texture (use first texture for now)
            if self.particle_textures:
                gl.glActiveTexture(gl.GL_TEXTURE0)
                gl.glBindTexture(gl.GL_TEXTURE_2D, self.particle_textures[0])
                shader_program.set_uniform("particleTexture", 0)
        
        # Draw particles
        gl.glBindVertexArray(self.vao)
        gl.glDrawArraysInstanced(gl.GL_TRIANGLES, 0, 6, len(particles))
        
        # Restore state
        gl.glDepthMask(gl.GL_TRUE)
        gl.glDisable(gl.GL_BLEND)
    
    def cleanup(self):
        """Clean up GPU resources."""
        if self.vao:
            gl.glDeleteVertexArrays(1, [self.vao])
        if self.vbo_vertices:
            gl.glDeleteBuffers(1, [self.vbo_vertices])
        if self.vbo_instances:
            gl.glDeleteBuffers(1, [self.vbo_instances])
        if self.particle_textures:
            gl.glDeleteTextures(len(self.particle_textures), self.particle_textures)
        
        self._is_initialized = False


class ParticleSystem:
    """Main particle system managing multiple emitters with enhanced effects."""
    
    def __init__(self, shader_manager: ShaderManager):
        self.shader_manager = shader_manager
        self.emitters: Dict[str, BaseParticleEmitter] = {}
        self.effect_configs: Dict[str, ParticleEffect] = {}
        self.renderer = ParticleRenderer(shader_manager)
        self._is_initialized = False
    
    def initialize(self) -> bool:
        """Initialize particle system."""
        try:
            if not self.renderer.initialize():
                print("Warning: Particle renderer initialization failed")
                return False
            
            self._is_initialized = True
            return True
        except Exception as e:
            print(f"Failed to initialize particle system: {e}")
            return False
    
    def create_emitter(self, emitter_id: str, effect_config: ParticleEffect,
                      position: Tuple[float, float, float]) -> bool:
        """Create a particle emitter with configurable emission and physics."""
        try:
            emitter_config = self._create_emitter_config(effect_config, position)
            
            if effect_config.type == ParticleType.SPARKLE:
                emitter = SparkleEmitter(emitter_config)
            elif effect_config.type == ParticleType.FIRE:
                emitter = FireEmitter(emitter_config)
            elif effect_config.type == ParticleType.SMOKE:
                emitter = SmokeEmitter(emitter_config)
            else:
                print(f"Unsupported particle type: {effect_config.type}")
                return False
            
            self.emitters[emitter_id] = emitter
            self.effect_configs[emitter_id] = effect_config
            
            return True
            
        except Exception as e:
            print(f"Failed to create particle emitter '{emitter_id}': {e}")
            return False
    
    def _create_emitter_config(self, effect_config: ParticleEffect,
                              position: Tuple[float, float, float]) -> ParticleEmitterConfig:
        """Create emitter configuration with physics parameters."""
        physics = effect_config.physics_parameters
        
        # Default physics parameters for different particle types
        if effect_config.type == ParticleType.SPARKLE:
            defaults = {
                'max_particles': 150,
                'lifetime_min': 1.0,
                'lifetime_max': 3.0,
                'position_variance': (20.0, 20.0, 5.0),
                'velocity_min': (-12.0, -8.0, -5.0),
                'velocity_max': (12.0, 15.0, 5.0),
                'acceleration': (0.0, -30.0, 0.0),  # Light gravity
                'size_min': 4.0,
                'size_max': 12.0,
                'color_start': (1.0, 0.9, 0.7, 0.9),
                'color_end': (1.0, 1.0, 1.0, 0.0)
            }
        elif effect_config.type == ParticleType.FIRE:
            defaults = {
                'max_particles': 250,
                'lifetime_min': 0.8,
                'lifetime_max': 1.8,
                'position_variance': (10.0, 0.0, 10.0),
                'velocity_min': (-20.0, 40.0, -20.0),
                'velocity_max': (20.0, 100.0, 20.0),
                'acceleration': (0.0, -20.0, 0.0),  # Reduced gravity for fire
                'size_min': 8.0,
                'size_max': 20.0,
                'color_start': (1.0, 0.3, 0.0, 0.8),
                'color_end': (1.0, 1.0, 0.2, 0.0)
            }
        elif effect_config.type == ParticleType.SMOKE:
            defaults = {
                'max_particles': 200,
                'lifetime_min': 2.0,
                'lifetime_max': 5.0,
                'position_variance': (15.0, 0.0, 15.0),
                'velocity_min': (-5.0, 15.0, -5.0),
                'velocity_max': (5.0, 35.0, 5.0),
                'acceleration': (0.0, -5.0, 0.0),  # Very light gravity for smoke
                'size_min': 12.0,
                'size_max': 30.0,
                'color_start': (0.7, 0.7, 0.7, 0.6),
                'color_end': (0.4, 0.4, 0.4, 0.0)
            }
        else:
            defaults = {}
        
        # Override defaults with custom physics parameters
        for key, value in physics.items():
            if key in defaults:
                defaults[key] = value
        
        return ParticleEmitterConfig(
            emission_rate=effect_config.emission_rate,
            max_particles=defaults.get('max_particles', 100),
            lifetime_min=defaults.get('lifetime_min', 1.0),
            lifetime_max=defaults.get('lifetime_max', 2.0),
            position=position,
            position_variance=defaults.get('position_variance', (10.0, 10.0, 10.0)),
            velocity_min=defaults.get('velocity_min', (-10.0, -10.0, -10.0)),
            velocity_max=defaults.get('velocity_max', (10.0, 10.0, 10.0)),
            acceleration=defaults.get('acceleration', (0.0, -50.0, 0.0)),
            size_min=defaults.get('size_min', 4.0),
            size_max=defaults.get('size_max', 8.0),
            color_start=defaults.get('color_start', (1.0, 1.0, 1.0, 1.0)),
            color_end=defaults.get('color_end', (1.0, 1.0, 1.0, 0.0)),
            texture_path=effect_config.texture_path
        )
    
    def update_emitter_position(self, emitter_id: str, position: Tuple[float, float, float]) -> bool:
        """Update emitter position for dynamic effects."""
        emitter = self.emitters.get(emitter_id)
        if emitter:
            emitter.set_position(position)
            return True
        return False
    
    def set_emitter_active(self, emitter_id: str, active: bool) -> bool:
        """Enable or disable particle emission."""
        emitter = self.emitters.get(emitter_id)
        if emitter:
            emitter.set_active(active)
            return True
        return False
    
    def remove_emitter(self, emitter_id: str) -> bool:
        """Remove a particle emitter."""
        if emitter_id in self.emitters:
            del self.emitters[emitter_id]
            if emitter_id in self.effect_configs:
                del self.effect_configs[emitter_id]
            return True
        return False
    
    def update(self, delta_time: float) -> None:
        """Update all particle emitters and their physics simulation."""
        if not self._is_initialized:
            return
        
        for emitter in self.emitters.values():
            emitter.update(delta_time)
    
    def render(self, view_matrix: np.ndarray, projection_matrix: np.ndarray) -> None:
        """Render all particles using GPU-based rendering."""
        if not self._is_initialized:
            return
        
        # Collect all particles from all emitters
        all_particles = []
        for emitter in self.emitters.values():
            all_particles.extend(emitter.particles)
        
        # Render particles using the renderer
        if all_particles:
            self.renderer.render_particles(all_particles, view_matrix, projection_matrix)
    
    def get_emitter_particle_count(self, emitter_id: str) -> int:
        """Get particle count for a specific emitter."""
        emitter = self.emitters.get(emitter_id)
        return emitter.get_particle_count() if emitter else 0
    
    def get_total_particle_count(self) -> int:
        """Get total number of active particles across all emitters."""
        return sum(emitter.get_particle_count() for emitter in self.emitters.values())
    
    def clear_all_particles(self) -> None:
        """Clear all particles from all emitters."""
        for emitter in self.emitters.values():
            emitter.clear_particles()
    
    def cleanup(self) -> None:
        """Clean up particle system resources."""
        if self.renderer:
            self.renderer.cleanup()
        self.emitters.clear()
        self.effect_configs.clear()
        self._is_initialized = False
    
    # Convenience methods for creating specific particle effects
    
    def create_sparkle_effect(self, emitter_id: str, position: Tuple[float, float, float],
                             emission_rate: float = 50.0, lifetime: float = 2.0) -> bool:
        """Create a sparkle particle effect with texture-based rendering."""
        effect_config = ParticleEffect(
            type=ParticleType.SPARKLE,
            emission_rate=emission_rate,
            lifetime=lifetime,
            texture_path="assets/textures/sparkle.png",
            physics_parameters={
                'max_particles': 150,
                'velocity_min': (-12.0, -8.0, -5.0),
                'velocity_max': (12.0, 15.0, 5.0),
                'size_min': 4.0,
                'size_max': 12.0,
                'color_start': (1.0, 0.9, 0.7, 0.9),  # Warm sparkle color
                'color_end': (1.0, 1.0, 1.0, 0.0)
            }
        )
        
        return self.create_emitter(emitter_id, effect_config, position)
    
    def create_fire_effect(self, emitter_id: str, position: Tuple[float, float, float],
                          emission_rate: float = 100.0, lifetime: float = 1.2) -> bool:
        """Create a fire particle effect with realistic particle behavior and coloring."""
        effect_config = ParticleEffect(
            type=ParticleType.FIRE,
            emission_rate=emission_rate,
            lifetime=lifetime,
            texture_path="assets/textures/fire.png",
            physics_parameters={
                'max_particles': 250,
                'velocity_min': (-20.0, 40.0, -20.0),
                'velocity_max': (20.0, 100.0, 20.0),
                'size_min': 8.0,
                'size_max': 20.0,
                'color_start': (1.0, 0.3, 0.0, 0.8),  # Hot orange-red
                'color_end': (1.0, 1.0, 0.2, 0.0)     # Cool yellow
            }
        )
        
        return self.create_emitter(emitter_id, effect_config, position)
    
    def create_smoke_effect(self, emitter_id: str, position: Tuple[float, float, float],
                           emission_rate: float = 30.0, lifetime: float = 3.0) -> bool:
        """Create a smoke trail effect with alpha blending and wind simulation."""
        effect_config = ParticleEffect(
            type=ParticleType.SMOKE,
            emission_rate=emission_rate,
            lifetime=lifetime,
            texture_path="assets/textures/smoke.png",
            physics_parameters={
                'max_particles': 200,
                'velocity_min': (-5.0, 15.0, -5.0),
                'velocity_max': (5.0, 35.0, 5.0),
                'size_min': 12.0,
                'size_max': 30.0,
                'color_start': (0.7, 0.7, 0.7, 0.6),  # Semi-transparent gray
                'color_end': (0.4, 0.4, 0.4, 0.0)     # Fade to transparent
            }
        )
        
        return self.create_emitter(emitter_id, effect_config, position)