"""
Clinical Data Integration Service

Integrates the comprehensive clinical data extraction from the clinical_data_debugger
into the main patient CDA view to enable the Clinical Information tab.
"""

import logging
from typing import Any, Dict, List, Optional

from .clinical_data_debugger import ClinicalDataExtractor

logger = logging.getLogger(__name__)


class ClinicalDataIntegrationService:
    """
    Service to integrate comprehensive clinical data extraction into main patient views
    """

    def __init__(self):
        self.extractor = ClinicalDataExtractor()

    def extract_and_format_clinical_data(
        self, cda_content: str, session_data: dict = None
    ) -> Dict[str, Any]:
        """
        Extract comprehensive clinical data and format it for the main patient template

        Args:
            cda_content: Raw CDA XML content
            session_data: Session data containing additional context

        Returns:
            Dictionary containing template-ready clinical data
        """
        try:
            # Extract comprehensive clinical data using our proven extraction methods
            extraction_results = self.extractor.extract_comprehensive_clinical_data(
                cda_content, session_data
            )

            # Format the extracted data for template consumption
            clinical_data = self._format_for_template(extraction_results)

            logger.info(
                f"[SUCCESS] Clinical data integration complete: {len(clinical_data.get('processed_sections', []))} sections processed"
            )

            return clinical_data

        except Exception as e:
            logger.error(f"[ERROR] Clinical data integration failed: {e}")
            return self._empty_clinical_data()

    def _format_for_template(
        self, extraction_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Format the comprehensive extraction results for template consumption
        """
        clinical_data = {
            "processed_sections": [],
            "medications": [],
            "allergies": [],
            "problems": [],
            "procedures": [],
            "vital_signs": [],
            "results": [],
            "immunizations": [],
            "has_clinical_data": False,
        }

        try:
            # Get enhanced parser sections
            enhanced_sections = (
                extraction_results.get("clinical_sections", {})
                .get("enhanced_parser", {})
                .get("sections_found", [])
            )

            # Get structured extractor data for detailed entries
            structured_data = (
                extraction_results.get("clinical_sections", {})
                .get("structured_extractor", {})
                .get("structured_entries_by_type", {})
            )

            if enhanced_sections:
                clinical_data["has_clinical_data"] = True

                for section in enhanced_sections:
                    # Process each section from enhanced parser
                    processed_section = self._process_enhanced_section(
                        section, structured_data
                    )

                    if processed_section:
                        clinical_data["processed_sections"].append(processed_section)

                        # Categorize into specific clinical types
                        self._categorize_clinical_data(processed_section, clinical_data)

            # Add statistics
            clinical_data["total_clinical_codes"] = extraction_results.get(
                "extraction_statistics", {}
            ).get("total_clinical_codes", 0)
            clinical_data["total_sections"] = len(clinical_data["processed_sections"])
            clinical_data["extraction_quality_score"] = extraction_results.get(
                "extraction_statistics", {}
            ).get("data_quality_score", 0)

            return clinical_data

        except Exception as e:
            logger.error(f"[ERROR] Template formatting failed: {e}")
            return self._empty_clinical_data()

    def _process_enhanced_section(
        self, section: Dict[str, Any], structured_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Process a section from the enhanced parser into template format
        """
        try:
            # Extract section display name
            display_name = section.get("display_name", "Unknown Section")
            if isinstance(display_name, dict):
                display_name = display_name.get(
                    "translated", display_name.get("coded", "Unknown Section")
                )

            section_id = section.get("section_id", "unknown")

            # Count clinical codes
            clinical_codes_obj = section.get("clinical_codes", [])
            codes_count = 0
            if hasattr(clinical_codes_obj, "codes"):
                codes_count = len(clinical_codes_obj.codes)
            elif hasattr(clinical_codes_obj, "__len__"):
                codes_count = len(clinical_codes_obj)

            # Get structured entries for this section type
            section_entries = self._get_structured_entries_for_section(
                display_name, structured_data
            )

            processed_section = {
                "section_id": section_id,
                "title": str(display_name),
                "display_name": str(display_name),
                "medical_terminology_count": codes_count,
                "has_entries": len(section_entries) > 0,
                "entries": section_entries,
                "is_coded_section": section.get("is_coded_section", False),
                "loinc_codes": section.get("loinc_codes", []),
                "snomed_codes": section.get("snomed_codes", []),
                "coding_density": section.get("coding_density", 0),
                "narrative_text": section.get("narrative_text", ""),
            }

            return processed_section

        except Exception as e:
            logger.error(f"[ERROR] Enhanced section processing failed: {e}")
            return None

    def _get_structured_entries_for_section(
        self, section_name: str, structured_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Get structured entries that match the section type
        """
        entries = []

        try:
            section_name_lower = str(section_name).lower()

            # Map section names to structured data categories
            if any(
                term in section_name_lower for term in ["medication", "drug", "prescr"]
            ):
                entries.extend(
                    self._format_structured_entries(
                        structured_data.get("medications", {})
                    )
                )
            elif any(
                term in section_name_lower for term in ["allerg", "adverse", "react"]
            ):
                entries.extend(
                    self._format_structured_entries(
                        structured_data.get("allergies", {})
                    )
                )
            elif any(
                term in section_name_lower
                for term in ["problem", "diagnos", "condition"]
            ):
                entries.extend(
                    self._format_structured_entries(structured_data.get("problems", {}))
                )
            elif any(
                term in section_name_lower
                for term in ["procedure", "surgic", "intervent"]
            ):
                entries.extend(
                    self._format_structured_entries(
                        structured_data.get("procedures", {})
                    )
                )

        except Exception as e:
            logger.warning(
                f"[WARNING] Structured entries mapping failed for {section_name}: {e}"
            )

        return entries

    def _format_structured_entries(
        self, structured_section: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Format structured entries from the structured extractor into template format
        """
        formatted_entries = []

        try:
            entries = structured_section.get("entries", [])

            for entry in entries:
                formatted_entry = {
                    "entry_id": entry.get("entry_id", "unknown"),
                    "entry_type": entry.get("entry_type", "unknown"),
                    "has_code": entry.get("has_code", False),
                    "has_value": entry.get("has_value", False),
                    "has_effective_time": entry.get("has_effective_time", False),
                    "template_ids": entry.get("template_ids", []),
                    "rich_attributes": entry.get("rich_attributes", {}),
                }
                formatted_entries.append(formatted_entry)

        except Exception as e:
            logger.warning(f"[WARNING] Structured entries formatting failed: {e}")

        return formatted_entries

    def _categorize_clinical_data(
        self, processed_section: Dict[str, Any], clinical_data: Dict[str, Any]
    ):
        """
        Categorize processed section into specific clinical data types
        """
        try:
            title_lower = processed_section["title"].lower()

            if any(term in title_lower for term in ["medication", "drug", "prescr"]):
                clinical_data["medications"].extend(processed_section["entries"])
            elif any(term in title_lower for term in ["allerg", "adverse", "react"]):
                clinical_data["allergies"].extend(processed_section["entries"])
            elif any(
                term in title_lower for term in ["problem", "diagnos", "condition"]
            ):
                clinical_data["problems"].extend(processed_section["entries"])
            elif any(
                term in title_lower for term in ["procedure", "surgic", "intervent"]
            ):
                clinical_data["procedures"].extend(processed_section["entries"])
            elif any(term in title_lower for term in ["vital", "observation"]):
                clinical_data["vital_signs"].extend(processed_section["entries"])
            elif any(term in title_lower for term in ["result", "lab", "test"]):
                clinical_data["results"].extend(processed_section["entries"])
            elif any(term in title_lower for term in ["immun", "vaccin"]):
                clinical_data["immunizations"].extend(processed_section["entries"])

        except Exception as e:
            logger.warning(f"[WARNING] Clinical data categorization failed: {e}")

    def _empty_clinical_data(self) -> Dict[str, Any]:
        """
        Return empty clinical data structure
        """
        return {
            "processed_sections": [],
            "medications": [],
            "allergies": [],
            "problems": [],
            "procedures": [],
            "vital_signs": [],
            "results": [],
            "immunizations": [],
            "has_clinical_data": False,
            "total_clinical_codes": 0,
            "total_sections": 0,
            "extraction_quality_score": 0,
        }
