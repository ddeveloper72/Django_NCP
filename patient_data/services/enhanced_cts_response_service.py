"""
Enhanced CTS Response Service
Provides structured clinical terminology responses with comprehensive medical data.

Architecture: XML → CTS Agent → MVC → Structured Object → Template
Returns: {code, code_name, description, agent, medication_text} objects
"""

import logging
from typing import Dict, Any, Optional, List
from django.conf import settings

from translation_services.terminology_translator import TerminologyTranslator
from translation_services.cts_integration import CTSAPIClient, MVCManager
from translation_services.mvc_models import ValueSetConcept, ConceptTranslation

logger = logging.getLogger(__name__)


class EnhancedCTSResponseService:
    """
    Enhanced Clinical Terminology Service providing structured responses
    for all clinical sections with comprehensive medical terminology data.
    """
    
    def __init__(self):
        """Initialize with existing CTS infrastructure"""
        self.terminology_translator = TerminologyTranslator()
        self.cts_client = CTSAPIClient()
        self.mvc_manager = MVCManager()
        
    def resolve_medication_code(
        self, 
        code: str, 
        code_system: str = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Resolve medication code to comprehensive structured response
        
        Args:
            code: Medication code (e.g., "H03AA01")
            code_system: Code system OID 
            context: Additional CDA context for enhanced resolution
            
        Returns:
            {
                'code': 'H03AA01',
                'code_name': 'Levothyroxine sodium',
                'description': 'Thyroid hormone replacement therapy',
                'agent': 'ATC',
                'medication_text': 'Levothyroxine sodium - Thyroid hormone replacement',
                'therapeutic_class': 'Thyroid preparations',
                'route': 'Oral',
                'form': 'Tablet',
                'strength': '50 mcg',
                'has_terminology': True,
                'source': 'CTS_MVC'
            }
        """
        try:
            # Primary CTS resolution with dual-key lookup
            structured_response = self._resolve_with_dual_key(code, code_system)
            
            if structured_response:
                # Enhance with medication-specific data
                structured_response = self._enhance_medication_response(
                    structured_response, context
                )
                structured_response['agent'] = self._determine_agent_system(code_system)
                structured_response['medication_text'] = self._generate_medication_text(
                    structured_response
                )
                
                logger.info(f"CTS enhanced medication resolution: {code} → {structured_response['code_name']}")
                return structured_response
                
        except Exception as e:
            logger.warning(f"Enhanced CTS medication resolution failed for {code}: {e}")
            
        # Fallback response maintaining template compatibility
        return self._create_fallback_response(code, 'medication')
        
    def resolve_allergy_code(
        self, 
        code: str, 
        code_system: str = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Resolve allergy/adverse reaction code to structured response
        
        Returns:
            {
                'code': '387207008',
                'code_name': 'Penicillin',
                'description': 'Beta-lactam antibiotic allergen',
                'agent': 'SNOMED_CT',
                'medication_text': 'Penicillin allergy - Beta-lactam sensitivity',
                'allergen_type': 'Drug',
                'severity': 'Moderate',
                'manifestation': 'Skin rash',
                'has_terminology': True,
                'source': 'CTS_MVC'
            }
        """
        try:
            structured_response = self._resolve_with_dual_key(code, code_system)
            
            if structured_response:
                # Enhance with allergy-specific data
                structured_response = self._enhance_allergy_response(
                    structured_response, context
                )
                structured_response['agent'] = self._determine_agent_system(code_system)
                structured_response['medication_text'] = self._generate_allergy_text(
                    structured_response
                )
                
                return structured_response
                
        except Exception as e:
            logger.warning(f"Enhanced CTS allergy resolution failed for {code}: {e}")
            
        return self._create_fallback_response(code, 'allergy')
        
    def resolve_procedure_code(
        self, 
        code: str, 
        code_system: str = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Resolve procedure code to structured response
        
        Returns:
            {
                'code': '80146002',
                'code_name': 'Appendectomy',
                'description': 'Surgical removal of appendix',
                'agent': 'SNOMED_CT',
                'medication_text': 'Appendectomy - Laparoscopic surgical procedure',
                'procedure_type': 'Surgical',
                'body_site': 'Appendix',
                'approach': 'Laparoscopic',
                'has_terminology': True,
                'source': 'CTS_MVC'
            }
        """
        try:
            structured_response = self._resolve_with_dual_key(code, code_system)
            
            if structured_response:
                structured_response = self._enhance_procedure_response(
                    structured_response, context
                )
                structured_response['agent'] = self._determine_agent_system(code_system)
                structured_response['medication_text'] = self._generate_procedure_text(
                    structured_response
                )
                
                return structured_response
                
        except Exception as e:
            logger.warning(f"Enhanced CTS procedure resolution failed for {code}: {e}")
            
        return self._create_fallback_response(code, 'procedure')
        
    def resolve_vital_sign_code(
        self, 
        code: str, 
        code_system: str = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Resolve vital signs/observation code to structured response
        
        Returns:
            {
                'code': '8480-6',
                'code_name': 'Systolic blood pressure',
                'description': 'Systolic arterial pressure measurement',
                'agent': 'LOINC',
                'medication_text': 'Systolic BP - Arterial pressure reading',
                'measurement_type': 'Pressure',
                'unit': 'mmHg',
                'normal_range': '90-140 mmHg',
                'has_terminology': True,
                'source': 'CTS_MVC'
            }
        """
        try:
            structured_response = self._resolve_with_dual_key(code, code_system)
            
            if structured_response:
                structured_response = self._enhance_vital_sign_response(
                    structured_response, context
                )
                structured_response['agent'] = self._determine_agent_system(code_system)
                structured_response['medication_text'] = self._generate_vital_sign_text(
                    structured_response
                )
                
                return structured_response
                
        except Exception as e:
            logger.warning(f"Enhanced CTS vital sign resolution failed for {code}: {e}")
            
        return self._create_fallback_response(code, 'vital_sign')
        
    def resolve_laboratory_code(
        self, 
        code: str, 
        code_system: str = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Resolve laboratory test code to structured response
        
        Returns:
            {
                'code': '33747-0',
                'code_name': 'Hemoglobin A1c',
                'description': 'Glycated hemoglobin measurement',
                'agent': 'LOINC',
                'medication_text': 'HbA1c - Diabetes monitoring test',
                'test_type': 'Chemistry',
                'specimen': 'Blood',
                'unit': '%',
                'reference_range': '4.0-6.0%',
                'has_terminology': True,
                'source': 'CTS_MVC'
            }
        """
        try:
            structured_response = self._resolve_with_dual_key(code, code_system)
            
            if structured_response:
                structured_response = self._enhance_laboratory_response(
                    structured_response, context
                )
                structured_response['agent'] = self._determine_agent_system(code_system)
                structured_response['medication_text'] = self._generate_laboratory_text(
                    structured_response
                )
                
                return structured_response
                
        except Exception as e:
            logger.warning(f"Enhanced CTS laboratory resolution failed for {code}: {e}")
            
        return self._create_fallback_response(code, 'laboratory')
        
    def _resolve_with_dual_key(
        self, 
        code: str, 
        code_system: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Core dual-key resolution using existing CTS infrastructure
        Leverages TerminologyTranslator and MVC data
        """
        try:
            # Primary resolution using TerminologyTranslator
            resolved_display = self.terminology_translator.resolve_code(code, code_system)
            
            if resolved_display:
                # Get comprehensive data from MVC
                concept = ValueSetConcept.objects.filter(
                    code=code.strip(),
                    status='active'
                ).first()
                
                if concept:
                    # Build structured response from MVC data
                    response = {
                        'code': code,
                        'code_name': resolved_display,
                        'description': concept.definition or resolved_display,
                        'has_terminology': True,
                        'source': 'CTS_MVC',
                        'concept_id': concept.id,
                        'value_set': concept.value_set.name if concept.value_set else None
                    }
                    
                    # Add translation if available
                    translation = ConceptTranslation.objects.filter(
                        concept=concept,
                        language_code=getattr(settings, 'LANGUAGE_CODE', 'en')
                    ).first()
                    
                    if translation:
                        response['translated_name'] = translation.translated_display
                        response['translated_description'] = translation.translated_definition
                        
                    return response
                    
        except Exception as e:
            logger.warning(f"Dual-key CTS resolution failed for {code}: {e}")
            
        return None
        
    def _enhance_medication_response(
        self, 
        response: Dict[str, Any], 
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Enhance medication response with therapeutic data"""
        if context:
            # Extract additional medication context from CDA
            response.update({
                'therapeutic_class': context.get('therapeutic_class', ''),
                'route': context.get('route', ''),
                'form': context.get('form', ''),
                'strength': context.get('strength', ''),
                'manufacturer': context.get('manufacturer', '')
            })
            
        return response
        
    def _enhance_allergy_response(
        self, 
        response: Dict[str, Any], 
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Enhance allergy response with reaction data"""
        if context:
            response.update({
                'allergen_type': context.get('allergen_type', 'Unknown'),
                'severity': context.get('severity', 'Unknown'),
                'manifestation': context.get('manifestation', ''),
                'onset': context.get('onset', ''),
                'status': context.get('status', 'Active')
            })
            
        return response
        
    def _enhance_procedure_response(
        self, 
        response: Dict[str, Any], 
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Enhance procedure response with surgical data"""
        if context:
            response.update({
                'procedure_type': context.get('procedure_type', 'Clinical'),
                'body_site': context.get('body_site', ''),
                'approach': context.get('approach', ''),
                'device': context.get('device', ''),
                'performer': context.get('performer', '')
            })
            
        return response
        
    def _enhance_vital_sign_response(
        self, 
        response: Dict[str, Any], 
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Enhance vital sign response with measurement data"""
        if context:
            response.update({
                'measurement_type': context.get('measurement_type', 'Observation'),
                'unit': context.get('unit', ''),
                'normal_range': context.get('normal_range', ''),
                'interpretation': context.get('interpretation', ''),
                'method': context.get('method', '')
            })
            
        return response
        
    def _enhance_laboratory_response(
        self, 
        response: Dict[str, Any], 
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Enhance laboratory response with test data"""
        if context:
            response.update({
                'test_type': context.get('test_type', 'Laboratory'),
                'specimen': context.get('specimen', 'Blood'),
                'unit': context.get('unit', ''),
                'reference_range': context.get('reference_range', ''),
                'abnormal_flag': context.get('abnormal_flag', '')
            })
            
        return response
        
    def _determine_agent_system(self, code_system: str = None) -> str:
        """Determine the agent system from code system OID"""
        if not code_system:
            return 'Unknown'
            
        # Map common OIDs to agent systems
        agent_mappings = {
            '2.16.840.1.113883.6.1': 'LOINC',
            '2.16.840.1.113883.6.96': 'SNOMED_CT',
            '2.16.840.1.113883.6.88': 'RxNorm',
            '2.16.840.1.113883.6.73': 'ATC',
            '2.16.840.1.113883.6.90': 'ICD10CM',
            '2.16.840.1.113883.6.103': 'ICD9CM',
            '2.16.840.1.113883.6.4': 'ICD10PCS'
        }
        
        return agent_mappings.get(code_system, 'Custom')
        
    def _generate_medication_text(self, response: Dict[str, Any]) -> str:
        """Generate comprehensive medication text"""
        base_text = f"{response.get('code_name', response['code'])}"
        
        if response.get('therapeutic_class'):
            base_text += f" - {response['therapeutic_class']}"
        elif response.get('description'):
            base_text += f" - {response['description']}"
            
        return base_text
        
    def _generate_allergy_text(self, response: Dict[str, Any]) -> str:
        """Generate comprehensive allergy text"""
        base_text = f"{response.get('code_name', response['code'])} allergy"
        
        if response.get('allergen_type'):
            base_text += f" - {response['allergen_type']} sensitivity"
            
        return base_text
        
    def _generate_procedure_text(self, response: Dict[str, Any]) -> str:
        """Generate comprehensive procedure text"""
        base_text = f"{response.get('code_name', response['code'])}"
        
        if response.get('approach'):
            base_text += f" - {response['approach']} procedure"
        elif response.get('procedure_type'):
            base_text += f" - {response['procedure_type']} intervention"
            
        return base_text
        
    def _generate_vital_sign_text(self, response: Dict[str, Any]) -> str:
        """Generate comprehensive vital sign text"""
        base_text = f"{response.get('code_name', response['code'])}"
        
        if response.get('measurement_type'):
            base_text += f" - {response['measurement_type']} measurement"
            
        return base_text
        
    def _generate_laboratory_text(self, response: Dict[str, Any]) -> str:
        """Generate comprehensive laboratory text"""
        base_text = f"{response.get('code_name', response['code'])}"
        
        if response.get('test_type'):
            base_text += f" - {response['test_type']} test"
            
        return base_text
        
    def _create_fallback_response(
        self, 
        code: str, 
        section_type: str
    ) -> Dict[str, Any]:
        """Create fallback response when CTS resolution fails"""
        return {
            'code': code,
            'code_name': f"Unknown {section_type.replace('_', ' ').title()}",
            'description': f"Code {code} - Resolution pending",
            'agent': 'Unknown',
            'medication_text': f"{code} - Awaiting terminology resolution",
            'has_terminology': False,
            'source': 'Fallback',
            'needs_resolution': True
        }