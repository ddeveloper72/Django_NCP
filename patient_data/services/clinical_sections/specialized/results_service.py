"""
Results Section Service

Specialized service for laboratory results section data processing.

Handles:
- Laboratory test results
- Diagnostic test results
- Blood group information
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


class ResultsSectionService(ClinicalServiceBase):
    """
    Specialized service for laboratory results section data processing.
    
    Handles:
    - Laboratory test results
    - Diagnostic test results
    - Blood group information
    - Clinical observations
    """
    
    def get_section_code(self) -> str:
        return "30954-2"
    
    def get_section_name(self) -> str:
        return "Results"
    
    def extract_from_session(self, request: HttpRequest, session_id: str) -> List[Dict[str, Any]]:
        """Extract results from session storage."""
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        
        enhanced_results = match_data.get('enhanced_results', [])
        
        if enhanced_results:
            self._log_extraction_result('extract_from_session', len(enhanced_results), 'Session')
            return enhanced_results
        
        clinical_arrays = match_data.get('enhanced_clinical_data', {}).get('clinical_sections', {})
        results_data = clinical_arrays.get('results', [])
        
        if results_data:
            self._log_extraction_result('extract_from_session', len(results_data), 'Clinical Arrays')
            return results_data
        
        self.logger.info("[RESULTS SERVICE] No results data found in session")
        return []
    
    def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
        """Extract results from CDA content using specialized parsing."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(cda_content)
            
            # Find results section using base method
            section = self._find_section_by_code(root, ['30954-2', '18748-4', '34530-6'])
            
            if section is not None:
                results = self._parse_results_xml(section)
                self._log_extraction_result('extract_from_cda', len(results), 'CDA')
                return results
            
            self.logger.info("[RESULTS SERVICE] No results section found in CDA")
            return []
            
        except Exception as e:
            self.logger.error(f"[RESULTS SERVICE] Error extracting results from CDA: {e}")
            return []
    
    def enhance_and_store(self, request: HttpRequest, session_id: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance results data and store in session."""
        enhanced_results = []
        
        for result_data in raw_data:
            enhanced_result = {
                'name': self._extract_field_value(result_data, 'name', 'Unknown test'),
                'display_name': self._extract_field_value(result_data, 'name', 'Unknown test'),
                'value': self._extract_field_value(result_data, 'value', 'Not specified'),
                'unit': self._extract_field_value(result_data, 'unit', ''),
                'reference_range': self._extract_field_value(result_data, 'reference_range', ''),
                'status': self._extract_field_value(result_data, 'status', 'Final'),
                'date': self._format_cda_date(self._extract_field_value(result_data, 'date', 'Not specified')),
                'interpretation': self._extract_field_value(result_data, 'interpretation', ''),
                'source': 'cda_extraction_enhanced'
            }
            enhanced_results.append(enhanced_result)
        
        # Store in session
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        match_data['enhanced_results'] = enhanced_results
        request.session[session_key] = match_data
        request.session.modified = True
        
        self.logger.info(f"[RESULTS SERVICE] Enhanced and stored {len(enhanced_results)} results")
        return enhanced_results
    
    def get_template_data(self, enhanced_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert enhanced results to template-ready format."""
        return {
            'items': enhanced_data,
            'metadata': {
                'section_name': 'Results',
                'section_code': '30954-2',
                'item_count': len(enhanced_data),
                'has_items': len(enhanced_data) > 0,
                'template_pattern': 'direct_field_access'  # result.field_name
            }
        }
    
    def _parse_results_xml(self, section) -> List[Dict[str, Any]]:
        """Parse results section XML into structured data."""
        results = []
        
        entries = section.findall('.//hl7:entry', self.namespaces)
        for entry in entries:
            observation = entry.find('.//hl7:observation', self.namespaces)
            if observation is not None:
                result = self._parse_result_observation(observation)
                if result:
                    results.append(result)
        
        return results
    
    def _parse_result_observation(self, observation) -> Dict[str, Any]:
        """Parse result observation into structured data."""
        # Extract test name
        code_elem = observation.find('hl7:code', self.namespaces)
        name = "Unknown test"
        if code_elem is not None:
            name = code_elem.get('displayName', code_elem.get('code', 'Unknown test'))
        
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
            'reference_range': '',
            'status': 'Final',
            'date': date,
            'interpretation': ''
        }