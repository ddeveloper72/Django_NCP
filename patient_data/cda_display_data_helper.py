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
            logger.debug("ClinicalDataExtractor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ClinicalDataExtractor: {e}")
            self.clinical_extractor = None

        try:
            self.enhanced_parser = EnhancedCDAXMLParser()
            logger.debug("EnhancedCDAXMLParser initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize EnhancedCDAXMLParser: {e}")
            self.enhanced_parser = None

        try:
            self.structured_extractor = StructuredCDAExtractor()
            logger.debug("StructuredCDAExtractor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize StructuredCDAExtractor: {e}")
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
                logger.debug("Enhanced CDA Processor initialized for allergies")
            except Exception as e:
                logger.warning(f"Could not initialize Enhanced CDA Processor: {e}")
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
                
                is_allergies_section = (
                    section_name == "allergies" or 
                    any(keyword in section_title for keyword in ["allerg", "adverse", "reaction", "intolerance"])
                )

                if is_allergies_section and enhanced_processor and cda_content:
                    logger.debug(f"Processing allergies section: {display_section.get('display_name')}")
                    
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
                            # Define namespaces for entry processing (include pharm namespace for agent extraction)
                            namespaces = {
                                'hl7': 'urn:hl7-org:v3',
                                'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                                'pharm': 'urn:hl7-org:pharm'
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
                                        logger.debug("Found observation in entry - extracting data")
                                        # Extract observation data for each allergy
                                        obs_data = enhanced_processor._extract_observation_data(observation, namespaces)
                                        if obs_data:
                                            logger.debug(f"Successfully extracted observation data with {len(obs_data)} fields")
                                            enhanced_allergies.append(obs_data)
                                        else:
                                            logger.warning("Observation data extraction returned empty")
                                    else:
                                        logger.warning("No observation found in entry")

                            if enhanced_allergies:
                                logger.debug(f"Found {len(enhanced_allergies)} enhanced allergies")
                                
                                # Create 8-column clinical table structure for allergies (Code column removed)
                                display_section["clinical_table"] = {
                                    "headers": [
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
                                    # Based on CDA structure: observation/code = reaction type, observation/value = manifestation
                                    # Code column removed - clinical codes will be displayed under manifestation and agent fields
                                    
                                    # Format date range from onset and end dates
                                    onset_date = allergy.get("onset_date", "")
                                    end_date = allergy.get("end_date", "")
                                    time_display = self._format_allergy_date_range(onset_date, end_date)
                                    
                                    row = {
                                        "data": {
                                            "reaction_type": {"value": allergy.get("reaction_type", "Allergic disposition"), "display_value": allergy.get("reaction_type", "Allergic disposition")},
                                            "manifestation": {"value": allergy.get("manifestation_display", "Unknown"), "display_value": allergy.get("manifestation_display", "Unknown"), "code": allergy.get("manifestation_code"), "code_system": allergy.get("manifestation_code_system", "SNOMED CT")},
                                            "agent": {"value": allergy.get("agent_display", "Unknown"), "display_value": allergy.get("agent_display", "Unknown"), "code": allergy.get("agent_code"), "code_system": allergy.get("agent_code_system", "SNOMED CT")},
                                            "time": {"value": time_display, "display_value": time_display},
                                            "severity": {"value": allergy.get("severity", "unknown"), "display_value": allergy.get("severity", "unknown").title()},
                                            "criticality": {"value": "High" if allergy.get("severity", "").lower() == "severe" else "Medium" if allergy.get("severity", "").lower() == "moderate" else "Low", "display_value": "High" if allergy.get("severity", "").lower() == "severe" else "Medium" if allergy.get("severity", "").lower() == "moderate" else "Low"},
                                            "status": {"value": allergy.get("status", "active"), "display_value": allergy.get("status", "active").title()},
                                            "certainty": {"value": "confirmed", "display_value": "Confirmed"},
                                        },
                                        "has_medical_codes": bool(allergy.get("code")),
                                        # Add the allergy object for template access to codes
                                        "allergy_data": allergy
                                    }
                                    display_section["clinical_table"]["rows"].append(row)

                                logger.debug(f"Created clinical_table with {len(display_section['clinical_table']['rows'])} allergy rows")
                            
                    except Exception as e:
                        logger.error(f"Enhanced allergies processing failed: {e}")

                # ENHANCED: Check if this is a procedures section and apply Enhanced CDA Processor
                is_procedures_section = (
                    section_name == "procedures" or 
                    section_name == "medical_procedures" or
                    any(keyword in section_title for keyword in ["procedure", "surgery", "surgical", "intervention"])
                )

                if is_procedures_section and enhanced_processor and cda_content:
                    logger.debug(f"Processing procedures section: {display_section.get('display_name')}")
                    
                    try:
                        # Extract procedures using Enhanced CDA Processor
                        import xml.etree.ElementTree as ET
                        root = ET.fromstring(cda_content)
                        
                        # Find procedures section (code 47519-4) using manual filtering
                        all_sections = root.findall(".//{urn:hl7-org:v3}section")
                        procedures_sections = []
                        
                        for section in all_sections:
                            code_elem = section.find('{urn:hl7-org:v3}code')
                            if code_elem is not None and code_elem.get('code') == '47519-4':
                                procedures_sections.append(section)
                        
                        if procedures_sections:
                            # Define namespaces for procedure processing
                            namespaces = {
                                'hl7': 'urn:hl7-org:v3',
                                'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
                            }
                            
                            enhanced_procedures = []
                            for section in procedures_sections:
                                # Extract entries from procedures section
                                entries = section.findall("{urn:hl7-org:v3}entry")
                                
                                for entry in entries:
                                    # Find procedure within entry
                                    procedure = entry.find("{urn:hl7-org:v3}procedure")
                                    
                                    if procedure is not None:
                                        logger.debug("Found procedure in entry - extracting data")
                                        # Extract procedure data
                                        proc_data = enhanced_processor._extract_procedure_data(procedure, namespaces)
                                        if proc_data:
                                            logger.debug(f"Successfully extracted procedure data with {len(proc_data)} fields")
                                            enhanced_procedures.append(proc_data)
                                        else:
                                            logger.warning("Procedure data extraction returned empty")
                            
                            if enhanced_procedures:
                                logger.debug(f"Found {len(enhanced_procedures)} enhanced procedures")
                                
                                # Create clinical table structure for procedures
                                display_section["clinical_table"] = {
                                    "headers": [
                                        {"key": "procedure", "label": "Procedure", "type": "procedure"},
                                        {"key": "target_site", "label": "Target Site", "type": "target_site"},  
                                        {"key": "procedure_date", "label": "Procedure Date", "type": "date"},
                                    ],
                                    "rows": [],
                                    "total_count": len(enhanced_procedures),
                                    "table_type": "procedures"
                                }
                                
                                # Process each procedure into table row
                                for procedure in enhanced_procedures:
                                    row = {
                                        "data": {
                                            "procedure": {"value": procedure.get("procedure_display", "Unknown"), "display_value": procedure.get("procedure_display", "Unknown"), "code": procedure.get("procedure_code"), "code_system": procedure.get("procedure_code_system", "SNOMED CT")},
                                            "target_site": {"value": procedure.get("target_site_display", "Not specified"), "display_value": procedure.get("target_site_display", "Not specified"), "code": procedure.get("target_site_code"), "code_system": procedure.get("target_site_code_system", "SNOMED CT")},
                                            "procedure_date": {"value": procedure.get("formatted_date", "Not specified"), "display_value": procedure.get("formatted_date", "Not specified")},
                                        },
                                        "has_medical_codes": bool(procedure.get("procedure_code")),
                                        # Add the procedure object for template access to codes
                                        "procedure_data": procedure
                                    }
                                    display_section["clinical_table"]["rows"].append(row)

                                logger.debug(f"Created clinical_table with {len(display_section['clinical_table']['rows'])} procedure rows")
                            
                    except Exception as e:
                        logger.error(f"Enhanced procedures processing failed: {e}")

                # ENHANCED: Check if this is a medical devices section and apply Enhanced CDA Processor
                is_medical_devices_section = (
                    section_name == "medical_devices" or 
                    section_name == "medical_device" or
                    any(keyword in section_title for keyword in ["medical device", "device", "implant", "equipment"])
                )

                if is_medical_devices_section and enhanced_processor and cda_content:
                    logger.debug(f"Processing medical devices section: {display_section.get('display_name')}")
                    
                    try:
                        # Extract medical devices using Enhanced CDA Processor
                        import xml.etree.ElementTree as ET
                        root = ET.fromstring(cda_content)
                        
                        # Find medical devices section (code 46264-8) using manual filtering
                        all_sections = root.findall(".//{urn:hl7-org:v3}section")
                        devices_sections = []
                        
                        for section in all_sections:
                            code_elem = section.find('{urn:hl7-org:v3}code')
                            if code_elem is not None and code_elem.get('code') == '46264-8':
                                devices_sections.append(section)
                        
                        if devices_sections:
                            # Define namespaces for device processing
                            namespaces = {
                                'hl7': 'urn:hl7-org:v3',
                                'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
                            }
                            
                            enhanced_devices = []
                            for section in devices_sections:
                                # Extract entries from medical devices section
                                entries = section.findall("{urn:hl7-org:v3}entry")
                                
                                for entry in entries:
                                    # Find different device elements (supply, act, organizer)
                                    device_elements = (
                                        entry.findall("{urn:hl7-org:v3}supply") +
                                        entry.findall("{urn:hl7-org:v3}act") +
                                        entry.findall("{urn:hl7-org:v3}organizer")
                                    )
                                    
                                    for device_elem in device_elements:
                                        logger.debug("Found medical device element - extracting data")
                                        # Extract medical device data
                                        device_data = enhanced_processor._extract_medical_device_data(device_elem, namespaces)
                                        if device_data:
                                            logger.debug(f"Successfully extracted device data with {len(device_data)} fields")
                                            enhanced_devices.append(device_data)
                                        else:
                                            logger.warning("Medical device data extraction returned empty")
                            
                            if enhanced_devices:
                                logger.debug(f"Found {len(enhanced_devices)} enhanced medical devices")
                                
                                # Create clinical table structure for medical devices
                                display_section["clinical_table"] = {
                                    "headers": [
                                        {"key": "device", "label": "Medical Device", "type": "device"},
                                        {"key": "usage_period", "label": "Usage Period", "type": "date"},  
                                        {"key": "status", "label": "Status", "type": "status"},
                                    ],
                                    "rows": [],
                                    "total_count": len(enhanced_devices),
                                    "table_type": "medical_devices"
                                }
                                
                                # Process each device into table row
                                for device in enhanced_devices:
                                    row = {
                                        "data": {
                                            "device": {"value": device.get("device_display", "Unknown"), "display_value": device.get("device_display", "Unknown"), "code": device.get("device_code"), "code_system": device.get("device_code_system", "SNOMED CT")},
                                            "usage_period": {"value": device.get("usage_period", "Not specified"), "display_value": device.get("usage_period", "Not specified")},
                                            "status": {"value": device.get("status_display", "Active"), "display_value": device.get("status_display", "Active")},
                                        },
                                        "has_medical_codes": bool(device.get("device_code")),
                                        # Add the device object for template access to codes
                                        "device_data": device
                                    }
                                    display_section["clinical_table"]["rows"].append(row)

                                logger.debug(f"Created clinical_table with {len(display_section['clinical_table']['rows'])} medical device rows")
                            
                    except Exception as e:
                        logger.error(f"Enhanced medical devices processing failed: {e}")

                clinical_sections.append(display_section)

            logger.debug(f"Extracted {len(clinical_sections)} clinical sections")
            return clinical_sections

        except Exception as e:
            logger.error(f"Clinical sections extraction failed: {e}")
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

    def _format_allergy_date_range(self, onset_date: str, end_date: str) -> str:
        """Format allergy date range from onset and end dates"""
        if onset_date and end_date:
            if onset_date == end_date:
                # Same date
                return onset_date
            else:
                # Different dates - show as range
                return f"{onset_date} - {end_date}"
        elif onset_date:
            # Only start date available
            return f"From {onset_date}"
        elif end_date:
            # Only end date available (unusual but possible)
            return f"Until {end_date}"
        else:
            return "Unknown"

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
