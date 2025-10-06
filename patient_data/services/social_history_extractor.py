# patient_data/services/social_history_extractor.py

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Optional
from translation_services.terminology_translator import TerminologyTranslator

logger = logging.getLogger(__name__)

@dataclass
class SocialHistoryEntry:
    """Structured data model for Social History entries"""
    observation_type: str
    observation_value: str = ""
    observation_time: str = ""
    observation_code: str = ""
    observation_code_system: str = ""
    value_unit: str = ""
    value_numeric: str = ""
    status: str = ""
    effective_time_low: str = ""
    effective_time_high: str = ""

class SocialHistoryExtractor:
    """Extracts Social History data from CDA documents"""
    
    def __init__(self):
        # Define XML namespace mappings for CDA parsing
        self.namespaces = {
            'hl7': 'urn:hl7-org:v3',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
        # Initialize CTS agent for terminology resolution
        self.terminology_translator = TerminologyTranslator()
    
    def extract_social_history(self, cda_content: str) -> List[SocialHistoryEntry]:
        """
        Extract Social History entries from CDA XML
        
        Args:
            cda_content (str): Raw CDA XML content
            
        Returns:
            List[SocialHistoryEntry]: Structured clinical data
        """
        try:
            root = ET.fromstring(cda_content)
            
            # Find the Social History section using LOINC code 29762-2
            section = None
            for sect in root.findall(".//hl7:section", self.namespaces):
                code_elem = sect.find("hl7:code", self.namespaces)
                if code_elem is not None and code_elem.get('code') == '29762-2':
                    section = sect
                    break
            
            if section is None:
                logger.info("No Social History section found")
                return []
            
            entries = []
            
            # Extract observation entries from the section
            for entry in section.findall(".//hl7:entry", self.namespaces):
                observation = entry.find(".//hl7:observation", self.namespaces)
                if observation is not None:
                    social_entry = self._extract_single_observation(observation)
                    if social_entry:
                        entries.append(social_entry)
            
            logger.info(f"Successfully extracted {len(entries)} Social History entries")
            return entries
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error in Social History extraction: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in Social History extraction: {e}")
            return []
    
    def _extract_single_observation(self, observation_element) -> Optional[SocialHistoryEntry]:
        """Extract data from a single observation element"""
        try:
            # Extract observation type from code displayName or originalText
            observation_type = self._extract_observation_type(observation_element)
            if not observation_type:
                return None
            
            # Extract observation value
            observation_value = self._extract_observation_value(observation_element)
            
            # Extract time information
            observation_time = self._extract_time_period(observation_element)
            
            # Extract effective time components
            effective_time_low, effective_time_high = self._extract_effective_time(observation_element)
            
            # Extract code information
            observation_code, observation_code_system = self._extract_code_info(observation_element)
            
            # Extract value unit and numeric value
            value_unit, value_numeric = self._extract_value_details(observation_element)
            
            # Extract status
            status = self._extract_status(observation_element)
            
            return SocialHistoryEntry(
                observation_type=observation_type,
                observation_value=observation_value,
                observation_time=observation_time,
                observation_code=observation_code,
                observation_code_system=observation_code_system,
                value_unit=value_unit,
                value_numeric=value_numeric,
                status=status,
                effective_time_low=effective_time_low,
                effective_time_high=effective_time_high
            )
            
        except Exception as e:
            logger.warning(f"Failed to extract single Social History observation: {e}")
            return None
    
    def _extract_observation_type(self, observation_element) -> str:
        """Extract the observation type from code element using CTS agent for SNOMED resolution"""
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
                
                # Use CTS agent to resolve SNOMED codes to proper medical descriptions
                if code and code_system:
                    resolved_description = self.terminology_translator.resolve_code(code, code_system)
                    if resolved_description:
                        logger.info(f"CTS resolved SNOMED code {code} to: {resolved_description}")
                        return resolved_description
                
                # If no CTS resolution, try originalText
                original_text = code_element.find(".//hl7:originalText", self.namespaces)
                if original_text is not None and original_text.text:
                    return original_text.text.strip()
            
            # Fallback to generic text only if all other methods fail
            logger.warning("Using fallback generic text for Social History observation")
            return "Social History Observation"
            
        except Exception as e:
            logger.warning(f"Error extracting observation type: {e}")
            return ""
    
    def _extract_observation_value(self, observation_element) -> str:
        """Extract the observation value from value element"""
        try:
            # Look for value element with different types
            value_element = observation_element.find(".//hl7:value", self.namespaces)
            if value_element is not None:
                # Check for PQ (Physical Quantity) type
                xsi_type = value_element.get('{http://www.w3.org/2001/XMLSchema-instance}type')
                if xsi_type == 'PQ':
                    value = value_element.get('value', '')
                    unit = value_element.get('unit', '')
                    if value and unit:
                        return f"{value} {unit}"
                    elif value:
                        return value
                
                # Check for CD (Coded Data) type
                elif xsi_type == 'CD':
                    display_name = value_element.get('displayName')
                    if display_name:
                        return display_name
                
                # Check for ST (String) type or direct text
                elif value_element.text:
                    return value_element.text.strip()
            
            return ""
            
        except Exception as e:
            logger.warning(f"Error extracting observation value: {e}")
            return ""
    
    def _extract_time_period(self, observation_element) -> str:
        """Extract formatted time period from effectiveTime"""
        try:
            effective_time = observation_element.find(".//hl7:effectiveTime", self.namespaces)
            if effective_time is not None:
                low_elem = effective_time.find(".//hl7:low", self.namespaces)
                high_elem = effective_time.find(".//hl7:high", self.namespaces)
                
                low_value = low_elem.get('value') if low_elem is not None else None
                high_value = high_elem.get('value') if high_elem is not None else None
                
                # Format the time period
                if low_value and high_value:
                    low_formatted = self._format_date(low_value)
                    high_formatted = self._format_date(high_value)
                    return f"{low_formatted} - {high_formatted}"
                elif low_value:
                    low_formatted = self._format_date(low_value)
                    return f"Since {low_formatted}"
                elif high_value:
                    high_formatted = self._format_date(high_value)
                    return f"Until {high_formatted}"
            
            return ""
            
        except Exception as e:
            logger.warning(f"Error extracting time period: {e}")
            return ""
    
    def _extract_effective_time(self, observation_element) -> tuple:
        """Extract effective time low and high values"""
        try:
            effective_time = observation_element.find(".//hl7:effectiveTime", self.namespaces)
            if effective_time is not None:
                low_elem = effective_time.find(".//hl7:low", self.namespaces)
                high_elem = effective_time.find(".//hl7:high", self.namespaces)
                
                low_value = low_elem.get('value') if low_elem is not None else ""
                high_value = high_elem.get('value') if high_elem is not None else ""
                
                return low_value, high_value
            
            return "", ""
            
        except Exception as e:
            logger.warning(f"Error extracting effective time: {e}")
            return "", ""
    
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
    
    def _extract_value_details(self, observation_element) -> tuple:
        """Extract numeric value and unit separately"""
        try:
            value_element = observation_element.find(".//hl7:value", self.namespaces)
            if value_element is not None:
                xsi_type = value_element.get('{http://www.w3.org/2001/XMLSchema-instance}type')
                if xsi_type == 'PQ':
                    value = value_element.get('value', '')
                    unit = value_element.get('unit', '')
                    return unit, value
            
            return "", ""
            
        except Exception as e:
            logger.warning(f"Error extracting value details: {e}")
            return "", ""
    
    def _extract_status(self, observation_element) -> str:
        """Extract status code"""
        try:
            status_element = observation_element.find(".//hl7:statusCode", self.namespaces)
            if status_element is not None:
                return status_element.get('code', '')
            
            return ""
            
        except Exception as e:
            logger.warning(f"Error extracting status: {e}")
            return ""
    
    def _format_date(self, date_value: str) -> str:
        """Format CDA date values for display"""
        try:
            if not date_value:
                return ""
            
            # Handle different date formats
            if len(date_value) >= 8:  # YYYYMMDD or longer
                year = date_value[:4]
                month = date_value[4:6] if len(date_value) >= 6 else ""
                day = date_value[6:8] if len(date_value) >= 8 else ""
                
                if month and day:
                    return f"{day}/{month}/{year}"
                elif month:
                    return f"{month}/{year}"
                else:
                    return year
            elif len(date_value) == 4:  # Just year
                return date_value
            
            return date_value
            
        except Exception as e:
            logger.warning(f"Error formatting date {date_value}: {e}")
            return date_value