"""
Pregnancy History Section Service

Specialized service for history of pregnancies section data processing.

Handles:
- Pregnancy history
- Obstetric history
- Pregnancy outcomes
- Gestational information

Author: Django_NCP Development Team
Date: October 2025
Version: 1.0.0
"""

import logging
from typing import Dict, List, Any
from django.http import HttpRequest
from ..base.clinical_service_base import ClinicalServiceBase

logger = logging.getLogger(__name__)


class PregnancyHistorySectionService(ClinicalServiceBase):
    """
    Specialized service for history of pregnancies section data processing.
    
    Handles:
    - Pregnancy history
    - Obstetric history
    - Pregnancy outcomes
    - Gestational information
    """
    
    def get_section_code(self) -> str:
        return "10162-6"
    
    def get_section_name(self) -> str:
        return "Pregnancy History"
    
    def extract_from_session(self, request: HttpRequest, session_id: str) -> List[Dict[str, Any]]:
        """Extract pregnancy history from session storage."""
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        
        # Check for enhanced pregnancy history data
        enhanced_pregnancy = match_data.get('enhanced_pregnancy_history', [])
        
        if enhanced_pregnancy:
            self._log_extraction_result('extract_from_session', len(enhanced_pregnancy), 'Session')
            return enhanced_pregnancy
        
        # Check for clinical arrays pregnancy history
        clinical_arrays = match_data.get('enhanced_clinical_data', {}).get('clinical_sections', {})
        pregnancy_data = clinical_arrays.get('pregnancy_history', [])
        
        if pregnancy_data:
            self._log_extraction_result('extract_from_session', len(pregnancy_data), 'Clinical Arrays')
            return pregnancy_data
        
        self.logger.info("[PREGNANCY HISTORY SERVICE] No pregnancy history data found in session")
        return []
    
    def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
        """Extract pregnancy history from CDA content using specialized parsing."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(cda_content)
            
            # Find pregnancy history section using base method
            section = self._find_section_by_code(root, ['10162-6', '10155-0'])
            
            if section is not None:
                pregnancies = self._parse_pregnancy_xml(section)
                self._log_extraction_result('extract_from_cda', len(pregnancies), 'CDA')
                return pregnancies
            
            self.logger.info("[PREGNANCY HISTORY SERVICE] No pregnancy history section found in CDA")
            return []
            
        except Exception as e:
            self.logger.error(f"[PREGNANCY HISTORY SERVICE] Error extracting pregnancy history from CDA: {e}")
            return []
    
    def enhance_and_store(self, request: HttpRequest, session_id: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance pregnancy history data and store in session."""
        enhanced_pregnancies = []
        
        for pregnancy_data in raw_data:
            enhanced_pregnancy = {
                'name': self._extract_field_value(pregnancy_data, 'description', 'Pregnancy record'),
                'display_name': self._extract_field_value(pregnancy_data, 'description', 'Pregnancy record'),
                'pregnancy_number': self._extract_field_value(pregnancy_data, 'pregnancy_number', 'Not specified'),
                'outcome': self._extract_field_value(pregnancy_data, 'outcome', 'Not specified'),
                'gestational_age': self._extract_field_value(pregnancy_data, 'gestational_age', 'Not specified'),
                'delivery_date': self._format_cda_date(self._extract_field_value(pregnancy_data, 'delivery_date', 'Not specified')),
                'birth_weight': self._extract_field_value(pregnancy_data, 'birth_weight', 'Not specified'),
                'complications': self._extract_field_value(pregnancy_data, 'complications', 'None reported'),
                'delivery_method': self._extract_field_value(pregnancy_data, 'delivery_method', 'Not specified'),
                'source': 'cda_extraction_enhanced'
            }
            enhanced_pregnancies.append(enhanced_pregnancy)
        
        # Store in session
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        match_data['enhanced_pregnancy_history'] = enhanced_pregnancies
        request.session[session_key] = match_data
        request.session.modified = True
        
        self.logger.info(f"[PREGNANCY HISTORY SERVICE] Enhanced and stored {len(enhanced_pregnancies)} pregnancy records")
        return enhanced_pregnancies
    
    def get_template_data(self, enhanced_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert enhanced pregnancy history to template-ready format."""
        return {
            'items': enhanced_data,
            'metadata': {
                'section_name': 'Pregnancy History',
                'section_code': '10162-6',
                'item_count': len(enhanced_data),
                'has_items': len(enhanced_data) > 0,
                'template_pattern': 'direct_field_access'  # pregnancy.field_name
            }
        }
    
    def _parse_pregnancy_xml(self, section) -> List[Dict[str, Any]]:
        """Parse pregnancy history section XML into structured data."""
        pregnancies = []
        
        entries = section.findall('.//hl7:entry', self.namespaces)
        for entry in entries:
            observation = entry.find('.//hl7:observation', self.namespaces)
            if observation is not None:
                pregnancy = self._parse_pregnancy_observation(observation)
                if pregnancy:
                    pregnancies.append(pregnancy)
        
        return pregnancies
    
    def _parse_pregnancy_observation(self, observation) -> Dict[str, Any]:
        """Parse pregnancy observation into structured data."""
        # Extract pregnancy outcome
        value_elem = observation.find('hl7:value', self.namespaces)
        outcome = "Not specified"
        if value_elem is not None:
            outcome = value_elem.get('displayName', value_elem.get('code', 'Not specified'))
        
        # Extract delivery date
        delivery_date = "Not specified"
        effective_time = observation.find('hl7:effectiveTime', self.namespaces)
        if effective_time is not None:
            delivery_date = effective_time.get('value', 'Not specified')
        
        # Extract gestational age and birth weight from related observations
        gestational_age = "Not specified"
        birth_weight = "Not specified"
        
        # Look for related observations in the same entry
        entry = observation.getparent()
        if entry is not None:
            related_observations = entry.findall('.//hl7:observation', self.namespaces)
            for obs in related_observations:
                code_elem = obs.find('hl7:code', self.namespaces)
                if code_elem is not None:
                    code = code_elem.get('code', '')
                    if code in ['11884-4', '18185-9']:  # Gestational age codes
                        val_elem = obs.find('hl7:value', self.namespaces)
                        if val_elem is not None:
                            gestational_age = f"{val_elem.get('value', '')} {val_elem.get('unit', 'weeks')}"
                    elif code in ['8339-4', '3141-9']:  # Birth weight codes
                        val_elem = obs.find('hl7:value', self.namespaces)
                        if val_elem is not None:
                            birth_weight = f"{val_elem.get('value', '')} {val_elem.get('unit', 'g')}"
        
        return {
            'description': f"Pregnancy with outcome: {outcome}",
            'pregnancy_number': 'Not specified',
            'outcome': outcome,
            'gestational_age': gestational_age,
            'delivery_date': delivery_date,
            'birth_weight': birth_weight,
            'complications': 'None reported',
            'delivery_method': 'Not specified'
        }