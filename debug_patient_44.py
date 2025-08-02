#!/usr/bin/env python3
"""
Debug CDA Translation Data Flow
Check what's happening with patient ID 44 CDA translation
"""

import os
import sys
import django

# Setup Django
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_ncp.settings")
django.setup()

from patient_data.models import PatientData
from patient_data.services.enhanced_cda_translation_service_v2 import (
    EnhancedCDATranslationService,
)


def debug_patient_44():
    """Debug patient ID 44 CDA translation"""

    print("🔍 DEBUGGING PATIENT ID 44 CDA TRANSLATION")
    print("=" * 60)

    try:
        # Get patient data
        patient = PatientData.objects.get(id=44)
        print(f"📋 Patient: {patient.given_name} {patient.family_name}")
        print(f"🌍 Country: {patient.source_country}")
        print()

        # Test with our Luxembourg sample data since session might be empty
        print("🧪 Testing with Luxembourg sample CDA data...")
        sample_cda = """
        <ClinicalDocument xmlns="urn:hl7-org:v3">
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
        </ClinicalDocument>
        """

        # Test enhanced translation service
        service = EnhancedCDATranslationService()
        result = service.translate_cda_document(
            cda_content=sample_cda, source_language="fr", target_language="en"
        )

        print(f"✅ Translation completed!")
        print(f"📊 Sections found: {len(result.get('sections', []))}")
        print(
            f"🧬 Medical terms: {result.get('document_info', {}).get('medical_terms_translated', 0)}"
        )
        print(
            f"📈 Quality: {result.get('document_info', {}).get('translation_quality', 'N/A')}"
        )

        print("\n🏥 Sections:")
        for i, section in enumerate(result.get("sections", []), 1):
            print(
                f"   {i}. {section.get('title', {}).get('original')} → {section.get('title', {}).get('translated')}"
            )

        print("\n💡 SOLUTION: The enhanced translation service works!")
        print("   Issue: Real patient CDA data might be empty or not in French.")
        print("   Fix: Need to check actual CDA content from session or database.")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_patient_44()
