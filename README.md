# Karaoke Subtitle Creator

A professional desktop application for creating karaoke videos with advanced text effects and real-time OpenGL-based preview capabilities.

## 🎵 Complete Workflow

### Step 1: Import Media Files

- **Add video file** (MP4, MOV, AVI) or add image if no video available
- **Add audio file** (MP3, WAV, AAC)
- **Add subtitle file** (.ass format with full styling support)

### Step 2: Preview & Edit

- **Preview window** shows karaoke overlay on video/image
- **Text editor** allows fixing typos in .ass subtitle text
- **Timeline editor** for adjusting subtitle timing

### Step 3: Apply Text Effects

- **Select text effects** from effect library:
  - **Animation Effects**: fade, slide, typewriter, bounce
  - **Visual Effects**: glow, outline, shadow, gradient
  - **Particle Effects**: sparkle, fire, smoke
  - **3D Transform**: rotation, extrusion, perspective
  - **Color Effects**: rainbow, pulse, strobe, temperature
- **Adjust effect parameters** with real-time preview

### Step 4: Export

- **Export to MP4** with subtitle burn-in
- **Choose quality settings** (Draft, Normal, High, Custom)
- **Save final karaoke video**

## 🚀 Quick Start

1. **Run the application**:

   ```bash
   python main.py
   ```

2. **Create a new project**:

   - File → New Project
   - Set resolution and frame rate

3. **Import your media**:

   - File → Import Video (optional)
   - File → Import Audio
   - File → Import Subtitles (.ass file)

4. **Edit and preview**:

   - Use timeline to scrub through video
   - Select text elements to apply effects
   - Adjust parameters in real-time

5. **Export your video**:
   - File → Export Video
   - Choose quality settings
   - Save as MP4

## 🎨 Features

### Core Features

- ✅ Real-time OpenGL-based video preview (60fps)
- ✅ Advanced text effects and animations
- ✅ Multiple subtitle format support (.ass, .srt, .vtt)
- ✅ Professional video export with customizable quality settings
- ✅ Timeline-based editing with keyframe animation
- ✅ Particle effects and 3D transformations

### Text Effects Library

- **Animation**: Fade in/out, slide transitions, typewriter reveal, bounce physics
- **Visual**: Glow effects, outline/stroke, drop shadows, gradient fills
- **Particle**: Sparkle effects, fire simulation, smoke trails
- **3D Transform**: Text rotation, extrusion, perspective projection
- **Color**: Rainbow cycling, pulse animations, strobe effects, temperature shifts

### Export Options

- **Formats**: MP4, MOV, AVI
- **Quality Presets**: Draft (fast), Normal (balanced), High (quality), Custom
- **Resolutions**: SD (480p), HD (720p), Full HD (1080p), 2K (1440p), 4K (2160p)
- **Hardware Acceleration**: GPU encoding support when available

## 📋 Requirements

- Python 3.8+
- PyQt6
- OpenGL 3.3+
- FFmpeg (for video export)
- FreeType (for text rendering)

## 🛠️ Installation

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd karaoke-subtitle-creator
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Install FFmpeg** (for video export):

   - Windows: Download from https://ffmpeg.org/
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg`

4. **Run the application**:
   ```bash
   python main.py
   ```

## 🧪 Testing

Run the workflow test to verify all components:

```bash
python test_workflow.py
```

This will test:

- ✅ Subtitle import functionality
- ✅ Project creation
- ✅ Effect system
- ✅ Export pipeline
- ✅ UI components

## 📁 Project Structure

```
/
├── src/                    # Source code
│   ├── core/              # Core application logic
│   │   ├── controller.py  # Main application controller
│   │   ├── models.py      # Data models
│   │   ├── project_manager.py # Project management
│   │   └── timeline_engine.py # Timeline and keyframes
│   ├── ui/                # User interface components
│   │   ├── main_window.py # Main application window
│   │   ├── timeline_panel.py # Timeline editor
│   │   ├── effect_properties_panel.py # Effect controls
│   │   └── text_editor_panel.py # Text editing
│   ├── graphics/          # OpenGL rendering
│   │   ├── opengl_renderer.py # Main renderer
│   │   └── shader_manager.py # Shader management
│   ├── effects/           # Text effects and animations
│   │   ├── animation_effects.py # Animation system
│   │   ├── visual_effects.py # Visual effects
│   │   ├── particle_system.py # Particle effects
│   │   ├── transform_3d.py # 3D transformations
│   │   └── color_effects.py # Color effects
│   ├── text/              # Text rendering and subtitle parsing
│   │   ├── subtitle_parser.py # Subtitle file parser
│   │   ├── text_renderer.py # Text rendering
│   │   └── font_manager.py # Font management
│   ├── video/             # Video processing and export
│   │   ├── export_pipeline.py # Video export
│   │   └── asset_handler.py # Video file handling
│   └── audio/             # Audio processing
│       ├── asset_handler.py # Audio file handling
│       └── waveform_generator.py # Waveform display
├── shaders/               # GLSL shader files
├── assets/                # Static resources
├── tests/                 # Test files
├── main.py               # Application entry point
├── test_workflow.py      # Workflow verification
└── requirements.txt      # Python dependencies
```

## 🎯 Usage Examples

### Basic Karaoke Video Creation

1. **Start with a new project**:

   ```python
   # File → New Project
   # Set resolution: 1920x1080, Frame rate: 30fps
   ```

2. **Import your files**:

   ```python
   # File → Import Audio → select your_song.mp3
   # File → Import Subtitles → select lyrics.ass
   ```

3. **Apply effects**:

   - Select text in timeline
   - Choose "Glow" effect with blue color
   - Add "Typewriter" animation
   - Set "Rainbow" color cycling

4. **Export**:
   ```python
   # File → Export Video
   # Quality: High, Format: MP4
   # Resolution: 1920x1080
   ```

### Advanced Effect Combinations

- **Karaoke Highlight**: Glow + Color Pulse + Typewriter
- **Party Mode**: Rainbow + Sparkle Particles + Bounce Animation
- **3D Style**: Perspective Transform + Outline + Shadow
- **Fire Text**: Fire Particles + Color Temperature + Glow

## 🔧 Configuration

### Export Settings

- **Video Codec**: H.264, H.265, or hardware-accelerated options
- **Audio Codec**: AAC, MP3, or PCM
- **Bitrate**: Customizable for quality vs file size balance
- **Hardware Acceleration**: Automatic GPU detection and usage

### Performance Optimization

- **Preview Quality**: Draft mode for smooth editing
- **GPU Memory**: Automatic texture management
- **Multi-threading**: Parallel processing for export

## 🐛 Troubleshooting

### Common Issues

1. **"FFmpeg not found"**:

   - Install FFmpeg and ensure it's in your PATH
   - Windows: Add FFmpeg bin folder to system PATH

2. **"OpenGL context failed"**:

   - Update graphics drivers
   - Ensure OpenGL 3.3+ support

3. **"Subtitle import failed"**:

   - Check file encoding (UTF-8 recommended)
   - Verify .ass file format compliance

4. **Poor export performance**:
   - Enable hardware acceleration
   - Reduce export resolution for testing
   - Close other applications during export

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python test_workflow.py`
5. Submit a pull request

## 🎉 Acknowledgments

- OpenGL community for rendering techniques
- FFmpeg team for video processing capabilities
- PyQt6 for the user interface framework
- FreeType for text rendering support
