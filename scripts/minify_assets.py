#!/usr/bin/env python3
"""
Asset Minification Script for Aldudu Academy
Minifies CSS and JavaScript files for production deployment.

Usage:
    python scripts/minify_assets.py

Requirements:
    pip install csscompressor jsmin
"""

import os
import sys
from pathlib import Path

try:
    from csscompressor import compress as compress_css
except ImportError:
    print("Installing csscompressor...")
    os.system('pip install csscompressor')
    from csscompressor import compress as compress_css

try:
    from jsmin import jsmin
except ImportError:
    print("Installing jsmin...")
    os.system('pip install jsmin')
    from jsmin import jsmin


STATIC_DIR = Path(__file__).parent.parent / 'app' / 'static'
BUILD_DIR = STATIC_DIR / 'build'


def minify_css(input_path: Path, output_path: Path) -> int:
    """Minify CSS file and return size reduction percentage."""
    with open(input_path, 'r', encoding='utf-8') as f:
        original = f.read()
    
    minified = compress_css(original)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(minified)
    
    original_size = len(original.encode('utf-8'))
    minified_size = len(minified.encode('utf-8'))
    reduction = ((original_size - minified_size) / original_size) * 100 if original_size > 0 else 0
    
    return reduction


def minify_js(input_path: Path, output_path: Path) -> int:
    """Minify JavaScript file and return size reduction percentage."""
    with open(input_path, 'r', encoding='utf-8') as f:
        original = f.read()
    
    minified = jsmin(original)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(minified)
    
    original_size = len(original.encode('utf-8'))
    minified_size = len(minified.encode('utf-8'))
    reduction = ((original_size - minified_size) / original_size) * 100 if original_size > 0 else 0
    
    return reduction


def main():
    """Main function to minify all CSS and JS files."""
    print("=" * 60)
    print("Aldudu Academy - Asset Minification")
    print("=" * 60)
    
    # Create build directory
    BUILD_DIR.mkdir(exist_ok=True)
    (BUILD_DIR / 'css').mkdir(exist_ok=True)
    (BUILD_DIR / 'js').mkdir(exist_ok=True)
    
    total_original = 0
    total_minified = 0
    files_processed = 0
    
    # Minify CSS files
    print("\n📄 Minifying CSS files...")
    css_files = list(STATIC_DIR.glob('*.css'))
    
    for css_file in css_files:
        output_file = BUILD_DIR / 'css' / css_file.name
        try:
            reduction = minify_css(css_file, output_file)
            original_size = css_file.stat().st_size
            minified_size = output_file.stat().st_size
            total_original += original_size
            total_minified += minified_size
            files_processed += 1
            print(f"  ✓ {css_file.name}: {original_size:,} → {minified_size:,} bytes ({reduction:.1f}% reduction)")
        except Exception as e:
            print(f"  ✗ {css_file.name}: Error - {e}")
    
    # Minify JS files in root static/js folder
    print("\n📜 Minifying JavaScript files...")
    js_files = list(STATIC_DIR.glob('*.js')) + list((STATIC_DIR / 'js').glob('*.js'))
    
    for js_file in js_files:
        if js_file.name.endswith('.min.js'):
            continue  # Skip already minified files
        
        # Preserve directory structure in build
        if js_file.parent == STATIC_DIR:
            output_file = BUILD_DIR / 'js' / js_file.name
        else:
            rel_path = js_file.relative_to(STATIC_DIR)
            output_file = BUILD_DIR / rel_path
            output_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            reduction = minify_js(js_file, output_file)
            original_size = js_file.stat().st_size
            minified_size = output_file.stat().st_size
            total_original += original_size
            total_minified += minified_size
            files_processed += 1
            print(f"  ✓ {js_file.name}: {original_size:,} → {minified_size:,} bytes ({reduction:.1f}% reduction)")
        except Exception as e:
            print(f"  ✗ {js_file.name}: Error - {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"✅ Minification complete!")
    print(f"   Files processed: {files_processed}")
    print(f"   Total size: {total_original:,} → {total_minified:,} bytes")
    
    if total_original > 0:
        overall_reduction = ((total_original - total_minified) / total_original) * 100
        print(f"   Overall reduction: {overall_reduction:.1f}%")
    
    print(f"   Output directory: {BUILD_DIR}")
    print("=" * 60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
