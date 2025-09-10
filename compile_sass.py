#!/usr/bin/env python
"""
SASS Compiler for Django NCP Project
Compiles SASS files to CSS with auto-watching and production builds
"""
import os
import sys
import time
import argparse
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sass


class SassCompiler:
    def __init__(self, watch=False, production=False):
        self.base_dir = Path(__file__).parent
        self.sass_dir = self.base_dir / "static" / "scss"
        self.css_dir = self.base_dir / "static" / "css"
        self.staticfiles_dir = self.base_dir / "staticfiles" / "css"
        self.main_sass = self.sass_dir / "main.scss"
        self.main_css = self.css_dir / "main.css"
        self.watch = watch
        self.production = production

        # Ensure directories exist
        self.css_dir.mkdir(parents=True, exist_ok=True)
        self.staticfiles_dir.mkdir(parents=True, exist_ok=True)

    def compile_sass(self):
        """Compile main SASS file to CSS"""
        try:
            print(f"🔄 Compiling SASS: {self.main_sass} -> {self.main_css}")

            # SASS compilation options
            output_style = "compressed" if self.production else "expanded"

            # Compile SASS to CSS
            compilation_result = sass.compile(
                filename=str(self.main_sass),
                output_style=output_style,
                include_paths=[str(self.sass_dir)],
                source_map_filename=(
                    str(self.main_css) + ".map" if not self.production else None
                ),
            )

            # Handle result - could be string or tuple
            if isinstance(compilation_result, tuple):
                css_content, source_map = compilation_result
            else:
                css_content = compilation_result

            # Write CSS file
            with open(self.main_css, "w", encoding="utf-8") as f:
                f.write(css_content)

            # Copy to staticfiles for production
            if self.production:
                staticfiles_css = self.staticfiles_dir / "main.css"
                with open(staticfiles_css, "w", encoding="utf-8") as f:
                    f.write(css_content)
                print(f"✅ Production CSS written to: {staticfiles_css}")

            print(f"✅ SASS compiled successfully!")
            return True

        except Exception as e:
            print(f"❌ SASS compilation failed: {e}")
            return False

    def start_watching(self):
        """Start watching SASS files for changes"""

        class SassEventHandler(FileSystemEventHandler):
            def __init__(self, compiler):
                self.compiler = compiler

            def on_modified(self, event):
                if event.is_directory:
                    return
                if event.src_path.endswith(".scss"):
                    print(f"📝 SASS file changed: {event.src_path}")
                    self.compiler.compile_sass()

        event_handler = SassEventHandler(self)
        observer = Observer()
        observer.schedule(event_handler, str(self.sass_dir), recursive=True)
        observer.start()

        print(f"👀 Watching SASS files in: {self.sass_dir}")
        print("Press Ctrl+C to stop watching...")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            print("\n🛑 Stopped watching SASS files")
        observer.join()


def main():
    parser = argparse.ArgumentParser(description="Compile SASS files for Django NCP")
    parser.add_argument(
        "--watch",
        "-w",
        action="store_true",
        help="Watch for changes and recompile automatically",
    )
    parser.add_argument(
        "--production",
        "-p",
        action="store_true",
        help="Compile for production (compressed, no source maps)",
    )

    args = parser.parse_args()

    compiler = SassCompiler(watch=args.watch, production=args.production)

    # Initial compilation
    success = compiler.compile_sass()

    if not success:
        sys.exit(1)

    # Start watching if requested
    if args.watch:
        compiler.start_watching()


if __name__ == "__main__":
    main()
