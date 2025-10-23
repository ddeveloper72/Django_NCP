"""
Past Illness Section Service

Specialized service for history of past illness section data processing.

Handles:
- History of past illness
- Previous medical conditions
- Resolved conditions
- Historical clinical context

Author: Django_NCP Development Team
Date: October 2025
Version: 1.0.0
"""

import logging
from typing import Dict, List, Any
from django.http import HttpRequest
from ..base.clinical_service_base import ClinicalServiceBase

logger = logging.getLogger(__name__)


class PastIllnessSectionService(ClinicalServiceBase):
    """
    Specialized service for history of past illness section data processing.
    
    Handles:
    - History of past illness
    - Previous medical conditions
    - Resolved conditions
    - Historical clinical context
    """
    
    def get_section_code(self) -> str:
        return "11348-0"
    
    def get_section_name(self) -> str:
        return "Past Illness"
    
    def extract_from_session(self, request: HttpRequest, session_id: str) -> List[Dict[str, Any]]:
        """Extract past illness from session storage."""
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        
        # Check for enhanced past illness data
        enhanced_past_illness = match_data.get('enhanced_past_illness', [])
        
        if enhanced_past_illness:
            self._log_extraction_result('extract_from_session', len(enhanced_past_illness), 'Session')
            return enhanced_past_illness
        
        # Check for clinical arrays past illness
        clinical_arrays = match_data.get('enhanced_clinical_data', {}).get('clinical_sections', {})
        past_illness_data = clinical_arrays.get('past_illness', [])
        
        if past_illness_data:
            self._log_extraction_result('extract_from_session', len(past_illness_data), 'Clinical Arrays')
            return past_illness_data
        
        self.logger.info("[PAST ILLNESS SERVICE] No past illness data found in session")
        return []
    
    def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
        """Extract past illness from CDA content using specialized parsing."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(cda_content)
            
            # Find past illness section using base method
            section = self._find_section_by_code(root, ['11348-0', '11450-4'])
            
            if section is not None:
                past_illnesses = self._parse_past_illness_xml(section)
                self._log_extraction_result('extract_from_cda', len(past_illnesses), 'CDA')
                return past_illnesses
            
            self.logger.info("[PAST ILLNESS SERVICE] No past illness section found in CDA")
            return []
            
        except Exception as e:
            self.logger.error(f"[PAST ILLNESS SERVICE] Error extracting past illness from CDA: {e}")
            return []
    
    def enhance_and_store(self, request: HttpRequest, session_id: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance past illness data and store in session."""
        enhanced_past_illness = []
        
        for illness_data in raw_data:
            enhanced_illness = {
                'name': self._extract_field_value(illness_data, 'condition', 'Unknown condition'),
                'display_name': self._extract_field_value(illness_data, 'condition', 'Unknown condition'),
                'condition': self._extract_field_value(illness_data, 'condition', 'Unknown condition'),
                'onset_date': self._format_cda_date(self._extract_field_value(illness_data, 'onset_date', 'Not specified')),
                'resolution_date': self._format_cda_date(self._extract_field_value(illness_data, 'resolution_date', 'Not specified')),
                'status': self._extract_field_value(illness_data, 'status', 'Resolved'),
                'severity': self._extract_field_value(illness_data, 'severity', 'Not specified'),
                'clinical_status': self._extract_field_value(illness_data, 'clinical_status', 'Inactive'),
                'verification_status': self._extract_field_value(illness_data, 'verification_status', 'Confirmed'),
                'source': 'cda_extraction_enhanced'
            }
            enhanced_past_illness.append(enhanced_illness)
        
        # Store in session
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        match_data['enhanced_past_illness'] = enhanced_past_illness
        request.session[session_key] = match_data
        request.session.modified = True
        
        self.logger.info(f"[PAST ILLNESS SERVICE] Enhanced and stored {len(enhanced_past_illness)} past illness records")
        return enhanced_past_illness
    
    def get_template_data(self, enhanced_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert enhanced past illness to template-ready format."""
        return {
            'items': enhanced_data,
            'metadata': {
                'section_name': 'Past Illness',
                'section_code': '11348-0',
                'item_count': len(enhanced_data),
                'has_items': len(enhanced_data) > 0,
                'template_pattern': 'direct_field_access'  # illness.field_name
            }
        }
    
    def _parse_past_illness_xml(self, section) -> List[Dict[str, Any]]:
        """Parse past illness section XML into structured data."""
        past_illnesses = []
        
        entries = section.findall('.//hl7:entry', self.namespaces)
        for entry in entries:
            observation = entry.find('.//hl7:observation', self.namespaces)
            if observation is not None:
                illness = self._parse_illness_observation(observation)
                if illness:
                    past_illnesses.append(illness)
        
        return past_illnesses
    
    def _parse_illness_observation(self, observation) -> Dict[str, Any]:
        """Parse past illness observation into structured data."""
        # Extract condition name
        value_elem = observation.find('hl7:value', self.namespaces)
        condition = "Unknown condition"
        if value_elem is not None:
            condition = value_elem.get('displayName', value_elem.get('code', 'Unknown condition'))
        
        # Extract onset date
        onset_date = "Not specified"
        effective_time = observation.find('hl7:effectiveTime', self.namespaces)
        if effective_time is not None:
            low_elem = effective_time.find('hl7:low', self.namespaces)
            if low_elem is not None:
                onset_date = low_elem.get('value', 'Not specified')
            else:
                onset_date = effective_time.get('value', 'Not specified')
        
        # Extract resolution date
        resolution_date = "Not specified"
        if effective_time is not None:
            high_elem = effective_time.find('hl7:high', self.namespaces)
            if high_elem is not None:
                resolution_date = high_elem.get('value', 'Not specified')
        
        # Extract status
        status_elem = observation.find('hl7:statusCode', self.namespaces)
        status = "Resolved"
        if status_elem is not None:
            status = status_elem.get('code', 'Resolved')
        
        return {
            'condition': condition,
            'onset_date': onset_date,
            'resolution_date': resolution_date,
            'status': status,
            'severity': 'Not specified',
            'clinical_status': 'Inactive',
            'verification_status': 'Confirmed'
        }