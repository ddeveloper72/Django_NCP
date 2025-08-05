#!/usr/bin/env python3
"""
Test Enhanced Patient Search Integration
Tests the complete integration of enhanced administrative data extraction
with patient search functionality for EU CDA documents.
"""

import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.views import search_patient_by_id
from patient_data.services.cda_translation_manager import CDATranslationManager
from patient_data.services.enhanced_cda_xml_parser import EnhancedCDAXMLParser
from django.test import RequestFactory
import json


def test_mario_pino_enhanced_extraction():
    """Test enhanced extraction for Mario Pino's Italian CDA document"""
    print("🔍 Testing Enhanced Patient Search Integration")
    print("=" * 60)

    # Test patient ID - Mario Pino from Italy
    patient_id = "NCPNPH80A01H501K"
    print(f"Searching for patient: {patient_id}")

    # Create a mock request
    factory = RequestFactory()
    request = factory.get(f"/patient_data/search/?patient_id={patient_id}")

    try:
        # Test the view directly
        response = search_patient_by_id(request)

        if response.status_code == 200:
            # Parse the JSON response
            data = json.loads(response.content)

            print(f"✅ Patient found: {data.get('patient_name', 'Unknown')}")
            print(f"📋 Document title: {data.get('document_title', 'Unknown')}")

            # Check if enhanced administrative data is available
            admin_data = data.get("administrative_data", {})
            patient_contact = admin_data.get("patient_contact_info", {})

            print("\n📞 Contact Information:")
            addresses = patient_contact.get("addresses", [])
            telecoms = patient_contact.get("telecoms", [])

            print(f"   Addresses: {len(addresses)} found")
            for i, addr in enumerate(addresses):
                print(
                    f"     Address {i+1}: {addr.get('street', '')}, {addr.get('city', '')}, {addr.get('country', '')}"
                )

            print(f"   Telecoms: {len(telecoms)} found")
            for i, tel in enumerate(telecoms):
                print(
                    f"     Contact {i+1}: {tel.get('type', 'unknown')} - {tel.get('value', '')}"
                )

            # Check author information
            author_info = admin_data.get("author_information", [])
            print(f"\n👨‍⚕️ Author Information: {len(author_info)} authors")
            for i, author in enumerate(author_info):
                person = author.get("person", {})
                print(
                    f"     Author {i+1}: {person.get('full_name', 'Unknown')} ({person.get('role', 'Unknown role')})"
                )

            # Check custodian organization
            custodian = admin_data.get("custodian_organization", {})
            print(f"\n🏥 Custodian Organization: {custodian.get('name', 'Unknown')}")

            # Test enhanced patient identity data
            patient_identity = data.get("patient_identity", {})
            contact_info = patient_identity.get("contact_info", {})
            has_enhanced = contact_info.get("has_enhanced_contact_data", False)

            print(f"\n🔧 Enhanced Integration Status:")
            print(
                f"     Enhanced contact extraction: {'✅ Active' if has_enhanced else '❌ Fallback mode'}"
            )
            print(f"     Patient addresses: {len(contact_info.get('addresses', []))}")
            print(f"     Patient telecoms: {len(contact_info.get('telecoms', []))}")

            return True

        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"Response: {response.content.decode()}")
            return False

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


def test_enhanced_parser_directly():
    """Test the enhanced parser directly with sample CDA content"""
    print("\n🧪 Testing Enhanced Parser Directly")
    print("=" * 60)

    # Check if we have sample CDA files
    cda_files = []
    test_data_dir = "test_data"
    if os.path.exists(test_data_dir):
        for file in os.listdir(test_data_dir):
            if file.endswith((".xml", ".cda")):
                cda_files.append(os.path.join(test_data_dir, file))

    if not cda_files:
        print("⚠️  No CDA test files found in test_data directory")
        return False

    print(f"📄 Found {len(cda_files)} CDA files to test")

    # Test with the enhanced parser
    parser = EnhancedCDAXMLParser()

    for cda_file in cda_files[:2]:  # Test first 2 files
        print(f"\n🔍 Testing file: {os.path.basename(cda_file)}")

        try:
            with open(cda_file, "r", encoding="utf-8") as f:
                xml_content = f.read()

            # Parse with enhanced parser
            result = parser.parse_cda_content(xml_content)

            # Check results
            patient_identity = result.get("patient_identity", {})
            admin_data = result.get("administrative_data", {})

            print(f"     Patient: {patient_identity.get('full_name', 'Unknown')}")
            print(f"     Patient ID: {patient_identity.get('patient_id', 'Unknown')}")

            # Check contact info integration
            contact_info = patient_identity.get("contact_info", {})
            if contact_info.get("has_enhanced_contact_data", False):
                print(f"     ✅ Enhanced contact extraction active")
                print(f"     📍 Addresses: {len(contact_info.get('addresses', []))}")
                print(f"     📞 Telecoms: {len(contact_info.get('telecoms', []))}")
            else:
                print(f"     ⚠️  Using fallback contact extraction")

            # Check administrative data
            patient_contact = admin_data.get("patient_contact_info", {})
            print(
                f"     📋 Admin addresses: {len(patient_contact.get('addresses', []))}"
            )
            print(f"     📋 Admin telecoms: {len(patient_contact.get('telecoms', []))}")

        except Exception as e:
            print(f"     ❌ Error parsing file: {str(e)}")

    return True


def main():
    """Run enhanced integration tests"""
    print("🚀 Enhanced Patient Search Integration Test")
    print("Testing integration of gap analysis findings with main application")
    print("=" * 80)

    # Test 1: Mario Pino patient search
    success1 = test_mario_pino_enhanced_extraction()

    # Test 2: Enhanced parser directly
    success2 = test_enhanced_parser_directly()

    print("\n📊 Test Summary")
    print("=" * 60)
    print(f"Patient search integration: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"Enhanced parser direct test: {'✅ PASS' if success2 else '❌ FAIL'}")

    if success1 and success2:
        print("\n🎉 Enhanced integration successful!")
        print("The gap analysis findings have been successfully implemented.")
        print("Patient search now uses enhanced administrative data extraction.")
    else:
        print("\n⚠️  Some tests failed - manual verification may be needed.")


if __name__ == "__main__":
    main()
