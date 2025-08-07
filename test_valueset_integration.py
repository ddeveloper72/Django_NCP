#!/usr/bin/env python3
"""
Test Value Set Integration for Clinical Terminology
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

from patient_data.services.enhanced_cda_processor import EnhancedCDAProcessor


def test_valueset_integration():
    """Test value set integration for Malta PS document"""

    print("🧪 Testing Value Set Integration for Clinical Terminology")
    print("=" * 60)

    # Initialize processor
    processor = EnhancedCDAProcessor()

    # Test Malta PS document path
    malta_ps_path = "test_data/MT_PS_Document.xml"

    if not os.path.exists(malta_ps_path):
        print(f"❌ Malta PS document not found at {malta_ps_path}")
        return

    print(f"📄 Processing Malta PS document: {malta_ps_path}")

    try:
        # Process the document
        with open(malta_ps_path, "r", encoding="utf-8") as f:
            cda_content = f.read()

        # Test enhanced processing
        result = processor.process_cda_document(
            cda_content=cda_content, source_language="en", target_language="lv"
        )

        print(f"✅ Processing completed successfully")
        print(f"📊 Sections processed: {len(result.get('sections', []))}")

        # Check for value set integration in Allergies section
        for section in result.get("sections", []):
            if "allerg" in section.get("title", "").lower():
                print(f"\n🔍 Allergies Section Analysis:")
                print(f"Title: {section.get('title', 'Unknown')}")

                # Check table data for value set terms
                table_data = section.get("table_data", [])
                print(f"Table entries: {len(table_data)}")

                for i, entry in enumerate(table_data[:3]):  # Show first 3 entries
                    print(f"\nEntry {i+1}:")
                    if "fields" in entry:
                        for field_name, field_info in entry["fields"].items():
                            value = field_info.get("value", "No value")
                            has_valueset = field_info.get("has_valueset", False)
                            needs_translation = field_info.get(
                                "needs_translation", False
                            )

                            print(f"  {field_name}: {value}")
                            if has_valueset:
                                print(f"    💊 Has ValueSet: YES")
                            if needs_translation:
                                print(f"    🔄 Needs Translation: YES")

                # Check if we still see "Unknown Agent" or proper medical terms
                table_html = section.get("table_html", "")
                if "Unknown Agent" in table_html or "Unknown Reaction" in table_html:
                    print(
                        f"\n⚠️  Still seeing generic labels - value set lookup may need improvement"
                    )
                else:
                    print(
                        f"\n✅ Clinical terminology appears to be properly translated"
                    )
                break

    except Exception as e:
        print(f"❌ Error processing document: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_valueset_integration()
