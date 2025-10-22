"""
Pregnancy History Section Service

Specialized service agent for pregnancy history clinical data processing.

Author: Django_NCP Development Team
Date: October 2025
Version: 1.0.0
"""

import logging
from typing import Dict, List, Any
from django.http import HttpRequest
from .clinical_data_pipeline_manager import ClinicalSectionServiceInterface

logger = logging.getLogger(__name__)


class PregnancyHistorySectionService(ClinicalSectionServiceInterface):
    """
    Specialized service for pregnancy history section data processing.
    
    Handles:
    - Pregnancy history records
    - Obstetric information
    - Delivery information
    - Pregnancy complications
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
            logger.info(f"[PREGNANCY HISTORY SERVICE] Found {len(enhanced_pregnancy)} enhanced pregnancy records in session")
            return enhanced_pregnancy
        
        # Check for clinical arrays pregnancy history
        clinical_arrays = match_data.get('enhanced_clinical_data', {}).get('clinical_sections', {})
        pregnancy_data = clinical_arrays.get('pregnancy_history', [])
        
        if pregnancy_data:
            logger.info(f"[PREGNANCY HISTORY SERVICE] Found {len(pregnancy_data)} pregnancy records in clinical arrays")
            return pregnancy_data
        
        # Check for existing pregnancy_entries (legacy format)
        pregnancy_entries = match_data.get('pregnancy_entries', [])
        if pregnancy_entries:
            logger.info(f"[PREGNANCY HISTORY SERVICE] Found {len(pregnancy_entries)} pregnancy entries in legacy format")
            return pregnancy_entries
        
        logger.info("[PREGNANCY HISTORY SERVICE] No pregnancy history data found in session")
        return []
    
    def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
        """Extract pregnancy history from CDA content using specialized parsing."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(cda_content)
            
            # Find pregnancy history section
            namespaces = {'hl7': 'urn:hl7-org:v3'}
            sections = root.findall('.//hl7:section', namespaces)
            
            for section in sections:
                code_elem = section.find('hl7:code', namespaces)
                if code_elem is not None and code_elem.get('code') == '10162-6':
                    # Parse pregnancy history section
                    pregnancy_records = self._parse_pregnancy_xml(section)
                    logger.info(f"[PREGNANCY HISTORY SERVICE] Extracted {len(pregnancy_records)} pregnancy records from CDA")
                    return pregnancy_records
            
            logger.info("[PREGNANCY HISTORY SERVICE] No pregnancy history section found in CDA")
            return []
            
        except Exception as e:
            logger.error(f"[PREGNANCY HISTORY SERVICE] Error extracting pregnancy history from CDA: {e}")
            return []
    
    def enhance_and_store(self, request: HttpRequest, session_id: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance pregnancy history data and store in session."""
        enhanced_pregnancy = []
        
        for pregnancy_data in raw_data:
            enhanced_record = {
                'pregnancy_number': self._extract_field_value(pregnancy_data, 'pregnancy_number', 'Not specified'),
                'display_name': f"Pregnancy {self._extract_field_value(pregnancy_data, 'pregnancy_number', 'N/A')}",
                'gestational_age': self._extract_field_value(pregnancy_data, 'gestational_age', 'Not specified'),
                'outcome': self._extract_field_value(pregnancy_data, 'outcome', 'Not specified'),
                'delivery_date': self._extract_field_value(pregnancy_data, 'delivery_date', 'Not specified'),
                'delivery_method': self._extract_field_value(pregnancy_data, 'delivery_method', 'Not specified'),
                'birth_weight': self._extract_field_value(pregnancy_data, 'birth_weight', 'Not specified'),
                'complications': self._extract_field_value(pregnancy_data, 'complications', 'None recorded'),
                'birth_location': self._extract_field_value(pregnancy_data, 'birth_location', 'Not specified'),
                'multiple_birth': self._extract_field_value(pregnancy_data, 'multiple_birth', 'No'),
                'source': 'cda_extraction_enhanced'
            }
            
            # Handle legacy format data
            if 'summary' in pregnancy_data:
                enhanced_record['summary'] = pregnancy_data['summary']
            
            enhanced_pregnancy.append(enhanced_record)
        
        # Store in session
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        match_data['enhanced_pregnancy_history'] = enhanced_pregnancy
        request.session[session_key] = match_data
        request.session.modified = True
        
        logger.info(f"[PREGNANCY HISTORY SERVICE] Enhanced and stored {len(enhanced_pregnancy)} pregnancy records")
        return enhanced_pregnancy
    
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
        pregnancy_records = []
        namespaces = {'hl7': 'urn:hl7-org:v3'}
        
        # Strategy 1: Extract from structured entries
        entries = section.findall('.//hl7:entry', namespaces)
        for entry in entries:
            observation = entry.find('.//hl7:observation', namespaces)
            if observation is not None:
                pregnancy_record = self._parse_pregnancy_observation(observation)
                if pregnancy_record:
                    pregnancy_records.append(pregnancy_record)
        
        # Strategy 2: Extract from narrative text if no structured data
        if not pregnancy_records:
            text_section = section.find('.//hl7:text', namespaces)
            if text_section is not None:
                # Look for structured table data
                table = text_section.find('.//hl7:table', namespaces)
                if table is not None:
                    pregnancy_records = self._parse_pregnancy_table(table)
                else:
                    # Parse paragraphs for pregnancy information
                    paragraphs = text_section.findall('.//hl7:paragraph', namespaces)
                    for paragraph in paragraphs:
                        text = self._extract_text_from_element(paragraph)
                        if text and 'pregnancy' in text.lower():
                            pregnancy_record = self._parse_pregnancy_narrative(text)
                            if pregnancy_record:
                                pregnancy_records.append(pregnancy_record)
        
        return pregnancy_records
    
    def _parse_pregnancy_observation(self, observation) -> Dict[str, Any]:
        """Parse pregnancy information from structured observation element."""
        namespaces = {'hl7': 'urn:hl7-org:v3'}
        
        # Extract pregnancy details from observation
        value_elem = observation.find('hl7:value', namespaces)
        outcome = "Not specified"
        gestational_age = "Not specified"
        
        if value_elem is not None:
            outcome = value_elem.get('displayName', value_elem.get('code', 'Not specified'))
        
        # Extract effective time for delivery date
        time_elem = observation.find('hl7:effectiveTime', namespaces)
        delivery_date = "Not specified"
        if time_elem is not None:
            delivery_date = time_elem.get('value', 'Not specified')
        
        # Look for additional pregnancy details in related observations
        birth_weight = "Not specified"
        delivery_method = "Not specified"
        
        # Check for birth weight observation
        weight_obs = observation.find('.//hl7:observation[hl7:code/@code="3141-9"]', namespaces)
        if weight_obs is not None:
            weight_value = weight_obs.find('hl7:value', namespaces)
            if weight_value is not None:
                weight = weight_value.get('value', '')
                unit = weight_value.get('unit', '')
                birth_weight = f"{weight} {unit}".strip()
        
        return {
            'pregnancy_number': 'Not specified',
            'gestational_age': gestational_age,
            'outcome': outcome,
            'delivery_date': delivery_date,
            'delivery_method': delivery_method,
            'birth_weight': birth_weight,
            'complications': 'None recorded',
            'birth_location': 'Not specified',
            'multiple_birth': 'No'
        }
    
    def _parse_pregnancy_table(self, table) -> List[Dict[str, Any]]:
        """Parse pregnancy information from structured table."""
        pregnancy_records = []
        namespaces = {'hl7': 'urn:hl7-org:v3'}
        
        # Extract table headers
        headers = []
        thead = table.find('hl7:thead', namespaces)
        if thead is not None:
            header_row = thead.find('hl7:tr', namespaces)
            if header_row is not None:
                for th in header_row.findall('hl7:th', namespaces):
                    headers.append(self._extract_text_from_element(th).lower())
        
        # Extract table data
        tbody = table.find('hl7:tbody', namespaces)
        if tbody is not None:
            for row in tbody.findall('hl7:tr', namespaces):
                cells = row.findall('hl7:td', namespaces)
                if len(cells) >= len(headers):
                    pregnancy_record = {}
                    for i, cell in enumerate(cells):
                        if i < len(headers):
                            cell_text = self._extract_text_from_element(cell)
                            pregnancy_record[headers[i]] = cell_text
                    
                    # Map table data to standard fields
                    standardized_record = self._standardize_pregnancy_record(pregnancy_record)
                    if standardized_record:
                        pregnancy_records.append(standardized_record)
        
        return pregnancy_records
    
    def _parse_pregnancy_narrative(self, text: str) -> Dict[str, Any]:
        """Parse pregnancy information from narrative text."""
        # Extract basic pregnancy information from text
        pregnancy_record = {
            'pregnancy_number': 'Not specified',
            'gestational_age': 'Not specified',
            'outcome': 'Not specified',
            'delivery_date': 'Not specified',
            'delivery_method': 'Not specified',
            'birth_weight': 'Not specified',
            'complications': 'None recorded',
            'birth_location': 'Not specified',
            'multiple_birth': 'No'
        }
        
        # Look for outcome information
        text_lower = text.lower()
        if 'live birth' in text_lower:
            pregnancy_record['outcome'] = 'Live birth'
        elif 'stillbirth' in text_lower:
            pregnancy_record['outcome'] = 'Stillbirth'
        elif 'miscarriage' in text_lower or 'abortion' in text_lower:
            pregnancy_record['outcome'] = 'Miscarriage'
        
        # Look for delivery method
        if 'cesarean' in text_lower or 'c-section' in text_lower:
            pregnancy_record['delivery_method'] = 'Cesarean section'
        elif 'vaginal' in text_lower:
            pregnancy_record['delivery_method'] = 'Vaginal delivery'
        
        # Look for multiple birth indicators
        if 'twin' in text_lower or 'triplet' in text_lower or 'multiple' in text_lower:
            pregnancy_record['multiple_birth'] = 'Yes'
        
        return pregnancy_record
    
    def _standardize_pregnancy_record(self, record: Dict[str, str]) -> Dict[str, Any]:
        """Standardize pregnancy record field names and values."""
        standardized = {
            'pregnancy_number': 'Not specified',
            'gestational_age': 'Not specified',
            'outcome': 'Not specified',
            'delivery_date': 'Not specified',
            'delivery_method': 'Not specified',
            'birth_weight': 'Not specified',
            'complications': 'None recorded',
            'birth_location': 'Not specified',
            'multiple_birth': 'No'
        }
        
        # Map common field variations
        field_mappings = {
            'pregnancy': 'pregnancy_number',
            'pregnancy number': 'pregnancy_number',
            'gestation': 'gestational_age',
            'gestational age': 'gestational_age',
            'weeks': 'gestational_age',
            'outcome': 'outcome',
            'result': 'outcome',
            'date': 'delivery_date',
            'delivery date': 'delivery_date',
            'birth date': 'delivery_date',
            'delivery': 'delivery_method',
            'delivery method': 'delivery_method',
            'method': 'delivery_method',
            'weight': 'birth_weight',
            'birth weight': 'birth_weight',
            'complications': 'complications',
            'location': 'birth_location',
            'hospital': 'birth_location',
            'multiple': 'multiple_birth'
        }
        
        for key, value in record.items():
            mapped_key = field_mappings.get(key.lower(), key.lower())
            if mapped_key in standardized:
                standardized[mapped_key] = value
        
        return standardized
    
    def _extract_text_from_element(self, element) -> str:
        """Extract clean text from XML element."""
        if element is None:
            return ""
        
        text = element.text
        if text and text.strip():
            return text.strip()
        
        all_text = ''.join(element.itertext()).strip()
        return all_text if all_text else ""
    
    def _extract_field_value(self, data: Dict[str, Any], field_name: str, default: str) -> str:
        """Extract field value handling both flat and nested structures."""
        value = data.get(field_name, default)
        
        if isinstance(value, dict):
            return value.get('display_value', value.get('value', default))
        
        return str(value) if value else default


# Register pregnancy history service with the global pipeline manager
from .clinical_data_pipeline_manager import clinical_pipeline_manager

clinical_pipeline_manager.register_service(PregnancyHistorySectionService())