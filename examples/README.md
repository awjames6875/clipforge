# 📚 ClipForge Examples

This directory contains practical examples and use cases for ClipForge.

## 🎯 Basic Examples

### Simple Captioning
```bash
# Clean, professional captions
python clipforge.py my_video.mp4 --template clean --output clean_video.mp4

# High-energy MrBeast style
python clipforge.py challenge.mp4 --template mrbeast --output challenge_captioned.mp4

# Sales/business content with Hormozi style
python clipforge.py sales_pitch.mp4 --template hormozi --output sales_final.mp4
```

### With B-Roll
```bash
# Add B-roll from a folder
python clipforge.py tutorial.mp4 \
  --template clean \
  --broll ./broll_footage/ \
  --output tutorial_enhanced.mp4
```

### With Background Music
```bash
# Add trending beat with custom volume
python clipforge.py content.mp4 \
  --template mrbeast \
  --beat trending_beat.mp3 \
  --beat-volume 0.08 \
  --output content_with_music.mp4
```

## 🎨 Template-Specific Examples

### Hormozi Template (Business/Sales)
Perfect for:
- Sales pitches
- Business advice
- Motivational content
- Course previews

```bash
python clipforge.py business_tips.mp4 \
  --template hormozi \
  --voice-volume 1.4 \
  --whoosh-volume 2.5 \
  --output business_final.mp4
```

Expected output:
- ALL CAPS text
- Green keyword highlights
- Impact font with thick outlines
- Aggressive, attention-grabbing style

### MrBeast Template (Entertainment)
Perfect for:
- Challenges and competitions
- High-energy content
- Number-heavy content
- Reaction videos

```bash
python clipforge.py challenge_video.mp4 \
  --template mrbeast \
  --broll ./reaction_footage/ \
  --beat upbeat_music.mp3 \
  --output challenge_final.mp4
```

Expected output:
- Bold, colorful text
- Yellow highlights with red outlines
- Large font sizes
- Background boxes for readability

### Clean Template (Educational)
Perfect for:
- Tutorials and how-tos
- Professional presentations
- Educational content
- Minimalist aesthetic

```bash
python clipforge.py tutorial.mp4 \
  --template clean \
  --voice-volume 1.2 \
  --no-broll \
  --output tutorial_clean.mp4
```

Expected output:
- Lowercase, readable text
- Subtle gold highlights
- Minimal styling
- Professional appearance

## 🔧 Advanced Workflows

### Batch Processing
Process multiple videos with the same settings:

```bash
#!/bin/bash
# batch_process.sh

TEMPLATE="hormozi"
BROLL_DIR="./broll_library"
BEAT_FILE="./assets/trending_beat.mp3"

for video in raw_videos/*.mp4; do
    filename=$(basename "$video" .mp4)
    echo "Processing: $filename"
    
    python clipforge.py "$video" \
        --template $TEMPLATE \
        --broll $BROLL_DIR \
        --beat $BEAT_FILE \
        --output "final_videos/${filename}_captioned.mp4" \
        --verbose
done

echo "Batch processing complete!"
```

### Quality Control Workflow
```bash
# 1. Quick preview with fast settings
python clipforge.py test_video.mp4 \
  --template clean \
  --model tiny \
  --keep-temp \
  --output preview.mp4

# 2. Review the preview and temp files

# 3. Final render with quality settings  
python clipforge.py test_video.mp4 \
  --template clean \
  --model large \
  --broll ./selected_broll/ \
  --beat final_music.mp3 \
  --output final_high_quality.mp4
```

### Custom Audio Mixing
```bash
# Boost quiet speaker with background music
python clipforge.py quiet_audio.mp4 \
  --template mrbeast \
  --voice-volume 2.0 \
  --beat relaxing_beat.mp3 \
  --beat-volume 0.05 \
  --output boosted_audio.mp4

# Aggressive sales style with no background music
python clipforge.py sales_video.mp4 \
  --template hormozi \
  --voice-volume 1.5 \
  --whoosh-volume 4.0 \
  --output aggressive_sales.mp4
```

## 📁 File Organization

### Recommended Folder Structure
```
my_content_project/
├── raw_videos/           # Original video files
├── broll_library/        # B-roll footage organized by theme
│   ├── money/
│   ├── technology/
│   ├── lifestyle/
│   └── reactions/
├── music/               # Background beats and music
├── final_videos/        # Processed output
└── scripts/            # Batch processing scripts
```

### B-Roll Organization Tips
```
broll_library/
├── business/
│   ├── handshake_deal.mp4
│   ├── money_cash_stack.mp4
│   └── office_meeting.mp4
├── tech/
│   ├── coding_screen.mp4
│   ├── smartphone_usage.mp4
│   └── laptop_work.mp4
└── lifestyle/
    ├── workout_gym.mp4
    ├── coffee_morning.mp4
    └── travel_city.mp4
```

## 🚨 Troubleshooting Examples

### Common Issues and Solutions

#### Audio/Video Sync Problems
```bash
# If captions are out of sync, try adjusting Whisper model
python clipforge.py problematic.mp4 \
  --template clean \
  --model medium \  # or 'large' for better accuracy
  --verbose
```

#### FFmpeg Errors
```bash
# Test FFmpeg installation
ffmpeg -version

# Simple test render without B-roll
python clipforge.py test.mp4 \
  --template clean \
  --no-broll \
  --keep-temp \
  --verbose
```

#### Memory Issues with Large Files
```bash
# Process shorter segments for very long videos
python clipforge.py long_video.mp4 \
  --template clean \
  --model base \  # smaller model
  --no-broll \    # skip B-roll processing
  --output processed_long.mp4
```

## 📊 Performance Benchmarks

### Processing Times (approximate)
| Video Length | Template | Model | Time |
|--------------|----------|-------|------|
| 30 seconds   | clean    | tiny  | 45s  |
| 30 seconds   | hormozi  | base  | 90s  |
| 60 seconds   | mrbeast  | large | 5min |
| 60 seconds + B-roll | any | base | 8min |

### Hardware Recommendations
- **Minimum**: 8GB RAM, dual-core CPU
- **Recommended**: 16GB RAM, quad-core CPU, dedicated GPU
- **Professional**: 32GB RAM, 8+ core CPU, RTX 3080+

## 🎓 Learning Path

### Beginner
1. Start with `--template clean` and no B-roll
2. Experiment with different templates
3. Add simple background music
4. Practice with short videos (30-60 seconds)

### Intermediate
1. Create custom template variations
2. Build B-roll library with organized filenames
3. Use batch processing scripts
4. Experiment with audio mixing settings

### Advanced
1. Modify template JSON files
2. Create custom AI prompts
3. Develop automated workflows
4. Contribute templates to the community

## 🔗 Integration Examples

### Social Media Automation
```bash
# Process and upload to multiple platforms
python clipforge.py content.mp4 --template mrbeast --output tiktok.mp4
python clipforge.py content.mp4 --template clean --output youtube.mp4
python clipforge.py content.mp4 --template hormozi --output instagram.mp4

# Then use platform APIs or tools like Zapier for uploads
```

### Content Creator Pipeline
```bash
#!/bin/bash
# creator_pipeline.sh

# Step 1: Process with different templates
python clipforge.py "$1" --template hormozi --output "${1%.*}_hormozi.mp4"
python clipforge.py "$1" --template mrbeast --output "${1%.*}_mrbeast.mp4"
python clipforge.py "$1" --template clean --output "${1%.*}_clean.mp4"

# Step 2: Generate thumbnails (placeholder for future feature)
echo "Thumbnails will be auto-generated in v1.1"

# Step 3: Upload to content management system
echo "Integration with your CMS here"
```

---

Ready to start creating? Pick an example that matches your content style and begin experimenting!

For more advanced use cases, check the [main README](../README.md) or join our community discussions.