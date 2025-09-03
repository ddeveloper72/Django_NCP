#!/usr/bin/env python3
"""
SASS Compilation Script for EU NCP Server

This script compiles SASS files to CSS for DMZ compatibility.
It can be run standalone or integrated with Django management commands.
"""

import os
import sys
import subprocess
from pathlib import Path


def compile_sass():
    """
    Compile SASS files to CSS using the sass command line tool.

    Returns:
        bool: True if compilation successful, False otherwise
    """
    # Get project root directory
    project_root = Path(__file__).parent
    scss_dir = project_root / "static" / "scss"
    css_dir = project_root / "static" / "css"

    # Ensure CSS directory exists
    css_dir.mkdir(parents=True, exist_ok=True)

    # Main SASS file
    main_scss = scss_dir / "main.scss"
    main_css = css_dir / "main.css"
    main_css_map = css_dir / "main.css.map"

    if not main_scss.exists():
        print(f"❌ Main SASS file not found: {main_scss}")
        return False

    try:
        # Compile expanded CSS for development
        cmd = [
            "sass",
            str(main_scss),
            str(main_css),
            "--style=expanded",
            "--source-map",
            "--watch" if "--watch" in sys.argv else "--no-watch",
        ]

        print(f"🔄 Compiling SASS: {main_scss} → {main_css}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ SASS compilation successful!")
            print(f"   📁 Output: {main_css}")
            if main_css_map.exists():
                print(f"   🗺️  Source map: {main_css_map}")
            return True
        else:
            print(f"❌ SASS compilation failed:")
            print(f"   Error: {result.stderr}")
            return False

    except FileNotFoundError:
        print("❌ SASS compiler not found. Please install sass:")
        print("   npm install -g sass")
        print("   or use Dart Sass: https://sass-lang.com/install")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during SASS compilation: {e}")
        return False


def compile_sass_production():
    """
    Compile SASS files to minified CSS for production.

    Returns:
        bool: True if compilation successful, False otherwise
    """
    # Get project root directory
    project_root = Path(__file__).parent
    scss_dir = project_root / "static" / "scss"
    css_dir = project_root / "static" / "css"

    # Ensure CSS directory exists
    css_dir.mkdir(parents=True, exist_ok=True)

    # Main SASS file
    main_scss = scss_dir / "main.scss"
    main_css_min = css_dir / "main.min.css"

    if not main_scss.exists():
        print(f"❌ Main SASS file not found: {main_scss}")
        return False

    try:
        # Compile compressed CSS for production
        cmd = [
            "sass",
            str(main_scss),
            str(main_css_min),
            "--style=compressed",
            "--no-source-map",
        ]

        print(f"🔄 Compiling SASS (production): {main_scss} → {main_css_min}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ Production SASS compilation successful!")
            print(f"   📁 Minified output: {main_css_min}")
            return True
        else:
            print(f"❌ Production SASS compilation failed:")
            print(f"   Error: {result.stderr}")
            return False

    except FileNotFoundError:
        print("❌ SASS compiler not found. Please install sass:")
        print("   npm install -g sass")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during production SASS compilation: {e}")
        return False


def watch_sass():
    """
    Watch SASS files for changes and compile automatically.
    """
    project_root = Path(__file__).parent
    scss_dir = project_root / "static" / "scss"
    css_dir = project_root / "static" / "css"

    # Ensure CSS directory exists
    css_dir.mkdir(parents=True, exist_ok=True)

    main_scss = scss_dir / "main.scss"
    main_css = css_dir / "main.css"

    if not main_scss.exists():
        print(f"❌ Main SASS file not found: {main_scss}")
        return False

    try:
        cmd = [
            "sass",
            "--watch",
            f"{scss_dir}:{css_dir}",
            "--style=expanded",
            "--source-map",
        ]

        print(f"👁️  Watching SASS files in {scss_dir}")
        print("   Press Ctrl+C to stop watching...")
        subprocess.run(cmd)

    except KeyboardInterrupt:
        print("\n🛑 SASS watching stopped.")
    except FileNotFoundError:
        print("❌ SASS compiler not found. Please install sass:")
        print("   npm install -g sass")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during SASS watching: {e}")
        return False


def main():
    """
    Main function to handle command line arguments.
    """
    if len(sys.argv) > 1:
        if sys.argv[1] == "--watch":
            watch_sass()
        elif sys.argv[1] == "--production":
            compile_sass_production()
        elif sys.argv[1] == "--help":
            print("SASS Compilation Script")
            print("Usage:")
            print("  python compile_sass.py           # Compile once")
            print("  python compile_sass.py --watch   # Watch for changes")
            print("  python compile_sass.py --production  # Minified output")
            print("  python compile_sass.py --help    # Show this help")
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Use --help for usage information")
    else:
        compile_sass()


if __name__ == "__main__":
    main()
