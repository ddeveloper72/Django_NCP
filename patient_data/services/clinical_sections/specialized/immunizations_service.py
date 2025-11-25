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
from ..cts_integration_mixin import CTSIntegrationMixin

logger = logging.getLogger(__name__)


class ImmunizationsSectionService(CTSIntegrationMixin, ClinicalServiceBase):
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
        """Enhance immunizations data and store in session with comprehensive field preservation."""
        enhanced_immunizations = []
        
        for immunization_data in raw_data:
            # Preserve all extracted fields using dict() pattern
            enhanced_immunization = dict(immunization_data)
            
            # Ensure display_name is set
            if 'display_name' not in enhanced_immunization:
                enhanced_immunization['display_name'] = enhanced_immunization.get('name', 'Unknown vaccine')
            
            # Format date_administered if present
            if 'date_administered' in enhanced_immunization and enhanced_immunization['date_administered']:
                enhanced_immunization['date_administered'] = self._format_cda_date(enhanced_immunization['date_administered'])
            
            # Mark as enhanced
            enhanced_immunization['source'] = 'cda_extraction_enhanced'
            enhanced_immunization['enhanced_data'] = True
            
            enhanced_immunizations.append(enhanced_immunization)
        
        # Store in session
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        match_data['enhanced_immunizations'] = enhanced_immunizations
        request.session[session_key] = match_data
        request.session.modified = True
        
        self.logger.info(f"[IMMUNIZATIONS SERVICE] Enhanced and stored {len(enhanced_immunizations)} immunizations with comprehensive fields")
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
        
        # Extract narrative mapping for text reference resolution
        narrative_mapping = self._extract_narrative_mapping(section)
        
        entries = section.findall('.//hl7:entry', self.namespaces)
        for entry in entries:
            substance_admin = entry.find('.//hl7:substanceAdministration', self.namespaces)
            if substance_admin is not None:
                immunization = self._parse_immunization_element(substance_admin, narrative_mapping)
                if immunization:
                    immunizations.append(immunization)
        
        return immunizations
    
    def _parse_immunization_element(self, substance_admin, narrative_mapping: Dict[str, str] = None) -> Dict[str, Any]:
        """Parse immunization element into structured data with comprehensive field extraction."""
        
        if narrative_mapping is None:
            narrative_mapping = {}
        
        # Extract vaccine name and brand name
        consumable = substance_admin.find('.//hl7:consumable', self.namespaces)
        vaccine_name = "Unknown vaccine"
        brand_name = ""
        # Agent info will be extracted from participant element later
        agent_code = ""
        agent_code_system = ""
        agent_code_system_name = ""
        agent_display_name = ""
        
        if consumable is not None:
            material = consumable.find('.//hl7:manufacturedMaterial', self.namespaces)
            if material is not None:
                # Get brand name from <name> element
                name_elem = material.find('hl7:name', self.namespaces)
                if name_elem is not None and name_elem.text:
                    brand_name = name_elem.text.strip()
                
                # Get vaccine information from <code> element
                code_elem = material.find('hl7:code', self.namespaces)
                if code_elem is not None:
                    vaccine_code = code_elem.get('code', '')
                    vaccine_code_system = code_elem.get('codeSystem', '')
                    code_display_name = code_elem.get('displayName', '')
                    
                    # Build text reference for fallback
                    text_reference = ""
                    original_text = code_elem.find('hl7:originalText', self.namespaces)
                    if original_text is not None:
                        reference = original_text.find('hl7:reference', self.namespaces)
                        if reference is not None:
                            ref_value = reference.get('value', '')
                            if ref_value.startswith('#'):
                                ref_id = ref_value[1:]
                                if ref_id in narrative_mapping:
                                    text_reference = narrative_mapping[ref_id]
                    
                    # Resolve vaccine name using CTS with fallbacks
                    vaccine_name = self._resolve_clinical_code_with_cts(
                        code=vaccine_code,
                        code_system=vaccine_code_system,
                        display_name=code_display_name,
                        text_reference=text_reference,
                        fallback_mappings=None
                    )
                    
                    logger.info(f"[IMMUNIZATIONS] Resolved vaccine: {vaccine_name} (code: {vaccine_code})")
        
        # CRITICAL: Use brand name as vaccine name if code displayName is not available
        # Brand name (<name> element) is more readable than code (e.g., "Engerix B (2294189)" vs "836374004")
        if vaccine_name == "Unknown vaccine" and brand_name:
            vaccine_name = brand_name
            logger.info(f"[IMMUNIZATIONS] Using brand name as vaccine name: {vaccine_name}")
        
        # Extract vaccination date (effectiveTime)
        time_elem = substance_admin.find('hl7:effectiveTime', self.namespaces)
        date_administered = ""
        if time_elem is not None:
            date_administered = time_elem.get('value', '')
        
        # Extract status code
        status_elem = substance_admin.find('hl7:statusCode', self.namespaces)
        status = "Active"
        if status_elem is not None:
            status_code = status_elem.get('code', 'completed')
            # Map status codes to display values
            status_mapping = {
                'completed': 'Completed',
                'active': 'Active',
                'aborted': 'Aborted',
                'suspended': 'Suspended'
            }
            status = status_mapping.get(status_code.lower(), status_code.title())
        
        # Extract dose number from repeatNumber
        dose_number = ""
        repeat_elem = substance_admin.find('hl7:repeatNumber', self.namespaces)
        if repeat_elem is not None:
            dose_value = repeat_elem.get('value', '')
            if dose_value:
                dose_number = f"Dose {dose_value}"
        
        # Extract route of administration with CTS resolution
        route_elem = substance_admin.find('hl7:routeCode', self.namespaces)
        route = ""
        if route_elem is not None:
            route_code = route_elem.get('code', '')
            route_code_system = route_elem.get('codeSystem', '')
            route_display = route_elem.get('displayName', '')
            
            if route_code:
                route = self._resolve_clinical_code_with_cts(
                    code=route_code,
                    code_system=route_code_system,
                    display_name=route_display,
                    text_reference="",
                    fallback_mappings=None
                )
        
        # Extract administration site with CTS resolution
        site_elem = substance_admin.find('hl7:approachSiteCode', self.namespaces)
        site = ""
        if site_elem is not None:
            site_code = site_elem.get('code', '')
            site_code_system = site_elem.get('codeSystem', '')
            site_display = site_elem.get('displayName', '')
            
            if site_code:
                site = self._resolve_clinical_code_with_cts(
                    code=site_code,
                    code_system=site_code_system,
                    display_name=site_display,
                    text_reference="",
                    fallback_mappings=None
                )
        
        # Extract lot number from lotNumberText
        lot_number = ""
        if consumable is not None:
            material = consumable.find('.//hl7:manufacturedMaterial', self.namespaces)
            if material is not None:
                lot_elem = material.find('hl7:lotNumberText', self.namespaces)
                if lot_elem is not None and lot_elem.text:
                    lot_number = lot_elem.text.strip()
        
        # Extract marketing authorization holder (manufacturer organization)
        manufacturer = ""
        if consumable is not None:
            product = consumable.find('.//hl7:manufacturedProduct', self.namespaces)
            if product is not None:
                org = product.find('.//hl7:manufacturerOrganization', self.namespaces)
                if org is not None:
                    name_elem = org.find('hl7:name', self.namespaces)
                    if name_elem is not None and name_elem.text:
                        manufacturer = name_elem.text.strip()
        
        # Extract administering center (performer)
        administering_center = ""
        performer = substance_admin.find('.//hl7:performer', self.namespaces)
        if performer is not None:
            assigned_entity = performer.find('.//hl7:assignedEntity', self.namespaces)
            if assigned_entity is not None:
                # Get organization name
                org = assigned_entity.find('.//hl7:representedOrganization', self.namespaces)
                if org is not None:
                    name_elem = org.find('hl7:name', self.namespaces)
                    if name_elem is not None and name_elem.text:
                        administering_center = name_elem.text.strip()
        
        # Extract health professional identification
        health_professional_id = ""
        health_professional_name = ""
        if performer is not None:
            assigned_entity = performer.find('.//hl7:assignedEntity', self.namespaces)
            if assigned_entity is not None:
                # Get professional ID
                id_elem = assigned_entity.find('hl7:id', self.namespaces)
                if id_elem is not None:
                    extension = id_elem.get('extension', '')
                    root = id_elem.get('root', '')
                    if extension:
                        health_professional_id = extension
                    elif root:
                        health_professional_id = root
                
                # Get professional name
                person = assigned_entity.find('.//hl7:assignedPerson', self.namespaces)
                if person is not None:
                    name_elem = person.find('.//hl7:name', self.namespaces)
                    if name_elem is not None:
                        # Concatenate name parts
                        given = name_elem.find('hl7:given', self.namespaces)
                        family = name_elem.find('hl7:family', self.namespaces)
                        name_parts = []
                        if given is not None and given.text:
                            name_parts.append(given.text.strip())
                        if family is not None and family.text:
                            name_parts.append(family.text.strip())
                        health_professional_name = ' '.join(name_parts)
        
        # Extract country of vaccination
        country = ""
        if performer is not None:
            assigned_entity = performer.find('.//hl7:assignedEntity', self.namespaces)
            if assigned_entity is not None:
                addr = assigned_entity.find('.//hl7:addr', self.namespaces)
                if addr is not None:
                    country_elem = addr.find('hl7:country', self.namespaces)
                    if country_elem is not None and country_elem.text:
                        country = country_elem.text.strip()
        
        # Extract annotations (text comments)
        annotations = ""
        text_elem = substance_admin.find('hl7:text', self.namespaces)
        if text_elem is not None:
            # Try to get direct text content
            if text_elem.text and text_elem.text.strip():
                annotations = text_elem.text.strip()
        
        # Extract agent from participant element (vaccine agent, not manufacturer)
        agent_code = ""
        agent_code_system = ""
        agent_display_name = ""
        participant = substance_admin.find('.//hl7:participant[@typeCode="IND"]', self.namespaces)
        if participant is not None:
            participant_role = participant.find('.//hl7:participantRole[@classCode="AGNT"]', self.namespaces)
            if participant_role is not None:
                agent_code_elem = participant_role.find('hl7:code', self.namespaces)
                if agent_code_elem is not None:
                    agent_code = agent_code_elem.get('code', '')
                    agent_code_system = agent_code_elem.get('codeSystem', '')
                    agent_code_system_name = agent_code_elem.get('codeSystemName', '')
                    agent_display_from_xml = agent_code_elem.get('displayName', '')
                    
                    # Resolve agent using CTS (SNOMED CT, ICD-10, etc.)
                    if agent_code and agent_code.upper() != 'UNK':
                        agent_display_name = self._resolve_clinical_code_with_cts(
                            code=agent_code,
                            code_system=agent_code_system,
                            display_name=agent_display_from_xml,
                            text_reference="",
                            fallback_mappings=None
                        )
                        logger.info(f"[IMMUNIZATIONS] Resolved agent: {agent_display_name} (code: {agent_code})")
        
        # Extract dose number from entryRelationship observation (LOINC 30973-2)
        dose_number_value = ""
        entry_relationships = substance_admin.findall('.//hl7:entryRelationship', self.namespaces)
        for entry_rel in entry_relationships:
            observation = entry_rel.find('.//hl7:observation', self.namespaces)
            if observation is not None:
                obs_code = observation.find('hl7:code', self.namespaces)
                if obs_code is not None and obs_code.get('code') == '30973-2':  # LOINC code for Dose Number
                    value_elem = observation.find('hl7:value', self.namespaces)
                    if value_elem is not None:
                        dose_value = value_elem.get('value', '')
                        if dose_value:
                            dose_number_value = f"Dose {dose_value}"
                            logger.info(f"[IMMUNIZATIONS] Found dose number from observation: {dose_number_value}")
        
        # Use dose_number_value if found, otherwise keep the repeatNumber value
        if dose_number_value:
            dose_number = dose_number_value
        
        return {
            'name': vaccine_name,
            'vaccine_name': vaccine_name,
            'brand_name': brand_name,
            'date_administered': date_administered,
            'agent_code': agent_code,
            'agent_code_system': agent_code_system,
            'agent_code_system_name': agent_code_system_name,
            'agent_display_name': agent_display_name,
            'marketing_authorization_holder': manufacturer,
            'dose_number': dose_number,
            'lot_number': lot_number,
            'batch_number': lot_number,  # Same as lot_number
            'route': route,
            'site': site,
            'status': status,
            'administering_center': administering_center,
            'health_professional_id': health_professional_id,
            'health_professional_name': health_professional_name,
            'country_of_vaccination': country,
            'annotations': annotations
        }
    
    def _extract_narrative_mapping(self, section) -> Dict[str, str]:
        """Extract narrative text mapping from section for reference resolution."""
        narrative_mapping = {}
        
        text_section = section.find('hl7:text', self.namespaces)
        if text_section is not None:
            # Extract all elements with ID attribute
            for elem in text_section.iter():
                elem_id = elem.get('ID')
                if elem_id:
                    # Get all text content, handling nested elements
                    elem_text = ''.join(elem.itertext()).strip()
                    if elem_text:
                        narrative_mapping[elem_id] = elem_text
                        logger.debug(f"[IMMUNIZATIONS] Mapped narrative ID '{elem_id}' -> '{elem_text[:50]}...'")
        
        logger.info(f"[IMMUNIZATIONS] Extracted {len(narrative_mapping)} narrative text references")
        return narrative_mapping