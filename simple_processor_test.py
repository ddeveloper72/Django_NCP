#!/usr/bin/env python3
"""
Simple test to verify Enhanced CDA Processor value set integration
"""

import os
import sys

# Add Django project to path
sys.path.append(r"c:\Users\Duncan\VS_Code_Projects\django_ncp")

try:
    # Setup Django
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_ncp.settings")
    django.setup()

    from patient_data.services.enhanced_cda_processor import EnhancedCDAProcessor

    print("Enhanced CDA Processor Value Set Integration Test")
    print("=" * 50)

    # Create processor
    processor = EnhancedCDAProcessor(target_language="lv")
    print("✅ Processor created successfully")

    # Test with HTML content that has section codes (like the view mock data)
    test_html = """
    <html>
        <body>
            <section class="allergy-summary" data-code="48765-2">
                <h2>Allergies et réactions indésirables</h2>
                <table class="clinical-table">
                    <thead>
                        <tr>
                            <th>Allergène</th>
                            <th>Réaction</th>
                            <th>Sévérité</th>
                            <th>Statut</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Pénicilline</td>
                            <td>Éruption cutanée</td>
                            <td>Modéré</td>
                            <td>Confirmé</td>
                        </tr>
                    </tbody>
                </table>
            </section>
        </body>
    </html>
    """

    print("🧪 Processing test HTML with Allergies section (48765-2)...")

    result = processor.process_clinical_sections(
        cda_content=test_html, source_language="fr"
    )

    print(f"✅ Processing completed")
    print(f"📊 Result keys: {list(result.keys())}")
    print(f"🏥 Content type: {result.get('content_type', 'unknown')}")
    print(f"📋 Sections count: {result.get('sections_count', 0)}")

    sections = result.get("sections", [])
    if sections:
        allergy_section = sections[0]  # Should be our allergies section

        print(f"\n🔍 Analyzing first section:")
        print(f"   Section Code: {allergy_section.get('section_code', 'None')}")
        print(f"   Title: {allergy_section.get('title', {}).get('original', 'None')}")
        print(f"   Has PS Table: {allergy_section.get('has_ps_table', False)}")

        # Check for table_data (our value set integration)
        table_data = allergy_section.get("table_data", [])
        print(f"   Table Data Entries: {len(table_data)}")

        if table_data:
            first_entry = table_data[0]
            print(f"   First Entry Type: {first_entry.get('type', 'unknown')}")

            fields = first_entry.get("fields", {})
            print(f"   Fields with Value Set Support: {len(fields)}")

            for field_name, field_info in fields.items():
                value = field_info.get("value", "No value")
                original = field_info.get("original_value", value)
                has_valueset = field_info.get("has_valueset", False)

                print(f"     {field_name}: '{value}'")
                if original != value:
                    print(f"       (Translated from: '{original}')")
                if has_valueset:
                    print(f"       (Uses Value Set: {has_valueset})")
        else:
            print(
                "   ❌ No table_data found - value set integration may not be working"
            )
    else:
        print("❌ No sections found in result")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
