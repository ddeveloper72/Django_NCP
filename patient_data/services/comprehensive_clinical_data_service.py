"""
Comprehensive Clinical Data Service
Extracts structured clinical data from CDA documents using multiple parsing strategies.
"""

import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")

try:
    django.setup()
except RuntimeError:
    # Already configured
    pass

from patient_data.services.cda_parser_service import CDAParserService
from patient_data.services.enhanced_cda_xml_parser import EnhancedCDAXMLParser
from patient_data.services.ps_table_renderer import PSTableRenderer
from patient_data.services.structured_cda_extractor import StructuredCDAExtractor
from patient_data.services.enhanced_cts_response_service import EnhancedCTSResponseService
from translation_services.terminology_translator import TerminologyTranslator
from translation_services.enhanced_cts_service import enhanced_cts_service

logger = logging.getLogger(__name__)


class ComprehensiveClinicalDataService:
    """Extract and analyze clinical data from CDA documents using multiple parsing strategies"""

    def __init__(self):
        self.enhanced_parser = EnhancedCDAXMLParser()
        self.ps_renderer = PSTableRenderer()
        self.cda_parser = CDAParserService()
        self.structured_extractor = StructuredCDAExtractor()
        self.terminology_service = TerminologyTranslator()
        self.enhanced_cts_service = EnhancedCTSResponseService()

    def extract_comprehensive_clinical_data(
        self, cda_content: str, session_data: dict = None
    ) -> Dict[str, Any]:
        """
        Extract comprehensive clinical data from CDA using all available parsers

        Args:
            cda_content: Raw CDA XML content
            session_data: Session data containing additional context

        Returns:
            Comprehensive clinical data structure for clinical display
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
                
                # DEBUG: Check what enhanced_data contains
                logger.info(f"[ENHANCED PARSER DEBUG] Enhanced data keys: {list(enhanced_data.keys())}")
                print(f"*** ENHANCED_PARSER_RESULT DEBUG: keys={list(enhanced_data.keys())} ***")
                if "detailed_medications" in enhanced_data:
                    detailed_meds = enhanced_data["detailed_medications"]
                    logger.info(f"[ENHANCED PARSER DEBUG] Found detailed_medications: {len(detailed_meds) if detailed_meds else 0}")
                    print(f"*** ENHANCED_PARSER_RESULT DEBUG: detailed_medications count={len(detailed_meds) if detailed_meds else 0} ***")
                else:
                    logger.info(f"[ENHANCED PARSER DEBUG] No detailed_medications in parser result")
                    print(f"*** ENHANCED_PARSER_RESULT DEBUG: No detailed_medications key ***")
                
                # CRITICAL FIX: If this enhanced_data doesn't have detailed_medications, try again
                if "detailed_medications" not in enhanced_data or not enhanced_data["detailed_medications"]:
                    logger.info(f"[ENHANCED PARSER FIX] First call failed to get detailed_medications, retrying...")
                    print(f"*** ENHANCED_PARSER_FIX: Retrying to get detailed_medications ***")
                    # Try again - sometimes the first call doesn't work properly
                    try:
                        enhanced_data_retry = self.enhanced_parser.parse_cda_content(cda_content)
                        if "detailed_medications" in enhanced_data_retry and enhanced_data_retry["detailed_medications"]:
                            logger.info(f"[ENHANCED PARSER FIX] Retry succeeded with {len(enhanced_data_retry['detailed_medications'])} medications")
                            print(f"*** ENHANCED_PARSER_FIX: Retry succeeded with {len(enhanced_data_retry['detailed_medications'])} medications ***")
                            enhanced_data = enhanced_data_retry  # Use the successful result
                    except Exception as e:
                        logger.warning(f"[ENHANCED PARSER FIX] Retry failed: {e}")
                
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
                    if enhanced_data and enhanced_data.get("sections"):
                        ps_tables = self.ps_renderer.render_section_tables(
                            enhanced_data["sections"]
                        )
                        extraction_results["clinical_sections"]["ps_renderer"] = (
                            self._analyze_ps_renderer_data(ps_tables)
                        )
                        extraction_results["extraction_methods"].append(
                            "ps_table_renderer"
                        )
                        logger.info(
                            f"Successfully rendered {len(ps_tables)} tables using PS Table Renderer"
                        )
                    else:
                        logger.warning(
                            "PS Table Renderer skipped - no sections from enhanced parser"
                        )
            except Exception as e:
                logger.error(f"PS Table Renderer failed: {e}")
                extraction_results["clinical_sections"]["ps_renderer"] = {
                    "error": str(e)
                }

            # Method 3: CDA Parser Service
            try:
                cda_data = self.cda_parser.parse_cda_document(cda_content)
                extraction_results["clinical_sections"]["cda_parser"] = (
                    self._analyze_cda_parser_data(cda_data)
                )
                extraction_results["extraction_methods"].append("cda_parser_service")
                logger.info("Successfully extracted data using CDA Parser Service")
            except Exception as e:
                logger.error(f"CDA Parser Service failed: {e}")
                extraction_results["clinical_sections"]["cda_parser"] = {
                    "error": str(e)
                }

            # Method 4: Structured CDA Extractor
            try:
                structured_data = self.structured_extractor.extract_structured_data(
                    cda_content
                )
                extraction_results["clinical_sections"]["structured_extractor"] = (
                    self._analyze_structured_extractor_data(structured_data)
                )
                extraction_results["extraction_methods"].append(
                    "structured_cda_extractor"
                )
                logger.info(
                    "Successfully extracted data using Structured CDA Extractor"
                )
            except Exception as e:
                logger.error(f"Structured CDA Extractor failed: {e}")
                extraction_results["clinical_sections"]["structured_extractor"] = {
                    "error": str(e)
                }

            # Generate comprehensive analysis
            extraction_results["extraction_statistics"] = (
                self._generate_extraction_statistics(extraction_results)
            )
            extraction_results["coding_analysis"] = self._analyze_clinical_coding(
                extraction_results
            )

            return extraction_results

        except Exception as e:
            logger.error(f"Comprehensive clinical data extraction failed: {e}")
            return {
                "error": str(e),
                "extraction_methods": [],
                "clinical_sections": {},
                "extraction_statistics": {},
            }

    def get_clinical_arrays_for_display(
        self, cda_content_or_comprehensive_data, session_data: dict = None
    ) -> Dict[str, List]:
        """
        Extract clinical data arrays for template display

        Args:
            cda_content_or_comprehensive_data: Either CDA content string or pre-extracted comprehensive data dict
            session_data: Optional session data

        Returns:
            Dict with medications, allergies, problems, procedures, vital_signs arrays
        """
        try:
            # Check if input is already comprehensive data or raw CDA content
            if (
                isinstance(cda_content_or_comprehensive_data, dict)
                and (
                    "clinical_sections" in cda_content_or_comprehensive_data
                    or len(cda_content_or_comprehensive_data) == 0  # Empty dict case
                )
            ):
                comprehensive_data = cda_content_or_comprehensive_data
                # If it's an empty dict, ensure it has the expected structure
                if len(comprehensive_data) == 0:
                    comprehensive_data = {
                        "clinical_sections": {},
                        "extraction_statistics": {},
                        "sections": []
                    }
            else:
                # Extract comprehensive data from CDA content
                comprehensive_data = self.extract_comprehensive_clinical_data(
                    cda_content_or_comprehensive_data, session_data
                )

            # Initialize arrays
            clinical_arrays = {
                "medications": [],
                "allergies": [],
                "problems": [],
                "procedures": [],
                "vital_signs": [],
                "results": [],
                "immunizations": [],
            }

            # PRIORITY: Check for detailed medications from Enhanced CDA XML Parser
            enhanced_data = comprehensive_data.get("clinical_sections", {}).get(
                "enhanced_parser", {}
            )
            
            # DEBUG: Log what's in enhanced_data
            logger.info(f"[DETAILED MEDICATIONS DEBUG] enhanced_data keys: {list(enhanced_data.keys())}")
            print(f"*** ENHANCED_DATA DEBUG: keys={list(enhanced_data.keys())} ***")
            if "detailed_medications" in enhanced_data:
                detailed_meds = enhanced_data["detailed_medications"]
                logger.info(f"[DETAILED MEDICATIONS DEBUG] Found detailed_medications: {len(detailed_meds) if detailed_meds else 0}")
                print(f"*** ENHANCED_DATA DEBUG: detailed_medications count={len(detailed_meds) if detailed_meds else 0} ***")
            else:
                logger.info(f"[DETAILED MEDICATIONS DEBUG] No detailed_medications key found")
                print(f"*** ENHANCED_DATA DEBUG: No detailed_medications key found ***")
            
            # If we have detailed medications from the enhanced parser, use them directly
            if "detailed_medications" in enhanced_data:
                detailed_meds = enhanced_data["detailed_medications"]
                if detailed_meds:
                    clinical_arrays["medications"] = detailed_meds
                    logger.info(f"[DETAILED MEDICATIONS] Using {len(detailed_meds)} detailed medications from Enhanced CDA Parser")
                    for med in detailed_meds[:3]:  # Debug first 3
                        name = med.get('name', 'NO_NAME')
                        dose = med.get('dose_quantity', 'NO_DOSE')
                        route = med.get('route', 'NO_ROUTE')
                        logger.info(f"[DETAILED MEDICATIONS] {name}: dose={dose}, route={route}")
                else:
                    logger.info(f"[DETAILED MEDICATIONS DEBUG] detailed_medications exists but is empty")
            
            sections_found = enhanced_data.get("sections_found", [])
            
            # Extract rich clinical data from enhanced parser sections first (skip if we have detailed medications)
            enhanced_medications_found = len(clinical_arrays["medications"]) > 0  # True if we have detailed medications
            for section in sections_found:
                if "structured_data" in section:
                    for entry in section["structured_data"]:
                        entry_data = entry.get("data", {})
                        section_type = entry.get("section_type", "")
                        entry_type = entry.get("type", "")
                        
                        # Handle different entry types from enhanced parser (skip medications if we have detailed ones)
                        if entry_type == "valueset_entry":
                            # For valueset entries, the data is in "fields"
                            entry_fields = entry.get("fields", {})
                            if section_type == "medication" and entry_fields and not enhanced_medications_found:
                                # Convert fields to data structure for template compatibility
                                medication_data = self._convert_valueset_fields_to_medication_data(entry_fields)
                                clinical_arrays["medications"].append(medication_data)
                                enhanced_medications_found = True
                        elif section_type == "medication" and entry_data and not enhanced_medications_found:
                            # Handle structured entries with data
                            clinical_arrays["medications"].append(entry_data)
                            enhanced_medications_found = True
                        elif section_type == "observation" and entry_data:
                            # Classify observations by content
                            obs_code = entry_data.get("observation_code", "")
                            obs_name = entry_data.get("observation_name", "").lower()
                            
                            if "allerg" in obs_name or "48765-2" in obs_code:
                                clinical_arrays["allergies"].append(entry_data)
                            elif "vital" in obs_name or "8716-3" in obs_code:
                                clinical_arrays["vital_signs"].append(entry_data)
                            else:
                                clinical_arrays["results"].append(entry_data)
                        elif section_type == "procedure" and entry_data:
                            clinical_arrays["procedures"].append(entry_data)

            # Primary source: CDA Parser Service structured data (fallback if enhanced parser has no medications)
            cda_data = comprehensive_data.get("clinical_sections", {}).get(
                "cda_parser", {}
            )
            if "structured_data" in cda_data:
                structured = cda_data["structured_data"]
                
                # Only use CDA parser medications if enhanced parser found none
                if not enhanced_medications_found:
                    cda_medications = structured.get("medications", [])
                    for med in cda_medications:
                        # Convert CDA parser medication to enhanced structure for consistency
                        enhanced_med = self._convert_cda_medication_to_enhanced_format(med)
                        clinical_arrays["medications"].append(enhanced_med)
                
                # Use CDA parser for other data types where enhanced parser might not have coverage
                clinical_arrays["allergies"].extend(structured.get("allergies", []))
                
                # Enhanced problem processing with rich clinical data
                raw_problems = structured.get("problems", [])
                enhanced_problems = self._extract_enhanced_problems(raw_problems)
                clinical_arrays["problems"].extend(enhanced_problems)
                
                clinical_arrays["procedures"].extend(structured.get("procedures", []))
                clinical_arrays["vital_signs"].extend(structured.get("vital_signs", []))
                clinical_arrays["results"].extend(structured.get("results", []))
                clinical_arrays["immunizations"].extend(
                    structured.get("immunizations", [])
                )

                logger.info(
                    f"[CLINICAL ARRAYS] Enhanced parser: med={len([m for m in clinical_arrays['medications'] if enhanced_medications_found])}, CDA Parser: med={len([m for m in clinical_arrays['medications'] if not enhanced_medications_found])}, all={len(clinical_arrays['allergies'])}, prob={len(clinical_arrays['problems'])}"
                )

            # CRITICAL: Fix template compatibility for medication objects
            # Template expects .coded/.translated structure but comprehensive service creates .code/.displayName structure
            self._fix_medication_template_compatibility(clinical_arrays["medications"])

            # CRITICAL ARCHITECTURAL FIX: Flatten nested data structure for template compatibility
            # Template expects med.medication_name, but we have med.data.medication_name
            self._flatten_medication_data_structure(clinical_arrays["medications"])

            # CRITICAL: Clean up data quality issues
            self._remove_duplicate_and_placeholder_data(clinical_arrays)            # If we have fewer items from both CDA parser and enhanced parser but sections exist, use section count as fallback
            total_clinical_items = sum(len(arr) for arr in clinical_arrays.values())
            if total_clinical_items == 0 and sections_found:
                logger.info(
                    f"[CLINICAL ARRAYS] CDA Parser extracted no items, using sections count as fallback"
                )
                # Count sections by type for badge display
                for section in sections_found:
                    section_code = section.get("section_code", "")
                    section_title = section.get("title", "")

                    # Create placeholder entries for sections that exist but have no extracted data
                    placeholder_entry = {
                        "display_name": section_title,
                        "section_code": section_code,
                        "source": "section_fallback",
                    }

                    if (
                        "medication" in section_title.lower()
                        or "10160-0" in section_code
                    ):
                        clinical_arrays["medications"].append(placeholder_entry)
                    elif "allerg" in section_title.lower() or "48765-2" in section_code:
                        clinical_arrays["allergies"].append(placeholder_entry)
                    elif (
                        "problem" in section_title.lower() or "11450-4" in section_code
                    ):
                        clinical_arrays["problems"].append(placeholder_entry)
                    elif (
                        "procedure" in section_title.lower()
                        or "47519-4" in section_code
                    ):
                        clinical_arrays["procedures"].append(placeholder_entry)
                    elif (
                        "vital" in section_title.lower()
                        or "physical findings" in section_title.lower()
                        or "8716-3" in section_code
                    ):
                        clinical_arrays["vital_signs"].append(placeholder_entry)
                    elif (
                        "result" in section_title.lower()
                        or "investigation" in section_title.lower()
                        or "30954-2" in section_code
                    ):
                        clinical_arrays["results"].append(placeholder_entry)
                    elif (
                        "immuniz" in section_title.lower()
                        or "vaccin" in section_title.lower()
                        or "11369-6" in section_code
                    ):
                        clinical_arrays["immunizations"].append(placeholder_entry)
                    # Additional comprehensive mappings for extended sections
                    elif (
                        "social history" in section_title.lower()
                        or "29762-2" in section_code
                    ):
                        # Social history can contain vital information - map to results
                        clinical_arrays["results"].append(placeholder_entry)
                    elif (
                        "past illness" in section_title.lower()
                        or "medical history" in section_title.lower()
                        or "11348-0" in section_code
                    ):
                        # Past illness maps to problems
                        clinical_arrays["problems"].append(placeholder_entry)
                    elif (
                        "pregnanc" in section_title.lower() or "10162-6" in section_code
                    ):
                        # Pregnancy history maps to results
                        clinical_arrays["results"].append(placeholder_entry)
                    elif (
                        "functional status" in section_title.lower()
                        or "47420-5" in section_code
                    ):
                        # Functional status maps to vital signs
                        clinical_arrays["vital_signs"].append(placeholder_entry)
                    elif (
                        "medical device" in section_title.lower()
                        or "46264-8" in section_code
                    ):
                        # Medical devices map to procedures
                        clinical_arrays["procedures"].append(placeholder_entry)
                    elif (
                        "advance directive" in section_title.lower()
                        or "42348-3" in section_code
                    ):
                        # Advance directives map to results for completeness
                        clinical_arrays["results"].append(placeholder_entry)

                logger.info(
                    f"[CLINICAL ARRAYS] Section fallback added: med={len(clinical_arrays['medications'])}, all={len(clinical_arrays['allergies'])}, prob={len(clinical_arrays['problems'])}, proc={len(clinical_arrays['procedures'])}, vs={len(clinical_arrays['vital_signs'])}"
                )

            return clinical_arrays

        except Exception as e:
            logger.error(f"Failed to get clinical arrays for display: {e}")
            return {
                "medications": [],
                "allergies": [],
                "problems": [],
                "procedures": [],
                "vital_signs": [],
                "results": [],
                "immunizations": [],
            }

    def get_administrative_data_for_display(
        self, comprehensive_data_or_cda_content, session_data: dict = None
    ) -> Dict[str, Any]:
        """
        Extract administrative and demographic data for template display

        Args:
            comprehensive_data_or_cda_content: Either comprehensive data dict or raw CDA content
            session_data: Optional session data

        Returns:
            Dict with patient_identity, document_metadata, contact_data, healthcare_provider_data
        """
        try:
            # Check if input is already comprehensive data or raw CDA content
            if (
                isinstance(comprehensive_data_or_cda_content, dict)
                and "clinical_sections" in comprehensive_data_or_cda_content
            ):
                comprehensive_data = comprehensive_data_or_cda_content
            else:
                # Extract comprehensive data from CDA content
                comprehensive_data = self.extract_comprehensive_clinical_data(
                    comprehensive_data_or_cda_content, session_data
                )

            # Initialize administrative data structure
            admin_data = {
                "patient_identity": {},
                "document_metadata": {},
                "contact_data": {},
                "healthcare_provider_data": {},
            }

            # Extract from enhanced parser results
            enhanced_data = comprehensive_data.get("clinical_sections", {}).get(
                "enhanced_parser", {}
            )

            # Patient Identity Data
            if "patient_identity" in enhanced_data:
                admin_data["patient_identity"] = enhanced_data["patient_identity"]
                logger.info(
                    f"[ADMIN DATA] Extracted patient identity: {enhanced_data['patient_identity'].get('full_name', 'Unknown')}"
                )

            # Administrative/Document Data
            if "administrative_data" in enhanced_data:
                admin_section = enhanced_data["administrative_data"]

                # Document metadata
                admin_data["document_metadata"] = {
                    "document_title": admin_section.get("document_title", ""),
                    "document_type": admin_section.get("document_type", ""),
                    "document_id": admin_section.get("document_id", ""),
                    "document_creation_date": admin_section.get(
                        "document_creation_date", ""
                    ),
                    "document_creation_date_raw": admin_section.get(
                        "document_creation_date_raw", ""
                    ),
                    "document_last_update_date": admin_section.get(
                        "document_last_update_date", ""
                    ),
                    "document_version_number": admin_section.get(
                        "document_version_number", ""
                    ),
                    "custodian_name": admin_section.get("custodian_name", ""),
                }

                # Contact data
                admin_data["contact_data"] = {
                    "patient_contact_info": admin_section.get(
                        "patient_contact_info", {}
                    ),
                    "guardian": admin_section.get("guardian", {}),
                    "other_contacts": admin_section.get("other_contacts", []),
                }

                # Healthcare provider data
                admin_data["healthcare_provider_data"] = {
                    "author_hcp": admin_section.get("author_hcp", {}),
                    "author_information": admin_section.get("author_information", []),
                    "legal_authenticator": admin_section.get("legal_authenticator", {}),
                    "custodian_organization": admin_section.get(
                        "custodian_organization", {}
                    ),
                    "preferred_hcp": admin_section.get("preferred_hcp", {}),
                }

                logger.info(
                    f"[ADMIN DATA] Extracted document: {admin_data['document_metadata']['document_title']}"
                )
                logger.info(
                    f"[ADMIN DATA] Extracted custodian: {admin_data['document_metadata']['custodian_name']}"
                )
                logger.info(
                    f"[ADMIN DATA] Extracted contact addresses: {len(admin_data['contact_data']['patient_contact_info'].get('addresses', []))}"
                )

            return admin_data

        except Exception as e:
            logger.error(f"Failed to get administrative data for display: {e}")
            return {
                "patient_identity": {},
                "document_metadata": {},
                "contact_data": {},
                "healthcare_provider_data": {},
            }

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

        # CRITICAL FIX: Extract detailed medications from Enhanced parser
        if "detailed_medications" in data:
            analysis["detailed_medications"] = data["detailed_medications"]
            logger.info(f"[ENHANCED_ANALYSIS] Preserved {len(data['detailed_medications'])} detailed medications from Enhanced parser")
            print(f"*** ENHANCED_ANALYSIS DEBUG: Preserved {len(data['detailed_medications'])} detailed medications ***")
        else:
            logger.info(f"[ENHANCED_ANALYSIS] No detailed_medications in input data, keys: {list(data.keys())}")
            print(f"*** ENHANCED_ANALYSIS DEBUG: No detailed_medications in input data, keys: {list(data.keys())} ***")

        # Extract administrative data if available
        if "administrative_data" in data:
            analysis["administrative_data"] = data["administrative_data"]

        # Extract patient identity data if available
        if "patient_identity" in data:
            analysis["patient_identity"] = data["patient_identity"]

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
                        "title", section_dict.get("section_title", "Unknown Section")
                    ),
                    "section_code": section_dict.get("section_code"),
                    "clinical_codes_extracted": {
                        "codes": [],
                        "count": 0,
                        "coding_systems": set(),
                    },
                    "text_content": section_dict.get("original_text_html", ""),
                    "template_ids": section_dict.get("template_ids", []),
                }

                # Extract clinical codes if available
                clinical_codes = section_dict.get("clinical_codes", [])
                if hasattr(clinical_codes, "codes"):
                    clinical_codes = clinical_codes.codes

                if clinical_codes:
                    for code in clinical_codes:
                        if hasattr(code, "__dict__"):
                            code_dict = code.__dict__
                        else:
                            code_dict = code

                        code_info = {
                            "code": code_dict.get("code"),
                            "system": code_dict.get("system"),
                            "display_name": code_dict.get("display_name"),
                            "system_name": code_dict.get("system_name"),
                        }
                        section_analysis["clinical_codes_extracted"]["codes"].append(
                            code_info
                        )
                        if code_dict.get("system"):
                            section_analysis["clinical_codes_extracted"][
                                "coding_systems"
                            ].add(code_dict.get("system"))

                section_analysis["clinical_codes_extracted"]["count"] = len(
                    section_analysis["clinical_codes_extracted"]["codes"]
                )
                section_analysis["clinical_codes_extracted"]["coding_systems"] = list(
                    section_analysis["clinical_codes_extracted"]["coding_systems"]
                )

                analysis["sections_found"].append(section_analysis)

        # Extract administrative data
        if "administrative_data" in data:
            analysis["administrative_data"] = data["administrative_data"]

        return analysis

    def _analyze_ps_renderer_data(self, data: Any) -> Dict[str, Any]:
        """Analyze data from PS Table Renderer"""
        return {"tables_rendered": len(data) if data else 0, "data": data}

    def _analyze_cda_parser_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data from CDA Parser Service"""
        analysis = {"structured_data": {}, "sections_count": 0}

        if data and isinstance(data, dict):
            # Extract structured body if available
            structured_body = data.get("structured_body", {})
            if structured_body:
                analysis["structured_data"] = structured_body
                analysis["sections_count"] = len(
                    [
                        key
                        for key, value in structured_body.items()
                        if isinstance(value, list) and value
                    ]
                )

        return analysis

    def _analyze_structured_extractor_data(self, data: Any) -> Dict[str, Any]:
        """Analyze data from Structured CDA Extractor"""
        return {"data_extracted": bool(data), "structure": type(data).__name__}

    def _generate_extraction_statistics(
        self, extraction_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive extraction statistics"""
        stats = {
            "total_methods_attempted": len(extraction_results["extraction_methods"]),
            "successful_methods": [],
            "failed_methods": [],
            "total_sections_found": 0,
            "total_clinical_codes": 0,
        }

        for method in extraction_results["extraction_methods"]:
            method_data = extraction_results["clinical_sections"].get(method, {})
            if "error" not in method_data:
                stats["successful_methods"].append(method)
                # Count sections and codes
                if method == "enhanced_parser" and "sections_found" in method_data:
                    stats["total_sections_found"] += len(method_data["sections_found"])
                    for section in method_data["sections_found"]:
                        stats["total_clinical_codes"] += section.get(
                            "clinical_codes_extracted", {}
                        ).get("count", 0)
            else:
                stats["failed_methods"].append(method)

        return stats

    def _analyze_clinical_coding(
        self, extraction_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze clinical coding across all extraction methods"""
        coding_systems = set()
        total_codes = 0

        for method, data in extraction_results["clinical_sections"].items():
            if "error" in data:
                continue

            if method == "enhanced_parser" and "sections_found" in data:
                for section in data["sections_found"]:
                    codes_data = section.get("clinical_codes_extracted", {})
                    total_codes += codes_data.get("count", 0)
                    coding_systems.update(codes_data.get("coding_systems", []))

        return {
            "total_clinical_codes": total_codes,
            "coding_systems_used": list(coding_systems),
            "coding_systems_count": len(coding_systems),
        }
    
    def _convert_valueset_fields_to_medication_data(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Convert valueset fields to medication data structure for template compatibility"""
        medication_data = {}
        
        # Map common medication fields
        field_mappings = {
            'substance_name': 'medication_name',
            'substance_code': 'substance_code', 
            'substance_display_name': 'substance_display_name',
            'administration_route': 'route',
            'dosage_instruction': 'dosage_instruction',
            'frequency': 'frequency',
            'pharmaceutical_form': 'form',
            'pharmaceutical_form_code': 'form_code'
        }
        
        # Apply field mappings
        for field_key, med_key in field_mappings.items():
            if field_key in fields:
                medication_data[med_key] = fields[field_key]
        
        # CTS Integration: Resolve administration route codes to display text
        # Check multiple possible route field names (CDA uses 'routeCode', templates expect 'route_display')
        route_source = fields.get('administration_route') or fields.get('routeCode') or fields.get('route')
        if route_source:
            route_data = route_source
            
            # Handle both simple codes and complex route structures
            route_code = None
            route_display = None
            
            if isinstance(route_data, dict):
                route_code = route_data.get('code')
                route_display = route_data.get('display_name') or route_data.get('displayName') or route_data.get('display')
            elif isinstance(route_data, str) and route_data.isdigit():
                route_code = route_data
            elif isinstance(route_data, str):
                # Could be a display name already
                route_display = route_data
            
            # Use CTS to resolve route code if available
            if route_code and not route_display:
                try:
                    route_display = self.terminology_service.resolve_code(route_code)
                    if route_display:
                        logger.info(f"CTS resolved route code {route_code} to '{route_display}'")
                except Exception as e:
                    logger.warning(f"Failed to resolve route code {route_code} via CTS: {e}")
            
            # Set medication route data with CTS-resolved display
            if route_display:
                medication_data['route'] = {
                    'code': route_code,
                    'display_name': route_display
                }
                # CRITICAL: Set route_display for template compatibility
                medication_data['route_display'] = route_display
            elif route_code:
                medication_data['route'] = {
                    'code': route_code,
                    'display_name': route_code  # Fallback to code if no display found
                }
                medication_data['route_display'] = route_code
        
        # Also check for route_display directly from CDA parser
        if 'route_display' in fields:
            medication_data['route_display'] = fields['route_display']
        
        # CTS Integration: Resolve pharmaceutical form codes to display text
        if 'pharmaceutical_form' in fields:
            form_data = fields['pharmaceutical_form']
            
            # Handle both simple codes and complex form structures
            form_code = None
            form_display = None
            
            if isinstance(form_data, dict):
                form_code = form_data.get('code')
                form_display = form_data.get('display_name') or form_data.get('display')
            elif isinstance(form_data, str) and form_data.isdigit():
                form_code = form_data
            
            # Use CTS to resolve form code if available
            if form_code and not form_display:
                try:
                    form_display = self.terminology_service.resolve_code(form_code)
                    if form_display:
                        logger.info(f"CTS resolved pharmaceutical form code {form_code} to '{form_display}'")
                except Exception as e:
                    logger.warning(f"Failed to resolve pharmaceutical form code {form_code} via CTS: {e}")
            
            # Set medication form data with CTS-resolved display
            if form_display:
                medication_data['form'] = {
                    'code': form_code,
                    'display_name': form_display
                }
                # Also set for template compatibility
                medication_data['pharmaceutical_form'] = form_display
                medication_data['pharmaceutical_form_code'] = form_code
            elif form_code:
                medication_data['form'] = {
                    'code': form_code,
                    'display_name': form_code  # Fallback to code if no display found
                }
                medication_data['pharmaceutical_form_code'] = form_code
        
        # Also check for pharmaceutical_form_code as separate field
        elif 'pharmaceutical_form_code' in fields:
            form_code = fields['pharmaceutical_form_code']
            form_code_system = fields.get('pharmaceutical_form_code_system', '')
            
            # Use CTS to resolve form code with codeSystem
            if form_code:
                try:
                    # Pass both code AND codeSystem for proper CTS resolution
                    form_display = self.terminology_service.resolve_code(form_code, form_code_system)
                    if form_display:
                        logger.info(f"CTS resolved pharmaceutical form code {form_code} (system: {form_code_system}) to '{form_display}'")
                        medication_data['pharmaceutical_form'] = form_display
                        medication_data['pharmaceutical_form_code'] = form_code
                        medication_data['form'] = {
                            'code': form_code,
                            'display_name': form_display
                        }
                    else:
                        medication_data['pharmaceutical_form_code'] = form_code
                except Exception as e:
                    logger.warning(f"Failed to resolve pharmaceutical form code {form_code} (system: {form_code_system}) via CTS: {e}")
                    medication_data['pharmaceutical_form_code'] = form_code
        
        # CTS Integration: Resolve active ingredient/substance codes to display text
        if 'substance_code' in fields:
            substance_code = fields['substance_code']
            substance_display = fields.get('substance_display_name') or fields.get('substance_name')
            
            # Use CTS to resolve substance code if no display name available
            if substance_code and not substance_display:
                try:
                    substance_display = self.terminology_service.resolve_code(substance_code)
                    if substance_display:
                        logger.info(f"CTS resolved substance code {substance_code} to '{substance_display}'")
                except Exception as e:
                    logger.warning(f"Failed to resolve substance code {substance_code} via CTS: {e}")
            
            # Set ingredient data with CTS-resolved display
            if substance_display:
                medication_data['ingredient_display'] = substance_display
                medication_data['ingredient_code'] = substance_code
                medication_data['active_ingredient'] = {
                    'code': substance_code,
                    'display_name': substance_display
                }
            elif substance_code:
                medication_data['ingredient_code'] = substance_code
        
        # Also check for separate active ingredient fields
        elif 'active_ingredient_code' in fields:
            ingredient_code = fields['active_ingredient_code']
            ingredient_code_system = fields.get('active_ingredient_code_system')
            ingredient_display = fields.get('active_ingredient_display') or fields.get('active_ingredient_name')
            
            # Use NEW Comprehensive Enhanced CTS to resolve ingredient code
            if ingredient_code:
                try:
                    comprehensive_response = enhanced_cts_service.get_comprehensive_code_data(
                        code=ingredient_code,
                        code_system_oid=ingredient_code_system,
                        target_language='en',
                        include_all_languages=True
                    )
                    
                    if comprehensive_response:
                        # Use comprehensive structured CTS response for full medication data
                        medication_data['ingredient_display'] = comprehensive_response['code_name']
                        medication_data['ingredient_code'] = comprehensive_response['code']  # ACTUAL CODE
                        medication_data['ingredient_description'] = comprehensive_response['description']
                        medication_data['therapeutic_class'] = comprehensive_response.get('description', '')
                        medication_data['active_ingredient'] = {
                            'code': comprehensive_response['code'],  # ACTUAL CTS CODE (e.g., H03AA01)
                            'coded': comprehensive_response['code'],  # FOR TEMPLATE DISPLAY - ACTUAL CODE
                            'display_name': comprehensive_response['code_name'],
                            'description': comprehensive_response['description'],
                            'code_system_id': comprehensive_response['code_system_id'],
                            'code_system_version': comprehensive_response['code_system_version'],
                            'languages': comprehensive_response['languages'],
                            'cts_metadata': comprehensive_response['cts_metadata']
                        }
                        logger.info(f"Enhanced CTS resolved ingredient {ingredient_code} → {comprehensive_response['code']} ({comprehensive_response['code_name']})")
                    else:
                        # Fallback response
                        medication_data['ingredient_code'] = ingredient_code
                        medication_data['active_ingredient'] = {
                            'code': ingredient_code,
                            'coded': ingredient_code,  # Show actual code even if not resolved
                            'display_name': ingredient_display or f"Code: {ingredient_code}"
                        }
                        
                except Exception as e:
                    logger.warning(f"Enhanced CTS ingredient resolution failed for {ingredient_code}: {e}")
                    # Fallback to basic resolution
                    medication_data['ingredient_code'] = ingredient_code
                    if ingredient_display:
                        medication_data['ingredient_display'] = ingredient_display
                    medication_data['active_ingredient'] = {
                        'code': ingredient_code,
                        'coded': ingredient_code,  # Always show the actual code
                        'display_name': ingredient_display or f"Code: {ingredient_code}",
                        'description': ingredient_display or f"Code: {ingredient_code}",
                        'code_system_id': ingredient_code_system,
                        'code_system_version': None,
                        'languages': {},
                        'cts_metadata': None
                    }
        
        # Enhanced active ingredient extraction from CDA structure
        # Check for active ingredient data in consumable/manufactured material structure
        if 'consumable' in fields:
            consumable_data = fields['consumable']
            if isinstance(consumable_data, dict):
                # Extract manufactured material from consumable
                manufactured_product = consumable_data.get('manufactured_product', {})
                manufactured_material = manufactured_product.get('manufactured_material', {})
                
                # Extract brand name if available
                if 'name' in manufactured_material and not medication_data.get('medication_name'):
                    medication_data['medication_name'] = manufactured_material['name']
                
                # Extract pharmaceutical form from manufactured material
                if 'form_code' in manufactured_material:
                    form_code = manufactured_material['form_code']
                    try:
                        form_display = self.terminology_service.resolve_code(form_code)
                        if form_display:
                            medication_data['pharmaceutical_form'] = form_display
                            medication_data['pharmaceutical_form_code'] = form_code
                            logger.info(f"CTS resolved pharmaceutical form code {form_code} to '{form_display}'")
                    except Exception as e:
                        logger.warning(f"Failed to resolve pharmaceutical form code {form_code}: {e}")
                
                # Extract active ingredients - ENHANCED: Handle multiple ingredients for combination medications
                ingredient_displays = []
                ingredient_codes = []
                primary_ingredient = None
                
                # Check for multiple ingredients first (new field)
                if 'all_ingredients' in manufactured_material:
                    all_ingredients = manufactured_material['all_ingredients']
                    if isinstance(all_ingredients, list):
                        for ingredient_data in all_ingredients:
                            if isinstance(ingredient_data, dict):
                                ingredient_substance = ingredient_data.get('ingredient_substance', {})
                                ingredient_code = ingredient_substance.get('code')
                                ingredient_code_system = ingredient_substance.get('code_system')
                                
                                if ingredient_code:
                                    try:
                                        # Use NEW Comprehensive Enhanced CTS for full MVC data
                                        comprehensive_response = enhanced_cts_service.get_comprehensive_code_data(
                                            code=ingredient_code,
                                            code_system_oid=ingredient_code_system,
                                            target_language='en',
                                            include_all_languages=True
                                        )
                                        
                                        if comprehensive_response:
                                            ingredient_display = comprehensive_response['code_name']
                                            
                                            # Extract strength from ingredient quantity
                                            strength_info = ""
                                            if 'quantity' in ingredient_data:
                                                quantity_data = ingredient_data['quantity']
                                                if isinstance(quantity_data, dict):
                                                    numerator = quantity_data.get('numerator', {})
                                                    if isinstance(numerator, dict):
                                                        num_value = numerator.get('value', '')
                                                        num_unit = numerator.get('unit', '')
                                                        if num_value and num_unit:
                                                            strength_info = f" {num_value} {num_unit}"
                                            
                                            ingredient_display_with_strength = f"{ingredient_display}{strength_info}"
                                            ingredient_displays.append(ingredient_display_with_strength)
                                            ingredient_codes.append(comprehensive_response['code'])  # ACTUAL CTS CODE (e.g., H03AA01)
                                            
                                            if not primary_ingredient:
                                                primary_ingredient = {
                                                    'code': comprehensive_response['code'],  # ACTUAL CODE
                                                    'coded': comprehensive_response['code'],  # FOR TEMPLATE - ACTUAL CODE
                                                    'display_name': comprehensive_response['code_name'],
                                                    'description': comprehensive_response['description'],
                                                    'cts_metadata': comprehensive_response['cts_metadata'],
                                                    'languages': comprehensive_response['languages'],
                                                    'code_system_version': comprehensive_response['code_system_version'],
                                                    'strength': strength_info.strip()
                                                }
                                            
                                            logger.info(f"Enhanced CTS resolved ingredient {ingredient_code} → {comprehensive_response['code']} ({comprehensive_response['code_name']}){strength_info}")
                                        else:
                                            # Use fallback but still show actual code
                                            ingredient_codes.append(ingredient_code)
                                            ingredient_displays.append(f"Code: {ingredient_code}")
                                            
                                    except Exception as e:
                                        logger.warning(f"Enhanced CTS ingredient resolution failed for {ingredient_code}: {e}")
                                        ingredient_codes.append(ingredient_code)
                                        ingredient_displays.append(f"Code: {ingredient_code}")
                                        
                                        if not primary_ingredient:
                                            primary_ingredient = {
                                                'code': ingredient_code,
                                                'coded': ingredient_code,  # Show actual code
                                                'display_name': f"Code: {ingredient_code}",
                                                'description': f"Code: {ingredient_code}",
                                                'code_system_id': ingredient_code_system,
                                                'code_system_version': None,
                                                'languages': {},
                                                'cts_metadata': None
                                            }
                        
                        # Set combined ingredient display
                        if ingredient_displays:
                            medication_data['ingredient_display'] = ', '.join(ingredient_displays)
                            medication_data['ingredient_code'] = ingredient_codes[0] if ingredient_codes else ''
                            medication_data['active_ingredient'] = primary_ingredient
                            medication_data['all_ingredients'] = [{
                                'code': code,
                                'display_name': display.split(' ')[0] if ' ' in display else display,
                                'strength': display.split(' ', 1)[1] if ' ' in display else ''
                            } for code, display in zip(ingredient_codes, ingredient_displays)]
                
                # Fallback to single ingredient (backward compatibility)
                elif 'ingredient' in manufactured_material:
                    ingredient_data = manufactured_material['ingredient']
                    if isinstance(ingredient_data, dict):
                        ingredient_substance = ingredient_data.get('ingredient_substance', {})
                        
                        # Get active ingredient code
                        ingredient_code = ingredient_substance.get('code')
                        ingredient_code_system = ingredient_substance.get('code_system')
                        
                        if ingredient_code:
                            try:
                                # Use NEW Comprehensive Enhanced CTS for single ingredient
                                comprehensive_response = enhanced_cts_service.get_comprehensive_code_data(
                                    code=ingredient_code,
                                    code_system_oid=ingredient_code_system,
                                    target_language='en',
                                    include_all_languages=True
                                )
                                
                                if comprehensive_response:
                                    medication_data['ingredient_display'] = comprehensive_response['code_name']
                                    medication_data['ingredient_code'] = comprehensive_response['code']  # ACTUAL CODE
                                    medication_data['ingredient_description'] = comprehensive_response['description']
                                    medication_data['active_ingredient'] = {
                                        'code': comprehensive_response['code'],  # ACTUAL CODE
                                        'coded': comprehensive_response['code'],  # FOR TEMPLATE - ACTUAL CODE
                                        'display_name': comprehensive_response['code_name'],
                                        'description': comprehensive_response['description'],
                                        'code_system_id': comprehensive_response['code_system_id'],
                                        'code_system_version': comprehensive_response['code_system_version'],
                                        'languages': comprehensive_response['languages'],
                                        'cts_metadata': comprehensive_response['cts_metadata']
                                    }
                                    logger.info(f"Enhanced CTS resolved single ingredient {ingredient_code} → {comprehensive_response['code']} ({comprehensive_response['code_name']})")
                                else:
                                    # Fallback to show actual code
                                    medication_data['ingredient_code'] = ingredient_code
                                    medication_data['active_ingredient'] = {
                                        'code': ingredient_code,
                                        'coded': ingredient_code,  # Show actual code
                                        'display_name': f"Code: {ingredient_code}"
                                    }
                                    
                            except Exception as e:
                                logger.warning(f"Enhanced CTS single ingredient resolution failed for {ingredient_code}: {e}")
                                medication_data['ingredient_code'] = ingredient_code
                                medication_data['active_ingredient'] = {
                                    'code': ingredient_code,
                                    'coded': ingredient_code,  # Always show actual code
                                    'display_name': f"Code: {ingredient_code}",
                                    'description': f"Code: {ingredient_code}",
                                    'code_system_id': ingredient_code_system,
                                    'code_system_version': None,
                                    'languages': {},
                                    'cts_metadata': None
                                }
                        
                        # Extract strength from ingredient quantity
                        if 'quantity' in ingredient_data:
                            quantity_data = ingredient_data['quantity']
                            if isinstance(quantity_data, dict):
                                numerator = quantity_data.get('numerator', {})
                                denominator = quantity_data.get('denominator', {})
                                
                                if isinstance(numerator, dict) and isinstance(denominator, dict):
                                    num_value = numerator.get('value', '')
                                    num_unit = numerator.get('unit', '')
                                    denom_value = denominator.get('value', '')
                                    
                                    if num_value and num_unit and denom_value:
                                        medication_data['strength'] = f"({num_value} {num_unit}/{denom_value})"
                                    elif num_value and num_unit:
                                        medication_data['strength'] = f"({num_value} {num_unit})"

        # Ensure we extract all medication data from the actual CDA document, not hardcoded mappings
        # All ingredient codes, names, and strengths should come from the parsed CDA XML
        
        # If we still don't have ingredient data, try to extract from medication codes in CDA
        if not medication_data.get('ingredient_display') and 'medication' in medication_data:
            medication_code = medication_data.get('medication', {}).get('code', {}).get('code')
            if medication_code:
                try:
                    # Use CTS to resolve medication code to active ingredient
                    ingredient_display = self.terminology_service.resolve_code(medication_code)
                    if ingredient_display:
                        medication_data['ingredient_display'] = ingredient_display
                        medication_data['ingredient_code'] = medication_code
                        medication_data['active_ingredient'] = {
                            'code': medication_code,
                            'display_name': ingredient_display
                        }
                        logger.info(f"CTS resolved medication code {medication_code} to '{ingredient_display}'")
                except Exception as e:
                    logger.warning(f"Failed to resolve medication code {medication_code}: {e}")
                    # Store the code even if we can't resolve the display name
                    medication_data['ingredient_code'] = medication_code
        
        # Handle strength/dosage information
        if 'strength' in fields:
            strength_data = fields['strength']
            if isinstance(strength_data, dict):
                # Extract strength value and unit
                value = strength_data.get('value', '')
                unit = strength_data.get('unit', '')
                if value and unit:
                    medication_data['strength'] = f"({value} {unit})"
                elif value:
                    medication_data['strength'] = f"({value})"
            else:
                medication_data['strength'] = f"({strength_data})" if strength_data else ''
        elif 'dosage_strength' in fields:
            dosage_strength = fields['dosage_strength']
            if dosage_strength:
                medication_data['strength'] = f"({dosage_strength})"
        
        # Handle pharmaceutical quantity with proper formatting
        if 'pharmaceutical_quantity' in fields:
            quantity_data = fields['pharmaceutical_quantity']
            if isinstance(quantity_data, dict):
                # Extract numerator for display value
                numerator = quantity_data.get('numerator', {})
                if isinstance(numerator, dict):
                    value = numerator.get('value', '')
                    unit = numerator.get('unit', '')
                    
                    # Format as simple string for template display
                    if value and unit:
                        medication_data['quantity'] = f"{value} {unit}"
                    elif value:
                        medication_data['quantity'] = str(value)
                else:
                    # Handle case where numerator is already a simple value
                    medication_data['quantity'] = str(numerator) if numerator else ''
            else:
                medication_data['quantity'] = str(quantity_data)
        
        # Enhanced dose quantity handling for CDA structure
        # Check both 'dose_quantity' and 'doseQuantity' (CDA field name)
        dose_source = fields.get('dose_quantity') or fields.get('doseQuantity')
        if dose_source:
            dose_data = dose_source
            if isinstance(dose_data, dict):
                # Handle range format with low/high values (CDA doseQuantity structure)
                low_value = None
                high_value = None
                
                # Extract low value
                if 'low' in dose_data:
                    low_data = dose_data['low']
                    if isinstance(low_data, dict):
                        low_value = low_data.get('value')
                        low_unit = low_data.get('unit', '')
                    else:
                        low_value = low_data
                        low_unit = ''
                
                # Extract high value  
                if 'high' in dose_data:
                    high_data = dose_data['high']
                    if isinstance(high_data, dict):
                        high_value = high_data.get('value')
                        high_unit = high_data.get('unit', '')
                    else:
                        high_value = high_data
                        high_unit = ''
                
                # Format dose quantity for display
                if low_value and high_value:
                    if low_unit:
                        medication_data['dose_quantity'] = f"{low_value}-{high_value} {low_unit}"
                    else:
                        medication_data['dose_quantity'] = f"{low_value}-{high_value}"
                elif low_value:
                    if low_unit:
                        medication_data['dose_quantity'] = f"{low_value} {low_unit}"
                    else:
                        medication_data['dose_quantity'] = str(low_value)
                elif 'value' in dose_data:
                    # Single value dose quantity
                    value = dose_data.get('value', '')
                    unit = dose_data.get('unit', '')
                    if value and unit:
                        medication_data['dose_quantity'] = f"{value} {unit}"
                    elif value:
                        medication_data['dose_quantity'] = str(value)
            else:
                medication_data['dose_quantity'] = str(dose_data) if dose_data else ''
        
        # CTS Integration: Extract and resolve schedule/frequency information
        if 'frequency' in fields:
            frequency_data = fields['frequency']
            
            # Handle various frequency formats
            if isinstance(frequency_data, dict):
                freq_code = frequency_data.get('code') or frequency_data.get('event_code')
                freq_display = frequency_data.get('display_name') or frequency_data.get('display')
                
                # Use CTS to resolve frequency code
                if freq_code and not freq_display:
                    try:
                        freq_display = self.terminology_service.resolve_code(freq_code, '2.16.840.1.113883.5.139')
                        if freq_display:
                            logger.info(f"CTS resolved frequency code {freq_code} to '{freq_display}'")
                    except Exception as e:
                        logger.warning(f"Failed to resolve frequency code {freq_code} via CTS: {e}")
                
                # Set frequency data with CTS-resolved display
                if freq_display:
                    medication_data['frequency_display'] = freq_display
                    medication_data['frequency_code'] = freq_code
                elif freq_code:
                    medication_data['frequency_code'] = freq_code
            elif isinstance(frequency_data, str):
                medication_data['frequency'] = frequency_data
        
        # CTS Integration: Extract schedule information from effective_time events (ACM, etc.)
        if 'effective_time_events' in fields:
            events = fields['effective_time_events']
            if isinstance(events, list):
                for event in events:
                    if isinstance(event, dict):
                        event_code = event.get('code')
                        event_system = event.get('code_system', '2.16.840.1.113883.5.139')
                        
                        # Resolve timing event codes like ACM, PC, BID, etc.
                        if event_code:
                            try:
                                event_display = self.terminology_service.resolve_code(event_code, event_system)
                                if event_display:
                                    medication_data['frequency_display'] = event_display
                                    medication_data['frequency_code'] = event_code
                                    logger.info(f"CTS resolved timing event {event_code} to '{event_display}'")
                                    break  # Use first resolved event
                            except Exception as e:
                                logger.warning(f"Failed to resolve timing event {event_code} via CTS: {e}")
        
        # Also check for single event code in effective_time
        elif 'event_code' in fields:
            event_code = fields['event_code']
            event_system = fields.get('event_code_system', '2.16.840.1.113883.5.139')
            
            # Resolve timing event code
            if event_code:
                try:
                    event_display = self.terminology_service.resolve_code(event_code, event_system)
                    if event_display:
                        medication_data['frequency_display'] = event_display
                        medication_data['frequency_code'] = event_code
                        logger.info(f"CTS resolved timing event {event_code} to '{event_display}'")
                except Exception as e:
                    logger.warning(f"Failed to resolve timing event {event_code} via CTS: {e}")
        
        # Check for period-based frequency information
        if 'period' in fields:
            period_data = fields['period']
            if isinstance(period_data, dict):
                period_value = period_data.get('value')
                period_unit = period_data.get('unit')
                
                if period_value and period_unit:
                    medication_data['period'] = f"Every {period_value} {period_unit}"
                elif period_value:
                    medication_data['period'] = f"Every {period_value}"
            elif isinstance(period_data, str):
                medication_data['period'] = period_data
        
        # Also check for period_info from enhanced extraction
        if 'period_info' in fields:
            period_info = fields['period_info']
            if isinstance(period_info, dict):
                medication_data['period'] = period_info.get('period_display', '')
                medication_data['period_info'] = period_info
                logger.info(f"Using enhanced period info: {medication_data['period']}")

        # Set display_name for template compatibility (critical for frontend display)
        display_name = None
        
        # Priority 1: Use explicit medication name if available
        if medication_data.get('medication_name'):
            display_name = medication_data['medication_name']
        
        # Priority 2: Use substance/ingredient display name
        elif medication_data.get('ingredient_display'):
            display_name = medication_data['ingredient_display']
        
        # Priority 3: Use any name from fields
        elif fields.get('medication_name'):
            display_name = fields['medication_name']
        elif fields.get('substance_name'):
            display_name = fields['substance_name']
        
        # Priority 4: Build name from available components
        if not display_name:
            name_parts = []
            if medication_data.get('active_ingredient', {}).get('display_name'):
                name_parts.append(medication_data['active_ingredient']['display_name'])
            if medication_data.get('pharmaceutical_form'):
                name_parts.append(medication_data['pharmaceutical_form'])
            if name_parts:
                display_name = ' '.join(name_parts)
        
        # Final fallback
        if not display_name:
            display_name = "History of Medication use Narrative"
        
        medication_data['display_name'] = display_name
        medication_data['name'] = display_name  # Also set 'name' for backward compatibility
        
        # TEMPLATE COMPATIBILITY: Add active_ingredients (plural) for template compatibility
        # Templates expect item.active_ingredients.coded but we create item.active_ingredient.coded
        if 'active_ingredient' in medication_data and medication_data['active_ingredient'] is not None:
            medication_data['active_ingredients'] = [medication_data['active_ingredient']]  # Wrap in list for template
            # Safe access to active_ingredient data
            if isinstance(medication_data['active_ingredient'], dict):
                coded_value = medication_data['active_ingredient'].get('coded', 'N/A')
            else:
                coded_value = 'N/A'
            logger.info(f"Added active_ingredients for template compatibility: {coded_value}")
        
        # Handle medication status from statusCode or status_code
        status_source = fields.get('statusCode') or fields.get('status_code') or fields.get('status')
        if status_source:
            if isinstance(status_source, dict):
                status_code = status_source.get('code', '')
                if status_code:
                    medication_data['status'] = status_code
                    medication_data['status_display'] = status_code.title()
            elif isinstance(status_source, str):
                medication_data['status'] = status_source
                medication_data['status_display'] = status_source.title()
        
        # Handle medical reason from entryRelationship or medical_reason
        medical_reason_source = fields.get('entryRelationship') or fields.get('entry_relationship') or fields.get('medical_reason')
        if medical_reason_source:
            if isinstance(medical_reason_source, dict):
                # Look for observation data in entryRelationship
                if 'observation' in medical_reason_source:
                    obs_data = medical_reason_source['observation']
                    if isinstance(obs_data, dict):
                        if 'value' in obs_data:
                            value_data = obs_data['value']
                            if isinstance(value_data, dict):
                                medical_reason_display = value_data.get('displayName', '')
                                if medical_reason_display:
                                    medication_data['medical_reason'] = medical_reason_display
                                    medication_data['indication'] = medical_reason_display
                
                # Also check for direct display_text
                elif 'display_text' in medical_reason_source:
                    medication_data['medical_reason'] = medical_reason_source['display_text']
                    medication_data['indication'] = medical_reason_source['display_text']
            elif isinstance(medical_reason_source, str):
                medication_data['medical_reason'] = medical_reason_source
                medication_data['indication'] = medical_reason_source
        
        # Also check for medical_reason directly
        if 'medical_reason' in fields and isinstance(fields['medical_reason'], dict):
            reason_data = fields['medical_reason']
            if 'display_text' in reason_data:
                medication_data['medical_reason'] = reason_data['display_text']
                medication_data['indication'] = reason_data['display_text']
        
        # Include original fields for debugging/completeness
        medication_data['original_fields'] = fields
        
        return medication_data
    
    def _convert_cda_medication_to_enhanced_format(self, cda_medication: Dict[str, Any]) -> Dict[str, Any]:
        """Convert CDA parser medication format to enhanced format with schedule extraction"""
        medication_data = {'type': 'medication'}
        
        # Copy basic fields
        for field in ['class_code', 'mood_code', 'effective_time', 'dose', 'route', 'medication']:
            if field in cda_medication:
                medication_data[field] = cda_medication[field]
        
        # CRITICAL FIX: Map CDA field names to template field names
        # CDA XML uses 'doseQuantity', 'routeCode', 'statusCode' but template expects different names
        field_mappings = {
            'doseQuantity': 'dose_quantity',
            'routeCode': 'route_code',
            'statusCode': 'status_code',
            'entryRelationship': 'entry_relationship',
            'routeDisplay': 'route_display',
            'route_display': 'route_display',  # Keep existing mapping
        }
        
        # Apply CDA field mappings
        for cda_field, template_field in field_mappings.items():
            if cda_field in cda_medication:
                medication_data[template_field] = cda_medication[cda_field]
        
        # Extract period information from effective_time data
        if 'effective_time' in cda_medication:
            effective_time_data = cda_medication['effective_time']
            
            # Handle both single effective_time and list of effective_time elements
            time_elements = effective_time_data if isinstance(effective_time_data, list) else [effective_time_data]
            
            period_info = None
            for time_elem in time_elements:
                if isinstance(time_elem, dict):
                    # Check for period information in PIVL_TS
                    if 'period' in time_elem:
                        period_data = time_elem['period']
                        if isinstance(period_data, dict):
                            period_value = period_data.get('value')
                            period_unit = period_data.get('unit')
                            
                            if period_value and period_unit:
                                period_info = {
                                    'period_value': period_value,
                                    'period_unit': period_unit,
                                    'period_display': f"Period: {period_value} {period_unit}",
                                    'xsi_type': time_elem.get('xsi_type', ''),
                                    'operator': time_elem.get('operator', ''),
                                    'institution_specified': time_elem.get('institution_specified', '')
                                }
                                break  # Use first period found
            
            if period_info:
                medication_data['period_info'] = period_info
                medication_data['period'] = period_info['period_display']
                logger.info(f"Extracted period information: {period_info['period_display']}")
        
        # Extract event code information for frequency/schedule
        if 'event_code' in cda_medication:
            event_code = cda_medication['event_code']
            event_system = cda_medication.get('event_code_system', '2.16.840.1.113883.5.139')
            event_display = cda_medication.get('event_display_name', '')
            
            # Resolve event code using CTS
            if event_code and not event_display:
                try:
                    event_display = self.terminology_service.resolve_code(event_code, event_system)
                    if event_display:
                        logger.info(f"CTS resolved event code {event_code} to '{event_display}'")
                except Exception as e:
                    logger.warning(f"Failed to resolve event code {event_code} via CTS: {e}")
            
            # Create medication data structure with enhanced event information
            fields_for_conversion = {
                'event_code': event_code,
                'event_code_system': event_system
            }
            
            # Add route information if available
            if 'route' in cda_medication:
                route_data = cda_medication['route']
                if isinstance(route_data, dict):
                    fields_for_conversion['administration_route'] = route_data.get('code', '')
            
            # Add medication name if available
            if 'medication' in cda_medication:
                med_data = cda_medication['medication']
                if isinstance(med_data, dict):
                    fields_for_conversion['medication_name'] = med_data.get('name', '')
                    fields_for_conversion['substance_name'] = med_data.get('name', '')
            
            # Add dose quantity if available - ENHANCED EXTRACTION
            if 'dose' in cda_medication:
                dose_data = cda_medication['dose']
                if isinstance(dose_data, dict):
                    fields_for_conversion['dose_quantity'] = dose_data
            
            # CRITICAL: Extract dose quantity from doseQuantity CDA element if available
            if 'doseQuantity' in cda_medication:
                dose_quantity_data = cda_medication['doseQuantity']
                fields_for_conversion['dose_quantity'] = dose_quantity_data
                logger.info(f"Extracted doseQuantity from CDA: {dose_quantity_data}")
            
            # CRITICAL: Extract route information for event path
            if 'routeCode' in cda_medication:
                route_data = cda_medication['routeCode']
                fields_for_conversion['routeCode'] = route_data
                logger.info(f"Extracted routeCode from CDA (event): {route_data}")
            
            # CRITICAL: Extract status information for event path
            if 'statusCode' in cda_medication:
                status_data = cda_medication['statusCode']
                fields_for_conversion['statusCode'] = status_data
                logger.info(f"Extracted statusCode from CDA (event): {status_data}")
            
            # CRITICAL: Extract medical reason for event path
            if 'entryRelationship' in cda_medication:
                entry_rel_data = cda_medication['entryRelationship']
                fields_for_conversion['entryRelationship'] = entry_rel_data
                logger.info(f"Extracted entryRelationship from CDA (event): {type(entry_rel_data)}")
            
            # CRITICAL: Extract pharmaceutical form from CDA structure
            # Look for consumable/manufactured_product/manufactured_material/formCode
            if 'consumable' in cda_medication:
                consumable_data = cda_medication['consumable']
                fields_for_conversion['consumable'] = consumable_data
                logger.info(f"Extracted consumable data for pharmaceutical form parsing")
            
            # Also look for direct formCode field
            if 'formCode' in cda_medication:
                form_code_data = cda_medication['formCode']
                if isinstance(form_code_data, dict):
                    fields_for_conversion['pharmaceutical_form_code'] = form_code_data.get('code', '')
                    fields_for_conversion['pharmaceutical_form_code_system'] = form_code_data.get('codeSystem', '')
                    logger.info(f"Extracted formCode: {form_code_data.get('code', '')} (system: {form_code_data.get('codeSystem', '')})")
                else:
                    fields_for_conversion['pharmaceutical_form_code'] = form_code_data
            
            # Look for direct pharmaceutical_form field
            if 'pharmaceutical_form' in cda_medication:
                fields_for_conversion['pharmaceutical_form'] = cda_medication['pharmaceutical_form']
            
            # Add period information from enhanced extraction
            if 'period_info' in medication_data:
                fields_for_conversion['period_info'] = medication_data['period_info']
                logger.info(f"Including period info in conversion: {medication_data['period_info']['period_display']}")
            
            # Convert to enhanced data structure
            enhanced_data = self._convert_valueset_fields_to_medication_data(fields_for_conversion)
            
            # Merge enhanced data with original medication data
            medication_data['data'] = enhanced_data
            
            # CRITICAL: Ensure CDA fields are accessible in data structure for templates
            # Copy critical CDA fields from medication root to data structure
            cda_to_data_mappings = {
                'route_display': 'route_display',
                'dose_quantity': 'dose_quantity', 
                'status': 'status',
                'medical_reason': 'medical_reason',
                'pharmaceutical_form': 'pharmaceutical_form'
            }
            
            for cda_field, data_field in cda_to_data_mappings.items():
                if cda_field in enhanced_data:
                    medication_data['data'][data_field] = enhanced_data[cda_field]
                    logger.debug(f"Mapped {cda_field} to data.{data_field}: {enhanced_data[cda_field]}")
            
            logger.info(f"Enhanced medication data keys: {list(enhanced_data.keys())}")
            
            # Set display fields for template
            if event_display:
                medication_data['data']['frequency_display'] = event_display
                medication_data['data']['frequency_code'] = event_code
        else:
            # No event code - just create basic data structure but still extract all fields
            fields_for_conversion = {}
            
            # Add available fields
            if 'route' in cda_medication:
                route_data = cda_medication['route']
                if isinstance(route_data, dict):
                    fields_for_conversion['administration_route'] = route_data.get('code', '')
            
            if 'medication' in cda_medication:
                med_data = cda_medication['medication']
                if isinstance(med_data, dict):
                    fields_for_conversion['medication_name'] = med_data.get('name', '')
                    fields_for_conversion['substance_name'] = med_data.get('name', '')
            
            # CRITICAL: Extract dose quantity even without event code
            if 'dose' in cda_medication:
                dose_data = cda_medication['dose']
                if isinstance(dose_data, dict):
                    fields_for_conversion['dose_quantity'] = dose_data
            
            if 'doseQuantity' in cda_medication:
                dose_quantity_data = cda_medication['doseQuantity']
                fields_for_conversion['dose_quantity'] = dose_quantity_data
                logger.info(f"Extracted doseQuantity from CDA (no event): {dose_quantity_data}")
            
            # CRITICAL: Extract route information for no-event path
            if 'routeCode' in cda_medication:
                route_data = cda_medication['routeCode']
                fields_for_conversion['routeCode'] = route_data
                logger.info(f"Extracted routeCode from CDA (no event): {route_data}")
            
            # CRITICAL: Extract status information for no-event path
            if 'statusCode' in cda_medication:
                status_data = cda_medication['statusCode']
                fields_for_conversion['statusCode'] = status_data
                logger.info(f"Extracted statusCode from CDA (no event): {status_data}")
            
            # CRITICAL: Extract medical reason for no-event path
            if 'entryRelationship' in cda_medication:
                entry_rel_data = cda_medication['entryRelationship']
                fields_for_conversion['entryRelationship'] = entry_rel_data
                logger.info(f"Extracted entryRelationship from CDA (no event): {type(entry_rel_data)}")
            
            # CRITICAL: Extract pharmaceutical form even without event code
            if 'consumable' in cda_medication:
                consumable_data = cda_medication['consumable']
                fields_for_conversion['consumable'] = consumable_data
                logger.info(f"Extracted consumable data for pharmaceutical form parsing (no event)")
            
            if 'formCode' in cda_medication:
                form_code_data = cda_medication['formCode']
                if isinstance(form_code_data, dict):
                    fields_for_conversion['pharmaceutical_form_code'] = form_code_data.get('code', '')
                    fields_for_conversion['pharmaceutical_form_code_system'] = form_code_data.get('codeSystem', '')
                    logger.info(f"Extracted formCode (no event): {form_code_data.get('code', '')} (system: {form_code_data.get('codeSystem', '')})")
                else:
                    fields_for_conversion['pharmaceutical_form_code'] = form_code_data
            
            if 'pharmaceutical_form' in cda_medication:
                fields_for_conversion['pharmaceutical_form'] = cda_medication['pharmaceutical_form']
            
            # Convert to enhanced data structure
            enhanced_data = self._convert_valueset_fields_to_medication_data(fields_for_conversion)
            medication_data['data'] = enhanced_data
            
            # CRITICAL: Ensure CDA fields are accessible in data structure for templates (no event path)
            # Copy critical CDA fields from enhanced data to data structure
            cda_to_data_mappings = {
                'route_display': 'route_display',
                'dose_quantity': 'dose_quantity', 
                'pharmaceutical_form': 'pharmaceutical_form',
                'medical_reason': 'medical_reason'
            }
            
            for cda_field, data_field in cda_to_data_mappings.items():
                if cda_field in enhanced_data:
                    medication_data['data'][data_field] = enhanced_data[cda_field]
                    logger.debug(f"Mapped {cda_field} to data.{data_field} (no event): {enhanced_data[cda_field]}")
            
            logger.info(f"Enhanced medication data keys (no event): {list(enhanced_data.keys())}")
        
        # Extract display_name for template compatibility
        display_name = None
        
        # Priority 1: Use medication name from CDA
        if 'medication' in cda_medication and isinstance(cda_medication['medication'], dict):
            display_name = cda_medication['medication'].get('name', '').strip()
        
        # Priority 2: Use display_name from converted data
        if not display_name and 'data' in medication_data:
            display_name = medication_data['data'].get('display_name', '').strip()
        
        # Priority 3: Use ingredient display from converted data
        if not display_name and 'data' in medication_data:
            display_name = medication_data['data'].get('ingredient_display', '').strip()
        
        # Final fallback
        if not display_name:
            display_name = "History of Medication use Narrative"
        
        medication_data['display_name'] = display_name
        medication_data['name'] = display_name  # For template compatibility
        
        # CRITICAL FIX: Create active_ingredient if missing (fallback for template compatibility)
        if 'active_ingredient' not in medication_data and display_name:
            # Create basic active ingredient structure from medication name
            medication_data['active_ingredient'] = {
                'code': 'UNKNOWN',  # Will be resolved by CTS if possible
                'coded': 'UNKNOWN',  # Template expects this field
                'name': display_name,
                'display_name': display_name,
                'description': display_name
            }
            logger.info(f"Created fallback active_ingredient for medication: {display_name}")
        
        # ENHANCED TEMPLATE COMPATIBILITY: Add individual fields that template expects
        enhanced_data = medication_data.get('data', {})
        
        # Extract template fields from enhanced data
        if enhanced_data:
            # Pharmaceutical form
            form_value = enhanced_data.get('form') or enhanced_data.get('pharmaceutical_form', 'Not specified')
            if isinstance(form_value, dict):
                medication_data['pharmaceutical_form'] = form_value.get('display_name', form_value.get('code', 'Not specified'))
            else:
                medication_data['pharmaceutical_form'] = form_value
            
            # Dose quantity
            dose_value = enhanced_data.get('dose_quantity')
            if isinstance(dose_value, dict):
                # Handle CDA dose structure
                if 'value' in dose_value and 'unit' in dose_value:
                    medication_data['dose_quantity'] = f"{dose_value['value']} {dose_value['unit']}"
                else:
                    medication_data['dose_quantity'] = dose_value.get('display_value', 'Not specified')
            else:
                medication_data['dose_quantity'] = dose_value or 'Not specified'
            
            # Route
            route_value = enhanced_data.get('route') or enhanced_data.get('route_display', 'Not specified')
            if isinstance(route_value, dict):
                medication_data['route'] = route_value.get('display_name', route_value.get('code', 'Not specified'))
            else:
                medication_data['route'] = route_value
            
            # Schedule/frequency
            schedule_value = enhanced_data.get('frequency_display') or enhanced_data.get('frequency') or enhanced_data.get('schedule', 'Not specified')
            if isinstance(schedule_value, dict):
                medication_data['schedule'] = schedule_value.get('display_name', schedule_value.get('code', 'Not specified'))
            else:
                medication_data['schedule'] = schedule_value
        else:
            # Fallback values if no enhanced data
            medication_data['pharmaceutical_form'] = 'Not specified'
            medication_data['dose_quantity'] = 'Not specified'
            medication_data['route'] = 'Not specified'
            medication_data['schedule'] = 'Not specified'
        
        # TEMPLATE COMPATIBILITY: Add active_ingredients (plural) for template compatibility
        # Templates expect item.active_ingredients.coded but we create item.active_ingredient.coded
        if 'active_ingredient' in medication_data and medication_data['active_ingredient'] is not None:
            medication_data['active_ingredients'] = [medication_data['active_ingredient']]  # Wrap in list for template
            # Safe access to active_ingredient data
            if isinstance(medication_data['active_ingredient'], dict):
                coded_value = medication_data['active_ingredient'].get('coded', 'N/A')
            else:
                coded_value = 'N/A'
            logger.info(f"Added active_ingredients for template compatibility: {coded_value}")
        
        return medication_data

    def _fix_medication_template_compatibility(self, medications: List) -> None:
        """Fix medication object structure for template compatibility
        
        Template expects: med.route.coded, med.route.translated
        But service creates: med.route = {'code': 'xxx', 'displayName': 'yyy'}
        
        Need to convert dictionary structure to object-like structure or add missing keys
        """
        for medication in medications:
            if not medication:
                continue
                
            # Handle both dictionary and object-like medication structures
            self._fix_medication_attribute_compatibility(medication, 'route')
            self._fix_medication_attribute_compatibility(medication, 'pharmaceutical_form')
            self._fix_medication_attribute_compatibility(medication, 'active_ingredients')
            self._fix_medication_attribute_compatibility(medication, 'schedule')
            
            # Fix specific dosage and schedule fields for template compatibility
            self._fix_dosage_field_compatibility(medication)
            self._fix_schedule_field_compatibility(medication)
            
            logger.info(f"[TEMPLATE_COMPAT] Fixed medication template compatibility for: {getattr(medication, 'name', getattr(medication, 'medication_name', 'Unknown'))}")
    
    def _flatten_medication_data_structure(self, medications: List) -> None:
        """
        ARCHITECTURAL FIX: Flatten nested medication data structure for template compatibility
        
        Problem: Template expects med.medication_name but we have med.data.medication_name
        Solution: Lift all fields from med.data to med top level
        
        This makes clinical sections work like demographics (direct field access)
        """
        for medication in medications:
            if not medication or not isinstance(medication, dict):
                continue
                
            # If medication has nested 'data' structure, flatten it
            if 'data' in medication and isinstance(medication['data'], dict):
                med_data = medication['data']
                
                # List of fields to lift from data to top level
                fields_to_flatten = [
                    'medication_name', 'name', 'display_name',
                    'active_ingredients', 'strength', 
                    'pharmaceutical_form', 'dose_quantity', 'dose_value', 'dose_unit',
                    'route', 'route_display', 'administration_route', 'route_code',
                    'schedule', 'frequency', 'dosage_frequency', 'timing_code',
                    'start_date', 'end_date', 'period', 'treatment_period',
                    'ingredient_display', 'form_display'
                ]
                
                # Flatten each field
                for field in fields_to_flatten:
                    if field in med_data:
                        # Only flatten if not already at top level (avoid overwriting)
                        if field not in medication:
                            medication[field] = med_data[field]
                            logger.info(f"[FLATTEN] Lifted {field} from data to top level: {med_data[field]}")
                        else:
                            logger.info(f"[FLATTEN] Field {field} already exists at top level, keeping original")
                
                # Keep the original data structure for backwards compatibility
                logger.info(f"[FLATTEN] Flattened medication: {medication.get('medication_name', medication.get('name', 'Unknown'))}")
            else:
                logger.info(f"[FLATTEN] Medication already has flat structure: {medication.get('medication_name', medication.get('name', 'Unknown'))}")
    
    def _fix_medication_attribute_compatibility(self, medication, attribute_name: str) -> None:
        """Fix individual medication attribute for template compatibility"""
        try:
            # Import DotDict here to avoid circular imports
            from patient_data.services.enhanced_cda_xml_parser import DotDict
            
            # Check if medication has this attribute (object-style access)
            if hasattr(medication, attribute_name):
                attr_value = getattr(medication, attribute_name, None)
                
                if isinstance(attr_value, dict):
                    # Convert dictionary structure patterns to template-compatible format:
                    # Pattern 1: {'code': 'xxx', 'displayName': 'yyy'} -> add 'coded' and 'translated'
                    # Pattern 2: {'value': 'xxx', 'display_value': 'yyy'} -> add 'coded' and 'translated'
                    
                    # Handle code/displayName pattern
                    if 'code' in attr_value and 'coded' not in attr_value:
                        attr_value['coded'] = attr_value.get('code', '')
                        
                    if ('displayName' in attr_value or 'display_name' in attr_value) and 'translated' not in attr_value:
                        attr_value['translated'] = attr_value.get('displayName', attr_value.get('display_name', ''))
                    
                    # Handle value/display_value pattern (from CDA processor)
                    if 'value' in attr_value and 'coded' not in attr_value:
                        attr_value['coded'] = attr_value.get('value', '')
                        
                    if 'display_value' in attr_value and 'translated' not in attr_value:
                        attr_value['translated'] = attr_value.get('display_value', '')
                    
                    # CRITICAL FIX: Convert nested dictionary to DotDict for template dot notation access
                    if not isinstance(attr_value, DotDict):
                        dotdict_attr_value = DotDict(attr_value)
                        setattr(medication, attribute_name, dotdict_attr_value)
                        logger.info(f"[TEMPLATE_COMPAT] Converted {attribute_name} to DotDict for template access: {dotdict_attr_value}")
                    else:
                        logger.info(f"[TEMPLATE_COMPAT] Fixed {attribute_name} structure: {attr_value}")
                    
                elif isinstance(attr_value, str):
                    # Convert string to DotDict structure with coded/translated
                    new_attr_value = DotDict({
                        'coded': attr_value,
                        'translated': attr_value
                    })
                    setattr(medication, attribute_name, new_attr_value)
                    logger.info(f"[TEMPLATE_COMPAT] Converted {attribute_name} string to DotDict: {new_attr_value}")
            
            # CRITICAL: Also check dictionary-style access for CDA Parser medications
            elif isinstance(medication, dict) and attribute_name in medication:
                attr_value = medication[attribute_name]
                
                if isinstance(attr_value, dict):
                    # Convert dictionary structure patterns to template-compatible format:
                    # Pattern 1: {'code': 'xxx', 'displayName': 'yyy'} -> add 'coded' and 'translated'
                    # Pattern 2: {'value': 'xxx', 'display_value': 'yyy'} -> add 'coded' and 'translated'
                    
                    # Handle code/displayName pattern
                    if 'code' in attr_value and 'coded' not in attr_value:
                        attr_value['coded'] = attr_value.get('code', '')
                        
                    if ('displayName' in attr_value or 'display_name' in attr_value) and 'translated' not in attr_value:
                        attr_value['translated'] = attr_value.get('displayName', attr_value.get('display_name', ''))
                    
                    # Handle value/display_value pattern (from CDA processor)
                    if 'value' in attr_value and 'coded' not in attr_value:
                        attr_value['coded'] = attr_value.get('value', '')
                        
                    if 'display_value' in attr_value and 'translated' not in attr_value:
                        attr_value['translated'] = attr_value.get('display_value', '')
                    
                    # CRITICAL FIX: Convert nested dictionary to DotDict for template dot notation access
                    if not isinstance(attr_value, DotDict):
                        dotdict_attr_value = DotDict(attr_value)
                        medication[attribute_name] = dotdict_attr_value
                        logger.info(f"[TEMPLATE_COMPAT] Converted dict {attribute_name} to DotDict for template access: {dotdict_attr_value}")
                    else:
                        logger.info(f"[TEMPLATE_COMPAT] Fixed dict {attribute_name} structure: {attr_value}")
                    
                elif isinstance(attr_value, str):
                    # Convert string to DotDict structure with coded/translated
                    new_attr_value = DotDict({
                        'coded': attr_value,
                        'translated': attr_value
                    })
                    medication[attribute_name] = new_attr_value
                    logger.info(f"[TEMPLATE_COMPAT] Converted dict {attribute_name} string to DotDict: {new_attr_value}")
                    
            # Also check dictionary-style access for medications that might be dicts with 'data' key
            elif isinstance(medication, dict) and 'data' in medication:
                med_data = medication['data']
                if attribute_name in med_data:
                    attr_value = med_data[attribute_name]
                    
                    if isinstance(attr_value, dict):
                        # Handle code/displayName pattern
                        if 'code' in attr_value and 'coded' not in attr_value:
                            attr_value['coded'] = attr_value.get('code', '')
                            
                        if ('displayName' in attr_value or 'display_name' in attr_value) and 'translated' not in attr_value:
                            attr_value['translated'] = attr_value.get('displayName', attr_value.get('display_name', ''))
                        
                        # Handle value/display_value pattern (from CDA processor)
                        if 'value' in attr_value and 'coded' not in attr_value:
                            attr_value['coded'] = attr_value.get('value', '')
                            
                        if 'display_value' in attr_value and 'translated' not in attr_value:
                            attr_value['translated'] = attr_value.get('display_value', '')
                        
                        logger.info(f"[TEMPLATE_COMPAT] Fixed {attribute_name} in data structure: {attr_value}")
                        
        except Exception as e:
            logger.warning(f"[TEMPLATE_COMPAT] Error fixing {attribute_name}: {e}")
            pass

    def _calculate_medication_completeness_score(self, med: Dict) -> int:
        """Calculate a completeness score for a medication record to prioritize better data"""
        score = 0
        
        if isinstance(med, dict):
            # Base score for having a name
            if med.get('name') or med.get('medication_name') or med.get('display_name'):
                score += 10
            
            # Points for strength information (HIGH PRIORITY)
            strength = med.get('strength', '')
            if strength and strength not in ['Not specified', 'Not found', '']:
                score += 30  # Increased from 20 to prioritize actual strength data
                
            # Points for route information  
            route = med.get('route')
            if route:
                if isinstance(route, dict) and route.get('coded'):
                    score += 15
                elif isinstance(route, str) and route not in ['Not found', 'NO_ROUTE', '']:
                    score += 15
                    
            # Points for dose information
            dose_quantity = med.get('dose_quantity', '')
            if dose_quantity and dose_quantity not in ['Not found', '']:
                score += 10
                
            # Points for pharmaceutical form
            pharm_form = med.get('pharmaceutical_form')
            if pharm_form:
                if isinstance(pharm_form, dict) and pharm_form.get('coded'):
                    score += 10
                elif isinstance(pharm_form, str) and pharm_form:
                    score += 10
                    
            # Points for active ingredients
            ingredients = med.get('active_ingredients')
            if ingredients and ingredients not in ['Not found', 'Not specified']:
                score += 15
                
            # Points for start date
            start_date = med.get('start_date', '')
            if start_date and start_date not in ['Not found', '']:
                score += 5
                
            # Points for section information (Enhanced parser provides this)
            if med.get('section_code') or med.get('section_title'):
                score += 5
                
            # Modest bonus for Enhanced parser (but not if data quality is poor)
            if med.get('type') == 'enhanced_medication' or med.get('source') == 'enhanced_cda_parser':
                # Only give Enhanced parser bonus if it actually has strength data
                if strength and strength not in ['Not specified', 'Not found', '']:
                    score += 15  # Reduced from 25 and only if has actual strength
                else:
                    score += 5   # Small bonus for structure even without strength
                
        return score

    def _remove_duplicate_and_placeholder_data(self, clinical_arrays: Dict[str, List]) -> None:
        """Remove duplicate entries and placeholder data from clinical arrays"""
        
        # Remove placeholder medications if real medications exist
        # Enhanced CDA Parser medications are dictionaries without 'source' attribute
        # CDA Parser medications are objects that may have 'source' attribute set to 'section_fallback'
        real_medications = []
        placeholder_medications = []
        
        for m in clinical_arrays["medications"]:
            # Check if this is a placeholder medication
            is_placeholder = False
            if hasattr(m, "source") and getattr(m, "source", None) == "section_fallback":
                is_placeholder = True
            elif isinstance(m, dict) and m.get("source") == "section_fallback":
                is_placeholder = True
            
            if is_placeholder:
                placeholder_medications.append(m)
            else:
                real_medications.append(m)
        
        # Only remove placeholders if we have real medications
        if real_medications and placeholder_medications:
            clinical_arrays["medications"] = real_medications
            logger.info(f"[DATA_CLEANUP] Removed {len(placeholder_medications)} placeholder medications, kept {len(real_medications)} real medications")
        
        # Deduplicate problems by name/display_name to prevent repeating entries
        seen_problems = set()
        unique_problems = []
        for problem in clinical_arrays["problems"]:
            # Create a unique key from problem name/display
            problem_key = None
            if isinstance(problem, dict):
                if 'data' in problem and isinstance(problem['data'], dict):
                    # Handle enhanced format
                    problem_key = problem['data'].get('problem_name', problem['data'].get('display_name', ''))
                else:
                    # Handle direct format
                    problem_key = problem.get('problem_name', problem.get('display_name', problem.get('name', '')))
            
            if problem_key and problem_key not in seen_problems:
                seen_problems.add(problem_key)
                unique_problems.append(problem)
                
        if len(unique_problems) != len(clinical_arrays["problems"]):
            logger.info(f"[DATA_CLEANUP] Deduplicated problems: {len(clinical_arrays['problems'])} -> {len(unique_problems)}")
            clinical_arrays["problems"] = unique_problems

        # CRITICAL FIX: Deduplicate medications by name/substance, prioritizing most complete records
        medication_groups = {}  # Group medications by name
        
        for med in clinical_arrays["medications"]:
            # Create a unique key from medication name/substance
            med_key = None
            if isinstance(med, dict):
                if 'data' in med and isinstance(med['data'], dict):
                    # Handle enhanced format
                    med_data = med['data']
                    med_key = (med_data.get('medication_name') or 
                              med_data.get('substance_name') or 
                              med_data.get('display_name', '')).strip().lower()
                else:
                    # Handle direct format AND Enhanced CDA Parser format
                    med_key = (med.get('medication_name') or 
                              med.get('substance_name') or 
                              med.get('display_name') or 
                              med.get('name', '')).strip().lower()
            
            if med_key:
                if med_key not in medication_groups:
                    medication_groups[med_key] = []
                medication_groups[med_key].append(med)
            else:
                logger.info(f"[DATA_CLEANUP] Removed medication entry with no name: {med}")
        
        # Select the most complete medication from each group
        unique_medications = []
        for med_key, med_list in medication_groups.items():
            if len(med_list) == 1:
                unique_medications.append(med_list[0])
            else:
                # Score each medication by completeness and select the best one
                best_med = None
                best_score = -1
                
                # Debug logging for Triapin specifically
                is_triapin = 'triapin' in med_key.lower()
                
                for i, med in enumerate(med_list):
                    score = self._calculate_medication_completeness_score(med)
                    if is_triapin:
                        logger.info(f"TRIAPIN DEDUP DEBUG: Entry {i+1}: score={score}, strength='{med.get('strength', 'None')}', source='{med.get('source', 'None')}', type='{med.get('type', 'None')}'")
                    
                    if score > best_score:
                        best_score = score
                        best_med = med
                
                if is_triapin:
                    logger.info(f"TRIAPIN DEDUP RESULT: Kept entry with score {best_score}")
                
                unique_medications.append(best_med)
                logger.info(f"[DATA_CLEANUP] Deduplicated {len(med_list)} entries for '{med_key}', kept most complete (score: {best_score})")
                
        if len(unique_medications) != len(clinical_arrays["medications"]):
            logger.info(f"[DATA_CLEANUP] CRITICAL: Deduplicated medications: {len(clinical_arrays['medications'])} -> {len(unique_medications)}")
            clinical_arrays["medications"] = unique_medications
        else:
            # Still remove invalid entries even if no deduplication needed
            valid_medications = []
            for med in clinical_arrays["medications"]:
                # Check if medication has meaningful data
                has_name = False
                if isinstance(med, dict):
                    if 'data' in med and isinstance(med['data'], dict):
                        med_data = med['data']
                        has_name = bool(med_data.get('medication_name') or med_data.get('substance_name') or med_data.get('display_name'))
                    else:
                        # CRITICAL FIX: Include Enhanced CDA Parser 'name' field in validation
                        has_name = bool(med.get('medication_name') or med.get('substance_name') or med.get('display_name') or med.get('name'))
                
                if has_name:
                    valid_medications.append(med)
                else:
                    logger.info(f"[DATA_CLEANUP] Removed invalid medication entry: {med}")
                    
            clinical_arrays["medications"] = valid_medications

    def _extract_enhanced_problems(self, raw_problems: List[Dict]) -> List[Dict]:
        """Extract rich clinical problem data from CDA parser results"""
        enhanced_problems = []
        
        try:
            for problem_entry in raw_problems:
                # Check if this is a problem act with detailed problems
                if problem_entry.get("type") == "problem_act" and "problems" in problem_entry:
                    # Get the nested problems for this act
                    nested_problems = problem_entry["problems"]
                    
                    if nested_problems:
                        # Take the first nested problem as the primary problem
                        # (all observations in this act represent the same clinical problem)
                        primary_problem = nested_problems[0]
                        enhanced_problem = self._format_problem_for_display(primary_problem, problem_entry)
                        
                        # Merge any additional clinical details from other observations
                        for additional_problem in nested_problems[1:]:
                            self._merge_additional_problem_details(enhanced_problem, additional_problem)
                        
                        if enhanced_problem:
                            enhanced_problems.append(enhanced_problem)
                else:
                    # Handle legacy problem format
                    enhanced_problem = self._format_legacy_problem_for_display(problem_entry)
                    if enhanced_problem:
                        enhanced_problems.append(enhanced_problem)
                        
        except Exception as e:
            logger.warning(f"Error extracting enhanced problems: {e}")
            # Return original problems on error
            return raw_problems
            
        return enhanced_problems if enhanced_problems else raw_problems

    def _merge_additional_problem_details(self, enhanced_problem: Dict, additional_problem: Dict) -> None:
        """Merge additional clinical details from secondary observations into the primary problem"""
        try:
            # Merge status details if not already present
            if not enhanced_problem.get("status") and "status_detail" in additional_problem:
                status_detail = additional_problem["status_detail"]
                enhanced_problem["status"] = status_detail.get("displayName", status_detail.get("code", ""))
            
            # Merge severity if not already present
            if not enhanced_problem.get("severity") and "severity" in additional_problem:
                enhanced_problem["severity"] = additional_problem["severity"]
            
            # Merge additional effective time information if needed
            if "effective_time" in additional_problem and not enhanced_problem.get("resolution"):
                additional_time = additional_problem["effective_time"]
                if "high_formatted" in additional_time:
                    enhanced_problem["resolution"] = additional_time["high_formatted"]
                    
        except Exception as e:
            logger.warning(f"Error merging additional problem details: {e}")

    def _format_problem_for_display(self, problem_detail: Dict, problem_act: Dict) -> Dict:
        """Format detailed problem data for clinical display"""
        try:
            formatted_problem = {}
            
            # Enhanced name extraction with multiple fallback strategies
            display_name = ""
            
            # Strategy 1: Try direct displayName from problem detail (CTS resolved)
            if "displayName" in problem_detail:
                display_name = str(problem_detail["displayName"]).strip()
            
            # Strategy 2: Try nested problem info structure
            if not display_name:
                problem_info = problem_detail.get("problem", {})
                code_info = problem_info.get("code", {})
                display_name = code_info.get("displayName", "").strip()
                
                # If displayName is empty, try other sources
                if not display_name:
                    # Try the 'name' field from problem_info
                    display_name = problem_info.get("name", "").strip()
            
            # Strategy 3: Try direct name field from problem detail
            if not display_name and "name" in problem_detail:
                display_name = str(problem_detail["name"]).strip()
            
            # Strategy 4: Try problem code resolution (should be already resolved by CTS)
            if not display_name:
                problem_info = problem_detail.get("problem", {})
                code_info = problem_info.get("code", {})
                if code_info.get("code"):
                    display_name = code_info.get("code", "").strip()
            
            # Strategy 5: Final fallback only if we have no other information
            if not display_name:
                display_name = "Medical Problem"
                logger.warning(f"Problem extraction falling back to generic name for problem_detail: {list(problem_detail.keys())}")
            
            formatted_problem["name"] = display_name
            formatted_problem["display_name"] = display_name  # For template consistency
            formatted_problem["code"] = code_info.get("code", "")
            formatted_problem["code_system"] = code_info.get("codeSystemName", "")
            
            # Extract problem type from the observation code element
            problem_type_info = problem_detail.get("problem_type", {})
            if problem_type_info and problem_type_info.get("displayName"):
                formatted_problem["type"] = problem_type_info["displayName"]
                formatted_problem["type_code"] = problem_type_info.get("code", "")
                formatted_problem["type_code_system"] = problem_type_info.get("codeSystem", "")
            else:
                # Set problem type based on clinical context (fallback)
                formatted_problem["type"] = "Active Problem"
                if problem_detail.get("effective_time", {}).get("high_formatted"):
                    formatted_problem["type"] = "Resolved Problem"
            
            # Extract effective time for display
            effective_time = problem_detail.get("effective_time", {})
            if effective_time:
                if "low_formatted" in effective_time:
                    formatted_problem["onset"] = effective_time["low_formatted"]
                elif "formatted" in effective_time:
                    formatted_problem["onset"] = effective_time["formatted"]
                    
                if "high_formatted" in effective_time:
                    formatted_problem["resolution"] = effective_time["high_formatted"]
            
            # Extract status information
            status_detail = problem_detail.get("status_detail", {})
            if status_detail:
                formatted_problem["status"] = status_detail.get("displayName", status_detail.get("code", ""))
            else:
                # Fallback to main act status
                formatted_problem["status"] = problem_act.get("status", "active")
            
            # Extract severity
            severity = problem_detail.get("severity", "")
            if severity:
                formatted_problem["severity"] = severity
            
            # Format time for display
            if formatted_problem.get("onset"):
                formatted_problem["time_display"] = formatted_problem["onset"]
                if formatted_problem.get("resolution"):
                    formatted_problem["time_display"] += f" - {formatted_problem['resolution']}"
            
            return formatted_problem
            
        except Exception as e:
            logger.warning(f"Error formatting problem for display: {e}")
            return {}

    def _format_legacy_problem_for_display(self, problem_entry: Dict) -> Dict:
        """Format legacy problem entry for display"""
        try:
            # Enhanced name extraction for legacy format
            display_name = ""
            
            # Strategy 1: Try display_name field (CTS resolved)
            if "display_name" in problem_entry:
                display_name = str(problem_entry["display_name"]).strip()
            
            # Strategy 2: Try name field
            if not display_name and "name" in problem_entry:
                display_name = str(problem_entry["name"]).strip()
            
            # Strategy 3: Try displayName field
            if not display_name and "displayName" in problem_entry:
                display_name = str(problem_entry["displayName"]).strip()
            
            # Strategy 4: Check if there's nested code info
            if not display_name and "code_info" in problem_entry:
                code_info = problem_entry["code_info"]
                if isinstance(code_info, dict):
                    display_name = code_info.get("displayName", "").strip()
            
            # Strategy 5: Check the code field directly (CTS resolved)
            if not display_name and "code" in problem_entry:
                code_data = problem_entry["code"]
                if isinstance(code_data, dict):
                    # Try displayName from code dictionary (CTS resolved)
                    display_name = code_data.get("displayName", "").strip()
                    # Try name from code dictionary
                    if not display_name:
                        display_name = code_data.get("name", "").strip()
                    
                    # If displayName is still empty, try CTS resolution
                    if not display_name and code_data.get("code") and code_data.get("codeSystem"):
                        try:
                            from translation_services.terminology_translator import TerminologyTranslator
                            translator = TerminologyTranslator()
                            resolved_name = translator.resolve_code(
                                code_data.get("code"),
                                code_data.get("codeSystem")
                            )
                            if resolved_name and resolved_name.strip():
                                display_name = resolved_name.strip()
                                logger.info(f"CTS resolved problem code {code_data.get('code')} to '{display_name}'")
                        except Exception as e:
                            logger.warning(f"CTS resolution failed for problem code {code_data.get('code')}: {e}")
            
            # Final fallback
            if not display_name:
                display_name = "Medical Problem"
                # Show more detailed info for debugging
                code_data = problem_entry.get("code", {})
                if isinstance(code_data, dict):
                    logger.warning(f"Legacy problem extraction falling back to generic name. Problem keys: {list(problem_entry.keys())}, Code keys: {list(code_data.keys())}")
                else:
                    logger.warning(f"Legacy problem extraction falling back to generic name for problem_entry: {list(problem_entry.keys())}")
            
            formatted_problem = {
                "name": display_name,
                "display_name": display_name,  # For template consistency
                "type": problem_entry.get("type", "Clinical finding"),
                "status": problem_entry.get("status", "active"),
                "code": problem_entry.get("code", ""),
                "source": problem_entry.get("source", "cda_parser")
            }
            
            # Extract time if available
            if "effective_time" in problem_entry:
                time_info = problem_entry["effective_time"]
                if isinstance(time_info, dict) and "formatted" in time_info:
                    formatted_problem["time_display"] = time_info["formatted"]
                elif isinstance(time_info, str):
                    formatted_problem["time_display"] = time_info
            
            return formatted_problem
            
        except Exception as e:
            logger.warning(f"Error formatting legacy problem: {e}")
            return {}

    def _fix_dosage_field_compatibility(self, medication) -> None:
        """Fix dosage field compatibility for template access"""
        try:
            # Create dose_quantity from doseQuantity if it exists
            dose_quantity_data = None
            if hasattr(medication, 'doseQuantity'):
                dose_quantity_data = getattr(medication, 'doseQuantity', None)
            elif isinstance(medication, dict) and 'doseQuantity' in medication:
                dose_quantity_data = medication.get('doseQuantity')
                
            if dose_quantity_data:
                # Handle complex doseQuantity structures
                if isinstance(dose_quantity_data, dict):
                    if 'low' in dose_quantity_data and 'high' in dose_quantity_data:
                        # Range: e.g., 1-2 tablets
                        low_val = dose_quantity_data['low'].get('value', '')
                        high_val = dose_quantity_data['high'].get('value', '')
                        unit = dose_quantity_data['low'].get('unit', dose_quantity_data['high'].get('unit', ''))
                        dose_display = f"{low_val}-{high_val} {unit}".strip()
                    elif 'value' in dose_quantity_data:
                        # Single value
                        value = dose_quantity_data.get('value', '')
                        unit = dose_quantity_data.get('unit', '')
                        dose_display = f"{value} {unit}".strip()
                    else:
                        dose_display = str(dose_quantity_data)
                else:
                    dose_display = str(dose_quantity_data)
                
                # Set dose_quantity for template access
                if hasattr(medication, '__setattr__'):
                    setattr(medication, 'dose_quantity', dose_display)
                elif isinstance(medication, dict):
                    medication['dose_quantity'] = dose_display
                
                logger.info(f"[DOSAGE_COMPAT] Created dose_quantity: {dose_display}")
                        
        except Exception as e:
            logger.warning(f"Error fixing dosage field compatibility: {e}")

    def _fix_schedule_field_compatibility(self, medication) -> None:
        """Fix schedule field compatibility for template access"""
        try:
            # Import DotDict here to avoid circular imports
            from patient_data.services.enhanced_cda_xml_parser import DotDict
            
            # Create schedule from event_code or effective_time if it exists
            schedule_display = None
            
            # Try event_code first (common for frequency)
            if hasattr(medication, 'event_code'):
                event_code = getattr(medication, 'event_code', None)
            elif isinstance(medication, dict) and 'event_code' in medication:
                event_code = medication.get('event_code')
            else:
                event_code = None
                
            if event_code:
                # Map common event codes to readable schedule
                if event_code == 'ACM':
                    schedule_display = 'Before breakfast'
                else:
                    schedule_display = event_code
                    
            # If no schedule found, try to extract from effective_time
            if not schedule_display:
                effective_time = None
                if hasattr(medication, 'effective_time'):
                    effective_time = getattr(medication, 'effective_time', None)
                elif isinstance(medication, dict) and 'effective_time' in medication:
                    effective_time = medication.get('effective_time')
                    
                if effective_time and isinstance(effective_time, list):
                    for time_entry in effective_time:
                        if isinstance(time_entry, dict) and 'event_code' in time_entry:
                            event_code = time_entry['event_code']
                            if event_code == 'ACM':
                                schedule_display = 'Before breakfast'
                            else:
                                schedule_display = event_code
                            break
            
            # Set schedule for template access if found
            if schedule_display:
                schedule_obj = DotDict({
                    'coded': schedule_display,
                    'translated': schedule_display
                })
                
                if hasattr(medication, '__setattr__'):
                    setattr(medication, 'schedule', schedule_obj)
                elif isinstance(medication, dict):
                    medication['schedule'] = schedule_obj
                
                logger.info(f"[SCHEDULE_COMPAT] Created schedule: {schedule_display}")
                        
        except Exception as e:
            logger.warning(f"Error fixing schedule field compatibility: {e}")
