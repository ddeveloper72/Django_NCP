"""
Allergies Section Service

Specialized service for allergies and adverse reactions section data processing.

Handles:
- Allergies and adverse reactions
- Allergy severity and criticality
- Reaction manifestations
- Substance identification

Author: Django_NCP Development Team
Date: October 2025
Version: 1.0.0
"""

import logging
from typing import Dict, List, Any
from django.http import HttpRequest
from ..base.clinical_service_base import ClinicalServiceBase

logger = logging.getLogger(__name__)


class AllergiesSectionService(ClinicalServiceBase):
    """
    Specialized service for allergies and adverse reactions section data processing.
    
    Handles:
    - Allergies and adverse reactions
    - Allergy severity and criticality
    - Reaction manifestations  
    - Substance identification
    """
    
    def get_section_code(self) -> str:
        return "48765-2"
    
    def get_section_name(self) -> str:
        return "Allergies"
    
    def extract_from_session(self, request: HttpRequest, session_id: str) -> List[Dict[str, Any]]:
        """Extract allergies from session storage."""
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        
        # Check for enhanced allergies data
        enhanced_allergies = match_data.get('enhanced_allergies', [])
        
        if enhanced_allergies:
            self._log_extraction_result('extract_from_session', len(enhanced_allergies), 'Session')
            return enhanced_allergies
        
        # Check for clinical arrays allergies
        clinical_arrays = match_data.get('enhanced_clinical_data', {}).get('clinical_sections', {})
        allergies_data = clinical_arrays.get('allergies', [])
        
        if allergies_data:
            self._log_extraction_result('extract_from_session', len(allergies_data), 'Clinical Arrays')
            return allergies_data
        
        self.logger.info("[ALLERGIES SERVICE] No allergies data found in session")
        return []
    
    def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
        """Extract allergies from CDA content using specialized parsing."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(cda_content)
            
            # Find allergies section using base method
            section = self._find_section_by_code(root, ['48765-2', '10155-0'])
            
            if section is not None:
                allergies = self._parse_allergies_xml(section)
                self._log_extraction_result('extract_from_cda', len(allergies), 'CDA')
                return allergies
            
            self.logger.info("[ALLERGIES SERVICE] No allergies section found in CDA")
            return []
            
        except Exception as e:
            self.logger.error(f"[ALLERGIES SERVICE] Error extracting allergies from CDA: {e}")
            return []
    
    def enhance_and_store(self, request: HttpRequest, session_id: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance allergies data and store in session."""
        enhanced_allergies = []
        
        for allergy_data in raw_data:
            enhanced_allergy = {
                'name': self._extract_field_value(allergy_data, 'substance', 'Unknown allergen'),
                'display_name': self._extract_field_value(allergy_data, 'substance', 'Unknown allergen'),
                'substance': self._extract_field_value(allergy_data, 'substance', 'Unknown allergen'),
                'reaction': self._extract_field_value(allergy_data, 'reaction', 'Not specified'),
                'severity': self._extract_field_value(allergy_data, 'severity', 'Not specified'),
                'criticality': self._extract_field_value(allergy_data, 'criticality', 'Not specified'),
                'onset_date': self._format_cda_date(self._extract_field_value(allergy_data, 'onset_date', 'Not specified')),
                'status': self._extract_field_value(allergy_data, 'status', 'Active'),
                'verification_status': self._extract_field_value(allergy_data, 'verification_status', 'Confirmed'),
                'source': 'cda_extraction_enhanced'
            }
            enhanced_allergies.append(enhanced_allergy)
        
        # Store in session
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        match_data['enhanced_allergies'] = enhanced_allergies
        request.session[session_key] = match_data
        request.session.modified = True
        
        self.logger.info(f"[ALLERGIES SERVICE] Enhanced and stored {len(enhanced_allergies)} allergies")
        return enhanced_allergies
    
    def get_template_data(self, enhanced_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert enhanced allergies to template-ready format."""
        return {
            'items': enhanced_data,
            'metadata': {
                'section_name': 'Allergies',
                'section_code': '48765-2',
                'item_count': len(enhanced_data),
                'has_items': len(enhanced_data) > 0,
                'template_pattern': 'direct_field_access'  # allergy.field_name
            }
        }
    
    def _parse_allergies_xml(self, section) -> List[Dict[str, Any]]:
        """Parse allergies section XML into structured data."""
        allergies = []
        
        entries = section.findall('.//hl7:entry', self.namespaces)
        for entry in entries:
            observation = entry.find('.//hl7:observation', self.namespaces)
            if observation is not None:
                allergy = self._parse_allergy_observation(observation)
                if allergy:
                    allergies.append(allergy)
        
        return allergies
    
    def _parse_allergy_observation(self, observation) -> Dict[str, Any]:
        """Parse allergy observation into structured data."""
        # Extract allergen substance
        participant = observation.find('.//hl7:participant', self.namespaces)
        substance = "Unknown allergen"
        if participant is not None:
            role = participant.find('.//hl7:participantRole', self.namespaces)
            if role is not None:
                entity = role.find('.//hl7:playingEntity', self.namespaces)
                if entity is not None:
                    code_elem = entity.find('hl7:code', self.namespaces)
                    if code_elem is not None:
                        substance = code_elem.get('displayName', code_elem.get('code', 'Unknown allergen'))
        
        # Extract reaction manifestation
        value_elem = observation.find('hl7:value', self.namespaces)
        reaction = "Not specified"
        if value_elem is not None:
            reaction = value_elem.get('displayName', value_elem.get('code', 'Not specified'))
        
        # Extract severity
        severity = "Not specified"
        severity_obs = observation.find('.//hl7:observation[hl7:code/@code="SEV"]', self.namespaces)
        if severity_obs is not None:
            severity_value = severity_obs.find('hl7:value', self.namespaces)
            if severity_value is not None:
                severity = severity_value.get('displayName', severity_value.get('code', 'Not specified'))
        
        # Extract status
        status_elem = observation.find('hl7:statusCode', self.namespaces)
        status = "Active"
        if status_elem is not None:
            status = status_elem.get('code', 'Active')
        
        return {
            'substance': substance,
            'reaction': reaction,
            'severity': severity,
            'criticality': 'Not specified',
            'onset_date': 'Not specified',
            'status': status,
            'verification_status': 'Confirmed'
        }