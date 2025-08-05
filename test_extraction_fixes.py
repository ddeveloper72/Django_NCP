#!/usr/bin/env python3
"""
Test the fixed extraction capabilities for both authors and patient data.
"""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from patient_data.utils.flexible_cda_extractor import FlexibleCDAExtractor
from patient_data.utils.administrative_extractor import EnhancedAdministrativeExtractor


def test_extraction_fixes():
    """Test both author and patient extraction with our fixes."""

    # Use the same test file
    test_file = "test_data/eu_member_states/IT/2025-03-28T13-29-45.499822Z_CDA_EHDSI---PIVOT-CDA-(L1)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"

    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return

    print(f"🧪 Testing extraction fixes on: {test_file}")
    print("=" * 60)

    # Parse XML
    tree = ET.parse(test_file)
    root = tree.getroot()

    # Test FlexibleCDAExtractor
    print("🔧 FLEXIBLE CDA EXTRACTOR TEST:")
    flex_extractor = FlexibleCDAExtractor()

    # Test author extraction
    authors = flex_extractor.extract_author_flexible(root)
    print(f"  Authors found: {len(authors)}")
    for i, author in enumerate(authors, 1):
        print(f"    Author {i}:")
        print(f"      Name: {author.get('full_name', 'N/A')}")
        print(f"      Organization: {author.get('organization', 'N/A')}")
        print(f"      Time: {author.get('time', 'N/A')}")

    print()

    # Test EnhancedAdministrativeExtractor
    print("🏥 ENHANCED ADMINISTRATIVE EXTRACTOR TEST:")
    admin_extractor = EnhancedAdministrativeExtractor()

    # Test patient extraction
    patient_info = admin_extractor.extract_patient_contact_info(root)
    print(f"  Patient extraction results:")
    print(f"    Name: {patient_info.get('name', 'N/A')}")
    print(f"    Given name: {patient_info.get('given_name', 'N/A')}")
    print(f"    Family name: {patient_info.get('family_name', 'N/A')}")
    print(f"    Birth date: {patient_info.get('birth_date', 'N/A')}")
    print(f"    Gender: {patient_info.get('gender', 'N/A')}")
    print(f"    Patient ID: {patient_info.get('patient_id', 'N/A')}")

    # Test author extraction via admin extractor
    admin_authors = admin_extractor.extract_author_information(root)
    print(f"  Authors via admin extractor: {len(admin_authors)}")
    for i, author in enumerate(admin_authors, 1):
        print(f"    Author {i}:")
        print(f"      Name: {author.get('name', 'N/A')}")
        print(f"      Organization: {author.get('organization', 'N/A')}")
        print(f"      Contact: {len(author.get('contact_info', []))} contact methods")

    print()
    print("✅ Extraction test completed!")


if __name__ == "__main__":
    test_extraction_fixes()
