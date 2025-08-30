# Technology Stack

## Core Technologies

- **OpenGL**: Primary graphics rendering API for video composition and effects
- **Audio Processing**: Libraries for audio file handling and synchronization
- **Video Encoding**: FFmpeg or similar for video output generation

## Likely Dependencies

- OpenGL libraries (OpenGL 3.3+ recommended)
- Audio libraries (OpenAL, FMOD, or similar)
- Video encoding libraries (FFmpeg, x264)
- Text rendering libraries (FreeType for font rendering)
- Math libraries for graphics calculations

## Build System

Since no build files are present yet, common approaches for OpenGL projects:

- **C/C++**: CMake, Makefile, or Visual Studio projects
- **Python**: pip requirements, virtual environments
- **JavaScript/WebGL**: npm/yarn with webpack or similar

## Common Commands

```bash
# Build (will vary based on chosen tech stack)
# For CMake projects:
mkdir build && cd build
cmake ..
make

# For Visual Studio:
# Open .sln file and build through IDE

# For Python:
pip install -r requirements.txt
python main.py

# For Node.js:
npm install
npm start
```

## Development Guidelines

- Use modern OpenGL (3.3+) with shaders
- Implement proper resource management for GPU memory
- Follow real-time rendering best practices
- Ensure cross-platform compatibility where possible
- DON'T OPEN UI FOR INTERACTIVE TEST
- TEST SILENTLY
