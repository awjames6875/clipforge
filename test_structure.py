#!/usr/bin/env python3
"""
Test script to verify ClipForge structure without dependencies
"""

import os
import json
from pathlib import Path

def test_project_structure():
    """Test that all required files and directories exist."""
    
    base_dir = Path(__file__).parent
    
    required_files = [
        'clipforge.py',
        'transcribe.py',
        'ai_enhance.py',
        'captions.py',
        'render.py',
        'requirements.txt',
        'README.md',
        'LICENSE',
        'templates/hormozi.json',
        'templates/mrbeast.json',
        'templates/clean.json',
        'examples/README.md'
    ]
    
    print("🔍 Testing ClipForge project structure...")
    
    missing_files = []
    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print(f"\n✅ All {len(required_files)} required files found!")
    return True

def test_template_validity():
    """Test that template JSON files are valid."""
    
    print("\n🧪 Testing template validity...")
    
    templates_dir = Path(__file__).parent / "templates"
    template_files = list(templates_dir.glob("*.json"))
    
    valid_templates = []
    invalid_templates = []
    
    for template_file in template_files:
        try:
            with open(template_file, 'r') as f:
                template_data = json.load(f)
            
            # Check required keys
            required_keys = ['name', 'description', 'styles']
            missing_keys = [key for key in required_keys if key not in template_data]
            
            if missing_keys:
                print(f"❌ {template_file.name} - missing keys: {missing_keys}")
                invalid_templates.append(template_file.name)
            else:
                print(f"✅ {template_file.name} - valid JSON structure")
                valid_templates.append(template_file.name)
                
        except json.JSONDecodeError as e:
            print(f"❌ {template_file.name} - invalid JSON: {e}")
            invalid_templates.append(template_file.name)
        except Exception as e:
            print(f"❌ {template_file.name} - error: {e}")
            invalid_templates.append(template_file.name)
    
    if invalid_templates:
        print(f"\n❌ {len(invalid_templates)} invalid templates")
        return False
    
    print(f"\n✅ All {len(valid_templates)} templates are valid!")
    return True

def test_imports():
    """Test which modules can be imported without dependencies."""
    
    print("\n📦 Testing module imports...")
    
    modules_to_test = [
        ('os', 'Built-in module'),
        ('json', 'Built-in module'),
        ('pathlib', 'Built-in module'),
        ('subprocess', 'Built-in module'),
        ('logging', 'Built-in module'),
        ('argparse', 'Built-in module')
    ]
    
    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"✅ {module_name} - {description}")
        except ImportError:
            print(f"❌ {module_name} - {description}")

def show_project_stats():
    """Show project statistics."""
    
    print("\n📊 Project Statistics:")
    
    base_dir = Path(__file__).parent
    
    # Count lines of code
    py_files = list(base_dir.rglob("*.py"))
    total_lines = 0
    
    for py_file in py_files:
        if py_file.name != 'test_structure.py':  # Exclude this test file
            try:
                with open(py_file, 'r') as f:
                    lines = len(f.readlines())
                    total_lines += lines
                    print(f"  {py_file.name}: {lines} lines")
            except Exception:
                pass
    
    print(f"\n  Total Python code: {total_lines} lines")
    
    # Count template files
    template_files = list((base_dir / "templates").glob("*.json"))
    print(f"  Templates: {len(template_files)}")
    
    # Check README size
    readme_path = base_dir / "README.md"
    if readme_path.exists():
        readme_size = readme_path.stat().st_size / 1024  # KB
        print(f"  README.md: {readme_size:.1f} KB")

if __name__ == "__main__":
    print("🎬 ClipForge v1.0 - Structure Test")
    print("=" * 50)
    
    structure_ok = test_project_structure()
    templates_ok = test_template_validity()
    
    test_imports()
    show_project_stats()
    
    print("\n" + "=" * 50)
    
    if structure_ok and templates_ok:
        print("🎉 ClipForge structure test PASSED!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Set up Claude API key in ~/.openclaw/.env")
        print("3. Test with a sample video: python3 clipforge.py --help")
        exit_code = 0
    else:
        print("❌ ClipForge structure test FAILED!")
        print("Fix the issues above before proceeding.")
        exit_code = 1
    
    exit(exit_code)