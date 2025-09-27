"""
Clinical Data Extraction Debugger and Visualizer

This module provides tools for debugging and visualizing clinical data extraction
from CDA documents and translation services. It helps identify what data is being
extracted, how it's structured, and what fields are available for clinical section mapping.
"""

import io
import json
import logging
from typing import Any, Dict, List, Optional

from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import Session
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from .models import PatientData
from .services.cda_parser_service import CDAParserService
from .services.enhanced_cda_xml_parser import EnhancedCDAXMLParser
from .services.ps_table_renderer import PSTableRenderer
from .services.structured_cda_extractor import StructuredCDAExtractor

logger = logging.getLogger(__name__)


class ClinicalDataExtractor:
    """Extract and analyze clinical data from CDA documents for debugging"""

    def __init__(self):
        self.enhanced_parser = EnhancedCDAXMLParser()
        self.ps_renderer = PSTableRenderer()
        self.cda_parser = CDAParserService()
        self.structured_extractor = StructuredCDAExtractor()

    def extract_comprehensive_clinical_data(
        self, cda_content: str, session_data: dict = None
    ) -> Dict[str, Any]:
        """
        Extract comprehensive clinical data from CDA using all available parsers

        Args:
            cda_content: Raw CDA XML content
            session_data: Session data containing additional context

        Returns:
            Comprehensive clinical data structure for visualization
        """
        try:
            extraction_results = {
                "extraction_timestamp": "2024-12-19T10:30:00Z",
                "extraction_methods": [],
                "clinical_sections": {},
                "coding_analysis": {},
                "rendering_data": {},
                "raw_xml_structure": {},
                "field_mapping_opportunities": {},
                "extraction_statistics": {},
            }

            # Initialize enhanced_data for use in other methods
            enhanced_data = None

            # Method 1: Enhanced CDA XML Parser
            try:
                enhanced_data = self.enhanced_parser.parse_cda_content(cda_content)
                extraction_results["extraction_methods"].append(
                    "enhanced_cda_xml_parser"
                )
                extraction_results["clinical_sections"]["enhanced_parser"] = (
                    self._analyze_enhanced_parser_data(enhanced_data)
                )
                logger.info("Successfully extracted data using Enhanced CDA XML Parser")
            except Exception as e:
                logger.error(f"Enhanced parser failed: {e}")
                extraction_results["clinical_sections"]["enhanced_parser"] = {
                    "error": str(e)
                }

            # Method 2: PS Table Renderer
            try:
                if hasattr(self.ps_renderer, "render_section_tables"):
                    # Get sections from enhanced parser first, then render them
                    sections_to_render = enhanced_data.get(
                        "sections", enhanced_data.get("clinical_sections", [])
                    )
                    if enhanced_data and sections_to_render:
                        ps_data = self.ps_renderer.render_section_tables(
                            sections_to_render
                        )
                        extraction_results["extraction_methods"].append(
                            "ps_table_renderer"
                        )
                        extraction_results["rendering_data"]["ps_tables"] = (
                            self._analyze_ps_table_data(ps_data)
                        )
                        logger.info(
                            "Successfully extracted data using PS Table Renderer"
                        )
                    else:
                        logger.warning(
                            "No clinical sections available for PS Table rendering"
                        )
                        extraction_results["rendering_data"]["ps_tables"] = {
                            "error": "No clinical sections available"
                        }
                else:
                    # Fallback method if render_section_tables doesn't exist
                    logger.warning(
                        "PS Table Renderer method 'render_section_tables' not found"
                    )
                    extraction_results["rendering_data"]["ps_tables"] = {
                        "error": "Method not implemented"
                    }
            except Exception as e:
                logger.error(f"PS Table renderer failed: {e}")
                extraction_results["rendering_data"]["ps_tables"] = {"error": str(e)}

            # Method 3: CDA Parser Service
            try:
                cda_service_data = self.cda_parser.parse_cda_document(cda_content)
                extraction_results["extraction_methods"].append("cda_parser_service")
                extraction_results["clinical_sections"]["cda_service"] = (
                    self._analyze_cda_service_data(cda_service_data)
                )
                logger.info("Successfully extracted data using CDA Parser Service")
            except Exception as e:
                logger.error(f"CDA Parser Service failed: {e}")
                extraction_results["clinical_sections"]["cda_service"] = {
                    "error": str(e)
                }

            # Method 4: Structured CDA Extractor (NEW - captures rich hierarchical data)
            try:
                structured_data = self.structured_extractor.extract_structured_entries(
                    cda_content
                )
                extraction_results["extraction_methods"].append(
                    "structured_cda_extractor"
                )
                extraction_results["clinical_sections"]["structured_extractor"] = (
                    self._analyze_structured_extractor_data(structured_data)
                )
                logger.info(
                    "Successfully extracted structured data using Structured CDA Extractor"
                )
            except Exception as e:
                logger.error(f"Structured CDA Extractor failed: {e}")
                extraction_results["clinical_sections"]["structured_extractor"] = {
                    "error": str(e)
                }

            # Analyze coding systems and terminologies
            extraction_results["coding_analysis"] = self._analyze_clinical_coding(
                cda_content
            )

            # Identify field mapping opportunities
            try:
                extraction_results["field_mapping_opportunities"] = (
                    self._identify_mapping_opportunities(extraction_results)
                )
                logger.info(
                    "[SUCCESS] Field mapping opportunities identified successfully"
                )
            except Exception as e:
                logger.error(f"[ERROR] Field mapping opportunities failed: {e}")
                extraction_results["field_mapping_opportunities"] = {"error": str(e)}

            # Generate extraction statistics
            try:
                extraction_results["extraction_statistics"] = (
                    self._generate_extraction_statistics(extraction_results)
                )
                logger.info("[SUCCESS] Extraction statistics generated successfully")
            except Exception as e:
                logger.error(f"[ERROR] Extraction statistics failed: {e}")
                extraction_results["extraction_statistics"] = {"error": str(e)}

            # Ensure we have basic structure for template compatibility
            if "clinical_sections" not in extraction_results:
                extraction_results["clinical_sections"] = {}
            if "enhanced_parser" not in extraction_results["clinical_sections"]:
                extraction_results["clinical_sections"]["enhanced_parser"] = {
                    "sections_found": [],
                    "error": "No data extracted",
                }
            if "rendering_data" not in extraction_results:
                extraction_results["rendering_data"] = {}
            if "ps_tables" not in extraction_results["rendering_data"]:
                extraction_results["rendering_data"]["ps_tables"] = {
                    "rendered_tables": {},
                    "error": "No data rendered",
                }

            return extraction_results

        except Exception as e:
            logger.error(f"Comprehensive clinical data extraction failed: {e}")
            return {"error": str(e), "extraction_timestamp": "2024-12-19T10:30:00Z"}

    def _analyze_enhanced_parser_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data from Enhanced CDA XML Parser"""
        analysis = {
            "sections_found": [],
            "clinical_codes_extracted": {},
            "structured_data": {},
            "administrative_data": {},
        }

        if not data:
            return analysis

        # Handle both direct sections and nested clinical_sections structure
        sections_data = data.get("clinical_sections", [])
        if not sections_data and "sections" in data:
            sections_data = data.get("sections", [])

        if sections_data:
            for section in sections_data:
                # Handle both dict and object formats
                if hasattr(section, "__dict__"):
                    section_dict = section.__dict__
                else:
                    section_dict = section

                section_analysis = {
                    "section_id": section_dict.get("section_id", "unknown"),
                    "display_name": section_dict.get(
                        "display_name", section_dict.get("title", "Unknown Section")
                    ),
                    "is_coded_section": section_dict.get("is_coded_section", False),
                    "clinical_codes": section_dict.get("clinical_codes", []),
                    "narrative_text": section_dict.get("narrative_text", ""),
                    "structured_entries": section_dict.get("structured_entries", []),
                    "loinc_codes": [],
                    "snomed_codes": [],
                    "field_count": 0,
                    "coding_density": 0,
                }

                # Analyze clinical codes if they exist
                clinical_codes_obj = section_analysis["clinical_codes"]
                if clinical_codes_obj:
                    # Handle ClinicalCodesCollection object
                    if hasattr(clinical_codes_obj, "codes"):
                        codes_list = clinical_codes_obj.codes
                    elif hasattr(clinical_codes_obj, "__iter__") and not isinstance(
                        clinical_codes_obj, str
                    ):
                        codes_list = clinical_codes_obj
                    else:
                        codes_list = []

                    for code in codes_list:
                        code_dict = (
                            code
                            if isinstance(code, dict)
                            else (code.__dict__ if hasattr(code, "__dict__") else {})
                        )
                        system = code_dict.get(
                            "system", code_dict.get("code_system", "")
                        ).lower()
                        if "loinc" in system:
                            section_analysis["loinc_codes"].append(code_dict)
                        elif "snomed" in system:
                            section_analysis["snomed_codes"].append(code_dict)

                # Calculate metrics
                section_analysis["field_count"] = len(
                    section_analysis["structured_entries"]
                )
                if section_analysis["field_count"] > 0:
                    # Use the actual codes count for density calculation
                    clinical_codes_obj = section_analysis["clinical_codes"]
                    codes_count = 0
                    if hasattr(clinical_codes_obj, "codes"):
                        codes_count = len(clinical_codes_obj.codes)
                    elif hasattr(clinical_codes_obj, "__len__"):
                        codes_count = len(clinical_codes_obj)

                    section_analysis["coding_density"] = (
                        codes_count / section_analysis["field_count"]
                    )

                analysis["sections_found"].append(section_analysis)

        if "administrative_data" in data:
            analysis["administrative_data"] = data["administrative_data"]

        return analysis

    def _analyze_ps_table_data(self, data) -> Dict[str, Any]:
        """Analyze data from PS Table Renderer"""
        analysis = {
            "rendered_tables": {},
            "loinc_mappings": {},
            "rendering_quality": {},
            "display_guidelines_compliance": {},
        }

        # Handle both list and dict data formats
        sections_to_analyze = []
        if isinstance(data, list):
            # PS Table Renderer returns List[Dict]
            sections_to_analyze = data
        elif isinstance(data, dict):
            # Handle case where data is a dict with section names as keys
            sections_to_analyze = list(data.values())
        else:
            logger.warning(f"Unexpected data type for PS Table analysis: {type(data)}")
            return analysis

        # Analyze each rendered section
        for section_data in sections_to_analyze:
            if isinstance(section_data, dict):
                # Get section name from the data
                section_name = section_data.get(
                    "section_title",
                    section_data.get(
                        "title", section_data.get("display_name", "unknown_section")
                    ),
                )

                # Handle cases where section_name might be a dict
                if isinstance(section_name, dict):
                    section_name = section_name.get(
                        "translated", section_name.get("coded", "unknown_section")
                    )

                analysis["rendered_tables"][str(section_name)] = {
                    "table_rows": len(section_data.get("rows", [])),
                    "columns": list(section_data.get("headers", [])),
                    "coded_entries": len(
                        [
                            row
                            for row in section_data.get("rows", [])
                            if any("code" in str(cell).lower() for cell in row)
                        ]
                    ),
                    "display_format": section_data.get("format", "unknown"),
                    "ps_compliance": section_data.get("ps_compliant", False),
                    "has_ps_table": section_data.get("has_ps_table", False),
                    "section_code": section_data.get("section_code", "unknown"),
                }

        return analysis

    def _analyze_cda_service_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data from CDA Parser Service"""
        analysis = {
            "patient_demographics": {},
            "clinical_content": {},
            "document_metadata": {},
            "section_breakdown": {},
        }

        def safe_get(obj, key, default=None):
            """Safely get attribute or dict key from object"""
            if hasattr(obj, "get") and callable(getattr(obj, "get")):
                # It's a dict-like object
                return obj.get(key, default)
            elif hasattr(obj, key):
                # It's an object with attributes
                return getattr(obj, key, default)
            elif isinstance(obj, dict):
                # It's a plain dictionary
                return obj.get(key, default)
            else:
                return default

        def safe_len(obj, default=0):
            """Safely get length of object"""
            try:
                if obj is None:
                    return default
                elif hasattr(obj, "__len__"):
                    return len(obj)
                else:
                    return default
            except:
                return default

        def safe_keys(obj):
            """Safely get keys from object"""
            try:
                if hasattr(obj, "keys"):
                    return list(obj.keys())
                elif hasattr(obj, "__dict__"):
                    return list(obj.__dict__.keys())
                else:
                    return []
            except:
                return []

        if "patient_summary" in data:
            patient_data = data["patient_summary"]
            analysis["patient_demographics"] = {
                "identifiers_found": safe_len(
                    safe_get(patient_data, "identifiers", [])
                ),
                "demographic_fields": safe_keys(patient_data),
                "contact_info_available": bool(safe_get(patient_data, "contact_info")),
                "emergency_contacts": safe_len(
                    safe_get(patient_data, "emergency_contacts", [])
                ),
            }

        if "clinical_sections" in data:
            clinical_sections = data["clinical_sections"]
            if clinical_sections:
                for section in clinical_sections:
                    section_name = safe_get(section, "title", "unknown")
                    if not isinstance(section_name, str):
                        section_name = str(section_name) if section_name else "unknown"

                    content = safe_get(section, "content", "")
                    content_length = len(content) if isinstance(content, str) else 0

                    analysis["section_breakdown"][section_name] = {
                        "content_length": content_length,
                        "has_structured_data": bool(
                            safe_get(section, "structured_entries")
                        ),
                        "coding_present": bool(safe_get(section, "codes")),
                        "translation_quality": safe_get(
                            section, "translation_quality", "unknown"
                        ),
                    }

        return analysis

    def _analyze_structured_extractor_data(
        self, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze data from Structured CDA Extractor (NEW METHOD)"""
        analysis = {
            "structured_entries_by_type": {},
            "hierarchical_data_found": {},
            "rich_clinical_attributes": {},
            "extraction_depth": {},
        }

        for section_type, entries in data.items():
            if entries:  # Only process sections with data
                analysis["structured_entries_by_type"][section_type] = {
                    "entry_count": len(entries),
                    "entries": [],
                }

                # Analyze each entry in detail
                for entry in entries:
                    entry_analysis = {
                        "entry_id": entry.entry_id,
                        "entry_type": entry.entry_type,
                        "has_code": bool(entry.code),
                        "has_value": bool(entry.value_code or entry.value),
                        "has_effective_time": bool(entry.effective_time),
                        "has_participants": len(entry.participants) > 0,
                        "has_relationships": len(entry.entry_relationships) > 0,
                        "template_ids": entry.template_ids,
                        "rich_attributes": {},
                    }

                    # Extract rich attributes that are often missed
                    if entry.effective_time:
                        entry_analysis["rich_attributes"][
                            "effective_time"
                        ] = entry.effective_time
                    if entry.status_code:
                        entry_analysis["rich_attributes"]["status"] = entry.status_code
                    if entry.value_code:
                        entry_analysis["rich_attributes"]["value_code"] = {
                            "code": entry.value_code,
                            "system": entry.value_system,
                            "display": entry.value_display,
                        }
                    if entry.participants:
                        entry_analysis["rich_attributes"]["participants"] = [
                            {
                                "type": p.get("type_code"),
                                "substance": p.get("substance_display"),
                                "code": p.get("substance_code"),
                            }
                            for p in entry.participants
                        ]
                    if entry.entry_relationships:
                        entry_analysis["rich_attributes"]["relationships"] = [
                            {
                                "type": r.get("type_code"),
                                "value": r.get("value_display"),
                                "code": r.get("value_code"),
                            }
                            for r in entry.entry_relationships
                        ]

                    analysis["structured_entries_by_type"][section_type][
                        "entries"
                    ].append(entry_analysis)

        # Calculate extraction depth metrics - add safety checks
        total_entries = 0
        entries_with_codes = 0
        entries_with_times = 0
        entries_with_participants = 0

        for entries in data.values():
            if not entries:
                continue
            try:
                # Handle both list and non-list entries
                entry_list = entries if isinstance(entries, list) else [entries]
                total_entries += len(entry_list)

                for entry in entry_list:
                    # Skip if entry is not what we expect
                    if not hasattr(entry, "__dict__"):
                        continue

                    if hasattr(entry, "code") and entry.code:
                        entries_with_codes += 1
                    if hasattr(entry, "effective_time") and entry.effective_time:
                        entries_with_times += 1
                    if hasattr(entry, "participants") and entry.participants:
                        entries_with_participants += 1

            except Exception as e:
                logger.warning(f"Error processing entries for depth metrics: {e}")
                continue

        analysis["extraction_depth"] = {
            "total_entries": total_entries,
            "entries_with_codes": entries_with_codes,
            "entries_with_effective_times": entries_with_times,
            "entries_with_participants": entries_with_participants,
            "code_coverage": (entries_with_codes / max(1, total_entries)) * 100,
            "temporal_data_coverage": (entries_with_times / max(1, total_entries))
            * 100,
            "participant_data_coverage": (
                entries_with_participants / max(1, total_entries)
            )
            * 100,
        }

        analysis["hierarchical_data_found"] = {
            "effective_times": entries_with_times,
            "participant_substances": entries_with_participants,
            "entry_relationships": sum(
                len(entry.entry_relationships)
                for entries in data.values()
                for entry in entries
            ),
            "template_usage": sum(
                len(entry.template_ids)
                for entries in data.values()
                for entry in entries
            ),
        }

        return analysis

    def _analyze_clinical_coding(self, cda_content: str) -> Dict[str, Any]:
        """Analyze clinical coding systems used in the CDA document"""
        coding_analysis = {
            "coding_systems_found": [],
            "terminology_distribution": {},
            "code_quality_metrics": {},
            "interoperability_score": 0,
        }

        # Basic XML parsing to find coding systems
        import xml.etree.ElementTree as ET

        try:
            root = ET.fromstring(cda_content)

            # Find all code elements
            code_elements = root.findall(".//code[@code]")
            snomed_codes = [
                elem
                for elem in code_elements
                if "snomed" in elem.get("codeSystem", "").lower()
            ]
            loinc_codes = [
                elem
                for elem in code_elements
                if "loinc" in elem.get("codeSystem", "").lower()
            ]
            icd_codes = [
                elem
                for elem in code_elements
                if "icd" in elem.get("codeSystem", "").lower()
            ]

            coding_analysis["terminology_distribution"] = {
                "SNOMED_CT": len(snomed_codes),
                "LOINC": len(loinc_codes),
                "ICD": len(icd_codes),
                "Other": len(code_elements)
                - len(snomed_codes)
                - len(loinc_codes)
                - len(icd_codes),
            }

            # Safe extraction of coding systems, handling potential nested structures
            coding_systems = []
            for elem in code_elements:
                try:
                    if isinstance(elem, dict):
                        code_system = elem.get("codeSystem", "unknown")
                        # Ensure we only add strings to the set
                        if isinstance(code_system, str):
                            coding_systems.append(code_system)
                        else:
                            coding_systems.append("unknown")
                    else:
                        coding_systems.append("unknown")
                except Exception:
                    coding_systems.append("unknown")

            coding_analysis["coding_systems_found"] = list(set(coding_systems))

            # Calculate interoperability score based on standard terminology usage
            standard_codes = len(snomed_codes) + len(loinc_codes) + len(icd_codes)
            total_codes = len(code_elements)
            coding_analysis["interoperability_score"] = (
                standard_codes / max(1, total_codes)
            ) * 100

        except Exception as e:
            logger.error(f"Clinical coding analysis failed: {e}")
            coding_analysis["error"] = str(e)

        return coding_analysis

    def _identify_mapping_opportunities(
        self, extraction_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Identify opportunities for improving field mapping"""
        opportunities = {
            "unmapped_clinical_codes": [],
            "rich_data_sources": [],
            "rendering_gaps": [],
            "enhancement_suggestions": [],
        }

        # Analyze what data is available but not being used
        enhanced_sections = (
            extraction_results.get("clinical_sections", {})
            .get("enhanced_parser", {})
            .get("sections_found", [])
        )
        ps_tables = (
            extraction_results.get("rendering_data", {})
            .get("ps_tables", {})
            .get("rendered_tables", {})
        )

        for section in enhanced_sections:
            # Extract section name properly from display_name
            display_name = section.get("display_name", "unknown")
            if isinstance(display_name, dict):
                section_name = display_name.get(
                    "translated", display_name.get("coded", "unknown")
                )
            else:
                section_name = str(display_name) if display_name else "unknown"

            clinical_codes_obj = section.get("clinical_codes")

            # Handle ClinicalCodesCollection properly
            codes_count = 0
            if clinical_codes_obj:
                if hasattr(clinical_codes_obj, "codes"):
                    codes_count = len(clinical_codes_obj.codes)
                elif hasattr(clinical_codes_obj, "__len__"):
                    codes_count = len(clinical_codes_obj)

            if codes_count > 0 and section_name not in ps_tables:
                opportunities["unmapped_clinical_codes"].append(
                    {
                        "section": section_name,
                        "available_codes": codes_count,
                        "structured_entries": len(
                            section.get("structured_entries", [])
                        ),
                        "coding_density": section.get("coding_density", 0),
                    }
                )

        return opportunities

    def _generate_extraction_statistics(
        self, extraction_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate overall extraction statistics"""
        stats = {
            "total_extraction_methods": len(
                extraction_results.get("extraction_methods", [])
            ),
            "successful_extractions": len(
                [m for m in extraction_results.get("extraction_methods", [])]
            ),
            "clinical_sections_found": 0,
            "total_clinical_codes": 0,
            "rendering_coverage": 0,
            "data_quality_score": 0,
        }

        # Count clinical sections across all methods
        enhanced_parser_data = extraction_results.get("clinical_sections", {}).get(
            "enhanced_parser", {}
        )
        enhanced_sections = enhanced_parser_data.get("sections_found", [])
        stats["clinical_sections_found"] = len(enhanced_sections)

        # Count total clinical codes
        for section in enhanced_sections:
            clinical_codes_obj = section.get("clinical_codes", [])
            if hasattr(clinical_codes_obj, "codes"):
                stats["total_clinical_codes"] += len(clinical_codes_obj.codes)
            elif hasattr(clinical_codes_obj, "__len__"):
                stats["total_clinical_codes"] += len(clinical_codes_obj)
            # If it's neither, assume it's empty and add 0

        # Calculate rendering coverage
        ps_tables = (
            extraction_results.get("rendering_data", {})
            .get("ps_tables", {})
            .get("rendered_tables", {})
        )
        if enhanced_sections:
            stats["rendering_coverage"] = (
                len(ps_tables) / len(enhanced_sections)
            ) * 100

        # Calculate overall data quality score
        coding_score = extraction_results.get("coding_analysis", {}).get(
            "interoperability_score", 0
        )
        extraction_success_rate = (
            stats["successful_extractions"] / max(1, stats["total_extraction_methods"])
        ) * 100
        stats["data_quality_score"] = (
            coding_score + extraction_success_rate + stats["rendering_coverage"]
        ) / 3

        return stats


def _categorize_section(display_name):
    """
    Categorize a clinical section based on its display name
    """
    display_lower = display_name.lower()

    # Define section categories
    if any(term in display_lower for term in ["allerg", "adverse", "react"]):
        return "allergies"
    elif any(
        term in display_lower for term in ["medication", "drug", "prescr", "pharma"]
    ):
        return "medications"
    elif any(term in display_lower for term in ["problem", "diagnos", "condition"]):
        return "problems"
    elif any(term in display_lower for term in ["vital", "observation"]):
        return "vitals"
    elif any(term in display_lower for term in ["procedure", "surgic", "intervent"]):
        return "procedures"
    elif any(term in display_lower for term in ["immun", "vaccin"]):
        return "immunizations"
    elif any(term in display_lower for term in ["result", "lab", "test"]):
        return "results"
    elif any(term in display_lower for term in ["social", "history"]):
        return "social_history"
    elif any(term in display_lower for term in ["family", "genetic"]):
        return "family_history"
    elif any(term in display_lower for term in ["plan", "care", "treatment"]):
        return "care_plan"
    else:
        return "other"


# @login_required  # Temporarily disabled for testing
@require_http_methods(["GET"])
def clinical_data_debugger(request, session_id):
    """
    Clinical data extraction debugger view - visualizes all extracted clinical data
    """
    try:
        # First, try to get session data from the current request session
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key)

        # If not found in current session, search across all database sessions
        if not match_data:
            # Try to find the session_id as a direct Django session key first
            try:
                db_session = Session.objects.get(session_key=session_id)
                db_session_data = db_session.get_decoded()
                match_data = db_session_data.get(session_key)
            except Session.DoesNotExist:
                pass

            # If still not found, search all sessions for patient_match_{session_id}
            if not match_data:
                all_sessions = Session.objects.all()
                for db_session in all_sessions:
                    try:
                        db_session_data = db_session.get_decoded()
                        if session_key in db_session_data:
                            match_data = db_session_data[session_key]
                            break
                    except Exception:
                        continue  # Skip corrupted sessions

        if not match_data:
            return JsonResponse(
                {
                    "error": f"No patient data found for session {session_id}. Available sessions may use different IDs."
                },
                status=404,
            )

        # Get CDA content based on user's current selection
        selected_cda_type = match_data.get("cda_type") or match_data.get(
            "preferred_cda_type", "L3"
        )

        if selected_cda_type == "L3":
            cda_content = match_data.get("l3_cda_content")
        elif selected_cda_type == "L1":
            cda_content = match_data.get("l1_cda_content")
        else:
            # Fallback to original priority if no clear selection
            cda_content = (
                match_data.get("l3_cda_content")
                or match_data.get("l1_cda_content")
                or match_data.get("cda_content")
            )

        if not cda_content:
            return JsonResponse({"error": "No CDA content available"}, status=404)

        # Extract comprehensive clinical data
        extractor = ClinicalDataExtractor()
        extraction_results = extractor.extract_comprehensive_clinical_data(
            cda_content, match_data
        )

        # ENHANCED: Extract comprehensive CDA structure including headers, administrative data, and patient data
        comprehensive_data = {}

        try:
            from .cda_display_data_helper import CDADisplayDataHelper
            from .services.enhanced_cda_xml_parser import EnhancedCDAXMLParser

            # Initialize enhanced parsers for comprehensive extraction
            display_helper = CDADisplayDataHelper()
            enhanced_parser = EnhancedCDAXMLParser()

            # 1. Extract CDA Headers and Document Metadata
            try:
                parsed_cda = enhanced_parser.parse_cda_content(cda_content)
                comprehensive_data["cda_headers"] = {
                    "document_metadata": parsed_cda.get("document_metadata", {}),
                    "patient_identity": parsed_cda.get("patient_identity", {}),
                    "document_structure": {
                        "has_administrative_data": bool(
                            parsed_cda.get("administrative_data")
                        ),
                        "has_clinical_sections": bool(
                            parsed_cda.get("clinical_sections")
                        ),
                        "total_sections": len(parsed_cda.get("clinical_sections", [])),
                    },
                }
                logger.info(
                    f"[SUCCESS] CDA Headers extracted: {len(comprehensive_data['cda_headers'])} categories"
                )
            except Exception as e:
                logger.error(f"[ERROR] CDA Headers extraction failed: {e}")
                comprehensive_data["cda_headers"] = {"error": str(e)}

            # 2. Extract Extended Patient Data (Administrative Data)
            try:
                extended_data = display_helper.extract_extended_patient_data(
                    cda_content
                )
                if extended_data:
                    # Enhanced healthcare data mapping using the same logic as patient views
                    admin_data = extended_data.get("administrative_data", {})
                    enhanced_healthcare_data = {}

                    # Use Enhanced CDA Parser logic for healthcare data mapping
                    if (
                        admin_data.get("author_hcp")
                        or admin_data.get("author_information")
                        or admin_data.get("custodian_organization")
                        or admin_data.get("legal_authenticator")
                    ):
                        # Map author information - prefer single author_hcp, fallback to first author_information
                        if admin_data.get("author_hcp"):
                            enhanced_healthcare_data["author"] = admin_data.get(
                                "author_hcp"
                            )
                        elif admin_data.get("author_information"):
                            author_info_list = admin_data.get("author_information")
                            if (
                                isinstance(author_info_list, list)
                                and len(author_info_list) > 0
                            ):
                                # Take the first author and flatten person info to top level
                                first_author = author_info_list[0]
                                if (
                                    isinstance(first_author, dict)
                                    and "person" in first_author
                                ):
                                    # Flatten person info to top level for template compatibility
                                    enhanced_healthcare_data["author"] = {
                                        "family_name": first_author["person"].get(
                                            "family_name"
                                        ),
                                        "given_name": first_author["person"].get(
                                            "given_name"
                                        ),
                                        "full_name": first_author["person"].get(
                                            "full_name"
                                        ),
                                        "title": first_author["person"].get("title"),
                                        "role": first_author["person"].get("role"),
                                        "organization": first_author.get(
                                            "organization", {}
                                        ),
                                    }
                                else:
                                    enhanced_healthcare_data["author"] = first_author
                            else:
                                enhanced_healthcare_data["author"] = author_info_list

                        # Map organization - prefer custodian_organization, fallback to organization
                        if admin_data.get("custodian_organization"):
                            enhanced_healthcare_data["custodian"] = admin_data.get(
                                "custodian_organization"
                            )
                        elif admin_data.get("organization"):
                            enhanced_healthcare_data["custodian"] = admin_data.get(
                                "organization"
                            )

                        # Map legal authenticator
                        if admin_data.get("legal_authenticator"):
                            enhanced_healthcare_data["legal_authenticator"] = (
                                admin_data.get("legal_authenticator")
                            )

                        logger.info(
                            f"[SUCCESS] Enhanced clinical debugger healthcare_data: {list(enhanced_healthcare_data.keys())}"
                        )
                        logger.info(
                            f"[DEBUG] Enhanced Author: {enhanced_healthcare_data.get('author', {}).get('full_name', 'None')}"
                        )
                        logger.info(
                            f"[DEBUG] Enhanced Custodian: {enhanced_healthcare_data.get('custodian', {}).get('name', 'None')}"
                        )

                    # Use enhanced healthcare data if available, otherwise fallback to original
                    final_healthcare_data = (
                        enhanced_healthcare_data
                        if enhanced_healthcare_data
                        else extended_data.get("healthcare_data", {})
                    )

                    comprehensive_data["extended_patient_data"] = {
                        "administrative_data": extended_data.get(
                            "administrative_data", {}
                        ),
                        "contact_data": extended_data.get("contact_data", {}),
                        "healthcare_data": final_healthcare_data,
                        "document_details": extended_data.get("document_details", {}),
                        "patient_extended_data": extended_data.get(
                            "patient_extended_data", {}
                        ),
                    }

                    # Add summary statistics
                    admin_data = extended_data.get("administrative_data", {})
                    comprehensive_data["administrative_summary"] = {
                        "guardian_present": bool(
                            admin_data.get("guardian", {}).get("family_name")
                        ),
                        "other_contacts_count": len(
                            admin_data.get("other_contacts", [])
                        ),
                        "patient_contact_addresses": len(
                            admin_data.get("patient_contact_info", {}).get(
                                "addresses", []
                            )
                        ),
                        "patient_contact_telecoms": len(
                            admin_data.get("patient_contact_info", {}).get(
                                "telecoms", []
                            )
                        ),
                        "has_legal_authenticator": bool(
                            admin_data.get("legal_authenticator", {}).get("family_name")
                        ),
                        "has_preferred_hcp": bool(
                            admin_data.get("preferred_hcp", {}).get("name")
                        ),
                        "document_creation_date": admin_data.get(
                            "document_creation_date"
                        ),
                        "document_title": admin_data.get("document_title"),
                        "custodian_name": admin_data.get("custodian_name"),
                    }
                    logger.info(
                        f"[SUCCESS] Extended Patient Data extracted: {len(comprehensive_data['extended_patient_data'])} categories"
                    )
                else:
                    comprehensive_data["extended_patient_data"] = {
                        "error": "No extended patient data found"
                    }
                    comprehensive_data["administrative_summary"] = {
                        "error": "No administrative data available"
                    }
            except Exception as e:
                logger.error(f"[ERROR] Extended Patient Data extraction failed: {e}")
                comprehensive_data["extended_patient_data"] = {"error": str(e)}
                comprehensive_data["administrative_summary"] = {"error": str(e)}

            # 3. Extract Raw CDA Structure Analysis
            try:
                import xml.etree.ElementTree as ET

                root = ET.fromstring(cda_content)

                # Analyze CDA structure
                namespaces = dict(
                    [
                        node
                        for _, node in ET.iterparse(
                            io.StringIO(cda_content), events=["start-ns"]
                        )
                    ]
                )

                def count_elements_by_tag(element):
                    tag_counts = {}
                    for child in element.iter():
                        tag = (
                            child.tag.split("}")[-1] if "}" in child.tag else child.tag
                        )
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
                    return tag_counts

                comprehensive_data["cda_structure_analysis"] = {
                    "root_tag": (
                        root.tag.split("}")[-1] if "}" in root.tag else root.tag
                    ),
                    "namespaces": namespaces,
                    "element_counts": count_elements_by_tag(root),
                    "total_elements": len(list(root.iter())),
                    "has_structured_body": bool(root.find(".//{*}structuredBody")),
                    "has_component": bool(root.find(".//{*}component")),
                    "sections_count": len(root.findall(".//{*}section")),
                }
                logger.info(
                    f"[SUCCESS] CDA Structure Analysis complete: {comprehensive_data['cda_structure_analysis']['total_elements']} elements analyzed"
                )
            except Exception as e:
                logger.error(f"[ERROR] CDA Structure Analysis failed: {e}")
                comprehensive_data["cda_structure_analysis"] = {"error": str(e)}

        except Exception as e:
            logger.error(f"[ERROR] Comprehensive data extraction failed: {e}")
            comprehensive_data = {"error": f"Comprehensive extraction failed: {str(e)}"}

        # Prepare context for template
        try:
            # Create a safe serializable copy for JSON
            def make_serializable(obj):
                """Convert complex objects to serializable format"""
                # Handle ClinicalCodesCollection first (before checking __dict__)
                if hasattr(obj, "codes"):  # ClinicalCodesCollection-like object
                    try:
                        codes_list = make_serializable(obj.codes)
                        return {
                            "codes": codes_list,
                            "length": (
                                len(obj.codes)
                                if hasattr(obj.codes, "__len__")
                                else len(codes_list)
                            ),
                        }
                    except Exception as e:
                        logger.warning(f"Failed to serialize codes collection: {e}")
                        return {"codes": [], "length": 0}
                elif hasattr(obj, "__dict__"):
                    return {k: make_serializable(v) for k, v in obj.__dict__.items()}
                elif isinstance(obj, dict):
                    return {k: make_serializable(v) for k, v in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [make_serializable(item) for item in obj]
                else:
                    return str(obj) if obj is not None else None

            safe_extraction_results = make_serializable(extraction_results)
            extraction_json = json.dumps(safe_extraction_results, indent=2, default=str)

            # Serialize comprehensive data for JSON display
            safe_comprehensive_data = make_serializable(comprehensive_data)
            comprehensive_json = json.dumps(
                safe_comprehensive_data, indent=2, default=str
            )
        except Exception as e:
            logger.error(f"Error serializing extraction results: {e}")
            extraction_json = f'{{"error": "Serialization failed: {str(e)}"}}'
            comprehensive_json = (
                f'{{"error": "Comprehensive data serialization failed: {str(e)}"}}'
            )
            safe_comprehensive_data = {"error": str(e)}

        context = {
            "session_id": session_id,
            "patient_data": match_data.get("patient_data", {}),
            "extraction_results": safe_extraction_results,  # Use serialized version for template
            "extraction_json": extraction_json,
            "comprehensive_data": safe_comprehensive_data,  # Enhanced comprehensive data
            "comprehensive_json": comprehensive_json,  # JSON version for display
            "country_code": match_data.get("country_code", "Unknown"),
            "confidence_score": match_data.get("confidence_score", 0),
            "cda_type": selected_cda_type,  # Use the actual selected CDA type
        }

        # Add JSON versions of ALL clinical sections for easy template display
        context["clinical_sections_json"] = []
        context["allergy_sections_json"] = []  # Keep for backward compatibility

        if (
            safe_extraction_results.get("clinical_sections", {})
            .get("enhanced_parser", {})
            .get("sections_found")
        ):
            for section in safe_extraction_results["clinical_sections"][
                "enhanced_parser"
            ]["sections_found"]:
                display_name = section.get("display_name", "")
                if isinstance(display_name, dict):
                    # Handle case where display_name is a dict with 'coded' or 'translated' keys
                    display_name = (
                        display_name.get("coded", "")
                        or display_name.get("translated", "")
                        or str(display_name)
                    )
                elif not isinstance(display_name, str):
                    display_name = str(display_name)

                try:
                    section_json = json.dumps(section, indent=2, default=str)
                except Exception as json_error:
                    logger.error(f"Error serializing section: {json_error}")
                    section_json = '{"error": "Section serialization failed"}'

                section_item = {
                    "section_data": section,  # Already serialized
                    "section_json": section_json,
                    "section_type": _categorize_section(display_name),
                    "is_allergy_related": any(
                        term in display_name.lower()
                        for term in ["allerg", "adverse", "react"]
                    ),
                }

                # Add to all sections
                context["clinical_sections_json"].append(section_item)

                # Keep allergy-specific for backward compatibility
                if section_item["is_allergy_related"]:
                    context["allergy_sections_json"].append(section_item)

        # Debug logging: Verify healthcare data before template rendering
        healthcare_data = (
            context.get("comprehensive_data", {})
            .get("extended_patient_data", {})
            .get("healthcare_data", {})
        )
        logger.info(
            f"[TEMPLATE DEBUG] Healthcare data keys being passed to template: {list(healthcare_data.keys())}"
        )
        if healthcare_data.get("author"):
            author_name = healthcare_data["author"].get("full_name", "No name")
            logger.info(f"[TEMPLATE DEBUG] Author data: {author_name}")
        if healthcare_data.get("custodian"):
            custodian_name = healthcare_data["custodian"].get("name", "No name")
            logger.info(f"[TEMPLATE DEBUG] Custodian data: {custodian_name}")
        if healthcare_data.get("legal_authenticator"):
            legal_name = healthcare_data["legal_authenticator"].get(
                "full_name", "No name"
            )
            logger.info(f"[TEMPLATE DEBUG] Legal authenticator data: {legal_name}")

        return render(request, "patient_data/clinical_data_debugger.html", context)

    except Exception as e:
        logger.error(f"Clinical data debugger failed: {e}")

        # For debugging - return a simple JSON response with key statistics if we have extraction results
        try:
            if "extraction_results" in locals():
                stats = extraction_results.get("extraction_statistics", {})
                return JsonResponse(
                    {
                        "debug_info": "Template rendering failed - showing statistics",
                        "sections_found": stats.get("clinical_sections_found", 0),
                        "clinical_codes": stats.get("total_clinical_codes", 0),
                        "coded_sections": len(
                            [
                                s
                                for s in extraction_results.get("clinical_sections", {})
                                .get("enhanced_parser", {})
                                .get("sections_found", [])
                                if s.get("is_coded_section", False)
                            ]
                        ),
                        "error": str(e),
                    }
                )
        except:
            pass

        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def clinical_data_api(request, session_id):
    """
    API endpoint to get clinical data as JSON for analysis
    """
    try:
        # Get session data
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key)

        if not match_data:
            return JsonResponse({"error": "No session data found"}, status=404)

        # Get CDA content
        cda_content = (
            match_data.get("cda_content")
            or match_data.get("l3_cda_content")
            or match_data.get("l1_cda_content")
        )
        if not cda_content:
            return JsonResponse({"error": "No CDA content available"}, status=404)

        # Extract clinical data
        extractor = ClinicalDataExtractor()
        extraction_results = extractor.extract_comprehensive_clinical_data(
            cda_content, match_data
        )

        return JsonResponse(extraction_results, json_dumps_params={"indent": 2})

    except Exception as e:
        logger.error(f"Clinical data API failed: {e}")
        return JsonResponse({"error": str(e)}, status=500)
