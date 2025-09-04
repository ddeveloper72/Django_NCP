#!/usr/bin/env python3
"""
Enhanced CDA Field Mapping Service
Uses the comprehensive JSON mapping from the CDA display guide analysis
"""

import json
import os
from typing import Dict, List, Any, Optional
import xml.etree.ElementTree as ET


class EnhancedCDAFieldMapper:
    """
    Enhanced CDA Field Mapper using comprehensive JSON mapping
    Maps CDA fields to display labels with translation and value set support
    """

    def __init__(self, mapping_file_path: str = None):
        """Initialize with the JSON mapping file"""
        if mapping_file_path is None:
            # Default to the docs directory in project root - use combined mappings with section codes
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            mapping_file_path = os.path.join(
                project_root, "docs", "ehdsi_cda_combined_mappings.json"
            )

        self.mapping_file_path = mapping_file_path
        self.field_mappings = self._load_mappings()
        self.section_mappings = self._index_by_section_code()

    def _load_mappings(self) -> List[Dict]:
        """Load the JSON mapping file"""
        try:
            with open(self.mapping_file_path, "r", encoding="utf-8") as file:
                mappings = json.load(file)
            print(
                f"✅ Loaded {len(mappings)} section mappings from {self.mapping_file_path}"
            )
            return mappings
        except FileNotFoundError:
            print(f"❌ Mapping file not found: {self.mapping_file_path}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error in mapping file: {e}")
            return []

    def _index_by_section_code(self) -> Dict[str, Dict]:
        """Create an index of mappings by section code for quick lookup"""
        section_index = {}

        for section_mapping in self.field_mappings:
            section_code = section_mapping.get("sectionCode")
            if section_code:
                section_index[section_code] = section_mapping

        print(f"✅ Indexed {len(section_index)} clinical sections by code")
        return section_index

    def get_section_mapping(self, section_code: str) -> Optional[Dict]:
        """Get field mapping for a specific section code"""
        return self.section_mappings.get(section_code)

    def get_patient_fields(self) -> List[Dict]:
        """Get patient demographic field mappings"""
        for section in self.field_mappings:
            if section.get("section") == "Demographic Data":
                return section.get("fields", [])
        return []

    def get_clinical_section_fields(self, section_code: str) -> List[Dict]:
        """Get field mappings for a clinical section"""
        section_mapping = self.get_section_mapping(section_code)
        if section_mapping:
            return section_mapping.get("fields", [])
        return []

    def convert_xpath_to_namespaced(self, xpath):
        """Convert JSON XPath patterns to namespaced XPath"""
        if not xpath or xpath == "N/A":
            return xpath

        # Quick namespace mapping for common elements
        xpath = xpath.replace("/ClinicalDocument/", "/hl7:ClinicalDocument/")
        xpath = xpath.replace("/recordTarget/", "/hl7:recordTarget/")
        xpath = xpath.replace("/patientRole/", "/hl7:patientRole/")
        xpath = xpath.replace("/patient/", "/hl7:patient/")
        xpath = xpath.replace("/name/", "/hl7:name/")
        xpath = xpath.replace("/given", "/hl7:given")
        xpath = xpath.replace("/family", "/hl7:family")
        xpath = xpath.replace("/prefix", "/hl7:prefix")
        xpath = xpath.replace("/id[", "/hl7:id[")
        xpath = xpath.replace(
            "/administrativeGenderCode/", "/hl7:administrativeGenderCode/"
        )
        xpath = xpath.replace("/birthtime/", "/hl7:birthTime/")
        xpath = xpath.replace("/birthTime/", "/hl7:birthTime/")

        # Convert to relative path for better matching
        if xpath.startswith("/hl7:ClinicalDocument/"):
            xpath = "." + xpath

        return xpath

    def extract_field_value(
        self, xml_root: ET.Element, xpath: str, namespaces: Dict[str, str]
    ) -> str:
        """Extract field value using XPath with namespace support"""
        if xpath == "N/A" or not xpath:
            return "Not Available"

        try:
            # Convert to namespaced XPath
            namespaced_xpath = self.convert_xpath_to_namespaced(xpath)

            # Handle simple attribute extraction
            if (
                namespaced_xpath.endswith("/@value")
                or namespaced_xpath.endswith("/@code")
                or namespaced_xpath.endswith("/@extension")
            ):
                element = xml_root.find(
                    namespaced_xpath[:-7], namespaces
                )  # Remove /@attribute
                if element is not None:
                    attr_name = namespaced_xpath.split("/")[-1][1:]  # Remove @ prefix
                    return element.get(attr_name, "")

            # Handle displayName attribute
            elif namespaced_xpath.endswith("/@displayName"):
                element = xml_root.find(
                    namespaced_xpath[:-13], namespaces
                )  # Remove /@displayName
                if element is not None:
                    return element.get("displayName", "")

            # Handle text content
            else:
                element = xml_root.find(namespaced_xpath, namespaces)
                if element is not None:
                    return element.text or ""

        except Exception as e:
            print(
                f"⚠️  XPath extraction error for '{xpath}' -> '{namespaced_xpath}': {e}"
            )

        return ""

    def map_patient_data(
        self, xml_root: ET.Element, namespaces: Dict[str, str]
    ) -> Dict[str, Any]:
        """Map patient demographic data using the field mappings"""
        patient_data = {}
        patient_fields = self.get_patient_fields()

        for field in patient_fields:
            label = field.get("label", "Unknown Field")
            xpath = field.get("xpath", "")
            value = self.extract_field_value(xml_root, xpath, namespaces)

            patient_data[label] = {
                "value": value,
                "xpath": xpath,
                "translation_required": field.get("translation", "NO") == "YES",
                "value_set": field.get("valueSet", "N") == "Y",
            }

        return patient_data

    def map_clinical_section(
        self,
        section_element: ET.Element,
        section_code: str,
        xml_root: ET.Element,
        namespaces: Dict[str, str],
    ) -> Dict[str, Any]:
        """Map a clinical section using the field mappings"""
        section_data = {
            "section_code": section_code,
            "mapped_fields": {},
            "entries": [],
        }

        section_fields = self.get_clinical_section_fields(section_code)
        if not section_fields:
            return section_data

        # Map section-level fields
        for field in section_fields:
            label = field.get("label", "Unknown Field")
            xpath = field.get("xpath", "")

            # For section title, use the section element directly
            if label == "Section Title":
                code_element = section_element.find("hl7:code", namespaces)
                if code_element is not None:
                    value = code_element.get("displayName", "")
                else:
                    value = ""
            else:
                # For other fields, search within the section
                value = self._extract_section_field_value(
                    section_element, xpath, namespaces
                )

            section_data["mapped_fields"][label] = {
                "value": value,
                "xpath": xpath,
                "translation_required": field.get("translation", "NO") == "YES",
                "value_set": field.get("valueSet", "N") == "Y",
            }

        # Extract entries for structured data
        entries = section_element.findall("hl7:entry", namespaces)
        for i, entry in enumerate(entries):
            entry_data = self._map_entry_fields(entry, section_fields, namespaces, i)
            if entry_data:
                section_data["entries"].append(entry_data)

        return section_data

    def _extract_section_field_value(
        self, section_element: ET.Element, xpath: str, namespaces: Dict[str, str]
    ) -> str:
        """Extract field value from within a section element"""
        if xpath == "N/A" or not xpath:
            return "Not Available"

        try:
            # Simplify xpath for section-relative search
            relative_xpath = xpath.replace("section/", "").replace(
                "entry/", "hl7:entry/"
            )

            # Handle attribute extraction
            if (
                relative_xpath.endswith("/@value")
                or relative_xpath.endswith("/@code")
                or relative_xpath.endswith("/@displayName")
            ):
                element_xpath = relative_xpath.rsplit("/@", 1)[0]
                attr_name = relative_xpath.split("/")[-1][1:]  # Remove @ prefix

                element = section_element.find(element_xpath, namespaces)
                if element is not None:
                    return element.get(attr_name, "")

            # Handle text content
            else:
                element = section_element.find(relative_xpath, namespaces)
                if element is not None:
                    return element.text or ""

        except Exception as e:
            print(f"⚠️  Section field extraction error for '{xpath}': {e}")

        return ""

    def _map_entry_fields(
        self,
        entry_element: ET.Element,
        section_fields: List[Dict],
        namespaces: Dict[str, str],
        entry_index: int,
    ) -> Dict[str, Any]:
        """Map individual entry fields within a clinical section"""
        entry_data = {"entry_index": entry_index, "fields": {}}

        for field in section_fields:
            if field.get("label") == "Section Title":
                continue  # Skip section-level fields

            label = field.get("label", "Unknown Field")
            xpath = field.get("xpath", "")

            # Extract value from entry context
            value = self._extract_entry_field_value(entry_element, xpath, namespaces)

            if value:  # Only include fields with values
                entry_data["fields"][label] = {
                    "value": value,
                    "xpath": xpath,
                    "translation_required": field.get("translation", "NO") == "YES",
                    "value_set": field.get("valueSet", "N") == "Y",
                }

        return entry_data if entry_data["fields"] else None

    def _extract_entry_field_value(
        self, entry_element: ET.Element, xpath: str, namespaces: Dict[str, str]
    ) -> str:
        """Extract field value from within an entry element"""
        if xpath == "N/A" or not xpath:
            return ""

        try:
            # Simplify xpath for entry-relative search
            relative_xpath = xpath.replace("entry/", "").replace("act/", "hl7:act/")
            relative_xpath = relative_xpath.replace("observation/", "hl7:observation/")
            relative_xpath = relative_xpath.replace(
                "substanceAdministration/", "hl7:substanceAdministration/"
            )
            relative_xpath = relative_xpath.replace("procedure/", "hl7:procedure/")

            # Handle the complex xpath patterns with "..."
            if "..." in relative_xpath:
                # For complex paths, try to find the target element more flexibly
                parts = relative_xpath.split("...")
                if len(parts) >= 2:
                    # Try to find the final part anywhere in the entry
                    final_part = parts[-1].lstrip("/")
                    elements = entry_element.findall(f".//{final_part}", namespaces)
                    if elements:
                        element = elements[0]  # Take first match
                        if (
                            final_part.endswith("/@value")
                            or final_part.endswith("/@code")
                            or final_part.endswith("/@displayName")
                        ):
                            attr_name = final_part.split("/")[-1][1:]
                            return element.get(attr_name, "")
                        else:
                            return element.text or ""

            # Handle standard attribute extraction
            elif (
                relative_xpath.endswith("/@value")
                or relative_xpath.endswith("/@code")
                or relative_xpath.endswith("/@displayName")
            ):
                element_xpath = relative_xpath.rsplit("/@", 1)[0]
                attr_name = relative_xpath.split("/")[-1][1:]

                element = entry_element.find(element_xpath, namespaces)
                if element is not None:
                    return element.get(attr_name, "")

            # Handle text content
            else:
                element = entry_element.find(relative_xpath, namespaces)
                if element is not None:
                    return element.text or ""

        except Exception as e:
            print(f"⚠️  Entry field extraction error for '{xpath}': {e}")

        return ""

    def get_available_sections(self) -> List[Dict[str, str]]:
        """Get list of all available clinical sections with codes"""
        sections = []

        for section_mapping in self.field_mappings:
            section_code = section_mapping.get("sectionCode")
            section_name = section_mapping.get("section")

            if section_code and section_name:
                sections.append(
                    {
                        "code": section_code,
                        "name": section_name,
                        "field_count": len(section_mapping.get("fields", [])),
                    }
                )

        return sections

    def get_mapping_summary(self) -> Dict[str, Any]:
        """Get a summary of the mapping capabilities"""
        total_sections = len(self.field_mappings)
        clinical_sections = len(
            [s for s in self.field_mappings if s.get("sectionCode")]
        )

        total_fields = sum(len(s.get("fields", [])) for s in self.field_mappings)

        translation_fields = sum(
            len([f for f in s.get("fields", []) if f.get("translation") == "YES"])
            for s in self.field_mappings
        )

        return {
            "total_sections": total_sections,
            "clinical_sections": clinical_sections,
            "total_fields": total_fields,
            "translation_required_fields": translation_fields,
            "available_sections": self.get_available_sections(),
        }


def test_field_mapper():
    """Test the Enhanced CDA Field Mapper"""
    print("🧪 Testing Enhanced CDA Field Mapper")
    print("=" * 50)

    # Initialize mapper
    mapper = EnhancedCDAFieldMapper()

    # Get mapping summary
    summary = mapper.get_mapping_summary()
    print(f"📊 Mapping Summary:")
    print(f"   Total sections: {summary['total_sections']}")
    print(f"   Clinical sections: {summary['clinical_sections']}")
    print(f"   Total fields: {summary['total_fields']}")
    print(f"   Translation fields: {summary['translation_required_fields']}")

    print(f"\n📋 Available Clinical Sections:")
    for section in summary["available_sections"]:
        print(
            f"   {section['code']}: {section['name']} ({section['field_count']} fields)"
        )

    # Test patient field mapping
    patient_fields = mapper.get_patient_fields()
    print(f"\n👤 Patient Fields ({len(patient_fields)} total):")
    for field in patient_fields[:5]:  # Show first 5
        print(f"   {field['label']}: {field['xpath']}")

    # Test medication section mapping
    med_fields = mapper.get_clinical_section_fields("10160-0")
    print(f"\n💊 Medication Section Fields ({len(med_fields)} total):")
    for field in med_fields[:5]:  # Show first 5
        print(f"   {field['label']}: {field['xpath']}")

    return mapper


if __name__ == "__main__":
    test_field_mapper()
