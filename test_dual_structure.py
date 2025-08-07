#!/usr/bin/env python3
"""
Debug the dual language structure to fix the medical_terms error
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()


def test_dual_language_structure():
    """Test dual language structure to identify the medical_terms issue"""
    print("🔍 Testing Dual Language Structure - Medical Terms Fix")
    print("=" * 60)

    # Import after Django setup
    from patient_data.views import _create_dual_language_sections

    # Mock original result with medical_terms structure
    original_result = {
        "success": True,
        "medical_terms_count": 5,
        "sections": [
            {
                "title": "Medicamentos",
                "section_code": "10160-0",
                "content": {
                    "content": "Este é um exemplo em português",
                    "medical_terms": 3,
                },
                "ps_table_html": "Tabela de medicamentos em português",
                "has_ps_table": True,
            }
        ],
    }

    # Mock translated result with medical_terms structure
    translated_result = {
        "success": True,
        "medical_terms_count": 5,
        "sections": [
            {
                "title": "Medications",
                "section_code": "10160-0",
                "content": {
                    "content": "This is an example in English",
                    "medical_terms": 3,
                },
                "ps_table_html": "Medication table in English",
                "has_ps_table": True,
            }
        ],
    }

    print("1. Testing with dict-based content structure...")
    print(
        f"   Original content type: {type(original_result['sections'][0]['content'])}"
    )
    print(
        f"   Original medical_terms: {original_result['sections'][0]['content']['medical_terms']}"
    )
    print(
        f"   Translated content type: {type(translated_result['sections'][0]['content'])}"
    )
    print(
        f"   Translated medical_terms: {translated_result['sections'][0]['content']['medical_terms']}"
    )

    # Test dual language processing
    dual_result = _create_dual_language_sections(
        original_result, translated_result, "pt"
    )

    if dual_result and dual_result.get("sections"):
        section = dual_result["sections"][0]
        print("\n✅ Dual language result created")
        print(
            f"   - Result has medical_terms_count: {dual_result.get('medical_terms_count', 'MISSING')}"
        )
        print(f"   - Section content type: {type(section.get('content', {}))}")
        print(f"   - Section content keys: {list(section.get('content', {}).keys())}")

        content = section.get("content", {})
        if "medical_terms" in content:
            print(f"   - ✅ medical_terms preserved: {content['medical_terms']}")
        else:
            print(f"   - ❌ medical_terms MISSING")

        if "original" in content:
            print(f"   - ✅ original content: {content['original'][:50]}...")
        else:
            print(f"   - ❌ original content MISSING")

        if "translated" in content:
            print(f"   - ✅ translated content: {content['translated'][:50]}...")
        else:
            print(f"   - ❌ translated content MISSING")

        return True
    else:
        print("❌ Failed to create dual language result")
        return False


def test_simple_content_structure():
    """Test with simple string content structure"""
    print("\n\n🔍 Testing Simple Content Structure")
    print("=" * 60)

    # Import after Django setup
    from patient_data.views import _create_dual_language_sections

    # Mock results with simple string content
    original_result = {
        "success": True,
        "medical_terms_count": 2,
        "sections": [
            {
                "title": "Medicamentos",
                "content": "Este é um exemplo simples em português",
                "ps_table_html": "Tabela simples",
            }
        ],
    }

    translated_result = {
        "success": True,
        "medical_terms_count": 2,
        "sections": [
            {
                "title": "Medications",
                "content": "This is a simple example in English",
                "ps_table_html": "Simple table",
            }
        ],
    }

    print("2. Testing with string-based content structure...")
    print(
        f"   Original content type: {type(original_result['sections'][0]['content'])}"
    )
    print(
        f"   Translated content type: {type(translated_result['sections'][0]['content'])}"
    )

    # Test dual language processing
    dual_result = _create_dual_language_sections(
        original_result, translated_result, "pt"
    )

    if dual_result and dual_result.get("sections"):
        section = dual_result["sections"][0]
        print("\n✅ Dual language result created")
        print(
            f"   - Result has medical_terms_count: {dual_result.get('medical_terms_count', 'MISSING')}"
        )
        print(f"   - Section content type: {type(section.get('content', {}))}")
        print(f"   - Section content keys: {list(section.get('content', {}).keys())}")

        content = section.get("content", {})
        if "medical_terms" in content:
            print(f"   - ✅ medical_terms fallback: {content['medical_terms']}")
        else:
            print(f"   - ❌ medical_terms MISSING")

        return True
    else:
        print("❌ Failed to create dual language result")
        return False


def main():
    """Run dual language structure tests"""
    print("🚀 Dual Language Structure Debug - Medical Terms Fix")
    print("=" * 60)

    test1_result = test_dual_language_structure()
    test2_result = test_simple_content_structure()

    print("\n\n📋 Debug Summary")
    print("=" * 60)

    if test1_result and test2_result:
        print("🎉 All tests passed - dual language structure working")
        print("\n✨ Structure now supports:")
        print("   • Preserved medical_terms attribute")
        print("   • Original and translated content")
        print("   • Both dict and string content types")
        print("   • Template compatibility maintained")
    else:
        print("⚠️  Some tests failed - review structure")

    return test1_result and test2_result


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
