"""
Subtitle format parser for various subtitle formats.

Supports parsing .ass (Advanced SubStation Alpha), .srt (SubRip), and .vtt (WebVTT)
subtitle files and converting them to the internal SubtitleTrack format.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

try:
    from ..core.models import SubtitleTrack, TextElement, ValidationResult
except ImportError:
    # For direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.models import SubtitleTrack, TextElement, ValidationResult


logger = logging.getLogger(__name__)


@dataclass
class SubtitleEntry:
    """Represents a single subtitle entry with timing and text."""
    start_time: float  # seconds
    end_time: float    # seconds
    text: str
    style_overrides: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.style_overrides is None:
            self.style_overrides = {}


class SubtitleParser:
    """
    Parser for various subtitle formats with conversion to internal format.
    
    Supports:
    - .ass (Advanced SubStation Alpha) - Full styling support
    - .srt (SubRip) - Basic text with timing
    - .vtt (WebVTT) - Basic text with timing and some styling
    """
    
    def __init__(self):
        self.supported_formats = {'.ass', '.srt', '.vtt'}
    
    def parse_file(self, file_path: str) -> ValidationResult:
        """
        Parse subtitle file and return validation result with parsed data.
        
        Args:
            file_path: Path to subtitle file
            
        Returns:
            ValidationResult with parsed SubtitleTrack in metadata
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return ValidationResult(
                    is_valid=False,
                    error_message=f"File not found: {file_path}"
                )
            
            if path.suffix.lower() not in self.supported_formats:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Unsupported format: {path.suffix}"
                )
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse based on format
            if path.suffix.lower() == '.ass':
                entries = self._parse_ass(content)
            elif path.suffix.lower() == '.srt':
                entries = self._parse_srt(content)
            elif path.suffix.lower() == '.vtt':
                entries = self._parse_vtt(content)
            else:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Parser not implemented for {path.suffix}"
                )
            
            if not entries:
                return ValidationResult(
                    is_valid=False,
                    error_message="No subtitle entries found in file"
                )
            
            # Convert to SubtitleTrack
            subtitle_track = self._convert_to_subtitle_track(entries, path.stem)
            
            return ValidationResult(
                is_valid=True,
                metadata={
                    'subtitle_track': subtitle_track,
                    'entry_count': len(entries),
                    'format': path.suffix.lower(),
                    'duration': max(entry.end_time for entry in entries)
                }
            )
            
        except Exception as e:
            logger.error(f"Error parsing subtitle file {file_path}: {e}")
            return ValidationResult(
                is_valid=False,
                error_message=f"Parse error: {str(e)}"
            )
    
    def _parse_ass(self, content: str) -> List[SubtitleEntry]:
        """Parse Advanced SubStation Alpha (.ass) format."""
        entries = []
        
        # Split into sections
        sections = self._split_ass_sections(content)
        
        # Parse styles section for default styling
        styles = self._parse_ass_styles(sections.get('V4+ Styles', ''))
        
        # Parse events section
        events_section = sections.get('Events', '')
        if not events_section:
            return entries
        
        # Find dialogue lines
        dialogue_pattern = r'^Dialogue:\s*(.+)$'
        
        for line in events_section.split('\n'):
            line = line.strip()
            if not line or line.startswith(';'):
                continue
                
            match = re.match(dialogue_pattern, line, re.IGNORECASE)
            if match:
                dialogue_data = match.group(1)
                entry = self._parse_ass_dialogue_line(dialogue_data, styles)
                if entry:
                    entries.append(entry)
        
        return entries
    
    def _split_ass_sections(self, content: str) -> Dict[str, str]:
        """Split ASS content into sections."""
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Check for section header
            if line.startswith('[') and line.endswith(']'):
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                
                # Start new section
                current_section = line[1:-1]
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def _parse_ass_styles(self, styles_section: str) -> Dict[str, Dict[str, Any]]:
        """Parse ASS styles section."""
        styles = {}
        
        format_line = None
        for line in styles_section.split('\n'):
            line = line.strip()
            if not line or line.startswith(';'):
                continue
                
            if line.startswith('Format:'):
                format_line = line[7:].strip()
                continue
            
            if line.startswith('Style:') and format_line:
                style_data = line[6:].strip()
                style = self._parse_ass_style_line(style_data, format_line)
                if style and 'Name' in style:
                    styles[style['Name']] = style
        
        return styles
    
    def _parse_ass_style_line(self, style_data: str, format_line: str) -> Optional[Dict[str, Any]]:
        """Parse a single ASS style line."""
        try:
            fields = format_line.split(',')
            values = style_data.split(',')
            
            if len(fields) != len(values):
                return None
            
            style = {}
            for field, value in zip(fields, values):
                field = field.strip()
                value = value.strip()
                
                # Convert specific fields
                if field in ['Fontsize', 'Bold', 'Italic', 'Underline', 'StrikeOut']:
                    try:
                        style[field] = int(value)
                    except ValueError:
                        style[field] = 0
                elif field in ['ScaleX', 'ScaleY', 'Spacing', 'Angle']:
                    try:
                        style[field] = float(value)
                    except ValueError:
                        style[field] = 0.0
                else:
                    style[field] = value
            
            return style
            
        except Exception as e:
            logger.warning(f"Error parsing ASS style line: {e}")
            return None
    
    def _parse_ass_dialogue_line(self, dialogue_data: str, styles: Dict[str, Dict[str, Any]]) -> Optional[SubtitleEntry]:
        """Parse a single ASS dialogue line."""
        try:
            # ASS dialogue format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
            parts = dialogue_data.split(',', 9)  # Split into max 10 parts
            
            if len(parts) < 10:
                return None
            
            # Parse timing
            start_time = self._parse_ass_time(parts[1])
            end_time = self._parse_ass_time(parts[2])
            
            if start_time is None or end_time is None:
                return None
            
            # Get style name and text
            style_name = parts[3].strip()
            text = parts[9].strip()
            
            # Clean ASS formatting tags from text (basic cleanup)
            clean_text = self._clean_ass_text(text)
            
            # Get style overrides from the referenced style
            style_overrides = {}
            if style_name in styles:
                style = styles[style_name]
                style_overrides = {
                    'font_family': style.get('Fontname', 'Arial'),
                    'font_size': style.get('Fontsize', 48),
                    'bold': bool(style.get('Bold', 0)),
                    'italic': bool(style.get('Italic', 0)),
                }
                
                # Parse color (ASS uses BGR format)
                primary_color = style.get('PrimaryColour', '&Hffffff')
                color = self._parse_ass_color(primary_color)
                if color:
                    style_overrides['color'] = color
            
            return SubtitleEntry(
                start_time=start_time,
                end_time=end_time,
                text=clean_text,
                style_overrides=style_overrides
            )
            
        except Exception as e:
            logger.warning(f"Error parsing ASS dialogue line: {e}")
            return None
    
    def _parse_ass_time(self, time_str: str) -> Optional[float]:
        """Parse ASS time format (H:MM:SS.CC) to seconds."""
        try:
            time_str = time_str.strip()
            # Format: H:MM:SS.CC
            match = re.match(r'(\d+):(\d{2}):(\d{2})\.(\d{2})', time_str)
            if match:
                hours = int(match.group(1))
                minutes = int(match.group(2))
                seconds = int(match.group(3))
                centiseconds = int(match.group(4))
                
                total_seconds = hours * 3600 + minutes * 60 + seconds + centiseconds / 100.0
                return total_seconds
            
            return None
            
        except Exception:
            return None
    
    def _clean_ass_text(self, text: str) -> str:
        """Remove ASS formatting tags from text."""
        # Remove override tags like {\tag}
        text = re.sub(r'\{[^}]*\}', '', text)
        
        # Remove line breaks and normalize whitespace
        text = re.sub(r'\\[nN]', '\n', text)  # Convert \n and \N to actual newlines
        text = re.sub(r'\\h', ' ', text)      # Convert \h to space
        
        return text.strip()
    
    def _parse_ass_color(self, color_str: str) -> Optional[Tuple[float, float, float, float]]:
        """Parse ASS color format to RGBA tuple."""
        try:
            # ASS colors are in format &HAABBGGRR or &HBBGGRR
            if color_str.startswith('&H'):
                hex_color = color_str[2:]
                
                if len(hex_color) == 6:  # BBGGRR
                    b = int(hex_color[0:2], 16) / 255.0
                    g = int(hex_color[2:4], 16) / 255.0
                    r = int(hex_color[4:6], 16) / 255.0
                    return (r, g, b, 1.0)
                elif len(hex_color) == 8:  # AABBGGRR
                    a = int(hex_color[0:2], 16) / 255.0
                    b = int(hex_color[2:4], 16) / 255.0
                    g = int(hex_color[4:6], 16) / 255.0
                    r = int(hex_color[6:8], 16) / 255.0
                    return (r, g, b, a)
            
            return None
            
        except Exception:
            return None
    
    def _parse_srt(self, content: str) -> List[SubtitleEntry]:
        """Parse SubRip (.srt) format."""
        entries = []
        
        # Split into subtitle blocks
        blocks = re.split(r'\n\s*\n', content.strip())
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue
            
            try:
                # Parse timing line (line 1, 0-indexed)
                timing_line = lines[1]
                match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})', timing_line)
                
                if not match:
                    continue
                
                # Convert to seconds
                start_time = (int(match.group(1)) * 3600 + 
                             int(match.group(2)) * 60 + 
                             int(match.group(3)) + 
                             int(match.group(4)) / 1000.0)
                
                end_time = (int(match.group(5)) * 3600 + 
                           int(match.group(6)) * 60 + 
                           int(match.group(7)) + 
                           int(match.group(8)) / 1000.0)
                
                # Get text (lines 2+)
                text = '\n'.join(lines[2:])
                
                # Clean basic HTML tags
                text = re.sub(r'<[^>]+>', '', text)
                
                entries.append(SubtitleEntry(
                    start_time=start_time,
                    end_time=end_time,
                    text=text.strip()
                ))
                
            except Exception as e:
                logger.warning(f"Error parsing SRT block: {e}")
                continue
        
        return entries
    
    def _parse_vtt(self, content: str) -> List[SubtitleEntry]:
        """Parse WebVTT (.vtt) format."""
        entries = []
        
        lines = content.split('\n')
        i = 0
        
        # Skip header
        while i < len(lines) and not lines[i].strip().startswith('WEBVTT'):
            i += 1
        i += 1
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines and notes
            if not line or line.startswith('NOTE'):
                i += 1
                continue
            
            # Check if this line contains timing
            if '-->' in line:
                timing_line = line
            else:
                # Skip cue identifier and get timing from next line
                i += 1
                if i >= len(lines):
                    break
                timing_line = lines[i].strip()
            
            # Parse timing
            match = re.match(r'(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})\.(\d{3})', timing_line)
            
            if not match:
                i += 1
                continue
            
            start_time = (int(match.group(1)) * 3600 + 
                         int(match.group(2)) * 60 + 
                         int(match.group(3)) + 
                         int(match.group(4)) / 1000.0)
            
            end_time = (int(match.group(5)) * 3600 + 
                       int(match.group(6)) * 60 + 
                       int(match.group(7)) + 
                       int(match.group(8)) / 1000.0)
            
            # Collect text lines until empty line or end
            i += 1
            text_lines = []
            while i < len(lines) and lines[i].strip():
                text_lines.append(lines[i].strip())
                i += 1
            
            if text_lines:
                text = '\n'.join(text_lines)
                # Clean basic WebVTT tags
                text = re.sub(r'<[^>]+>', '', text)
                
                entries.append(SubtitleEntry(
                    start_time=start_time,
                    end_time=end_time,
                    text=text
                ))
            
            i += 1
        
        return entries
    
    def _convert_to_subtitle_track(self, entries: List[SubtitleEntry], track_name: str) -> SubtitleTrack:
        """Convert parsed subtitle entries to internal SubtitleTrack format."""
        text_elements = []
        
        for i, entry in enumerate(entries):
            # Create text element with default styling
            element = TextElement(
                content=entry.text,
                font_family=entry.style_overrides.get('font_family', 'Arial'),
                font_size=entry.style_overrides.get('font_size', 48.0),
                color=entry.style_overrides.get('color', (1.0, 1.0, 1.0, 1.0)),
                position=(0.5, 0.1),  # Default bottom center
                rotation=(0.0, 0.0, 0.0),
                effects=[]
            )
            text_elements.append(element)
        
        # Calculate track bounds
        start_time = min(entry.start_time for entry in entries) if entries else 0.0
        end_time = max(entry.end_time for entry in entries) if entries else 0.0
        
        return SubtitleTrack(
            id=f"imported_{track_name}",
            elements=text_elements,
            keyframes=[],  # No keyframes from subtitle files
            start_time=start_time,
            end_time=end_time
        )