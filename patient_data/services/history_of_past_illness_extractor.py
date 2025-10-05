"""
History of Past Illness CDA Extractor Service

Extracts and structures History of Past Illness data from CDA documents
according to European healthcare standards.

Section Code: 11348-0 - "History of past illness"

Expected table columns:
1. Closed/Inactive Problem
2. Problem Type  
3. Time (from-to timeline)
4. Problem Status
5. Health Status

Clinical codes extracted for CTS lookup integration.
"""

import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class HistoryIllnessEntry:
    """Represents a single History of Past Illness entry"""
    
    # Core data fields matching table columns
    problem_name: str
    problem_type: str
    time_period: str  # formatted from-to range
    problem_status: str
    health_status: str
    
    # Raw time data
    effective_time_low: Optional[str] = None
    effective_time_high: Optional[str] = None
    
    # Clinical codes for CTS lookup
    problem_code: Optional[str] = None
    problem_code_system: Optional[str] = None
    problem_code_display: Optional[str] = None
    
    health_status_code: Optional[str] = None
    health_status_code_system: Optional[str] = None
    
    status_code: Optional[str] = None
    
    # Additional metadata
    entry_id: Optional[str] = None
    narrative_reference: Optional[str] = None


class HistoryOfPastIllnessExtractor:
    """Extracts History of Past Illness data from CDA documents"""
    
    def __init__(self):
        self.namespaces = {
            'hl7': 'urn:hl7-org:v3',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
        
        # Section code for History of Past Illness
        self.section_code = '11348-0'
        
    def extract_history_of_past_illness(self, cda_content: str) -> List[HistoryIllnessEntry]:
        """
        Extract History of Past Illness entries from CDA XML content
        
        Args:
            cda_content: Raw CDA XML content
            
        Returns:
            List of HistoryIllnessEntry objects
        """
        try:
            root = ET.fromstring(cda_content)
            self.root = root  # Store root for reference resolution
            entries = []
            
            # Find History of Past Illness section
            history_sections = self._find_history_sections(root)
            
            logger.info(f"Found {len(history_sections)} History of Past Illness sections")
            
            for section in history_sections:
                section_entries = self._extract_section_entries(section)
                entries.extend(section_entries)
                
            logger.info(f"Extracted {len(entries)} History of Past Illness entries")
            return entries
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error in History of Past Illness extraction: {e}")
            return []
        except Exception as e:
            logger.error(f"Error extracting History of Past Illness: {e}")
            return []
    
    def _find_history_sections(self, root: ET.Element) -> List[ET.Element]:
        """Find all History of Past Illness sections"""
        sections = []
        
        # Find all sections and filter by code
        all_sections = root.findall(".//{urn:hl7-org:v3}section")
        
        for section in all_sections:
            code_elem = section.find('{urn:hl7-org:v3}code')
            if code_elem is not None and code_elem.get('code') == self.section_code:
                sections.append(section)
                logger.debug(f"Found History of Past Illness section with code {self.section_code}")
                
        return sections
    
    def _extract_section_entries(self, section: ET.Element) -> List[HistoryIllnessEntry]:
        """Extract entries from a History of Past Illness section"""
        entries = []
        
        # Find all entry elements in the section
        entry_elements = section.findall('.//{urn:hl7-org:v3}entry')
        
        logger.info(f"Processing {len(entry_elements)} entries in History of Past Illness section")
        
        for entry_elem in entry_elements:
            entry = self._parse_single_entry(entry_elem)
            if entry:
                entries.append(entry)
                
        return entries
    
    def _parse_single_entry(self, entry_elem: ET.Element) -> Optional[HistoryIllnessEntry]:
        """Parse a single entry element into HistoryIllnessEntry"""
        try:
            # Find the act element (should be immediate child)
            act_elem = entry_elem.find('{urn:hl7-org:v3}act')
            if act_elem is None:
                logger.warning("No act element found in entry")
                return None
                
            # Extract entry ID
            entry_id = self._get_element_attribute(act_elem, '{urn:hl7-org:v3}id', 'root')
            
            # Extract narrative reference
            narrative_ref = self._extract_narrative_reference(act_elem)
            
            # Extract status code from act
            status_code = self._get_element_attribute(act_elem, '{urn:hl7-org:v3}statusCode', 'code')
            
            # Extract effective time from act level
            act_time_low, act_time_high = self._extract_effective_time(act_elem)
            
            # Find the observation in entryRelationship
            observation = self._find_primary_observation(act_elem)
            if observation is None:
                logger.warning(f"No primary observation found in entry {entry_id}")
                return None
                
            # Extract problem details from observation
            problem_name = self._extract_problem_name(observation)
            problem_code, problem_code_system, problem_display = self._extract_problem_code(observation)
            
            # Extract observation effective time (may override act time)
            obs_time_low, obs_time_high = self._extract_effective_time(observation)
            effective_low = obs_time_low or act_time_low
            effective_high = obs_time_high or act_time_high
            
            # Extract health status from related observations
            health_status, health_status_code, health_status_code_system = self._extract_health_status(observation)
            
            # Format time period
            time_period = self._format_time_period(effective_low, effective_high)
            
            # Create entry object
            entry = HistoryIllnessEntry(
                problem_name=problem_name or "Unknown Problem",
                problem_type="Problem",  # Default from CDA structure
                time_period=time_period,
                problem_status=self._format_status_code(status_code),
                health_status=health_status or "Unknown",
                effective_time_low=effective_low,
                effective_time_high=effective_high,
                problem_code=problem_code,
                problem_code_system=problem_code_system,
                problem_code_display=problem_display,
                health_status_code=health_status_code,
                health_status_code_system=health_status_code_system,
                status_code=status_code,
                entry_id=entry_id,
                narrative_reference=narrative_ref
            )
            
            logger.debug(f"Successfully parsed History of Past Illness entry: {problem_name}")
            return entry
            
        except Exception as e:
            logger.error(f"Error parsing History of Past Illness entry: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return None
    
    def _find_primary_observation(self, act_elem: ET.Element) -> Optional[ET.Element]:
        """Find the primary observation element in entry relationship"""
        # Look for entryRelationship with typeCode="SUBJ"
        entry_relationships = act_elem.findall('{urn:hl7-org:v3}entryRelationship[@typeCode="SUBJ"]')
        
        for rel in entry_relationships:
            observation = rel.find('{urn:hl7-org:v3}observation')
            if observation is not None:
                return observation
                
        return None
    
    def _extract_problem_name(self, observation: ET.Element) -> Optional[str]:
        """Extract problem name from observation"""
        # Try to get from value element originalText reference
        value_elem = observation.find('{urn:hl7-org:v3}value')
        if value_elem is not None:
            original_text = value_elem.find('{urn:hl7-org:v3}originalText')
            if original_text is not None:
                reference = original_text.find('{urn:hl7-org:v3}reference')
                if reference is not None:
                    ref_value = reference.get('value', '')
                    # Try to resolve reference to actual text content from section
                    resolved_text = self._resolve_narrative_reference(ref_value, observation)
                    if resolved_text:
                        return resolved_text
                    # Fallback to reference placeholder
                    return f"Problem (ref: {ref_value})"
        
        # Try to get from code displayName
        code_elem = observation.find('{urn:hl7-org:v3}code')
        if code_elem is not None:
            display_name = code_elem.get('displayName')
            if display_name:
                return display_name
                
        # Try to get from value displayName
        if value_elem is not None:
            display_name = value_elem.get('displayName')
            if display_name:
                return display_name
                
        return None
    
    def _resolve_narrative_reference(self, ref_value: str, observation: ET.Element) -> Optional[str]:
        """Try to resolve narrative reference to actual text content"""
        if not ref_value.startswith('#'):
            return None
            
        ref_id = ref_value[1:]  # Remove '#' prefix
        
        # Use stored root element to find text content
        if hasattr(self, 'root') and self.root is not None:
            # Find all sections and look for the text content
            for sect in self.root.findall(".//{urn:hl7-org:v3}section"):
                text_content = self._find_text_by_id(sect, ref_id)
                if text_content:
                    return text_content
                
        return None
    
    def _find_text_by_id(self, section: ET.Element, ref_id: str) -> Optional[str]:
        """Find text content by ID reference in a section"""
        # Check paragraphs with matching ID
        xpath_query = f".//{{{self.namespaces['hl7']}}}paragraph[@ID='{ref_id}']"
        for paragraph in section.findall(xpath_query):
            text_content = paragraph.text
            if text_content:
                return text_content.strip()
        
        # Check content elements with matching ID
        xpath_query = f".//{{{self.namespaces['hl7']}}}content[@ID='{ref_id}']"
        for content in section.findall(xpath_query):
            text_content = content.text
            if text_content:
                return text_content.strip()
        
        # Check table rows with matching ID
        xpath_query = f".//{{{self.namespaces['hl7']}}}tr[@ID='{ref_id}']"
        for tr in section.findall(xpath_query):
            # Extract text from first td element (problem name column)
            td_xpath = f".//{{{self.namespaces['hl7']}}}td"
            first_td = tr.find(td_xpath)
            if first_td is not None:
                # Get text content, handling nested content elements
                text_parts = []
                for elem in first_td.iter():
                    if elem.text:
                        text_parts.append(elem.text.strip())
                if text_parts:
                    return ' '.join(text_parts)
        
        return None
    
    def _extract_problem_code(self, observation: ET.Element) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract problem code information"""
        # First try the value element (primary condition code)
        value_elem = observation.find('{urn:hl7-org:v3}value')
        if value_elem is not None:
            code = value_elem.get('code')
            code_system = value_elem.get('codeSystem') 
            display_name = value_elem.get('displayName')
            if code:
                return code, code_system, display_name
        
        # Fallback to code element
        code_elem = observation.find('{urn:hl7-org:v3}code')
        if code_elem is not None:
            code = code_elem.get('code')
            code_system = code_elem.get('codeSystem')
            display_name = code_elem.get('displayName')
            return code, code_system, display_name
            
        return None, None, None
    
    def _extract_health_status(self, observation: ET.Element) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract health status from related observations"""
        # Look for entryRelationship with Health Status observation
        entry_relationships = observation.findall('{urn:hl7-org:v3}entryRelationship[@typeCode="REFR"]')
        
        for rel in entry_relationships:
            health_obs = rel.find('{urn:hl7-org:v3}observation')
            if health_obs is not None:
                # Check if this is a health status observation
                code_elem = health_obs.find('{urn:hl7-org:v3}code')
                if code_elem is not None and code_elem.get('code') == '11323-3':  # Health Status LOINC code
                    # Extract health status value
                    value_elem = health_obs.find('{urn:hl7-org:v3}value')
                    if value_elem is not None:
                        display_name = value_elem.get('displayName')
                        code = value_elem.get('code')
                        code_system = value_elem.get('codeSystem')
                        
                        # Try to resolve originalText reference if no displayName
                        if not display_name:
                            original_text = value_elem.find('{urn:hl7-org:v3}originalText')
                            if original_text is not None:
                                reference = original_text.find('{urn:hl7-org:v3}reference')
                                if reference is not None:
                                    ref_value = reference.get('value', '')
                                    resolved_text = self._resolve_narrative_reference(ref_value, observation)
                                    if resolved_text:
                                        display_name = resolved_text
                                    else:
                                        display_name = f"Health Status (ref: {ref_value})"
                        
                        return display_name, code, code_system
        
        return None, None, None
    
    def _extract_effective_time(self, element: ET.Element) -> tuple[Optional[str], Optional[str]]:
        """Extract effective time low and high values"""
        effective_time = element.find('{urn:hl7-org:v3}effectiveTime')
        if effective_time is not None:
            low_elem = effective_time.find('{urn:hl7-org:v3}low')
            high_elem = effective_time.find('{urn:hl7-org:v3}high')
            
            low_value = low_elem.get('value') if low_elem is not None else None
            high_value = high_elem.get('value') if high_elem is not None else None
            
            return low_value, high_value
            
        return None, None
    
    def _extract_narrative_reference(self, act_elem: ET.Element) -> Optional[str]:
        """Extract narrative text reference"""
        text_elem = act_elem.find('{urn:hl7-org:v3}text')
        if text_elem is not None:
            reference = text_elem.find('{urn:hl7-org:v3}reference')
            if reference is not None:
                return reference.get('value')
        return None
    
    def _extract_problem_status(self, observation: ET.Element) -> str:
        """Extract problem status from related observations"""
        # Look for entryRelationship with Problem Status observation
        entry_relationships = observation.findall('{urn:hl7-org:v3}entryRelationship[@typeCode="REFR"]')
        
        for rel in entry_relationships:
            status_obs = rel.find('{urn:hl7-org:v3}observation')
            if status_obs is not None:
                # Check if this is a problem status observation
                code_elem = status_obs.find('{urn:hl7-org:v3}code')
                if code_elem is not None and code_elem.get('code') == '33999-4':  # Problem Status LOINC code
                    # Extract status value
                    value_elem = status_obs.find('{urn:hl7-org:v3}value')
                    if value_elem is not None:
                        display_name = value_elem.get('displayName')
                        if display_name:
                            return display_name
                        code = value_elem.get('code')
                        if code:
                            return f"Status code: {code}"
        
        return "Unknown"

    def _get_element_attribute(self, parent: ET.Element, element_path: str, attribute: str) -> Optional[str]:
        """Helper to safely get element attribute"""
        element = parent.find(element_path)
        if element is not None:
            return element.get(attribute)
        return None
    
    def _format_time_period(self, low_value: Optional[str], high_value: Optional[str]) -> str:
        """Format time period from CDA datetime values"""
        if not low_value and not high_value:
            return "Unknown"
            
        formatted_low = self._format_cda_date(low_value) if low_value else "Unknown"
        formatted_high = self._format_cda_date(high_value) if high_value else "Ongoing"
        
        if low_value == high_value:
            return formatted_low
        elif low_value and high_value:
            return f"between {formatted_low} and {formatted_high}"
        elif low_value:
            return f"from {formatted_low}"
        else:
            return f"until {formatted_high}"
    
    def _format_cda_date(self, cda_date: str) -> str:
        """Format CDA date string to readable format"""
        if not cda_date:
            return "Unknown"
            
        try:
            # CDA dates are typically YYYYMMDD or YYYYMMDDHHMMSS
            if len(cda_date) >= 8:
                year = cda_date[:4]
                month = cda_date[4:6]
                day = cda_date[6:8]
                return f"{year}-{month}-{day}"
            else:
                return cda_date
        except:
            return cda_date
    
    def _format_status_code(self, status_code: Optional[str]) -> str:
        """Format status code to readable text"""
        if not status_code:
            return "Unknown"
            
        status_mapping = {
            "completed": "Completed",
            "active": "Active", 
            "suspended": "Suspended",
            "cancelled": "Cancelled",
            "aborted": "Aborted"
        }
        
        return status_mapping.get(status_code.lower(), status_code.capitalize())


def create_history_of_past_illness_extractor() -> HistoryOfPastIllnessExtractor:
    """Factory function to create History of Past Illness extractor"""
    return HistoryOfPastIllnessExtractor()