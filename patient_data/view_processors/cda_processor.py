"""
CDA View Processor

Dedicated processor for CDA document data that provides clean, consistent
context building for CDA-based patient data display.

This replaces the hybrid FHIR/CDA processing in the main view to eliminate
data loss and confusion.
"""

import logging
from typing import Dict, Any, Optional, List
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from .context_builders import ContextBuilder

logger = logging.getLogger(__name__)


class CDAViewProcessor:
    """
    Dedicated CDA document processor for patient view rendering
    
    Provides clean separation from FHIR processing and ensures consistent
    context structure for CDA-based patient data.
    """
    
    def __init__(self):
        """Initialize CDA processor with required services"""
        self.context_builder = ContextBuilder()
        # Import CDA services only when needed to avoid circular imports
        self._cda_display_service = None
        self._comprehensive_service = None
    
    @property
    def cda_display_service(self):
        """Lazy-load CDA display service"""
        if self._cda_display_service is None:
            from ..services.cda_display_service import CDADisplayService
            self._cda_display_service = CDADisplayService()
        return self._cda_display_service
    
    @property
    def comprehensive_service(self):
        """Lazy-load comprehensive clinical data service"""
        if self._comprehensive_service is None:
            from ..services.comprehensive_clinical_data_service import ComprehensiveClinicalDataService
            self._comprehensive_service = ComprehensiveClinicalDataService()
        return self._comprehensive_service
    
    def process_cda_document(self, request, session_id: str, cda_type: Optional[str] = None) -> HttpResponse:
        """
        Router-compatible wrapper for CDA document processing
        
        Args:
            request: Django HTTP request
            session_id: Session identifier
            cda_type: CDA type preference ('L1' or 'L3')
            
        Returns:
            HttpResponse with rendered template
        """
        logger.info(f"[CDA PROCESSOR] Router called process_cda_document for session {session_id}")
        
        # Get match data from session
        match_data = request.session.get(f"patient_match_{session_id}", {})
        
        if not match_data:
            logger.error(f"[CDA PROCESSOR] No session data found for session {session_id}")
            context = self.context_builder.build_base_context(session_id, 'CDA')
            return self._handle_cda_error(
                request,
                f"No patient session data found for session {session_id}",
                session_id,
                context
            )
        
        # Delegate to the main processing method
        return self.process_cda_patient_view(request, session_id, match_data, cda_type)
    
    def process_cda_patient_view(
        self, 
        request, 
        session_id: str, 
        match_data: Dict[str, Any], 
        cda_type: Optional[str] = None
    ) -> HttpResponse:
        """
        Process CDA patient view with dedicated CDA pipeline
        
        Args:
            request: Django HTTP request
            session_id: Session identifier
            match_data: Session match data containing CDA content
            cda_type: CDA type preference ('L1' or 'L3')
            
        Returns:
            HttpResponse with rendered template
        """
        logger.info(f"[CDA PROCESSOR] Processing CDA patient view for session {session_id}")
        
        try:
            # Initialize base context
            context = self.context_builder.build_base_context(session_id, 'CDA')
            
            # Extract CDA content from match data
            cda_content, actual_cda_type = self._get_cda_content(match_data, cda_type)
            if not cda_content:
                return self._handle_cda_error(
                    request,
                    "No CDA content found in session data",
                    session_id,
                    context
                )
            
            # Parse CDA document
            parsed_data = self._parse_cda_document(cda_content, session_id)
            if not parsed_data:
                return self._handle_cda_error(
                    request,
                    "CDA document parsing failed",
                    session_id,
                    context
                )
            
            # Build context from parsed CDA data
            self._build_cda_context(context, parsed_data, match_data)
            
            # Add CDA-specific metadata
            self._add_cda_metadata(context, match_data, cda_content, actual_cda_type)
            
            # Finalize context
            context = self.context_builder.finalize_context(context)
            
            logger.info(f"[CDA PROCESSOR] Successfully processed CDA patient view for session {session_id}")
            
            return render(request, 'patient_data/enhanced_patient_cda.html', context)
            
        except Exception as e:
            logger.error(f"[CDA PROCESSOR] Error processing CDA patient view: {e}")
            return self._handle_cda_error(request, str(e), session_id, context)
    
    def _get_cda_content(self, match_data: Dict[str, Any], cda_type: Optional[str]) -> tuple:
        """
        Extract CDA content from match data based on type preference
        
        Args:
            match_data: Session match data
            cda_type: Preferred CDA type ('L1' or 'L3')
            
        Returns:
            Tuple of (cda_content, actual_cda_type)
        """
        # Determine preferred CDA type
        preferred_type = cda_type or match_data.get('preferred_cda_type', 'L3')
        
        # Try to get requested type first
        if preferred_type.upper() == 'L1':
            cda_content = match_data.get('l1_cda_content')
            if cda_content and cda_content.strip():
                return cda_content, 'L1'
        
        elif preferred_type.upper() == 'L3':
            cda_content = match_data.get('l3_cda_content')
            if cda_content and cda_content.strip():
                return cda_content, 'L3'
        
        # Fallback to any available content
        for content_key, type_name in [
            ('l3_cda_content', 'L3'),
            ('l1_cda_content', 'L1'),
            ('cda_content', 'Generic')
        ]:
            cda_content = match_data.get(content_key)
            if cda_content and cda_content.strip() and '<!-- No CDA content available -->' not in cda_content:
                logger.info(f"[CDA PROCESSOR] Using {type_name} CDA content as fallback")
                return cda_content, type_name
        
        logger.warning("[CDA PROCESSOR] No valid CDA content found in match data")
        return None, None
    
    def _parse_cda_document(self, cda_content: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Parse CDA document using CDA display service
        
        Args:
            cda_content: CDA XML content
            session_id: Session identifier
            
        Returns:
            Parsed CDA data or None if parsing failed
        """
        try:
            logger.info(f"[CDA PROCESSOR] Parsing CDA document for session {session_id}")
            
            # Use CDA display service for enhanced parsing
            clinical_data = self.cda_display_service.extract_patient_clinical_data(session_id)
            
            if clinical_data:
                logger.info(f"[CDA PROCESSOR] CDA document parsed successfully")
                return clinical_data
            else:
                # Fallback to comprehensive service
                logger.info("[CDA PROCESSOR] Falling back to comprehensive clinical data service")
                comprehensive_data = self.comprehensive_service.extract_comprehensive_clinical_data(
                    cda_content, 'Unknown'  # TODO: Extract country from session
                )
                return comprehensive_data
                
        except Exception as e:
            logger.error(f"[CDA PROCESSOR] CDA document parsing error: {e}")
            return None
    
    def _build_cda_context(
        self,
        context: Dict[str, Any],
        parsed_data: Dict[str, Any],
        match_data: Dict[str, Any]
    ) -> None:
        """
        Build template context from parsed CDA data
        
        Args:
            context: Base context to update
            parsed_data: Parsed CDA data
            match_data: Original session match data
        """
        # Add patient data from match data
        patient_info = match_data.get('patient_data', {})
        if patient_info:
            self.context_builder.add_patient_data(context, patient_info)
        
        # Add clinical data from CDA parsing
        if parsed_data:
            # CDA parsing returns different structure than FHIR
            sections = parsed_data.get('sections', [])
            clinical_data = parsed_data.get('clinical_data', {})
            
            if sections:
                context['sections'] = sections
                context['has_clinical_data'] = len(sections) > 0
                logger.info(f"[CDA PROCESSOR] Added {len(sections)} clinical sections")
            
            # Extract clinical arrays using the comprehensive service method
            if not clinical_data and sections:
                logger.info("[CDA PROCESSOR] Extracting clinical arrays from sections")
                clinical_arrays = self.comprehensive_service.get_clinical_arrays_for_display(parsed_data)
                if clinical_arrays:
                    context['clinical_arrays'] = clinical_arrays
                    context['has_clinical_data'] = bool(clinical_arrays)
                    logger.info(f"[CDA PROCESSOR] Added clinical arrays: {list(clinical_arrays.keys())}")
            elif clinical_data:
                context['clinical_arrays'] = clinical_data
                context['has_clinical_data'] = bool(clinical_data)
                logger.info(f"[CDA PROCESSOR] Added clinical arrays: {list(clinical_data.keys())}")
            
            # Add backward compatibility template variables
            self._add_template_compatibility_variables(context, sections)
            
            # CDA administrative data (if available)
            admin_data = parsed_data.get('administrative_data')
            if admin_data:
                # Convert administrative data object to dictionary if needed
                if hasattr(admin_data, '__dict__'):
                    admin_dict = admin_data.__dict__
                elif hasattr(admin_data, 'to_dict'):
                    admin_dict = admin_data.to_dict()
                else:
                    admin_dict = admin_data if isinstance(admin_data, dict) else {}
                
                if admin_dict:
                    self.context_builder.add_administrative_data(context, admin_dict)
    
    def _add_cda_metadata(
        self,
        context: Dict[str, Any],
        match_data: Dict[str, Any],
        cda_content: str,
        cda_type: str
    ) -> None:
        """
        Add CDA-specific metadata to context
        
        Args:
            context: Context to update
            match_data: Session match data
            cda_content: CDA XML content
            cda_type: Actual CDA type used
        """
        metadata = {
            'confidence_score': match_data.get('confidence_score', 0.9),
            'source_country': match_data.get('country_code', 'Unknown'),
            'source_language': match_data.get('source_language', 'Unknown'),
            'file_path': match_data.get('file_path', 'Unknown'),
            'translation_quality': 'Standard',  # CDA requires translation
        }
        
        self.context_builder.add_processing_metadata(context, metadata)
        
        # Add CDA-specific context
        context.update({
            'cda_processing': True,
            'cda_content': cda_content,
            'cda_type': cda_type,
            'preferred_cda_type': cda_type,
            'actual_cda_type': cda_type,
            'has_l1': match_data.get('has_l1', False),
            'has_l3': match_data.get('has_l3', False),
            # Template compatibility - add both variable formats
            'has_l1_cda': match_data.get('has_l1', False),
            'has_l3_cda': match_data.get('has_l3', False),
            'display_filename': self._get_display_filename(match_data),
        })
    
    def _get_display_filename(self, match_data: Dict[str, Any]) -> str:
        """Get appropriate display filename for CDA document"""
        file_path = match_data.get('file_path', '')
        if file_path and file_path != 'FHIR_BUNDLE':
            import os
            return os.path.basename(file_path)
        return 'CDA Document'
    
    def _add_template_compatibility_variables(self, context: Dict[str, Any], sections: List[Dict[str, Any]]) -> None:
        """
        Add backward compatibility variables for older template structure
        
        Args:
            context: Template context to update
            sections: Clinical sections data
        """
        # Initialize empty variables for template compatibility
        compatibility_vars = {
            'medications': [],
            'allergies': [],
            'problems': [],
            'vital_signs': [],
            'procedures': [],
            'immunizations': [],
            'coded_results': {'blood_group': [], 'diagnostic_results': []},
            'laboratory_results': [],
            'history_of_past_illness': [],
            'pregnancy_history': [],
            'social_history': [],
            'physical_findings': [],
            'advance_directives': [],
            'additional_sections': []
        }
        
        # Map sections to compatibility variables based on section codes
        if sections:
            for section in sections:
                section_code = section.get('section_code', '')
                section_id = section.get('section_id', '')
                
                # Map specific section codes to template variables
                if section_code in ['10160-0', '10164-2']:  # Medication sections
                    compatibility_vars['medications'].append(section)
                elif section_code in ['48765-2', '48766-0']:  # Allergy sections
                    compatibility_vars['allergies'].append(section)
                elif section_code in ['11450-4', '11348-0']:  # Problem lists
                    compatibility_vars['problems'].append(section)
                elif section_code in ['8716-3']:  # Vital signs / Physical findings
                    compatibility_vars['vital_signs'].append(section)
                    compatibility_vars['physical_findings'].append(section)
                elif section_code in ['47519-4']:  # Procedures
                    compatibility_vars['procedures'].append(section)
                elif section_code in ['11369-6']:  # Immunization
                    compatibility_vars['immunizations'].append(section)
                elif section_code in ['30954-2', '18748-4', '34530-6']:  # Results sections
                    compatibility_vars['coded_results']['diagnostic_results'].append(section)
                    compatibility_vars['laboratory_results'].append(section)
                elif section_code in ['10157-6']:  # History of past illness
                    compatibility_vars['history_of_past_illness'].append(section)
                elif section_code in ['10162-6']:  # Pregnancy history
                    compatibility_vars['pregnancy_history'].append(section)
                elif section_code in ['29762-2']:  # Social history
                    compatibility_vars['social_history'].append(section)
                elif section_code in ['42348-3']:  # Advance directives
                    compatibility_vars['advance_directives'].append(section)
                else:
                    # Additional sections not mapped to specific variables
                    compatibility_vars['additional_sections'].append(section)
        
        # Add all compatibility variables to context
        context.update(compatibility_vars)
        
        logger.info(f"[CDA PROCESSOR] Added template compatibility variables: {list(compatibility_vars.keys())}")
    
    def _handle_cda_error(
        self,
        request,
        error_message: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> HttpResponse:
        """
        Handle CDA processing errors with appropriate response
        
        Args:
            request: Django HTTP request
            error_message: Error description
            session_id: Session identifier
            context: Partial context if available
            
        Returns:
            Error response
        """
        logger.error(f"[CDA PROCESSOR] Error for session {session_id}: {error_message}")
        
        if context is None:
            context = self.context_builder.build_base_context(session_id, 'CDA')
        
        self.context_builder.add_error(context, error_message)
        
        # Add error-specific context
        context.update({
            'processing_failed': True,
            'error_type': 'CDA Processing Error',
            'error_details': error_message,
            'suggested_action': 'Please verify the CDA document is valid or try a different document type.',
        })
        
        return render(request, 'patient_data/enhanced_patient_cda.html', context)