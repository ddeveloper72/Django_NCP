#!/usr/bin/env python3
"""
Test the CDA display viewer with the Portuguese Wave 7 document
This will verify that clinical tables are properly populated with real data
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")

try:
    django.setup()
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)


def test_wave7_cda_display():
    """Test the CDA display viewer with Wave 7 Portuguese test data"""

    print("🇵🇹 Testing CDA Display Viewer with Wave 7 Data")
    print("=" * 60)

    # Load the Wave 7 CDA document
    cda_path = "test_data/eu_member_states/PT/2-1234-W7.xml"

    try:
        with open(cda_path, "r", encoding="utf-8") as file:
            cda_content = file.read()
        print(f"✅ Loaded Wave 7 CDA: {len(cda_content)} characters")
    except FileNotFoundError:
        print(f"❌ CDA file not found: {cda_path}")
        return

    # Import the Enhanced CDA Processor
    try:
        from patient_data.services.enhanced_cda_processor import EnhancedCDAProcessor

        print("✅ Enhanced CDA Processor imported")
    except ImportError as e:
        print(f"❌ Failed to import Enhanced CDA Processor: {e}")
        return

    # Initialize processor
    processor = EnhancedCDAProcessor(target_language="en")
    print("✅ Enhanced CDA Processor initialized")

    # Process the clinical sections
    print("\n🔄 Processing Clinical Sections...")
    try:
        result = processor.process_clinical_sections(
            cda_content=cda_content, source_language="en"
        )

        if result.get("success"):
            sections = result.get("sections", [])
            print(f"✅ Processing successful: {len(sections)} sections processed")

            # Analyze each section for table data
            print("\n📊 Section-by-Section Table Population Analysis:")
            print("-" * 50)

            for i, section in enumerate(sections):
                title = section.get("title", {})
                section_title = (
                    title.get("translated", "Unknown Section")
                    if isinstance(title, dict)
                    else str(title)
                )

                structured_data = section.get("structured_data", [])
                table_rows = section.get("table_rows", [])
                has_ps_table = section.get("has_ps_table", False)
                ps_table_html = section.get("ps_table_html", "")

                print(f"\n📋 Section {i+1}: {section_title}")
                print(f"   Code: {section.get('section_code', 'N/A')}")
                print(f"   Structured Data Items: {len(structured_data)}")
                print(
                    f"   Table Rows Generated: {len(table_rows) if isinstance(table_rows, list) else 'Invalid format'}"
                )
                print(f"   PS-Compliant Table: {'Yes' if has_ps_table else 'No'}")
                print(f"   HTML Table Size: {len(ps_table_html)} characters")

                # Show structured data details for key sections
                if len(structured_data) > 0:
                    print(f"   📝 Structured Data Sample:")
                    for j, item in enumerate(structured_data[:2]):  # Show first 2 items
                        item_data = item.get("data", {})
                        item_type = item.get("section_type", "unknown")
                        print(
                            f"      Item {j+1} ({item_type}): {list(item_data.keys())}"
                        )

                        # Show specific clinical data based on section type
                        if item_type == "observation":
                            condition = item_data.get(
                                "condition_display", item_data.get("value", "N/A")
                            )
                            status = item_data.get("status", "N/A")
                            print(f"         Condition: {condition}")
                            print(f"         Status: {status}")
                        elif item_type == "medication":
                            med_name = item_data.get(
                                "medication_display", item_data.get("name", "N/A")
                            )
                            dosage = item_data.get("dosage", "N/A")
                            print(f"         Medication: {med_name}")
                            print(f"         Dosage: {dosage}")

                # Check for actual table content
                if has_ps_table and ps_table_html:
                    # Look for actual clinical data in the HTML
                    html_lower = ps_table_html.lower()
                    has_real_data = any(
                        term in html_lower
                        for term in [
                            "eutirox",
                            "triapin",
                            "tresiba",
                            "augmentin",
                            "combivent",  # Medications
                            "hypertension",
                            "diabetes",
                            "allergy",
                            "kiwi",
                            "latex",  # Conditions/Allergies
                            "diana",
                            "ferreira",  # Patient name
                        ]
                    )

                    print(
                        f"   🎯 Real Clinical Data in Table: {'Yes' if has_real_data else 'No'}"
                    )

                    if has_real_data:
                        print(f"   ✅ SUCCESS: Table contains actual clinical data!")
                    else:
                        print(f"   ❌ WARNING: Table may contain placeholder data")
                else:
                    print(f"   ❌ No PS-compliant table generated")

                if len(structured_data) > 2:
                    print(f"      ... and {len(structured_data) - 2} more items")

            # Overall assessment
            print(f"\n🎯 Overall Assessment:")
            print("-" * 30)

            total_structured = sum(len(s.get("structured_data", [])) for s in sections)
            sections_with_tables = sum(
                1 for s in sections if s.get("has_ps_table", False)
            )
            sections_with_data = sum(
                1 for s in sections if len(s.get("structured_data", [])) > 0
            )

            print(f"📊 Total structured data items extracted: {total_structured}")
            print(
                f"📋 Sections with PS-compliant tables: {sections_with_tables}/{len(sections)}"
            )
            print(
                f"🔬 Sections with structured data: {sections_with_data}/{len(sections)}"
            )

            # Check specific clinical sections
            medication_section = next(
                (s for s in sections if s.get("section_code") == "10160-0"), None
            )
            allergy_section = next(
                (s for s in sections if s.get("section_code") == "48765-2"), None
            )
            problem_section = next(
                (s for s in sections if s.get("section_code") == "11450-4"), None
            )

            print(f"\n🏥 Key Clinical Sections:")
            if medication_section:
                med_data = len(medication_section.get("structured_data", []))
                med_table = medication_section.get("has_ps_table", False)
                print(
                    f"   💊 Medications: {med_data} items, Table: {'Yes' if med_table else 'No'}"
                )

            if allergy_section:
                allergy_data = len(allergy_section.get("structured_data", []))
                allergy_table = allergy_section.get("has_ps_table", False)
                print(
                    f"   🚨 Allergies: {allergy_data} items, Table: {'Yes' if allergy_table else 'No'}"
                )

            if problem_section:
                problem_data = len(problem_section.get("structured_data", []))
                problem_table = problem_section.get("has_ps_table", False)
                print(
                    f"   📋 Problems: {problem_data} items, Table: {'Yes' if problem_table else 'No'}"
                )

            # Final verdict
            success_rate = (
                (sections_with_tables / len(sections)) * 100 if sections else 0
            )
            print(f"\n🎖️  Table Population Success Rate: {success_rate:.1f}%")

            if success_rate >= 80:
                print("🏆 EXCELLENT: CDA display viewer is working properly!")
            elif success_rate >= 60:
                print("✅ GOOD: Most tables are being populated correctly")
            elif success_rate >= 40:
                print("⚠️  MODERATE: Some tables are missing, needs investigation")
            else:
                print("❌ POOR: Significant issues with table population")

        else:
            print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Processing failed with exception: {e}")
        import traceback

        traceback.print_exc()


def test_individual_section_extraction():
    """Test extraction of specific sections to verify data mapping"""

    print("\n🔬 Individual Section Data Extraction Test:")
    print("-" * 50)

    # Test with a specific medication entry from the Wave 7 document
    medication_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:pharm="urn:hl7-org:pharm">
        <component>
            <structuredBody>
                <component>
                    <section>
                        <code code="10160-0" displayName="History of medication use" codeSystem="2.16.840.1.113883.6.1"/>
                        <title>History of Medication use</title>
                        <entry>
                            <substanceAdministration classCode="SBADM" moodCode="INT">
                                <statusCode code="active"/>
                                <consumable>
                                    <manufacturedProduct>
                                        <manufacturedMaterial>
                                            <name>Eutirox</name>
                                            <pharm:ingredient classCode="ACTI">
                                                <pharm:ingredientSubstance>
                                                    <pharm:code code="H03AA01" codeSystem="2.16.840.1.113883.6.73"/>
                                                </pharm:ingredientSubstance>
                                            </pharm:ingredient>
                                        </manufacturedMaterial>
                                    </manufacturedProduct>
                                </consumable>
                            </substanceAdministration>
                        </entry>
                    </section>
                </component>
            </structuredBody>
        </component>
    </ClinicalDocument>"""

    try:
        from patient_data.services.enhanced_cda_processor import EnhancedCDAProcessor

        processor = EnhancedCDAProcessor(target_language="en")

        result = processor.process_clinical_sections(
            cda_content=medication_xml, source_language="en"
        )

        if result.get("success"):
            sections = result.get("sections", [])
            if sections:
                section = sections[0]
                structured_data = section.get("structured_data", [])

                print(f"✅ Medication extraction test:")
                print(f"   Structured data items: {len(structured_data)}")

                if structured_data:
                    med_data = structured_data[0].get("data", {})
                    print(f"   Medication data keys: {list(med_data.keys())}")
                    print(
                        f"   Medication name: {med_data.get('medication_display', 'N/A')}"
                    )
                    print(f"   Status: {med_data.get('status', 'N/A')}")
                else:
                    print(f"   ❌ No structured data extracted")
            else:
                print(f"   ❌ No sections processed")
        else:
            print(f"   ❌ Processing failed")

    except Exception as e:
        print(f"   ❌ Individual test failed: {e}")


if __name__ == "__main__":
    test_wave7_cda_display()
    test_individual_section_extraction()
