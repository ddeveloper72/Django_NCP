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
from translation_services.terminology_translator import TerminologyTranslator

logger = logging.getLogger(__name__)


class ComprehensiveClinicalDataService:
    """Extract and analyze clinical data from CDA documents using multiple parsing strategies"""

    def __init__(self):
        self.enhanced_parser = EnhancedCDAXMLParser()
        self.ps_renderer = PSTableRenderer()
        self.cda_parser = CDAParserService()
        self.structured_extractor = StructuredCDAExtractor()
        self.terminology_service = TerminologyTranslator()

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
                and "clinical_sections" in cda_content_or_comprehensive_data
            ):
                comprehensive_data = cda_content_or_comprehensive_data
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

            # Enhanced parser sections for rich clinical data (priority for medications)
            enhanced_data = comprehensive_data.get("clinical_sections", {}).get(
                "enhanced_parser", {}
            )
            sections_found = enhanced_data.get("sections_found", [])
            
            # Extract rich clinical data from enhanced parser sections first
            enhanced_medications_found = False
            for section in sections_found:
                if "structured_data" in section:
                    for entry in section["structured_data"]:
                        entry_data = entry.get("data", {})
                        section_type = entry.get("section_type", "")
                        entry_type = entry.get("type", "")
                        
                        # Handle different entry types from enhanced parser
                        if entry_type == "valueset_entry":
                            # For valueset entries, the data is in "fields"
                            entry_fields = entry.get("fields", {})
                            if section_type == "medication" and entry_fields:
                                # Convert fields to data structure for template compatibility
                                medication_data = self._convert_valueset_fields_to_medication_data(entry_fields)
                                clinical_arrays["medications"].append(medication_data)
                                enhanced_medications_found = True
                        elif section_type == "medication" and entry_data:
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
                clinical_arrays["problems"].extend(structured.get("problems", []))
                clinical_arrays["procedures"].extend(structured.get("procedures", []))
                clinical_arrays["vital_signs"].extend(structured.get("vital_signs", []))
                clinical_arrays["results"].extend(structured.get("results", []))
                clinical_arrays["immunizations"].extend(
                    structured.get("immunizations", [])
                )

                logger.info(
                    f"[CLINICAL ARRAYS] Enhanced parser: med={len([m for m in clinical_arrays['medications'] if enhanced_medications_found])}, CDA Parser: med={len([m for m in clinical_arrays['medications'] if not enhanced_medications_found])}, all={len(clinical_arrays['allergies'])}, prob={len(clinical_arrays['problems'])}"
                )

            # If we have fewer items from both CDA parser and enhanced parser but sections exist, use section count as fallback
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
        if 'administration_route' in fields:
            route_data = fields['administration_route']
            
            # Handle both simple codes and complex route structures
            route_code = None
            route_display = None
            
            if isinstance(route_data, dict):
                route_code = route_data.get('code')
                route_display = route_data.get('display_name') or route_data.get('display')
            elif isinstance(route_data, str) and route_data.isdigit():
                route_code = route_data
            
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
                # Also set for template compatibility
                medication_data['route_display'] = route_display
            elif route_code:
                medication_data['route'] = {
                    'code': route_code,
                    'display_name': route_code  # Fallback to code if no display found
                }
        
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
            ingredient_display = fields.get('active_ingredient_display') or fields.get('active_ingredient_name')
            
            # Use CTS to resolve ingredient code
            if ingredient_code and not ingredient_display:
                try:
                    ingredient_display = self.terminology_service.resolve_code(ingredient_code)
                    if ingredient_display:
                        logger.info(f"CTS resolved active ingredient code {ingredient_code} to '{ingredient_display}'")
                except Exception as e:
                    logger.warning(f"Failed to resolve active ingredient code {ingredient_code} via CTS: {e}")
            
            # Set ingredient data
            if ingredient_display:
                medication_data['ingredient_display'] = ingredient_display
                medication_data['ingredient_code'] = ingredient_code
                medication_data['active_ingredient'] = {
                    'code': ingredient_code,
                    'display_name': ingredient_display
                }
            elif ingredient_code:
                medication_data['ingredient_code'] = ingredient_code
        
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
                                
                                if ingredient_code:
                                    try:
                                        ingredient_display = self.terminology_service.resolve_code(ingredient_code)
                                        if ingredient_display:
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
                                            ingredient_codes.append(ingredient_code)
                                            
                                            if not primary_ingredient:
                                                primary_ingredient = {
                                                    'code': ingredient_code,
                                                    'display_name': ingredient_display,
                                                    'strength': strength_info.strip()
                                                }
                                            
                                            logger.info(f"CTS resolved active ingredient code {ingredient_code} to '{ingredient_display}'{strength_info}")
                                    except Exception as e:
                                        logger.warning(f"Failed to resolve active ingredient code {ingredient_code}: {e}")
                                        ingredient_codes.append(ingredient_code)
                        
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
                        if ingredient_code:
                            try:
                                ingredient_display = self.terminology_service.resolve_code(ingredient_code)
                                if ingredient_display:
                                    medication_data['ingredient_display'] = ingredient_display
                                    medication_data['ingredient_code'] = ingredient_code
                                    medication_data['active_ingredient'] = {
                                        'code': ingredient_code,
                                        'display_name': ingredient_display
                                    }
                                    logger.info(f"CTS resolved active ingredient code {ingredient_code} to '{ingredient_display}'")
                            except Exception as e:
                                logger.warning(f"Failed to resolve active ingredient code {ingredient_code}: {e}")
                                medication_data['ingredient_code'] = ingredient_code
                        
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
        if 'dose_quantity' in fields:
            dose_data = fields['dose_quantity']
            if isinstance(dose_data, dict):
                # Handle range format with low/high values
                low_value = dose_data.get('low', {}).get('value') if isinstance(dose_data.get('low'), dict) else dose_data.get('low')
                high_value = dose_data.get('high', {}).get('value') if isinstance(dose_data.get('high'), dict) else dose_data.get('high')
                
                if low_value and high_value:
                    medication_data['dose_quantity'] = f"{low_value}-{high_value}"
                elif low_value:
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
            medication_data['data'] = self._convert_valueset_fields_to_medication_data(fields_for_conversion)
        
        return medication_data
