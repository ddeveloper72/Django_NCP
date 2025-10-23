"""
Advance Directives Section Service

Specialized service for advance directives section data processing.

Handles:
- Advance directives documentation
- Healthcare proxies and power of attorney
- Living wills and care preferences
- End-of-life care instructions

Author: Django_NCP Development Team
Date: October 2025
Version: 1.0.0
"""

import logging
from typing import Dict, List, Any
from django.http import HttpRequest
from ..base.clinical_service_base import ClinicalServiceBase

logger = logging.getLogger(__name__)


class AdvanceDirectivesSectionService(ClinicalServiceBase):
    """
    Specialized service for advance directives section data processing.
    
    Handles:
    - Advance directives documentation
    - Healthcare proxies and power of attorney
    - Living wills and care preferences
    - End-of-life care instructions
    """
    
    def get_section_code(self) -> str:
        return "42348-3"
    
    def get_section_name(self) -> str:
        return "Advance Directives"
    
    def extract_from_session(self, request: HttpRequest, session_id: str) -> List[Dict[str, Any]]:
        """Extract advance directives from session storage."""
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        
        # Check for enhanced advance directives data
        enhanced_directives = match_data.get('enhanced_advance_directives', [])
        
        if enhanced_directives:
            self._log_extraction_result('extract_from_session', len(enhanced_directives), 'Session')
            return enhanced_directives
        
        # Check for clinical arrays advance directives
        clinical_arrays = match_data.get('enhanced_clinical_data', {}).get('clinical_sections', {})
        directives_data = clinical_arrays.get('advance_directives', [])
        
        if directives_data:
            self._log_extraction_result('extract_from_session', len(directives_data), 'Clinical Arrays')
            return directives_data
        
        self.logger.info("[ADVANCE DIRECTIVES SERVICE] No advance directives data found in session")
        return []
    
    def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
        """Extract advance directives from CDA content using specialized parsing."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(cda_content)
            
            # Find advance directives section using base method
            section = self._find_section_by_code(root, ['42348-3', '75320-2'])
            
            if section is not None:
                directives = self._parse_directives_xml(section)
                self._log_extraction_result('extract_from_cda', len(directives), 'CDA')
                return directives
            
            self.logger.info("[ADVANCE DIRECTIVES SERVICE] No advance directives section found in CDA")
            return []
            
        except Exception as e:
            self.logger.error(f"[ADVANCE DIRECTIVES SERVICE] Error extracting advance directives from CDA: {e}")
            return []
    
    def enhance_and_store(self, request: HttpRequest, session_id: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance advance directives data and store in session."""
        enhanced_directives = []
        
        for directive_data in raw_data:
            enhanced_directive = {
                'name': self._extract_field_value(directive_data, 'type', 'Advance directive'),
                'display_name': self._extract_field_value(directive_data, 'type', 'Advance directive'),
                'type': self._extract_field_value(directive_data, 'type', 'General directive'),
                'description': self._extract_field_value(directive_data, 'description', 'Not specified'),
                'status': self._extract_field_value(directive_data, 'status', 'Active'),
                'date_created': self._format_cda_date(self._extract_field_value(directive_data, 'date_created', 'Not specified')),
                'date_effective': self._format_cda_date(self._extract_field_value(directive_data, 'date_effective', 'Not specified')),
                'healthcare_proxy': self._extract_field_value(directive_data, 'healthcare_proxy', 'Not specified'),
                'witness': self._extract_field_value(directive_data, 'witness', 'Not specified'),
                'source': 'cda_extraction_enhanced'
            }
            enhanced_directives.append(enhanced_directive)
        
        # Store in session
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        match_data['enhanced_advance_directives'] = enhanced_directives
        request.session[session_key] = match_data
        request.session.modified = True
        
        self.logger.info(f"[ADVANCE DIRECTIVES SERVICE] Enhanced and stored {len(enhanced_directives)} advance directives")
        return enhanced_directives
    
    def get_template_data(self, enhanced_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert enhanced advance directives to template-ready format."""
        return {
            'items': enhanced_data,
            'metadata': {
                'section_name': 'Advance Directives',
                'section_code': '42348-3',
                'item_count': len(enhanced_data),
                'has_items': len(enhanced_data) > 0,
                'template_pattern': 'direct_field_access'  # directive.field_name
            }
        }
    
    def _parse_directives_xml(self, section) -> List[Dict[str, Any]]:
        """Parse advance directives section XML into structured data."""
        directives = []
        
        entries = section.findall('.//hl7:entry', self.namespaces)
        for entry in entries:
            observation = entry.find('.//hl7:observation', self.namespaces)
            if observation is not None:
                directive = self._parse_directive_observation(observation)
                if directive:
                    directives.append(directive)
        
        return directives
    
    def _parse_directive_observation(self, observation) -> Dict[str, Any]:
        """Parse advance directive observation into structured data."""
        # Extract directive type from code
        code_elem = observation.find('hl7:code', self.namespaces)
        directive_type = "General directive"
        if code_elem is not None:
            code = code_elem.get('code', '')
            display_name = code_elem.get('displayName', '')
            
            # Map common advance directive codes to types
            if code in ['75320-2', '371538006']:  # Living will
                directive_type = "Living will"
            elif code in ['75781-5', '186065004']:  # Healthcare proxy
                directive_type = "Healthcare proxy"
            elif code in ['75776-5', '225204009']:  # DNR order
                directive_type = "Do not resuscitate"
            elif code in ['75777-3', '304253006']:  # POLST
                directive_type = "POLST"
            else:
                directive_type = display_name or "General directive"
        
        # Extract description from value or text
        description = "Not specified"
        value_elem = observation.find('hl7:value', self.namespaces)
        if value_elem is not None:
            description = value_elem.get('displayName', value_elem.get('code', 'Not specified'))
        
        # If no value, try to get from text content
        if description == "Not specified":
            text_elem = observation.find('.//hl7:text', self.namespaces)
            if text_elem is not None:
                description = self._extract_text_from_element(text_elem)
        
        # Extract effective dates
        date_created = "Not specified"
        date_effective = "Not specified"
        effective_time = observation.find('hl7:effectiveTime', self.namespaces)
        if effective_time is not None:
            low_elem = effective_time.find('hl7:low', self.namespaces)
            high_elem = effective_time.find('hl7:high', self.namespaces)
            
            if low_elem is not None:
                date_created = low_elem.get('value', 'Not specified')
            if high_elem is not None:
                date_effective = high_elem.get('value', 'Not specified')
            else:
                # Single value time
                date_created = effective_time.get('value', 'Not specified')
                date_effective = date_created
        
        # Extract status
        status_elem = observation.find('hl7:statusCode', self.namespaces)
        status = "Active"
        if status_elem is not None:
            status = status_elem.get('code', 'Active')
        
        # Extract healthcare proxy information
        healthcare_proxy = "Not specified"
        performer = observation.find('.//hl7:performer', self.namespaces)
        if performer is not None:
            name_elem = performer.find('.//hl7:name', self.namespaces)
            if name_elem is not None:
                given = name_elem.find('hl7:given', self.namespaces)
                family = name_elem.find('hl7:family', self.namespaces)
                if given is not None and family is not None:
                    healthcare_proxy = f"{given.text} {family.text}"
        
        return {
            'type': directive_type,
            'description': description,
            'status': status,
            'date_created': date_created,
            'date_effective': date_effective,
            'healthcare_proxy': healthcare_proxy,
            'witness': 'Not specified'
        }