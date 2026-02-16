#!/usr/bin/env python3
"""
ClipForge Setup Script
Handles installation and configuration
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check Python version compatibility."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher required")
        print(f"Current version: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} compatible")
    return True

def check_ffmpeg():
    """Check if FFmpeg is installed."""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                               capture_output=True, check=True)
        print("✅ FFmpeg is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg not found")
        print("Install FFmpeg:")
        print("  Ubuntu/Debian: sudo apt install ffmpeg")
        print("  macOS: brew install ffmpeg")
        print("  Windows: Download from https://ffmpeg.org/")
        return False

def install_requirements():
    """Install Python requirements."""
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    print("📦 Installing Python dependencies...")
    
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)], 
                      check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        print("Try running manually: pip install -r requirements.txt")
        return False

def setup_api_key():
    """Setup Claude API key."""
    env_file = Path.home() / ".openclaw" / ".env"
    
    # Check if key already exists
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
            if "ANTHROPIC_API_KEY" in content:
                print("✅ Claude API key already configured")
                return True
    
    print("🔑 Claude API key setup required")
    print("Get your API key from: https://console.anthropic.com/")
    
    api_key = input("Enter your Claude API key (or press Enter to skip): ").strip()
    
    if not api_key:
        print("⚠️  API key skipped - you'll need to set ANTHROPIC_API_KEY manually")
        return False
    
    # Create .openclaw directory if it doesn't exist
    env_file.parent.mkdir(exist_ok=True)
    
    # Append API key to .env file
    with open(env_file, 'a') as f:
        f.write(f"\nANTHROPIC_API_KEY={api_key}\n")
    
    # Set secure permissions
    os.chmod(env_file, 0o600)
    
    print("✅ API key configured successfully")
    return True

def test_installation():
    """Test ClipForge installation."""
    print("\n🧪 Testing installation...")
    
    try:
        # Test imports
        import whisper
        print("✅ Whisper imported successfully")
    except ImportError:
        print("❌ Whisper import failed")
        return False
    
    try:
        import anthropic
        print("✅ Anthropic imported successfully")
    except ImportError:
        print("❌ Anthropic import failed")
        return False
    
    # Test ClipForge help
    clipforge_path = Path(__file__).parent / "clipforge.py"
    try:
        result = subprocess.run([sys.executable, str(clipforge_path), '--help'], 
                               capture_output=True, check=True)
        print("✅ ClipForge CLI working")
        return True
    except subprocess.CalledProcessError:
        print("❌ ClipForge CLI failed")
        return False

def main():
    """Main setup function."""
    print("🎬 ClipForge v1.0 Setup")
    print("=" * 40)
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    if not check_ffmpeg():
        print("\n⚠️  FFmpeg is required but not installed")
        continue_anyway = input("Continue setup anyway? (y/n): ").lower().strip()
        if continue_anyway != 'y':
            sys.exit(1)
    
    # Install dependencies
    if not install_requirements():
        sys.exit(1)
    
    # Setup API key
    setup_api_key()
    
    # Test installation
    if test_installation():
        print("\n🎉 ClipForge setup complete!")
        print("\nQuick start:")
        print("  python3 clipforge.py input.mp4 --template clean --output final.mp4")
        print("\nFor more examples, see: examples/README.md")
    else:
        print("\n❌ Setup completed with issues")
        print("Check the errors above and try running setup again")
        sys.exit(1)

if __name__ == "__main__":
    main()