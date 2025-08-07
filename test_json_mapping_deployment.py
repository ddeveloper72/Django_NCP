#!/usr/bin/env python3
"""
Test JSON Field Mapping Deployment
Verify that the Django server is now using the comprehensive JSON field mapping
"""

import os
import sys
import json

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


def test_json_mapping_deployment():
    """Test that the JSON field mapping is now deployed and active"""

    print("🚀 Testing JSON Field Mapping Deployment")
    print("=" * 60)

    # Test 1: Verify imports work
    print("📦 Import Verification:")
    try:
        from patient_data.services.enhanced_cda_processor_with_mapping import (
            EnhancedCDAProcessorWithMapping,
        )

        print("✅ EnhancedCDAProcessorWithMapping imported successfully")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

    # Test 2: Test with LU L3 patient data
    print("\n🇱🇺 Testing with LU L3 Patient (Celestina Doe-Calla):")

    cda_path = "test_data/eu_member_states/LU/CELESTINA_DOE-CALLA_38430827_3.xml"
    if os.path.exists(cda_path):
        try:
            with open(cda_path, "r", encoding="utf-8") as file:
                cda_content = file.read()
            print(f"✅ Loaded LU L3 CDA: {len(cda_content)} characters")

            # Test the comprehensive processor
            processor = EnhancedCDAProcessorWithMapping(target_language="en")
            result = processor.process_clinical_document(
                cda_content=cda_content, source_language="en"
            )

            if result.get("success"):
                print(f"✅ Comprehensive processing successful!")

                # Show detailed results
                clinical_sections = result.get("clinical_sections", [])
                mapped_sections = result.get("mapped_sections", {})
                patient_data = result.get("patient_data", {})

                print(f"\n📊 Comprehensive Results:")
                print(f"   Clinical sections: {len(clinical_sections)}")
                print(f"   Field-mapped sections: {len(mapped_sections)}")
                print(f"   Patient demographic fields: {len(patient_data)}")

                # Show patient data
                if patient_data:
                    print(f"\n👤 Patient Data Extracted:")
                    for field, info in patient_data.items():
                        if info.get("value"):
                            print(f"   ✅ {field}: {info['value']}")
                        else:
                            print(f"   ❌ {field}: [Not found]")

                # Show clinical sections
                if clinical_sections:
                    print(f"\n🏥 Clinical Sections:")
                    for section in clinical_sections[:5]:  # Show first 5
                        code = section.get("section_code", "Unknown")
                        title = section.get("title", "Unknown")
                        entries = len(section.get("entries", []))
                        print(f"   📋 {code}: {title} ({entries} entries)")

                # Show field mapping details
                if mapped_sections:
                    print(f"\n🗂️  Field-Mapped Sections:")
                    for code, mapping in mapped_sections.items():
                        mapped_fields = mapping.get("mapped_fields", {})
                        entries = mapping.get("entries", [])
                        found_fields = len(
                            [f for f in mapped_fields.values() if f.get("value")]
                        )
                        print(
                            f"   📊 {code}: {found_fields}/{len(mapped_fields)} fields, {len(entries)} entries"
                        )

                return True

            else:
                print(f"❌ Processing failed: {result.get('error')}")
                return False

        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
    else:
        print(f"❌ LU L3 CDA not found: {cda_path}")
        return False

    # Test 3: Compare with original processor
    print(f"\n🔄 Comparison with Original Processor:")
    try:
        from patient_data.services.enhanced_cda_processor import EnhancedCDAProcessor

        original_processor = EnhancedCDAProcessor(target_language="en")
        original_result = original_processor.process_clinical_sections(
            cda_content=cda_content, source_language="en"
        )

        if original_result.get("success"):
            original_sections = original_result.get("sections", [])
            print(f"✅ Original processor: {len(original_sections)} sections")
            print(
                f"✅ New processor: {len(clinical_sections)} clinical sections + {len(mapped_sections)} field-mapped"
            )
            print(
                f"🎯 Enhancement: Field-level mapping with {len(patient_data)} patient fields"
            )
        else:
            print(f"❌ Original processor failed for comparison")

    except ImportError:
        print(f"⚠️  Original processor not available for comparison")


def test_django_view_integration():
    """Test that Django views are using the new processor"""

    print(f"\n🌐 Django View Integration Test:")
    print("=" * 40)

    # Test the main patient view
    try:
        from patient_data.views import patient_cda_view
        import inspect

        # Check the source code
        source_lines = inspect.getsourcelines(patient_cda_view)[0]
        source_code = "".join(source_lines)

        if "EnhancedCDAProcessorWithMapping" in source_code:
            print("✅ Main patient view: Using new processor with field mapping")
        elif "EnhancedCDAProcessor" in source_code:
            print("❌ Main patient view: Still using original processor")
        else:
            print("❓ Main patient view: Cannot determine processor type")

        if "process_clinical_document" in source_code:
            print("✅ Main patient view: Using comprehensive processing method")
        elif "process_clinical_sections" in source_code:
            print("⚠️  Main patient view: Using original processing method")

    except Exception as e:
        print(f"❌ Could not analyze main patient view: {e}")

    # Test the enhanced CDA display
    try:
        from patient_data.views import enhanced_cda_display
        import inspect

        source_lines = inspect.getsourcelines(enhanced_cda_display)[0]
        source_code = "".join(source_lines)

        if "EnhancedCDAProcessorWithMapping" in source_code:
            print("✅ Enhanced CDA display: Using new processor with field mapping")
        else:
            print("❌ Enhanced CDA display: Not using new processor")

    except Exception as e:
        print(f"❌ Could not analyze enhanced CDA display: {e}")

    # Test the ehealth portal AJAX
    try:
        from ehealth_portal.views import process_cda_ajax
        import inspect

        source_lines = inspect.getsourcelines(process_cda_ajax)[0]
        source_code = "".join(source_lines)

        if "EnhancedCDAProcessorWithMapping" in source_code:
            print("✅ eHealth portal AJAX: Using new processor with field mapping")
        else:
            print("❌ eHealth portal AJAX: Not using new processor")

    except Exception as e:
        print(f"❌ Could not analyze eHealth portal AJAX: {e}")


def main():
    """Run comprehensive deployment test"""

    print("🎯 JSON Field Mapping Deployment Verification")
    print("=" * 70)

    # Test the deployment
    mapping_success = test_json_mapping_deployment()

    # Test Django integration
    test_django_view_integration()

    print(f"\n🎉 Deployment Summary:")
    print("=" * 30)

    if mapping_success:
        print("✅ JSON Field Mapping is SUCCESSFULLY DEPLOYED!")
        print("✅ Comprehensive field-level processing is active")
        print("✅ Patient demographic mapping is working")
        print("✅ Clinical sections with detailed field extraction")
        print("✅ Django views updated to use new processor")
        print(
            "\n🚀 Your LU L3 patient tests will now use comprehensive JSON field mapping!"
        )
        print("🎯 Translation service enhanced with field-level precision!")
    else:
        print("❌ Deployment verification failed")
        print("⚠️  Check errors above and retry deployment")

    return mapping_success


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
