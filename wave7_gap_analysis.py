#!/usr/bin/env python3
"""
Comprehensive Gap Analysis for Portuguese Wave 7 eHDSI Test CDA Document
This document was created by an eHDSI solution provider and contains rich clinical data
"""

import os
import sys
import xml.etree.ElementTree as ET

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")

try:
    import django

    django.setup()
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)


def analyze_wave7_cda():
    """Comprehensive analysis of the Portuguese Wave 7 CDA document"""

    print("🇵🇹 Portuguese Wave 7 eHDSI Test CDA Analysis")
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

    print("\n📋 Manual Structure Analysis:")
    print("-" * 40)

    # Parse the CDA
    root = ET.fromstring(cda_content)
    namespaces = {"hl7": "urn:hl7-org:v3", "pharm": "urn:hl7-org:pharm"}

    # Extract document metadata
    doc_id = root.find(".//hl7:id", namespaces)
    if doc_id is not None:
        print(f"📄 Document ID: {doc_id.get('extension', 'N/A')}")

    language_code = root.find(".//hl7:languageCode", namespaces)
    if language_code is not None:
        print(f"🌐 Language: {language_code.get('code', 'N/A')}")

    # Extract patient information
    patient = root.find(".//hl7:patient", namespaces)
    if patient is not None:
        given_name = patient.find(".//hl7:given", namespaces)
        family_name = patient.find(".//hl7:family", namespaces)
        birth_time = patient.find(".//hl7:birthTime", namespaces)
        gender = patient.find(".//hl7:administrativeGenderCode", namespaces)

        print(
            f"👤 Patient: {given_name.text if given_name is not None else 'N/A'} {family_name.text if family_name is not None else 'N/A'}"
        )
        print(
            f"🎂 Birth: {birth_time.get('value', 'N/A') if birth_time is not None else 'N/A'}"
        )
        print(
            f"⚥ Gender: {gender.get('displayName', 'N/A') if gender is not None else 'N/A'}"
        )

    # Analyze clinical sections
    sections = root.findall(".//hl7:section", namespaces)
    print(f"\n📊 Found {len(sections)} clinical sections:")

    section_analysis = []

    for i, section in enumerate(sections):
        section_info = {"number": i + 1}

        # Extract section code and title
        code_elem = section.find("hl7:code", namespaces)
        title_elem = section.find("hl7:title", namespaces)

        if code_elem is not None:
            section_info["code"] = code_elem.get("code", "N/A")
            section_info["display"] = code_elem.get("displayName", "N/A")
        else:
            section_info["code"] = "No Code"
            section_info["display"] = "Unknown Section"

        if title_elem is not None:
            section_info["title"] = title_elem.text or "Untitled"
        else:
            section_info["title"] = "No Title"

        # Count entries
        entries = section.findall("hl7:entry", namespaces)
        section_info["entries"] = len(entries)

        # Analyze entry types
        entry_types = []
        structured_data_count = 0

        for entry in entries:
            # Check for medications
            if entry.find(".//hl7:substanceAdministration", namespaces) is not None:
                entry_types.append("Medication")
                structured_data_count += 1

            # Check for observations (allergies, problems, etc.)
            elif entry.find(".//hl7:observation", namespaces) is not None:
                entry_types.append("Observation")
                structured_data_count += 1

            # Check for procedures
            elif entry.find(".//hl7:procedure", namespaces) is not None:
                entry_types.append("Procedure")
                structured_data_count += 1

            # Check for acts (general activities)
            elif entry.find(".//hl7:act", namespaces) is not None:
                entry_types.append("Act")
                structured_data_count += 1
            else:
                entry_types.append("Other")

        section_info["entry_types"] = entry_types
        section_info["structured_data_count"] = structured_data_count

        # Check for HTML tables
        text_elem = section.find("hl7:text", namespaces)
        has_table = False
        table_rows = 0

        if text_elem is not None:
            # Convert to string and check for tables
            text_content = ET.tostring(text_elem, encoding="unicode")
            has_table = "<table" in text_content or "<tbody" in text_content

            # Count table rows (approximate)
            table_rows = text_content.count("<tr")

        section_info["has_table"] = has_table
        section_info["table_rows"] = table_rows

        section_analysis.append(section_info)

        print(f"\n   Section {i+1}: {section_info['title']}")
        print(f"      Code: {section_info['code']} - {section_info['display']}")
        print(
            f"      Entries: {section_info['entries']} ({', '.join(set(entry_types)) if entry_types else 'None'})"
        )
        print(f"      Structured Data: {structured_data_count} items")
        print(f"      HTML Table: {'Yes' if has_table else 'No'} ({table_rows} rows)")

    print("\n🧪 Testing Enhanced CDA Processor:")
    print("-" * 40)

    # Import and test the Enhanced CDA Processor
    try:
        from patient_data.services.enhanced_cda_processor import EnhancedCDAProcessor

        processor = EnhancedCDAProcessor(target_language="en")
        print("✅ Enhanced CDA Processor initialized")

        # Process the Wave 7 document
        result = processor.process_clinical_sections(
            cda_content=cda_content, source_language="en"  # Document is in English
        )

        if result.get("success"):
            processed_sections = result.get("sections", [])
            print(
                f"✅ Processing successful: {len(processed_sections)} sections processed"
            )

            # Compare manual analysis with processor results
            print(f"\n📊 Comparison Results:")
            print(f"   Manual Analysis: {len(sections)} sections found")
            print(f"   Processor Result: {len(processed_sections)} sections processed")

            total_entries_manual = sum(s["entries"] for s in section_analysis)
            total_structured_manual = sum(
                s["structured_data_count"] for s in section_analysis
            )

            print(
                f"   Manual Analysis: {total_entries_manual} total entries, {total_structured_manual} structured items"
            )

            # Analyze processor results
            for i, proc_section in enumerate(processed_sections):
                if i < len(section_analysis):
                    manual_section = section_analysis[i]

                    print(f"\n   Section {i+1} Comparison:")
                    print(f"      Title: {manual_section['title']}")
                    print(f"      Manual entries: {manual_section['entries']}")
                    print(
                        f"      Manual structured: {manual_section['structured_data_count']}"
                    )
                    print(
                        f"      Processor structured: {len(proc_section.get('structured_data', []))}"
                    )
                    print(
                        f"      Processor table rows: {len(proc_section.get('table_rows', []))}"
                    )

                    # Check if processor found the data
                    if manual_section["structured_data_count"] > 0:
                        if len(proc_section.get("structured_data", [])) > 0:
                            print(f"      ✅ Structured data extraction: SUCCESS")
                        else:
                            print(f"      ❌ Structured data extraction: FAILED")

                    if manual_section["has_table"]:
                        if proc_section.get("has_ps_table", False):
                            print(f"      ✅ Table processing: SUCCESS")
                        else:
                            print(f"      ❌ Table processing: FAILED")
        else:
            print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Enhanced CDA Processor test failed: {e}")
        import traceback

        traceback.print_exc()

    print("\n📋 Clinical Data Richness Assessment:")
    print("-" * 40)

    # Assess the richness of clinical data
    medication_sections = [s for s in section_analysis if s["code"] == "10160-0"]
    allergy_sections = [s for s in section_analysis if s["code"] == "48765-2"]
    procedure_sections = [s for s in section_analysis if s["code"] == "47519-4"]
    problem_sections = [s for s in section_analysis if s["code"] == "11450-4"]

    print(f"🏥 Clinical Content Summary:")
    print(f"   Medication History: {len(medication_sections)} sections")
    if medication_sections:
        med_section = medication_sections[0]
        print(f"      Entries: {med_section['entries']}")
        print(f"      Structured data: {med_section['structured_data_count']}")
        print(f"      Table rows: {med_section['table_rows']}")

    print(f"   Allergies/Adverse Reactions: {len(allergy_sections)} sections")
    if allergy_sections:
        allergy_section = allergy_sections[0]
        print(f"      Entries: {allergy_section['entries']}")
        print(f"      Structured data: {allergy_section['structured_data_count']}")
        print(f"      Table rows: {allergy_section['table_rows']}")

    print(f"   Procedure History: {len(procedure_sections)} sections")
    if procedure_sections:
        proc_section = procedure_sections[0]
        print(f"      Entries: {proc_section['entries']}")
        print(f"      Structured data: {proc_section['structured_data_count']}")
        print(f"      Table rows: {proc_section['table_rows']}")

    print(f"   Problem List: {len(problem_sections)} sections")

    print(f"\n🎯 Gap Analysis Summary:")
    print(
        f"   Total sections with structured data: {len([s for s in section_analysis if s['structured_data_count'] > 0])}"
    )
    print(
        f"   Total sections with HTML tables: {len([s for s in section_analysis if s['has_table']])}"
    )
    print(
        f"   Rich clinical content: {'YES' if any(s['structured_data_count'] > 3 for s in section_analysis) else 'NO'}"
    )
    print(
        f"   Multi-modal data (structured + unstructured): {'YES' if any(s['has_table'] and s['structured_data_count'] > 0 for s in section_analysis) else 'NO'}"
    )


if __name__ == "__main__":
    analyze_wave7_cda()
