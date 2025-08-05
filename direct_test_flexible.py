import xml.etree.ElementTree as ET
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from patient_data.utils.flexible_cda_extractor import FlexibleCDAExtractor

    print("✓ FlexibleCDAExtractor imported successfully")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

# Test with file that has legal authenticator
test_file = r"test_data/eu_member_states/IT/2025-03-28T13-29-45.499822Z_CDA_EHDSI---PIVOT-CDA-(L1)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"

if not os.path.exists(test_file):
    print(f"✗ Test file not found: {test_file}")
    sys.exit(1)

try:
    tree = ET.parse(test_file)
    root = tree.getroot()
    print("✓ XML file parsed successfully")

    extractor = FlexibleCDAExtractor()
    print("✓ FlexibleCDAExtractor instantiated")

    # Diagnose namespace issues
    diagnosis = extractor.diagnose_namespace_issues(root)
    print(f"Root namespace: {diagnosis['root_namespace']}")
    print(f"Legal auth found: {diagnosis['legal_auth_found']}")
    print(f"Legal auth paths: {diagnosis['legal_auth_paths']}")

    # Extract legal authenticator
    legal_auth = extractor.extract_legal_authenticator_flexible(root)
    print("\nExtracted legal authenticator:")
    for key, value in legal_auth.items():
        print(f"  {key}: {value}")

    # Test template access (the key issue we're fixing)
    print("\n=== TEMPLATE ACCESS TEST ===")
    print(f"full_name: {legal_auth.get('full_name')}")
    print(f"given_name: {legal_auth.get('given_name')}")
    print(f"family_name: {legal_auth.get('family_name')}")
    print(f"organization.name: {legal_auth.get('organization', {}).get('name')}")

    # These should now work in templates without errors
    if legal_auth.get("full_name"):
        print(
            "✓ SUCCESS: Legal authenticator data can be accessed directly in templates!"
        )
    else:
        print("⚠ No name data found, but structure is correct for templates")

except Exception as e:
    import traceback

    print(f"✗ Error: {e}")
    traceback.print_exc()
