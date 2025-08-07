#!/usr/bin/env python3
"""
Portuguese Patient Search Test - UI Simulation
Test the exact search process that the web UI uses
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


def test_portuguese_patient_search_ui():
    """Test the exact search process the UI uses"""

    print("🔍 Portuguese Patient UI Search Test")
    print("=" * 50)

    # These are the exact values you should enter in the web form
    country_code = "PT"
    patient_id = "2-1234-W7"

    print(f"🎯 Search Parameters:")
    print(f"   Country Code: {country_code}")
    print(f"   Patient ID: {patient_id}")

    try:
        from patient_data.services.patient_search_service import (
            EUPatientSearchService,
            PatientCredentials,
        )

        # Step 1: Create credentials (same as the form does)
        credentials = PatientCredentials(
            country_code=country_code,
            patient_id=patient_id,
        )

        print(f"\n✅ Created search credentials")

        # Step 2: Search for patient (same as views.py does)
        search_service = EUPatientSearchService()
        matches = search_service.search_patient(credentials)

        if matches:
            match = matches[0]

            print(f"\n🎉 PATIENT FOUND!")
            print(f"   Name: {match.given_name} {match.family_name}")
            print(f"   Birth Date: {match.birth_date}")
            print(f"   Gender: {match.gender}")
            print(f"   Country: {match.country_code}")
            print(f"   Patient ID: {match.patient_id}")
            print(f"   Confidence: {match.confidence_score * 100:.1f}%")

            # Check CDA availability
            print(f"\n📄 CDA Documents Available:")
            print(f"   L1 CDA: {'✅ Yes' if match.l1_cda_content else '❌ No'}")
            print(f"   L3 CDA: {'✅ Yes' if match.l3_cda_content else '❌ No'}")

            if match.l3_cda_content:
                print(f"   L3 Content Size: {len(match.l3_cda_content):,} characters")

            # Step 3: Generate session ID (same as views.py does)
            temp_patient_id = hash(f"{country_code}_{patient_id}") % 1000000
            print(f"\n🔗 Session Patient ID: {temp_patient_id}")

            print(f"\n✅ This patient should appear in the web UI!")

            return True
        else:
            print(f"\n❌ No patient found with these credentials")
            return False

    except Exception as e:
        print(f"❌ Error during search: {e}")
        import traceback

        traceback.print_exc()
        return False


def show_web_ui_instructions():
    """Show exact instructions for using the web UI"""

    print("\n📱 Web UI Search Instructions")
    print("=" * 50)

    print("1. 🌐 Open your Django server")
    print("   Navigate to: http://localhost:8000/patient_data/")

    print("\n2. 🔍 Use the Patient Search Form")
    print("   Fill in these EXACT values:")
    print("   ┌─────────────────────────────────┐")
    print("   │ Country Code: PT                │")
    print("   │ Patient ID: 2-1234-W7           │")
    print("   └─────────────────────────────────┘")

    print("\n3. 🔍 Click 'Search Patient'")
    print("   You should see:")
    print("   ✅ 'Patient documents found with 100.0% confidence in PT NCP!'")

    print("\n4. 📋 Patient Details Page")
    print("   You should see:")
    print("   • Name: Diana Ferreira")
    print("   • Birth Date: 1982-05-08")
    print("   • Gender: Female")
    print("   • Country: PT")
    print("   • Patient ID: 2-1234-W7")

    print("\n5. 📄 View CDA Document")
    print("   • Click 'View CDA Document' or 'L3 Browser View'")
    print("   • The Portuguese CDA should load with dual language support")

    print("\n6. 🇵🇹 Test Dual Language Features")
    print("   • Look for Portuguese | English section headers")
    print("   • Test the language toggle controls")
    print("   • Check responsive medication table layout")


def test_all_portuguese_patients():
    """Test all available Portuguese patients"""

    print("\n🇵🇹 All Portuguese Patients Available")
    print("=" * 50)

    try:
        from patient_data.services.cda_document_index import get_cda_indexer

        indexer = get_cda_indexer()
        all_patients = indexer.get_all_patients()

        # Filter Portuguese patients
        pt_patients = [p for p in all_patients if p["country_code"].upper() == "PT"]

        print(f"Found {len(pt_patients)} Portuguese patients:")

        for i, patient in enumerate(pt_patients, 1):
            print(f"\n{i}. Patient ID: {patient['patient_id']}")
            print(f"   Name: {patient['given_name']} {patient['family_name']}")
            print(f"   Birth Date: {patient['birth_date']}")
            print(f"   Gender: {patient['gender']}")
            print(
                f"   Documents: {patient['document_count']} ({', '.join(patient['cda_types'])})"
            )

            print(f"   🔍 Web UI Search:")
            print(f"      Country Code: PT")
            print(f"      Patient ID: {patient['patient_id']}")

        return pt_patients

    except Exception as e:
        print(f"❌ Error listing Portuguese patients: {e}")
        return []


def main():
    print("🇵🇹 Portuguese Patient Search Verification")
    print("=" * 80)

    # Test the main patient search
    search_success = test_portuguese_patient_search_ui()

    # Show all Portuguese patients
    pt_patients = test_all_portuguese_patients()

    # Show UI instructions
    show_web_ui_instructions()

    print("\n📊 SEARCH TEST RESULTS")
    print("=" * 40)
    print(
        f"Portuguese Patient Search: {'✅ SUCCESS' if search_success else '❌ FAILED'}"
    )
    print(f"Available PT Patients: {len(pt_patients)}")

    if search_success:
        print("\n🎉 Portuguese patient search is working correctly!")
        print("   The issue is not with the indexing or search system.")
        print("   Please check:")
        print("   1. You're using the correct search form")
        print("   2. You're entering 'PT' for country code")
        print("   3. You're entering '2-1234-W7' for patient ID")
        print("   4. Your Django server is running")
    else:
        print("\n⚠️  There may be an issue with the search system")

    print("=" * 80)


if __name__ == "__main__":
    main()
