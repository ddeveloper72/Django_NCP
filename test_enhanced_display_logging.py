#!/usr/bin/env python3
"""
Test Enhanced CDA Display View with Value Set Integration
"""

import os
import sys
import django

# Add the Django project directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_ncp.settings")
django.setup()

from django.test import RequestFactory
from patient_data.views.enhanced_cda_display import EnhancedCDADisplayView


def test_enhanced_display_with_logging():
    """Test the enhanced display view with detailed logging"""

    print("Testing Enhanced CDA Display View with Value Set Integration")
    print("=" * 65)

    try:
        # Create a mock request
        factory = RequestFactory()
        request = factory.get("/enhanced_cda/test_patient_123?lang=lv")

        # Create view instance
        view = EnhancedCDADisplayView()

        print("🔍 Testing patient CDA content retrieval...")

        # Test getting patient CDA content
        cda_content = view._get_patient_cda_content("test_patient_123")

        if cda_content:
            print(f"✅ CDA content retrieved: {len(cda_content)} characters")

            # Check content type
            if "<?xml" in cda_content or "<ClinicalDocument" in cda_content:
                print("📄 Content type: XML CDA")
            elif "<html" in cda_content or "<body" in cda_content:
                print("📄 Content type: HTML CDA")
                print("🔍 Looking for section codes in HTML...")

                # Check for section codes
                import re

                section_codes = re.findall(r'data-code="([^"]+)"', cda_content)
                if section_codes:
                    print(f"✅ Found section codes: {section_codes}")
                    for code in section_codes:
                        print(f"  - {code}")
                else:
                    print("⚠️  No section codes found in HTML content")

            # Test the enhanced processor directly
            print("\n🧪 Testing Enhanced CDA Processor directly...")

            from patient_data.services.enhanced_cda_processor import (
                EnhancedCDAProcessor,
            )

            processor = EnhancedCDAProcessor(target_language="lv")

            result = processor.process_clinical_sections(
                cda_content=cda_content, source_language="fr"
            )

            print(f"✅ Processing result keys: {list(result.keys())}")
            print(f"📊 Sections processed: {result.get('sections_count', 0)}")
            print(f"🏥 Content type: {result.get('content_type', 'unknown')}")

            # Analyze sections
            sections = result.get("sections", [])
            for i, section in enumerate(sections):
                section_code = section.get("section_code", "No code")
                title = section.get("title", {})
                original_title = (
                    title.get("original", "No title")
                    if isinstance(title, dict)
                    else str(title)
                )
                has_ps_table = section.get("has_ps_table", False)
                table_data = section.get("table_data", [])

                print(f"\n📋 Section {i+1}:")
                print(f"   Code: {section_code}")
                print(f"   Title: {original_title}")
                print(f"   Has PS Table: {has_ps_table}")
                print(f"   Table Data Entries: {len(table_data)}")

                # Check for value set data
                if table_data:
                    first_entry = table_data[0]
                    entry_type = first_entry.get("type", "unknown")
                    print(f"   First Entry Type: {entry_type}")

                    if "fields" in first_entry:
                        fields = first_entry.get("fields", {})
                        print(f"   Value Set Fields: {len(fields)}")

                        for field_name, field_info in list(fields.items())[
                            :3
                        ]:  # Show first 3 fields
                            value = field_info.get("value", "No value")
                            has_valueset = field_info.get("has_valueset", False)
                            original_value = field_info.get("original_value", value)

                            print(f"     {field_name}: {value}")
                            if has_valueset:
                                print(
                                    f"       (Original: {original_value}, Has ValueSet: {has_valueset})"
                                )
        else:
            print("❌ No CDA content retrieved")

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_enhanced_display_with_logging()
