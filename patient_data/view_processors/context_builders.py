"""
Context Builders - Shared utilities for building template context

Provides common functionality for building consistent context structures
across both FHIR and CDA processors.
"""

import logging
from typing import Dict, Any, Optional
from django.utils import timezone

logger = logging.getLogger(__name__)


class ContextBuilder:
    """
    Shared context building utilities for both FHIR and CDA processors
    
    Ensures consistent context structure across different data sources
    """
    
    @staticmethod
    def build_base_context(session_id: str, data_source: str) -> Dict[str, Any]:
        """
        Build base context structure common to all data sources
        
        Args:
            session_id: Session identifier
            data_source: Data source type ('FHIR' or 'CDA')
            
        Returns:
            Base context dictionary
        """
        return {
            'session_id': session_id,
            'data_source': data_source,
            'processing_timestamp': timezone.now().isoformat(),
            'template_version': '2025.10',
            
            # Initialize common template variables to prevent template errors
            'patient_data': {},
            'administrative_data': {},
            'healthcare_data': {},
            'contact_data': {},
            'clinical_arrays': {},
            'sections': [],
            
            # Processing flags
            'has_administrative_data': False,
            'has_clinical_data': False,
            'has_healthcare_data': False,
            'has_extended_data': False,
            
            # Error handling
            'processing_errors': [],
            'processing_warnings': [],
        }
    
    @staticmethod
    def add_patient_data(context: Dict[str, Any], patient_data: Dict[str, Any]) -> None:
        """
        Add patient demographic data to context
        
        Args:
            context: Context dictionary to update
            patient_data: Patient demographic information
        """
        context['patient_data'] = patient_data
        context['patient_information'] = patient_data  # Alias for compatibility
        context['patient_identity'] = patient_data     # Additional alias
        
        # Set display name for UI
        given_name = patient_data.get('given_name', '')
        family_name = patient_data.get('family_name', '')
        context['patient_display_name'] = f"{given_name} {family_name}".strip()
        
        logger.info(f"Added patient data for: {context['patient_display_name']}")
    
    @staticmethod
    def add_administrative_data(context: Dict[str, Any], admin_data: Dict[str, Any]) -> None:
        """
        Add administrative data to context with validation
        
        Args:
            context: Context dictionary to update
            admin_data: Administrative data including custodian organization
        """
        context['administrative_data'] = admin_data
        context['has_administrative_data'] = bool(admin_data)
        
        # Validate custodian organization (critical for organization display)
        custodian_org = admin_data.get('custodian_organization')
        if custodian_org:
            org_name = custodian_org.get('name', 'Unknown Organization')
            addresses = custodian_org.get('addresses', [])
            location = 'Unknown Location'
            if addresses:
                addr = addresses[0]
                city = addr.get('city', '')
                country = addr.get('country', '')
                location = f"{city}, {country}" if city and country else 'Unknown Location'
            
            logger.info(f"Added custodian organization: {org_name} from {location}")
        else:
            logger.warning("No custodian organization found in administrative data")
    
    @staticmethod
    def add_clinical_data(context: Dict[str, Any], clinical_arrays: Dict[str, Any], sections: list = None) -> None:
        """
        Add clinical data to context
        
        Args:
            context: Context dictionary to update
            clinical_arrays: Clinical data arrays (medications, allergies, etc.)
            sections: Clinical sections list
        """
        context['clinical_arrays'] = clinical_arrays
        context['sections'] = sections or []
        
        # Add individual clinical arrays for template compatibility
        if clinical_arrays:
            context.update({
                'medications': clinical_arrays.get('medications', []),
                'allergies': clinical_arrays.get('allergies', []),
                'problems': clinical_arrays.get('problems', []),
                'conditions': clinical_arrays.get('conditions', []),
                'procedures': clinical_arrays.get('procedures', []),
                'vital_signs': clinical_arrays.get('vital_signs', []),
                'results': clinical_arrays.get('results', []),
                'immunizations': clinical_arrays.get('immunizations', []),
                'observations': clinical_arrays.get('observations', []),
            })
            
            # Calculate if we have any clinical data
            total_clinical_items = sum(
                len(v) if isinstance(v, list) else 0 
                for v in clinical_arrays.values()
            )
            context['has_clinical_data'] = total_clinical_items > 0
            
            logger.info(f"Added clinical data: {total_clinical_items} total items across {len(clinical_arrays)} categories")
        else:
            context['has_clinical_data'] = False
    
    @staticmethod
    def add_healthcare_data(context: Dict[str, Any], healthcare_data: Dict[str, Any]) -> None:
        """
        Add healthcare provider data to context
        
        Args:
            context: Context dictionary to update
            healthcare_data: Healthcare providers and organizations
        """
        context['healthcare_data'] = healthcare_data
        
        practitioners = healthcare_data.get('practitioners', [])
        organizations = healthcare_data.get('organizations', [])
        
        context['has_healthcare_data'] = len(practitioners) > 0 or len(organizations) > 0
        
        logger.info(f"Added healthcare data: {len(practitioners)} practitioners, {len(organizations)} organizations")
    
    @staticmethod
    def add_processing_metadata(context: Dict[str, Any], metadata: Dict[str, Any]) -> None:
        """
        Add processing metadata to context
        
        Args:
            context: Context dictionary to update
            metadata: Processing metadata (confidence, source, etc.)
        """
        context.update({
            'confidence_score': metadata.get('confidence_score', 0.95),
            'source_country': metadata.get('source_country', 'Unknown'),
            'source_language': metadata.get('source_language', 'en'),
            'file_path': metadata.get('file_path', 'Unknown'),
            'translation_quality': metadata.get('translation_quality', 'Unknown'),
        })
    
    @staticmethod
    def add_error(context: Dict[str, Any], error_message: str, error_type: str = 'error') -> None:
        """
        Add error or warning to context
        
        Args:
            context: Context dictionary to update
            error_message: Error message
            error_type: Type of error ('error' or 'warning')
        """
        if error_type == 'warning':
            context['processing_warnings'].append(error_message)
            logger.warning(f"Processing warning: {error_message}")
        else:
            context['processing_errors'].append(error_message)
            logger.error(f"Processing error: {error_message}")
    
    @staticmethod
    def finalize_context(context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Finalize context with computed values and validation
        
        Args:
            context: Context dictionary to finalize
            
        Returns:
            Finalized context dictionary
        """
        # Set overall extended data flag
        context['has_extended_data'] = any([
            context.get('has_administrative_data', False),
            context.get('has_healthcare_data', False),
            len(context.get('contact_data', {})) > 0
        ])
        
        # Add summary information for debugging
        context['processing_summary'] = {
            'patient_loaded': bool(context.get('patient_data')),
            'admin_loaded': context.get('has_administrative_data', False),
            'clinical_loaded': context.get('has_clinical_data', False),
            'healthcare_loaded': context.get('has_healthcare_data', False),
            'errors_count': len(context.get('processing_errors', [])),
            'warnings_count': len(context.get('processing_warnings', [])),
        }
        
        logger.info(f"Context finalized: {context['processing_summary']}")
        
        return context