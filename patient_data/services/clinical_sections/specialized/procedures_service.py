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
            from defusedxml import ElementTree as ET
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
                'display_name': self._extract_field_value(procedure_data, 'display_name', 
                                                        self._extract_field_value(procedure_data, 'name', 'Unknown procedure')),
                'date': self._format_procedure_date(self._extract_field_value(procedure_data, 'date', 'Not specified')),
                'provider': self._extract_field_value(procedure_data, 'provider', 'Not specified'),
                'location': self._extract_field_value(procedure_data, 'location', 'Not specified'),
                'status': self._extract_field_value(procedure_data, 'status', 'completed'),
                'indication': self._extract_field_value(procedure_data, 'indication', 'Not specified'),
                'source': 'cda_extraction_enhanced',
                
                # Enhanced structured data
                'procedure_code': self._extract_field_value(procedure_data, 'procedure_code', None),
                'code_system': self._extract_field_value(procedure_data, 'code_system', None),
                'target_site': self._extract_field_value(procedure_data, 'target_site', None),
                'laterality': self._extract_field_value(procedure_data, 'laterality', None),
                'template_id': self._extract_field_value(procedure_data, 'template_id', None),
                'procedure_id': self._extract_field_value(procedure_data, 'procedure_id', None),
                'text_reference': self._extract_field_value(procedure_data, 'text_reference', None)
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
        """Parse procedures section XML into structured data with narrative enhancement."""
        procedures = []
        
        # First, extract narrative text mapping for resolving references
        narrative_mapping = self._extract_narrative_mapping(section)
        
        entries = section.findall('.//hl7:entry', self.namespaces)
        for entry in entries:
            procedure_elem = entry.find('.//hl7:procedure', self.namespaces)
            if procedure_elem is not None:
                procedure = self._parse_procedure_element(procedure_elem)
                
                # Enhance with narrative text if available
                if procedure and narrative_mapping:
                    procedure = self._enhance_with_narrative(procedure, narrative_mapping)
                
                if procedure:
                    procedures.append(procedure)
        
        return procedures
    
    def _extract_narrative_mapping(self, section) -> Dict[str, str]:
        """Extract narrative text mapping from section for reference resolution."""
        narrative_mapping = {}
        
        # Look for text elements with IDs and content references
        text_section = section.find('hl7:text', self.namespaces)
        if text_section is not None:
            # Extract paragraph mappings
            paragraphs = text_section.findall('.//hl7:paragraph', self.namespaces)
            for para in paragraphs:
                para_id = para.get('ID')
                if para_id:
                    para_text = ''.join(para.itertext()).strip()
                    narrative_mapping[para_id] = para_text
            
            # Extract content mappings from table cells
            content_elements = text_section.findall('.//hl7:content', self.namespaces)
            for content in content_elements:
                content_id = content.get('ID')
                if content_id:
                    content_text = ''.join(content.itertext()).strip()
                    narrative_mapping[content_id] = content_text
        
        return narrative_mapping
    
    def _enhance_with_narrative(self, procedure: Dict[str, Any], narrative_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Enhance procedure data with narrative text content."""
        # Try to resolve text reference for procedure name
        text_ref = procedure.get('text_reference')
        if text_ref and text_ref in narrative_mapping:
            narrative_text = narrative_mapping[text_ref]
            # Extract procedure name and date from narrative
            if ',' in narrative_text:
                parts = narrative_text.split(',')
                if len(parts) >= 2:
                    procedure_name = parts[0].strip()
                    if procedure_name and procedure_name != 'Unknown procedure':
                        procedure['name'] = procedure_name
                        procedure['display_name'] = procedure_name
        
        # Try to resolve originalText reference for procedure name if still unknown
        if procedure.get('name', '').startswith('Procedure (ref:'):
            ref_match = procedure['name'].replace('Procedure (ref: ', '').replace(')', '')
            if ref_match in narrative_mapping:
                resolved_name = narrative_mapping[ref_match]
                if resolved_name:
                    procedure['name'] = resolved_name
                    procedure['display_name'] = resolved_name
        
        return procedure
    
    def _parse_procedure_element(self, procedure_elem) -> Dict[str, Any]:
        """Parse procedure element into structured data with comprehensive extraction."""
        # Extract procedure code and name
        code_elem = procedure_elem.find('hl7:code', self.namespaces)
        name = "Unknown procedure"
        procedure_code = None
        code_system = None
        
        if code_elem is not None:
            procedure_code = code_elem.get('code')
            code_system = code_elem.get('codeSystem')
            name = code_elem.get('displayName', 'Unknown procedure')
            
            # Try to get name from originalText reference if displayName not available
            if name == 'Unknown procedure':
                original_text = code_elem.find('hl7:originalText', self.namespaces)
                if original_text is not None:
                    ref_elem = original_text.find('hl7:reference', self.namespaces)
                    if ref_elem is not None:
                        ref_value = ref_elem.get('value', '').replace('#', '')
                        # Store reference for potential narrative lookup
                        name = f"Procedure (ref: {ref_value})"
        
        # Extract date
        time_elem = procedure_elem.find('hl7:effectiveTime', self.namespaces)
        date = "Not specified"
        if time_elem is not None:
            date = time_elem.get('value', 'Not specified')
        
        # Extract status
        status_elem = procedure_elem.find('hl7:statusCode', self.namespaces)
        status = "completed"
        if status_elem is not None:
            status = status_elem.get('code', 'completed')
        
        # Extract target site information
        target_site_info = self._extract_target_site(procedure_elem)
        
        # Extract template ID for CDA compliance
        template_elem = procedure_elem.find('hl7:templateId', self.namespaces)
        template_id = None
        if template_elem is not None:
            template_id = template_elem.get('root')
        
        # Extract procedure ID
        id_elem = procedure_elem.find('hl7:id', self.namespaces)
        procedure_id = None
        if id_elem is not None:
            procedure_id = id_elem.get('root')
        
        # Extract narrative text reference
        text_elem = procedure_elem.find('hl7:text', self.namespaces)
        text_reference = None
        if text_elem is not None:
            ref_elem = text_elem.find('hl7:reference', self.namespaces)
            if ref_elem is not None:
                text_reference = ref_elem.get('value', '').replace('#', '')
        
        procedure_data = {
            'name': name,
            'date': date,
            'provider': 'Not specified',
            'location': target_site_info.get('location', 'Not specified'),
            'status': status,
            'indication': 'Not specified',
            'procedure_code': procedure_code,
            'code_system': code_system,
            'target_site': target_site_info.get('site_description'),
            'laterality': target_site_info.get('laterality'),
            'template_id': template_id,
            'procedure_id': procedure_id,
            'text_reference': text_reference
        }
        
        return procedure_data
    
    def _extract_target_site(self, procedure_elem) -> Dict[str, Any]:
        """Extract target site information including anatomical location and laterality."""
        target_site_elem = procedure_elem.find('hl7:targetSiteCode', self.namespaces)
        
        if target_site_elem is None:
            return {
                'site_description': None,
                'laterality': None,
                'location': 'Not specified'
            }
        
        # Get site description
        site_description = target_site_elem.get('displayName', 'Unknown site')
        site_code = target_site_elem.get('code')
        
        # Extract laterality from qualifier
        laterality = None
        qualifier_elem = target_site_elem.find('hl7:qualifier', self.namespaces)
        if qualifier_elem is not None:
            name_elem = qualifier_elem.find('hl7:name', self.namespaces)
            value_elem = qualifier_elem.find('hl7:value', self.namespaces)
            
            if (name_elem is not None and value_elem is not None and 
                name_elem.get('displayName') == 'Laterality'):
                laterality = value_elem.get('displayName')
        
        # Construct comprehensive location description
        location_parts = []
        if site_description and site_description != 'Unknown site':
            location_parts.append(site_description)
        if laterality:
            location_parts.append(f"({laterality})")
        
        location = ' '.join(location_parts) if location_parts else 'Not specified'
        
        return {
            'site_description': site_description,
            'site_code': site_code,
            'laterality': laterality,
            'location': location
        }
    
    def _format_procedure_date(self, cda_date: str) -> str:
        """
        Format CDA date string to ISO format (YYYY-MM-DD)
        
        Args:
            cda_date: CDA date string (e.g., "20141020" or "2014-10-20")
            
        Returns:
            str: Formatted date string in YYYY-MM-DD format
        """
        from datetime import datetime
        import re
        
        if not cda_date or cda_date == 'Not specified':
            return 'Not specified'
        
        try:
            # Remove any timezone info and clean up
            date_clean = re.sub(r'[T\+\-].*$', '', cda_date)
            
            # Handle different date formats
            if len(date_clean) == 8 and date_clean.isdigit():
                # Format: YYYYMMDD
                date_obj = datetime.strptime(date_clean, '%Y%m%d')
            elif '-' in date_clean:
                # Format: YYYY-MM-DD (already correct)
                return date_clean
            elif '/' in date_clean:
                # Format: MM/DD/YYYY or DD/MM/YYYY
                parts = date_clean.split('/')
                if len(parts[2]) == 4:  # YYYY is 4 digits
                    date_obj = datetime.strptime(date_clean, '%m/%d/%Y')
                else:
                    date_obj = datetime.strptime(date_clean, '%d/%m/%Y')
            else:
                return cda_date  # Return original if format unknown
            
            # Format as "YYYY-MM-DD"
            return date_obj.strftime("%Y-%m-%d")
            
        except (ValueError, IndexError) as e:
            self.logger.warning(f"Could not parse procedure date '{cda_date}': {e}")
            return cda_date  # Return original if parsing fails