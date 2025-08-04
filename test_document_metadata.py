#!/usr/bin/env python3
"""
Test Document Metadata Extraction for Last Update Information
Critical for healthcare professionals to assess data currency
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.services.cda_administrative_extractor import (
    CDAAdministrativeExtractor,
)


def test_document_metadata():
    """Test document metadata extraction"""
    print("🏥 Testing Document Metadata Extraction")
    print("=" * 60)

    # Sample CDA with document metadata
    sample_cda = """<?xml version="1.0" encoding="UTF-8"?>
    <ClinicalDocument xmlns="urn:hl7-org:v3">
        <id extension="44" root="2.16.840.1.113883.2.1.4.5.2.1"/>
        <effectiveTime value="20230925141338+0200"/>
        <setId root="2.16.840.1.113883.2.1.4.5.2.1.44"/>
        <versionNumber value="1"/>
        
        <documentationOf>
            <serviceEvent>
                <effectiveTime>
                    <low value="20230925141338+0200"/>
                    <high value="20230925141338+0200"/>
                </effectiveTime>
            </serviceEvent>
        </documentationOf>
        
        <author>
            <time value="20230925141338+0200"/>
        </author>
    </ClinicalDocument>"""

    extractor = CDAAdministrativeExtractor()
    admin_data = extractor.extract_from_xml(sample_cda)

    print(f"📅 Document Creation Date: {admin_data.document_creation_date}")
    print(f"🔄 Last Update of Information: {admin_data.document_last_update_date}")
    print(f"📝 Document Version: {admin_data.document_version_number}")
    print(f"🆔 Document Set ID: {admin_data.document_set_id}")

    print("\n" + "=" * 60)

    # Test with updated document
    updated_cda = """<?xml version="1.0" encoding="UTF-8"?>
    <ClinicalDocument xmlns="urn:hl7-org:v3">
        <id extension="44" root="2.16.840.1.113883.2.1.4.5.2.1"/>
        <effectiveTime value="20230925141338+0200"/>
        <setId root="2.16.840.1.113883.2.1.4.5.2.1.44"/>
        <versionNumber value="2"/>
        
        <documentationOf>
            <serviceEvent>
                <effectiveTime>
                    <low value="20230925141338+0200"/>
                    <high value="20231015093022+0200"/>
                </effectiveTime>
            </serviceEvent>
        </documentationOf>
        
        <author>
            <time value="20231015093022+0200"/>
        </author>
    </ClinicalDocument>"""

    print("🔄 Testing Updated Document:")
    updated_admin_data = extractor.extract_from_xml(updated_cda)

    print(f"📅 Document Creation Date: {updated_admin_data.document_creation_date}")
    print(
        f"🔄 Last Update of Information: {updated_admin_data.document_last_update_date}"
    )
    print(f"📝 Document Version: {updated_admin_data.document_version_number}")

    # Verify critical information for healthcare professionals
    if (
        updated_admin_data.document_last_update_date
        != updated_admin_data.document_creation_date
    ):
        print("✅ CRITICAL: Document has been updated since creation")
        print("   Healthcare professionals should note information currency")
    else:
        print("ℹ️  INFO: Document unchanged since creation")

    print("\n🏥 Document metadata extraction test completed successfully!")


if __name__ == "__main__":
    test_document_metadata()
