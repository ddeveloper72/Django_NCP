#!/usr/bin/env python3
"""
Test script to verify patient demographics extraction from Malta PS document
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.services.enhanced_cda_processor import EnhancedCDAProcessor


def test_malta_patient_demographics():
    """Test Malta PS document patient demographics extraction"""

    # Load Malta PS document
    malta_file_path = "test_data/Malta PS Documents/Mario_Borg_9999002M_3.xml"

    print("🧪 Testing Malta PS Patient Demographics Extraction")
    print("=" * 55)

    if not os.path.exists(malta_file_path):
        print(f"❌ Malta test file not found: {malta_file_path}")
        return False

    try:
        # Read the XML content
        with open(malta_file_path, "r", encoding="utf-8") as f:
            cda_content = f.read()

        print(f"✅ Loaded Malta PS document: {len(cda_content)} characters")

        # Initialize Enhanced CDA Processor
        processor = EnhancedCDAProcessor(target_language="en")

        print("\n🔄 Processing document with Enhanced CDA Processor...")

        # Process the document
        result = processor.process_clinical_sections(cda_content, source_language="en")

        if result.get("success"):
            print("✅ Document processing successful!")

            # Check patient identity extraction
            patient_identity = result.get("patient_identity", {})
            print(f"\n👤 Patient Identity Extracted:")
            print(f"   - Given Name: {patient_identity.get('given_name', 'Not found')}")
            print(
                f"   - Family Name: {patient_identity.get('family_name', 'Not found')}"
            )
            print(f"   - Birth Date: {patient_identity.get('birth_date', 'Not found')}")
            print(f"   - Gender: {patient_identity.get('gender', 'Not found')}")
            print(
                f"   - Primary Patient ID: {patient_identity.get('primary_patient_id', 'Not found')}"
            )
            print(
                f"   - Secondary Patient ID: {patient_identity.get('secondary_patient_id', 'Not found')}"
            )

            # Check patient identifiers array
            identifiers = patient_identity.get("patient_identifiers", [])
            print(f"\n🔢 Patient Identifiers ({len(identifiers)} found):")
            for i, identifier in enumerate(identifiers, 1):
                print(
                    f"   {i}. {identifier.get('type', 'Unknown')} ID: {identifier.get('extension', 'N/A')}"
                )
                print(f"      Root: {identifier.get('root', 'N/A')}")

            # Check administrative data
            admin_data = result.get("administrative_data", {})
            has_admin_data = result.get("has_administrative_data", False)
            print(f"\n📋 Administrative Data (Present: {has_admin_data}):")
            print(
                f"   - Document Date: {admin_data.get('document_creation_date', 'Not found')}"
            )
            print(
                f"   - Author: {admin_data.get('author_hcp', {}).get('family_name', 'Not found')}"
            )
            print(
                f"   - Organization: {admin_data.get('author_hcp', {}).get('organization', {}).get('name', 'Not found')}"
            )
            print(
                f"   - Custodian: {admin_data.get('custodian_organization', {}).get('name', 'Not found')}"
            )

            # Check clinical sections
            sections = result.get("sections", [])
            print(f"\n🏥 Clinical Sections: {len(sections)} found")
            for i, section in enumerate(sections[:3], 1):  # Show first 3 sections
                title = section.get("title", "Unknown")
                print(f"   {i}. {title}")

            # Summary
            print(f"\n📊 Processing Summary:")
            print(f"   - Sections: {result.get('sections_count', 0)}")
            print(f"   - Medical terms: {result.get('medical_terms_count', 0)}")
            print(f"   - Coded sections: {result.get('coded_sections_count', 0)}")
            print(f"   - Patient IDs found: {len(identifiers)}")

            return True

        else:
            print(
                f"❌ Document processing failed: {result.get('error', 'Unknown error')}"
            )
            return False

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_malta_patient_demographics()
    if success:
        print("\n🎉 Malta patient demographics extraction test completed!")
    else:
        print("\n💥 Malta patient demographics extraction test failed!")
        sys.exit(1)
