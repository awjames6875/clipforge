# 🎬 ClipForge v1.0

**The Open Source Alternative to Submagic**

Auto-caption your short-form videos with word-by-word highlighting, B-roll overlays, and professional styling. Built for creators who want full control over their content without subscription fees.

![ClipForge Demo](demo.gif)
*Demo GIF placeholder - showing before/after video transformation*

---

## 🚀 Features

### ✨ Core Capabilities
- **Word-by-word highlighting** - Precise timing with Whisper transcription
- **Professional templates** - Hormozi, MrBeast, and Clean styles included
- **AI-powered enhancement** - Claude API picks keywords and suggests B-roll moments
- **B-roll automation** - Intelligent overlay of supplementary footage
- **Audio enhancement** - Voice boosting, background music, transition SFX
- **ASS caption format** - Advanced styling with full customization control

### 🎨 Built-in Templates

| Template | Style | Best For |
|----------|-------|----------|
| **hormozi** | ALL CAPS, Impact font, green highlights | Business/sales content, aggressive messaging |
| **mrbeast** | Bold colors, yellow highlights, large text | High-energy content, challenges, big numbers |
| **clean** | Minimal, lowercase, subtle highlights | Educational content, professional presentations |

### 🤖 AI Enhancement
- Keyword detection for strategic highlighting
- Hook identification (first 3-5 seconds get larger text)
- B-roll moment suggestions based on content analysis
- Context-aware styling recommendations

---

## 📦 Installation

### Prerequisites
```bash
# Install FFmpeg (required)
# Ubuntu/Debian:
sudo apt update && sudo apt install ffmpeg

# macOS:
brew install ffmpeg

# Windows: Download from https://ffmpeg.org/download.html
```

### Install ClipForge
```bash
# Clone the repository
git clone https://github.com/your-username/clipforge.git
cd clipforge

# Install Python dependencies
pip install -r requirements.txt

# Set up Claude API (required for AI enhancement)
echo "ANTHROPIC_API_KEY=your_api_key_here" >> ~/.openclaw/.env
```

### Verify Installation
```bash
python clipforge.py --help
```

---

## 🎯 Quick Start

### Basic Usage
```bash
# Simple captioning with clean template
python clipforge.py input.mp4 --template clean --output final.mp4

# Hormozi-style with all features
python clipforge.py video.mp4 --template hormozi --broll ./broll_folder --beat music.mp3
```

### Advanced Examples
```bash
# Custom audio settings
python clipforge.py content.mp4 \
  --template mrbeast \
  --voice-volume 1.5 \
  --beat-volume 0.08 \
  --whoosh-volume 2.0

# Keep intermediate files for editing
python clipforge.py video.mp4 \
  --template clean \
  --keep-temp \
  --no-broll

# Verbose logging for troubleshooting
python clipforge.py problematic.mp4 \
  --template hormozi \
  --verbose
```

---

## 🏗️ Architecture

```
Input Video → Whisper → Claude AI → ASS Captions → FFmpeg → Final Video
     ↓           ↓         ↓           ↓           ↓
   Audio      Word       Keywords    Styled      B-roll
 Extraction  Timestamps  Detection   Captions    Overlay
```

### Pipeline Stages

1. **Transcription** (`transcribe.py`)
   - Whisper with `word_timestamps=True`
   - Confidence scoring and validation
   - Language auto-detection

2. **AI Enhancement** (`ai_enhance.py`)
   - Claude API analyzes transcript
   - Identifies 8-15 keywords for highlighting
   - Suggests 3-5 B-roll insertion points
   - Detects opening hook for larger text

3. **Caption Generation** (`captions.py`)
   - ASS format for advanced styling
   - Word-by-word timing precision
   - Template-based visual formatting

4. **Rendering** (`render.py`)
   - FFmpeg pipeline with complex filters
   - Audio enhancement and mixing
   - B-roll overlay with transitions
   - Final video assembly

---

## 🎨 Template Customization

Templates are JSON files in the `templates/` directory. Create your own by copying and modifying existing templates.

### Template Structure
```json
{
  "name": "your_template",
  "description": "Your custom style",
  
  "styles": {
    "main": {
      "font": "Arial",
      "size": 28,
      "color": "&H00FFFFFF",
      "outline_color": "&H00000000",
      "outline_width": 3
    },
    "highlight": { /* highlighted words */ },
    "hook": { /* opening hook styling */ }
  },
  
  "text_processing": {
    "transform": "uppercase", // or "lowercase", "title_case"
    "max_chars_per_line": 35
  },
  
  "ai_prompts": {
    "keyword_focus": "power words, emotions, calls to action",
    "style_context": "Your content style description"
  }
}
```

### Color Format
ASS uses BGR format with transparency:
- `&H00FFFFFF` = White
- `&H0000FF00` = Green  
- `&H0000FFFF` = Yellow
- `&H00FF0000` = Blue

---

## 📁 Project Structure

```
clipforge/
├── clipforge.py          # Main CLI entry point
├── transcribe.py         # Whisper transcription engine
├── captions.py           # ASS caption generation
├── ai_enhance.py         # Claude API integration
├── render.py             # FFmpeg rendering pipeline
├── templates/
│   ├── hormozi.json      # Alex Hormozi style
│   ├── mrbeast.json      # MrBeast style
│   └── clean.json        # Minimal style
├── examples/
│   └── README.md         # Usage examples
├── requirements.txt      # Python dependencies
├── LICENSE               # MIT License
└── README.md             # This file
```

---

## 🔧 Configuration

### Environment Variables
```bash
# Required for AI enhancement
ANTHROPIC_API_KEY=your_claude_api_key

# Optional: Custom model settings
WHISPER_MODEL=base  # tiny, base, small, medium, large
```

### Advanced Settings
Create a `config.json` file for project-specific settings:
```json
{
  "default_template": "clean",
  "audio_boost": 1.3,
  "background_music_volume": 0.12,
  "max_video_duration": 300,
  "temp_dir": "./temp"
}
```

---

## 🎥 B-Roll System

ClipForge can automatically overlay B-roll footage at strategic moments:

### Setup
1. Create a folder with your B-roll videos (MP4, MOV, AVI, MKV, WebM)
2. Use descriptive filenames (e.g., `money_cash_dollars.mp4`, `office_workspace.mp4`)
3. Run with `--broll ./your_broll_folder`

### How It Works
- Claude AI analyzes transcript for visual concepts
- Matches B-roll files based on filename keywords
- Overlays in picture-in-picture style (configurable)
- Adds whoosh transition effects
- Maintains original audio throughout

---

## 🚀 Performance Tips

### Speed Optimization
- Use `--model tiny` for faster transcription (lower accuracy)
- Pre-process B-roll videos to 1080p for faster overlay
- Use SSD storage for temp files (`--keep-temp` for analysis)

### Quality Optimization  
- Use `--model large` for best transcription accuracy
- Provide high-quality B-roll footage (1080p+)
- Record clean audio (reduces transcription errors)
- Use `--voice-volume` to boost quiet audio

### Batch Processing
```bash
#!/bin/bash
for video in *.mp4; do
  python clipforge.py "$video" --template hormozi --output "captioned_$video"
done
```

---

## 🤝 Contributing

We welcome contributions! Areas where help is needed:

- **New templates** - Create styles for different creators/niches
- **Enhanced B-roll matching** - Better AI selection algorithms  
- **Animation effects** - Advanced caption animations
- **Multi-language support** - Templates for different languages
- **GUI interface** - Desktop/web interface for non-technical users

### Development Setup
```bash
git clone https://github.com/your-username/clipforge.git
cd clipforge

# Install development dependencies
pip install -r requirements.txt
pip install pytest black flake8

# Run tests
python -m pytest tests/

# Format code
black .

# Lint
flake8 --max-line-length=100
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

You are free to use, modify, and distribute this software for both personal and commercial purposes.

---

## 🙏 Credits

**Built by [GrowthGenix AI](https://growthgenix.ai)**

### Technology Stack
- **Whisper** - OpenAI's speech recognition
- **Claude** - Anthropic's AI for content analysis
- **FFmpeg** - Video processing and rendering
- **Python** - Core application framework

### Inspiration
Created as an open-source alternative to Submagic, empowering creators with full control over their content and no subscription fees.

---

## 📞 Support

- **GitHub Issues** - Bug reports and feature requests
- **Discussions** - Community help and template sharing
- **Documentation** - Full docs at [clipforge.dev](https://clipforge.dev)

### Professional Services
Need custom templates, bulk processing, or integration support? Contact [GrowthGenix AI](https://growthgenix.ai) for professional development services.

---

## 🔮 Roadmap

### v1.1 - Enhanced AI
- GPT-4V integration for visual content analysis
- Automated thumbnail generation
- Sentiment-based keyword weighting

### v1.2 - Advanced Styling  
- Custom font loading system
- Gradient text effects
- Particle animations for highlights

### v1.3 - Multi-Platform
- Direct upload to TikTok, YouTube Shorts, Instagram Reels
- Cloud processing API
- Mobile app (React Native)

### v2.0 - Studio Edition
- GUI interface with real-time preview
- Advanced timeline editing
- Team collaboration features
- Analytics and performance tracking

---

*Made with ❤️ by creators, for creators*