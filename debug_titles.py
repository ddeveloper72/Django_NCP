#!/usr/bin/env python3
"""
Debug section title extraction
"""

import os
import sys
import django

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.services.enhanced_cda_processor import EnhancedCDAProcessor
from bs4 import BeautifulSoup


def debug_title_extraction():
    """Debug exactly what's happening with title extraction"""

    print("🔍 DEBUGGING TITLE EXTRACTION")
    print("=" * 40)

    test_html = """
    <html>
    <body>
        <h2>Résumé des médicaments</h2>
        <p>Some medication content</p>
        
        <div class="medication-section" data-code="10160-0">
            <h2>Liste des médicaments</h2>
            <table><tr><td>Drug info</td></tr></table>
        </div>
    </body>
    </html>
    """

    # Parse with BeautifulSoup to see what the processor sees
    soup = BeautifulSoup(test_html, "html.parser")

    # Find section elements as the processor does
    section_elements = soup.find_all(
        ["div", "section"],
        class_=lambda x: x and "section" in x.lower() if x else False,
    )

    if not section_elements:
        section_elements = soup.find_all(["h1", "h2", "h3", "h4"])

    print(f"Found {len(section_elements)} potential sections:")

    for i, elem in enumerate(section_elements):
        print(f"\nSection {i+1}:")
        print(f"  Element: {elem.name}")
        print(f"  Class: {elem.get('class', 'No class')}")
        print(f"  Data-code: {elem.get('data-code', 'No data-code')}")
        print(f"  ID: {elem.get('id', 'No ID')}")

        # Get section title as the processor does
        if elem.name in ["h1", "h2", "h3", "h4"]:
            section_title = elem.get_text().strip()
            content_elem = elem.find_next_sibling()
            print(f"  Title (from heading): {section_title}")
            print(f"  Next sibling: {content_elem.name if content_elem else 'None'}")
        else:
            title_elem = elem.find(["h1", "h2", "h3", "h4"])
            section_title = (
                title_elem.get_text().strip() if title_elem else f"Section {i + 1}"
            )
            content_elem = elem
            print(f"  Title (from div): {section_title}")
            print(f"  Content element: {content_elem.name if content_elem else 'None'}")

    # Now test the actual processor
    print(f"\n🔧 TESTING ENHANCED PROCESSOR:")

    try:
        processor = EnhancedCDAProcessor(target_language="en")
        result = processor.process_clinical_sections(test_html, "fr")

        sections = result.get("sections", [])
        print(f"Processor found {len(sections)} sections:")

        for i, section in enumerate(sections):
            title_info = section.get("title", {})
            print(f"  Section {i+1}:")
            print(f"    Original: '{title_info.get('source', 'MISSING')}'")
            print(f"    Translated: '{title_info.get('target', 'MISSING')}'")
            print(f"    Section code: '{section.get('section_code', 'N/A')}'")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_title_extraction()
