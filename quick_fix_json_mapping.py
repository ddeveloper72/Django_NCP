#!/usr/bin/env python3
"""
Quick Fix for JSON Mapping Deployment Issue
Create a simple, working version that doesn't cause method signature errors
"""

import os
import sys

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")

try:
    import django

    django.setup()
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)


def quick_test_simple_processing():
    """Test with a simpler approach to avoid method signature issues"""

    print("🔧 Quick Fix: Testing Simple Processing")
    print("=" * 50)

    try:
        # Test just the field mapper by itself
        from patient_data.services.enhanced_cda_field_mapper import (
            EnhancedCDAFieldMapper,
        )

        mapper = EnhancedCDAFieldMapper()
        print("✅ Field mapper loaded successfully")

        # Test with simple XML
        import xml.etree.ElementTree as ET

        # Load real LU data
        cda_path = "test_data/eu_member_states/LU/CELESTINA_DOE-CALLA_38430827_3.xml"

        if os.path.exists(cda_path):
            with open(cda_path, "r", encoding="utf-8") as file:
                cda_content = file.read()

            root = ET.fromstring(cda_content)
            namespaces = {"hl7": "urn:hl7-org:v3"}

            print("✅ XML parsed successfully")

            # Test patient mapping step by step
            print("\n👤 Testing Patient Mapping:")
            try:
                patient_data = mapper.map_patient_data(root, namespaces)
                print(f"✅ Patient mapping successful: {len(patient_data)} fields")

                for field, info in patient_data.items():
                    if info.get("value"):
                        print(f"   ✅ {field}: {info['value']}")

            except Exception as e:
                print(f"❌ Patient mapping failed: {e}")
                import traceback

                traceback.print_exc()
                return False

            # Test section mapping
            print("\n🏥 Testing Section Mapping:")
            try:
                sections = root.findall(".//hl7:section", namespaces)
                print(f"✅ Found {len(sections)} sections")

                for i, section in enumerate(sections[:3]):  # Test first 3 sections
                    code_elem = section.find("hl7:code", namespaces)
                    if code_elem is not None:
                        section_code = code_elem.get("code")

                        if mapper.get_section_mapping(section_code):
                            try:
                                section_data = mapper.map_clinical_section(
                                    section, section_code, root, namespaces
                                )
                                print(
                                    f"   ✅ Section {section_code}: Mapped successfully"
                                )
                            except Exception as e:
                                print(
                                    f"   ❌ Section {section_code}: Mapping failed - {e}"
                                )
                                import traceback

                                traceback.print_exc()
                                return False
                        else:
                            print(f"   ⚠️  Section {section_code}: No mapping available")

            except Exception as e:
                print(f"❌ Section mapping failed: {e}")
                import traceback

                traceback.print_exc()
                return False

            print("\n✅ All basic mappings work - issue is likely in integration layer")
            return True

        else:
            print(f"❌ CDA file not found: {cda_path}")
            return False

    except Exception as e:
        print(f"❌ Simple test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def quick_fix_deployment():
    """Create a quick fix that bypasses the integration issues"""

    print("\n🚀 Quick Fix: Bypass Integration Issues")
    print("=" * 45)

    # If the basic mapping works, let's temporarily modify the views
    # to use the original processor but enhance it with field mapping

    try:
        from patient_data.services.enhanced_cda_processor import EnhancedCDAProcessor
        from patient_data.services.enhanced_cda_field_mapper import (
            EnhancedCDAFieldMapper,
        )

        # Test a hybrid approach
        processor = EnhancedCDAProcessor(target_language="en")
        mapper = EnhancedCDAFieldMapper()

        # Load test data
        cda_path = "test_data/eu_member_states/LU/CELESTINA_DOE-CALLA_38430827_3.xml"

        if os.path.exists(cda_path):
            with open(cda_path, "r", encoding="utf-8") as file:
                cda_content = file.read()

            # Process with original processor
            original_result = processor.process_clinical_sections(
                cda_content=cda_content, source_language="en"
            )

            if original_result.get("success"):
                print("✅ Original processor works")

                # Add field mapping data to the result
                import xml.etree.ElementTree as ET

                root = ET.fromstring(cda_content)
                namespaces = {"hl7": "urn:hl7-org:v3"}

                # Add patient data
                patient_data = mapper.map_patient_data(root, namespaces)
                original_result["patient_data"] = patient_data
                original_result["field_mapping_active"] = True

                print("✅ Enhanced with field mapping data")
                print(
                    f"   Original sections: {len(original_result.get('sections', []))}"
                )
                print(f"   Patient fields: {len(patient_data)}")

                return True, original_result
            else:
                print(f"❌ Original processor failed: {original_result.get('error')}")
                return False, None
        else:
            print(f"❌ Test file not found")
            return False, None

    except Exception as e:
        print(f"❌ Quick fix failed: {e}")
        import traceback

        traceback.print_exc()
        return False, None


def main():
    """Run quick diagnosis and fix"""

    print("🩺 Quick Diagnosis and Fix")
    print("=" * 70)

    # Test basic functionality
    basic_works = quick_test_simple_processing()

    if basic_works:
        print("\n✅ Basic field mapping works")

        # Try the quick fix
        fix_works, result = quick_fix_deployment()

        if fix_works:
            print("\n✅ Quick fix successful!")
            print("🎯 The issue is in the integration layer, not the core mapping")
            print("🔧 We can use a hybrid approach temporarily")

            # Show what we would recommend
            print("\n📋 Recommended Fix:")
            print("1. Temporarily revert to original Enhanced CDA Processor")
            print("2. Add field mapping data as enhancement")
            print("3. Fix integration layer separately")
            print("4. This will give you working JSON field mapping without errors")

        else:
            print("\n❌ Quick fix failed")
            print("🔧 Need to investigate integration layer issues")
    else:
        print("\n❌ Basic field mapping has issues")
        print("🔧 Need to fix core mapping functionality first")


if __name__ == "__main__":
    main()
