"""
Advanced text layout engine for multi-line text and complex formatting.

This module provides text layout capabilities including line breaking,
alignment, and advanced typography features for karaoke subtitle display.
"""

import logging
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import re

from .font_manager import FontManager, GlyphMetrics
from .text_renderer import TextStyle, TextAlignment


logger = logging.getLogger(__name__)


@dataclass
class LineBreak:
    """Information about a line break position."""
    position: int  # Character position in text
    width: float   # Width up to this position
    is_forced: bool = False  # True for explicit line breaks (\n)


@dataclass
class TextLine:
    """Represents a single line of text with layout information."""
    text: str
    width: float
    height: float
    baseline_y: float
    start_index: int  # Start character index in original text
    end_index: int    # End character index in original text


@dataclass
class TextBlock:
    """Complete text layout with multiple lines."""
    lines: List[TextLine]
    total_width: float
    total_height: float
    baseline_offset: float


class TextLayoutEngine:
    """
    Advanced text layout engine with support for multi-line text,
    word wrapping, and complex typography features.
    """
    
    def __init__(self, font_manager: FontManager):
        self.font_manager = font_manager
        
        # Layout parameters
        self._word_break_chars = set(' \t\n\r-–—')
        self._whitespace_chars = set(' \t')
        
    def layout_text(self, text: str, style: TextStyle, max_width: Optional[float] = None,
                   max_height: Optional[float] = None) -> TextBlock:
        """
        Layout text with word wrapping and alignment.
        
        Args:
            text: Text to layout
            style: Text styling parameters
            max_width: Maximum line width (None for no wrapping)
            max_height: Maximum total height (None for no limit)
            
        Returns:
            TextBlock with layout information
        """
        if not text:
            return TextBlock([], 0.0, 0.0, 0.0)
            
        # Ensure font is loaded and glyphs are rendered
        self.font_manager.render_text_glyphs(style.font_path, style.font_size, text)
        
        # Get font atlas for measurements
        atlas = self.font_manager.get_font_atlas(style.font_path, style.font_size)
        if not atlas:
            logger.error(f"Font atlas not found: {style.font_path}")
            return TextBlock([], 0.0, 0.0, 0.0)
            
        # Break text into lines
        lines = self._break_into_lines(text, style, atlas, max_width)
        
        # Apply height constraints if specified
        if max_height is not None:
            lines = self._apply_height_constraint(lines, style, max_height)
            
        # Calculate line positions and alignment
        positioned_lines = self._position_lines(lines, style, max_width)
        
        # Calculate total dimensions
        total_width = max((line.width for line in positioned_lines), default=0.0)
        total_height = self._calculate_total_height(positioned_lines, style)
        
        # Calculate baseline offset (distance from top to first baseline)
        baseline_offset = style.font_size * 0.8 if positioned_lines else 0.0
        
        return TextBlock(positioned_lines, total_width, total_height, baseline_offset)
        
    def _break_into_lines(self, text: str, style: TextStyle, atlas, max_width: Optional[float]) -> List[TextLine]:
        """Break text into lines based on width constraints and line breaks."""
        lines = []
        
        # Split by explicit line breaks first
        paragraphs = text.split('\n')
        
        for para_index, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                # Empty line
                lines.append(TextLine("", 0.0, style.font_size, 0.0, 0, 0))
                continue
                
            if max_width is None:
                # No wrapping - single line per paragraph
                width = self._measure_text_width(paragraph, style, atlas)
                lines.append(TextLine(
                    paragraph, width, style.font_size, 0.0,
                    0, len(paragraph)
                ))
            else:
                # Word wrapping
                para_lines = self._wrap_paragraph(paragraph, style, atlas, max_width)
                lines.extend(para_lines)
                
        return lines
        
    def _wrap_paragraph(self, paragraph: str, style: TextStyle, atlas, max_width: float) -> List[TextLine]:
        """Wrap a paragraph into multiple lines based on width constraint."""
        lines = []
        words = self._split_into_words(paragraph)
        
        current_line = ""
        current_width = 0.0
        line_start_index = 0
        
        for word_info in words:
            word, is_whitespace = word_info
            word_width = self._measure_text_width(word, style, atlas)
            
            # Check if adding this word would exceed max width
            test_line = current_line + word
            test_width = self._measure_text_width(test_line, style, atlas)
            
            if test_width > max_width and current_line:
                # Finish current line
                lines.append(TextLine(
                    current_line.rstrip(), current_width, style.font_size, 0.0,
                    line_start_index, line_start_index + len(current_line)
                ))
                
                # Start new line
                current_line = word.lstrip() if not is_whitespace else ""
                current_width = self._measure_text_width(current_line, style, atlas)
                line_start_index += len(current_line)
            else:
                # Add word to current line
                current_line += word
                current_width = test_width
                
        # Add final line if not empty
        if current_line.strip():
            lines.append(TextLine(
                current_line.rstrip(), current_width, style.font_size, 0.0,
                line_start_index, line_start_index + len(current_line)
            ))
            
        return lines
        
    def _split_into_words(self, text: str) -> List[Tuple[str, bool]]:
        """Split text into words and whitespace segments."""
        words = []
        current_word = ""
        is_whitespace = False
        
        for char in text:
            char_is_whitespace = char in self._whitespace_chars
            
            if char_is_whitespace != is_whitespace:
                # Transition between word and whitespace
                if current_word:
                    words.append((current_word, is_whitespace))
                current_word = char
                is_whitespace = char_is_whitespace
            else:
                current_word += char
                
        # Add final word
        if current_word:
            words.append((current_word, is_whitespace))
            
        return words
        
    def _measure_text_width(self, text: str, style: TextStyle, atlas) -> float:
        """Measure the width of text in pixels."""
        if not text:
            return 0.0
            
        total_width = 0.0
        
        for char in text:
            codepoint = ord(char)
            glyph = atlas.get_glyph(codepoint)
            
            if glyph:
                total_width += glyph.advance + style.character_spacing
                
        return total_width
        
    def _apply_height_constraint(self, lines: List[TextLine], style: TextStyle, max_height: float) -> List[TextLine]:
        """Apply height constraint by truncating lines if necessary."""
        line_height = style.font_size * style.line_spacing
        max_lines = int(max_height / line_height)
        
        if len(lines) <= max_lines:
            return lines
            
        # Truncate and add ellipsis to last visible line
        truncated_lines = lines[:max_lines]
        
        if max_lines > 0:
            last_line = truncated_lines[-1]
            # Try to add ellipsis if there's space
            ellipsis_text = last_line.text + "..."
            # Note: In a full implementation, we'd check if ellipsis fits
            truncated_lines[-1] = TextLine(
                ellipsis_text, last_line.width, last_line.height,
                last_line.baseline_y, last_line.start_index, last_line.end_index
            )
            
        return truncated_lines
        
    def _position_lines(self, lines: List[TextLine], style: TextStyle, max_width: Optional[float]) -> List[TextLine]:
        """Position lines based on alignment settings."""
        positioned_lines = []
        current_y = 0.0
        
        for line in lines:
            # Calculate Y position
            baseline_y = current_y + style.font_size * 0.8  # Approximate baseline offset
            
            # Apply alignment if max_width is specified
            if max_width is not None and style.alignment != TextAlignment.LEFT:
                # Alignment adjustments would be applied during rendering
                # For now, we just store the line as-is
                pass
                
            positioned_line = TextLine(
                line.text, line.width, line.height, baseline_y,
                line.start_index, line.end_index
            )
            positioned_lines.append(positioned_line)
            
            # Move to next line position
            current_y += style.font_size * style.line_spacing
            
        return positioned_lines
        
    def _calculate_total_height(self, lines: List[TextLine], style: TextStyle) -> float:
        """Calculate total height of text block."""
        if not lines:
            return 0.0
            
        # Height is number of lines * line spacing, minus one line spacing, plus one font size
        return (len(lines) - 1) * style.font_size * style.line_spacing + style.font_size
        
    def get_character_position(self, text_block: TextBlock, char_index: int, style: TextStyle) -> Optional[Tuple[float, float]]:
        """
        Get the position of a character within a text block.
        
        Args:
            text_block: Layout text block
            char_index: Character index in original text
            style: Text style parameters
            
        Returns:
            (x, y) position of character or None if not found
        """
        # Find which line contains this character
        for line in text_block.lines:
            if line.start_index <= char_index < line.end_index:
                # Character is in this line
                line_char_index = char_index - line.start_index
                
                # Measure width up to this character
                text_before = line.text[:line_char_index]
                atlas = self.font_manager.get_font_atlas(style.font_path, style.font_size)
                
                if atlas:
                    x = self._measure_text_width(text_before, style, atlas)
                    y = line.baseline_y
                    return (x, y)
                    
        return None
        
    def find_character_at_position(self, text_block: TextBlock, x: float, y: float, style: TextStyle) -> Optional[int]:
        """
        Find the character index at a given position.
        
        Args:
            text_block: Layout text block
            x: X coordinate
            y: Y coordinate
            style: Text style parameters
            
        Returns:
            Character index or None if position is outside text
        """
        # Find the line at this Y position
        target_line = None
        for line in text_block.lines:
            line_top = line.baseline_y - style.font_size * 0.8
            line_bottom = line.baseline_y + style.font_size * 0.2
            
            if line_top <= y <= line_bottom:
                target_line = line
                break
                
        if not target_line:
            return None
            
        # Find character position within the line
        atlas = self.font_manager.get_font_atlas(style.font_path, style.font_size)
        if not atlas:
            return None
            
        current_x = 0.0
        for i, char in enumerate(target_line.text):
            codepoint = ord(char)
            glyph = atlas.get_glyph(codepoint)
            
            if glyph:
                char_width = glyph.advance + style.character_spacing
                
                if current_x + char_width / 2 > x:
                    return target_line.start_index + i
                    
                current_x += char_width
                
        # Position is after the last character
        return target_line.end_index
        
    def get_line_metrics(self, text_block: TextBlock) -> Dict[str, Any]:
        """Get detailed metrics about the text layout."""
        if not text_block.lines:
            return {
                "line_count": 0,
                "average_line_width": 0.0,
                "max_line_width": 0.0,
                "total_height": 0.0
            }
            
        line_widths = [line.width for line in text_block.lines]
        
        return {
            "line_count": len(text_block.lines),
            "average_line_width": sum(line_widths) / len(line_widths),
            "max_line_width": max(line_widths),
            "total_height": text_block.total_height,
            "lines": [
                {
                    "text": line.text,
                    "width": line.width,
                    "height": line.height,
                    "baseline_y": line.baseline_y
                }
                for line in text_block.lines
            ]
        }