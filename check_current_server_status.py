#!/usr/bin/env python3
"""
Check Current Server Implementation Status
Determines which CDA processor version is currently deployed
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


def check_current_implementation():
    """Check what's currently implemented in the server"""

    print("🔍 Current Server Implementation Analysis")
    print("=" * 60)

    # Check what's available
    print("📦 Available Components:")

    try:
        from patient_data.services.enhanced_cda_processor import EnhancedCDAProcessor

        print("✅ Enhanced CDA Processor (original)")
    except ImportError:
        print("❌ Enhanced CDA Processor not available")

    try:
        from patient_data.services.enhanced_cda_field_mapper import (
            EnhancedCDAFieldMapper,
        )

        print("✅ Enhanced CDA Field Mapper (new JSON mapping)")
    except ImportError:
        print("❌ Enhanced CDA Field Mapper not available")

    try:
        from patient_data.services.enhanced_cda_processor_with_mapping import (
            EnhancedCDAProcessorWithMapping,
        )

        print("✅ Enhanced CDA Processor with Mapping (integrated)")
    except ImportError:
        print("❌ Enhanced CDA Processor with Mapping not available")

    # Check current view implementation
    print("\n🌐 Current Django View Implementation:")

    try:
        from patient_data.views import patient_cda_view
        import inspect

        # Get the source code of the view function
        source_lines = inspect.getsourcelines(patient_cda_view)[0]

        # Check what processor is being used
        using_original = False
        using_field_mapper = False
        using_integrated = False

        for line in source_lines:
            if "EnhancedCDAProcessor" in line and "WithMapping" not in line:
                using_original = True
            if "EnhancedCDAFieldMapper" in line:
                using_field_mapper = True
            if "EnhancedCDAProcessorWithMapping" in line:
                using_integrated = True

        if using_integrated:
            print("✅ CURRENT: Using integrated processor with JSON field mapping")
        elif using_field_mapper:
            print("⚠️  CURRENT: Using field mapper but not integrated processor")
        elif using_original:
            print("❌ CURRENT: Using original Enhanced CDA Processor (NO JSON mapping)")
        else:
            print("❓ CURRENT: Cannot determine processor type")

    except Exception as e:
        print(f"❌ Could not analyze current view: {e}")

    # Test with LU L3 patient data
    print("\n🇱🇺 Testing Current Implementation with LU L3 Patient:")

    cda_path = "test_data/eu_member_states/LU/LUCAS-CELESTINA_DOE-CALLA_38430827_3.xml"
    if os.path.exists(cda_path):
        print(f"✅ Found LU L3 CDA: {cda_path}")

        try:
            with open(cda_path, "r", encoding="utf-8") as file:
                cda_content = file.read()

            # Test with current implementation
            from patient_data.services.enhanced_cda_processor import (
                EnhancedCDAProcessor,
            )

            processor = EnhancedCDAProcessor(target_language="en")
            result = processor.process_clinical_sections(
                cda_content=cda_content, source_language="en"
            )

            if result.get("success"):
                sections = result.get("sections", [])
                print(f"✅ Current processor handles {len(sections)} sections")

                # Check if JSON field mapping would provide more data
                try:
                    from patient_data.services.enhanced_cda_field_mapper import (
                        EnhancedCDAFieldMapper,
                    )

                    mapper = EnhancedCDAFieldMapper()
                    summary = mapper.get_mapping_summary()

                    print(f"🆕 JSON mapping would provide:")
                    print(
                        f"   📊 {summary['total_fields']} total fields across {summary['total_sections']} sections"
                    )
                    print(
                        f"   🔤 {summary['translation_required_fields']} fields requiring translation"
                    )
                    print(
                        f"   📋 {summary['clinical_sections']} clinical sections with field mapping"
                    )

                    # Show the difference
                    available_sections = summary["available_sections"]
                    json_section_codes = set(s["code"] for s in available_sections)
                    current_section_codes = set(
                        s.get("section_code", "")
                        for s in sections
                        if s.get("section_code")
                    )

                    print(f"\n📈 Enhancement Potential:")
                    print(f"   Current sections: {sorted(current_section_codes)}")
                    print(f"   JSON mapping sections: {sorted(json_section_codes)}")
                    print(
                        f"   Additional sections available: {sorted(json_section_codes - current_section_codes)}"
                    )

                except ImportError:
                    print("❌ JSON field mapping not available for comparison")

            else:
                print(f"❌ Current processor failed: {result.get('error')}")

        except Exception as e:
            print(f"❌ Testing failed: {e}")
    else:
        print(f"❌ LU L3 CDA not found: {cda_path}")

    print(f"\n🎯 Summary:")
    print(f"📊 Your JSON field mapping system is BUILT but NOT YET DEPLOYED")
    print(f"🔄 Server is still using last night's Enhanced CDA Processor")
    print(f"🚀 Ready to upgrade to comprehensive field mapping system")


if __name__ == "__main__":
    check_current_implementation()
