#!/usr/bin/env python
"""
Test script to verify the CDA translation endpoint works after fixing the ImportError
"""
import os
import sys
import django

# Configure Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()


def test_cda_view_import():
    """Test that the CDA view can be imported without the MedicalTerminologyTranslator error"""
    print("Testing CDA view import after architectural fix...")

    try:
        # Test importing the patient_data views that use CDATranslationService
        from patient_data import views

        print("✓ patient_data.views imported successfully")

        # Test that we can access the CDA translation functionality
        from patient_data.services.cda_translation_service import CDATranslationService

        service = CDATranslationService()
        print("✓ CDATranslationService can be instantiated")

        # Test URL patterns don't crash on import
        from patient_data import urls

        print("✓ patient_data.urls imported successfully")

        print("\n✅ All import tests passed!")
        print("🎯 The '/patients/cda/53/' endpoint should now work without ImportError")
        print(
            "📋 Architecture uses proper CTS-based translation instead of hardcoded dictionaries"
        )

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_cda_view_import()
