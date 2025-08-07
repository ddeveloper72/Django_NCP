"""
Simple test for dual language medical_terms fix
"""


def _create_dual_language_sections(original_result, translated_result, source_language):
    """
    Create dual language sections by combining original and translated processing results
    """
    if not original_result.get("success") or not translated_result.get("success"):
        print("WARNING: One or both processing results failed")
        return (
            translated_result if translated_result.get("success") else original_result
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

        # Preserve original content structure while adding dual language content
        original_content = (
            original_section.get("content", "") if original_section else ""
        )
        translated_content = translated_section.get("content", "")

        # Handle content that might be a dict (with medical_terms) or string
        if isinstance(translated_content, dict):
            # Keep all the metadata from translated content
            dual_section["content"] = dict(translated_content)
            dual_section["content"]["translated"] = translated_content.get(
                "content", str(translated_content)
            )
            dual_section["content"]["original"] = (
                original_content.get("content", str(original_content))
                if isinstance(original_content, dict)
                else str(original_content)
            )
        else:
            # Simple string content
            dual_section["content"] = {
                "translated": str(translated_content),
                "original": str(original_content),
                "medical_terms": 0,  # Default for compatibility
            }

        # Add source language info
        dual_section["source_language"] = source_language
        dual_section["has_dual_language"] = True

        # Handle PS table content for both languages if available
        if translated_section.get("has_ps_table"):
            dual_section["ps_table_html"] = translated_section.get("ps_table_html", "")
            if original_section and original_section.get("has_ps_table"):
                dual_section["ps_table_html_original"] = original_section.get(
                    "ps_table_html", ""
                )
            else:
                dual_section["ps_table_html_original"] = ""

        dual_sections.append(dual_section)

    # Update the result with dual language sections
    dual_result["sections"] = dual_sections
    dual_result["dual_language_active"] = True
    dual_result["source_language"] = source_language

    # Ensure medical_terms_count is preserved for template compatibility
    if "medical_terms_count" not in dual_result:
        dual_result["medical_terms_count"] = translated_result.get(
            "medical_terms_count", 0
        )

    print(
        f"Created {len(dual_sections)} dual language sections ({source_language} | en)"
    )

    return dual_result


# Test the function
original_result = {
    "success": True,
    "medical_terms_count": 5,
    "sections": [
        {
            "title": "Medicamentos",
            "content": {"content": "Portuguese content", "medical_terms": 3},
        }
    ],
}

translated_result = {
    "success": True,
    "medical_terms_count": 5,
    "sections": [
        {
            "title": "Medications",
            "content": {"content": "English content", "medical_terms": 3},
        }
    ],
}

print("🔍 Testing dual language with dict content...")
result = _create_dual_language_sections(original_result, translated_result, "pt")

if result and result.get("sections"):
    section = result["sections"][0]
    content = section.get("content", {})
    print(f"✅ Success! Content keys: {list(content.keys())}")
    print(f"   medical_terms: {content.get('medical_terms', 'MISSING')}")
    print(f"   original: {content.get('original', 'MISSING')[:20]}...")
    print(f"   translated: {content.get('translated', 'MISSING')[:20]}...")
else:
    print("❌ Failed!")
