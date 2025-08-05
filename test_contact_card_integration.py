#!/usr/bin/env python3
"""
Test the complete contact card integration with fixed extractors.
"""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from patient_data.utils.administrative_extractor import EnhancedAdministrativeExtractor
from patient_data.utils.contact_card_parser import ContactCardCompatibleParser


def test_contact_card_integration():
    """Test the complete contact card pipeline with our fixes."""

    test_file = "test_data/eu_member_states/IT/2025-03-28T13-29-45.499822Z_CDA_EHDSI---PIVOT-CDA-(L1)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"

    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return

    print(f"🧪 Testing complete contact card integration")
    print("=" * 60)

    # Parse XML
    tree = ET.parse(test_file)
    root = tree.getroot()

    # Extract administrative data
    print("📋 STEP 1: Extract administrative data...")
    admin_extractor = EnhancedAdministrativeExtractor()
    administrative_data = admin_extractor.extract_administrative_section(root)

    print(
        f"   Patient info: {administrative_data.get('patient', {}).get('name', 'N/A')}"
    )
    print(f"   Authors: {len(administrative_data.get('authors', []))}")
    print(
        f"   Legal authenticators: {len(administrative_data.get('legal_authenticators', []))}"
    )
    print(f"   Custodians: {len(administrative_data.get('custodians', []))}")

    # Transform for contact cards
    print("🔄 STEP 2: Transform to contact card format...")
    parser = ContactCardCompatibleParser()
    administrative_info = parser.parse_administrative_data(administrative_data)

    print(
        f"   Contact entities: {len(administrative_info.get('contact_entities', []))}"
    )

    # Display contact entities
    print("👥 STEP 3: Contact entities for contact cards:")
    for i, entity in enumerate(administrative_info.get("contact_entities", []), 1):
        print(f"   Entity {i}:")
        print(f"     Name: {entity.get('name', 'N/A')}")
        print(f"     Title: {entity.get('title', 'N/A')}")
        print(f"     Organization: {entity.get('organization', 'N/A')}")
        print(f"     Contact methods: {len(entity.get('contact_info', []))}")

        # Show first contact method if available
        contacts = entity.get("contact_info", [])
        if contacts:
            contact = contacts[0]
            print(
                f"       Primary contact: {contact.get('type', 'N/A')} - {contact.get('display_value', 'N/A')}"
            )

    # Show patient info in contact card format
    patient_info = administrative_info.get("patient_info", {})
    if patient_info.get("name"):
        print("🏥 PATIENT INFO for contact card:")
        print(f"   Name: {patient_info.get('name', 'N/A')}")
        print(f"   Birth date: {patient_info.get('birth_date', 'N/A')}")
        print(f"   Gender: {patient_info.get('gender', 'N/A')}")
        print(f"   ID: {patient_info.get('patient_id', 'N/A')}")

    print()
    print("✅ Contact card integration test completed!")

    # Show summary
    total_entities = len(administrative_info.get("contact_entities", []))
    has_patient = bool(patient_info.get("name"))

    print("📊 SUMMARY:")
    print(f"   Total contact entities ready for display: {total_entities}")
    print(f"   Patient information available: {'Yes' if has_patient else 'No'}")
    print(
        f"   Contact card system: {'Ready' if total_entities > 0 or has_patient else 'No data'}"
    )


if __name__ == "__main__":
    test_contact_card_integration()
