#!/usr/bin/env python3
"""
Debug script to check if vaccination data is being mixed with allergy data
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()


def debug_section_data_confusion():
    """Debug if vaccination data is being sent to allergy sections"""
    print("🔍 Debugging Section Data Confusion")
    print("=" * 60)

    # Import after Django setup
    from patient_data.models import Patient
    from patient_data.services.enhanced_cda_processor import EnhancedCDAProcessor
    from patient_data.services import EUPatientSearchService

    try:
        # Find Portuguese patient
        portuguese_patient = Patient.objects.filter(
            first_name__icontains="Diana", last_name__icontains="Ferreira"
        ).first()

        if not portuguese_patient:
            print("❌ Portuguese patient Diana Ferreira not found")
            return False

        print(
            f"✅ Found Portuguese patient: {portuguese_patient.first_name} {portuguese_patient.last_name}"
        )

        # Get patient's CDA content (simulate what the view does)
        search_service = EUPatientSearchService()

        # Find patient matches to get CDA content
        search_results = search_service.search_patient_by_demographics(
            given_name=portuguese_patient.first_name,
            family_name=portuguese_patient.last_name,
            birth_date=portuguese_patient.birth_date,
            gender=portuguese_patient.gender,
        )

        if not search_results:
            print("❌ No search results found for Portuguese patient")
            return False

        # Get the first match (best confidence)
        search_result = search_results[0]
        cda_content, cda_type = search_result.get_rendering_cda()

        if not cda_content:
            print("❌ No CDA content found")
            return False

        print(f"✅ Found CDA content: {len(cda_content)} characters ({cda_type})")

        # Process with Enhanced CDA Processor
        processor = EnhancedCDAProcessor(target_language="en")
        result = processor.process_clinical_sections(
            cda_content=cda_content, source_language="pt"
        )

        if not result.get("success"):
            print("❌ CDA processing failed")
            return False

        print(
            f"✅ CDA processing successful: {len(result.get('sections', []))} sections"
        )

        # Analyze each section for data confusion
        sections = result.get("sections", [])

        print("\n🔍 Section Analysis:")
        print("-" * 40)

        for i, section in enumerate(sections):
            title = section.get("title", "Unknown")
            section_code = section.get("section_code", "Unknown")
            content = section.get("content", "")
            ps_table_html = section.get("ps_table_html", "")

            print(f"\nSection {i+1}: {title}")
            print(f"  Code: {section_code}")
            print(f"  Content type: {type(content)}")
            print(f"  Has PS table: {bool(ps_table_html)}")

            # Check for specific data patterns
            content_str = str(content)

            # Look for vaccination-related terms in allergy sections
            if section_code == "48765-2":  # Allergies section
                print(f"  🚨 ALLERGY SECTION ANALYSIS:")
                vaccination_keywords = [
                    "vaccination",
                    "vaccine",
                    "immunization",
                    "hepatitis",
                    "influenza",
                    "covid",
                    "pfizer",
                    "moderna",
                    "dose",
                ]

                found_vaccination_terms = []
                for keyword in vaccination_keywords:
                    if keyword.lower() in content_str.lower():
                        found_vaccination_terms.append(keyword)

                if found_vaccination_terms:
                    print(
                        f"    ❌ VACCINATION TERMS IN ALLERGY SECTION: {found_vaccination_terms}"
                    )
                else:
                    print(f"    ✅ No vaccination terms found in allergy section")

                # Check PS table for vaccination data
                if ps_table_html:
                    ps_vaccination_terms = []
                    for keyword in vaccination_keywords:
                        if keyword.lower() in ps_table_html.lower():
                            ps_vaccination_terms.append(keyword)

                    if ps_vaccination_terms:
                        print(
                            f"    ❌ VACCINATION TERMS IN ALLERGY PS TABLE: {ps_vaccination_terms}"
                        )
                    else:
                        print(f"    ✅ No vaccination terms in allergy PS table")

            # Look for allergy-related terms in vaccination sections
            elif section_code == "10157-6":  # Immunizations section
                print(f"  🚨 IMMUNIZATION SECTION ANALYSIS:")
                allergy_keywords = [
                    "allergy",
                    "allergic",
                    "intolerance",
                    "adverse",
                    "reaction",
                    "anaphylaxis",
                    "rash",
                    "hives",
                    "sensitivity",
                ]

                found_allergy_terms = []
                for keyword in allergy_keywords:
                    if keyword.lower() in content_str.lower():
                        found_allergy_terms.append(keyword)

                if found_allergy_terms:
                    print(
                        f"    ❌ ALLERGY TERMS IN IMMUNIZATION SECTION: {found_allergy_terms}"
                    )
                else:
                    print(f"    ✅ No allergy terms found in immunization section")

            # Show first 200 characters of content for inspection
            content_preview = (
                content_str[:200] + "..." if len(content_str) > 200 else content_str
            )
            print(f"  Content preview: {content_preview}")

            # If this section has a PS table, show first 200 characters
            if ps_table_html:
                ps_preview = (
                    ps_table_html[:200] + "..."
                    if len(ps_table_html) > 200
                    else ps_table_html
                )
                print(f"  PS table preview: {ps_preview}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run the debug analysis"""
    print("🚀 Section Data Confusion Debug")
    print("Checking if vaccination data is mixed with allergy data")
    print()

    success = debug_section_data_confusion()

    print("\n📋 Debug Summary")
    print("=" * 60)

    if success:
        print("✅ Debug completed successfully")
        print("Check the section analysis above for data confusion patterns")
    else:
        print("❌ Debug failed - check error messages above")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
