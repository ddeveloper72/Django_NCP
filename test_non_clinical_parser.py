#!/usr/bin/env python3
"""
Test Non-Clinical CDA Parser
Test the comprehensive non-clinical data extraction
"""

import os
import sys
import django
from pathlib import Path

# Add the Django project path
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.services.non_clinical_cda_parser import NonClinicalCDAParser


def test_non_clinical_parser():
    """Test the non-clinical parser on Italian CDA document"""

    print("🧪 TESTING NON-CLINICAL CDA PARSER")
    print("=" * 70)

    # Test with Italian L3 file
    test_file = Path(
        "test_data/eu_member_states/IT/2025-03-28T13-29-59.727799Z_CDA_EHDSI---FRIENDLY-CDA-(L3)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"
    )

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return

    print(f"📄 Testing: {test_file.name}")

    # Read CDA content
    with open(test_file, "r", encoding="utf-8") as f:
        xml_content = f.read()

    print(f"📊 CDA Content Length: {len(xml_content)} characters")

    # Initialize the non-clinical parser
    parser = NonClinicalCDAParser()

    print("\\n🔄 Processing with Non-Clinical Parser...")

    # Parse the CDA content
    result = parser.parse_cda_content(xml_content)

    print(f"\\n✅ PARSING RESULTS:")
    print("-" * 70)

    if result.get("success"):
        print("✅ Non-clinical parsing successful!")

        # 1. DOCUMENT METADATA
        doc_metadata = result.get("document_metadata")
        if doc_metadata:
            print(f"\\n📋 DOCUMENT METADATA:")
            print(f"   📄 Title: {doc_metadata.title}")
            print(f"   🆔 Document ID: {doc_metadata.document_id}")
            print(f"   📅 Creation Date: {doc_metadata.creation_date}")
            print(
                f"   🏷️  Document Type: {doc_metadata.document_type_display} ({doc_metadata.document_type_code})"
            )
            print(
                f"   🔒 Confidentiality: {doc_metadata.confidentiality_display} ({doc_metadata.confidentiality_code})"
            )
            print(f"   🌍 Language: {doc_metadata.language_code}")
            if doc_metadata.related_documents:
                print(f"   🔗 Related Documents: {len(doc_metadata.related_documents)}")

        # 2. PATIENT DEMOGRAPHICS
        patient_demo = result.get("patient_demographics")
        if patient_demo:
            print(f"\\n👤 PATIENT DEMOGRAPHICS:")
            print(f"   👨‍💼 Name: {patient_demo.full_name}")
            print(f"   🆔 Patient ID: {patient_demo.patient_id}")
            print(f"   🎂 Birth Date: {patient_demo.birth_date}")
            print(
                f"   ⚧️  Gender: {patient_demo.gender_display} ({patient_demo.gender_code})"
            )
            print(f"   🏠 Address: {patient_demo.formatted_address}")
            if patient_demo.telecom:
                print(f"   📞 Contact: {len(patient_demo.telecom)} methods")

        # 3. HEALTHCARE PROVIDERS
        providers = result.get("healthcare_providers", [])
        if providers:
            print(f"\\n👩‍⚕️ HEALTHCARE PROVIDERS ({len(providers)}):")
            for i, provider in enumerate(providers, 1):
                print(f"   Provider {i}:")
                print(f"      👨‍💼 Name: {provider.full_name}")
                print(f"      🆔 ID: {provider.provider_id}")
                print(f"      🏥 Organization: {provider.organization_name}")
                if provider.timestamp:
                    print(f"      ⏰ Timestamp: {provider.timestamp}")

        # 4. CUSTODIAN INFORMATION
        custodian = result.get("custodian_information")
        if custodian and custodian.organization_name:
            print(f"\\n🏥 CUSTODIAN INFORMATION:")
            print(f"   🏢 Organization: {custodian.organization_name}")
            print(f"   🆔 ID: {custodian.organization_id}")
            if custodian.address:
                print(f"   🏠 Address: {custodian.address}")
            if custodian.telecom:
                print(f"   📞 Contact: {len(custodian.telecom)} methods")

        # 5. LEGAL AUTHENTICATOR
        legal_auth = result.get("legal_authenticator")
        if legal_auth and legal_auth.full_name:
            print(f"\\n⚖️ LEGAL AUTHENTICATOR:")
            print(f"   👨‍💼 Name: {legal_auth.full_name}")
            print(f"   🆔 ID: {legal_auth.authenticator_id}")
            print(f"   ⏰ Authentication Time: {legal_auth.authentication_time}")
            print(f"   ✍️ Signature Code: {legal_auth.signature_code}")
            if legal_auth.organization_name:
                print(f"   🏥 Organization: {legal_auth.organization_name}")

        # 6. DOCUMENT STRUCTURE
        doc_structure = result.get("document_structure", {})
        if doc_structure:
            print(f"\\n📑 DOCUMENT STRUCTURE:")
            print(f"   📋 Total Sections: {doc_structure.get('total_sections', 0)}")

            section_types = doc_structure.get("section_types", {})
            if section_types:
                print(f"   📊 Section Types:")
                for section_type, count in sorted(section_types.items()):
                    print(f"      - {section_type}: {count}")

        # 7. PARSING STATISTICS
        stats = result.get("parsing_stats", {})
        if stats:
            print(f"\\n📊 PARSING STATISTICS:")
            print(f"   📋 Total Sections: {stats.get('total_sections', 0)}")
            print(f"   👤 Has Patient Data: {stats.get('has_patient_data', False)}")
            print(f"   👩‍⚕️ Has Authors: {stats.get('has_authors', False)}")
            print(f"   🏥 Has Custodian: {stats.get('has_custodian', False)}")
            print(f"   ⚖️ Has Legal Auth: {stats.get('has_legal_auth', False)}")

        # 8. ASSESSMENT
        print(f"\\n🎯 NON-CLINICAL PARSER ASSESSMENT:")
        print("-" * 70)

        has_document_metadata = bool(doc_metadata and doc_metadata.title)
        has_patient_data = bool(patient_demo and patient_demo.full_name)
        has_providers = len(providers) > 0
        has_custodian = bool(custodian and custodian.organization_name)

        success_areas = []
        if has_document_metadata:
            success_areas.append("Document Metadata")
        if has_patient_data:
            success_areas.append("Patient Demographics")
        if has_providers:
            success_areas.append("Healthcare Providers")
        if has_custodian:
            success_areas.append("Custodian Information")

        print(f"✅ Successfully extracted: {', '.join(success_areas)}")

        total_score = sum(
            [has_document_metadata, has_patient_data, has_providers, has_custodian]
        )

        if total_score >= 3:
            print("🎉 EXCELLENT: Non-clinical parser working comprehensively!")
            print("   ✅ Ready to complement the Enhanced Clinical Parser")
        elif total_score >= 2:
            print("👍 GOOD: Most non-clinical data extracted successfully")
        else:
            print("⚠️ NEEDS IMPROVEMENT: Limited non-clinical data extraction")

    else:
        print("❌ Non-clinical parsing failed!")
        print(f"Error: {result.get('error', 'Unknown error')}")

    return result


if __name__ == "__main__":
    test_non_clinical_parser()
