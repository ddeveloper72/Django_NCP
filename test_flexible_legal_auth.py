"""
Test the flexible legal authenticator extraction
"""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_flexible_legal_authenticator():
    """Test flexible legal authenticator extraction"""
    print("Testing flexible legal authenticator extraction...")

    # Import our modules
    from patient_data.utils.flexible_cda_extractor import FlexibleCDAExtractor
    from patient_data.utils.administrative_extractor import CDAAdministrativeExtractor

    # Load a test CDA file
    test_files = [
        "test_data/test_cda_document.xml",
        "test_data/patient_44.xml",
        "test_data/sample_cda.xml",
    ]

    test_file = None
    for file_path in test_files:
        if os.path.exists(file_path):
            test_file = file_path
            break

    if not test_file:
        print("No test CDA files found. Looking for XML files in current directory...")
        xml_files = list(Path(".").glob("*.xml"))
        if xml_files:
            test_file = str(xml_files[0])
        else:
            print("No XML files found to test with.")
            return

    print(f"Using test file: {test_file}")

    try:
        # Parse the XML
        tree = ET.parse(test_file)
        root = tree.getroot()

        # Test namespace diagnosis
        print("\n=== NAMESPACE DIAGNOSIS ===")
        flexible_extractor = FlexibleCDAExtractor()
        diagnosis = flexible_extractor.diagnose_namespace_issues(root)

        for key, value in diagnosis.items():
            print(f"{key}: {value}")

        # Test direct flexible extraction
        print("\n=== DIRECT FLEXIBLE EXTRACTION ===")
        legal_auth_data = flexible_extractor.extract_legal_authenticator_flexible(root)
        print("Legal Authenticator Data:")
        for key, value in legal_auth_data.items():
            print(f"  {key}: {value}")

        # Test through administrative extractor
        print("\n=== ADMINISTRATIVE EXTRACTOR ===")
        admin_extractor = CDAAdministrativeExtractor()
        legal_auth_admin = admin_extractor.extract_legal_authenticator(root)
        print("Legal Authenticator (Admin):")
        for key, value in legal_auth_admin.items():
            print(f"  {key}: {value}")

        # Test template-friendly access
        print("\n=== TEMPLATE ACCESS TEST ===")
        print("Template-friendly fields:")
        print(f"  full_name: {legal_auth_data.get('full_name')}")
        print(f"  given_name: {legal_auth_data.get('given_name')}")
        print(f"  family_name: {legal_auth_data.get('family_name')}")
        print(
            f"  person.full_name: {legal_auth_data.get('person', {}).get('full_name')}"
        )
        print(
            f"  organization.name: {legal_auth_data.get('organization', {}).get('name')}"
        )

        # Simulate template access
        print("\n=== TEMPLATE SIMULATION ===")
        context = {"legal_authenticator": legal_auth_data}

        # These should work now without "{{ no such element: dict object['...'] }}" errors
        try:
            name = context["legal_authenticator"]["full_name"]
            print(f"✓ Template access legal_authenticator.full_name: {name}")
        except Exception as e:
            print(f"✗ Template access failed: {e}")

        try:
            given = context["legal_authenticator"]["given_name"]
            print(f"✓ Template access legal_authenticator.given_name: {given}")
        except Exception as e:
            print(f"✗ Template access failed: {e}")

        try:
            family = context["legal_authenticator"]["family_name"]
            print(f"✓ Template access legal_authenticator.family_name: {family}")
        except Exception as e:
            print(f"✗ Template access failed: {e}")

    except Exception as e:
        print(f"Error testing legal authenticator extraction: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_flexible_legal_authenticator()
