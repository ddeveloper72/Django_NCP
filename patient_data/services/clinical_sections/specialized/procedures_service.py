"""
Procedures Section Service

Specialized service for procedures section data processing.

Handles:
- Surgical procedures
- Medical procedures
- Diagnostic procedures  
- Interventions

Author: Django_NCP Development Team
Date: October 2025
Version: 1.0.0
"""

import logging
from typing import Dict, List, Any
from django.http import HttpRequest
from ..base.clinical_service_base import ClinicalServiceBase

logger = logging.getLogger(__name__)


class ProceduresSectionService(ClinicalServiceBase):
    """
    Specialized service for procedures section data processing.
    
    Handles:
    - Surgical procedures
    - Medical procedures  
    - Diagnostic procedures
    - Interventions
    """
    
    def get_section_code(self) -> str:
        return "47519-4"
    
    def get_section_name(self) -> str:
        return "Procedures"
    
    def extract_from_session(self, request: HttpRequest, session_id: str) -> List[Dict[str, Any]]:
        """Extract procedures from session storage."""
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        
        enhanced_procedures = match_data.get('enhanced_procedures', [])
        
        if enhanced_procedures:
            self._log_extraction_result('extract_from_session', len(enhanced_procedures), 'Session')
            return enhanced_procedures
        
        clinical_arrays = match_data.get('enhanced_clinical_data', {}).get('clinical_sections', {})
        procedures_data = clinical_arrays.get('procedures', [])
        
        if procedures_data:
            self._log_extraction_result('extract_from_session', len(procedures_data), 'Clinical Arrays')
            return procedures_data
        
        self.logger.info("[PROCEDURES SERVICE] No procedures data found in session")
        return []
    
    def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
        """Extract procedures from CDA content using specialized parsing."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(cda_content)
            
            # Find procedures section using base method
            section = self._find_section_by_code(root, ['47519-4'])
            
            if section is not None:
                procedures = self._parse_procedures_xml(section)
                self._log_extraction_result('extract_from_cda', len(procedures), 'CDA')
                return procedures
            
            self.logger.info("[PROCEDURES SERVICE] No procedures section found in CDA")
            return []
            
        except Exception as e:
            self.logger.error(f"[PROCEDURES SERVICE] Error extracting procedures from CDA: {e}")
            return []
    
    def enhance_and_store(self, request: HttpRequest, session_id: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance procedures data and store in session."""
        enhanced_procedures = []
        
        for procedure_data in raw_data:
            enhanced_procedure = {
                'name': self._extract_field_value(procedure_data, 'name', 'Unknown procedure'),
                'display_name': self._extract_field_value(procedure_data, 'name', 'Unknown procedure'),
                'date': self._format_cda_date(self._extract_field_value(procedure_data, 'date', 'Not specified')),
                'provider': self._extract_field_value(procedure_data, 'provider', 'Not specified'),
                'location': self._extract_field_value(procedure_data, 'location', 'Not specified'),
                'status': self._extract_field_value(procedure_data, 'status', 'Completed'),
                'indication': self._extract_field_value(procedure_data, 'indication', 'Not specified'),
                'source': 'cda_extraction_enhanced'
            }
            enhanced_procedures.append(enhanced_procedure)
        
        # Store in session
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        match_data['enhanced_procedures'] = enhanced_procedures
        request.session[session_key] = match_data
        request.session.modified = True
        
        self.logger.info(f"[PROCEDURES SERVICE] Enhanced and stored {len(enhanced_procedures)} procedures")
        return enhanced_procedures
    
    def get_template_data(self, enhanced_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert enhanced procedures to template-ready format."""
        return {
            'items': enhanced_data,
            'metadata': {
                'section_name': 'Procedures',
                'section_code': '47519-4',
                'item_count': len(enhanced_data),
                'has_items': len(enhanced_data) > 0,
                'template_pattern': 'direct_field_access'  # procedure.field_name
            }
        }
    
    def _parse_procedures_xml(self, section) -> List[Dict[str, Any]]:
        """Parse procedures section XML into structured data."""
        procedures = []
        
        entries = section.findall('.//hl7:entry', self.namespaces)
        for entry in entries:
            procedure_elem = entry.find('.//hl7:procedure', self.namespaces)
            if procedure_elem is not None:
                procedure = self._parse_procedure_element(procedure_elem)
                if procedure:
                    procedures.append(procedure)
        
        return procedures
    
    def _parse_procedure_element(self, procedure_elem) -> Dict[str, Any]:
        """Parse procedure element into structured data."""
        # Extract procedure name
        code_elem = procedure_elem.find('hl7:code', self.namespaces)
        name = "Unknown procedure"
        if code_elem is not None:
            name = code_elem.get('displayName', code_elem.get('code', 'Unknown procedure'))
        
        # Extract date
        time_elem = procedure_elem.find('hl7:effectiveTime', self.namespaces)
        date = "Not specified"
        if time_elem is not None:
            date = time_elem.get('value', 'Not specified')
        
        # Extract status
        status_elem = procedure_elem.find('hl7:statusCode', self.namespaces)
        status = "Completed"
        if status_elem is not None:
            status = status_elem.get('code', 'Completed')
        
        return {
            'name': name,
            'date': date,
            'provider': 'Not specified',
            'location': 'Not specified',
            'status': status,
            'indication': 'Not specified'
        }