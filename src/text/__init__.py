"""
Text rendering and subtitle handling with FreeType integration.

This module provides comprehensive text rendering capabilities including:
- Font loading and management with FreeType
- Glyph texture atlas generation
- Unicode support for multi-language text
- Advanced text layout and typography
- OpenGL-accelerated text rendering
- Subtitle format parsing (.ass, .srt, .vtt)
"""

from .font_manager import FontManager, FontAtlas, GlyphMetrics
from .text_renderer import TextRenderer, TextStyle, TextAlignment, TextMesh
from .text_layout import TextLayoutEngine, TextBlock, TextLine, LineBreak
try:
    from .subtitle_parser import SubtitleParser, SubtitleEntry
except ImportError:
    # Handle import issues during testing
    SubtitleParser = None
    SubtitleEntry = None

__all__ = [
    # Font management
    'FontManager',
    'FontAtlas', 
    'GlyphMetrics',
    
    # Text rendering
    'TextRenderer',
    'TextStyle',
    'TextAlignment',
    'TextMesh',
    
    # Text layout
    'TextLayoutEngine',
    'TextBlock',
    'TextLine',
    'LineBreak',
    
    # Subtitle parsing
    'SubtitleParser',
    'SubtitleEntry'
]