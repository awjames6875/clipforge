"""
AI Enhancement Module
Uses Claude API to identify keywords for highlighting and suggest B-roll moments
"""

import os
import json
import logging
import random
from pathlib import Path
import anthropic

logger = logging.getLogger(__name__)

def enhance_with_ai(transcript_data, template, enable_broll=True, broll_folder=None):
    """
    Enhance transcript with AI-powered keyword highlighting and B-roll suggestions.
    
    Args:
        transcript_data (dict): Transcript from transcribe.py
        template (dict): Template configuration
        enable_broll (bool): Whether to generate B-roll suggestions
        broll_folder (str): Path to B-roll library folder
        
    Returns:
        dict: Enhanced data with keywords and B-roll suggestions
    """
    # Load environment variables
    if not os.getenv('ANTHROPIC_API_KEY'):
        # Try loading from ~/.openclaw/.env
        env_path = os.path.expanduser('~/.openclaw/.env')
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith('ANTHROPIC_API_KEY='):
                        os.environ['ANTHROPIC_API_KEY'] = line.split('=', 1)[1].strip()
                        break
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        logger.warning("No ANTHROPIC_API_KEY found — using heuristic keyword detection (no AI)")
        return _fallback_enhance(transcript_data, template, enable_broll, broll_folder)
    
    client = anthropic.Anthropic(api_key=api_key)
    
    logger.info("Analyzing transcript with Claude AI...")
    
    # Prepare transcript text
    full_text = transcript_data["full_text"]
    word_count = len(transcript_data["words"])
    
    # Get available B-roll files if folder provided
    broll_files = []
    if enable_broll and broll_folder and os.path.exists(broll_folder):
        broll_files = get_broll_files(broll_folder)
        logger.info(f"Found {len(broll_files)} B-roll files")
    
    # Build AI prompt
    prompt = build_enhancement_prompt(
        full_text, 
        template, 
        enable_broll, 
        broll_files,
        word_count
    )
    
    try:
        # Call Claude API
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        ai_response = response.content[0].text
        logger.debug(f"Claude response: {ai_response[:200]}...")
        
        # Parse AI response
        enhanced_data = parse_ai_response(ai_response, transcript_data, template)
        
        # Apply keyword highlighting to words
        enhanced_data = apply_keyword_highlighting(enhanced_data, transcript_data)
        
        logger.info(f"AI enhancement complete: {len(enhanced_data['keywords'])} keywords, "
                   f"{len(enhanced_data.get('broll_suggestions', []))} B-roll suggestions")
        
        return enhanced_data
        
    except Exception as e:
        logger.error(f"AI enhancement failed: {e}")
        # Fallback: return basic enhanced data without AI
        return create_fallback_enhancement(transcript_data, template)

def build_enhancement_prompt(text, template, enable_broll, broll_files, word_count):
    """Build the prompt for Claude AI analysis."""
    
    template_style = template["name"]
    
    prompt = f"""Analyze this video transcript and enhance it for {template_style}-style captions:

TRANSCRIPT:
{text}

TASK 1 - KEYWORD HIGHLIGHTING:
Identify 8-15 impactful keywords/phrases that should be highlighted in {template_style} style.
Focus on:
- Power words that grab attention
- Key concepts and topics
- Emotional triggers
- Action words and strong verbs
- Numbers and statistics

TASK 2 - HOOK IDENTIFICATION:
Identify the opening hook (first 3-5 seconds) that should use larger text size.
This should be the most attention-grabbing opening statement.

"""

    if enable_broll:
        prompt += f"""TASK 3 - B-ROLL SUGGESTIONS:
Suggest 3-5 strategic moments for B-roll overlay based on the content.
Look for:
- Visual concepts mentioned (objects, places, actions)
- Moments that would benefit from visual support
- Natural pauses or transitions
- Scenes that could use visual emphasis

Available B-roll files: {broll_files[:10] if broll_files else 'None provided'}
"""

    prompt += """
RESPONSE FORMAT (JSON):
{
  "keywords": [
    {"phrase": "keyword or phrase", "importance": 1-5, "context": "why highlight this"},
    ...
  ],
  "hook": {
    "text": "opening hook text",
    "end_time": 5.2,
    "reason": "why this is the hook"
  },
  "broll_suggestions": [
    {
      "start_time": 15.5,
      "end_time": 18.2,
      "description": "what to show",
      "search_query": "specific Pexels search query to find matching stock footage (e.g. 'money cash falling', 'robot artificial intelligence', 'happy children playing')",
      "trigger_phrase": "phrase that triggers this B-roll",
      "suggested_file": "filename.mp4 or null if no specific file"
    },
    ...
  ]
}

Be strategic and selective. Quality over quantity."""

    return prompt

def parse_ai_response(ai_response, transcript_data, template):
    """Parse Claude's JSON response into enhanced data structure."""
    
    try:
        # Extract JSON from response
        json_start = ai_response.find('{')
        json_end = ai_response.rfind('}') + 1
        
        if json_start == -1 or json_end <= json_start:
            raise ValueError("No JSON found in AI response")
        
        json_str = ai_response[json_start:json_end]
        ai_data = json.loads(json_str)
        
        # Build enhanced data structure
        enhanced_data = {
            "transcript": transcript_data,
            "template": template,
            "keywords": ai_data.get("keywords", []),
            "hook": ai_data.get("hook"),
            "broll_suggestions": ai_data.get("broll_suggestions", []),
            "processing_info": {
                "ai_model": "claude-3-sonnet",
                "enhancement_timestamp": str(__import__('datetime').datetime.now())
            }
        }
        
        # Validate and clean data
        enhanced_data = validate_enhanced_data(enhanced_data)
        
        return enhanced_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {e}")
        raise
    except Exception as e:
        logger.error(f"Error parsing AI response: {e}")
        raise

def apply_keyword_highlighting(enhanced_data, transcript_data):
    """Apply keyword highlighting flags to individual words."""
    
    keywords = [kw["phrase"].lower() for kw in enhanced_data["keywords"]]
    hook_text = enhanced_data.get("hook", {}).get("text", "").lower()
    hook_end_time = enhanced_data.get("hook", {}).get("end_time", 5.0)
    
    # Mark words for highlighting
    for word in transcript_data["words"]:
        word_text = word["word"].lower().strip()
        
        # Check if word is part of hook (larger text)
        if word["end"] <= hook_end_time and hook_text and word_text in hook_text:
            word["is_hook"] = True
            word["is_highlighted"] = True
        else:
            word["is_hook"] = False
            
            # Check if word should be highlighted
            word["is_highlighted"] = any(
                word_text in keyword or keyword in word_text 
                for keyword in keywords
            )
    
    # Add word highlighting info to enhanced data
    enhanced_data["word_highlighting"] = {
        "total_words": len(transcript_data["words"]),
        "highlighted_words": sum(1 for w in transcript_data["words"] if w.get("is_highlighted")),
        "hook_words": sum(1 for w in transcript_data["words"] if w.get("is_hook"))
    }
    
    return enhanced_data

def get_broll_files(broll_folder):
    """Get list of available B-roll video files."""
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

def create_fallback_enhancement(transcript_data, template):
    """Create basic enhancement without AI (fallback mode)."""
    
    logger.warning("Creating fallback enhancement without AI")
    
    # Simple keyword detection based on common patterns
    common_keywords = [
        "amazing", "incredible", "secret", "powerful", "proven", "results",
        "money", "success", "growth", "massive", "breakthrough", "game-changer"
    ]
    
    words = [w["word"].lower() for w in transcript_data["words"]]
    
    # Find keywords that appear in transcript
    found_keywords = []
    for keyword in common_keywords:
        if any(keyword in word for word in words):
            found_keywords.append({
                "phrase": keyword,
                "importance": 3,
                "context": "Fallback keyword detection"
            })
    
    # Create basic hook (first 5 seconds)
    hook = {
        "text": transcript_data["sentences"][0]["text"][:50] + "..." if transcript_data["sentences"] else "",
        "end_time": 5.0,
        "reason": "First 5 seconds (fallback)"
    }
    
    enhanced_data = {
        "transcript": transcript_data,
        "template": template,
        "keywords": found_keywords,
        "hook": hook,
        "broll_suggestions": [],
        "processing_info": {
            "ai_model": "fallback",
            "note": "AI enhancement failed, using fallback method"
        }
    }
    
    return apply_keyword_highlighting(enhanced_data, transcript_data)

def validate_enhanced_data(enhanced_data):
    """Validate and clean enhanced data structure."""
    
    # Ensure required keys exist
    required_keys = ["keywords", "hook", "broll_suggestions"]
    for key in required_keys:
        if key not in enhanced_data:
            enhanced_data[key] = [] if key != "hook" else None
    
    # Validate keywords
    valid_keywords = []
    for kw in enhanced_data.get("keywords", []):
        if isinstance(kw, dict) and "phrase" in kw:
            kw["importance"] = max(1, min(5, kw.get("importance", 3)))  # Clamp 1-5
            valid_keywords.append(kw)
    
    enhanced_data["keywords"] = valid_keywords
    
    # Validate B-roll suggestions
    valid_broll = []
    for broll in enhanced_data.get("broll_suggestions", []):
        if isinstance(broll, dict) and "start_time" in broll and "end_time" in broll:
            if broll["start_time"] < broll["end_time"]:
                valid_broll.append(broll)
    
    enhanced_data["broll_suggestions"] = valid_broll
    
    return enhanced_data

if __name__ == "__main__":
    # Test AI enhancement
    import sys
    from transcribe import transcribe_video
    
    if len(sys.argv) < 2:
        print("Usage: python ai_enhance.py <video_file> [template_name]")
        sys.exit(1)
    
    video_file = sys.argv[1]
    template_name = sys.argv[2] if len(sys.argv) > 2 else "clean"
    
    logging.basicConfig(level=logging.INFO)
    
    # Load template
    template_path = Path(__file__).parent / "templates" / f"{template_name}.json"
    with open(template_path, 'r') as f:
        template = json.load(f)
    
    # Get transcript
    transcript_data = transcribe_video(video_file, "base")
    
    # Enhance with AI
    enhanced_data = enhance_with_ai(transcript_data, template, enable_broll=True)
    
    print(f"✅ AI Enhancement complete!")
    print(f"Keywords: {len(enhanced_data['keywords'])}")
    print(f"B-roll suggestions: {len(enhanced_data['broll_suggestions'])}")
    print(f"Hook: {enhanced_data.get('hook', {}).get('text', 'None')}")

def _fallback_enhance(transcript_data, template, enable_broll=True, broll_folder=None):
    """Heuristic keyword detection when no API key available."""
    import re
    full_text = transcript_data["full_text"]
    words = transcript_data.get("words", [])
    
    # Common power words to highlight
    power_words = {
        "money", "free", "save", "cost", "profit", "revenue", "growth",
        "ai", "automate", "scale", "viral", "million", "thousand",
        "secret", "hack", "trick", "strategy", "powerful", "insane",
        "never", "always", "stop", "start", "need", "must", "now",
        "business", "clients", "customers", "leads", "sales",
        "follow", "subscribe", "watch", "click", "link",
        "kids", "children", "parents", "family", "health", "care",
        "partner", "daycare", "program", "community",
    }
    
    # Find keywords from transcript
    keywords = []
    text_words = re.findall(r'\b\w+\b', full_text.lower())
    for w in text_words:
        if w in power_words and w not in [k.lower() for k in keywords]:
            keywords.append(w)
    
    # Also grab any numbers or dollar amounts
    for w in words:
        word_lower = w.get("word", "").lower().strip()
        if any(c.isdigit() for c in word_lower) or word_lower.startswith("$"):
            if word_lower not in [k.lower() for k in keywords]:
                keywords.append(word_lower)
    
    # Limit to ~15 keywords
    keywords = keywords[:15]
    
    # Simple B-roll suggestions based on content
    broll_suggestions = []
    if enable_broll:
        broll_suggestions = _detect_broll_moments(words, full_text)
    
    logger.info(f"Heuristic found {len(keywords)} keywords to highlight")
    
    return {
        "keywords": keywords,
        "broll_suggestions": broll_suggestions,
        "hook_end_time": 3.0,
        "sections": [],
    }


def _detect_broll_moments(words, full_text):
    """
    Scan transcript word-by-word to find B-roll moments that MATCH what's being said.
    Each B-roll gets a specific Pexels search query based on the spoken content.
    """
    import re
    
    # Trigger phrases → Pexels search query (what to SHOW when they SAY this)
    TRIGGER_MAP = {
        # Money / Business
        "money": "money cash dollars close up",
        "cash": "money cash dollars close up",
        "dollar": "dollar bills falling",
        "dollars": "dollar bills falling",
        "revenue": "money counting cash register",
        "profit": "profit chart going up",
        "income": "money cash luxury",
        "cost": "money wallet payment",
        "price": "price tag shopping",
        "expensive": "luxury expensive lifestyle",
        "cheap": "money savings piggy bank",
        "free": "gift box surprise",
        "pay": "payment credit card",
        "afford": "money wallet cash",
        "investment": "stock market trading",
        "invest": "stock market trading",
        "budget": "calculator budget planning",
        "save": "money savings jar",
        "500": "money cash five hundred dollars",
        "thousand": "money stack thousands",
        "million": "luxury mansion lifestyle",
        
        # Tech / AI
        "ai": "artificial intelligence robot futuristic",
        "robot": "robot artificial intelligence",
        "automate": "robot automation factory",
        "automation": "robot automation technology",
        "software": "coding programming computer screen",
        "computer": "laptop computer typing",
        "app": "smartphone mobile app",
        "technology": "futuristic technology hologram",
        "algorithm": "data visualization matrix",
        "system": "server room data center",
        "digital": "digital screen interface",
        "tool": "tools workshop equipment",
        "tools": "tools workshop equipment",
        
        # Business
        "business": "business meeting office professional",
        "company": "corporate office building",
        "client": "business handshake agreement",
        "clients": "business meeting clients",
        "customer": "customer service happy",
        "customers": "crowd of people shopping",
        "lead": "business leads funnel",
        "leads": "phone notifications incoming",
        "sales": "sales chart growth upward",
        "marketing": "social media marketing phone",
        "agency": "modern office team working",
        "startup": "startup office whiteboard",
        "scale": "rocket launch growth",
        "growth": "plant growing timelapse",
        "grow": "plant growing timelapse",
        
        # People / Kids / Family
        "kids": "happy children playing outside",
        "children": "children learning classroom",
        "child": "child playing happy",
        "parent": "parent and child together",
        "parents": "family parents children happy",
        "family": "happy family together",
        "daycare": "daycare children playing colorful",
        "school": "school classroom students",
        "learn": "student studying learning",
        "youth": "teenagers young people group",
        "community": "community gathering people together",
        "people": "diverse group of people",
        
        # Health / Therapy
        "health": "wellness health meditation",
        "therapy": "therapy counseling session peaceful",
        "mental": "meditation peaceful mindfulness",
        "wellness": "spa wellness relaxation",
        "care": "caring hands heart",
        "behavioral": "brain psychology colorful",
        "treatment": "medical healthcare professional",
        "healing": "nature peaceful healing zen",
        
        # Action / Motivation
        "grind": "hustle working late night",
        "hustle": "entrepreneur working hard",
        "work": "person working focused laptop",
        "success": "celebration success winning",
        "goal": "target bullseye achievement",
        "dream": "dreaming clouds sky beautiful",
        "achieve": "trophy award celebration",
        "win": "winning celebration confetti",
        "sleep": "person sleeping bed peaceful",
        "sleeping": "person sleeping bed peaceful",
        "tired": "person tired exhausted",
        
        # Social / Content
        "follow": "social media followers phone",
        "subscribe": "youtube subscribe button",
        "watch": "person watching phone screen",
        "click": "finger clicking mouse cursor",
        "viral": "phone notifications going viral",
        "content": "content creator filming camera",
        "video": "video camera filming production",
        "social media": "social media apps phone scrolling",
    }
    
    # Scan words to find trigger moments
    moments = []
    used_times = []  # Avoid overlapping B-roll
    
    MIN_GAP = 5.0  # Minimum seconds between B-roll moments
    BROLL_DURATION = 3.0
    
    for i, word_data in enumerate(words):
        word = word_data.get("word", "").lower().strip().strip(".,!?\"'")
        start = word_data.get("start", 0)
        
        # Check if this word triggers B-roll
        if word in TRIGGER_MAP:
            # Check minimum gap from previous B-roll
            too_close = any(abs(start - t) < MIN_GAP for t in used_times)
            if too_close:
                continue
            
            query = TRIGGER_MAP[word]
            moments.append({
                "start_time": start,
                "end_time": start + BROLL_DURATION,
                "description": query,
                "trigger_word": word,
                "search_query": query,
            })
            used_times.append(start)
            
            # Max 4 B-roll moments per 60s of video
            total_dur = words[-1]["end"] if words else 30
            max_moments = max(2, int(total_dur / 15))
            if len(moments) >= max_moments:
                break
    
    # If no triggers found, pick 2 evenly spaced generic moments
    if not moments and words:
        total_dur = words[-1]["end"]
        t1, t2 = total_dur * 0.25, total_dur * 0.65
        moments = [
            {"start_time": t1, "end_time": t1 + 3.0, "description": "business motivation success",
             "trigger_word": "auto", "search_query": "business motivation success"},
            {"start_time": t2, "end_time": t2 + 3.0, "description": "technology digital future",
             "trigger_word": "auto", "search_query": "technology digital future"},
        ]
    
    logger.info(f"Found {len(moments)} B-roll moments: {[m['trigger_word'] for m in moments]}")
    return moments
