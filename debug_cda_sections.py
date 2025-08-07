#!/usr/bin/env python3
"""
Check what sections are actually being identified in the Portuguese CDA content
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()


def debug_cda_section_identification():
    """Debug what sections are being identified in the Portuguese CDA"""
    print("🔍 CDA Section Identification Debug")
    print("=" * 60)

    # Import after Django setup
    from patient_data.models import Patient
    from patient_data.services import EUPatientSearchService
    from bs4 import BeautifulSoup
    import xml.etree.ElementTree as ET

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

        # Get patient's CDA content
        search_service = EUPatientSearchService()
        search_results = search_service.search_patient_by_demographics(
            given_name=portuguese_patient.first_name,
            family_name=portuguese_patient.last_name,
            birth_date=portuguese_patient.birth_date,
            gender=portuguese_patient.gender,
        )

        if not search_results:
            print("❌ No search results found")
            return False

        search_result = search_results[0]
        cda_content, cda_type = search_result.get_rendering_cda()

        if not cda_content:
            print("❌ No CDA content found")
            return False

        print(f"✅ Found CDA content: {len(cda_content)} characters ({cda_type})")

        # Parse and analyze the CDA structure
        print("\n🔍 Raw CDA Section Analysis:")
        print("-" * 40)

        # Try parsing as XML first
        try:
            root = ET.fromstring(cda_content)
            namespaces = {"hl7": "urn:hl7-org:v3"}

            sections = root.findall(".//hl7:section", namespaces)
            print(f"Found {len(sections)} XML sections")

            for i, section in enumerate(sections):
                code_elem = section.find("hl7:code", namespaces)
                title_elem = section.find("hl7:title", namespaces)

                if code_elem is not None:
                    section_code = code_elem.get("code", "Unknown")
                    section_name = (
                        title_elem.text if title_elem is not None else "Unknown"
                    )

                    print(f"\nSection {i+1}: {section_name}")
                    print(f"  Code: {section_code}")

                    # Check what this section code should be
                    expected_sections = {
                        "48765-2": "Allergies and Adverse Reactions",
                        "10157-6": "History of Immunization",
                        "10160-0": "History of Medication use",
                        "11450-4": "Problem List",
                        "47519-4": "History of Procedures",
                    }

                    expected = expected_sections.get(
                        section_code, "Unknown section type"
                    )
                    print(f"  Expected: {expected}")

                    if section_code == "48765-2":
                        print("  🚨 THIS IS THE ALLERGIES SECTION")
                    elif section_code == "10157-6":
                        print("  🚨 THIS IS THE IMMUNIZATIONS SECTION")

                    # Extract entries in this section
                    entries = section.findall(".//hl7:entry", namespaces)
                    print(f"  Entries: {len(entries)}")

                    # For allergy and immunization sections, show more detail
                    if section_code in ["48765-2", "10157-6"]:
                        print(f"  🔍 Detailed Analysis of {expected}:")

                        for j, entry in enumerate(entries[:3]):  # Show first 3 entries
                            observation = entry.find(".//hl7:observation", namespaces)
                            if observation is not None:
                                # Check the observation type
                                code = observation.find("hl7:code", namespaces)
                                value = observation.find("hl7:value", namespaces)

                                if code is not None:
                                    obs_code = code.get("code", "")
                                    obs_display = code.get("displayName", "")
                                    print(
                                        f"    Entry {j+1}: {obs_display} ({obs_code})"
                                    )

                                if value is not None:
                                    val_display = value.get("displayName", "")
                                    val_code = value.get("code", "")
                                    print(f"      Value: {val_display} ({val_code})")

        except ET.ParseError:
            print("CDA is not valid XML, trying HTML parsing...")

            # Try parsing as HTML
            soup = BeautifulSoup(cda_content, "html.parser")
            sections = soup.find_all(
                ["div", "section"], class_=lambda x: x and "section" in x
            ) or soup.find_all("h3")

            print(f"Found {len(sections)} HTML sections")

            for i, section in enumerate(sections[:10]):  # Show first 10
                text = section.get_text(strip=True)[:100]
                print(f"Section {i+1}: {text}...")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run the CDA section identification debug"""
    print("🚀 CDA Section Identification Debug")
    print("Checking what sections are in the Portuguese CDA")
    print()

    success = debug_cda_section_identification()

    print("\n📋 Debug Summary")
    print("=" * 60)

    if success:
        print("✅ CDA analysis completed")
        print("Check the section details above to see if data is in wrong sections")
    else:
        print("❌ CDA analysis failed")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
