#!/usr/bin/env python3
"""
Debug Portuguese Patient Name Extraction
Check why patient name shows as "Unknown Patient" instead of "Diana Ferreira"
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


def debug_patient_name_extraction():
    """Debug the patient name extraction process step by step"""

    print("🔍 Debugging Portuguese Patient Name Extraction")
    print("=" * 60)

    # Step 1: Read the CDA file directly
    cda_path = "test_data/eu_member_states/PT/2-1234-W7.xml"

    if not os.path.exists(cda_path):
        print(f"❌ CDA file not found: {cda_path}")
        return

    print(f"✅ CDA file found: {cda_path}")

    try:
        with open(cda_path, "r", encoding="utf-8") as file:
            cda_content = file.read()

        print(f"✅ CDA content loaded: {len(cda_content):,} characters")

        # Step 2: Test the patient extraction service directly
        from patient_data.services.patient_search_service import EUPatientSearchService

        search_service = EUPatientSearchService()
        patient_info = search_service.extract_patient_info_from_cda(cda_content)

        print(f"\n📋 Direct CDA extraction results:")
        print(f"   Given Name: '{patient_info.get('given_name', 'NOT FOUND')}'")
        print(f"   Family Name: '{patient_info.get('family_name', 'NOT FOUND')}'")
        print(f"   Birth Date: '{patient_info.get('birth_date', 'NOT FOUND')}'")
        print(f"   Gender: '{patient_info.get('gender', 'NOT FOUND')}'")

        # Step 3: Check the CDA document indexer
        from patient_data.services.cda_document_index import get_cda_indexer

        indexer = get_cda_indexer()
        documents = indexer.find_patient_documents("2-1234-W7", "PT")

        if documents:
            doc = documents[0]
            print(f"\n📊 CDA Index results:")
            print(f"   Given Name: '{doc.given_name}'")
            print(f"   Family Name: '{doc.family_name}'")
            print(f"   Birth Date: '{doc.birth_date}'")
            print(f"   Gender: '{doc.gender}'")
            print(f"   CDA Type: '{doc.cda_type}'")
            print(f"   File Path: '{doc.file_path}'")
        else:
            print(f"\n❌ No documents found in index")

        # Step 4: Test the full search process
        from patient_data.services.patient_search_service import PatientCredentials

        credentials = PatientCredentials(country_code="PT", patient_id="2-1234-W7")

        matches = search_service.search_patient(credentials)

        if matches:
            match = matches[0]
            print(f"\n🎯 Full search results:")
            print(f"   Given Name: '{match.given_name}'")
            print(f"   Family Name: '{match.family_name}'")
            print(f"   Birth Date: '{match.birth_date}'")
            print(f"   Gender: '{match.gender}'")
            print(f"   Patient Data: {match.patient_data}")
        else:
            print(f"\n❌ No matches found in full search")

        # Step 5: Test XML parsing manually
        import xml.etree.ElementTree as ET

        print(f"\n🔧 Manual XML parsing test:")
        root = ET.fromstring(cda_content)
        namespaces = {
            "hl7": "urn:hl7-org:v3",
            "ext": "urn:hl7-EE-DL-Ext:v1",
        }

        # Find patient name manually
        patient_role = root.find(".//hl7:patientRole", namespaces)
        if patient_role is not None:
            patient = patient_role.find("hl7:patient", namespaces)
            if patient is not None:
                name_elem = patient.find("hl7:name", namespaces)
                if name_elem is not None:
                    given_elem = name_elem.find("hl7:given", namespaces)
                    family_elem = name_elem.find("hl7:family", namespaces)

                    given_name = (
                        given_elem.text if given_elem is not None else "NOT FOUND"
                    )
                    family_name = (
                        family_elem.text if family_elem is not None else "NOT FOUND"
                    )

                    print(f"   Manual Given Name: '{given_name}'")
                    print(f"   Manual Family Name: '{family_name}'")
                else:
                    print(f"   ❌ Name element not found")
            else:
                print(f"   ❌ Patient element not found")
        else:
            print(f"   ❌ Patient role not found")

        # Step 6: Check what the views actually receive
        print(f"\n🌐 Testing what the web view would see:")

        # Simulate session storage like the views do
        temp_patient_id = hash(f"PT_2-1234-W7") % 1000000

        if matches:
            match = matches[0]
            session_data = {
                "patient_data": match.patient_data,
                "match_score": match.match_score,
                "confidence_score": match.confidence_score,
                "l1_cda_content": match.l1_cda_content,
                "l3_cda_content": match.l3_cda_content,
                "l1_cda_path": match.l1_cda_path,
                "l3_cda_path": match.l3_cda_path,
                "available_documents": match.available_documents,
                "file_path": getattr(match, "file_path", ""),
            }

            print(f"   Session Patient ID: {temp_patient_id}")
            print(f"   Session Patient Data:")
            for key, value in session_data["patient_data"].items():
                print(f"      {key}: '{value}'")

        return True

    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    print("🇵🇹 Portuguese Patient Name Extraction Debug")
    print("=" * 80)

    success = debug_patient_name_extraction()

    if success:
        print("\n✅ Debug completed successfully")
        print("Check the output above to identify where the name extraction fails")
    else:
        print("\n❌ Debug failed - check error messages above")

    print("=" * 80)


if __name__ == "__main__":
    main()
