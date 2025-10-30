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
                self.logger.info("[VITAL SIGNS SERVICE] Found vital signs section in CDA")
                vitals = self._parse_vitals_xml(section)
                self.logger.info(f"[VITAL SIGNS SERVICE] Extracted {len(vitals)} vital signs from CDA")
                if vitals:
                    self.logger.info(f"[VITAL SIGNS SERVICE] First vital: {vitals[0]}")
                self._log_extraction_result('extract_from_cda', len(vitals), 'CDA')
                return vitals
            
            self.logger.warning("[VITAL SIGNS SERVICE] No vital signs section found in CDA")
            return []
            
        except Exception as e:
            self.logger.error(f"[VITAL SIGNS SERVICE] Error extracting vital signs from CDA: {e}", exc_info=True)
            return []
    
    def enhance_and_store(self, request: HttpRequest, session_id: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance vital signs data and store in session."""
        self.logger.info(f"[VITAL SIGNS SERVICE] enhance_and_store received {len(raw_data)} vital signs")
        
        enhanced_vitals = []
        
        for vital_data in raw_data:
            # Preserve all extracted fields
            enhanced_vital = {
                'name': self._extract_field_value(vital_data, 'name', 'Unknown measurement'),
                'display_name': self._extract_field_value(vital_data, 'name', 'Unknown measurement'),
                'value': self._extract_field_value(vital_data, 'value'),
                'unit': self._extract_field_value(vital_data, 'unit', ''),
                'date': self._format_cda_date(self._extract_field_value(vital_data, 'date')),
                'status': self._extract_field_value(vital_data, 'status', 'Final'),
                'reference_range': self._extract_field_value(vital_data, 'reference_range', ''),
                'source': 'cda_extraction_enhanced',
                
                # Preserve LOINC codes and identifiers
                'vital_code': self._extract_field_value(vital_data, 'vital_code', ''),
                'code_system': self._extract_field_value(vital_data, 'code_system', ''),
                'observation_id': self._extract_field_value(vital_data, 'observation_id', ''),
                
                # Keep original data for reference
                'data': vital_data
            }
            enhanced_vitals.append(enhanced_vital)
        
        # Store in session
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        match_data['enhanced_vital_signs'] = enhanced_vitals
        request.session[session_key] = match_data
        request.session.modified = True
        
        self.logger.info(f"[VITAL SIGNS SERVICE] Enhanced and stored {len(enhanced_vitals)} vital signs")
        if enhanced_vitals:
            first_vital = enhanced_vitals[0]
            self.logger.info(f"[VITAL SIGNS SERVICE] First vital: name='{first_vital.get('name')}', value='{first_vital.get('value')}', unit='{first_vital.get('unit')}', code='{first_vital.get('vital_code')}'")
        
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
        
        self.logger.info("[VITAL SIGNS SERVICE] Starting XML parsing")
        
        # First try organizer pattern (multiple observations grouped)
        organizers = section.findall('.//hl7:entry/hl7:organizer', self.namespaces)
        self.logger.info(f"[VITAL SIGNS SERVICE] Found {len(organizers)} organizers")
        
        for organizer in organizers:
            # Find all component observations within the organizer
            components = organizer.findall('.//hl7:component/hl7:observation', self.namespaces)
            self.logger.info(f"[VITAL SIGNS SERVICE] Found {len(components)} observations in organizer")
            
            for observation in components:
                vital = self._parse_vital_observation(observation)
                if vital:
                    self.logger.info(f"[VITAL SIGNS SERVICE] Parsed vital: {vital.get('name')} = {vital.get('value')} {vital.get('unit')}")
                    vitals.append(vital)
                else:
                    self.logger.warning("[VITAL SIGNS SERVICE] Failed to parse observation")
        
        # If no organizers found, try direct observation entries
        if not vitals:
            self.logger.info("[VITAL SIGNS SERVICE] No organizers found, trying direct entries")
            entries = section.findall('.//hl7:entry', self.namespaces)
            self.logger.info(f"[VITAL SIGNS SERVICE] Found {len(entries)} direct entries")
            
            for entry in entries:
                observation = entry.find('.//hl7:observation', self.namespaces)
                if observation is not None:
                    vital = self._parse_vital_observation(observation)
                    if vital:
                        self.logger.info(f"[VITAL SIGNS SERVICE] Parsed vital: {vital.get('name')} = {vital.get('value')} {vital.get('unit')}")
                        vitals.append(vital)
        
        self.logger.info(f"[VITAL SIGNS SERVICE] Total vitals parsed: {len(vitals)}")
        return vitals
    
    def _parse_vital_observation(self, observation) -> Dict[str, Any]:
        """Parse vital sign observation into structured data."""
        # Extract LOINC code and display name
        code_elem = observation.find('hl7:code', self.namespaces)
        vital_code = ""
        code_system = ""
        name = "Unknown measurement"
        
        if code_elem is not None:
            vital_code = code_elem.get('code', '')
            code_system = code_elem.get('codeSystem', '')
            name = code_elem.get('displayName', '')
            
            # If no displayName, try to resolve from narrative text
            if not name:
                text_ref = code_elem.find('hl7:originalText/hl7:reference', self.namespaces)
                if text_ref is not None:
                    ref_value = text_ref.get('value', '').replace('#', '')
                    if ref_value:
                        name = self._resolve_text_reference(observation, ref_value)
                        
            # Fallback to code if still no name
            if not name:
                name = self._get_loinc_display_name(vital_code)
        
        # Extract value and unit
        value_elem = observation.find('hl7:value', self.namespaces)
        value = ""
        unit = ""
        if value_elem is not None:
            value = value_elem.get('value', '')
            unit = value_elem.get('unit', '')
        
        # Extract date
        time_elem = observation.find('hl7:effectiveTime', self.namespaces)
        date = ""
        if time_elem is not None:
            date = time_elem.get('value', '')
        
        # Extract status
        status_elem = observation.find('hl7:statusCode', self.namespaces)
        status = "Final"
        if status_elem is not None:
            status = status_elem.get('code', 'Final')
        
        return {
            'name': name,
            'vital_code': vital_code,
            'code_system': code_system,
            'value': value,
            'unit': unit,
            'date': date,
            'status': status.capitalize(),
            'reference_range': '',
            'observation_id': observation.find('hl7:id', self.namespaces).get('root', '') if observation.find('hl7:id', self.namespaces) is not None else ''
        }
    
    def _resolve_text_reference(self, observation, ref_id: str) -> str:
        """Resolve narrative text reference from section."""
        try:
            # Navigate up to section to find the text content
            section = observation
            for _ in range(10):  # Limit upward traversal
                parent = section.find('..')
                if parent is None:
                    break
                if parent.tag.endswith('section'):
                    section = parent
                    break
                section = parent
            
            # Find the referenced element
            text_section = section.find('.//hl7:text', self.namespaces)
            if text_section is not None:
                # Try to find element with matching ID
                ref_elem = text_section.find(f".//*[@ID='{ref_id}']")
                if ref_elem is not None and ref_elem.text:
                    return ref_elem.text.strip()
        except Exception as e:
            self.logger.debug(f"Could not resolve text reference {ref_id}: {e}")
        
        return ""
    
    def _get_loinc_display_name(self, code: str) -> str:
        """Get display name for common LOINC vital sign codes."""
        loinc_names = {
            '8462-4': 'Diastolic blood pressure',
            '8480-6': 'Systolic blood pressure',
            '8867-4': 'Heart rate',
            '9279-1': 'Respiratory rate',
            '8310-5': 'Body temperature',
            '29463-7': 'Body weight',
            '8302-2': 'Body height',
            '39156-5': 'Body mass index',
            '2708-6': 'Oxygen saturation',
            '8306-3': 'Body height (lying)',
            '8287-5': 'Head circumference'
        }
        return loinc_names.get(code, f'Vital Sign (LOINC: {code})')