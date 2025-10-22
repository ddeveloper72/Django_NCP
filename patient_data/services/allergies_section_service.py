"""
Allergies Section Service

Specialized service agent for allergies and intolerances clinical data processing.
Implements the ClinicalSectionServiceInterface for consistent pipeline integration.

Author: Django_NCP Development Team
Date: October 2025
Version: 1.0.0
"""

import logging
from typing import Dict, List, Any
from django.http import HttpRequest
from .clinical_data_pipeline_manager import ClinicalSectionServiceInterface

logger = logging.getLogger(__name__)


class AllergiesSectionService(ClinicalSectionServiceInterface):
    """
    Specialized service for allergies and intolerances section data processing.
    
    Handles:
    - Food allergies and intolerances  
    - Medication allergies
    - Environmental allergies
    - Severity assessment
    - Reaction documentation
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
            logger.info(f"[ALLERGIES SERVICE] Found {len(enhanced_allergies)} enhanced allergies in session")
            return enhanced_allergies
        
        # Check for clinical arrays allergies
        clinical_arrays = match_data.get('enhanced_clinical_data', {}).get('clinical_sections', {})
        allergies_data = clinical_arrays.get('allergies', [])
        
        if allergies_data:
            logger.info(f"[ALLERGIES SERVICE] Found {len(allergies_data)} allergies in clinical arrays")
            return allergies_data
        
        logger.info("[ALLERGIES SERVICE] No allergies data found in session")
        return []
    
    def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
        """Extract allergies from CDA content using specialized parsing."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(cda_content)
            
            # Find allergies section
            namespaces = {'hl7': 'urn:hl7-org:v3'}
            sections = root.findall('.//hl7:section', namespaces)
            
            for section in sections:
                code_elem = section.find('hl7:code', namespaces)
                if code_elem is not None and code_elem.get('code') == '48765-2':
                    # Parse allergies section
                    allergies = self._parse_allergies_xml(section)
                    logger.info(f"[ALLERGIES SERVICE] Extracted {len(allergies)} allergies from CDA")
                    return allergies
            
            logger.info("[ALLERGIES SERVICE] No allergies section found in CDA")
            return []
            
        except Exception as e:
            logger.error(f"[ALLERGIES SERVICE] Error extracting allergies from CDA: {e}")
            return []
    
    def enhance_and_store(self, request: HttpRequest, session_id: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance allergies data and store in session."""
        enhanced_allergies = []
        
        for allergy_data in raw_data:
            # Apply enhancement pattern following medications model
            enhanced_allergy = {
                'allergen': self._extract_field_value(allergy_data, 'allergen', 'Unknown allergen'),
                'display_name': self._extract_field_value(allergy_data, 'allergen', 'Unknown allergen'),
                'type': self._extract_field_value(allergy_data, 'type', 'Allergy'),
                'reaction': self._extract_field_value(allergy_data, 'reaction', 'Unknown reaction'),
                'severity': self._extract_field_value(allergy_data, 'severity', 'Not specified'),
                'status': self._extract_field_value(allergy_data, 'status', 'Active'),
                'date_identified': self._extract_field_value(allergy_data, 'date', 'Not specified'),
                'notes': self._extract_field_value(allergy_data, 'notes', ''),
                'source': 'cda_extraction_enhanced'
            }
            enhanced_allergies.append(enhanced_allergy)
        
        # Store in session using consistent pattern
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        match_data['enhanced_allergies'] = enhanced_allergies
        request.session[session_key] = match_data
        request.session.modified = True
        
        logger.info(f"[ALLERGIES SERVICE] Enhanced and stored {len(enhanced_allergies)} allergies")
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
        namespaces = {'hl7': 'urn:hl7-org:v3'}
        
        # Strategy 1: Extract from narrative paragraphs
        text_section = section.find('.//hl7:text', namespaces) or section.find('.//text')
        if text_section is not None:
            paragraphs = text_section.findall('.//hl7:paragraph', namespaces) or text_section.findall('.//paragraph')
            
            for paragraph in paragraphs:
                text = self._extract_text_from_element(paragraph)
                if text and ('allergy' in text.lower() or 'intolerance' in text.lower()):
                    allergy = self._parse_allergy_narrative(text)
                    if allergy:
                        allergies.append(allergy)
        
        # Strategy 2: Extract from structured entries
        entries = section.findall('.//hl7:entry', namespaces)
        for entry in entries:
            observation = entry.find('.//hl7:observation', namespaces)
            if observation is not None:
                allergy = self._parse_allergy_observation(observation)
                if allergy:
                    allergies.append(allergy)
        
        return allergies
    
    def _parse_allergy_narrative(self, text: str) -> Dict[str, Any]:
        """Parse allergy information from narrative text."""
        allergen = "Unknown"
        reaction = "Unknown"
        allergy_type = "Unknown"
        status = "Active"
        
        # Extract allergen
        if 'allergy to' in text.lower():
            parts = text.lower().split('allergy to')
            if len(parts) > 1:
                allergen_part = parts[1].split(',')[0].strip()
                allergen = allergen_part.title()
        elif 'intolerance to' in text.lower():
            parts = text.lower().split('intolerance to')
            if len(parts) > 1:
                allergen_part = parts[1].split(',')[0].strip()
                allergen = allergen_part.title()
        
        # Extract reaction
        if 'reaction:' in text.lower():
            reaction_part = text.lower().split('reaction:')[1].strip()
            reaction = reaction_part.title()
        
        # Determine allergy type
        if 'food' in text.lower():
            allergy_type = "Food allergy"
        elif 'medication' in text.lower():
            allergy_type = "Medication allergy"
        elif 'intolerance' in text.lower():
            allergy_type = "Food intolerance"
        else:
            allergy_type = "Allergy"
        
        return {
            'allergen': allergen,
            'type': allergy_type,
            'reaction': reaction,
            'status': status,
            'severity': 'Not specified',
            'date': 'Not specified'
        }
    
    def _parse_allergy_observation(self, observation) -> Dict[str, Any]:
        """Parse allergy information from structured observation element."""
        namespaces = {'hl7': 'urn:hl7-org:v3'}
        
        # Extract participant (allergen)
        allergen = "Unknown"
        participant = observation.find('.//hl7:participant', namespaces)
        if participant is not None:
            code_elem = participant.find('.//hl7:code', namespaces)
            if code_elem is not None:
                allergen = code_elem.get('displayName', code_elem.get('code', 'Unknown'))
        
        # Extract value (reaction type)
        reaction = "Unknown"
        value_elem = observation.find('hl7:value', namespaces)
        if value_elem is not None:
            reaction = value_elem.get('displayName', value_elem.get('code', 'Unknown'))
        
        # Extract severity
        severity = "Not specified"
        severity_obs = observation.find('.//hl7:observation[hl7:code/@code="SEV"]', namespaces)
        if severity_obs is not None:
            severity_value = severity_obs.find('hl7:value', namespaces)
            if severity_value is not None:
                severity = severity_value.get('displayName', severity_value.get('code', 'Not specified'))
        
        return {
            'allergen': allergen,
            'type': 'Allergy',
            'reaction': reaction,
            'status': 'Active',
            'severity': severity,
            'date': 'Not specified'
        }
    
    def _extract_text_from_element(self, element) -> str:
        """Extract clean text from XML element."""
        if element is None:
            return ""
        
        # Try to find content tags first
        content_elements = element.findall('.//content')
        if content_elements:
            text = content_elements[-1].text
            if text and text.strip():
                return text.strip()
        
        # Fallback to element text
        text = element.text
        if text and text.strip():
            return text.strip()
        
        # If no direct text, try to get all text content
        all_text = ''.join(element.itertext()).strip()
        return all_text if all_text else ""
    
    def _extract_field_value(self, data: Dict[str, Any], field_name: str, default: str) -> str:
        """Extract field value handling both flat and nested structures."""
        value = data.get(field_name, default)
        
        if isinstance(value, dict):
            # Handle nested structures like {'value': 'X', 'display_value': 'Y'}
            return value.get('display_value', value.get('value', default))
        
        return str(value) if value else default


# Register the allergies service with the global pipeline manager
from .clinical_data_pipeline_manager import clinical_pipeline_manager
clinical_pipeline_manager.register_service(AllergiesSectionService())