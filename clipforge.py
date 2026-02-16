#!/usr/bin/env python3
"""
ClipForge v1.0 - Open Source Alternative to Submagic
Auto-caption short-form videos with word-by-word highlighting, B-roll, and SFX

Built by GrowthGenix AI
"""

import argparse
import os
import sys
import json
import logging
from pathlib import Path

from transcribe import transcribe_video
from ai_enhance import enhance_with_ai
from captions import generate_ass_captions
from render import render_final_video
from broll_fetch import fetch_broll_for_transcript

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def load_template(template_name):
    """Load template configuration from JSON file."""
    template_path = Path(__file__).parent / "templates" / f"{template_name}.json"
    
    if not template_path.exists():
        available_templates = [f.stem for f in (Path(__file__).parent / "templates").glob("*.json")]
        logger.error(f"Template '{template_name}' not found. Available templates: {available_templates}")
        sys.exit(1)
    
    with open(template_path, 'r') as f:
        return json.load(f)

def validate_dependencies():
    """Check if required dependencies are installed."""
    import subprocess
    
    # Check FFmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        logger.info("✓ FFmpeg found")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("✗ FFmpeg not found. Please install FFmpeg")
        sys.exit(1)
    
    # Check Whisper
    try:
        import whisper
        logger.info("✓ Whisper found")
    except ImportError:
        logger.error("✗ Whisper not found. Please install: pip install openai-whisper")
        sys.exit(1)
    
    # Check Claude API key (optional — falls back to heuristic)
    if not os.getenv('ANTHROPIC_API_KEY'):
        logger.warning("⚠ ANTHROPIC_API_KEY not found — will use heuristic keyword detection")
    else:
        logger.info("✓ Claude API key found")

def main():
    parser = argparse.ArgumentParser(
        description="ClipForge v1.0 - Auto-caption videos with word-by-word highlighting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python clipforge.py input.mp4 --template hormozi --output final.mp4
  python clipforge.py video.mp4 --template mrbeast --broll ./broll_folder --beat music.mp3
  python clipforge.py content.mp4 --template clean --no-broll --voice-volume 1.5

Templates:
  hormozi   - ALL CAPS, Impact font, green highlights (Alex Hormozi style)
  mrbeast   - Bold colors, yellow highlights, large text with emoji support  
  clean     - Minimal, lowercase, thin font with subtle highlights
        """
    )
    
    # Required arguments
    parser.add_argument('input', help='Input video file path')
    parser.add_argument('--template', '-t', required=True, 
                       choices=['hormozi', 'mrbeast', 'clean'],
                       help='Caption template style')
    
    # Optional arguments
    parser.add_argument('--output', '-o', default='output.mp4',
                       help='Output video file path (default: output.mp4)')
    parser.add_argument('--broll', help='B-roll library folder path')
    parser.add_argument('--beat', help='Background music file path')
    parser.add_argument('--beat-volume', type=float, default=0.12,
                       help='Background music volume (default: 0.12)')
    parser.add_argument('--voice-volume', type=float, default=1.3,
                       help='Voice audio boost (default: 1.3)')
    parser.add_argument('--whoosh-volume', type=float, default=3.0,
                       help='Whoosh SFX volume for B-roll transitions (default: 3.0)')
    parser.add_argument('--no-broll', action='store_true',
                       help='Disable B-roll suggestions and overlay')
    parser.add_argument('--keep-temp', action='store_true',
                       help='Keep intermediate files (clean.mp4, captions.ass, etc.)')
    parser.add_argument('--model', default='base',
                       help='Whisper model size: tiny, base, small, medium, large (default: base)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate input file
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    
    # Validate dependencies
    logger.info("Checking dependencies...")
    validate_dependencies()
    
    # Load template
    logger.info(f"Loading template: {args.template}")
    template = load_template(args.template)
    
    # Pipeline execution
    try:
        # Step 1: Transcription
        logger.info("Step 1/4: Transcribing video with Whisper...")
        transcript_data = transcribe_video(args.input, model_size=args.model)
        
        # Step 2: AI Enhancement
        logger.info("Step 2/4: Enhancing with Claude AI...")
        enhanced_data = enhance_with_ai(
            transcript_data, 
            template, 
            enable_broll=not args.no_broll,
            broll_folder=args.broll
        )
        # Ensure transcript is attached to enhanced data
        if "transcript" not in enhanced_data:
            enhanced_data["transcript"] = transcript_data
        
        # Step 2.5: Auto-fetch B-roll from Pexels matching each moment
        if not args.no_broll and enhanced_data.get("broll_suggestions"):
            broll_dir = args.broll or os.path.join(os.path.dirname(os.path.abspath(args.output)), "broll_cache")
            logger.info("Step 2.5/4: Fetching context-matched B-roll from Pexels...")
            from broll_fetch import search_pexels_videos, download_video, get_pexels_key
            api_key = get_pexels_key()
            if api_key:
                os.makedirs(broll_dir, exist_ok=True)
                for idx, suggestion in enumerate(enhanced_data["broll_suggestions"]):
                    query = suggestion.get("search_query", suggestion.get("description", "trending"))
                    trigger = suggestion.get("trigger_word", suggestion.get("trigger_phrase", f"clip{idx}"))
                    results = search_pexels_videos(query, api_key, count=1, orientation="portrait")
                    if results:
                        clip = results[0]
                        safe_trigger = str(trigger).replace(" ", "_")[:20]
                        filename = f"broll_{safe_trigger}_{clip['id']}.mp4"
                        filepath = os.path.join(broll_dir, filename)
                        if not os.path.exists(filepath):
                            logger.info(f"Downloading B-roll for '{trigger}': {query}")
                            download_video(clip["url"], filepath)
                        else:
                            logger.info(f"B-roll cached for '{trigger}'")
                        suggestion["suggested_file"] = filename
                args.broll = broll_dir
                logger.info(f"✅ B-roll matched to {len(enhanced_data['broll_suggestions'])} transcript moments")
            else:
                logger.warning("No PEXELS_API_KEY — skipping B-roll fetch")
        
        # Step 3: Generate Captions
        logger.info("Step 3/4: Generating ASS captions...")
        caption_file = generate_ass_captions(
            enhanced_data, 
            template,
            output_path=args.output.replace('.mp4', '.ass'),
            video_path=args.input
        )
        
        # Step 4: Render Final Video
        logger.info("Step 4/4: Rendering final video...")
        render_final_video(
            input_video=args.input,
            caption_file=caption_file,
            output_path=args.output,
            enhanced_data=enhanced_data,
            broll_folder=args.broll,
            beat_file=args.beat,
            beat_volume=args.beat_volume,
            voice_volume=args.voice_volume,
            whoosh_volume=args.whoosh_volume,
            keep_temp=args.keep_temp
        )
        
        logger.info(f"✅ ClipForge complete! Output saved to: {args.output}")
        
        if not args.keep_temp:
            logger.info("Cleaned up temporary files")
        else:
            logger.info(f"Temporary files kept: {caption_file}, clean.mp4, etc.")
            
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()