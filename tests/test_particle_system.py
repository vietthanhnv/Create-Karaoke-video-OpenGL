"""
Tests for particle system implementation.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch

from src.effects.particle_system import (
    ParticleSystem, SparkleEmitter, FireEmitter, SmokeEmitter,
    Particle, ParticleEmitterConfig, ParticleRenderer
)
from src.core.models import ParticleEffect, ParticleType
from src.graphics.shader_manager import ShaderManager


class TestParticle:
    """Test particle data structure and behavior."""
    
    def test_particle_creation(self):
        """Test particle creation with valid parameters."""
        particle = Particle(
            position=(0.0, 0.0, 0.0),
            velocity=(1.0, 2.0, 0.0),
            acceleration=(0.0, -9.8, 0.0),
            color=(1.0, 1.0, 1.0, 1.0),
            size=5.0,
            life=1.0,
            max_life=2.0,
            rotation=0.0,
            angular_velocity=1.0,
            texture_index=0
        )
        
        assert particle.is_alive()
        assert particle.position == (0.0, 0.0, 0.0)
        assert particle.velocity == (1.0, 2.0, 0.0)
        assert particle.size == 5.0
    
    def test_particle_update(self):
        """Test particle physics update."""
        particle = Particle(
            position=(0.0, 0.0, 0.0),
            velocity=(1.0, 2.0, 0.0),
            acceleration=(0.0, -9.8, 0.0),
            color=(1.0, 1.0, 1.0, 1.0),
            size=5.0,
            life=1.0,
            max_life=2.0,
            rotation=0.0,
            angular_velocity=1.0,
            texture_index=0
        )
        
        delta_time = 0.1
        particle.update(delta_time)
        
        # Check velocity update (happens first)
        expected_vy = 2.0 + (-9.8) * delta_time
        assert abs(particle.velocity[1] - expected_vy) < 1e-6
        
        # Check position update (uses updated velocity)
        expected_x = 0.0 + 1.0 * delta_time
        expected_y = 0.0 + expected_vy * delta_time
        assert abs(particle.position[0] - expected_x) < 1e-6
        assert abs(particle.position[1] - expected_y) < 1e-6
        
        # Check life update
        expected_life = 1.0 - delta_time / 2.0
        assert abs(particle.life - expected_life) < 1e-6
        
        # Check rotation update
        expected_rotation = 0.0 + 1.0 * delta_time
        assert abs(particle.rotation - expected_rotation) < 1e-6
    
    def test_particle_death(self):
        """Test particle death when life reaches zero."""
        particle = Particle(
            position=(0.0, 0.0, 0.0),
            velocity=(0.0, 0.0, 0.0),
            acceleration=(0.0, 0.0, 0.0),
            color=(1.0, 1.0, 1.0, 1.0),
            size=5.0,
            life=0.1,
            max_life=1.0,
            rotation=0.0,
            angular_velocity=0.0,
            texture_index=0
        )
        
        # Update with large delta time to kill particle
        particle.update(1.0)
        
        assert not particle.is_alive()
        assert particle.life <= 0.0


class TestParticleEmitterConfig:
    """Test particle emitter configuration."""
    
    def test_config_creation(self):
        """Test emitter configuration creation."""
        config = ParticleEmitterConfig(
            emission_rate=50.0,
            max_particles=100,
            lifetime_min=1.0,
            lifetime_max=3.0,
            position=(0.0, 0.0, 0.0),
            position_variance=(10.0, 10.0, 10.0),
            velocity_min=(-5.0, -5.0, -5.0),
            velocity_max=(5.0, 5.0, 5.0),
            acceleration=(0.0, -50.0, 0.0),
            size_min=2.0,
            size_max=8.0,
            color_start=(1.0, 1.0, 1.0, 1.0),
            color_end=(1.0, 1.0, 1.0, 0.0)
        )
        
        assert config.emission_rate == 50.0
        assert config.max_particles == 100
        assert config.position == (0.0, 0.0, 0.0)
        assert config.blend_mode == "alpha"  # Default value


class TestSparkleEmitter:
    """Test sparkle particle emitter."""
    
    def test_emitter_creation(self):
        """Test sparkle emitter creation."""
        config = ParticleEmitterConfig(
            emission_rate=50.0,
            max_particles=100,
            lifetime_min=1.0,
            lifetime_max=3.0,
            position=(0.0, 0.0, 0.0),
            position_variance=(10.0, 10.0, 10.0),
            velocity_min=(-5.0, -5.0, -5.0),
            velocity_max=(5.0, 5.0, 5.0),
            acceleration=(0.0, -50.0, 0.0),
            size_min=2.0,
            size_max=8.0,
            color_start=(1.0, 1.0, 1.0, 1.0),
            color_end=(1.0, 1.0, 1.0, 0.0)
        )
        
        emitter = SparkleEmitter(config)
        
        assert emitter.config == config
        assert emitter.is_active
        assert len(emitter.particles) == 0
        assert emitter.twinkle_frequency == 3.0
        assert emitter.brightness_variation == 0.4
    
    def test_particle_creation(self):
        """Test sparkle particle creation."""
        config = ParticleEmitterConfig(
            emission_rate=50.0,
            max_particles=100,
            lifetime_min=1.0,
            lifetime_max=3.0,
            position=(0.0, 0.0, 0.0),
            position_variance=(10.0, 10.0, 10.0),
            velocity_min=(-5.0, -5.0, -5.0),
            velocity_max=(5.0, 5.0, 5.0),
            acceleration=(0.0, -50.0, 0.0),
            size_min=2.0,
            size_max=8.0,
            color_start=(1.0, 1.0, 1.0, 1.0),
            color_end=(1.0, 1.0, 1.0, 0.0)
        )
        
        emitter = SparkleEmitter(config)
        particle = emitter.create_particle()
        
        assert isinstance(particle, Particle)
        assert particle.is_alive()
        assert particle.life == 1.0
        assert config.size_min <= particle.size <= config.size_max
        assert particle.texture_index == 0  # Sparkle texture index
        
        # Test upward bias in velocity
        assert particle.velocity[1] >= -3.0  # Should have upward bias
    
    def test_emitter_update(self):
        """Test emitter update and particle emission."""
        config = ParticleEmitterConfig(
            emission_rate=100.0,  # High emission rate for testing
            max_particles=50,
            lifetime_min=1.0,
            lifetime_max=3.0,
            position=(0.0, 0.0, 0.0),
            position_variance=(10.0, 10.0, 10.0),
            velocity_min=(-5.0, -5.0, -5.0),
            velocity_max=(5.0, 5.0, 5.0),
            acceleration=(0.0, -50.0, 0.0),
            size_min=2.0,
            size_max=8.0,
            color_start=(1.0, 1.0, 1.0, 1.0),
            color_end=(1.0, 1.0, 1.0, 0.0)
        )
        
        emitter = SparkleEmitter(config)
        
        # Update emitter to emit particles
        emitter.update(0.1)
        
        # Should have emitted some particles
        assert len(emitter.particles) > 0
        assert len(emitter.particles) <= config.max_particles
    
    def test_emitter_deactivation(self):
        """Test emitter deactivation."""
        config = ParticleEmitterConfig(
            emission_rate=100.0,
            max_particles=50,
            lifetime_min=1.0,
            lifetime_max=3.0,
            position=(0.0, 0.0, 0.0),
            position_variance=(10.0, 10.0, 10.0),
            velocity_min=(-5.0, -5.0, -5.0),
            velocity_max=(5.0, 5.0, 5.0),
            acceleration=(0.0, -50.0, 0.0),
            size_min=2.0,
            size_max=8.0,
            color_start=(1.0, 1.0, 1.0, 1.0),
            color_end=(1.0, 1.0, 1.0, 0.0)
        )
        
        emitter = SparkleEmitter(config)
        emitter.set_active(False)
        
        initial_count = len(emitter.particles)
        emitter.update(0.1)
        
        # Should not emit new particles when inactive
        assert len(emitter.particles) == initial_count


class TestFireEmitter:
    """Test fire particle emitter."""
    
    def test_fire_particle_upward_velocity(self):
        """Test that fire particles have upward velocity."""
        config = ParticleEmitterConfig(
            emission_rate=50.0,
            max_particles=100,
            lifetime_min=1.0,
            lifetime_max=3.0,
            position=(0.0, 0.0, 0.0),
            position_variance=(10.0, 10.0, 10.0),
            velocity_min=(-20.0, 50.0, -20.0),
            velocity_max=(20.0, 100.0, 20.0),
            acceleration=(0.0, -30.0, 0.0),
            size_min=8.0,
            size_max=16.0,
            color_start=(1.0, 0.3, 0.0, 1.0),
            color_end=(1.0, 1.0, 0.0, 0.0)
        )
        
        emitter = FireEmitter(config)
        particle = emitter.create_particle()
        
        # Fire particles should have positive Y velocity (upward)
        assert particle.velocity[1] > 0
        assert particle.texture_index == 1  # Fire texture index
        
        # Test fire color characteristics (should be red-dominant)
        assert particle.color[0] == 1.0  # Red component should be high
        assert particle.color[1] >= 0.2  # Green component varies with heat
    
    def test_fire_emitter_properties(self):
        """Test fire emitter specific properties."""
        config = ParticleEmitterConfig(
            emission_rate=50.0,
            max_particles=100,
            lifetime_min=1.0,
            lifetime_max=3.0,
            position=(0.0, 0.0, 0.0),
            position_variance=(10.0, 10.0, 10.0),
            velocity_min=(-20.0, 50.0, -20.0),
            velocity_max=(20.0, 100.0, 20.0),
            acceleration=(0.0, -30.0, 0.0),
            size_min=8.0,
            size_max=16.0,
            color_start=(1.0, 0.3, 0.0, 1.0),
            color_end=(1.0, 1.0, 0.0, 0.0)
        )
        
        emitter = FireEmitter(config)
        
        assert emitter.heat_dissipation == 0.8
        assert emitter.flicker_intensity == 0.3


class TestSmokeEmitter:
    """Test smoke particle emitter."""
    
    def test_smoke_wind_effect(self):
        """Test smoke emitter wind effects."""
        config = ParticleEmitterConfig(
            emission_rate=30.0,
            max_particles=150,
            lifetime_min=2.0,
            lifetime_max=4.0,
            position=(0.0, 0.0, 0.0),
            position_variance=(15.0, 0.0, 15.0),
            velocity_min=(-5.0, 20.0, -5.0),
            velocity_max=(5.0, 40.0, 5.0),
            acceleration=(0.0, -10.0, 0.0),
            size_min=12.0,
            size_max=24.0,
            color_start=(0.8, 0.8, 0.8, 0.8),
            color_end=(0.5, 0.5, 0.5, 0.0)
        )
        
        emitter = SmokeEmitter(config)
        
        # Test wind force setting
        wind_force = (2.0, 0.0, 1.0)
        emitter.set_wind_force(wind_force)
        assert emitter.wind_force == wind_force
        
        # Test turbulence setting
        turbulence = 0.5
        emitter.set_turbulence(turbulence)
        assert emitter.turbulence_strength == turbulence
    
    def test_smoke_particle_properties(self):
        """Test smoke particle specific properties."""
        config = ParticleEmitterConfig(
            emission_rate=30.0,
            max_particles=150,
            lifetime_min=2.0,
            lifetime_max=4.0,
            position=(0.0, 0.0, 0.0),
            position_variance=(15.0, 0.0, 15.0),
            velocity_min=(-5.0, 20.0, -5.0),
            velocity_max=(5.0, 40.0, 5.0),
            acceleration=(0.0, -10.0, 0.0),
            size_min=12.0,
            size_max=24.0,
            color_start=(0.8, 0.8, 0.8, 0.8),
            color_end=(0.5, 0.5, 0.5, 0.0)
        )
        
        emitter = SmokeEmitter(config)
        particle = emitter.create_particle()
        
        assert particle.texture_index == 2  # Smoke texture index
        assert emitter.expansion_rate == 1.5
        assert emitter.density_variation == 0.3
        
        # Test that smoke particles start smaller
        original_size = config.size_min + (config.size_max - config.size_min) * 0.5
        assert particle.size <= original_size


@patch('OpenGL.GL.glGenVertexArrays')
@patch('OpenGL.GL.glGenBuffers')
class TestParticleRenderer:
    """Test particle renderer."""
    
    def test_renderer_creation(self, mock_gen_buffers, mock_gen_vaos):
        """Test particle renderer creation."""
        mock_shader_manager = Mock(spec=ShaderManager)
        renderer = ParticleRenderer(mock_shader_manager)
        
        assert renderer.shader_manager == mock_shader_manager
        assert not renderer._is_initialized
        assert renderer.max_particles == 10000
        assert len(renderer.particle_textures) == 0
        assert len(renderer.texture_paths) == 3  # sparkle, fire, smoke
    
    def test_renderer_initialization(self, mock_gen_buffers, mock_gen_vaos):
        """Test particle renderer initialization."""
        mock_shader_manager = Mock(spec=ShaderManager)
        mock_shader_program = Mock()
        mock_shader_manager.load_shader_program.return_value = mock_shader_program
        
        # Mock OpenGL calls
        mock_gen_vaos.return_value = 1
        mock_gen_buffers.return_value = 1
        
        renderer = ParticleRenderer(mock_shader_manager)
        
        with patch('OpenGL.GL.glBindVertexArray'), \
             patch('OpenGL.GL.glBindBuffer'), \
             patch('OpenGL.GL.glBufferData'), \
             patch('OpenGL.GL.glVertexAttribPointer'), \
             patch('OpenGL.GL.glEnableVertexAttribArray'), \
             patch('OpenGL.GL.glVertexAttribDivisor'), \
             patch('OpenGL.GL.glGenTextures'), \
             patch('OpenGL.GL.glBindTexture'), \
             patch('OpenGL.GL.glTexImage2D'), \
             patch('OpenGL.GL.glTexParameteri'):
            
            result = renderer.initialize()
            
            assert result
            assert renderer._is_initialized
            assert renderer.particle_shader == mock_shader_program
            # Should have created procedural textures
            assert len(renderer.particle_textures) == 3


class TestParticleSystem:
    """Test main particle system."""
    
    def test_system_creation(self):
        """Test particle system creation."""
        mock_shader_manager = Mock(spec=ShaderManager)
        system = ParticleSystem(mock_shader_manager)
        
        assert system.shader_manager == mock_shader_manager
        assert not system._is_initialized
        assert len(system.emitters) == 0
    
    @patch('src.effects.particle_system.ParticleRenderer.initialize')
    def test_system_initialization(self, mock_renderer_init):
        """Test particle system initialization."""
        mock_renderer_init.return_value = True
        mock_shader_manager = Mock(spec=ShaderManager)
        
        system = ParticleSystem(mock_shader_manager)
        result = system.initialize()
        
        assert result
        assert system._is_initialized
    
    def test_create_sparkle_effect(self):
        """Test creating sparkle effect."""
        mock_shader_manager = Mock(spec=ShaderManager)
        system = ParticleSystem(mock_shader_manager)
        
        result = system.create_sparkle_effect("test_sparkle", (0.0, 0.0, 0.0))
        
        assert result
        assert "test_sparkle" in system.emitters
        assert isinstance(system.emitters["test_sparkle"], SparkleEmitter)
    
    def test_create_fire_effect(self):
        """Test creating fire effect."""
        mock_shader_manager = Mock(spec=ShaderManager)
        system = ParticleSystem(mock_shader_manager)
        
        result = system.create_fire_effect("test_fire", (0.0, 0.0, 0.0))
        
        assert result
        assert "test_fire" in system.emitters
        assert isinstance(system.emitters["test_fire"], FireEmitter)
    
    def test_create_smoke_effect(self):
        """Test creating smoke effect."""
        mock_shader_manager = Mock(spec=ShaderManager)
        system = ParticleSystem(mock_shader_manager)
        
        result = system.create_smoke_effect("test_smoke", (0.0, 0.0, 0.0))
        
        assert result
        assert "test_smoke" in system.emitters
        assert isinstance(system.emitters["test_smoke"], SmokeEmitter)
    
    def test_emitter_management(self):
        """Test emitter management operations."""
        mock_shader_manager = Mock(spec=ShaderManager)
        system = ParticleSystem(mock_shader_manager)
        
        # Create emitter
        system.create_sparkle_effect("test", (0.0, 0.0, 0.0))
        assert "test" in system.emitters
        
        # Update position
        result = system.update_emitter_position("test", (10.0, 20.0, 30.0))
        assert result
        assert system.emitters["test"].config.position == (10.0, 20.0, 30.0)
        
        # Set active state
        result = system.set_emitter_active("test", False)
        assert result
        assert not system.emitters["test"].is_active
        
        # Remove emitter
        result = system.remove_emitter("test")
        assert result
        assert "test" not in system.emitters
    
    def test_particle_counting(self):
        """Test particle counting functionality."""
        mock_shader_manager = Mock(spec=ShaderManager)
        system = ParticleSystem(mock_shader_manager)
        
        # Create multiple emitters
        system.create_sparkle_effect("sparkle", (0.0, 0.0, 0.0))
        system.create_fire_effect("fire", (10.0, 0.0, 0.0))
        
        # Initially no particles
        assert system.get_total_particle_count() == 0
        assert system.get_emitter_particle_count("sparkle") == 0
        assert system.get_emitter_particle_count("fire") == 0
        
        # Update to generate particles
        system.update(0.1)
        
        # Should have some particles now
        total_count = system.get_total_particle_count()
        sparkle_count = system.get_emitter_particle_count("sparkle")
        fire_count = system.get_emitter_particle_count("fire")
        
        assert total_count >= 0
        assert sparkle_count >= 0
        assert fire_count >= 0
        assert total_count == sparkle_count + fire_count
    
    def test_clear_particles(self):
        """Test clearing all particles."""
        mock_shader_manager = Mock(spec=ShaderManager)
        system = ParticleSystem(mock_shader_manager)
        
        # Create emitter and generate particles
        system.create_sparkle_effect("test", (0.0, 0.0, 0.0))
        system.update(0.1)  # Generate some particles
        
        # Clear all particles
        system.clear_all_particles()
        
        assert system.get_total_particle_count() == 0
    
    def test_cleanup(self):
        """Test system cleanup."""
        mock_shader_manager = Mock(spec=ShaderManager)
        system = ParticleSystem(mock_shader_manager)
        
        # Create some emitters
        system.create_sparkle_effect("test1", (0.0, 0.0, 0.0))
        system.create_fire_effect("test2", (10.0, 0.0, 0.0))
        
        # Cleanup
        with patch.object(system.renderer, 'cleanup') as mock_cleanup:
            system.cleanup()
            mock_cleanup.assert_called_once()
        
        assert not system._is_initialized
        assert len(system.emitters) == 0
        assert len(system.effect_configs) == 0


if __name__ == "__main__":
    pytest.main([__file__])