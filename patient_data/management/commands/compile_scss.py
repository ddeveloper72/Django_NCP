"""
Management command to compile SCSS to CSS using libsass
"""
import os
import sass
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Compile SCSS files to CSS using libsass'

    def handle(self, *args, **options):
        """Compile all SCSS files to CSS for production deployment"""
        # Define paths
        scss_path = Path(settings.BASE_DIR) / "static" / "scss"
        css_path = Path(settings.BASE_DIR) / "static" / "css"
        
        # Ensure output directory exists
        css_path.mkdir(parents=True, exist_ok=True)
        
        # Compile main.scss
        main_scss = scss_path / "main.scss"
        main_css = css_path / "main.css"
        
        # Delete old compiled CSS to force fresh compilation
        if main_css.exists():
            main_css.unlink()
            self.stdout.write(f"Removed old CSS: {main_css}")
        
        if main_scss.exists():
            self.stdout.write(f"Compiling {main_scss} → {main_css}...")
            
            try:
                # Compile SCSS to CSS with COMPRESSED output
                self.stdout.write('Compiling with output_style=compressed...')
                compiled_css = sass.compile(
                    filename=str(main_scss),
                    output_style='compressed',
                    include_paths=[str(scss_path)]
                )
                
                # Verify compression (compressed CSS should have no newlines)
                line_count = compiled_css.count('\n')
                is_minified = line_count < 10  # Compressed CSS should be ~1-5 lines max
                
                # Write compiled CSS with explicit newline at end (forces collectstatic to see it as changed)
                with open(main_css, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(compiled_css)
                
                # Force file modification timestamp update to ensure collectstatic copies it
                os.utime(main_css, None)
                
                status_msg = f'✓ Successfully compiled SCSS to CSS ({len(compiled_css)} bytes, {line_count} lines)'
                if is_minified:
                    status_msg += ' [COMPRESSED ✓]'
                else:
                    status_msg += ' [WARNING: NOT COMPRESSED!]'
                    self.stdout.write(self.style.WARNING('CSS is not minified - check libsass version'))
                
                self.stdout.write(self.style.SUCCESS(status_msg))
                self.stdout.write(f'File timestamp updated: {main_css}')
                
            except sass.CompileError as e:
                self.stdout.write(self.style.ERROR(f'✗ SCSS compilation error: {e}'))
                raise
                
        else:
            self.stdout.write(self.style.WARNING(f'⚠ SCSS file not found: {main_scss}'))
