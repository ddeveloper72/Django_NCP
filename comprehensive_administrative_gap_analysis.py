#!/usr/bin/env python3
"""
Comprehensive Administrative Gap Analysis
Analyze administrative data availability across all EU member state CDA documents
Compare against PDF display guidelines to identify parsing gaps
"""

import os
import sys
import django
from pathlib import Path
import xml.etree.ElementTree as ET
import json
from collections import defaultdict, Counter
from datetime import datetime

# Add the Django project path
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.services.enhanced_cda_xml_parser import EnhancedCDAXMLParser


class AdministrativeGapAnalyzer:
    """Analyze administrative data gaps across EU member states"""

    def __init__(self):
        self.parser = EnhancedCDAXMLParser()
        self.test_data_path = Path("test_data/eu_member_states")
        self.results = {
            "summary": {},
            "by_country": {},
            "field_availability": defaultdict(int),
            "missing_fields": defaultdict(list),
            "xml_structure_analysis": {},
            "recommendations": [],
        }

        # Define expected fields based on PDF guidelines
        self.expected_fields = {
            "patient_contact": [
                "full_name",
                "given_name",
                "family_name",
                "prefix",
                "suffix",
                "address",
                "city",
                "postal_code",
                "country",
                "state",
                "phone",
                "email",
                "telecoms",
                "birth_date",
                "gender",
                "patient_id",
                "id_authority",
                "id_root",
            ],
            "legal_authenticator": [
                "full_name",
                "given_name",
                "family_name",
                "title",
                "role",
                "organization_name",
                "organization_id",
                "signature_code",
                "time",
                "address",
                "city",
                "postal_code",
                "country",
                "phone",
                "email",
                "telecoms",
            ],
            "custodian": [
                "organization_name",
                "organization_id",
                "address",
                "city",
                "postal_code",
                "country",
                "phone",
                "email",
                "telecoms",
            ],
            "authors": [
                "full_name",
                "given_name",
                "family_name",
                "title",
                "role",
                "organization_name",
                "organization_id",
                "time",
                "address",
                "city",
                "postal_code",
                "country",
                "phone",
                "email",
                "telecoms",
                "author_type",
            ],
        }

    def analyze_xml_structure(self, xml_content, country, filename):
        """Analyze raw XML structure for administrative elements"""
        try:
            root = ET.fromstring(xml_content)

            # Find all administrative elements with their full paths
            admin_elements = {}

            # Patient/RecordTarget analysis
            record_targets = root.findall(".//{urn:hl7-org:v3}recordTarget")
            if record_targets:
                admin_elements["recordTarget"] = self._analyze_record_target(
                    record_targets[0]
                )

            # Legal Authenticator analysis
            legal_auths = root.findall(".//{urn:hl7-org:v3}legalAuthenticator")
            if legal_auths:
                admin_elements["legalAuthenticator"] = (
                    self._analyze_legal_authenticator(legal_auths[0])
                )

            # Custodian analysis
            custodians = root.findall(".//{urn:hl7-org:v3}custodian")
            if custodians:
                admin_elements["custodian"] = self._analyze_custodian(custodians[0])

            # Authors analysis
            authors = root.findall(".//{urn:hl7-org:v3}author")
            if authors:
                admin_elements["authors"] = [
                    self._analyze_author(author) for author in authors
                ]

            return admin_elements

        except Exception as e:
            print(f"❌ XML structure analysis error for {country}/{filename}: {e}")
            return {}

    def _analyze_record_target(self, element):
        """Analyze recordTarget structure"""
        structure = {"found_elements": [], "missing_elements": []}

        # Check for patient role
        patient_role = element.find("{urn:hl7-org:v3}patientRole")
        if patient_role is not None:
            structure["found_elements"].append("patientRole")

            # Check ID
            id_elem = patient_role.find("{urn:hl7-org:v3}id")
            if id_elem is not None:
                structure["found_elements"].append("id")
                structure["id_attributes"] = dict(id_elem.attrib)

            # Check addresses
            addresses = patient_role.findall("{urn:hl7-org:v3}addr")
            if addresses:
                structure["found_elements"].append("addr")
                structure["address_count"] = len(addresses)
                structure["address_details"] = self._analyze_address(addresses[0])

            # Check telecoms
            telecoms = patient_role.findall("{urn:hl7-org:v3}telecom")
            if telecoms:
                structure["found_elements"].append("telecom")
                structure["telecom_count"] = len(telecoms)
                structure["telecom_details"] = [dict(t.attrib) for t in telecoms]

            # Check patient element
            patient = patient_role.find("{urn:hl7-org:v3}patient")
            if patient is not None:
                structure["found_elements"].append("patient")

                # Check name
                names = patient.findall("{urn:hl7-org:v3}name")
                if names:
                    structure["found_elements"].append("name")
                    structure["name_details"] = self._analyze_name(names[0])

                # Check birth time
                birth_time = patient.find("{urn:hl7-org:v3}birthTime")
                if birth_time is not None:
                    structure["found_elements"].append("birthTime")

                # Check gender
                gender = patient.find("{urn:hl7-org:v3}administrativeGenderCode")
                if gender is not None:
                    structure["found_elements"].append("administrativeGenderCode")

        return structure

    def _analyze_legal_authenticator(self, element):
        """Analyze legalAuthenticator structure"""
        structure = {"found_elements": [], "missing_elements": []}

        # Check signature code
        sig_code = element.find("{urn:hl7-org:v3}signatureCode")
        if sig_code is not None:
            structure["found_elements"].append("signatureCode")
            structure["signature_code"] = dict(sig_code.attrib)

        # Check time
        time_elem = element.find("{urn:hl7-org:v3}time")
        if time_elem is not None:
            structure["found_elements"].append("time")
            structure["time_value"] = dict(time_elem.attrib)

        # Check assigned entity
        assigned_entity = element.find("{urn:hl7-org:v3}assignedEntity")
        if assigned_entity is not None:
            structure["found_elements"].append("assignedEntity")
            structure.update(self._analyze_assigned_entity(assigned_entity))

        return structure

    def _analyze_custodian(self, element):
        """Analyze custodian structure"""
        structure = {"found_elements": [], "missing_elements": []}

        assigned_custodian = element.find("{urn:hl7-org:v3}assignedCustodian")
        if assigned_custodian is not None:
            structure["found_elements"].append("assignedCustodian")

            represented_org = assigned_custodian.find(
                "{urn:hl7-org:v3}representedCustodianOrganization"
            )
            if represented_org is not None:
                structure["found_elements"].append("representedCustodianOrganization")
                structure.update(self._analyze_organization(represented_org))

        return structure

    def _analyze_author(self, element):
        """Analyze author structure"""
        structure = {"found_elements": [], "missing_elements": []}

        # Check time
        time_elem = element.find("{urn:hl7-org:v3}time")
        if time_elem is not None:
            structure["found_elements"].append("time")
            structure["time_value"] = dict(time_elem.attrib)

        # Check assigned author
        assigned_author = element.find("{urn:hl7-org:v3}assignedAuthor")
        if assigned_author is not None:
            structure["found_elements"].append("assignedAuthor")
            structure.update(self._analyze_assigned_entity(assigned_author))

        return structure

    def _analyze_assigned_entity(self, element):
        """Analyze assignedEntity or assignedAuthor structure"""
        structure = {"entity_elements": []}

        # Check ID
        id_elems = element.findall("{urn:hl7-org:v3}id")
        if id_elems:
            structure["entity_elements"].append("id")
            structure["id_count"] = len(id_elems)
            structure["id_details"] = [dict(id_elem.attrib) for id_elem in id_elems]

        # Check addresses
        addresses = element.findall("{urn:hl7-org:v3}addr")
        if addresses:
            structure["entity_elements"].append("addr")
            structure["address_count"] = len(addresses)
            structure["address_details"] = self._analyze_address(addresses[0])

        # Check telecoms
        telecoms = element.findall("{urn:hl7-org:v3}telecom")
        if telecoms:
            structure["entity_elements"].append("telecom")
            structure["telecom_count"] = len(telecoms)
            structure["telecom_details"] = [dict(t.attrib) for t in telecoms]

        # Check assigned person
        assigned_person = element.find("{urn:hl7-org:v3}assignedPerson")
        if assigned_person is not None:
            structure["entity_elements"].append("assignedPerson")

            names = assigned_person.findall("{urn:hl7-org:v3}name")
            if names:
                structure["person_name_details"] = self._analyze_name(names[0])

        # Check represented organization
        rep_org = element.find("{urn:hl7-org:v3}representedOrganization")
        if rep_org is not None:
            structure["entity_elements"].append("representedOrganization")
            structure["organization_details"] = self._analyze_organization(rep_org)

        return structure

    def _analyze_organization(self, element):
        """Analyze organization structure"""
        org_structure = {"org_elements": []}

        # Check ID
        id_elems = element.findall("{urn:hl7-org:v3}id")
        if id_elems:
            org_structure["org_elements"].append("id")
            org_structure["org_id_details"] = [
                dict(id_elem.attrib) for id_elem in id_elems
            ]

        # Check name
        names = element.findall("{urn:hl7-org:v3}name")
        if names:
            org_structure["org_elements"].append("name")
            org_structure["org_name_value"] = names[0].text if names[0].text else ""

        # Check addresses
        addresses = element.findall("{urn:hl7-org:v3}addr")
        if addresses:
            org_structure["org_elements"].append("addr")
            org_structure["org_address_details"] = self._analyze_address(addresses[0])

        # Check telecoms
        telecoms = element.findall("{urn:hl7-org:v3}telecom")
        if telecoms:
            org_structure["org_elements"].append("telecom")
            org_structure["org_telecom_details"] = [dict(t.attrib) for t in telecoms]

        return org_structure

    def _analyze_address(self, addr_element):
        """Analyze address structure"""
        addr_details = {"addr_components": []}

        for child in addr_element:
            local_name = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            addr_details["addr_components"].append(local_name)
            addr_details[local_name] = child.text if child.text else ""

        return addr_details

    def _analyze_name(self, name_element):
        """Analyze name structure"""
        name_details = {"name_components": []}

        for child in name_element:
            local_name = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            name_details["name_components"].append(local_name)
            name_details[local_name] = child.text if child.text else ""

        return name_details

    def analyze_country_files(self, country_code):
        """Analyze all CDA files for a specific country"""
        country_path = self.test_data_path / country_code
        if not country_path.exists():
            return None

        country_results = {
            "files_analyzed": 0,
            "files_with_errors": 0,
            "administrative_data": {},
            "xml_structures": {},
            "field_coverage": defaultdict(int),
        }

        # Find all XML files
        xml_files = list(country_path.glob("*.xml"))

        for xml_file in xml_files:
            try:
                print(f"  📄 Analyzing {xml_file.name}")

                with open(xml_file, "r", encoding="utf-8") as f:
                    xml_content = f.read()

                # Parse with our current parser
                try:
                    result = self.parser.parse_cda_content(xml_content)
                    admin_info = result.get("administrative_info", {})
                    country_results["administrative_data"][xml_file.name] = admin_info

                    # Track field availability
                    self._track_field_availability(
                        admin_info, country_results["field_coverage"]
                    )

                except Exception as parser_error:
                    print(f"    ⚠️ Parser error: {parser_error}")
                    country_results["files_with_errors"] += 1

                # Analyze raw XML structure
                xml_structure = self.analyze_xml_structure(
                    xml_content, country_code, xml_file.name
                )
                country_results["xml_structures"][xml_file.name] = xml_structure

                country_results["files_analyzed"] += 1

            except Exception as e:
                print(f"    ❌ File error {xml_file.name}: {e}")
                country_results["files_with_errors"] += 1

        return country_results

    def _track_field_availability(self, admin_info, field_coverage):
        """Track which fields are available in parsed data"""
        for section_name, expected_fields in self.expected_fields.items():
            section_data = admin_info.get(section_name)

            if section_name == "authors" and isinstance(section_data, list):
                for author in section_data:
                    for field in expected_fields:
                        if self._field_has_value(author, field):
                            field_coverage[f"{section_name}.{field}"] += 1
            elif section_data:
                for field in expected_fields:
                    if self._field_has_value(section_data, field):
                        field_coverage[f"{section_name}.{field}"] += 1

    def _field_has_value(self, data, field_path):
        """Check if a field has a meaningful value"""
        if not data:
            return False

        # Handle nested field paths (e.g., "address.city")
        if "." in field_path:
            parts = field_path.split(".")
            current = data
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return False
            return bool(current and str(current).strip())

        # Direct field access
        value = data.get(field_path) if isinstance(data, dict) else None
        return bool(value and str(value).strip())

    def run_comprehensive_analysis(self):
        """Run analysis across all EU member states"""
        print("🔍 COMPREHENSIVE ADMINISTRATIVE GAP ANALYSIS")
        print("=" * 60)
        print(f"Analysis started: {datetime.now()}")
        print(f"Test data path: {self.test_data_path}")

        if not self.test_data_path.exists():
            print(f"❌ Test data path not found: {self.test_data_path}")
            return

        # Get all country directories
        country_dirs = [d for d in self.test_data_path.iterdir() if d.is_dir()]

        total_files = 0
        total_errors = 0

        for country_dir in sorted(country_dirs):
            country_code = country_dir.name
            print(f"\n📍 Analyzing {country_code}")

            country_results = self.analyze_country_files(country_code)
            if country_results:
                self.results["by_country"][country_code] = country_results
                total_files += country_results["files_analyzed"]
                total_errors += country_results["files_with_errors"]

                # Aggregate field availability
                for field, count in country_results["field_coverage"].items():
                    self.results["field_availability"][field] += count

        # Generate summary
        self.results["summary"] = {
            "countries_analyzed": len(country_dirs),
            "total_files": total_files,
            "total_errors": total_errors,
            "success_rate": (
                (total_files - total_errors) / total_files * 100
                if total_files > 0
                else 0
            ),
        }

        # Generate recommendations
        self._generate_recommendations()

        # Save results
        self._save_results()

        # Print analysis
        self._print_analysis()

    def _generate_recommendations(self):
        """Generate recommendations based on gap analysis"""
        recommendations = []

        # Analyze field availability gaps
        total_files = sum(
            1
            for country in self.results["by_country"].values()
            for file in country["administrative_data"]
        )

        for section_name, expected_fields in self.expected_fields.items():
            section_gaps = []

            for field in expected_fields:
                field_key = f"{section_name}.{field}"
                availability = self.results["field_availability"].get(field_key, 0)
                coverage_percent = (
                    (availability / total_files * 100) if total_files > 0 else 0
                )

                if coverage_percent < 50:  # Less than 50% coverage
                    section_gaps.append(
                        {
                            "field": field,
                            "coverage": coverage_percent,
                            "files_with_data": availability,
                            "total_files": total_files,
                        }
                    )

            if section_gaps:
                recommendations.append(
                    {
                        "section": section_name,
                        "type": "low_coverage_fields",
                        "gaps": section_gaps,
                        "priority": (
                            "high"
                            if len(section_gaps) > len(expected_fields) * 0.5
                            else "medium"
                        ),
                    }
                )

        # Check for completely missing sections
        for country_code, country_data in self.results["by_country"].items():
            for filename, admin_data in country_data["administrative_data"].items():
                missing_sections = []
                for section_name in self.expected_fields.keys():
                    if not admin_data.get(section_name):
                        missing_sections.append(section_name)

                if missing_sections:
                    recommendations.append(
                        {
                            "type": "missing_sections",
                            "country": country_code,
                            "file": filename,
                            "missing_sections": missing_sections,
                            "priority": "high",
                        }
                    )

        self.results["recommendations"] = recommendations

    def _save_results(self):
        """Save analysis results to JSON file"""
        output_file = Path("administrative_gap_analysis_results.json")

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"\n💾 Results saved to: {output_file}")

    def _print_analysis(self):
        """Print comprehensive analysis results"""
        print(f"\n📊 ANALYSIS RESULTS")
        print("=" * 50)

        summary = self.results["summary"]
        print(f"Countries analyzed: {summary['countries_analyzed']}")
        print(f"Total files processed: {summary['total_files']}")
        print(f"Files with errors: {summary['total_errors']}")
        print(f"Success rate: {summary['success_rate']:.1f}%")

        print(f"\n📈 FIELD AVAILABILITY ANALYSIS")
        print("-" * 40)

        # Group by section
        sections = defaultdict(list)
        for field_key, count in self.results["field_availability"].items():
            if "." in field_key:
                section, field = field_key.split(".", 1)
                coverage = (
                    (count / summary["total_files"] * 100)
                    if summary["total_files"] > 0
                    else 0
                )
                sections[section].append((field, count, coverage))

        for section_name, fields in sections.items():
            print(f"\n🏷️ {section_name.upper()}:")
            fields.sort(key=lambda x: x[2], reverse=True)  # Sort by coverage

            for field, count, coverage in fields:
                status = "✅" if coverage >= 80 else "⚠️" if coverage >= 50 else "❌"
                print(
                    f"  {status} {field:<20} {count:>3}/{summary['total_files']:<3} ({coverage:>5.1f}%)"
                )

        print(f"\n🎯 RECOMMENDATIONS")
        print("-" * 30)

        high_priority = [
            r for r in self.results["recommendations"] if r.get("priority") == "high"
        ]
        medium_priority = [
            r for r in self.results["recommendations"] if r.get("priority") == "medium"
        ]

        print(f"High priority issues: {len(high_priority)}")
        print(f"Medium priority issues: {len(medium_priority)}")

        for rec in high_priority[:5]:  # Show top 5 high priority
            if rec["type"] == "low_coverage_fields":
                gap_fields = [g["field"] for g in rec["gaps"]]
                print(
                    f"  🔴 {rec['section']}: Missing fields - {', '.join(gap_fields[:3])}{'...' if len(gap_fields) > 3 else ''}"
                )
            elif rec["type"] == "missing_sections":
                print(
                    f"  🔴 {rec['country']}/{rec['file']}: Missing sections - {', '.join(rec['missing_sections'])}"
                )

        print(f"\n💡 PARSER ENHANCEMENT SUGGESTIONS:")
        print("  1. Enhance address extraction for better coverage")
        print("  2. Improve telecom parsing for phone/email extraction")
        print("  3. Add flexible organization name handling")
        print("  4. Implement better role/title extraction")
        print("  5. Add comprehensive ID authority parsing")


def main():
    """Run the comprehensive gap analysis"""
    analyzer = AdministrativeGapAnalyzer()
    analyzer.run_comprehensive_analysis()


if __name__ == "__main__":
    main()
