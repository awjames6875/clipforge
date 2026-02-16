"""
Whisper Transcription Module
Handles video transcription with word-level timestamps using OpenAI Whisper
"""

import whisper
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

def transcribe_video(video_path, model_size="base", language=None):
    """
    Transcribe video using Whisper with word-level timestamps.
    
    Args:
        video_path (str): Path to input video file
        model_size (str): Whisper model size (tiny, base, small, medium, large)
        language (str): Language code (auto-detect if None)
    
    Returns:
        dict: Transcript data with word-level timing information
    """
    logger.info(f"Loading Whisper model: {model_size}")
    
    # Load Whisper model
    try:
        model = whisper.load_model(model_size)
    except Exception as e:
        logger.error(f"Failed to load Whisper model '{model_size}': {e}")
        raise
    
    logger.info(f"Transcribing: {os.path.basename(video_path)}")
    
    # Transcribe with word timestamps
    try:
        result = model.transcribe(
            video_path,
            language=language,
            word_timestamps=True,  # Critical for word-by-word highlighting
            verbose=False
        )
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise
    
    # Extract word-level data
    word_data = []
    sentence_data = []
    
    for segment in result["segments"]:
        # Store sentence-level data
        sentence_info = {
            "text": segment["text"].strip(),
            "start": segment["start"],
            "end": segment["end"],
            "words": []
        }
        
        # Extract word-level timestamps
        if "words" in segment:
            for word_info in segment["words"]:
                word_entry = {
                    "word": word_info["word"].strip(),
                    "start": word_info["start"],
                    "end": word_info["end"],
                    "confidence": word_info.get("probability", 0.0)
                }
                
                word_data.append(word_entry)
                sentence_info["words"].append(word_entry)
        
        sentence_data.append(sentence_info)
    
    transcript_data = {
        "language": result.get("language", "en"),
        "full_text": result["text"].strip(),
        "duration": get_video_duration(video_path),
        "words": word_data,
        "sentences": sentence_data,
        "segments": result["segments"]  # Keep original segments for reference
    }
    
    logger.info(f"Transcription complete: {len(word_data)} words, {len(sentence_data)} sentences")
    logger.debug(f"Detected language: {transcript_data['language']}")
    
    return transcript_data

def get_video_duration(video_path):
    """
    Get video duration in seconds using FFprobe.
    
    Args:
        video_path (str): Path to video file
        
    Returns:
        float: Duration in seconds
    """
    import subprocess
    import json
    
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        probe_data = json.loads(result.stdout)
        
        duration = float(probe_data['format']['duration'])
        return duration
        
    except Exception as e:
        logger.warning(f"Could not determine video duration: {e}")
        return 0.0

def validate_transcript(transcript_data):
    """
    Validate transcript data structure and quality.
    
    Args:
        transcript_data (dict): Transcript data from transcribe_video
        
    Returns:
        bool: True if valid, raises exception if invalid
    """
    required_keys = ["language", "full_text", "words", "sentences"]
    
    for key in required_keys:
        if key not in transcript_data:
            raise ValueError(f"Missing required key in transcript data: {key}")
    
    if not transcript_data["words"]:
        raise ValueError("No words found in transcript")
    
    if not transcript_data["sentences"]:
        raise ValueError("No sentences found in transcript")
    
    # Check word timing consistency
    prev_end = 0
    for word in transcript_data["words"]:
        if word["start"] < prev_end:
            logger.warning(f"Overlapping word timing detected: {word['word']}")
        prev_end = word["end"]
    
    logger.info("Transcript validation passed")
    return True

def export_srt(transcript_data, output_path):
    """
    Export transcript as SRT subtitle file for reference.
    
    Args:
        transcript_data (dict): Transcript data
        output_path (str): Output SRT file path
    """
    def format_srt_time(seconds):
        """Convert seconds to SRT time format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, sentence in enumerate(transcript_data["sentences"], 1):
            start_time = format_srt_time(sentence["start"])
            end_time = format_srt_time(sentence["end"])
            
            f.write(f"{i}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{sentence['text']}\n\n")
    
    logger.info(f"SRT export complete: {output_path}")

if __name__ == "__main__":
    # Test transcription
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python transcribe.py <video_file> [model_size]")
        sys.exit(1)
    
    video_file = sys.argv[1]
    model_size = sys.argv[2] if len(sys.argv) > 2 else "base"
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        transcript = transcribe_video(video_file, model_size)
        validate_transcript(transcript)
        
        # Export SRT for testing
        srt_path = video_file.replace('.mp4', '_transcript.srt')
        export_srt(transcript, srt_path)
        
        print(f"✅ Transcription complete!")
        print(f"Words: {len(transcript['words'])}")
        print(f"Sentences: {len(transcript['sentences'])}")
        print(f"Language: {transcript['language']}")
        print(f"SRT exported: {srt_path}")
        
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        sys.exit(1)