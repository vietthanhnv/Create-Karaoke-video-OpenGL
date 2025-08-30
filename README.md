# Karaoke Subtitle Creator

A professional desktop application for creating karaoke videos with advanced text effects and real-time OpenGL-based preview capabilities.

## Features

- Real-time OpenGL-accelerated preview at 60fps
- Advanced text effects (animations, particles, 3D transformations)
- Timeline-based editing with keyframe support
- Multi-format video and audio support
- Professional export capabilities (HD/4K)
- Hardware acceleration support

## Requirements

- Python 3.8+
- OpenGL 3.3+ compatible GPU
- PyQt6
- FFmpeg (for video processing)

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

## Development Setup

For development, install additional dependencies:

```bash
pip install -r requirements.txt
pip install -e .
```

## Project Structure

```
/
├── src/                    # Source code
│   ├── core/              # Core application logic
│   ├── graphics/          # OpenGL rendering code
│   ├── audio/             # Audio processing
│   ├── text/              # Text rendering
│   ├── video/             # Video encoding
│   └── ui/                # PyQt6 interface
├── shaders/               # GLSL shader files
├── assets/                # Static resources
├── tests/                 # Unit and integration tests
└── main.py               # Application entry point
```

## License

MIT License - see LICENSE file for details.
