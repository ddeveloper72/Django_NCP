#!/usr/bin/env python3
"""
Quick Luxembourg CDA Translation Analysis
Shows exactly what clinical sections and items we're translating
"""

import os
import sys
import django

# Setup Django
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_ncp.settings")
django.setup()

from patient_data.services.enhanced_cda_translation_service_v2 import (
    EnhancedCDATranslationService,
)


def analyze_luxembourg_translation():
    """Show exactly what we're translating from Luxembourg CDA"""

    print("🇱🇺 LUXEMBOURG PATIENT SUMMARY TRANSLATION ANALYSIS")
    print("=" * 65)

    # Our test Luxembourg CDA content
    luxembourg_cda = """
    <component>
        <section>
            <title>Historique médicamenteux</title>
            <text>
                <content ID="med1">Metformine 500mg - pour traitement du diabète</content>
                <content ID="med2">Atorvastatine 20mg - pour réduction du cholestérol</content>
                <content ID="med3">Lisinopril 10mg - pour hypertension artérielle</content>
            </text>
        </section>
    </component>
    <component>
        <section>
            <title>Allergies</title>
            <text>
                <content ID="allergy1">Allergie à la pénicilline - réaction cutanée</content>
                <content ID="allergy2">Allergie aux fruits de mer - anaphylaxie</content>
            </text>
        </section>
    </component>
    <component>
        <section>
            <title>Vaccinations</title>
            <text>
                <content ID="vacc1">Vaccin contre la grippe - administré en octobre 2023</content>
                <content ID="vacc2">Vaccin COVID-19 (Pfizer) - rappel en septembre 2023</content>
            </text>
        </section>
    </component>
    """

    # Initialize and process
    service = EnhancedCDATranslationService()
    result = service.translate_cda_document(luxembourg_cda, "fr", "en")

    print(f"📊 OVERALL STATISTICS:")
    print(f"   🏥 Total Clinical Sections: {len(result['sections'])}")
    print(
        f"   🧬 Total Medical Terms Translated: {result['document_info']['medical_terms_translated']}"
    )
    print(
        f"   📈 Translation Quality: {result['document_info']['translation_quality']}"
    )
    print()

    # Analyze each section
    total_items = 0
    for i, section in enumerate(result["sections"], 1):
        print(f"📋 SECTION {i}: {section['title']['original']}")
        print(f"   🇬🇧 Translation: {section['title']['translated']}")

        # Count items in this section
        import re

        original_content = section["content"]["original"]
        items = re.findall(r'<content ID="[^"]*">([^<]+)</content>', original_content)
        section_items = len(items)
        total_items += section_items

        print(f"   📊 Items in section: {section_items}")
        print(f"   🧬 Medical terms found: {section['content']['medical_terms']}")

        # Show each item
        for j, item in enumerate(items, 1):
            print(f"      {j}. 🇫🇷 {item}")
            # Try to translate this item
            translated_item = service.translate_medical_term(item, "fr", "en")
            if translated_item != item:  # If translation occurred
                print(f"         🇬🇧 {translated_item}")
        print()

    print(f"📈 SUMMARY:")
    print(f"   🏥 Clinical Sections: {len(result['sections'])}")
    print(f"   📋 Total Medical Items: {total_items}")
    print(
        f"   🧬 Medical Terms Translated: {result['document_info']['medical_terms_translated']}"
    )
    print(
        f"   📊 Average Items per Section: {total_items / len(result['sections']):.1f}"
    )

    return result


if __name__ == "__main__":
    analyze_luxembourg_translation()
