"""
Social History Section Service

Specialized service for social history section data processing.

Handles:
- Social history information
- Lifestyle factors
- Smoking, alcohol, and substance use
- Occupation and environmental factors

Author: Django_NCP Development Team
Date: October 2025
Version: 1.0.0
"""

import logging
from typing import Dict, List, Any
from django.http import HttpRequest
from ..base.clinical_service_base import ClinicalServiceBase
from ..cts_integration_mixin import CTSIntegrationMixin

logger = logging.getLogger(__name__)


class SocialHistorySectionService(CTSIntegrationMixin, ClinicalServiceBase):
    """
    Specialized service for social history section data processing.
    
    Handles:
    - Social history information
    - Lifestyle factors
    - Smoking, alcohol, and substance use
    - Occupation and environmental factors
    """
    
    def get_section_code(self) -> str:
        return "29762-2"
    
    def get_section_name(self) -> str:
        return "Social History"
    
    def extract_from_session(self, request: HttpRequest, session_id: str) -> List[Dict[str, Any]]:
        """Extract social history from session storage."""
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        
        # Check for enhanced social history data
        enhanced_social_history = match_data.get('enhanced_social_history', [])
        
        if enhanced_social_history:
            self._log_extraction_result('extract_from_session', len(enhanced_social_history), 'Session')
            return enhanced_social_history
        
        # Check for clinical arrays social history
        clinical_arrays = match_data.get('enhanced_clinical_data', {}).get('clinical_sections', {})
        social_history_data = clinical_arrays.get('social_history', [])
        
        if social_history_data:
            self._log_extraction_result('extract_from_session', len(social_history_data), 'Clinical Arrays')
            return social_history_data
        
        self.logger.info("[SOCIAL HISTORY SERVICE] No social history data found in session")
        return []
    
    def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
        """Extract social history from CDA content using specialized parsing."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(cda_content)
            
            # Find social history section using base method
            section = self._find_section_by_code(root, ['29762-2', '10164-2'])
            
            if section is not None:
                social_history = self._parse_social_history_xml(section)
                self._log_extraction_result('extract_from_cda', len(social_history), 'CDA')
                return social_history
            
            self.logger.info("[SOCIAL HISTORY SERVICE] No social history section found in CDA")
            return []
            
        except Exception as e:
            self.logger.error(f"[SOCIAL HISTORY SERVICE] Error extracting social history from CDA: {e}")
            return []
    
    def enhance_and_store(self, request: HttpRequest, session_id: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance social history data and store in session."""
        enhanced_social_history = []
        
        for social_data in raw_data:
            enhanced_social = {
                'name': self._extract_field_value(social_data, 'category', 'Social history item'),
                'display_name': self._extract_field_value(social_data, 'category', 'Social history item'),
                'category': self._extract_field_value(social_data, 'category', 'Lifestyle'),
                'description': self._extract_field_value(social_data, 'description', 'Not specified'),
                'status': self._extract_field_value(social_data, 'status', 'Active'),
                'frequency': self._extract_field_value(social_data, 'frequency', 'Not specified'),
                'quantity': self._extract_field_value(social_data, 'quantity', 'Not specified'),
                'start_date': self._format_cda_date(self._extract_field_value(social_data, 'start_date', 'Not specified')),
                'end_date': self._format_cda_date(self._extract_field_value(social_data, 'end_date', 'Not specified')),
                'source': 'cda_extraction_enhanced'
            }
            enhanced_social_history.append(enhanced_social)
        
        # Store in session
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        match_data['enhanced_social_history'] = enhanced_social_history
        request.session[session_key] = match_data
        request.session.modified = True
        
        self.logger.info(f"[SOCIAL HISTORY SERVICE] Enhanced and stored {len(enhanced_social_history)} social history items")
        return enhanced_social_history
    
    def get_template_data(self, enhanced_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert enhanced social history to template-ready format."""
        return {
            'items': enhanced_data,
            'metadata': {
                'section_name': 'Social History',
                'section_code': '29762-2',
                'item_count': len(enhanced_data),
                'has_items': len(enhanced_data) > 0,
                'template_pattern': 'direct_field_access'  # social.field_name
            }
        }
    
    def _parse_social_history_xml(self, section) -> List[Dict[str, Any]]:
        """Parse social history section XML into structured data."""
        social_history = []
        
        # First, build a mapping of observation IDs to narrative text from <text> section
        narrative_map = {}
        text_section = section.find('hl7:text', self.namespaces)
        if text_section is not None:
            paragraphs = text_section.findall('.//hl7:paragraph', self.namespaces)
            for para in paragraphs:
                para_id = para.get('ID')
                para_text = para.text if para.text else ''
                if para_id and para_text:
                    narrative_map[para_id] = para_text.strip()
        
        entries = section.findall('.//hl7:entry', self.namespaces)
        for entry in entries:
            observation = entry.find('.//hl7:observation', self.namespaces)
            if observation is not None:
                social_item = self._parse_social_observation(observation, narrative_map)
                if social_item:
                    social_history.append(social_item)
        
        return social_history
    
    def _parse_social_observation(self, observation, narrative_map: Dict[str, str] = None) -> Dict[str, Any]:
        """Parse social history observation into structured data."""
        if narrative_map is None:
            narrative_map = {}
        
        # Extract category from code
        code_elem = observation.find('hl7:code', self.namespaces)
        category = "Lifestyle"
        if code_elem is not None:
            code = code_elem.get('code', '')
            display_name = code_elem.get('displayName', '')
            
            # Map common social history codes to categories
            if code in ['72166-2', '11341-5']:  # Smoking status
                category = "Smoking"
            elif code in ['11331-6', '160573003']:  # Alcohol use
                category = "Alcohol use"
            elif code in ['364393001', '228273003']:  # Substance use
                category = "Substance use"
            elif code in ['224362002', '14679004']:  # Occupation
                category = "Occupation"
            else:
                category = display_name or "Lifestyle"
        
        # Extract value/description with code for CTS translation
        value_elem = observation.find('hl7:value', self.namespaces)
        description = "Not specified"
        value_code = None
        value_system = None
        quantity = "Not specified"
        frequency = "Not specified"
        
        if value_elem is not None:
            # Try to get displayName first
            description = value_elem.get('displayName', 'Not specified')
            value_code = value_elem.get('code')
            value_system = value_elem.get('codeSystem')
            
            # Check if value has text content (for quantity/frequency)
            if value_elem.text:
                description = value_elem.text.strip()
            
            # If no displayName and no text, store code for CTS translation
            if description == 'Not specified' and value_code:
                description = value_code  # Will be translated by CTS
        
        # Try to extract quantity from value element attributes or child elements
        # Look for quantity in value[@value] or value/quantity elements
        if value_elem is not None:
            quantity_value = value_elem.get('value')
            quantity_unit = value_elem.get('unit')
            if quantity_value:
                if quantity_unit:
                    quantity = f"{quantity_value} {quantity_unit}"
                else:
                    quantity = quantity_value
        
        # Look for text content in the observation using reference to narrative
        text_elem = observation.find('hl7:text', self.namespaces)
        if text_elem is not None:
            # Check for reference to paragraph ID
            reference_elem = text_elem.find('hl7:reference', self.namespaces)
            if reference_elem is not None:
                ref_value = reference_elem.get('value', '')
                # Remove leading '#' from reference
                if ref_value.startswith('#'):
                    ref_id = ref_value[1:]
                    # Look up narrative text from map
                    if ref_id in narrative_map:
                        narrative_text = narrative_map[ref_id]
                        # Parse narrative text for category, quantity and frequency
                        # Format: "Tobacco use and exposure: 0.5 {pack}/d since 2017-04-15"
                        if ':' in narrative_text:
                            parts = narrative_text.split(':', 1)
                            if len(parts) == 2:
                                # Update category from narrative if more descriptive
                                category_from_text = parts[0].strip()
                                if category_from_text:
                                    category = category_from_text
                                
                                value_part = parts[1].strip()
                                # Extract quantity/frequency from value_part
                                if ' since ' in value_part:
                                    qty_freq = value_part.split(' since ')[0].strip()
                                    if qty_freq and qty_freq != '':
                                        quantity = qty_freq
                                        description = qty_freq
            elif text_elem.text:
                # Fallback: direct text content
                narrative_text = text_elem.text.strip()
                if ':' in narrative_text:
                    parts = narrative_text.split(':', 1)
                    if len(parts) == 2:
                        value_part = parts[1].strip()
                        if ' since ' in value_part:
                            qty_freq = value_part.split(' since ')[0].strip()
                            if qty_freq and qty_freq != '':
                                quantity = qty_freq
                                description = qty_freq
        
        # Extract effective time
        start_date = "Not specified"
        end_date = "Not specified"
        effective_time = observation.find('hl7:effectiveTime', self.namespaces)
        if effective_time is not None:
            low_elem = effective_time.find('hl7:low', self.namespaces)
            high_elem = effective_time.find('hl7:high', self.namespaces)
            
            if low_elem is not None:
                start_date = low_elem.get('value', 'Not specified')
            if high_elem is not None:
                end_date = high_elem.get('value', 'Not specified')
            
            # If no low/high elements, try direct value attribute
            if start_date == 'Not specified' and end_date == 'Not specified':
                single_value = effective_time.get('value')
                if single_value:
                    start_date = single_value
        
        # Extract status
        status_elem = observation.find('hl7:statusCode', self.namespaces)
        status = "Active"
        if status_elem is not None:
            status = status_elem.get('code', 'Active')
        
        return {
            'category': category,
            'description': description,
            'value_code': value_code,
            'value_system': value_system,
            'status': status,
            'frequency': frequency,
            'quantity': quantity,
            'start_date': start_date,
            'end_date': end_date
        }
