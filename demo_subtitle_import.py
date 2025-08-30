#!/usr/bin/env python3
"""
Demo: Subtitle Import System

Demonstrates the subtitle import functionality for .ass, .srt, and .vtt files.
Creates sample subtitle files and tests the parsing system.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from text.subtitle_parser import SubtitleParser


def create_sample_ass_file():
    """Create a sample .ass file for testing."""
    ass_content = """[Script Info]
Title: Sample Karaoke
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,48,&Hffffff,&Hffffff,&H0,&H0,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1
Style: Karaoke,Arial,52,&H00ffff,&Hffffff,&H0,&H0,1,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:04.00,Karaoke,,0,0,0,,Hello world, this is karaoke!
Dialogue: 0,0:00:05.00,0:00:08.00,Default,,0,0,0,,Welcome to the subtitle system
Dialogue: 0,0:00:10.00,0:00:13.00,Karaoke,,0,0,0,,{\\c&HFF0000&}Red text {\\c&H00FF00&}Green text
Dialogue: 0,0:00:15.00,0:00:18.00,Default,,0,0,0,,Line one\\NLine two with break
"""
    
    with open('sample.ass', 'w', encoding='utf-8') as f:
        f.write(ass_content)
    
    return 'sample.ass'


def create_sample_srt_file():
    """Create a sample .srt file for testing."""
    srt_content = """1
00:00:01,000 --> 00:00:04,000
Hello world, this is karaoke!

2
00:00:05,000 --> 00:00:08,000
Welcome to the subtitle system

3
00:00:10,000 --> 00:00:13,000
<i>Italic text</i> and <b>bold text</b>

4
00:00:15,000 --> 00:00:18,000
Line one
Line two with break
"""
    
    with open('sample.srt', 'w', encoding='utf-8') as f:
        f.write(srt_content)
    
    return 'sample.srt'


def create_sample_vtt_file():
    """Create a sample .vtt file for testing."""
    vtt_content = """WEBVTT

00:01.000 --> 00:04.000
Hello world, this is karaoke!

00:05.000 --> 00:08.000
Welcome to the subtitle system

00:10.000 --> 00:13.000
<i>Italic text</i> and <b>bold text</b>

00:15.000 --> 00:18.000
Line one
Line two with break
"""
    
    with open('sample.vtt', 'w', encoding='utf-8') as f:
        f.write(vtt_content)
    
    return 'sample.vtt'


def test_subtitle_parser():
    """Test the subtitle parser with different formats."""
    print("Subtitle Import System Demo")
    print("=" * 50)
    
    parser = SubtitleParser()
    
    # Create sample files
    print("Creating sample subtitle files...")
    ass_file = create_sample_ass_file()
    srt_file = create_sample_srt_file()
    vtt_file = create_sample_vtt_file()
    
    files_to_test = [
        (ass_file, "Advanced SubStation Alpha"),
        (srt_file, "SubRip"),
        (vtt_file, "WebVTT")
    ]
    
    for file_path, format_name in files_to_test:
        print(f"\n--- Testing {format_name} ({file_path}) ---")
        
        result = parser.parse_file(file_path)
        
        if result.is_valid:
            print("✓ Parse successful!")
            
            metadata = result.metadata
            subtitle_track = metadata['subtitle_track']
            
            print(f"  Entries: {metadata['entry_count']}")
            print(f"  Duration: {metadata['duration']:.1f} seconds")
            print(f"  Track ID: {subtitle_track.id}")
            print(f"  Elements: {len(subtitle_track.elements)}")
            
            # Show first few entries
            print("  First entries:")
            for i, element in enumerate(subtitle_track.elements[:3]):
                print(f"    {i+1}. \"{element.content[:50]}{'...' if len(element.content) > 50 else ''}\"")
                print(f"       Font: {element.font_family}, Size: {element.font_size}")
                print(f"       Color: {element.color}")
            
            if result.warnings:
                print("  Warnings:")
                for warning in result.warnings:
                    print(f"    - {warning}")
        else:
            print("✗ Parse failed!")
            print(f"  Error: {result.error_message}")
    
    # Test invalid file
    print(f"\n--- Testing Invalid File ---")
    result = parser.parse_file("nonexistent.ass")
    if not result.is_valid:
        print("✓ Correctly rejected nonexistent file")
        print(f"  Error: {result.error_message}")
    
    # Cleanup
    print(f"\nCleaning up sample files...")
    for file_path, _ in files_to_test:
        try:
            os.remove(file_path)
            print(f"  Removed {file_path}")
        except OSError:
            pass


def test_ass_advanced_features():
    """Test advanced ASS features like styling and formatting."""
    print(f"\n--- Testing Advanced ASS Features ---")
    
    # Create ASS with advanced styling
    advanced_ass = """[Script Info]
Title: Advanced ASS Test

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,Arial,48,&Hffffff,&Hffffff,&H0,&H0,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1
Style: Singer1,Times New Roman,52,&H00ffff,&Hffffff,&H0,&H0,1,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1
Style: Singer2,Comic Sans MS,50,&Hff00ff,&Hffffff,&H0,&H0,0,1,0,0,100,100,0,0,1,2,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.50,0:00:04.20,Singer1,,0,0,0,,{\\k25}Hel{\\k30}lo {\\k40}world
Dialogue: 0,0:00:05.00,0:00:07.80,Singer2,,0,0,0,,{\\c&HFF0000&}Red {\\c&H00FF00&}Green {\\c&H0000FF&}Blue
Dialogue: 0,0:00:09.00,0:00:12.00,Main,,0,0,0,,Normal text with \\N{\\i1}italic{\\i0} and {\\b1}bold{\\b0}
"""
    
    with open('advanced.ass', 'w', encoding='utf-8') as f:
        f.write(advanced_ass)
    
    parser = SubtitleParser()
    result = parser.parse_file('advanced.ass')
    
    if result.is_valid:
        print("✓ Advanced ASS parsing successful!")
        
        subtitle_track = result.metadata['subtitle_track']
        print(f"  Parsed {len(subtitle_track.elements)} elements")
        
        for i, element in enumerate(subtitle_track.elements):
            print(f"  Element {i+1}:")
            print(f"    Text: \"{element.content}\"")
            print(f"    Font: {element.font_family} ({element.font_size}pt)")
            print(f"    Color: {element.color}")
    else:
        print("✗ Advanced ASS parsing failed!")
        print(f"  Error: {result.error_message}")
    
    # Cleanup
    try:
        os.remove('advanced.ass')
    except OSError:
        pass


if __name__ == "__main__":
    try:
        test_subtitle_parser()
        test_ass_advanced_features()
        
        print(f"\n" + "=" * 50)
        print("Demo completed successfully!")
        print("\nTo use subtitle import in the application:")
        print("1. Run the main application: python main.py")
        print("2. Go to File > Import Subtitles...")
        print("3. Select your .ass, .srt, or .vtt file")
        print("4. The subtitles will be imported as a new track")
        
    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()