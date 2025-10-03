"""
CDA Data Extraction Helper Service

This service acts as a bridge between the Clinical Data Extraction Debugger
and the CDA display view, providing structured data extraction while keeping
the view function simple and focused.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from .clinical_data_debugger import ClinicalDataExtractor
from .services.enhanced_cda_xml_parser import EnhancedCDAXMLParser
from .services.structured_cda_extractor import StructuredCDAExtractor

logger = logging.getLogger(__name__)


class CDADisplayDataHelper:
    """
    Helper service that extracts structured CDA data for display views
    Leverages the Clinical Data Extraction Debugger's proven methods
    """

    def __init__(self):
        try:
            self.clinical_extractor = ClinicalDataExtractor()
            logger.info("[SUCCESS] ClinicalDataExtractor initialized successfully")
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize ClinicalDataExtractor: {e}")
            self.clinical_extractor = None

        try:
            self.enhanced_parser = EnhancedCDAXMLParser()
            logger.info("[SUCCESS] EnhancedCDAXMLParser initialized successfully")
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize EnhancedCDAXMLParser: {e}")
            self.enhanced_parser = None

        try:
            self.structured_extractor = StructuredCDAExtractor()
            logger.info("[SUCCESS] StructuredCDAExtractor initialized successfully")
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize StructuredCDAExtractor: {e}")
            self.structured_extractor = None

    def extract_display_data(
        self, cda_content: str, session_data: dict = None
    ) -> Dict[str, Any]:
        """
        Extract comprehensive data for CDA display views

        Args:
            cda_content: Raw CDA XML content
            session_data: Optional session context data

        Returns:
            Dictionary with structured data ready for template display
        """
        try:
            logger.info("[INFO] Starting CDA data extraction for display...")

            if not self.clinical_extractor:
                logger.error("[ERROR] ClinicalDataExtractor not available")
                return self._get_empty_display_data(
                    error="ClinicalDataExtractor not initialized"
                )

            # Use the proven clinical data extractor
            extraction_result = (
                self.clinical_extractor.extract_comprehensive_clinical_data(
                    cda_content, session_data
                )
            )

            # Transform the extraction result into display-ready format
            display_data = self._transform_to_display_format(extraction_result)

            logger.info("[SUCCESS] CDA display data extraction completed successfully")
            return display_data

        except Exception as e:
            logger.error(f"[ERROR] CDA display data extraction failed: {e}")
            return self._get_empty_display_data(error=str(e))

    def extract_extended_patient_data(
        self, cda_content: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract extended patient information (administrative data) from CDA

        Args:
            cda_content: Raw CDA XML content

        Returns:
            Extended patient data dictionary or None
        """
        try:
            if not self.enhanced_parser:
                logger.error("[ERROR] EnhancedCDAXMLParser not available")
                return None

            # Use enhanced parser to extract administrative data
            parsed_data = self.enhanced_parser.parse_cda_content(cda_content)

            # Extract administrative data section
            admin_data = parsed_data.get("administrative_data", {})
            patient_identity = parsed_data.get("patient_identity", {})

            if not admin_data and not patient_identity:
                logger.warning("No administrative/extended patient data found in CDA")
                return None

            # Structure extended patient data for template display with STANDARDIZED context keys
            extended_data = {
                "patient_extended_data": {
                    "patient_identity_extended": patient_identity,
                    "document_metadata": parsed_data.get("document_metadata", {}),
                },
                "administrative_data": admin_data,
                "contact_data": self._extract_contact_information_standardized(
                    admin_data
                ),
                "healthcare_data": self._extract_healthcare_providers_standardized(
                    admin_data
                ),
                "document_details": self._extract_document_details(admin_data),
            }

            logger.info("SUCCESS: Extended patient data extracted successfully")
            return extended_data

        except Exception as e:
            logger.error(f"ERROR: Extended patient data extraction failed: {e}")
            return None

    def extract_clinical_sections(self, cda_content: str) -> List[Dict[str, Any]]:
        """
        Extract clinical sections in a format ready for template display

        Args:
            cda_content: Raw CDA XML content

        Returns:
            List of clinical sections with structured data
        """
        try:
            # Use structured extractor for rich hierarchical data
            structured_data = self.structured_extractor.extract_structured_entries(
                cda_content
            )

            if not structured_data:
                logger.warning("No structured clinical data extracted")
                return []

            # ENHANCED: Import Enhanced CDA Processor for 9-column allergies
            try:
                from .services.enhanced_cda_processor import EnhancedCDAProcessor
                enhanced_processor = EnhancedCDAProcessor(target_language='en', country_code='PT')
                logger.info("[ENHANCED CDA HELPER] Enhanced CDA Processor initialized for allergies")
            except Exception as e:
                logger.warning(f"[ENHANCED CDA HELPER] Could not initialize Enhanced CDA Processor: {e}")
                enhanced_processor = None

            # Transform to display format
            clinical_sections = []
            
            # structured_data is a Dict[str, List[StructuredClinicalEntry]]
            for section_name, entries_list in structured_data.items():
                if not entries_list:  # Skip empty sections
                    continue
                    
                display_section = {
                    "section_id": section_name,
                    "display_name": section_name.replace("_", " ").title(),
                    "narrative_text": "",
                    "entries": entries_list,
                    "clinical_codes": [],
                    "is_coded_section": len(entries_list) > 0,
                    "entry_count": len(entries_list),
                    "coding_systems": [],
                }

                # ENHANCED: Check if this is an allergies section and apply Enhanced CDA Processor
                section_title = display_section.get("display_name", "").lower()
                logger.info(f"[ENHANCED CDA HELPER DEBUG] Section title: '{section_title}' (from {section_name})")
                
                is_allergies_section = (
                    section_name == "allergies" or 
                    any(keyword in section_title for keyword in ["allerg", "adverse", "reaction", "intolerance"])
                )
                
                logger.info(f"[ENHANCED CDA HELPER DEBUG] Is allergies section: {is_allergies_section}")
                logger.info(f"[ENHANCED CDA HELPER DEBUG] Enhanced processor available: {enhanced_processor is not None}")
                logger.info(f"[ENHANCED CDA HELPER DEBUG] CDA content available: {cda_content is not None}")

                if is_allergies_section and enhanced_processor and cda_content:
                    logger.info(f"[ENHANCED CDA HELPER] Processing allergies section: {display_section.get('display_name')}")
                    
                    try:
                        # Extract allergies using Enhanced CDA Processor
                        import xml.etree.ElementTree as ET
                        root = ET.fromstring(cda_content)
                        
                        # Find allergies section (code 48765-2) using manual filtering
                        all_sections = root.findall(".//{urn:hl7-org:v3}section")
                        allergies_sections = []
                        
                        for section in all_sections:
                            code_elem = section.find('{urn:hl7-org:v3}code')
                            if code_elem is not None and code_elem.get('code') == '48765-2':
                                allergies_sections.append(section)
                        
                        if allergies_sections:
                            # Define namespaces for entry processing
                            namespaces = {
                                'hl7': 'urn:hl7-org:v3',
                                'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
                            }
                            
                            enhanced_allergies = []
                            for section in allergies_sections:
                                # Extract entries from allergies section
                                entries = section.findall("{urn:hl7-org:v3}entry")
                                
                                for entry in entries:
                                    # Find observation within entry (handle nested structure)
                                    # First try direct observation
                                    observation = entry.find("{urn:hl7-org:v3}observation")
                                    
                                    # If not found directly, look for nested observations (Mario Pino structure)
                                    if observation is None:
                                        # Look for: entry > act > entryRelationship > observation
                                        act = entry.find("{urn:hl7-org:v3}act")
                                        if act is not None:
                                            entryrel = act.find("{urn:hl7-org:v3}entryRelationship")
                                            if entryrel is not None:
                                                observation = entryrel.find("{urn:hl7-org:v3}observation")
                                    
                                    # If still not found, try finding any nested observation
                                    if observation is None:
                                        observation = entry.find(".//{urn:hl7-org:v3}observation")
                                    
                                    if observation is not None:
                                        logger.info(f"[ENHANCED CDA HELPER] Found observation in entry - extracting data")
                                        # Extract observation data for each allergy
                                        obs_data = enhanced_processor._extract_observation_data(observation, namespaces)
                                        if obs_data:
                                            logger.info(f"[ENHANCED CDA HELPER] Successfully extracted observation data: {list(obs_data.keys())}")
                                            enhanced_allergies.append(obs_data)
                                        else:
                                            logger.warning(f"[ENHANCED CDA HELPER] Observation data extraction returned empty")
                                    else:
                                        logger.warning(f"[ENHANCED CDA HELPER] No observation found in entry")

                            if enhanced_allergies:
                                logger.info(f"[ENHANCED CDA HELPER] Found {len(enhanced_allergies)} enhanced allergies")
                                
                                # Create 9-column clinical table structure for allergies
                                display_section["clinical_table"] = {
                                    "headers": [
                                        {"key": "code", "label": "Code", "type": "code"},
                                        {"key": "reaction_type", "label": "Reaction Type", "primary": True, "type": "reaction"},
                                        {"key": "manifestation", "label": "Clinical Manifestation", "type": "reaction"},
                                        {"key": "agent", "label": "Agent", "type": "allergen"},
                                        {"key": "time", "label": "Time", "type": "date"},
                                        {"key": "severity", "label": "Severity", "type": "severity"},
                                        {"key": "criticality", "label": "Criticality", "type": "severity"},
                                        {"key": "status", "label": "Status", "type": "status"},
                                        {"key": "certainty", "label": "Certainty", "type": "status"},
                                    ],
                                    "rows": []
                                }

                                # Convert enhanced allergies to clinical table rows
                                for allergy in enhanced_allergies:
                                    # Map Enhanced CDA Processor field names to clinical table format
                                    row = {
                                        "data": {
                                            "code": {"value": allergy.get("code", "Unknown"), "display_value": allergy.get("display", "Unknown")},
                                            "reaction_type": {"value": allergy.get("display", "Propensity to adverse reaction"), "display_value": allergy.get("display", "Propensity to adverse reaction")},
                                            "manifestation": {"value": allergy.get("manifestation_display", "Unknown reaction"), "display_value": allergy.get("manifestation_display", "Unknown reaction")},
                                            "agent": {"value": allergy.get("agent_display", "Unknown"), "display_value": allergy.get("agent_display", "Unknown")},
                                            "time": {"value": allergy.get("onset_date", "Unknown"), "display_value": allergy.get("onset_date", "Unknown")},
                                            "severity": {"value": allergy.get("severity", "unknown"), "display_value": allergy.get("severity", "unknown").title()},
                                            "criticality": {"value": "High" if allergy.get("severity", "").lower() == "severe" else "Medium" if allergy.get("severity", "").lower() == "moderate" else "Low", "display_value": "High" if allergy.get("severity", "").lower() == "severe" else "Medium" if allergy.get("severity", "").lower() == "moderate" else "Low"},
                                            "status": {"value": allergy.get("status", "active"), "display_value": allergy.get("status", "active").title()},
                                            "certainty": {"value": "confirmed", "display_value": "Confirmed"},
                                        },
                                        "has_medical_codes": bool(allergy.get("code"))
                                    }
                                    display_section["clinical_table"]["rows"].append(row)

                                logger.info(f"[ENHANCED CDA HELPER] Created clinical_table with {len(display_section['clinical_table']['rows'])} allergy rows")
                            
                    except Exception as e:
                        logger.error(f"[ENHANCED CDA HELPER] Enhanced allergies processing failed: {e}")

                clinical_sections.append(display_section)

            logger.info(
                f"[SUCCESS] Extracted {len(clinical_sections)} clinical sections"
            )
            return clinical_sections

        except Exception as e:
            logger.error(f"[ERROR] Clinical sections extraction failed: {e}")
            return []

    def _transform_to_display_format(
        self, extraction_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transform clinical extractor result to display-ready format"""

        # Get the enhanced parser data which has the best structure
        enhanced_data = extraction_result.get("clinical_sections", {}).get(
            "enhanced_parser", {}
        )

        # Transform to simplified display format
        display_data = {
            "success": True,
            "extraction_timestamp": extraction_result.get("extraction_timestamp"),
            "extraction_methods": extraction_result.get("extraction_methods", []),
            "clinical_sections": enhanced_data.get("sections_found", []),
            "administrative_data": enhanced_data.get("administrative_data", {}),
            "sections_count": len(enhanced_data.get("sections_found", [])),
            "coded_sections_count": len(
                [
                    s
                    for s in enhanced_data.get("sections_found", [])
                    if s.get("is_coded_section", False)
                ]
            ),
            "medical_terms_count": sum(
                [
                    len(s.get("loinc_codes", [])) + len(s.get("snomed_codes", []))
                    for s in enhanced_data.get("sections_found", [])
                ]
            ),
            "uses_coded_sections": any(
                [
                    s.get("is_coded_section", False)
                    for s in enhanced_data.get("sections_found", [])
                ]
            ),
            "translation_quality": (
                "High (Structured)" if enhanced_data.get("sections_found") else "Basic"
            ),
        }

        # Calculate coding percentage
        if display_data["sections_count"] > 0:
            display_data["coded_sections_percentage"] = (
                display_data["coded_sections_count"]
                / display_data["sections_count"]
                * 100
            )
        else:
            display_data["coded_sections_percentage"] = 0

        return display_data

    def _extract_contact_information(self, admin_data: Dict) -> Dict[str, Any]:
        """Extract and structure contact information"""
        contact_info = {}

        if admin_data.get("patient_contact_info"):
            patient_contact = admin_data["patient_contact_info"]
            contact_info["patient_addresses"] = patient_contact.get("addresses", [])
            contact_info["patient_telecoms"] = patient_contact.get("telecoms", [])

        return contact_info

    def _extract_healthcare_providers(self, admin_data: Dict) -> Dict[str, Any]:
        """Extract healthcare provider information"""
        providers = {}

        if admin_data.get("author_hcp"):
            providers["author"] = admin_data["author_hcp"]

        if admin_data.get("legal_authenticator"):
            providers["legal_authenticator"] = admin_data["legal_authenticator"]

        if admin_data.get("custodian_organization"):
            providers["custodian"] = admin_data["custodian_organization"]

        return providers

    def _extract_document_details(self, admin_data: Dict) -> Dict[str, Any]:
        """Extract document metadata details"""
        details = {
            "creation_date": admin_data.get("document_creation_date"),
            "last_update": admin_data.get("document_last_update_date"),
            "version": admin_data.get("document_version_number"),
        }

        return details

    def _extract_contact_information_standardized(
        self, admin_data: Dict
    ) -> Dict[str, Any]:
        """Extract and structure contact information with STANDARDIZED template keys"""
        contact_data = {
            "addresses": [],
            "telecoms": [],
        }

        if admin_data.get("patient_contact_info"):
            patient_contact = admin_data["patient_contact_info"]
            contact_data["addresses"] = patient_contact.get("addresses", [])
            contact_data["telecoms"] = patient_contact.get("telecoms", [])

        return contact_data

    def _extract_healthcare_providers_standardized(
        self, admin_data: Dict
    ) -> Dict[str, Any]:
        """Extract healthcare provider information with STANDARDIZED template keys"""
        healthcare_data = {}

        logger.info(f"[DEBUG] CDA Helper - Admin data keys: {list(admin_data.keys())}")
        logger.info(
            f"[DEBUG] CDA Helper - Has author_hcp: {bool(admin_data.get('author_hcp'))}"
        )
        logger.info(
            f"[DEBUG] CDA Helper - Has legal_authenticator: {bool(admin_data.get('legal_authenticator'))}"
        )
        logger.info(
            f"[DEBUG] CDA Helper - Has custodian_organization: {bool(admin_data.get('custodian_organization'))}"
        )

        if admin_data.get("author_hcp"):
            healthcare_data["author"] = admin_data["author_hcp"]
            logger.info(
                f"[DEBUG] CDA Helper - Author mapped: {admin_data['author_hcp'].get('full_name', 'No name')}"
            )

        if admin_data.get("legal_authenticator"):
            healthcare_data["legal_authenticator"] = admin_data["legal_authenticator"]
            logger.info(
                f"[DEBUG] CDA Helper - Legal auth mapped: {admin_data['legal_authenticator'].get('full_name', 'No name')}"
            )

        if admin_data.get("custodian_organization"):
            healthcare_data["custodian"] = admin_data["custodian_organization"]
            logger.info(
                f"[DEBUG] CDA Helper - Custodian mapped: {admin_data['custodian_organization'].get('name', 'No name')}"
            )

        logger.info(
            f"[DEBUG] CDA Helper - Final healthcare_data keys: {list(healthcare_data.keys())}"
        )
        return healthcare_data

    def _identify_coding_systems(self, clinical_codes: List) -> List[str]:
        """Identify which coding systems are used in clinical codes"""
        systems = set()

        for code in clinical_codes:
            if hasattr(code, "system"):
                system_name = code.system.lower()
            elif isinstance(code, dict):
                system_name = code.get("system", code.get("code_system", "")).lower()
            else:
                continue

            if "loinc" in system_name:
                systems.add("LOINC")
            elif "snomed" in system_name:
                systems.add("SNOMED CT")
            elif "icd" in system_name:
                systems.add("ICD")

        return list(systems)

    def _get_empty_display_data(self, error: str = None) -> Dict[str, Any]:
        """Return empty display data structure for error cases"""
        return {
            "success": False,
            "error": error,
            "clinical_sections": [],
            "administrative_data": {},
            "sections_count": 0,
            "coded_sections_count": 0,
            "coded_sections_percentage": 0,
            "medical_terms_count": 0,
            "uses_coded_sections": False,
            "translation_quality": "Error",
        }

    def get_service_status(self) -> Dict[str, str]:
        """Get service status information"""
        return {
            "service": "CDADisplayDataHelper",
            "status": "active",
            "clinical_extractor": "active" if self.clinical_extractor else "inactive",
            "enhanced_parser": "active" if self.enhanced_parser else "inactive",
            "structured_extractor": (
                "active" if self.structured_extractor else "inactive"
            ),
            "version": "v1.0",
        }
