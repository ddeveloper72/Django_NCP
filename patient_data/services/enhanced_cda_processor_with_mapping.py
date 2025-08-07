#!/usr/bin/env python3
"""
Enhanced CDA Processor with JSON Field Mapping Integration
Combines the comprehensive JSON mapping with the existing Enhanced CDA Processor
"""

import json
import os
from typing import Dict, List, Any, Optional
import xml.etree.ElementTree as ET
from .enhanced_cda_field_mapper import EnhancedCDAFieldMapper


class EnhancedCDAProcessorWithMapping:
    """
    Enhanced CDA Processor that leverages the comprehensive JSON field mapping
    Provides both the existing functionality and new field-level mapping capabilities
    """

    def __init__(self, target_language: str = "en"):
        """Initialize with field mapper and existing processor"""
        self.target_language = target_language

        # Load the field mapper
        self.field_mapper = EnhancedCDAFieldMapper()

        # Load the existing Enhanced CDA Processor
        try:
            from .enhanced_cda_processor import EnhancedCDAProcessor

            self.enhanced_processor = EnhancedCDAProcessor(
                target_language=target_language
            )
        except ImportError:
            self.enhanced_processor = None
            print("⚠️  Enhanced CDA Processor not available, using mapping-only mode")

    def process_clinical_document(
        self, cda_content: str, source_language: str = "en"
    ) -> Dict[str, Any]:
        """
        Process a complete CDA document with comprehensive field mapping
        """
        result = {
            "success": False,
            "patient_data": {},
            "clinical_sections": [],
            "mapped_sections": {},
            "metadata": {},
            "error": None,
        }

        try:
            # Parse the CDA document
            root = ET.fromstring(cda_content)
            namespaces = {"hl7": "urn:hl7-org:v3", "pharm": "urn:hl7-org:pharm"}

            # Extract patient demographics using field mapping
            patient_data = self.field_mapper.map_patient_data(root, namespaces)
            result["patient_data"] = patient_data

            # Extract document metadata
            metadata = self._extract_document_metadata(root, namespaces)
            result["metadata"] = metadata

            # Process clinical sections with field mapping
            sections = root.findall(".//hl7:section", namespaces)
            mapped_sections = {}
            clinical_sections = []

            for section in sections:
                code_elem = section.find("hl7:code", namespaces)
                if code_elem is not None:
                    section_code = code_elem.get("code")
                    section_title = code_elem.get("displayName", "Unknown Section")

                    # Check if we have mapping for this section
                    if self.field_mapper.get_section_mapping(section_code):
                        # Map using field mappings
                        section_data = self.field_mapper.map_clinical_section(
                            section, section_code, root, namespaces
                        )
                        mapped_sections[section_code] = section_data

                        # Convert to clinical section format
                        clinical_section = self._convert_to_clinical_section(
                            section_data, section, namespaces
                        )
                        clinical_sections.append(clinical_section)

            result["mapped_sections"] = mapped_sections
            result["clinical_sections"] = clinical_sections

            # If Enhanced CDA Processor is available, compare results
            if self.enhanced_processor:
                enhanced_result = self.enhanced_processor.process_clinical_sections(
                    cda_content=cda_content, source_language=source_language
                )

                if enhanced_result.get("success"):
                    # Merge enhanced processor results
                    enhanced_sections = enhanced_result.get("sections", [])
                    result["enhanced_sections"] = enhanced_sections

                    # Enhance clinical sections with structured data from enhanced processor
                    self._merge_enhanced_data(
                        result["clinical_sections"], enhanced_sections
                    )

            result["success"] = True

        except Exception as e:
            result["error"] = str(e)
            print(f"❌ CDA processing error: {e}")

        return result

    def _extract_document_metadata(
        self, root: ET.Element, namespaces: Dict[str, str]
    ) -> Dict[str, Any]:
        """Extract document metadata using field mappings"""
        metadata = {}

        # Find General Information Block mapping
        for section_mapping in self.field_mapper.field_mappings:
            if section_mapping.get("section") == "General Information Block":
                fields = section_mapping.get("fields", [])

                for field in fields:
                    label = field.get("label", "Unknown Field")
                    xpath = field.get("xpath", "")
                    value = self.field_mapper.extract_field_value(
                        root, xpath, namespaces
                    )

                    metadata[label] = {
                        "value": value,
                        "xpath": xpath,
                        "translation_required": field.get("translation", "NO") == "YES",
                    }
                break

        return metadata

    def _convert_to_clinical_section(
        self,
        section_data: Dict[str, Any],
        section_element: ET.Element,
        namespaces: Dict[str, str],
    ) -> Dict[str, Any]:
        """Convert field mapping data to clinical section format"""
        section_code = section_data["section_code"]

        # Get section title
        section_title = "Unknown Section"
        title_field = section_data["mapped_fields"].get("Section Title")
        if title_field and title_field["value"]:
            section_title = title_field["value"]

        clinical_section = {
            "section_code": section_code,
            "title": section_title,
            "translated_title": section_title,  # Will be enhanced with translation
            "mapped_fields": section_data["mapped_fields"],
            "structured_data": [],
            "table_rows": [],
            "html_content": "",
            "has_ps_table": False,
            "field_mapping_success": True,
        }

        # Convert entries to structured data
        for entry in section_data["entries"]:
            structured_item = self._convert_entry_to_structured_data(
                entry, section_code
            )
            if structured_item:
                clinical_section["structured_data"].append(structured_item)

        # Extract HTML content if available
        text_elem = section_element.find("hl7:text", namespaces)
        if text_elem is not None:
            html_content = ET.tostring(text_elem, encoding="unicode")
            clinical_section["html_content"] = html_content
            clinical_section["has_ps_table"] = "<table" in html_content

        return clinical_section

    def _convert_entry_to_structured_data(
        self, entry_data: Dict[str, Any], section_code: str
    ) -> Dict[str, Any]:
        """Convert field mapping entry to structured data format"""
        if not entry_data.get("fields"):
            return None

        structured_item = {"entry_index": entry_data.get("entry_index", 0)}

        # Map common field names based on section type
        field_mappings = {
            "10160-0": {  # Medication Summary
                "medication_code": ["Medicinal Product", "Active Ingredient"],
                "medication_display": [
                    "Active Ingredient Description",
                    "Medicinal Product",
                ],
                "dosage": ["Strength Value", "Dose"],
                "status": ["Administration Status"],
            },
            "48765-2": {  # Alerts/Allergies
                "condition_code": ["Agent ID", "Reaction Type"],
                "condition_display": ["Agent Description", "Clinical Manifestation"],
                "severity": ["Severity"],
                "status": ["Allergy Status"],
            },
            "11450-4": {  # Problems/Diagnosis
                "condition_code": ["Problem ID"],
                "condition_display": ["Problem"],
                "onset_date": ["Onset Date"],
                "status": ["Diagnosis Assertion Status"],
            },
            "30954-2": {  # Diagnostic Tests
                "observation_code": ["Result Type"],
                "observation_display": ["Result Type"],
                "value": ["Result Value"],
                "date": ["Diagnostic Date"],
            },
        }

        # Apply field mappings for this section type
        section_mappings = field_mappings.get(section_code, {})

        for target_field, source_fields in section_mappings.items():
            for source_field in source_fields:
                if source_field in entry_data["fields"]:
                    field_info = entry_data["fields"][source_field]
                    if field_info["value"]:
                        structured_item[target_field] = field_info["value"]
                        break

        # Add all original fields for reference
        structured_item["mapped_fields"] = entry_data["fields"]

        return structured_item

    def _merge_enhanced_data(
        self,
        clinical_sections: List[Dict[str, Any]],
        enhanced_sections: List[Dict[str, Any]],
    ):
        """Merge data from Enhanced CDA Processor with field mapping results"""
        # Create a lookup for enhanced sections by section code
        enhanced_lookup = {}
        for section in enhanced_sections:
            code = section.get("section_code")
            if code:
                enhanced_lookup[code] = section

        # Enhance each clinical section
        for clinical_section in clinical_sections:
            section_code = clinical_section.get("section_code")
            enhanced_section = enhanced_lookup.get(section_code)

            if enhanced_section:
                # Merge structured data
                enhanced_structured = enhanced_section.get("structured_data", [])
                if enhanced_structured:
                    # Add enhanced structured data alongside field mapped data
                    clinical_section["enhanced_structured_data"] = enhanced_structured

                # Merge table rows
                enhanced_tables = enhanced_section.get("table_rows", [])
                if enhanced_tables:
                    clinical_section["table_rows"] = enhanced_tables
                    clinical_section["has_ps_table"] = True

                # Use enhanced translation if available
                enhanced_title = enhanced_section.get("translated_title")
                if enhanced_title and enhanced_title != clinical_section.get("title"):
                    clinical_section["translated_title"] = enhanced_title

    def get_comprehensive_summary(
        self, cda_content: str, source_language: str = "en"
    ) -> Dict[str, Any]:
        """Get a comprehensive summary combining all capabilities"""
        result = self.process_clinical_document(cda_content, source_language)

        if not result["success"]:
            return result

        # Create comprehensive summary
        summary = {
            "processing_success": True,
            "patient_summary": self._summarize_patient_data(result["patient_data"]),
            "clinical_summary": self._summarize_clinical_sections(
                result["clinical_sections"]
            ),
            "field_mapping_summary": self._summarize_field_mappings(
                result["mapped_sections"]
            ),
            "metadata_summary": self._summarize_metadata(result["metadata"]),
            "total_sections": len(result["clinical_sections"]),
            "mapped_fields_count": self._count_mapped_fields(result),
            "translation_candidates": self._identify_translation_candidates(result),
        }

        return summary

    def _summarize_patient_data(self, patient_data: Dict[str, Any]) -> Dict[str, str]:
        """Summarize patient demographic data"""
        summary = {}

        for field_name, field_info in patient_data.items():
            if field_info["value"]:
                summary[field_name] = field_info["value"]

        return summary

    def _summarize_clinical_sections(
        self, clinical_sections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Summarize clinical sections"""
        summary = []

        for section in clinical_sections:
            section_summary = {
                "code": section.get("section_code"),
                "title": section.get("title"),
                "translated_title": section.get("translated_title"),
                "structured_items": len(section.get("structured_data", [])),
                "table_rows": len(section.get("table_rows", [])),
                "has_html": bool(section.get("html_content")),
                "field_mapping_success": section.get("field_mapping_success", False),
            }
            summary.append(section_summary)

        return summary

    def _summarize_field_mappings(
        self, mapped_sections: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Summarize field mapping results"""
        total_fields = 0
        found_fields = 0

        for section_data in mapped_sections.values():
            mapped_fields = section_data.get("mapped_fields", {})
            total_fields += len(mapped_fields)
            found_fields += len([f for f in mapped_fields.values() if f["value"]])

        return {
            "total_mapped_fields": total_fields,
            "fields_with_values": found_fields,
            "mapping_success_rate": (
                f"{(found_fields/total_fields*100):.1f}%" if total_fields > 0 else "0%"
            ),
        }

    def _summarize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, str]:
        """Summarize document metadata"""
        summary = {}

        for field_name, field_info in metadata.items():
            if field_info["value"]:
                summary[field_name] = field_info["value"]

        return summary

    def _count_mapped_fields(self, result: Dict[str, Any]) -> int:
        """Count total mapped fields across all sections"""
        count = 0

        # Count patient fields
        count += len([f for f in result["patient_data"].values() if f["value"]])

        # Count metadata fields
        count += len([f for f in result["metadata"].values() if f["value"]])

        # Count clinical section fields
        for section_data in result["mapped_sections"].values():
            mapped_fields = section_data.get("mapped_fields", {})
            count += len([f for f in mapped_fields.values() if f["value"]])

        return count

    def _identify_translation_candidates(
        self, result: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Identify fields that require translation"""
        candidates = []

        # Check patient fields
        for field_name, field_info in result["patient_data"].items():
            if field_info.get("translation_required") and field_info["value"]:
                candidates.append(
                    {
                        "section": "Patient",
                        "field": field_name,
                        "value": field_info["value"],
                        "type": "patient_data",
                    }
                )

        # Check clinical section fields
        for section_code, section_data in result["mapped_sections"].items():
            for field_name, field_info in section_data.get("mapped_fields", {}).items():
                if field_info.get("translation_required") and field_info["value"]:
                    candidates.append(
                        {
                            "section": section_code,
                            "field": field_name,
                            "value": field_info["value"],
                            "type": "clinical_data",
                        }
                    )

        return candidates


def test_integrated_processor():
    """Test the integrated processor with Portuguese Wave 7 data"""
    print("🔄 Testing Enhanced CDA Processor with JSON Field Mapping")
    print("=" * 60)

    # Initialize integrated processor
    processor = EnhancedCDAProcessorWithMapping(target_language="en")

    # Load Portuguese Wave 7 test data
    cda_path = "test_data/eu_member_states/PT/2-1234-W7.xml"

    try:
        with open(cda_path, "r", encoding="utf-8") as file:
            cda_content = file.read()
        print(f"✅ Loaded Wave 7 CDA: {len(cda_content)} characters")
    except FileNotFoundError:
        print(f"❌ CDA file not found: {cda_path}")
        return

    # Process the document
    result = processor.process_clinical_document(cda_content, "en")

    if result["success"]:
        print(f"✅ Processing successful!")

        # Show comprehensive summary
        summary = processor.get_comprehensive_summary(cda_content, "en")

        print(f"\n📊 Comprehensive Summary:")
        print(f"   Total sections: {summary['total_sections']}")
        print(f"   Mapped fields: {summary['mapped_fields_count']}")
        print(
            f"   Field mapping success: {summary['field_mapping_summary']['mapping_success_rate']}"
        )
        print(f"   Translation candidates: {len(summary['translation_candidates'])}")

        print(f"\n👤 Patient Summary:")
        for field, value in summary["patient_summary"].items():
            print(f"   {field}: {value}")

        print(f"\n🏥 Clinical Sections:")
        for section in summary["clinical_summary"]:
            print(f"   {section['code']}: {section['title']}")
            print(f"      Structured items: {section['structured_items']}")
            print(f"      Table rows: {section['table_rows']}")
            print(
                f"      Field mapping: {'✅' if section['field_mapping_success'] else '❌'}"
            )

    else:
        print(f"❌ Processing failed: {result['error']}")


if __name__ == "__main__":
    # Setup Django environment
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")

    try:
        import django

        django.setup()
        test_integrated_processor()
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
