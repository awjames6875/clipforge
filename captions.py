"""
ASS Caption Generation Module
Creates Advanced SubStation Alpha (.ass) files with word-by-word highlighting
"""

import logging
import os
from pathlib import Path
import math

logger = logging.getLogger(__name__)

def generate_ass_captions(enhanced_data, template, output_path, video_path=None):
    """
    Generate ASS caption file with word-by-word highlighting.
    
    Args:
        enhanced_data (dict): Enhanced transcript data from ai_enhance.py
        template (dict): Template configuration
        output_path (str): Output ASS file path
        video_path (str): Input video to detect resolution
        
    Returns:
        str: Path to generated ASS file
    """
    transcript_data = enhanced_data["transcript"]
    words = transcript_data["words"]
    
    # Detect actual video resolution
    if video_path:
        try:
            import subprocess, json as _json
            probe = subprocess.run(
                ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', video_path],
                capture_output=True, text=True
            )
            data = _json.loads(probe.stdout)
            vs = [s for s in data['streams'] if s['codec_type'] == 'video'][0]
            w, h = int(vs['width']), int(vs['height'])
            # Check for rotation (Samsung phones store portrait as rotated landscape)
            rotation = 0
            if 'tags' in vs and 'rotate' in vs['tags']:
                rotation = int(vs['tags']['rotate'])
            if 'side_data_list' in vs:
                for sd in vs['side_data_list']:
                    if 'rotation' in sd:
                        rotation = abs(int(sd['rotation']))
            if rotation in (90, 270):
                w, h = h, w  # Swap for rotated video
            template["_video_width"] = w
            template["_video_height"] = h
            logger.info(f"Detected video resolution: {w}x{h} (rotation: {rotation}°)")
        except Exception:
            pass
    
    logger.info(f"Generating ASS captions: {len(words)} words")
    
    # Create ASS file content
    ass_content = build_ass_header(template)
    
    # Process words into caption events
    caption_events = create_caption_events(words, template, enhanced_data)
    
    # Add events to ASS content
    for event in caption_events:
        ass_content += event + "\n"
    
    # Write to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ass_content)
    
    logger.info(f"ASS captions generated: {output_path}")
    return output_path

def build_ass_header(template):
    """Build the ASS file header with styles."""
    
    # Extract template styling
    main_style = template["styles"]["main"]
    highlight_style = template["styles"]["highlight"]
    hook_style = template["styles"].get("hook", main_style)
    
    # Video resolution — detect from video or default to 1080x1920
    video_width = template.get("_video_width", 1080)
    video_height = template.get("_video_height", 1920)
    
    ass_header = f"""[Script Info]
Title: ClipForge Generated Captions
ScriptType: v4.00+
Collisions: Normal
PlayResX: {video_width}
PlayResY: {video_height}
Timer: 100.0000
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{main_style["font"]},{main_style["size"]},{main_style["color"]},{main_style["color"]},{main_style["outline_color"]},{main_style["background_color"]},{1 if main_style.get("bold", True) else 0},0,0,0,100,100,0,0,1,{main_style["outline_width"]},{main_style["shadow_offset"]},{main_style["alignment"]},{main_style["margin_left"]},{main_style["margin_right"]},{main_style["margin_vertical"]},1
Style: Highlight,{highlight_style["font"]},{highlight_style["size"]},{highlight_style["color"]},{highlight_style["color"]},{highlight_style["outline_color"]},{highlight_style["background_color"]},{1 if highlight_style.get("bold", True) else 0},0,0,0,100,100,0,0,1,{highlight_style["outline_width"]},{highlight_style["shadow_offset"]},{highlight_style["alignment"]},{highlight_style["margin_left"]},{highlight_style["margin_right"]},{highlight_style["margin_vertical"]},1
Style: Hook,{hook_style["font"]},{hook_style["size"]},{hook_style["color"]},{hook_style["color"]},{hook_style["outline_color"]},{hook_style["background_color"]},{1 if hook_style.get("bold", True) else 0},0,0,0,100,100,0,0,1,{hook_style["outline_width"]},{hook_style["shadow_offset"]},{hook_style["alignment"]},{hook_style["margin_left"]},{hook_style["margin_right"]},{hook_style["margin_vertical"]},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    return ass_header

def create_caption_events(words, template, enhanced_data):
    """Create ASS dialogue events for word-by-word highlighting."""
    
    events = []
    
    # Group words into display lines based on timing and length
    display_groups = group_words_for_display(words, template)
    
    for group in display_groups:
        # Create the base text line showing all words
        full_line = create_full_line_event(group, template, enhanced_data)
        events.append(full_line)
        
        # Create individual word highlight events
        for word_info in group:
            if word_info.get("is_highlighted") or word_info.get("is_hook"):
                highlight_event = create_word_highlight_event(word_info, group, template, enhanced_data)
                events.append(highlight_event)
    
    return events

def group_words_for_display(words, template):
    """Group words into logical display lines based on timing and character limits."""
    
    max_chars_per_line = template.get("max_chars_per_line", 35)
    max_duration_per_line = template.get("max_duration_per_line", 4.0)
    
    groups = []
    current_group = []
    current_length = 0
    group_start_time = None
    
    for word in words:
        word_text = word["word"].strip()
        
        # Initialize group timing
        if group_start_time is None:
            group_start_time = word["start"]
        
        # Calculate potential new length
        new_length = current_length + len(word_text) + (1 if current_group else 0)
        group_duration = word["end"] - group_start_time
        
        # Check if we should start a new group
        should_break = (
            new_length > max_chars_per_line or 
            group_duration > max_duration_per_line or
            (current_group and word["start"] - current_group[-1]["end"] > 1.0)  # Long pause
        )
        
        if should_break and current_group:
            # Finalize current group
            groups.append(current_group)
            
            # Start new group
            current_group = [word]
            current_length = len(word_text)
            group_start_time = word["start"]
        else:
            # Add to current group
            current_group.append(word)
            current_length = new_length
    
    # Add final group
    if current_group:
        groups.append(current_group)
    
    logger.debug(f"Grouped {len(words)} words into {len(groups)} display lines")
    return groups

def create_full_line_event(word_group, template, enhanced_data):
    """Create the base text line showing all words in the group."""
    
    start_time = format_ass_time(word_group[0]["start"])
    end_time = format_ass_time(word_group[-1]["end"])
    
    # Build the full text with proper formatting
    formatted_words = []
    for word in word_group:
        word_text = word["word"].strip()
        
        # Apply template text transformations
        if template["name"] == "hormozi":
            word_text = word_text.upper()
        elif template["name"] == "clean":
            word_text = word_text.lower()
        
        formatted_words.append(word_text)
    
    full_text = " ".join(formatted_words)
    
    # Escape special ASS characters
    full_text = escape_ass_text(full_text)
    
    # Determine base style
    has_hook = any(w.get("is_hook", False) for w in word_group)
    base_style = "Hook" if has_hook else "Default"
    
    event = f"Dialogue: 0,{start_time},{end_time},{base_style},,0,0,0,,{full_text}"
    
    return event

def create_word_highlight_event(word_info, word_group, template, enhanced_data):
    """Create a highlight event for a specific word."""
    
    word_start = format_ass_time(word_info["start"])
    word_end = format_ass_time(word_info["end"])
    
    word_text = word_info["word"].strip()
    
    # Apply text transformations
    if template["name"] == "hormozi":
        word_text = word_text.upper()
    elif template["name"] == "clean":
        word_text = word_text.lower()
    
    # Build the line with this word highlighted
    highlighted_words = []
    for word in word_group:
        w_text = word["word"].strip()
        
        # Apply template transformations
        if template["name"] == "hormozi":
            w_text = w_text.upper()
        elif template["name"] == "clean":
            w_text = w_text.lower()
        
        if word == word_info:
            # This is the highlighted word
            if word_info.get("is_hook"):
                w_text = f"{{\\rHook}}{w_text}{{\\rDefault}}"
            else:
                w_text = f"{{\\rHighlight}}{w_text}{{\\rDefault}}"
        
        highlighted_words.append(w_text)
    
    full_text = " ".join(highlighted_words)
    full_text = escape_ass_text(full_text)
    
    # Use higher layer so highlight appears on top
    event = f"Dialogue: 1,{word_start},{word_end},Default,,0,0,0,,{full_text}"
    
    return event

def format_ass_time(seconds):
    """Convert seconds to ASS time format (H:MM:SS.CC)."""
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centiseconds = int((seconds % 1) * 100)
    
    return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"

def escape_ass_text(text):
    """Escape special characters in ASS text."""
    
    # Replace newlines and tabs
    text = text.replace('\n', '\\N')
    text = text.replace('\t', ' ')
    
    # Escape braces if they're not ASS tags
    # (Keep simple for now - more complex escaping can be added later)
    
    return text

def validate_ass_file(ass_path):
    """Validate generated ASS file for common issues."""
    
    if not os.path.exists(ass_path):
        raise FileNotFoundError(f"ASS file not found: {ass_path}")
    
    with open(ass_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Basic validation checks
    required_sections = ['[Script Info]', '[V4+ Styles]', '[Events]']
    for section in required_sections:
        if section not in content:
            raise ValueError(f"Missing required ASS section: {section}")
    
    # Count dialogue events
    dialogue_count = content.count('Dialogue:')
    if dialogue_count == 0:
        raise ValueError("No dialogue events found in ASS file")
    
    logger.info(f"ASS validation passed: {dialogue_count} dialogue events")
    return True

def preview_captions(ass_path, num_lines=10):
    """Preview generated captions for debugging."""
    
    with open(ass_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find events section
    events_start = -1
    for i, line in enumerate(lines):
        if line.strip() == '[Events]':
            events_start = i
            break
    
    if events_start == -1:
        logger.error("Could not find [Events] section in ASS file")
        return
    
    # Skip format line and show dialogue events
    dialogue_lines = [line for line in lines[events_start:] if line.startswith('Dialogue:')]
    
    logger.info(f"Caption preview ({min(num_lines, len(dialogue_lines))} of {len(dialogue_lines)} events):")
    for i, line in enumerate(dialogue_lines[:num_lines]):
        # Parse dialogue line to show timing and text
        parts = line.strip().split(',', 9)
        if len(parts) >= 10:
            start_time = parts[1]
            end_time = parts[2]
            text = parts[9]
            logger.info(f"  [{start_time} -> {end_time}] {text[:60]}...")

if __name__ == "__main__":
    # Test caption generation
    import sys
    import json
    from pathlib import Path
    from transcribe import transcribe_video
    from ai_enhance import enhance_with_ai
    
    if len(sys.argv) < 2:
        print("Usage: python captions.py <video_file> [template_name]")
        sys.exit(1)
    
    video_file = sys.argv[1]
    template_name = sys.argv[2] if len(sys.argv) > 2 else "clean"
    
    logging.basicConfig(level=logging.INFO)
    
    # Load template
    template_path = Path(__file__).parent / "templates" / f"{template_name}.json"
    with open(template_path, 'r') as f:
        template = json.load(f)
    
    # Get transcript and enhance
    transcript_data = transcribe_video(video_file, "base")
    enhanced_data = enhance_with_ai(transcript_data, template)
    
    # Generate captions
    output_path = video_file.replace('.mp4', '_captions.ass')
    ass_file = generate_ass_captions(enhanced_data, template, output_path)
    
    # Validate and preview
    validate_ass_file(ass_file)
    preview_captions(ass_file)
    
    print(f"✅ ASS captions generated: {ass_file}")