#!/usr/bin/env python3
"""
JSON Bundle CDA Parser - Universal approach for all countries
Converts CDA XML to JSON bundle, then uses flexible queries
"""

import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ClinicalResource:
    """Represents a clinical resource in the bundle"""

    resource_type: str
    id: str
    data: Dict[str, Any]
    codes: List[Dict[str, str]] = None

    def __post_init__(self):
        if self.codes is None:
            self.codes = []


class JSONBundleCDAParser:
    """
    Universal CDA parser using JSON bundle approach
    Works with CDA documents from any EU country
    """

    def __init__(self):
        self.namespaces = {"cda": "urn:hl7-org:v3", "pharm": "urn:hl7-org:pharm"}

    def parse_cda_to_bundle(self, xml_content: str) -> Dict[str, Any]:
        """Convert CDA XML to JSON bundle format"""
        try:
            # Parse XML
            root = ET.fromstring(xml_content)

            # Create bundle structure
            bundle = {
                "resourceType": "Bundle",
                "id": "cda-bundle",
                "type": "document",
                "timestamp": None,
                "entry": [],
            }

            # Extract document metadata
            bundle["entry"].append(self._extract_document_metadata(root))

            # Extract patient resource
            patient_resource = self._extract_patient_resource(root)
            if patient_resource:
                bundle["entry"].append(patient_resource)

            # Extract all clinical sections as resources
            sections = self._extract_section_resources(root)
            bundle["entry"].extend(sections)

            # Extract observations, medications, procedures, etc.
            clinical_resources = self._extract_clinical_resources(root)
            bundle["entry"].extend(clinical_resources)

            return bundle

        except Exception as e:
            logger.error(f"Error creating JSON bundle: {e}")
            return {"error": str(e)}

    def _extract_document_metadata(self, root: ET.Element) -> Dict[str, Any]:
        """Extract document-level metadata"""
        doc_id = root.find(".//{urn:hl7-org:v3}id")
        doc_code = root.find(".//{urn:hl7-org:v3}code")
        effective_time = root.find(".//{urn:hl7-org:v3}effectiveTime")

        return {
            "fullUrl": "document/metadata",
            "resource": {
                "resourceType": "Composition",
                "id": doc_id.get("extension") if doc_id is not None else "unknown",
                "status": "final",
                "type": {
                    "coding": [
                        {
                            "system": (
                                doc_code.get("codeSystem")
                                if doc_code is not None
                                else ""
                            ),
                            "code": (
                                doc_code.get("code") if doc_code is not None else ""
                            ),
                            "display": (
                                doc_code.get("displayName")
                                if doc_code is not None
                                else ""
                            ),
                        }
                    ]
                },
                "date": (
                    effective_time.get("value") if effective_time is not None else None
                ),
                "title": (
                    root.find(".//{urn:hl7-org:v3}title").text
                    if root.find(".//{urn:hl7-org:v3}title") is not None
                    else "Patient Summary"
                ),
            },
        }

    def _extract_patient_resource(self, root: ET.Element) -> Optional[Dict[str, Any]]:
        """Extract patient information as FHIR-like resource"""
        patient_role = root.find(".//{urn:hl7-org:v3}patientRole")
        if patient_role is None:
            return None

        patient = patient_role.find("{urn:hl7-org:v3}patient")
        if patient is None:
            return None

        # Extract name
        name_elem = patient.find("{urn:hl7-org:v3}name")
        given_name = ""
        family_name = ""
        if name_elem is not None:
            given_elem = name_elem.find("{urn:hl7-org:v3}given")
            family_elem = name_elem.find("{urn:hl7-org:v3}family")
            given_name = given_elem.text if given_elem is not None else ""
            family_name = family_elem.text if family_elem is not None else ""

        # Extract identifiers
        identifiers = []
        for id_elem in patient_role.findall("{urn:hl7-org:v3}id"):
            identifiers.append(
                {
                    "system": id_elem.get("root", ""),
                    "value": id_elem.get("extension", ""),
                    "assigner": id_elem.get("assigningAuthorityName", ""),
                }
            )

        # Extract birth date and gender
        birth_elem = patient.find("{urn:hl7-org:v3}birthTime")
        gender_elem = patient.find("{urn:hl7-org:v3}administrativeGenderCode")

        return {
            "fullUrl": "patient/main",
            "resource": {
                "resourceType": "Patient",
                "id": "main",
                "identifier": identifiers,
                "name": [
                    {"given": [given_name] if given_name else [], "family": family_name}
                ],
                "gender": gender_elem.get("code") if gender_elem is not None else None,
                "birthDate": (
                    birth_elem.get("value") if birth_elem is not None else None
                ),
            },
        }

    def _extract_section_resources(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract all clinical sections as resources"""
        sections = []
        section_elements = root.findall(".//{urn:hl7-org:v3}section")

        for i, section_elem in enumerate(section_elements):
            # Extract section metadata
            section_code = section_elem.find("{urn:hl7-org:v3}code")
            title_elem = section_elem.find("{urn:hl7-org:v3}title")
            text_elem = section_elem.find("{urn:hl7-org:v3}text")

            # Extract template IDs
            template_ids = [
                tmpl.get("root", "")
                for tmpl in section_elem.findall("{urn:hl7-org:v3}templateId")
            ]

            section_resource = {
                "fullUrl": f"section/{i}",
                "resource": {
                    "resourceType": "DocumentSection",
                    "id": str(i),
                    "code": (
                        {
                            "coding": [
                                {
                                    "system": (
                                        section_code.get("codeSystem")
                                        if section_code is not None
                                        else ""
                                    ),
                                    "code": (
                                        section_code.get("code")
                                        if section_code is not None
                                        else ""
                                    ),
                                    "display": (
                                        section_code.get("displayName")
                                        if section_code is not None
                                        else ""
                                    ),
                                }
                            ]
                        }
                        if section_code is not None
                        else None
                    ),
                    "title": (
                        title_elem.text if title_elem is not None else f"Section {i+1}"
                    ),
                    "narrative": (
                        self._extract_narrative_text(text_elem)
                        if text_elem is not None
                        else ""
                    ),
                    "templateIds": template_ids,
                    "entries": self._extract_section_entries(section_elem),
                },
            }

            sections.append(section_resource)

        return sections

    def _extract_clinical_resources(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract clinical resources (observations, medications, etc.)"""
        resources = []

        # Find all entries across all sections
        entries = root.findall(".//{urn:hl7-org:v3}entry")

        for i, entry in enumerate(entries):
            # Determine resource type and extract data
            clinical_resource = self._convert_entry_to_resource(entry, i)
            if clinical_resource:
                resources.append(clinical_resource)

        return resources

    def _convert_entry_to_resource(
        self, entry: ET.Element, index: int
    ) -> Optional[Dict[str, Any]]:
        """Convert CDA entry to FHIR-like resource"""
        # Look for different types of clinical statements
        observation = entry.find(".//{urn:hl7-org:v3}observation")
        act = entry.find(".//{urn:hl7-org:v3}act")
        substance_admin = entry.find(".//{urn:hl7-org:v3}substanceAdministration")

        if observation is not None:
            return self._create_observation_resource(observation, index)
        elif act is not None:
            return self._create_act_resource(act, index)
        elif substance_admin is not None:
            return self._create_medication_resource(substance_admin, index)

        return None

    def _create_observation_resource(
        self, obs_elem: ET.Element, index: int
    ) -> Dict[str, Any]:
        """Create observation resource from CDA observation"""
        code_elem = obs_elem.find("{urn:hl7-org:v3}code")
        value_elem = obs_elem.find("{urn:hl7-org:v3}value")
        status_elem = obs_elem.find("{urn:hl7-org:v3}statusCode")

        # Extract all coded values
        codes = []
        for elem in obs_elem.iter():
            if elem.get("code") and elem.get("codeSystem"):
                codes.append(
                    {
                        "system": elem.get("codeSystem"),
                        "code": elem.get("code"),
                        "display": elem.get("displayName", ""),
                        "systemName": elem.get("codeSystemName", ""),
                    }
                )

        return {
            "fullUrl": f"observation/{index}",
            "resource": {
                "resourceType": "Observation",
                "id": str(index),
                "status": (
                    status_elem.get("code") if status_elem is not None else "unknown"
                ),
                "code": (
                    {
                        "coding": [
                            {
                                "system": (
                                    code_elem.get("codeSystem")
                                    if code_elem is not None
                                    else ""
                                ),
                                "code": (
                                    code_elem.get("code")
                                    if code_elem is not None
                                    else ""
                                ),
                                "display": (
                                    code_elem.get("displayName")
                                    if code_elem is not None
                                    else ""
                                ),
                            }
                        ]
                    }
                    if code_elem is not None
                    else None
                ),
                "valueCodeableConcept": (
                    {
                        "coding": [
                            {
                                "system": (
                                    value_elem.get("codeSystem")
                                    if value_elem is not None
                                    else ""
                                ),
                                "code": (
                                    value_elem.get("code")
                                    if value_elem is not None
                                    else ""
                                ),
                                "display": (
                                    value_elem.get("displayName")
                                    if value_elem is not None
                                    else ""
                                ),
                            }
                        ]
                    }
                    if value_elem is not None and value_elem.get("code")
                    else None
                ),
                "allCodes": codes,  # Custom field for all codes found
            },
        }

    def _create_medication_resource(
        self, med_elem: ET.Element, index: int
    ) -> Dict[str, Any]:
        """Create medication resource from substanceAdministration"""
        codes = []
        for elem in med_elem.iter():
            if elem.get("code") and elem.get("codeSystem"):
                codes.append(
                    {
                        "system": elem.get("codeSystem"),
                        "code": elem.get("code"),
                        "display": elem.get("displayName", ""),
                        "systemName": elem.get("codeSystemName", ""),
                    }
                )

        return {
            "fullUrl": f"medication/{index}",
            "resource": {
                "resourceType": "MedicationStatement",
                "id": str(index),
                "status": "unknown",
                "allCodes": codes,
            },
        }

    def _create_act_resource(self, act_elem: ET.Element, index: int) -> Dict[str, Any]:
        """Create general act resource"""
        codes = []
        for elem in act_elem.iter():
            if elem.get("code") and elem.get("codeSystem"):
                codes.append(
                    {
                        "system": elem.get("codeSystem"),
                        "code": elem.get("code"),
                        "display": elem.get("displayName", ""),
                        "systemName": elem.get("codeSystemName", ""),
                    }
                )

        return {
            "fullUrl": f"act/{index}",
            "resource": {
                "resourceType": "Procedure",  # or other appropriate type
                "id": str(index),
                "status": "unknown",
                "allCodes": codes,
            },
        }

    def _extract_narrative_text(self, text_elem: ET.Element) -> str:
        """Extract narrative text from section"""
        if text_elem is None:
            return ""

        # Convert XML text content to string
        return ET.tostring(text_elem, encoding="unicode", method="text").strip()

    def _extract_section_entries(self, section_elem: ET.Element) -> List[str]:
        """Extract entry references from a section"""
        entries = section_elem.findall("{urn:hl7-org:v3}entry")
        return [f"entry/{i}" for i in range(len(entries))]


class BundleQueryEngine:
    """Query engine for searching the JSON bundle"""

    def __init__(self, bundle: Dict[str, Any]):
        self.bundle = bundle

    def find_all_codes(self) -> List[Dict[str, str]]:
        """Find all clinical codes in the bundle"""
        codes = []

        for entry in self.bundle.get("entry", []):
            resource = entry.get("resource", {})

            # Look for codes in different places
            if "allCodes" in resource:
                codes.extend(resource["allCodes"])

            # Look for coding in code fields
            if "code" in resource and "coding" in resource["code"]:
                for coding in resource["code"]["coding"]:
                    if coding.get("code"):
                        codes.append(coding)

        return codes

    def find_sections(self) -> List[Dict[str, Any]]:
        """Find all clinical sections"""
        sections = []

        for entry in self.bundle.get("entry", []):
            resource = entry.get("resource", {})
            if resource.get("resourceType") == "DocumentSection":
                sections.append(resource)

        return sections

    def find_by_code_system(self, system_name: str) -> List[Dict[str, str]]:
        """Find all codes from a specific system (SNOMED, LOINC, etc.)"""
        all_codes = self.find_all_codes()
        return [
            code
            for code in all_codes
            if system_name.lower() in code.get("systemName", "").lower()
            or system_name.lower() in code.get("system", "").lower()
        ]

    def get_patient_data(self) -> Optional[Dict[str, Any]]:
        """Get patient resource"""
        for entry in self.bundle.get("entry", []):
            resource = entry.get("resource", {})
            if resource.get("resourceType") == "Patient":
                return resource
        return None


def test_bundle_approach():
    """Test the JSON bundle approach with Italian CDA"""

    # Path to Italian CDA
    italian_cda_path = "test_data/eu_member_states/IT/2025-03-28T13-29-59.727799Z_CDA_EHDSI---FRIENDLY-CDA-(L3)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"

    try:
        # Read CDA file
        with open(italian_cda_path, "r", encoding="utf-8") as f:
            xml_content = f.read()

        # Convert to JSON bundle
        parser = JSONBundleCDAParser()
        bundle = parser.parse_cda_to_bundle(xml_content)

        # Query the bundle
        query_engine = BundleQueryEngine(bundle)

        print("🔍 JSON Bundle CDA Parser Test")
        print("=" * 50)

        # Test queries
        all_codes = query_engine.find_all_codes()
        sections = query_engine.find_sections()
        snomed_codes = query_engine.find_by_code_system("SNOMED")
        loinc_codes = query_engine.find_by_code_system("LOINC")
        patient = query_engine.get_patient_data()

        print(f"📊 Total codes found: {len(all_codes)}")
        print(f"📑 Sections found: {len(sections)}")
        print(f"🏷️  SNOMED codes: {len(snomed_codes)}")
        print(f"🏷️  LOINC codes: {len(loinc_codes)}")

        # Show some example codes
        if snomed_codes:
            print(f"\n🔬 SNOMED Examples:")
            for code in snomed_codes[:3]:
                print(f"   {code.get('code')} - {code.get('display')}")

        # Show sections
        if sections:
            print(f"\n📋 Section Examples:")
            for section in sections[:3]:
                print(f"   {section.get('title')}")

        # Save bundle for inspection
        with open("italian_cda_bundle.json", "w") as f:
            json.dump(bundle, f, indent=2)

        print(f"\n💾 Bundle saved to: italian_cda_bundle.json")

        return bundle

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        print(traceback.format_exc())


if __name__ == "__main__":
    test_bundle_approach()
