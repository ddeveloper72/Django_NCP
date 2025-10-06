# patient_data/services/physical_findings_extractor.py

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Optional
from translation_services.terminology_translator import TerminologyTranslator

logger = logging.getLogger(__name__)

@dataclass
class PhysicalFindingsEntry:
    """Structured data model for Physical Findings entries"""
    observation_type: str
    observation_value: str = ""
    observation_time: str = ""
    observation_code: str = ""
    observation_code_system: str = ""
    value_unit: str = ""
    value_numeric: str = ""
    status: str = ""
    effective_time: str = ""
    organizer_type: str = ""
    organizer_code: str = ""
    organizer_code_system: str = ""

class PhysicalFindingsExtractor:
    """Extracts Physical Findings data from CDA documents"""
    
    def __init__(self):
        # Define XML namespace mappings for CDA parsing
        self.namespaces = {
            'hl7': 'urn:hl7-org:v3',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
        # Initialize CTS agent for terminology resolution
        self.terminology_translator = TerminologyTranslator()
    
    def extract_physical_findings(self, cda_content: str) -> List[PhysicalFindingsEntry]:
        """
        Extract Physical Findings entries from CDA XML
        
        Args:
            cda_content (str): Raw CDA XML content
            
        Returns:
            List[PhysicalFindingsEntry]: Structured clinical data
        """
        try:
            root = ET.fromstring(cda_content)
            
            # Find sections that contain Physical Findings
            # Look for various section codes that might contain vital signs/physical findings
            physical_findings_sections = []
            
            # Search for sections with Physical Findings related codes
            for section in root.findall(".//hl7:section", self.namespaces):
                code_elem = section.find("hl7:code", self.namespaces)
                if code_elem is not None:
                    section_code = code_elem.get('code')
                    # Common codes for Physical Findings/Vital Signs sections
                    if section_code in ['8716-3', '29545-1', '8867-4', '46680005']:
                        physical_findings_sections.append(section)
            
            if not physical_findings_sections:
                logger.info("No Physical Findings sections found")
                return []
            
            entries = []
            
            # Extract from all Physical Findings sections
            for section in physical_findings_sections:
                section_entries = self._extract_from_section(section)
                entries.extend(section_entries)
            
            logger.info(f"Successfully extracted {len(entries)} Physical Findings entries")
            return entries
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error in Physical Findings extraction: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in Physical Findings extraction: {e}")
            return []
    
    def _extract_from_section(self, section) -> List[PhysicalFindingsEntry]:
        """Extract entries from a specific section"""
        entries = []
        
        # Look for organizer entries (like the XSLT structure shows)
        for entry in section.findall(".//hl7:entry", self.namespaces):
            organizer = entry.find(".//hl7:organizer", self.namespaces)
            if organizer is not None:
                organizer_entries = self._extract_organizer_observations(organizer)
                entries.extend(organizer_entries)
            else:
                # Also check for direct observations
                observation = entry.find(".//hl7:observation", self.namespaces)
                if observation is not None:
                    obs_entry = self._extract_single_observation(observation)
                    if obs_entry:
                        entries.append(obs_entry)
        
        return entries
    
    def _extract_organizer_observations(self, organizer_element) -> List[PhysicalFindingsEntry]:
        """Extract observations from an organizer element"""
        entries = []
        
        # Get organizer-level information
        organizer_type, organizer_code, organizer_code_system = self._extract_organizer_info(organizer_element)
        organizer_time = self._extract_effective_time(organizer_element)
        organizer_status = self._extract_status(organizer_element)
        
        # Extract component observations
        for component in organizer_element.findall(".//hl7:component", self.namespaces):
            observation = component.find(".//hl7:observation", self.namespaces)
            if observation is not None:
                entry = self._extract_single_observation(
                    observation, 
                    organizer_type=organizer_type,
                    organizer_code=organizer_code,
                    organizer_code_system=organizer_code_system,
                    default_time=organizer_time,
                    default_status=organizer_status
                )
                if entry:
                    entries.append(entry)
        
        return entries
    
    def _extract_single_observation(self, observation_element, organizer_type="", organizer_code="", 
                                  organizer_code_system="", default_time="", default_status="") -> Optional[PhysicalFindingsEntry]:
        """Extract data from a single observation element"""
        try:
            # Extract observation type from code element using CTS agent
            observation_type = self._extract_observation_type(observation_element)
            if not observation_type:
                return None
            
            # Extract observation value and unit
            observation_value, value_unit, value_numeric = self._extract_observation_value(observation_element)
            
            # Extract time information
            observation_time = self._extract_effective_time(observation_element) or default_time
            
            # Extract code information
            observation_code, observation_code_system = self._extract_code_info(observation_element)
            
            # Extract status
            status = self._extract_status(observation_element) or default_status
            
            return PhysicalFindingsEntry(
                observation_type=observation_type,
                observation_value=observation_value,
                observation_time=observation_time,
                observation_code=observation_code,
                observation_code_system=observation_code_system,
                value_unit=value_unit,
                value_numeric=value_numeric,
                status=status,
                effective_time=observation_time,
                organizer_type=organizer_type,
                organizer_code=organizer_code,
                organizer_code_system=organizer_code_system
            )
            
        except Exception as e:
            logger.warning(f"Failed to extract single Physical Findings observation: {e}")
            return None
    
    def _extract_observation_type(self, observation_element) -> str:
        """Extract the observation type from code element using CTS agent for SNOMED/LOINC resolution"""
        try:
            # First get the code information
            code_element = observation_element.find(".//hl7:code", self.namespaces)
            if code_element is not None:
                # Try to get displayName from code element first
                display_name = code_element.get('displayName')
                if display_name:
                    return display_name.strip()
                
                # Get the code and codeSystem for CTS resolution
                code = code_element.get('code')
                code_system = code_element.get('codeSystem')
                
                # Use CTS agent to resolve SNOMED/LOINC codes to proper medical descriptions
                if code and code_system:
                    resolved_description = self.terminology_translator.resolve_code(code, code_system)
                    if resolved_description:
                        logger.info(f"CTS resolved code {code} to: {resolved_description}")
                        return resolved_description
                
                # If no CTS resolution, try originalText
                original_text = code_element.find(".//hl7:originalText", self.namespaces)
                if original_text is not None and original_text.text:
                    return original_text.text.strip()
            
            # Fallback to generic text only if all other methods fail
            logger.warning("Using fallback generic text for Physical Findings observation")
            return "Physical Finding"
            
        except Exception as e:
            logger.warning(f"Error extracting observation type: {e}")
            return ""
    
    def _extract_observation_value(self, observation_element) -> tuple:
        """Extract the observation value, unit, and numeric value from value element"""
        try:
            # Look for value element with different types
            value_element = observation_element.find(".//hl7:value", self.namespaces)
            if value_element is not None:
                # Check for PQ (Physical Quantity) type
                xsi_type = value_element.get('{http://www.w3.org/2001/XMLSchema-instance}type')
                if xsi_type == 'PQ':
                    value = value_element.get('value', '')
                    unit = value_element.get('unit', '')
                    # Format display value
                    if value and unit:
                        display_value = f"{value} {unit}"
                    else:
                        display_value = value or ""
                    return display_value, unit, value
                
                # Handle other value types (CD, ST, etc.)
                elif value_element.text:
                    return value_element.text.strip(), "", ""
            
            return "", "", ""
            
        except Exception as e:
            logger.warning(f"Error extracting observation value: {e}")
            return "", "", ""
    
    def _extract_effective_time(self, element) -> str:
        """Extract effective time from element"""
        try:
            effective_time = element.find(".//hl7:effectiveTime", self.namespaces)
            if effective_time is not None:
                # Try value attribute first
                time_value = effective_time.get('value')
                if time_value:
                    return self._format_date(time_value)
                
                # Try low/high values for ranges
                low_elem = effective_time.find(".//hl7:low", self.namespaces)
                high_elem = effective_time.find(".//hl7:high", self.namespaces)
                
                if low_elem is not None and high_elem is not None:
                    low_value = self._format_date(low_elem.get('value', ''))
                    high_value = self._format_date(high_elem.get('value', ''))
                    if low_value and high_value:
                        return f"{low_value} - {high_value}"
                elif low_elem is not None:
                    return f"Since {self._format_date(low_elem.get('value', ''))}"
            
            return ""
            
        except Exception as e:
            logger.warning(f"Error extracting effective time: {e}")
            return ""
    
    def _extract_code_info(self, observation_element) -> tuple:
        """Extract code and code system information"""
        try:
            code_element = observation_element.find(".//hl7:code", self.namespaces)
            if code_element is not None:
                code = code_element.get('code', '')
                code_system = code_element.get('codeSystem', '')
                return code, code_system
            
            return "", ""
            
        except Exception as e:
            logger.warning(f"Error extracting code info: {e}")
            return "", ""
    
    def _extract_status(self, element) -> str:
        """Extract status from element"""
        try:
            status_element = element.find(".//hl7:statusCode", self.namespaces)
            if status_element is not None:
                return status_element.get('code', '').capitalize()
            return ""
            
        except Exception as e:
            logger.warning(f"Error extracting status: {e}")
            return ""
    
    def _extract_organizer_info(self, organizer_element) -> tuple:
        """Extract organizer type and code information"""
        try:
            # Extract organizer type using CTS agent
            organizer_type = self._extract_observation_type(organizer_element)
            
            # Extract organizer code info
            code_element = organizer_element.find(".//hl7:code", self.namespaces)
            if code_element is not None:
                code = code_element.get('code', '')
                code_system = code_element.get('codeSystem', '')
                return organizer_type, code, code_system
            
            return organizer_type, "", ""
            
        except Exception as e:
            logger.warning(f"Error extracting organizer info: {e}")
            return "", "", ""
    
    def _format_date(self, date_string: str) -> str:
        """Format date string for display"""
        if not date_string:
            return ""
        
        try:
            # Handle different date formats
            if len(date_string) >= 8:
                # YYYYMMDD format
                year = date_string[:4]
                month = date_string[4:6]
                day = date_string[6:8]
                return f"{day}/{month}/{year}"
            
            return date_string
            
        except Exception as e:
            logger.warning(f"Error formatting date {date_string}: {e}")
            return date_string