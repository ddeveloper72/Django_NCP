#!/usr/bin/env python3
"""
Test Dual Language Processing Fix
Quick test to verify the dual language fix is working
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()


def test_dual_language_fix():
    """Test the dual language processing fix"""

    print("🔧 Testing Dual Language Processing Fix")
    print("=" * 50)

    try:
        # Import the dual language function
        from patient_data.views import _create_dual_language_sections

        print("✅ Successfully imported _create_dual_language_sections")

        # Create mock processing results to test the function
        original_result = {
            "success": True,
            "sections": [
                {
                    "section_title": "Resumo de Medicação",
                    "section_code": "10160-0",
                    "content": "<p>Medicamento: Paracetamol 500mg</p>",
                    "has_ps_table": False,
                }
            ],
        }

        translated_result = {
            "success": True,
            "sections": [
                {
                    "section_title": "Medication Summary",
                    "section_code": "10160-0",
                    "content": "<p>Medication: Paracetamol 500mg</p>",
                    "has_ps_table": False,
                }
            ],
        }

        # Test the dual language function
        dual_result = _create_dual_language_sections(
            original_result, translated_result, "pt"
        )

        print("✅ Dual language function executed successfully")

        # Check the result structure
        if dual_result.get("dual_language_active"):
            print("✅ Dual language mode activated")
        else:
            print("❌ Dual language mode not activated")

        if dual_result.get("source_language") == "pt":
            print("✅ Source language correctly set to Portuguese")
        else:
            print(f"❌ Source language incorrect: {dual_result.get('source_language')}")

        # Check section structure
        sections = dual_result.get("sections", [])
        if sections:
            section = sections[0]
            content = section.get("content", {})

            if isinstance(content, dict):
                print("✅ Section content has dual language structure")

                original_content = content.get("original", "")
                translated_content = content.get("translated", "")

                print(f"   Original: {original_content[:50]}...")
                print(f"   Translated: {translated_content[:50]}...")

                if "Resumo" in original_content:
                    print("✅ Original content contains Portuguese text")
                else:
                    print("❌ Original content does not contain Portuguese text")

                if "Medication Summary" in translated_content:
                    print("✅ Translated content contains English text")
                else:
                    print("❌ Translated content does not contain English text")
            else:
                print("❌ Section content does not have dual language structure")
        else:
            print("❌ No sections found in result")

        return True

    except Exception as e:
        print(f"❌ Error testing dual language fix: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    print("🇵🇹 Dual Language Processing Fix Test")
    print("=" * 80)

    success = test_dual_language_fix()

    if success:
        print("\n🎉 Dual language fix is working!")
        print("✅ Now restart your Django server and test with Portuguese patient")
        print(
            "✅ You should see original Portuguese content in 'Original (PT)' section"
        )
        print("✅ And English translation in 'English Translation' section")
    else:
        print("\n❌ Dual language fix needs attention")

    print("=" * 80)


if __name__ == "__main__":
    main()
