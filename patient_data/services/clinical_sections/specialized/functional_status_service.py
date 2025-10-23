"""
Functional Status Section Service

Specialized service for functional status section data processing.

Handles:
- Functional status assessments
- Activities of daily living (ADL)
- Instrumental activities of daily living (IADL)  
- Mobility and independence measures

Author: Django_NCP Development Team
Date: October 2025
Version: 1.0.0
"""

import logging
from typing import Dict, List, Any
from django.http import HttpRequest
from ..base.clinical_service_base import ClinicalServiceBase

logger = logging.getLogger(__name__)


class FunctionalStatusSectionService(ClinicalServiceBase):
    """
    Specialized service for functional status section data processing.
    
    Handles:
    - Functional status assessments
    - Activities of daily living (ADL)
    - Instrumental activities of daily living (IADL)
    - Mobility and independence measures
    """
    
    def get_section_code(self) -> str:
        return "47420-5"
    
    def get_section_name(self) -> str:
        return "Functional Status"
    
    def extract_from_session(self, request: HttpRequest, session_id: str) -> List[Dict[str, Any]]:
        """Extract functional status from session storage."""
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        
        # Check for enhanced functional status data
        enhanced_functional_status = match_data.get('enhanced_functional_status', [])
        
        if enhanced_functional_status:
            self._log_extraction_result('extract_from_session', len(enhanced_functional_status), 'Session')
            return enhanced_functional_status
        
        # Check for clinical arrays functional status
        clinical_arrays = match_data.get('enhanced_clinical_data', {}).get('clinical_sections', {})
        functional_status_data = clinical_arrays.get('functional_status', [])
        
        if functional_status_data:
            self._log_extraction_result('extract_from_session', len(functional_status_data), 'Clinical Arrays')
            return functional_status_data
        
        self.logger.info("[FUNCTIONAL STATUS SERVICE] No functional status data found in session")
        return []
    
    def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
        """Extract functional status from CDA content using specialized parsing."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(cda_content)
            
            # Find functional status section using base method
            section = self._find_section_by_code(root, ['47420-5', '47109-7'])
            
            if section is not None:
                functional_status = self._parse_functional_status_xml(section)
                self._log_extraction_result('extract_from_cda', len(functional_status), 'CDA')
                return functional_status
            
            self.logger.info("[FUNCTIONAL STATUS SERVICE] No functional status section found in CDA")
            return []
            
        except Exception as e:
            self.logger.error(f"[FUNCTIONAL STATUS SERVICE] Error extracting functional status from CDA: {e}")
            return []
    
    def enhance_and_store(self, request: HttpRequest, session_id: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance functional status data and store in session."""
        enhanced_functional_status = []
        
        for status_data in raw_data:
            enhanced_status = {
                'name': self._extract_field_value(status_data, 'assessment', 'Functional assessment'),
                'display_name': self._extract_field_value(status_data, 'assessment', 'Functional assessment'),
                'assessment': self._extract_field_value(status_data, 'assessment', 'General assessment'),
                'category': self._extract_field_value(status_data, 'category', 'ADL'),
                'score': self._extract_field_value(status_data, 'score', 'Not specified'),
                'level': self._extract_field_value(status_data, 'level', 'Not specified'),
                'independence': self._extract_field_value(status_data, 'independence', 'Not specified'),
                'assistance_required': self._extract_field_value(status_data, 'assistance_required', 'Not specified'),
                'assessment_date': self._format_cda_date(self._extract_field_value(status_data, 'assessment_date', 'Not specified')),
                'source': 'cda_extraction_enhanced'
            }
            enhanced_functional_status.append(enhanced_status)
        
        # Store in session
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        match_data['enhanced_functional_status'] = enhanced_functional_status
        request.session[session_key] = match_data
        request.session.modified = True
        
        self.logger.info(f"[FUNCTIONAL STATUS SERVICE] Enhanced and stored {len(enhanced_functional_status)} functional status assessments")
        return enhanced_functional_status
    
    def get_template_data(self, enhanced_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert enhanced functional status to template-ready format."""
        return {
            'items': enhanced_data,
            'metadata': {
                'section_name': 'Functional Status',
                'section_code': '47420-5',
                'item_count': len(enhanced_data),
                'has_items': len(enhanced_data) > 0,
                'template_pattern': 'direct_field_access'  # status.field_name
            }
        }
    
    def _parse_functional_status_xml(self, section) -> List[Dict[str, Any]]:
        """Parse functional status section XML into structured data."""
        functional_status = []
        
        entries = section.findall('.//hl7:entry', self.namespaces)
        for entry in entries:
            observation = entry.find('.//hl7:observation', self.namespaces)
            if observation is not None:
                status = self._parse_status_observation(observation)
                if status:
                    functional_status.append(status)
        
        return functional_status
    
    def _parse_status_observation(self, observation) -> Dict[str, Any]:
        """Parse functional status observation into structured data."""
        # Extract assessment type from code
        code_elem = observation.find('hl7:code', self.namespaces)
        assessment = "General assessment"
        category = "ADL"
        
        if code_elem is not None:
            code = code_elem.get('code', '')
            display_name = code_elem.get('displayName', '')
            
            # Map common functional status codes to categories
            if code in ['57267-9', '83254-7']:  # Activities of daily living
                category = "ADL"
                assessment = "Activities of Daily Living"
            elif code in ['57266-1', '83255-4']:  # Instrumental ADL
                category = "IADL"
                assessment = "Instrumental Activities of Daily Living"
            elif code in ['72133-2', '72134-0']:  # Mobility
                category = "Mobility"
                assessment = "Mobility Assessment"
            elif code in ['72101-9', '72102-7']:  # Cognitive function
                category = "Cognitive"
                assessment = "Cognitive Function"
            else:
                assessment = display_name or "General assessment"
        
        # Extract score/value
        score = "Not specified"
        level = "Not specified"
        value_elem = observation.find('hl7:value', self.namespaces)
        if value_elem is not None:
            if value_elem.get('xsi:type') == 'PQ':  # Physical quantity (numeric score)
                score = f"{value_elem.get('value', '')} {value_elem.get('unit', '')}"
            else:
                level = value_elem.get('displayName', value_elem.get('code', 'Not specified'))
        
        # Extract assessment date
        assessment_date = "Not specified"
        effective_time = observation.find('hl7:effectiveTime', self.namespaces)
        if effective_time is not None:
            assessment_date = effective_time.get('value', 'Not specified')
        
        # Determine independence level based on score or level
        independence = "Not specified"
        assistance_required = "Not specified"
        
        if level != "Not specified":
            if "independent" in level.lower():
                independence = "Independent"
                assistance_required = "None"
            elif "dependent" in level.lower():
                independence = "Dependent"
                assistance_required = "Full assistance"
            elif "partial" in level.lower() or "assist" in level.lower():
                independence = "Partially dependent"
                assistance_required = "Partial assistance"
        
        return {
            'assessment': assessment,
            'category': category,
            'score': score,
            'level': level,
            'independence': independence,
            'assistance_required': assistance_required,
            'assessment_date': assessment_date
        }