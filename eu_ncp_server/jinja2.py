from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from django.template.context_processors import csrf
from jinja2 import Environment


def environment(**options):
    """
    Jinja2 environment factory for Django integration.
    This function is referenced in Django settings TEMPLATES configuration.
    """
    env = Environment(**options)

    # Add Django's static and url functions to Jinja2 global namespace
    env.globals.update(
        {
            "static": staticfiles_storage.url,
            "url": reverse,
        }
    )

    return env
