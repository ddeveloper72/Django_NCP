#!/usr/bin/env python3
"""
Simple CDA Translation Demo
Focused test for the Luxembourg CDA document
"""

import sys
import os
from pathlib import Path
import re

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def simple_medical_translate(text):
    """Simple medical term translation"""
    medical_terms = {
        "médicamenteuse": "medication",
        "médicament": "medication",
        "allergie": "allergy",
        "allergies": "allergies",
        "traitement": "treatment",
        "patient": "patient",
        "maladie": "disease",
        "historique": "history",
        "prise": "intake",
        "effets": "effects",
        "indésirables": "adverse",
        "alertes": "alerts",
        "problème": "problem",
        "problèmes": "problems",
        "vaccination": "vaccination",
        "dispositif": "device",
        "médical": "medical",
        "implant": "implant",
    }

    result = text
    for french, english in medical_terms.items():
        result = re.sub(french, english, result, flags=re.IGNORECASE)

    return result


def extract_cda_sections(html_content):
    """Extract sections from Luxembourg CDA"""
    sections = []

    # Pattern for CDA sections
    pattern = r'<h3[^>]*title="([^"]*)"[^>]*>([^<]+)</h3>.*?<div[^>]*class="section-body"[^>]*>(.*?)</div>'
    matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)

    for i, (english_hint, french_title, content) in enumerate(matches):
        # Clean content
        clean_content = re.sub(r"<[^>]+>", " ", content)
        clean_content = re.sub(r"\s+", " ", clean_content).strip()

        # Translate
        translated_title = simple_medical_translate(french_title)
        translated_content = simple_medical_translate(clean_content)

        sections.append(
            {
                "id": i + 1,
                "french_title": french_title.strip(),
                "english_hint": english_hint.strip(),
                "translated_title": translated_title.strip(),
                "original_content": (
                    clean_content[:200] + "..."
                    if len(clean_content) > 200
                    else clean_content
                ),
                "translated_content": (
                    translated_content[:200] + "..."
                    if len(translated_content) > 200
                    else translated_content
                ),
            }
        )

    return sections


def main():
    print("Luxembourg CDA Translation Demo")
    print("=" * 50)

    # Load Luxembourg CDA file
    lu_file = (
        project_root / "test_data" / "eu_member_states" / "LU" / "DefaultXsltOutput.htm"
    )

    if not lu_file.exists():
        print(f"ERROR: File not found: {lu_file}")
        return

    # Read file
    with open(lu_file, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"Document loaded: {len(content):,} characters")

    # Extract sections
    sections = extract_cda_sections(content)
    print(f"Sections found: {len(sections)}")

    # Display each section
    for section in sections:
        print(f"\nSection {section['id']}: {section['french_title']}")
        print(f"   English hint: {section['english_hint']}")
        print(f"   Translated: {section['translated_title']}")
        print(f"   Original: {section['original_content']}")
        print(f"   Translated: {section['translated_content']}")

    print(f"\nDemo completed - {len(sections)} medical sections processed")
    print("Ready for Django integration!")


if __name__ == "__main__":
    main()
