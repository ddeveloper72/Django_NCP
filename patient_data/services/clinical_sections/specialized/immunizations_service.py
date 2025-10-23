"""
Immunizations Section Service

Specialized service for immunizations section data processing.

Handles:
- Vaccination records
- Immunization history
- Vaccine details
- Administration information

Author: Django_NCP Development Team
Date: October 2025
Version: 1.0.0
"""

import logging
from typing import Dict, List, Any
from django.http import HttpRequest
from ..base.clinical_service_base import ClinicalServiceBase

logger = logging.getLogger(__name__)


class ImmunizationsSectionService(ClinicalServiceBase):
    """
    Specialized service for immunizations section data processing.
    
    Handles:
    - Vaccination records
    - Immunization history
    - Vaccine details
    - Administration information
    """
    
    def get_section_code(self) -> str:
        return "11369-6"
    
    def get_section_name(self) -> str:
        return "Immunizations"
    
    def extract_from_session(self, request: HttpRequest, session_id: str) -> List[Dict[str, Any]]:
        """Extract immunizations from session storage."""
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        
        enhanced_immunizations = match_data.get('enhanced_immunizations', [])
        
        if enhanced_immunizations:
            self._log_extraction_result('extract_from_session', len(enhanced_immunizations), 'Session')
            return enhanced_immunizations
        
        clinical_arrays = match_data.get('enhanced_clinical_data', {}).get('clinical_sections', {})
        immunizations_data = clinical_arrays.get('immunizations', [])
        
        if immunizations_data:
            self._log_extraction_result('extract_from_session', len(immunizations_data), 'Clinical Arrays')
            return immunizations_data
        
        self.logger.info("[IMMUNIZATIONS SERVICE] No immunizations data found in session")
        return []
    
    def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
        """Extract immunizations from CDA content using specialized parsing."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(cda_content)
            
            # Find immunizations section using base method
            section = self._find_section_by_code(root, ['11369-6'])
            
            if section is not None:
                immunizations = self._parse_immunizations_xml(section)
                self._log_extraction_result('extract_from_cda', len(immunizations), 'CDA')
                return immunizations
            
            self.logger.info("[IMMUNIZATIONS SERVICE] No immunizations section found in CDA")
            return []
            
        except Exception as e:
            self.logger.error(f"[IMMUNIZATIONS SERVICE] Error extracting immunizations from CDA: {e}")
            return []
    
    def enhance_and_store(self, request: HttpRequest, session_id: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance immunizations data and store in session."""
        enhanced_immunizations = []
        
        for immunization_data in raw_data:
            enhanced_immunization = {
                'name': self._extract_field_value(immunization_data, 'name', 'Unknown vaccine'),
                'display_name': self._extract_field_value(immunization_data, 'name', 'Unknown vaccine'),
                'date_administered': self._format_cda_date(self._extract_field_value(immunization_data, 'date_administered', 'Not specified')),
                'dose_number': self._extract_field_value(immunization_data, 'dose_number', 'Not specified'),
                'manufacturer': self._extract_field_value(immunization_data, 'manufacturer', 'Not specified'),
                'lot_number': self._extract_field_value(immunization_data, 'lot_number', 'Not specified'),
                'route': self._extract_field_value(immunization_data, 'route', 'Not specified'),
                'site': self._extract_field_value(immunization_data, 'site', 'Not specified'),
                'source': 'cda_extraction_enhanced'
            }
            enhanced_immunizations.append(enhanced_immunization)
        
        # Store in session
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        match_data['enhanced_immunizations'] = enhanced_immunizations
        request.session[session_key] = match_data
        request.session.modified = True
        
        self.logger.info(f"[IMMUNIZATIONS SERVICE] Enhanced and stored {len(enhanced_immunizations)} immunizations")
        return enhanced_immunizations
    
    def get_template_data(self, enhanced_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert enhanced immunizations to template-ready format."""
        return {
            'items': enhanced_data,
            'metadata': {
                'section_name': 'Immunizations',
                'section_code': '11369-6',
                'item_count': len(enhanced_data),
                'has_items': len(enhanced_data) > 0,
                'template_pattern': 'direct_field_access'  # immunization.field_name
            }
        }
    
    def _parse_immunizations_xml(self, section) -> List[Dict[str, Any]]:
        """Parse immunizations section XML into structured data."""
        immunizations = []
        
        entries = section.findall('.//hl7:entry', self.namespaces)
        for entry in entries:
            substance_admin = entry.find('.//hl7:substanceAdministration', self.namespaces)
            if substance_admin is not None:
                immunization = self._parse_immunization_element(substance_admin)
                if immunization:
                    immunizations.append(immunization)
        
        return immunizations
    
    def _parse_immunization_element(self, substance_admin) -> Dict[str, Any]:
        """Parse immunization element into structured data."""
        # Extract vaccine name
        consumable = substance_admin.find('.//hl7:consumable', self.namespaces)
        name = "Unknown vaccine"
        if consumable is not None:
            material = consumable.find('.//hl7:manufacturedMaterial', self.namespaces)
            if material is not None:
                code_elem = material.find('hl7:code', self.namespaces)
                if code_elem is not None:
                    name = code_elem.get('displayName', code_elem.get('code', 'Unknown vaccine'))
        
        # Extract date
        time_elem = substance_admin.find('hl7:effectiveTime', self.namespaces)
        date = "Not specified"
        if time_elem is not None:
            date = time_elem.get('value', 'Not specified')
        
        # Extract route
        route_elem = substance_admin.find('.//hl7:routeCode', self.namespaces)
        route = "Not specified"
        if route_elem is not None:
            route = route_elem.get('displayName', route_elem.get('code', 'Not specified'))
        
        return {
            'name': name,
            'date_administered': date,
            'dose_number': 'Not specified',
            'manufacturer': 'Not specified',
            'lot_number': 'Not specified',
            'route': route,
            'site': 'Not specified'
        }