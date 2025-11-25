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
        """Compile all SCSS files to CSS"""
        # Define paths
        scss_path = Path(settings.BASE_DIR) / "static" / "scss"
        css_path = Path(settings.BASE_DIR) / "static" / "css"
        
        # Ensure output directory exists
        css_path.mkdir(parents=True, exist_ok=True)
        
        # Compile main.scss
        main_scss = scss_path / "main.scss"
        main_css = css_path / "main.css"
        
        if main_scss.exists():
            self.stdout.write(f"Compiling {main_scss} → {main_css}...")
            
            try:
                # Compile SCSS to CSS
                compiled_css = sass.compile(
                    filename=str(main_scss),
                    output_style='compressed',
                    include_paths=[str(scss_path)]
                )
                
                # Write compiled CSS
                with open(main_css, 'w', encoding='utf-8') as f:
                    f.write(compiled_css)
                
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Successfully compiled SCSS to CSS ({len(compiled_css)} bytes)'
                ))
                
            except sass.CompileError as e:
                self.stdout.write(self.style.ERROR(f'✗ SCSS compilation error: {e}'))
                raise
                
        else:
            self.stdout.write(self.style.WARNING(f'⚠ SCSS file not found: {main_scss}'))
