#!/usr/bin/env python3
"""
Test script to verify Malta PS document processing with single-language fixes
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.views import process_uploaded_document
import xml.etree.ElementTree as ET


def test_malta_document_processing():
    """Test Malta PS document processing for single-language handling"""

    # Load Malta PS document
    malta_file_path = "test_data/Malta PS Documents/Mario_Borg_9999002M_3.xml"

    print("🧪 Testing Malta PS Document Processing")
    print("=" * 50)

    if not os.path.exists(malta_file_path):
        print(f"❌ Malta test file not found: {malta_file_path}")
        return False

    try:
        # Read the XML content
        with open(malta_file_path, "r", encoding="utf-8") as f:
            cda_content = f.read()

        print(f"✅ Loaded Malta PS document: {len(cda_content)} characters")

        # Parse XML to verify language
        try:
            root = ET.fromstring(cda_content)
            language_code = root.get("languageCode")
            print(f"📝 Document language code: {language_code}")
        except ET.ParseError as e:
            print(f"⚠️  XML parsing issue: {e}")

        # Create a mock document info structure
        document_info = {
            "uuid": "test-malta-uuid",
            "original_filename": "Mario_Borg_9999002M_3.xml",
            "upload_date": "2024-01-01",
            "file_path": malta_file_path,
        }

        print("\n🔄 Processing document...")

        # Test the processing function
        result = process_uploaded_document(document_info, cda_content)

        if result.get("success"):
            print("✅ Document processing successful!")

            # Check for single language flag
            is_single_language = result.get("is_single_language", False)
            print(f"📄 Single language mode: {is_single_language}")

            # Check sections
            sections = result.get("sections", [])
            print(f"📋 Sections found: {len(sections)}")

            # Examine first section content structure
            if sections:
                first_section = sections[0]
                section_title = first_section.get("title", "Unknown")
                content = first_section.get("content", {})

                print(f"\n🔍 First section: '{section_title}'")

                if isinstance(content, dict):
                    has_original = "original" in content
                    has_translated = "translated" in content
                    print(f"   - Has 'original' content: {has_original}")
                    print(f"   - Has 'translated' content: {has_translated}")

                    if is_single_language:
                        if has_original and has_translated:
                            print(
                                "   ⚠️  WARNING: Single language document has dual content structure"
                            )
                        else:
                            print("   ✅ Single language structure correct")
                    else:
                        if has_original and has_translated:
                            print("   ✅ Dual language structure present")
                        else:
                            print(
                                "   ⚠️  WARNING: Dual language document missing proper structure"
                            )

                    # Show content preview
                    if isinstance(content, str):
                        preview = (
                            content[:200] + "..." if len(content) > 200 else content
                        )
                        print(f"   📝 Content preview: {preview}")
                    elif isinstance(content, dict) and "content" in content:
                        content_text = content["content"]
                        preview = (
                            content_text[:200] + "..."
                            if len(content_text) > 200
                            else content_text
                        )
                        print(f"   📝 Content preview: {preview}")

                print()

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
    success = test_malta_document_processing()
    if success:
        print("🎉 Malta document processing test completed successfully!")
    else:
        print("💥 Malta document processing test failed!")
        sys.exit(1)
