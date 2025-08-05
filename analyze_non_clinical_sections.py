#!/usr/bin/env python3
"""
Non-Clinical CDA Sections Analysis
Analyze CDA documents to identify all non-clinical sections that need parsing
"""

import os
import sys
import django
from pathlib import Path
import xml.etree.ElementTree as ET
from collections import defaultdict

# Add the Django project path
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()


def analyze_non_clinical_sections():
    """Analyze CDA documents to identify non-clinical sections and administrative data"""

    print("🔍 NON-CLINICAL CDA SECTIONS ANALYSIS")
    print("=" * 70)

    # Test with Italian L3 file
    test_file = Path(
        "test_data/eu_member_states/IT/2025-03-28T13-29-59.727799Z_CDA_EHDSI---FRIENDLY-CDA-(L3)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"
    )

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return

    print(f"📄 Analyzing: {test_file.name}")

    with open(test_file, "r", encoding="utf-8") as f:
        xml_content = f.read()

    try:
        root = ET.fromstring(xml_content)

        # 1. DOCUMENT HEADER ANALYSIS
        print(f"\\n📋 DOCUMENT HEADER INFORMATION")
        print("-" * 70)

        # Document metadata
        doc_id = root.find(".//{urn:hl7-org:v3}id")
        if doc_id is not None:
            print(
                f"Document ID: {doc_id.get('extension', 'N/A')} (root: {doc_id.get('root', 'N/A')})"
            )

        # Document title
        title = root.find(".//{urn:hl7-org:v3}title")
        if title is not None:
            print(f"Document Title: {title.text}")

        # Creation date
        effective_time = root.find(".//{urn:hl7-org:v3}effectiveTime")
        if effective_time is not None:
            print(f"Creation Date: {effective_time.get('value', 'N/A')}")

        # Document type
        code = root.find(".//{urn:hl7-org:v3}code")
        if code is not None:
            print(
                f"Document Type: {code.get('code', 'N/A')} - {code.get('displayName', 'N/A')}"
            )
            print(f"Code System: {code.get('codeSystem', 'N/A')}")

        # Confidentiality
        confidentiality = root.find(".//{urn:hl7-org:v3}confidentialityCode")
        if confidentiality is not None:
            print(
                f"Confidentiality: {confidentiality.get('code', 'N/A')} - {confidentiality.get('displayName', 'N/A')}"
            )

        # Language
        language = root.find(".//{urn:hl7-org:v3}languageCode")
        if language is not None:
            print(f"Language: {language.get('code', 'N/A')}")

        # 2. PATIENT DEMOGRAPHICS
        print(f"\\n👤 PATIENT DEMOGRAPHICS")
        print("-" * 70)

        # Patient record target
        patient_role = root.find(
            ".//{urn:hl7-org:v3}recordTarget/{urn:hl7-org:v3}patientRole"
        )
        if patient_role is not None:
            # Patient ID
            patient_id = patient_role.find("{urn:hl7-org:v3}id")
            if patient_id is not None:
                print(
                    f"Patient ID: {patient_id.get('extension', 'N/A')} (root: {patient_id.get('root', 'N/A')})"
                )

            # Patient name
            patient = patient_role.find("{urn:hl7-org:v3}patient")
            if patient is not None:
                name = patient.find("{urn:hl7-org:v3}name")
                if name is not None:
                    given = name.find("{urn:hl7-org:v3}given")
                    family = name.find("{urn:hl7-org:v3}family")
                    print(
                        f"Patient Name: {given.text if given is not None else 'N/A'} {family.text if family is not None else 'N/A'}"
                    )

                # Birth date
                birth_time = patient.find("{urn:hl7-org:v3}birthTime")
                if birth_time is not None:
                    print(f"Birth Date: {birth_time.get('value', 'N/A')}")

                # Gender
                gender = patient.find("{urn:hl7-org:v3}administrativeGenderCode")
                if gender is not None:
                    print(
                        f"Gender: {gender.get('code', 'N/A')} - {gender.get('displayName', 'N/A')}"
                    )

            # Address
            addr = patient_role.find("{urn:hl7-org:v3}addr")
            if addr is not None:
                street = addr.find("{urn:hl7-org:v3}streetAddressLine")
                city = addr.find("{urn:hl7-org:v3}city")
                postal = addr.find("{urn:hl7-org:v3}postalCode")
                country = addr.find("{urn:hl7-org:v3}country")

                address_parts = []
                if street is not None:
                    address_parts.append(street.text)
                if city is not None:
                    address_parts.append(city.text)
                if postal is not None:
                    address_parts.append(postal.text)
                if country is not None:
                    address_parts.append(country.text)

                if address_parts:
                    print(f"Address: {', '.join(address_parts)}")

        # 3. AUTHOR INFORMATION
        print(f"\\n✍️  AUTHOR INFORMATION")
        print("-" * 70)

        authors = root.findall(".//{urn:hl7-org:v3}author")
        for i, author in enumerate(authors, 1):
            print(f"Author {i}:")

            # Author time
            time_elem = author.find("{urn:hl7-org:v3}time")
            if time_elem is not None:
                print(f"  Time: {time_elem.get('value', 'N/A')}")

            # Assigned author
            assigned_author = author.find("{urn:hl7-org:v3}assignedAuthor")
            if assigned_author is not None:
                # Author ID
                author_id = assigned_author.find("{urn:hl7-org:v3}id")
                if author_id is not None:
                    print(f"  ID: {author_id.get('extension', 'N/A')}")

                # Author name
                assigned_person = assigned_author.find("{urn:hl7-org:v3}assignedPerson")
                if assigned_person is not None:
                    name = assigned_person.find("{urn:hl7-org:v3}name")
                    if name is not None:
                        given = name.find("{urn:hl7-org:v3}given")
                        family = name.find("{urn:hl7-org:v3}family")
                        print(
                            f"  Name: {given.text if given is not None else 'N/A'} {family.text if family is not None else 'N/A'}"
                        )

                # Organization
                org = assigned_author.find("{urn:hl7-org:v3}representedOrganization")
                if org is not None:
                    org_name = org.find("{urn:hl7-org:v3}name")
                    if org_name is not None:
                        print(f"  Organization: {org_name.text}")

        # 4. CUSTODIAN INFORMATION
        print(f"\\n🏥 CUSTODIAN INFORMATION")
        print("-" * 70)

        custodian = root.find(".//{urn:hl7-org:v3}custodian")
        if custodian is not None:
            assigned_custodian = custodian.find("{urn:hl7-org:v3}assignedCustodian")
            if assigned_custodian is not None:
                org = assigned_custodian.find(
                    "{urn:hl7-org:v3}representedCustodianOrganization"
                )
                if org is not None:
                    # Organization ID
                    org_id = org.find("{urn:hl7-org:v3}id")
                    if org_id is not None:
                        print(f"Custodian ID: {org_id.get('extension', 'N/A')}")

                    # Organization name
                    org_name = org.find("{urn:hl7-org:v3}name")
                    if org_name is not None:
                        print(f"Custodian Name: {org_name.text}")

        # 5. LEGAL AUTHENTICATOR
        print(f"\\n⚖️  LEGAL AUTHENTICATOR")
        print("-" * 70)

        legal_auth = root.find(".//{urn:hl7-org:v3}legalAuthenticator")
        if legal_auth is not None:
            # Time
            time_elem = legal_auth.find("{urn:hl7-org:v3}time")
            if time_elem is not None:
                print(f"Authentication Time: {time_elem.get('value', 'N/A')}")

            # Signature code
            sig_code = legal_auth.find("{urn:hl7-org:v3}signatureCode")
            if sig_code is not None:
                print(f"Signature Code: {sig_code.get('code', 'N/A')}")

            # Assigned entity
            assigned_entity = legal_auth.find("{urn:hl7-org:v3}assignedEntity")
            if assigned_entity is not None:
                # Entity ID
                entity_id = assigned_entity.find("{urn:hl7-org:v3}id")
                if entity_id is not None:
                    print(f"Authenticator ID: {entity_id.get('extension', 'N/A')}")

        # 6. DOCUMENT RELATIONSHIPS
        print(f"\\n🔗 DOCUMENT RELATIONSHIPS")
        print("-" * 70)

        related_docs = root.findall(".//{urn:hl7-org:v3}relatedDocument")
        for i, rel_doc in enumerate(related_docs, 1):
            print(f"Related Document {i}:")
            print(f"  Type: {rel_doc.get('typeCode', 'N/A')}")

            parent_doc = rel_doc.find("{urn:hl7-org:v3}parentDocument")
            if parent_doc is not None:
                doc_id = parent_doc.find("{urn:hl7-org:v3}id")
                if doc_id is not None:
                    print(f"  Parent ID: {doc_id.get('extension', 'N/A')}")

        # 7. ANALYZE ALL SECTIONS
        print(f"\\n📑 ALL SECTIONS ANALYSIS")
        print("-" * 70)

        sections = root.findall(".//{urn:hl7-org:v3}section")
        section_types = defaultdict(int)

        for section in sections:
            code_elem = section.find("{urn:hl7-org:v3}code")
            title_elem = section.find("{urn:hl7-org:v3}title")

            code_value = (
                code_elem.get("code", "NO_CODE") if code_elem is not None else "NO_CODE"
            )
            title_text = title_elem.text if title_elem is not None else "NO_TITLE"

            section_types[f"{code_value}: {title_text}"] += 1

        print(f"Found {len(sections)} total sections:")
        for section_type, count in section_types.items():
            print(f"  - {section_type} ({count})")

        # 8. RECOMMENDATIONS
        print(f"\\n💡 NON-CLINICAL PARSER RECOMMENDATIONS")
        print("-" * 70)
        print(
            "Based on this analysis, we need a Non-Clinical CDA Parser that extracts:"
        )
        print("\\n🔧 ADMINISTRATIVE DATA:")
        print("  - Document metadata (ID, title, creation date, type)")
        print("  - Document classification (confidentiality, language)")
        print("  - Document relationships and versioning")

        print("\\n👤 PATIENT DEMOGRAPHICS:")
        print("  - Complete patient identity (ID, name, birth date, gender)")
        print("  - Patient contact information (address, telecom)")
        print("  - Patient identifiers across healthcare systems")

        print("\\n🏥 HEALTHCARE PROVIDERS:")
        print("  - Author information (who created the document)")
        print("  - Custodian information (who maintains the document)")
        print("  - Legal authenticators (who signed/approved)")
        print("  - Healthcare organizations and roles")

        print("\\n📋 DOCUMENT STRUCTURE:")
        print("  - Section organization and hierarchy")
        print("  - Non-clinical section content")
        print("  - Document formatting and presentation metadata")

        return {
            "total_sections": len(sections),
            "section_types": dict(section_types),
            "has_patient_data": patient_role is not None,
            "has_authors": len(authors) > 0,
            "has_custodian": custodian is not None,
            "has_legal_auth": legal_auth is not None,
        }

    except Exception as e:
        print(f"❌ Error analyzing CDA: {e}")
        import traceback

        print(f"🔥 Traceback:\\n{traceback.format_exc()}")
        return None


if __name__ == "__main__":
    analyze_non_clinical_sections()
