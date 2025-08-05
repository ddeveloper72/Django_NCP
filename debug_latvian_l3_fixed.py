#!/usr/bin/env python3
"""
Debug script to test Enhanced CDA Processor with Latvian L3 CDA document
Fixed for proper Unicode handling
"""

import os
import sys
import django
import logging

# Fix Unicode encoding for Windows console
if sys.platform == "win32":
    import codecs

    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Configure logging to handle Unicode properly
logging.basicConfig(
    level=logging.INFO, format="%(levelname)s %(message)s", stream=sys.stdout
)

# Add project root to Python path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.services.enhanced_cda_processor import EnhancedCDAProcessor


def test_latvian_l3_cda():
    """Test Enhanced CDA Processor with real Latvian L3 CDA document"""

    # Path to Latvian L3 FRIENDLY CDA document
    latvian_l3_path = "test_data/eu_member_states/LV/2025-04-01T11-25-07.284098Z_CDA_EHDSI---FRIENDLY-CDA-(L3)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"

    try:
        # Read the Latvian L3 CDA document
        with open(latvian_l3_path, "r", encoding="utf-8") as f:
            latvian_cda_content = f.read()

        print("=== LATVIAN L3 CDA DOCUMENT ANALYSIS ===")
        print(f"Document path: {latvian_l3_path}")
        print(f"Document size: {len(latvian_cda_content)} characters")

        # Quick check for language and structure
        if 'languageCode code="lv' in latvian_cda_content:
            print("✓ Language: Latvian (lv-LV)")

        if "<section>" in latvian_cda_content:
            print("✓ Contains XML sections (L3 structure)")

        if "<nonXMLBody>" in latvian_cda_content:
            print("⚠ Warning: Contains PDF content (mixed structure)")
        else:
            print("✓ Pure XML structure (no embedded PDF)")

        print("\n=== ENHANCED CDA PROCESSOR TEST ===")

        # Initialize Enhanced CDA Processor for English translation
        processor = EnhancedCDAProcessor(target_language="en")

        # Process the Latvian CDA content
        result = processor.process_clinical_sections(
            cda_content=latvian_cda_content,
            source_language="lv",  # Latvian source language
        )

        print(f"Processing success: {result['success']}")
        print(f"Content type: {result.get('content_type', 'Unknown')}")
        print(f"Sections found: {result.get('sections_count', 0)}")
        print(f"Medical terms: {result.get('medical_terms_count', 0)}")
        print(f"Coded sections: {result.get('coded_sections_count', 0)}")

        if result.get("sections"):
            print("\n=== CLINICAL SECTIONS FOUND ===")
            for i, section in enumerate(result["sections"], 1):
                print(f"\nSection {i}:")
                print(f"  ID: {section.get('section_id', 'N/A')}")
                print(f"  Section Code: {section.get('section_code', 'N/A')}")
                print(
                    f"  Original Title: {section.get('title', {}).get('original', 'N/A')}"
                )
                print(
                    f"  Translated Title: {section.get('title', {}).get('translated', 'N/A')}"
                )
                print(f"  Is Coded: {section.get('is_coded_section', False)}")
                print(f"  Has PS Table: {section.get('has_ps_table', False)}")

                # Show content preview
                content = section.get("content", {})
                original_content = content.get("original", "")
                if original_content:
                    preview = (
                        original_content[:200] + "..."
                        if len(original_content) > 200
                        else original_content
                    )
                    print(f"  Content Preview: {preview}")

        else:
            print("❌ No clinical sections found")
            if "error" in result:
                print(f"Error: {result['error']}")

        return result

    except FileNotFoundError:
        print(f"❌ File not found: {latvian_l3_path}")
        return None
    except Exception as e:
        print(f"❌ Error processing Latvian L3 CDA: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("Testing Enhanced CDA Processor with Latvian L3 CDA Document")
    print("=" * 60)

    result = test_latvian_l3_cda()

    if result and result.get("success"):
        print("\n✅ SUCCESS: Latvian L3 CDA processing completed!")
        print(
            f"Found {result.get('sections_count', 0)} clinical sections with proper LOINC codes"
        )
    else:
        print("\n❌ FAILED: Latvian L3 CDA processing failed")
