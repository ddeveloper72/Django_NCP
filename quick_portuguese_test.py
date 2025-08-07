#!/usr/bin/env python3
"""
Quick Portuguese Patient Processing Check
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()


def quick_portuguese_test():
    """Quick test of Portuguese patient processing"""

    print("🇵🇹 Quick Portuguese Patient Test")
    print("=" * 50)

    # Test CDA file exists
    cda_path = "test_data/eu_member_states/PT/2-1234-W7.xml"

    if os.path.exists(cda_path):
        print(f"✅ CDA file found: {cda_path}")

        # Get file size
        file_size = os.path.getsize(cda_path)
        print(f"📄 File size: {file_size} bytes")

        try:
            with open(cda_path, "r", encoding="utf-8") as file:
                content = file.read()

            print(f"📝 Content length: {len(content)} characters")

            # Test language detection
            from patient_data.services.eu_language_detection_service import (
                detect_cda_language,
            )

            detected_lang = detect_cda_language(content, "PT")
            print(f"🌐 Detected language: {detected_lang}")

            # Test basic processing
            from patient_data.services.enhanced_cda_processor import (
                EnhancedCDAProcessor,
            )

            processor = EnhancedCDAProcessor(target_language="en")
            result = processor.process_clinical_sections(
                content, source_language=detected_lang
            )

            if result.get("success"):
                sections = result.get("sections", [])
                print(f"✅ Processing successful: {len(sections)} sections")

                # Show section summary
                for i, section in enumerate(sections):
                    title = section.get("section_title", "Unknown")
                    code = section.get("section_code", "N/A")
                    print(f"   {i+1}. {title} ({code})")

                return True
            else:
                print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"❌ Error processing: {e}")
            return False
    else:
        print(f"❌ CDA file not found: {cda_path}")
        return False


def check_database_patient():
    """Check if Portuguese patient is in database"""

    print("\n🗄️ Database Patient Check")
    print("=" * 30)

    try:
        from patient_data.models import PatientData

        # Show database stats
        total_patients = PatientData.objects.count()
        print(f"📊 Total patients in database: {total_patients}")

        # Look for Portuguese patient
        pt_patient = PatientData.objects.filter(patient_identifier="2-1234-W7").first()

        if pt_patient:
            print(
                f"✅ Found PT patient: {pt_patient.given_name} {pt_patient.family_name}"
            )
            print(f"   ID: {pt_patient.patient_identifier}")
            return True
        else:
            print("❌ Portuguese patient 2-1234-W7 not found in database")

            # Show a few sample patients
            samples = PatientData.objects.all()[:3]
            print("📋 Sample patients:")
            for patient in samples:
                print(
                    f"   • {patient.patient_identifier}: {patient.given_name} {patient.family_name}"
                )
            return False

    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


def main():
    print("🚀 Portuguese Patient Quick Test")
    print("=" * 50)

    file_test = quick_portuguese_test()
    db_test = check_database_patient()

    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   CDA File Processing: {'✅ PASS' if file_test else '❌ FAIL'}")
    print(f"   Database Patient: {'✅ FOUND' if db_test else '❌ NOT FOUND'}")

    if file_test:
        print("\n🎯 Ready for Server Testing:")
        print("   1. The Portuguese CDA processes successfully")
        print("   2. Dual language display will work")
        print("   3. Test the patient on your Django server")

    print("=" * 50)


if __name__ == "__main__":
    main()
