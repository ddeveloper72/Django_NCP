#!/usr/bin/env python3
"""
Test script to verify actual CDA processing with the Enhanced CDA Processor
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()


def test_actual_cda_processing():
    """Test the Enhanced CDA Processor with actual sample data"""
    print("🧪 Testing Enhanced CDA Processor with Actual Sample Data")
    print("=" * 60)

    # Load the sample CDA document
    sample_cda_path = "patient_data/test_data/sample_cda_document.xml"

    try:
        with open(sample_cda_path, "r", encoding="utf-8") as file:
            cda_content = file.read()
        print(f"✅ Loaded CDA content: {len(cda_content)} characters")
    except FileNotFoundError:
        print(f"❌ Sample CDA file not found: {sample_cda_path}")
        return

    # Import the Enhanced CDA Processor
    try:
        from patient_data.services.enhanced_cda_processor import EnhancedCDAProcessor

        print("✅ Enhanced CDA Processor imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Enhanced CDA Processor: {e}")
        return

    # Initialize the processor
    processor = EnhancedCDAProcessor(target_language="en")
    print("✅ Enhanced CDA Processor initialized")

    # Process the clinical sections
    print("\n📊 Processing clinical sections...")
    try:
        result = processor.process_clinical_sections(
            cda_content=cda_content, source_language="en"  # English sample document
        )

        print(f"✅ Processing result success: {result.get('success', False)}")

        if result.get("success"):
            print(f"📝 Sections processed: {result.get('sections_count', 0)}")
            print(f"🏷️  Coded sections: {result.get('coded_sections_count', 0)}")
            print(f"🔬 Medical terms: {result.get('medical_terms_count', 0)}")

            # Extract sections to examine the data
            sections = result.get("sections", [])
            print(f"\n📋 Found {len(sections)} sections:")

            for i, section in enumerate(sections):
                print(f"\n  Section {i+1}: {section.get('title', 'Unknown Title')}")
                print(f"    Code: {section.get('code', 'No Code')}")
                print(f"    Rows: {len(section.get('table_rows', []))}")

                # Show first few rows to check data
                rows = section.get("table_rows", [])
                for j, row in enumerate(rows[:3]):  # Show first 3 rows
                    print(f"    Row {j+1}: {row}")

                if len(rows) > 3:
                    print(f"    ... and {len(rows) - 3} more rows")

        else:
            print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Exception during processing: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_actual_cda_processing()
