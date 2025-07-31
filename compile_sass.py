#!/usr/bin/env python
import os
import django
from django.conf import settings

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

import sass


def compile_sass_file():
    try:
        # Compile the main SASS file
        sass_input = "staticfiles/scss/main.scss"
        css_output = "static/css/main.css"

        # Ensure output directory exists
        os.makedirs(os.path.dirname(css_output), exist_ok=True)

        # Compile SASS to CSS
        with open(sass_input, "r", encoding="utf-8") as f:
            sass_content = f.read()

        compiled_css = sass.compile(
            string=sass_content,
            include_paths=["staticfiles/scss/"],
            output_style="compressed",
        )

        # Write the compiled CSS
        with open(css_output, "w", encoding="utf-8") as f:
            f.write(compiled_css)

        print(f"✅ Successfully compiled {sass_input} to {css_output}")

    except Exception as e:
        print(f"❌ Error compiling SASS: {e}")


if __name__ == "__main__":
    compile_sass_file()
