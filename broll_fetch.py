"""
B-Roll Auto-Fetch Module
Downloads trending stock footage from Pexels API based on transcript content.
Free, unlimited, HD clips — no subscription needed.
"""

import os
import json
import logging
import requests
import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)

# Pexels API - free, just needs a key from pexels.com/api
PEXELS_API_URL = "https://api.pexels.com/videos/search"
PIXABAY_API_URL = "https://pixabay.com/api/videos/"

# Default B-roll search terms by category
TRENDING_PACKS = {
    "money": ["counting money", "cash falling", "cryptocurrency", "stock market", "dollar bills", "luxury lifestyle"],
    "tech": ["coding computer", "robot ai", "smartphone typing", "data visualization", "circuit board"],
    "motivation": ["sunrise morning", "running workout", "mountain top", "city timelapse", "gym training"],
    "business": ["office meeting", "handshake deal", "presentation", "startup team", "whiteboard strategy"],
    "kids": ["children playing", "kids learning", "daycare classroom", "family happy", "playground"],
    "health": ["yoga meditation", "healthy food", "therapy session", "mental health", "wellness spa"],
    "nature": ["ocean waves", "forest aerial", "rain drops", "clouds timelapse", "fire flames"],
}

# Keyword → B-roll mapping for auto-detection
KEYWORD_BROLL_MAP = {
    "money": ["money", "cash", "dollar", "cost", "price", "revenue", "profit", "income", "pay", "afford", "expensive", "cheap", "free", "budget", "investment"],
    "tech": ["ai", "robot", "automate", "software", "computer", "app", "technology", "digital", "algorithm", "code", "system"],
    "motivation": ["grind", "hustle", "work", "success", "goal", "dream", "achieve", "win", "champion", "growth"],
    "business": ["business", "company", "client", "customer", "lead", "sales", "marketing", "agency", "startup", "scale"],
    "kids": ["kids", "children", "child", "parent", "family", "daycare", "school", "learn", "play", "youth"],
    "health": ["health", "therapy", "mental", "wellness", "care", "behavioral", "treatment", "healing"],
}


def get_pexels_key():
    """Get Pexels API key from environment or .env file."""
    key = os.getenv('PEXELS_API_KEY')
    if key:
        return key
    
    env_path = os.path.expanduser('~/.openclaw/.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('PEXELS_API_KEY='):
                    return line.split('=', 1)[1].strip()
    return None


def search_pexels_videos(query, api_key, count=3, orientation="portrait", min_duration=3, max_duration=15):
    """Search Pexels for stock video clips."""
    headers = {"Authorization": api_key}
    params = {
        "query": query,
        "per_page": count,
        "orientation": orientation,
        "size": "medium",
    }
    
    try:
        resp = requests.get(PEXELS_API_URL, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        results = []
        for video in data.get("videos", []):
            duration = video.get("duration", 0)
            if min_duration <= duration <= max_duration:
                # Get the HD file
                video_files = video.get("video_files", [])
                # Prefer HD portrait
                best = None
                for vf in video_files:
                    if vf.get("height", 0) >= 720:
                        if best is None or vf.get("height", 0) <= 1080:
                            best = vf
                if not best and video_files:
                    best = video_files[0]
                
                if best:
                    results.append({
                        "id": video["id"],
                        "query": query,
                        "duration": duration,
                        "width": best.get("width"),
                        "height": best.get("height"),
                        "url": best.get("link"),
                        "photographer": video.get("user", {}).get("name", "Unknown"),
                    })
        
        return results
    except Exception as e:
        logger.warning(f"Pexels search failed for '{query}': {e}")
        return []


def download_video(url, output_path, timeout=30):
    """Download a video file."""
    try:
        resp = requests.get(url, timeout=timeout, stream=True)
        resp.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        logger.warning(f"Download failed: {e}")
        return False


def detect_broll_categories(transcript_text):
    """Analyze transcript to determine which B-roll categories to fetch."""
    text_lower = transcript_text.lower()
    scores = {}
    
    for category, keywords in KEYWORD_BROLL_MAP.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[category] = score
    
    # Sort by relevance, return top 3
    sorted_cats = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [cat for cat, _ in sorted_cats[:3]]


def fetch_broll_for_transcript(transcript_data, output_dir, api_key=None, max_clips=5):
    """
    Main function: analyze transcript and fetch relevant B-roll clips.
    
    Args:
        transcript_data: Dict with 'full_text' and 'words'
        output_dir: Where to save downloaded clips
        api_key: Pexels API key (auto-detects if None)
        max_clips: Max clips to download
        
    Returns:
        list: Paths to downloaded B-roll clips with metadata
    """
    if api_key is None:
        api_key = get_pexels_key()
    
    if not api_key:
        logger.warning("No PEXELS_API_KEY found. Get a free key at https://www.pexels.com/api/")
        logger.warning("Add to ~/.openclaw/.env: PEXELS_API_KEY=your_key_here")
        return []
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Detect relevant categories
    text = transcript_data.get("full_text", "")
    categories = detect_broll_categories(text)
    
    if not categories:
        categories = ["motivation"]  # Default fallback
    
    logger.info(f"B-roll categories detected: {categories}")
    
    # Search for clips
    all_clips = []
    clips_per_cat = max(1, max_clips // len(categories))
    
    for category in categories:
        queries = TRENDING_PACKS.get(category, [category])
        # Pick top 2 queries
        for query in queries[:2]:
            results = search_pexels_videos(query, api_key, count=clips_per_cat)
            all_clips.extend(results)
            if len(all_clips) >= max_clips:
                break
        if len(all_clips) >= max_clips:
            break
    
    # Download clips
    downloaded = []
    for i, clip in enumerate(all_clips[:max_clips]):
        filename = f"broll_{clip['query'].replace(' ', '_')}_{clip['id']}.mp4"
        filepath = os.path.join(output_dir, filename)
        
        # Skip if already downloaded
        if os.path.exists(filepath):
            logger.info(f"B-roll cached: {filename}")
            clip["local_path"] = filepath
            downloaded.append(clip)
            continue
        
        logger.info(f"Downloading B-roll {i+1}/{min(len(all_clips), max_clips)}: '{clip['query']}' ({clip['duration']}s)")
        if download_video(clip["url"], filepath):
            clip["local_path"] = filepath
            downloaded.append(clip)
    
    logger.info(f"✅ {len(downloaded)} B-roll clips ready in {output_dir}")
    return downloaded


def download_broll_pack(pack_name, output_dir, api_key=None, clips_per_query=2):
    """
    Download a themed B-roll pack for your library.
    
    Usage: python broll_fetch.py --pack money --output ./broll/money/
    """
    if api_key is None:
        api_key = get_pexels_key()
    
    if not api_key:
        logger.error("No PEXELS_API_KEY. Get free at https://www.pexels.com/api/")
        return []
    
    if pack_name not in TRENDING_PACKS:
        logger.error(f"Unknown pack: {pack_name}. Available: {list(TRENDING_PACKS.keys())}")
        return []
    
    os.makedirs(output_dir, exist_ok=True)
    queries = TRENDING_PACKS[pack_name]
    
    downloaded = []
    for query in queries:
        results = search_pexels_videos(query, api_key, count=clips_per_query)
        for clip in results:
            filename = f"{query.replace(' ', '_')}_{clip['id']}.mp4"
            filepath = os.path.join(output_dir, filename)
            
            if os.path.exists(filepath):
                logger.info(f"Cached: {filename}")
                clip["local_path"] = filepath
                downloaded.append(clip)
                continue
            
            logger.info(f"Downloading: '{query}' ({clip['duration']}s)")
            if download_video(clip["url"], filepath):
                clip["local_path"] = filepath
                downloaded.append(clip)
    
    logger.info(f"✅ Pack '{pack_name}': {len(downloaded)} clips saved to {output_dir}")
    return downloaded


if __name__ == "__main__":
    import argparse
    
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    parser = argparse.ArgumentParser(description="ClipForge B-Roll Fetcher")
    parser.add_argument("--pack", help="Download a themed pack: money, tech, motivation, business, kids, health, nature")
    parser.add_argument("--search", help="Search for specific B-roll clips")
    parser.add_argument("--output", default="./broll", help="Output directory")
    parser.add_argument("--count", type=int, default=5, help="Number of clips")
    parser.add_argument("--api-key", help="Pexels API key (or set PEXELS_API_KEY)")
    
    args = parser.parse_args()
    
    key = args.api_key or get_pexels_key()
    
    if args.pack:
        download_broll_pack(args.pack, os.path.join(args.output, args.pack), key)
    elif args.search:
        results = search_pexels_videos(args.search, key, count=args.count)
        for r in results:
            print(f"  {r['query']} | {r['duration']}s | {r['width']}x{r['height']}")
            filepath = os.path.join(args.output, f"{r['query'].replace(' ', '_')}_{r['id']}.mp4")
            os.makedirs(args.output, exist_ok=True)
            download_video(r["url"], filepath)
            print(f"  → {filepath}")
    else:
        print("Usage:")
        print("  Download pack:  python broll_fetch.py --pack money --output ./broll")
        print("  Search clips:   python broll_fetch.py --search 'cash falling' --count 3")
        print(f"\nAvailable packs: {', '.join(TRENDING_PACKS.keys())}")


def get_pixabay_key():
    """Get Pixabay API key from environment or .env file."""
    key = os.getenv('PIXABAY_API_KEY')
    if key:
        return key
    env_path = os.path.expanduser('~/.openclaw/.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('PIXABAY_API_KEY='):
                    return line.split('=', 1)[1].strip()
    return None


def search_pixabay_videos(query, api_key, count=3, orientation="vertical", min_duration=3, max_duration=15):
    """Search Pixabay for stock video clips."""
    params = {
        "key": api_key,
        "q": query,
        "per_page": count,
        "video_type": "film",
        "safesearch": "true",
        "order": "popular",
    }
    
    try:
        resp = requests.get(PIXABAY_API_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        results = []
        for video in data.get("hits", []):
            duration = video.get("duration", 0)
            if min_duration <= duration <= max_duration:
                # Get medium or large video file
                videos = video.get("videos", {})
                best = videos.get("medium", videos.get("large", videos.get("small", {})))
                
                if best and best.get("url"):
                    w = best.get("width", 0)
                    h = best.get("height", 0)
                    results.append({
                        "id": video["id"],
                        "query": query,
                        "duration": duration,
                        "width": w,
                        "height": h,
                        "url": best["url"],
                        "photographer": video.get("user", "Unknown"),
                        "source": "pixabay",
                    })
        
        return results
    except Exception as e:
        logger.warning(f"Pixabay search failed for '{query}': {e}")
        return []


def search_all_sources(query, count=2, orientation="portrait"):
    """Search BOTH Pexels and Pixabay, return best results combined."""
    all_results = []
    
    pexels_key = get_pexels_key()
    if pexels_key:
        pexels_results = search_pexels_videos(query, pexels_key, count=count, orientation=orientation)
        for r in pexels_results:
            r["source"] = "pexels"
        all_results.extend(pexels_results)
    
    pixabay_key = get_pixabay_key()
    if pixabay_key:
        px_orientation = "vertical" if orientation == "portrait" else "horizontal"
        pixabay_results = search_pixabay_videos(query, pixabay_key, count=count, orientation=px_orientation)
        all_results.extend(pixabay_results)
    
    if not all_results:
        logger.warning(f"No results from any source for: {query}")
    else:
        logger.info(f"Found {len(all_results)} clips for '{query}' (Pexels: {len([r for r in all_results if r.get('source')=='pexels'])}, Pixabay: {len([r for r in all_results if r.get('source')=='pixabay'])})")
    
    return all_results
