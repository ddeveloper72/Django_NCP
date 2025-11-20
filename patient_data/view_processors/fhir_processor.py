"""
FHIR View Processor

Dedicated processor for FHIR bundle data that provides clean, consistent
context building for FHIR-based patient data display.

This replaces the hybrid FHIR/CDA processing in the main view to eliminate
data loss and confusion.
"""

import logging
from typing import Dict, Any, Optional, Union
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from .context_builders import ContextBuilder
from ..services.fhir_bundle_parser import FHIRBundleParser
from ..services.fhir_agent_service import FHIRAgentService

logger = logging.getLogger(__name__)


class FHIRViewProcessor:
    """
    Dedicated FHIR bundle processor for patient view rendering
    
    Provides clean separation from CDA processing and ensures consistent
    context structure for FHIR-based patient data.
    """
    
    def __init__(self):
        """Initialize FHIR processor with required services"""
        self.fhir_parser = FHIRBundleParser()
        self.fhir_agent = FHIRAgentService()
        self.context_builder = ContextBuilder()
    
    def process_fhir_document(self, request, session_id: str, cda_type: Optional[str] = None) -> HttpResponse:
        """
        Router-compatible wrapper for FHIR document processing
        
        Args:
            request: Django HTTP request
            session_id: Session identifier
            cda_type: CDA type preference (unused for FHIR but kept for interface consistency)
            
        Returns:
            HttpResponse with rendered template
        """
        logger.info(f"[FHIR PROCESSOR] Router called process_fhir_document for session {session_id}")
        
        # Get match data from session
        match_data = request.session.get(f"patient_match_{session_id}", {})
        
        if not match_data:
            logger.error(f"[FHIR PROCESSOR] No session data found for session {session_id}")
            context = self.context_builder.build_base_context(session_id, 'FHIR')
            return self._handle_fhir_error(
                request,
                f"No patient session data found for session {session_id}",
                session_id,
                context
            )
        
        # Delegate to the main processing method
        return self.process_fhir_patient_view(request, session_id, match_data, cda_type)
    
    def process_fhir_patient_view(
        self, 
        request, 
        session_id: str, 
        match_data: Dict[str, Any], 
        cda_type: Optional[str] = None
    ) -> HttpResponse:
        """
        Process FHIR patient view with dedicated FHIR pipeline
        
        Args:
            request: Django HTTP request
            session_id: Session identifier
            match_data: Session match data containing FHIR bundle
            cda_type: CDA type preference (for compatibility)
            
        Returns:
            HttpResponse with rendered template
        """
        logger.info(f"[FHIR PROCESSOR] Processing FHIR patient view for session {session_id}")
        
        try:
            # Initialize base context
            context = self.context_builder.build_base_context(session_id, 'FHIR')
            
            # Extract FHIR bundle from match data
            fhir_bundle = match_data.get('fhir_bundle')
            if not fhir_bundle:
                return self._handle_fhir_error(
                    request, 
                    "No FHIR bundle found in session data", 
                    session_id, 
                    context
                )
            
            # Parse FHIR bundle using enhanced parser
            parsed_data = self._parse_fhir_bundle(fhir_bundle)
            if not parsed_data:
                return self._handle_fhir_error(
                    request,
                    "FHIR bundle parsing failed",
                    session_id,
                    context
                )
            
            # Build context from parsed FHIR data
            self._build_fhir_context(context, parsed_data, match_data)
            
            # Add FHIR-specific metadata
            self._add_fhir_metadata(context, match_data, cda_type)
            
            # Finalize context
            context = self.context_builder.finalize_context(context)
            
            logger.info(f"[FHIR PROCESSOR] Successfully processed FHIR patient view for session {session_id}")
            logger.info(f"[VIEW PROCESSOR DEBUG] Final context source_country before render: {context.get('source_country')}")
            
            # DEBUG: Log clinical section availability
            clinical_sections_status = {
                'problems': len(context.get('problems', [])),
                'history_of_past_illness': len(context.get('history_of_past_illness', [])),
                'immunizations': len(context.get('immunizations', [])),
                'pregnancy_history': len(context.get('pregnancy_history', [])) if isinstance(context.get('pregnancy_history'), list) else 'dict',
                'medications': len(context.get('medications', [])),
                'allergies': len(context.get('allergies', [])),
                'procedures': len(context.get('procedures', [])),
                'vital_signs': len(context.get('vital_signs', [])),
                'physical_findings': len(context.get('physical_findings', [])),
                'social_history': len(context.get('social_history', [])),
                'laboratory_results': len(context.get('laboratory_results', [])),
                'medical_devices': len(context.get('medical_devices', [])),
                'advance_directives': len(context.get('advance_directives', [])),
            }
            logger.info(f"[FHIR PROCESSOR] Clinical sections status: {clinical_sections_status}")
            
            return render(request, 'patient_data/enhanced_patient_cda.html', context)
            
        except Exception as e:
            logger.error(f"[FHIR PROCESSOR] Error processing FHIR patient view: {e}")
            return self._handle_fhir_error(request, str(e), session_id, context)
    
    def _parse_fhir_bundle(self, fhir_bundle: Union[Dict, str]) -> Optional[Dict[str, Any]]:
        """
        Parse FHIR bundle using enhanced parser
        
        Args:
            fhir_bundle: FHIR bundle data
            
        Returns:
            Parsed FHIR data or None if parsing failed
        """
        try:
            logger.info("[FHIR PROCESSOR] Parsing FHIR bundle with enhanced parser")
            
            parsed_data = self.fhir_parser.parse_patient_summary_bundle(fhir_bundle)
            
            if parsed_data and parsed_data.get('success'):
                logger.info(f"[FHIR PROCESSOR] FHIR bundle parsed successfully: {parsed_data.get('sections_count', 0)} sections")
                return parsed_data
            else:
                logger.error("[FHIR PROCESSOR] FHIR bundle parsing failed")
                return None
                
        except Exception as e:
            logger.error(f"[FHIR PROCESSOR] FHIR bundle parsing error: {e}")
            return None
    
    def _build_fhir_context(
        self, 
        context: Dict[str, Any], 
        parsed_data: Dict[str, Any], 
        match_data: Dict[str, Any]
    ) -> None:
        """
        Build template context from parsed FHIR data
        
        Args:
            context: Base context to update
            parsed_data: Parsed FHIR bundle data
            match_data: Original session match data
        """
        # Add patient demographic data
        patient_identity = parsed_data.get('patient_identity', {})
        if patient_identity:
            self.context_builder.add_patient_data(context, patient_identity)
        
        # Add administrative data (CRITICAL for organization display)
        administrative_data = parsed_data.get('administrative_data', {})
        if administrative_data:
            self.context_builder.add_administrative_data(context, administrative_data)
            
            # Log custodian organization for verification
            custodian_org = administrative_data.get('custodian_organization')
            if custodian_org:
                org_name = custodian_org.get('name', 'Unknown')
                logger.info(f"[FHIR PROCESSOR] Custodian organization loaded: {org_name}")
            else:
                logger.warning("[FHIR PROCESSOR] No custodian organization in administrative data")
        
        # Add clinical data
        clinical_arrays = parsed_data.get('clinical_arrays', {})
        sections = parsed_data.get('sections', [])
        if clinical_arrays or sections:
            self.context_builder.add_clinical_data(context, clinical_arrays, sections)
            
            # Add enhanced variables for template compatibility (like CDA processor)
            context['enhanced_pregnancy_history'] = clinical_arrays.get('pregnancy_history', [])
            context['enhanced_medications'] = clinical_arrays.get('medications', [])
            context['enhanced_allergies'] = clinical_arrays.get('allergies', [])
            context['enhanced_problems'] = clinical_arrays.get('problems', [])
            context['enhanced_procedures'] = clinical_arrays.get('procedures', [])
            context['enhanced_immunizations'] = clinical_arrays.get('immunizations', [])
            context['enhanced_vital_signs'] = clinical_arrays.get('vital_signs', [])
            context['enhanced_results'] = clinical_arrays.get('results', [])
            
            logger.info(f"[FHIR PROCESSOR] Added enhanced variables: pregnancy_history={len(context['enhanced_pregnancy_history'])}")
        
        # Add healthcare provider data
        healthcare_data = parsed_data.get('healthcare_data', {})
        if healthcare_data:
            logger.info(f"[FHIR PROCESSOR DEBUG] healthcare_data from parser: practitioners={len(healthcare_data.get('practitioners', []))}, organizations={len(healthcare_data.get('organizations', []))}")
            self.context_builder.add_healthcare_data(context, healthcare_data)
        
        # Add contact data
        contact_data = parsed_data.get('contact_data', {})
        if contact_data:
            context['contact_data'] = contact_data
            # CRITICAL: Map contact_data to patient_contact_info for template compatibility with CDA
            # Templates expect 'patient_contact_info' for patient's own contact details
            context['patient_contact_info'] = {
                'addresses': contact_data.get('addresses', []),
                'telecoms': contact_data.get('telecoms', [])
            }
            logger.info(f"[FHIR PROCESSOR] Mapped contact_data to patient_contact_info: {len(contact_data.get('addresses', []))} addresses, {len(contact_data.get('telecoms', []))} telecoms")
        
        # Add extended patient data
        extended_data = parsed_data.get('patient_extended_data', {})
        if extended_data:
            context['patient_extended_data'] = extended_data
            context['extended_data'] = extended_data  # Alias for compatibility
    
    def _add_fhir_metadata(
        self, 
        context: Dict[str, Any], 
        match_data: Dict[str, Any], 
        cda_type: Optional[str]
    ) -> None:
        """
        Add FHIR-specific metadata to context
        
        Args:
            context: Context to update
            match_data: Session match data
            cda_type: CDA type preference
        """
        # Extract patient info from match data and parsed data
        patient_info = match_data.get('patient_data', {})
        patient_identity = context.get('patient_identity', {})
        
        # Get source country from patient identity (extracted from FHIR Patient resource)
        source_country = patient_identity.get('source_country', 
                                              patient_info.get('source_country', 'Unknown'))
        logger.info(f"[VIEW PROCESSOR DEBUG] patient_identity.source_country = {patient_identity.get('source_country')}, final source_country = {source_country}")
        
        metadata = {
            'confidence_score': 0.95,  # FHIR has high confidence
            'source_country': source_country,
            'source_language': 'en',  # TODO: Extract from FHIR bundle
            'file_path': 'FHIR_BUNDLE',
            'translation_quality': 'High',  # FHIR has structured data
        }
        
        self.context_builder.add_processing_metadata(context, metadata)
        
        # Add FHIR-specific context
        context.update({
            'fhir_processing': True,
            'cda_type': cda_type or 'FHIR',
            'preferred_cda_type': cda_type or 'FHIR',
            'has_l1': False,  # FHIR doesn't have L1/L3 concept
            'has_l3': False,
            'display_filename': 'FHIR Patient Summary Bundle',
            'patient_summary': {
                'data_source': 'FHIR',
                'file_path': 'FHIR_BUNDLE',
                'confidence_score': 0.95,
            }
        })
    
    def _handle_fhir_error(
        self, 
        request, 
        error_message: str, 
        session_id: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> HttpResponse:
        """
        Handle FHIR processing errors with appropriate response
        
        Args:
            request: Django HTTP request
            error_message: Error description
            session_id: Session identifier
            context: Partial context if available
            
        Returns:
            Error response
        """
        logger.error(f"[FHIR PROCESSOR] Error for session {session_id}: {error_message}")
        
        if context is None:
            context = self.context_builder.build_base_context(session_id, 'FHIR')
        
        self.context_builder.add_error(context, error_message)
        
        # Add error-specific context
        context.update({
            'processing_failed': True,
            'error_type': 'FHIR Processing Error',
            'error_details': error_message,
            'suggested_action': 'Please try refreshing the page or contact support if the issue persists.',
        })
        
        return render(request, 'patient_data/enhanced_patient_cda.html', context)
    
    def get_fhir_bundle_from_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get FHIR bundle from session data
        
        Args:
            session_id: Session identifier
            
        Returns:
            FHIR bundle data or None
        """
        try:
            return self.fhir_agent.get_fhir_bundle_from_session(session_id)
        except Exception as e:
            logger.error(f"[FHIR PROCESSOR] Error getting FHIR bundle from session {session_id}: {e}")
            return None