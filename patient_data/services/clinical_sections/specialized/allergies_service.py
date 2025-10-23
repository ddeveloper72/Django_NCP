"""
Allergies Section Service

Specialized service for allergies and adverse reactions section data processing.

Handles:
- Allergies and adverse reactions
- Allergy severity and criticality
- Reaction manifestations
- Substance identification

Author: Django_NCP Development Team
Date: October 2025
Version: 1.0.0
"""

import logging
from typing import Dict, List, Any
from django.http import HttpRequest
from ..base.clinical_service_base import ClinicalServiceBase

logger = logging.getLogger(__name__)


class AllergiesSectionService(ClinicalServiceBase):
    """
    Specialized service for allergies and adverse reactions section data processing.
    
    Handles:
    - Allergies and adverse reactions
    - Allergy severity and criticality
    - Reaction manifestations  
    - Substance identification
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
            self._log_extraction_result('extract_from_session', len(enhanced_allergies), 'Session')
            return enhanced_allergies
        
        # Check for clinical arrays allergies
        clinical_arrays = match_data.get('enhanced_clinical_data', {}).get('clinical_sections', {})
        allergies_data = clinical_arrays.get('allergies', [])
        
        if allergies_data:
            self._log_extraction_result('extract_from_session', len(allergies_data), 'Clinical Arrays')
            return allergies_data
        
        self.logger.info("[ALLERGIES SERVICE] No allergies data found in session")
        return []
    
    def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
        """Extract allergies from CDA content using specialized parsing."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(cda_content)
            
            # Find allergies section using base method
            section = self._find_section_by_code(root, ['48765-2', '10155-0'])
            
            if section is not None:
                allergies = self._parse_allergies_xml(section)
                self._log_extraction_result('extract_from_cda', len(allergies), 'CDA')
                return allergies
            
            self.logger.info("[ALLERGIES SERVICE] No allergies section found in CDA")
            return []
            
        except Exception as e:
            self.logger.error(f"[ALLERGIES SERVICE] Error extracting allergies from CDA: {e}")
            return []
    
    def enhance_and_store(self, request: HttpRequest, session_id: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance allergies data and store in session."""
        enhanced_allergies = []
        
        for allergy_data in raw_data:
            enhanced_allergy = {
                'name': self._extract_field_value(allergy_data, 'substance', 'Unknown allergen'),
                'display_name': self._extract_field_value(allergy_data, 'substance', 'Unknown allergen'),
                'substance': self._extract_field_value(allergy_data, 'substance', 'Unknown allergen'),
                'reaction': self._extract_field_value(allergy_data, 'reaction', 'Not specified'),
                'severity': self._extract_field_value(allergy_data, 'severity', 'Not specified'),
                'criticality': self._extract_field_value(allergy_data, 'criticality', 'Not specified'),
                'onset_date': self._format_cda_date(self._extract_field_value(allergy_data, 'onset_date', 'Not specified')),
                'status': self._extract_field_value(allergy_data, 'status', 'Active'),
                'verification_status': self._extract_field_value(allergy_data, 'verification_status', 'Confirmed'),
                'source': 'cda_extraction_enhanced'
            }
            enhanced_allergies.append(enhanced_allergy)
        
        # Store in session
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        match_data['enhanced_allergies'] = enhanced_allergies
        request.session[session_key] = match_data
        request.session.modified = True
        
        self.logger.info(f"[ALLERGIES SERVICE] Enhanced and stored {len(enhanced_allergies)} allergies")
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
        
        entries = section.findall('.//hl7:entry', self.namespaces)
        for entry in entries:
            observation = entry.find('.//hl7:observation', self.namespaces)
            if observation is not None:
                allergy = self._parse_allergy_observation(observation)
                if allergy:
                    allergies.append(allergy)
        
        return allergies
    
    def _parse_allergy_observation(self, observation) -> Dict[str, Any]:
        """Parse allergy observation into structured data with enhanced temporal and severity extraction."""
        # Extract allergen substance with enhanced code-based name resolution
        participant = observation.find('.//hl7:participant', self.namespaces)
        substance = "Unknown allergen"
        if participant is not None:
            role = participant.find('.//hl7:participantRole', self.namespaces)
            if role is not None:
                entity = role.find('.//hl7:playingEntity', self.namespaces)
                if entity is not None:
                    code_elem = entity.find('hl7:code', self.namespaces)
                    if code_elem is not None:
                        # Try displayName first
                        substance = code_elem.get('displayName')
                        if not substance:
                            # Use medical code mapping instead of ID references
                            code = code_elem.get('code', '')
                            code_system = code_elem.get('codeSystem', '')
                            substance = self._map_substance_code_to_description(code, code_system)
                        
                        # If still no readable name, use formatted code
                        if not substance or substance == code_elem.get('code'):
                            substance = self._get_substance_description(code_elem.get('code', ''), code_elem.get('codeSystem', ''))

        # Extract reaction manifestation with enhanced code mapping
        reaction = "Not specified"
        value_elem = observation.find('hl7:value', self.namespaces)
        if value_elem is not None:
            reaction = value_elem.get('displayName')
            if not reaction:
                # Map reaction codes to descriptions
                reaction_code = value_elem.get('code', '')
                reaction_system = value_elem.get('codeSystem', '')
                reaction = self._map_reaction_code_to_description(reaction_code, reaction_system) or reaction_code or "Not specified"        # Look for reaction manifestation in entryRelationship
        mfst_entry = observation.find('.//hl7:entryRelationship[@typeCode="MFST"]', self.namespaces)
        if mfst_entry is not None:
            mfst_obs = mfst_entry.find('hl7:observation', self.namespaces)
            if mfst_obs is not None:
                mfst_value = mfst_obs.find('hl7:value', self.namespaces)
                if mfst_value is not None:
                    reaction = mfst_value.get('displayName', mfst_value.get('code', reaction))
        
        # Extract severity with enhanced XPath
        severity = "Not specified"
        severity_relations = observation.findall('.//hl7:entryRelationship', self.namespaces)
        for rel in severity_relations:
            if rel.get('typeCode') == 'SUBJ' and rel.get('inversionInd') == 'true':
                severity_obs = rel.find('hl7:observation', self.namespaces)
                if severity_obs is not None:
                    code_elem = severity_obs.find('hl7:code', self.namespaces)
                    if code_elem is not None and code_elem.get('code') == 'SEV':
                        severity_value = severity_obs.find('hl7:value', self.namespaces)
                        if severity_value is not None:
                            severity = severity_value.get('displayName', severity_value.get('code', 'Not specified'))

        # Extract criticality (code="82606-5")
        criticality = "Not specified"
        criticality_relations = observation.findall('.//hl7:entryRelationship', self.namespaces)
        for rel in criticality_relations:
            if rel.get('typeCode') == 'SUBJ':
                criticality_obs = rel.find('hl7:observation', self.namespaces)
                if criticality_obs is not None:
                    code_elem = criticality_obs.find('hl7:code', self.namespaces)
                    if code_elem is not None and code_elem.get('code') == '82606-5':
                        criticality_value = criticality_obs.find('hl7:value', self.namespaces)
                        if criticality_value is not None:
                            criticality = criticality_value.get('displayName', criticality_value.get('code', 'Not specified'))        # Extract onset time with enhanced effectiveTime parsing
        onset_date = "Not specified"
        effective_time = observation.find('hl7:effectiveTime', self.namespaces)
        if effective_time is not None:
            # Check for low value (onset)
            low_elem = effective_time.find('hl7:low', self.namespaces)
            if low_elem is not None:
                onset_date = low_elem.get('value', 'Not specified')
            else:
                # Single value
                onset_date = effective_time.get('value', 'Not specified')
        
        # Extract allergy status (code="33999-4")
        allergy_status = "Active"
        status_relations = observation.findall('.//hl7:entryRelationship', self.namespaces)
        for rel in status_relations:
            if rel.get('typeCode') == 'REFR':
                status_obs = rel.find('hl7:observation', self.namespaces)
                if status_obs is not None:
                    code_elem = status_obs.find('hl7:code', self.namespaces)
                    if code_elem is not None and code_elem.get('code') == '33999-4':
                        status_value = status_obs.find('hl7:value', self.namespaces)
                        if status_value is not None:
                            allergy_status = status_value.get('displayName', status_value.get('code', 'Active'))

        # Extract verification status/certainty (code="66455-7")
        verification_status = "Confirmed"
        certainty_relations = observation.findall('.//hl7:entryRelationship', self.namespaces)
        for rel in certainty_relations:
            if rel.get('typeCode') == 'SUBJ':
                certainty_obs = rel.find('hl7:observation', self.namespaces)
                if certainty_obs is not None:
                    code_elem = certainty_obs.find('hl7:code', self.namespaces)
                    if code_elem is not None and code_elem.get('code') == '66455-7':
                        certainty_value = certainty_obs.find('hl7:value', self.namespaces)
                        if certainty_value is not None:
                            verification_status = certainty_value.get('displayName', certainty_value.get('code', 'Confirmed'))
        
        self.logger.debug(f"[ALLERGIES SERVICE] Parsed allergy: {substance}, onset: {onset_date}, severity: {severity}, criticality: {criticality}")
        
        return {
            'substance': substance,
            'reaction': reaction,
            'severity': severity,
            'criticality': criticality,
            'onset_date': onset_date,
            'status': allergy_status,
            'verification_status': verification_status
        }
    
    def _resolve_text_reference(self, observation, ref_value: str) -> str:
        """Resolve text reference to actual content from CDA text section."""
        if not ref_value or not ref_value.startswith('#'):
            return ref_value
        
        # Remove the # prefix to get the ID
        target_id = ref_value[1:]
        
        # Try to find the referenced element in the parent section
        # Walk up to find the section element
        current = observation
        section = None
        for _ in range(10):  # Limit search depth
            parent = current.getparent() if hasattr(current, 'getparent') else None
            if parent is None:
                break
            if parent.tag.endswith('section'):
                section = parent
                break
            current = parent
        
        if section is not None:
            # Look for element with matching ID in the text section
            text_section = section.find('hl7:text', self.namespaces)
            if text_section is not None:
                # Search for elements with matching ID
                for elem in text_section.iter():
                    if elem.get('ID') == target_id:
                        # Return the text content, handling nested elements
                        text_content = ''.join(elem.itertext()).strip()
                        return text_content if text_content else ref_value
        
        return ref_value
    
    def _map_substance_code_to_description(self, code: str, code_system: str) -> str:
        """Map substance codes to human-readable descriptions."""
        if not code:
            return ""
        
        # SNOMED CT substance codes (2.16.840.1.113883.6.96)
        snomed_substances = {
            '260176001': 'Kiwi fruit',
            '47703008': 'Lactose',
            '111088007': 'Latex',
            '387207008': 'Aspirin',
            '387517004': 'Paracetamol',
            '387362001': 'Ibuprofen',
            '226760005': 'Dairy products',
            '412061001': 'Shellfish',
            '412062008': 'Tree nuts',
            '762952008': 'Peanuts',
            '227493005': 'Cashew nuts',
            '102261002': 'Almonds',
            '256306003': 'Penicillin',
            '387467008': 'Codeine',
            '387248006': 'Morphine'
        }
        
        if code_system == '2.16.840.1.113883.6.96':
            description = snomed_substances.get(code)
            if description:
                return description
        
        # ATC codes (Anatomical Therapeutic Chemical Classification)
        atc_substances = {
            'N02BA01': 'Acetylsalicylic acid (Aspirin)',
            'N02BE01': 'Paracetamol',
            'M01AE01': 'Ibuprofen',
            'J01CA04': 'Amoxicillin',
            'J01AA02': 'Doxycycline',
            'N02AA01': 'Morphine',
            'N02AA05': 'Oxycodone'
        }
        
        # Check various ATC code systems
        if 'atc' in code_system.lower() or code.startswith(('A', 'B', 'C', 'D', 'G', 'H', 'J', 'L', 'M', 'N', 'P', 'R', 'S', 'V')):
            description = atc_substances.get(code)
            if description:
                return description
        
        return ""
    
    def _map_reaction_code_to_description(self, code: str, code_system: str) -> str:
        """Map reaction codes to human-readable descriptions."""
        if not code:
            return ""
        
        # SNOMED CT reaction codes
        snomed_reactions = {
            '43116000': 'Anaphylaxis',
            '62315008': 'Diarrhea',
            '422587007': 'Nausea',
            '422400008': 'Vomiting',
            '418363000': 'Itching',
            '271807003': 'Skin rash',
            '247472004': 'Hives',
            '267036007': 'Dyspnea (difficulty breathing)',
            '70076002': 'Bronchospasm',
            '162290004': 'Dry mouth',
            '25064002': 'Headache',
            '404640003': 'Dizziness',
            '426000000': 'Fever'
        }
        
        if code_system == '2.16.840.1.113883.6.96':
            description = snomed_reactions.get(code)
            if description:
                return description
        
        return ""
    
    def _get_substance_description(self, code: str, code_system: str) -> str:
        """Get substance description, potentially using CTS integration."""
        # For now, use our local mapping
        # TODO: Integrate with CTS (Common Terminology Services) for real-time code resolution
        description = self._map_substance_code_to_description(code, code_system)
        
        if description:
            return description
        
        # If no mapping found, return a formatted version of the code
        if code:
            return f"Substance ({code})"
        
        return "Unknown allergen"