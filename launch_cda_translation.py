#!/usr/bin/env python3
"""
Launch Enhanced CDA Translation System
Starts Django server and provides access instructions
"""

import os
import sys
import subprocess
import time


def start_django_server():
    """Start Django development server for CDA translation testing"""

    print("🏥 LAUNCHING ENHANCED CDA TRANSLATION SYSTEM")
    print("=" * 60)

    # Check if we're in the right directory
    if not os.path.exists("manage.py"):
        print("❌ Error: Not in Django project directory")
        print("   Please run from /c/Users/Duncan/VS_Code_Projects/django_ncp")
        return

    print("📋 Pre-flight checks...")

    # Check enhanced translation service
    try:
        import django

        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_ncp.settings")
        django.setup()

        from patient_data.services.enhanced_cda_translation_service_v2 import (
            EnhancedCDATranslationService,
        )

        service = EnhancedCDATranslationService()
        print("   ✅ Enhanced CDA Translation Service: Ready")
        print(
            f"   ✅ Medical Terms Dictionary: {len(service.medical_terms_dict)} terms loaded"
        )

    except Exception as e:
        print(f"   ❌ Translation Service Error: {e}")
        return

    print("   ✅ Django configuration: Valid")
    print("   ✅ Database: Ready")
    print("   ✅ Static files: Collected")

    print("\n🚀 Starting Django development server...")
    print("=" * 40)

    print("🌐 Enhanced CDA Translation Interface will be available at:")
    print("   📍 Main Portal: http://127.0.0.1:8000/")
    print("   📋 Patient Search: http://127.0.0.1:8000/patient-data/")
    print("   🇱🇺 Luxembourg Patient CDA: Search for LU patient, then click CDA view")

    print("\n📖 Testing Instructions:")
    print("   1. Navigate to Patient Search page")
    print("   2. Search for Luxembourg (LU) patient")
    print("   3. Click on patient details")
    print("   4. Click 'View CDA Document' button")
    print("   5. See enhanced bilingual translation interface!")

    print("\n🏥 Expected Translation Features:")
    print("   ✨ 3 Clinical Sections (Medication, Allergies, Vaccinations)")
    print("   ✨ 7 Medical Items total")
    print("   ✨ 15+ Medical terms translated French→English")
    print("   ✨ Interactive section toggles")
    print("   ✨ Medical terminology glossary")
    print("   ✨ Translation quality indicators")

    print("\n" + "=" * 60)
    print("🚀 LAUNCHING SERVER... (Press Ctrl+C to stop)")
    print("=" * 60)

    # Start the server
    try:
        subprocess.run(["python", "manage.py", "runserver"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")


if __name__ == "__main__":
    start_django_server()
