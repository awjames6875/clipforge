"""
FFmpeg Rendering Module
Handles final video rendering with captions, B-roll, and audio enhancements
"""

import subprocess
import os
import logging
import random
import json
from pathlib import Path

logger = logging.getLogger(__name__)

def render_final_video(input_video, caption_file, output_path, enhanced_data, 
                      broll_folder=None, beat_file=None, beat_volume=0.12, 
                      voice_volume=1.3, whoosh_volume=3.0, keep_temp=False):
    """
    Render final video with captions, B-roll, and audio enhancements.
    
    Args:
        input_video (str): Path to input video
        caption_file (str): Path to ASS caption file
        output_path (str): Path for final output video
        enhanced_data (dict): Enhanced transcript data
        broll_folder (str): B-roll library folder path
        beat_file (str): Background music file path
        beat_volume (float): Background music volume
        voice_volume (float): Voice audio boost multiplier
        whoosh_volume (float): Whoosh SFX volume
        keep_temp (bool): Keep intermediate files
    """
    logger.info("Starting final video render...")
    
    # Create temp directory
    temp_dir = Path(output_path).parent / "temp_clipforge"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Step 1: Extract and boost audio
        audio_file = extract_and_boost_audio(input_video, temp_dir, voice_volume)
        
        # Step 2: Create clean video (video only, no audio)
        clean_video = create_clean_video(input_video, temp_dir)
        
        # Step 3: Apply B-roll overlays if requested
        if broll_folder and enhanced_data.get("broll_suggestions"):
            broll_video = apply_broll_overlays(
                clean_video, enhanced_data["broll_suggestions"], 
                broll_folder, temp_dir, whoosh_volume
            )
        else:
            broll_video = clean_video
        
        # Step 4: Add background music if provided
        if beat_file and os.path.exists(beat_file):
            audio_with_beat = add_background_music(
                audio_file, beat_file, temp_dir, beat_volume
            )
        else:
            audio_with_beat = audio_file
        
        # Step 5: Combine video with captions
        video_with_captions = apply_ass_captions(broll_video, caption_file, temp_dir)
        
        # Step 6: Final render - combine video and audio
        final_render(video_with_captions, audio_with_beat, output_path)
        
        logger.info(f"✅ Render complete: {output_path}")
        
        # Cleanup temp files unless requested to keep them
        if not keep_temp:
            cleanup_temp_files(temp_dir)
        else:
            logger.info(f"Temporary files kept in: {temp_dir}")
            
    except Exception as e:
        logger.error(f"Render failed: {e}")
        raise

def extract_and_boost_audio(input_video, temp_dir, voice_volume):
    """Extract audio from video and apply voice boost."""
    
    audio_file = temp_dir / "audio_boosted.aac"
    
    cmd = [
        'ffmpeg', '-y',
        '-i', str(input_video),
        '-vn',  # No video
        '-acodec', 'aac',
        '-ab', '128k',
        '-af', f'volume={voice_volume}',  # Voice boost
        str(audio_file)
    ]
    
    logger.info("Extracting and boosting audio...")
    run_ffmpeg_command(cmd, "Audio extraction failed")
    
    return audio_file

def create_clean_video(input_video, temp_dir):
    """Create video-only file without audio."""
    
    clean_video = temp_dir / "clean_video.mp4"
    
    cmd = [
        'ffmpeg', '-y',
        '-i', str(input_video),
        '-an',  # No audio
        '-vcodec', 'libx264',
        '-crf', '23',
        '-preset', 'medium',
        str(clean_video)
    ]
    
    logger.info("Creating clean video...")
    run_ffmpeg_command(cmd, "Clean video creation failed")
    
    return clean_video

def apply_broll_overlays(clean_video, broll_suggestions, broll_folder, temp_dir, whoosh_volume):
    """Apply full-screen B-roll overlays at suggested timestamps (Submagic style)."""
    
    if not broll_suggestions:
        return clean_video
    
    logger.info(f"Applying {len(broll_suggestions)} B-roll overlays...")
    
    broll_files = get_broll_files(broll_folder)
    if not broll_files:
        logger.warning("No B-roll files found, skipping B-roll overlay")
        return clean_video
    
    # Match each suggestion to a B-roll file and track inputs
    matched = []  # list of (suggestion, broll_path, input_index)
    input_paths = []  # unique paths added as FFmpeg inputs
    path_to_index = {}  # path → input index
    
    for suggestion in broll_suggestions:
        broll_file = select_broll_file(suggestion, broll_files)
        if not broll_file:
            continue
        broll_path = str(Path(broll_folder) / broll_file)
        if not Path(broll_path).exists():
            continue
        
        if broll_path not in path_to_index:
            idx = len(input_paths) + 1  # +1 because input 0 is the main video
            path_to_index[broll_path] = idx
            input_paths.append(broll_path)
        
        matched.append((suggestion, broll_path, path_to_index[broll_path]))
    
    if not matched:
        return clean_video
    
    # Build filter complex
    filter_parts = []
    current_label = "[0:v]"
    
    for i, (suggestion, broll_path, input_idx) in enumerate(matched):
        start_time = suggestion["start_time"]
        end_time = suggestion["end_time"]
        
        # Scale B-roll to FULL SCREEN 1080x1920 — force fill, no black bars
        filter_parts.append(
            f"[{input_idx}:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920:(iw-1080)/2:(ih-1920)/2,setsar=1[fs{i}]"
        )
        # Full-screen overlay — voice audio continues underneath
        filter_parts.append(
            f"{current_label}[fs{i}]overlay=0:0:enable='between(t,{start_time},{end_time})'[v{i}]"
        )
        current_label = f"[v{i}]"
    
    filter_parts.append(f"{current_label}copy[final]")
    filter_complex = ';'.join(filter_parts)
    
    # Build FFmpeg command
    broll_video = temp_dir / "video_with_broll.mp4"
    cmd = ['ffmpeg', '-y', '-i', str(clean_video)]
    for p in input_paths:
        cmd.extend(['-i', p])
    cmd.extend([
        '-filter_complex', filter_complex,
        '-map', '[final]',
        '-vcodec', 'libx264', '-crf', '23', '-preset', 'medium',
        str(broll_video)
    ])
    
    run_ffmpeg_command(cmd, "B-roll overlay failed")
    return broll_video

def select_broll_file(suggestion, broll_files):
    """Select appropriate B-roll file for a suggestion."""
    
    # If AI suggested a specific file, use it
    suggested_file = suggestion.get("suggested_file")
    if suggested_file and suggested_file in broll_files:
        return suggested_file
    
    # Otherwise, try to match based on description keywords
    description = suggestion.get("description", "").lower()
    trigger_phrase = suggestion.get("trigger_phrase", "").lower()
    
    # Simple keyword matching
    keywords = [description, trigger_phrase]
    
    for broll_file in broll_files:
        filename_lower = broll_file.lower()
        for keyword in keywords:
            if keyword and any(word in filename_lower for word in keyword.split() if len(word) > 3):
                return broll_file
    
    # Fallback: random selection
    if broll_files:
        return random.choice(broll_files)
    
    return None

def get_broll_files(broll_folder):
    """Get list of video files from B-roll folder."""
    
    if not broll_folder or not os.path.exists(broll_folder):
        return []
    
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
    broll_files = []
    
    try:
        for file_path in Path(broll_folder).rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in video_extensions:
                broll_files.append(file_path.name)
        
        return sorted(broll_files)
        
    except Exception as e:
        logger.warning(f"Could not scan B-roll folder: {e}")
        return []

def add_background_music(audio_file, beat_file, temp_dir, beat_volume):
    """Add background music to audio track."""
    
    audio_with_beat = temp_dir / "audio_with_beat.aac"
    
    cmd = [
        'ffmpeg', '-y',
        '-i', str(audio_file),
        '-i', str(beat_file),
        '-filter_complex', f'[1:a]volume={beat_volume}[bg];[0:a][bg]amix=inputs=2:duration=shortest',
        '-acodec', 'aac',
        '-ab', '128k',
        str(audio_with_beat)
    ]
    
    logger.info("Adding background music...")
    run_ffmpeg_command(cmd, "Background music failed")
    
    return audio_with_beat

def apply_ass_captions(video_file, caption_file, temp_dir):
    """Apply ASS captions to video."""
    
    video_with_captions = temp_dir / "video_with_captions.mp4"
    
    # Ensure ASS file path is properly escaped for FFmpeg
    ass_path = str(caption_file).replace('\\', '/')
    
    cmd = [
        'ffmpeg', '-y',
        '-i', str(video_file),
        '-vf', f'ass={ass_path}',
        '-vcodec', 'libx264',
        '-crf', '23',
        '-preset', 'medium',
        str(video_with_captions)
    ]
    
    logger.info("Applying ASS captions...")
    run_ffmpeg_command(cmd, "Caption overlay failed")
    
    return video_with_captions

def final_render(video_file, audio_file, output_path):
    """Combine final video and audio."""
    
    cmd = [
        'ffmpeg', '-y',
        '-i', str(video_file),
        '-i', str(audio_file),
        '-c:v', 'copy',  # Copy video stream (already encoded)
        '-c:a', 'aac',
        '-ab', '128k',
        '-shortest',  # Match shortest stream
        str(output_path)
    ]
    
    logger.info("Final render...")
    run_ffmpeg_command(cmd, "Final render failed")

def run_ffmpeg_command(cmd, error_message):
    """Run FFmpeg command with error handling."""
    
    logger.debug(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Log any warnings from FFmpeg
        if result.stderr:
            logger.debug(f"FFmpeg stderr: {result.stderr}")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"{error_message}")
        logger.error(f"Command: {' '.join(cmd)}")
        logger.error(f"Return code: {e.returncode}")
        logger.error(f"Stderr: {e.stderr}")
        raise

def cleanup_temp_files(temp_dir):
    """Remove temporary files and directory."""
    
    import shutil
    
    if temp_dir.exists():
        try:
            shutil.rmtree(temp_dir)
            logger.info("Temporary files cleaned up")
        except Exception as e:
            logger.warning(f"Could not clean up temp files: {e}")

def get_video_info(video_path):
    """Get video information using FFprobe."""
    
    cmd = [
        'ffprobe',
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        str(video_path)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        probe_data = json.loads(result.stdout)
        
        # Extract video stream info
        video_stream = None
        for stream in probe_data['streams']:
            if stream['codec_type'] == 'video':
                video_stream = stream
                break
        
        if not video_stream:
            raise ValueError("No video stream found")
        
        info = {
            'duration': float(probe_data['format']['duration']),
            'width': int(video_stream['width']),
            'height': int(video_stream['height']),
            'fps': eval(video_stream.get('r_frame_rate', '30/1')),
            'codec': video_stream['codec_name']
        }
        
        return info
        
    except Exception as e:
        logger.error(f"Failed to get video info: {e}")
        return None

if __name__ == "__main__":
    # Test rendering
    import sys
    import json
    from pathlib import Path
    from transcribe import transcribe_video
    from ai_enhance import enhance_with_ai
    from captions import generate_ass_captions
    
    if len(sys.argv) < 2:
        print("Usage: python render.py <video_file> [template_name]")
        sys.exit(1)
    
    video_file = sys.argv[1]
    template_name = sys.argv[2] if len(sys.argv) > 2 else "clean"
    
    logging.basicConfig(level=logging.INFO)
    
    # Load template
    template_path = Path(__file__).parent / "templates" / f"{template_name}.json"
    with open(template_path, 'r') as f:
        template = json.load(f)
    
    # Full pipeline test
    transcript_data = transcribe_video(video_file, "base")
    enhanced_data = enhance_with_ai(transcript_data, template)
    caption_file = generate_ass_captions(enhanced_data, template, 
                                        video_file.replace('.mp4', '_test.ass'))
    
    # Render
    output_path = video_file.replace('.mp4', '_rendered.mp4')
    render_final_video(
        input_video=video_file,
        caption_file=caption_file,
        output_path=output_path,
        enhanced_data=enhanced_data,
        keep_temp=True
    )
    
    print(f"✅ Test render complete: {output_path}")