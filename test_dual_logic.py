#!/usr/bin/env python3
"""
Direct test of dual language function logic
"""


def test_dual_language_sections():
    """Test the dual language section creation logic"""

    # Mock the logger
    class Logger:
        def warning(self, msg):
            print(f"WARNING: {msg}")

        def info(self, msg):
            print(f"INFO: {msg}")

    logger = Logger()

    def _create_dual_language_sections(
        original_result, translated_result, source_language
    ):
        """
        Create dual language sections by combining original and translated processing results
        """
        if not original_result.get("success") or not translated_result.get("success"):
            logger.warning(
                "One or both processing results failed, falling back to single language"
            )
            return (
                translated_result
                if translated_result.get("success")
                else original_result
            )

        # Start with the translated result structure
        dual_result = dict(translated_result)

        original_sections = original_result.get("sections", [])
        translated_sections = translated_result.get("sections", [])

        # Create dual language sections
        dual_sections = []

        for i, translated_section in enumerate(translated_sections):
            # Find corresponding original section
            original_section = None
            if i < len(original_sections):
                original_section = original_sections[i]

            # Create dual language section
            dual_section = dict(translated_section)

            # Replace content with dual language structure
            dual_section["content"] = {
                "original": (
                    original_section.get("content", "") if original_section else ""
                ),
                "translated": translated_section.get("content", ""),
            }

            # Handle PS table content
            if "ps_table_content" in translated_section or (
                original_section and "ps_table_content" in original_section
            ):
                dual_section["ps_table_content"] = {
                    "original": (
                        original_section.get("ps_table_content", "")
                        if original_section
                        else ""
                    ),
                    "translated": translated_section.get("ps_table_content", ""),
                }

            # Add language metadata
            dual_section["language_info"] = {
                "source_language": source_language,
                "target_language": "en",
                "dual_language": True,
            }

            dual_sections.append(dual_section)

        # Update result with dual language sections
        dual_result["sections"] = dual_sections
        dual_result["dual_language"] = True
        dual_result["source_language"] = source_language

        return dual_result

    # Test data
    original_result = {
        "success": True,
        "sections": [
            {
                "title": "Medicamentos",
                "content": "Este é um exemplo em português",
                "ps_table_content": "Tabela de medicamentos em português",
            }
        ],
    }

    translated_result = {
        "success": True,
        "sections": [
            {
                "title": "Medications",
                "content": "This is an example in English",
                "ps_table_content": "Medication table in English",
            }
        ],
    }

    print("🔍 Testing dual language sections creation...")
    result = _create_dual_language_sections(original_result, translated_result, "pt")

    if result and result.get("sections"):
        print("✅ SUCCESS: Dual language sections created")
        section = result["sections"][0]
        print(f"   Title: {section['title']}")
        print(f"   Original content: {section['content']['original']}")
        print(f"   Translated content: {section['content']['translated']}")
        print(f"   Dual language flag: {result.get('dual_language', False)}")
        print(f"   Source language: {result.get('source_language', 'unknown')}")
        return True
    else:
        print("❌ FAILED: Could not create dual language sections")
        return False


if __name__ == "__main__":
    success = test_dual_language_sections()
    print(f"\n🎯 Test {'PASSED' if success else 'FAILED'}")
