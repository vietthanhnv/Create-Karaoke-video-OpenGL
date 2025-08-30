"""
Effects system for text animations and visual effects.
"""

from .animation_effects import (
    AnimationEffectProcessor,
    FadeEffect,
    SlideEffect,
    TypewriterEffect,
    BounceEffect
)

from .visual_effects import (
    VisualEffectProcessor,
    GlowEffect,
    OutlineEffect,
    ShadowEffect,
    GradientEffect,
    GradientStop
)

from .transform_3d import (
    Transform3D,
    Transform3DParams,
    CameraAnimation,
    CameraMovement,
    ProjectionType
)

# Particle system imports temporarily disabled
# from .particle_system import (
#     ParticleSystem,
#     BaseParticleEmitter,
#     SparkleEmitter,
#     FireEmitter,
#     SmokeEmitter,
#     ParticleRenderer,
#     Particle,
#     ParticleEmitterConfig
# )

__all__ = [
    'AnimationEffectProcessor',
    'FadeEffect',
    'SlideEffect', 
    'TypewriterEffect',
    'BounceEffect',
    'VisualEffectProcessor',
    'GlowEffect',
    'OutlineEffect',
    'ShadowEffect',
    'GradientEffect',
    'GradientStop',
    'Transform3D',
    'Transform3DParams',
    'CameraAnimation',
    'CameraMovement',
    'ProjectionType',
    # Particle system exports temporarily disabled
    # 'ParticleSystem',
    # 'BaseParticleEmitter',
    # 'SparkleEmitter',
    # 'FireEmitter',
    # 'SmokeEmitter',
    # 'ParticleRenderer',
    # 'Particle',
    # 'ParticleEmitterConfig'
]