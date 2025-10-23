"""
Vital Signs Section Service

Specialized service for vital signs and physical findings section data processing.

Handles:
- Vital signs measurements
- Physical examination findings  
- Laboratory values
- Clinical observations

Author: Django_NCP Development Team
Date: October 2025
Version: 1.0.0
"""

import logging
from typing import Dict, List, Any
from django.http import HttpRequest
from ..base.clinical_service_base import ClinicalServiceBase

logger = logging.getLogger(__name__)


class VitalSignsSectionService(ClinicalServiceBase):
    """
    Specialized service for vital signs and physical findings section data processing.
    
    Handles:
    - Vital signs measurements
    - Physical examination findings
    - Laboratory values
    - Clinical observations
    """
    
    def get_section_code(self) -> str:
        return "8716-3"
    
    def get_section_name(self) -> str:
        return "Vital Signs"
    
    def extract_from_session(self, request: HttpRequest, session_id: str) -> List[Dict[str, Any]]:
        """Extract vital signs from session storage."""
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        
        enhanced_vitals = match_data.get('enhanced_vital_signs', [])
        
        if enhanced_vitals:
            self._log_extraction_result('extract_from_session', len(enhanced_vitals), 'Session')
            return enhanced_vitals
        
        clinical_arrays = match_data.get('enhanced_clinical_data', {}).get('clinical_sections', {})
        vitals_data = clinical_arrays.get('vital_signs', [])
        
        if vitals_data:
            self._log_extraction_result('extract_from_session', len(vitals_data), 'Clinical Arrays')
            return vitals_data
        
        self.logger.info("[VITAL SIGNS SERVICE] No vital signs data found in session")
        return []
    
    def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
        """Extract vital signs from CDA content using specialized parsing."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(cda_content)
            
            # Find vital signs section using base method
            section = self._find_section_by_code(root, ['8716-3', '29545-1'])
            
            if section is not None:
                vitals = self._parse_vitals_xml(section)
                self._log_extraction_result('extract_from_cda', len(vitals), 'CDA')
                return vitals
            
            self.logger.info("[VITAL SIGNS SERVICE] No vital signs section found in CDA")
            return []
            
        except Exception as e:
            self.logger.error(f"[VITAL SIGNS SERVICE] Error extracting vital signs from CDA: {e}")
            return []
    
    def enhance_and_store(self, request: HttpRequest, session_id: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance vital signs data and store in session."""
        enhanced_vitals = []
        
        for vital_data in raw_data:
            enhanced_vital = {
                'name': self._extract_field_value(vital_data, 'name', 'Unknown measurement'),
                'display_name': self._extract_field_value(vital_data, 'name', 'Unknown measurement'),
                'value': self._extract_field_value(vital_data, 'value', 'Not specified'),
                'unit': self._extract_field_value(vital_data, 'unit', ''),
                'date': self._format_cda_date(self._extract_field_value(vital_data, 'date', 'Not specified')),
                'status': self._extract_field_value(vital_data, 'status', 'Final'),
                'reference_range': self._extract_field_value(vital_data, 'reference_range', ''),
                'source': 'cda_extraction_enhanced'
            }
            enhanced_vitals.append(enhanced_vital)
        
        # Store in session
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        match_data['enhanced_vital_signs'] = enhanced_vitals
        request.session[session_key] = match_data
        request.session.modified = True
        
        self.logger.info(f"[VITAL SIGNS SERVICE] Enhanced and stored {len(enhanced_vitals)} vital signs")
        return enhanced_vitals
    
    def get_template_data(self, enhanced_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert enhanced vital signs to template-ready format."""
        return {
            'items': enhanced_data,
            'metadata': {
                'section_name': 'Vital Signs',
                'section_code': '8716-3',
                'item_count': len(enhanced_data),
                'has_items': len(enhanced_data) > 0,
                'template_pattern': 'direct_field_access'  # vital.field_name
            }
        }
    
    def _parse_vitals_xml(self, section) -> List[Dict[str, Any]]:
        """Parse vital signs section XML into structured data."""
        vitals = []
        
        entries = section.findall('.//hl7:entry', self.namespaces)
        for entry in entries:
            observation = entry.find('.//hl7:observation', self.namespaces)
            if observation is not None:
                vital = self._parse_vital_observation(observation)
                if vital:
                    vitals.append(vital)
        
        return vitals
    
    def _parse_vital_observation(self, observation) -> Dict[str, Any]:
        """Parse vital sign observation into structured data."""
        # Extract measurement name
        code_elem = observation.find('hl7:code', self.namespaces)
        name = "Unknown measurement"
        if code_elem is not None:
            name = code_elem.get('displayName', code_elem.get('code', 'Unknown measurement'))
        
        # Extract value and unit
        value_elem = observation.find('hl7:value', self.namespaces)
        value = "Not specified"
        unit = ""
        if value_elem is not None:
            value = value_elem.get('value', 'Not specified')
            unit = value_elem.get('unit', '')
        
        # Extract date
        time_elem = observation.find('hl7:effectiveTime', self.namespaces)
        date = "Not specified"
        if time_elem is not None:
            date = time_elem.get('value', 'Not specified')
        
        return {
            'name': name,
            'value': value,
            'unit': unit,
            'date': date,
            'status': 'Final',
            'reference_range': ''
        }