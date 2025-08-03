#!/usr/bin/env python
"""
Test PSTableRenderer fixes with actual Django services
"""

import os
import sys
import django

# Set up Django environment
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")

try:
    django.setup()

    # Import Django services
    from patient_data.services.cda_translation_service import CDATranslationService
    from patient_data.services.ps_table_renderer import PSTableRenderer

    def test_actual_services():
        """Test with actual Django services"""

        # Sample CDA content from user's example
        sample_cda_html = """
        <html>
            <body>
                <section>
                    <h3 id="section-10160-0" data-code="10160-0">History of Medication Use</h3>
                    <div class="section-content">
                        <table>
                            <thead>
                                <tr><th>Medication</th><th>Dosage</th><th>Frequency</th></tr>
                            </thead>
                            <tbody>
                                <tr><td>Aspirin</td><td>100mg</td><td>Once daily</td></tr>
                                <tr><td>Metformin</td><td>500mg</td><td>Twice daily</td></tr>
                            </tbody>
                        </table>
                    </div>
                </section>
                
                <section>
                    <h3 id="section-48765-2" data-code="48765-2">Allergies and Intolerances</h3>
                    <div class="section-content">
                        <table>
                            <thead>
                                <tr><th>Allergy Type</th><th>Causative Agent</th><th>Manifestation</th><th>Severity</th></tr>
                            </thead>
                            <tbody>
                                <tr><td>Drug allergy</td><td>Penicillin</td><td>Skin rash</td><td>Moderate</td></tr>
                            </tbody>
                        </table>
                    </div>
                </section>
            </body>
        </html>
        """

        print("=== Testing Django Services ===")
        print("Testing CDA translation and PS table rendering with actual services...")

        # Test the actual services
        try:
            # Create translation service
            service = CDATranslationService(target_language="en")
            print("✅ CDATranslationService created successfully")

            # Parse CDA content
            cda_data = service.parse_cda_html(sample_cda_html)
            print(f"✅ CDA parsed: {len(cda_data['sections'])} sections found")

            for section in cda_data["sections"]:
                print(f"   - {section['title']} (Code: {section['section_code']})")
                print(
                    f"     Content preserved: {'<table>' in section.get('content', '')}"
                )

            # Create bilingual document with table rendering
            bilingual_data = service.create_bilingual_document(cda_data)
            print(
                f"✅ Bilingual document created with {len(bilingual_data['sections'])} sections"
            )

            # Check results
            success_count = 0
            for section in bilingual_data["sections"]:
                section_title = section.get(
                    "title_original", section.get("title_translated", "Unknown")
                )
                has_ps_table = bool(section.get("ps_table_html", ""))

                print(f"\n   Section: {section_title}")
                print(f"   Code: {section.get('section_code', 'N/A')}")
                print(f"   Has PS table: {has_ps_table}")

                if has_ps_table:
                    success_count += 1
                    ps_table_html = section.get("ps_table_html", "")
                    print(f"   PS table preview: {ps_table_html[:150]}...")
                else:
                    print("   ❌ No PS table generated")

            print(f"\n=== Results Summary ===")
            print(
                f"Sections with PS tables: {success_count}/{len(bilingual_data['sections'])}"
            )

            if success_count >= 2:
                print("✅ SUCCESS: PSTableRenderer is working correctly!")
                print("✅ Table content extraction is fixed!")
            else:
                print("❌ ISSUE: Some sections are not generating PS tables")

        except Exception as e:
            print(f"❌ Error testing services: {e}")
            import traceback

            traceback.print_exc()

    if __name__ == "__main__":
        test_actual_services()

except Exception as e:
    print(f"Django setup error: {e}")
    print("Note: This test requires a proper Django environment")
