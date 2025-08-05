#!/usr/bin/env python
"""Test the EU translation library"""

import os
import sys
import django
from pathlib import Path

# Setup Django environment
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.translation_utils import get_template_translations
from patient_data.services.eu_ui_translations import eu_ui_translations


def test_eu_translations():
    print("=== EU UI TRANSLATION LIBRARY TEST ===")

    # Test basic translations for different EU languages
    test_languages = ["de", "fr", "lv", "es", "it", "pl"]
    test_terms = ["name", "address", "email", "phone", "contact"]

    print("Basic UI term translations:")
    print("-" * 50)

    for lang in test_languages:
        print(f"\n{lang.upper()}:")
        for term in test_terms:
            translation = eu_ui_translations.get_translation(term, lang)
            print(f"  {term}: {translation}")

    print("\n" + "=" * 50)
    print("Template translations for different languages:")
    print("-" * 50)

    for lang in ["en", "de", "fr", "lv"]:
        print(f"\n{lang.upper()} template translations:")
        translations = get_template_translations("en", lang)
        ui_keys = ["name", "address", "email", "phone", "contact", "organization"]
        for key in ui_keys:
            print(f"  {key}: {translations.get(key, 'MISSING')}")


if __name__ == "__main__":
    test_eu_translations()
