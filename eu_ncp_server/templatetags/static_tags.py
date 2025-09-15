import os
import time
from django import template
from django.templatetags.static import static
from django.conf import settings

register = template.Library()


@register.simple_tag
def static_versioned(path):
    """
    Generate a static file URL with automatic cache busting based on file modification time.
    Usage: {% static_versioned 'css/main.css' %}
    """
    # Get the static file URL
    static_url = static(path)

    # Get the absolute path to the static file
    if hasattr(settings, "STATICFILES_DIRS") and settings.STATICFILES_DIRS:
        # Development: check in STATICFILES_DIRS
        static_root = settings.STATICFILES_DIRS[0]
    else:
        # Production: check in STATIC_ROOT
        static_root = getattr(settings, "STATIC_ROOT", "")

    file_path = os.path.join(static_root, path)

    # Get file modification time as version number
    try:
        if os.path.exists(file_path):
            mtime = int(os.path.getmtime(file_path))
        else:
            # Fallback to current timestamp if file not found
            mtime = int(time.time())
    except (OSError, ValueError):
        # Fallback to current timestamp if any error
        mtime = int(time.time())

    # Return URL with version parameter
    return f"{static_url}?v={mtime}"
