# Project Structure

## Recommended Organization

```
/
├── src/                    # Source code
│   ├── core/              # Core application logic
│   ├── graphics/          # OpenGL rendering code
│   ├── audio/             # Audio processing and synchronization
│   ├── text/              # Text rendering and lyrics handling
│   └── video/             # Video encoding and output
├── shaders/               # GLSL shader files
│   ├── vertex/            # Vertex shaders
│   └── fragment/          # Fragment shaders
├── assets/                # Static resources
│   ├── fonts/             # Font files for text rendering
│   ├── textures/          # Image textures
│   └── samples/           # Sample audio/video files
├── tests/                 # Unit and integration tests
├── docs/                  # Documentation
├── build/                 # Build output (generated)
└── examples/              # Example usage and demos
```

## File Naming Conventions

- Use lowercase with underscores for source files: `audio_processor.cpp`
- Use descriptive names for shaders: `text_vertex.glsl`, `background_fragment.glsl`
- Keep asset files organized by type and purpose
- Use consistent extensions: `.cpp/.h` for C++, `.py` for Python, `.glsl` for shaders

## Code Organization Principles

- Separate concerns: graphics, audio, video encoding in different modules
- Keep platform-specific code isolated
- Use clear interfaces between components
- Maintain separation between rendering logic and business logic

## Key Directories

- **src/**: All source code, organized by functionality
- **shaders/**: OpenGL shader programs separate from source
- **assets/**: Runtime resources that don't change
- **build/**: Generated files, should be in .gitignore
- **tests/**: Automated testing code
