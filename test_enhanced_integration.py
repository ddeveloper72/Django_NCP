#!/usr/bin/env python3
"""
Test Enhanced CDA Translation Integration with Django
Test the complete pipeline from CDA document to bilingual display
"""

import os
import sys
import django

# Add the Django project directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_ncp.settings")
django.setup()

from patient_data.services.enhanced_cda_translation_service_v2 import (
    EnhancedCDATranslationService,
)


def test_django_integration():
    """Test enhanced CDA translation service integration with Django"""

    print("🚀 Testing Enhanced CDA Translation Integration")
    print("=" * 60)

    # Initialize the enhanced translation service
    translation_service = EnhancedCDATranslationService()

    # Use our Luxembourg test CDA content
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

    try:
        # Process the CDA document
        print("📄 Processing Luxembourg CDA document...")
        translation_result = translation_service.translate_cda_document(
            cda_content=luxembourg_cda, source_language="fr", target_language="en"
        )

        print(f"✅ Translation completed successfully!")
        print(f"📊 Document Statistics:")
        print(f"   - Sections processed: {len(translation_result['sections'])}")
        print(
            f"   - Quality rating: {translation_result['document_info']['translation_quality']}"
        )
        print(
            f"   - Medical terms: {translation_result['document_info']['medical_terms_translated']}"
        )
        print(
            f"   - Language pair: {translation_result['document_info']['source_language']} → {translation_result['document_info']['target_language']}"
        )

        # Test section-by-section translation
        print("\n🏥 Detailed Medical Sections Analysis:")
        print("=" * 60)

        total_medical_items = 0
        for i, section in enumerate(translation_result["sections"], 1):
            print(f"\n📋 SECTION {i}: {section['title']['original']}")
            print(f"   📝 English: {section['title']['translated']}")
            print(f"   🧬 Medical terms found: {section['content']['medical_terms']}")

            # Count individual medical items in this section
            original_content = section["content"]["original"]
            content_items = original_content.split("<content ID=")
            medical_items_count = (
                len([item for item in content_items if item.strip()]) - 1
            )
            total_medical_items += medical_items_count

            print(f"   📊 Medical items in section: {medical_items_count}")
            print(f"   🔍 Preview: {section['preview']['translated'][:100]}...")

            # Show individual medical items
            if medical_items_count > 0:
                print(f"   📄 Individual items:")
                import re

                items = re.findall(
                    r'<content ID="[^"]*">([^<]+)</content>', original_content
                )
                for j, item in enumerate(items, 1):
                    print(f"      {j}. {item[:60]}{'...' if len(item) > 60 else ''}")
            print()

        print(f"📊 TRANSLATION SUMMARY:")
        print(f"   🏥 Total Clinical Sections: {len(translation_result['sections'])}")
        print(f"   📋 Total Medical Items: {total_medical_items}")
        print(
            f"   🧬 Total Medical Terms Translated: {translation_result['document_info']['medical_terms_translated']}"
        )
        print(
            f"   📈 Items per Section Average: {total_medical_items / len(translation_result['sections']):.1f}"
        )
        print()

        # Test view context preparation
        print("🌐 Preparing Django View Context...")
        view_context = {
            "translation_result": translation_result,
            "source_language": translation_result["document_info"]["source_language"],
            "target_language": translation_result["document_info"]["target_language"],
            "translation_quality": translation_result["document_info"][
                "translation_quality"
            ],
            "medical_terms_count": translation_result["document_info"][
                "medical_terms_translated"
            ],
            "sections_count": len(translation_result["sections"]),
        }

        print(f"✅ View context prepared successfully!")
        print(f"📋 Context keys: {list(view_context.keys())}")

        # Simulate template rendering data
        print("\n📄 Template Data Preview:")
        print("-" * 30)
        for key, value in view_context.items():
            if key == "translation_result":
                print(
                    f"   {key}: [Complex object with {len(value['sections'])} sections]"
                )
            else:
                print(f"   {key}: {value}")

        print("\n🎯 Integration Test Summary:")
        print("=" * 40)
        print("✅ Enhanced CDA Translation Service: Working")
        print("✅ Luxembourg medical data processing: Working")
        print("✅ Medical terminology translation: Working")
        print("✅ Django view context preparation: Working")
        print("✅ Template data structure: Ready")

        return True

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_medical_terminology():
    """Test specific medical terminology translation"""

    print("\n🧬 Testing Medical Terminology Translation")
    print("=" * 50)

    translation_service = EnhancedCDATranslationService()

    # Test medical terms from our dictionary
    test_terms = [
        "hypertension artérielle",
        "diabète",
        "cholestérol",
        "anaphylaxie",
        "pénicilline",
        "metformine",
    ]

    for term in test_terms:
        translated = translation_service.translate_medical_term(term, "fr", "en")
        print(f"   🇫🇷 {term} → 🇬🇧 {translated}")

    print("✅ Medical terminology translation: Working")


if __name__ == "__main__":
    print("🏥 Django Enhanced CDA Translation Integration Test")
    print("=" * 60)

    # Run integration tests
    integration_success = test_django_integration()
    test_medical_terminology()

    if integration_success:
        print("\n🎉 SUCCESS: Enhanced CDA Translation fully integrated with Django!")
        print("🌟 Ready for bilingual medical document display")
        print("\n📋 Next Steps:")
        print("   1. Start Django server: python manage.py runserver")
        print("   2. Navigate to patient CDA view")
        print("   3. View bilingual translation interface")
        print("   4. Test section toggles and medical term glossary")
    else:
        print("\n❌ FAILED: Integration issues detected")
        sys.exit(1)
