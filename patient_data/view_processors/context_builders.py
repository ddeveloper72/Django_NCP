"""
Context Builders - Shared utilities for building template context

Provides common functionality for building consistent context structures
across both FHIR and CDA processors.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import asdict, is_dataclass
from django.utils import timezone

from ..services.patient_demographics_service import PatientDemographicsService

logger = logging.getLogger(__name__)


class ContextBuilder:
    """
    Shared context building utilities for both FHIR and CDA processors
    
    Ensures consistent context structure across different data sources
    """
    
    def __init__(self):
        """Initialize context builder with unified patient demographics service"""
        self.demographics_service = PatientDemographicsService()
    
    @staticmethod
    def detect_data_source(request, session_id: str) -> str:
        """
        Detect whether the session contains FHIR or CDA data
        
        Args:
            request: Django request object
            session_id: Session identifier
            
        Returns:
            'FHIR' or 'CDA' based on data source detection
        """
        try:
            # Get session data
            match_data = request.session.get(f"patient_match_{session_id}", {})
            
            # Check for explicit data_source flag (Portuguese FHIR integration)
            explicit_data_source = match_data.get("data_source")
            if explicit_data_source:
                logger.info(f"[DETECT] Explicit data_source found: {explicit_data_source}")
                return explicit_data_source.upper()
            
            # Check for FHIR bundle presence (Portuguese FHIR integration)
            if "fhir_bundle" in match_data:
                logger.info(f"[DETECT] FHIR bundle detected in session {session_id}")
                return "FHIR"
            
            # Check for CDA content (traditional CDA integration)
            # Look for CDA-specific markers in session data
            if any(key in match_data for key in ["has_l1", "has_l3", "cda_content"]):
                logger.info(f"[DETECT] CDA content detected in session {session_id}")
                return "CDA"
            
            # Check for country code patterns that indicate FHIR (Portugal)
            country_code = match_data.get("country_code", "").upper()
            if country_code == "PT":
                logger.info(f"[DETECT] Portuguese country code detected, assuming FHIR for session {session_id}")
                return "FHIR"
            
            # Default fallback - if we have any patient data, assume CDA
            patient_info = match_data.get("patient_info", {})
            if patient_info:
                logger.info(f"[DETECT] Patient data found, defaulting to CDA for session {session_id}")
                return "CDA"
            
            # Ultimate fallback
            logger.warning(f"[DETECT] Could not determine data source for session {session_id}, defaulting to CDA")
            return "CDA"
            
        except Exception as e:
            logger.error(f"[DETECT] Error detecting data source for session {session_id}: {e}")
            return "CDA"
    
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
    
    def add_patient_data(self, context: Dict[str, Any], patient_data: Dict[str, Any]) -> None:
        """
        Add patient demographic data to context using unified service
        
        Args:
            context: Context dictionary to update
            patient_data: Patient demographic information from session
        """
        # Convert session data to unified demographics model
        demographics = self.demographics_service.extract_from_session_data(patient_data)
        
        # Create unified template context with backward compatibility
        patient_context = self.demographics_service.create_unified_template_context(demographics)
        
        # Add to main context
        context.update(patient_context)
        
        logger.info(f"Added unified patient data for: {demographics.get_display_name()}")
    
    def add_patient_data_from_cda(self, context: Dict[str, Any], xml_root) -> None:
        """
        Add patient demographic data from CDA XML using unified service
        
        Args:
            context: Context dictionary to update
            xml_root: CDA XML root element
        """
        # Extract demographics from CDA XML
        demographics = self.demographics_service.extract_from_cda_xml(xml_root)
        
        # Create unified template context with backward compatibility
        patient_context = self.demographics_service.create_unified_template_context(demographics)
        
        # Add to main context
        context.update(patient_context)
        
        logger.info(f"Added CDA patient data for: {demographics.get_display_name()}")
    
    def add_patient_data_from_fhir(self, context: Dict[str, Any], fhir_bundle: Dict[str, Any]) -> None:
        """
        Add patient demographic data from FHIR bundle using unified service
        
        Args:
            context: Context dictionary to update
            fhir_bundle: FHIR bundle containing patient resource
        """
        # Extract demographics from FHIR bundle
        demographics = self.demographics_service.extract_from_fhir_bundle(fhir_bundle)
        
        # Create unified template context with backward compatibility
        patient_context = self.demographics_service.create_unified_template_context(demographics)
        
        # Add to main context
        context.update(patient_context)
        
        logger.info(f"Added FHIR patient data for: {demographics.get_display_name()}")
    
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
        
        # CRITICAL FIX: Add individual administrative data attributes as separate template variables
        # This allows templates to access author_hcp, custodian_organization, guardians, etc. directly
        # Handle both dictionary and dataclass object access
        if isinstance(admin_data, dict):
            # Extract individual attributes from the administrative data dictionary
            context['author_hcp'] = admin_data.get('author_hcp')
            context['custodian_organization'] = admin_data.get('custodian_organization')
            context['guardians'] = admin_data.get('guardians', [])
            context['participants'] = admin_data.get('participants', [])
            context['legal_authenticator'] = admin_data.get('legal_authenticator')
            context['document_creation_date'] = admin_data.get('document_creation_date')
            context['document_title'] = admin_data.get('document_title')
        elif is_dataclass(admin_data):
            # ARCHITECTURE ALIGNMENT: Convert dataclass to dict following clinical sections pattern
            # Clinical sections return dict structures, so administrative data should match
            
            # Extract and convert nested dataclass objects to dicts for template compatibility
            author_hcp = getattr(admin_data, 'author_hcp', None)
            if author_hcp and is_dataclass(author_hcp):
                # Convert AuthorInfo dataclass to dict with nested Person, Organization, ContactInfo
                context['author_hcp'] = asdict(author_hcp)
            else:
                context['author_hcp'] = author_hcp
            
            custodian_org = getattr(admin_data, 'custodian_organization', None)
            if custodian_org and is_dataclass(custodian_org):
                # Convert Organization dataclass to dict
                context['custodian_organization'] = asdict(custodian_org)
            else:
                context['custodian_organization'] = custodian_org
            
            legal_auth = getattr(admin_data, 'legal_authenticator', None)
            if legal_auth and is_dataclass(legal_auth):
                context['legal_authenticator'] = asdict(legal_auth)
            else:
                context['legal_authenticator'] = legal_auth
            
            # Convert lists that may contain dataclass objects
            guardians_list = getattr(admin_data, 'guardians', []) or []
            guardians_converted = [
                asdict(g) if is_dataclass(g) else g for g in guardians_list
            ]
            
            participants_list = getattr(admin_data, 'participants', []) or []
            participants_converted = [
                asdict(p) if is_dataclass(p) else p for p in participants_list
            ]
            
            # Merge guardians and participants for unified display in Emergency Contacts section
            context['participants'] = guardians_converted + participants_converted
            context['guardians'] = guardians_converted  # Keep separate for backward compatibility
            
            # Documentation of service events (if present)
            doc_of = getattr(admin_data, 'documentation_of', None)
            if doc_of and is_dataclass(doc_of):
                context['documentation_of'] = asdict(doc_of)
            else:
                context['documentation_of'] = doc_of
            
            context['document_creation_date'] = getattr(admin_data, 'document_creation_date', '')
            context['document_title'] = getattr(admin_data, 'document_title', '')
        
        # Log successful extraction of individual attributes
        author_info = context.get('author_hcp')
        if author_info:
            author_name = getattr(author_info, 'person', {})
            if hasattr(author_name, 'full_name'):
                logger.info(f"[TEMPLATE CONTEXT] Added author_hcp: {author_name.full_name}")
            else:
                logger.info(f"[TEMPLATE CONTEXT] Added author_hcp: {type(author_info)}")
        
        custodian_org = context.get('custodian_organization')
        if custodian_org:
            if hasattr(custodian_org, 'name'):
                logger.info(f"[TEMPLATE CONTEXT] Added custodian_organization: {custodian_org.name}")
            else:
                logger.info(f"[TEMPLATE CONTEXT] Added custodian_organization: {type(custodian_org)}")
        
        guardians = context.get('guardians', [])
        participants = context.get('participants', [])
        logger.info(f"[TEMPLATE CONTEXT] Added {len(guardians)} guardians and {len(participants)} participants")
        
        # Validate custodian organization (critical for organization display)
        # Handle both dictionary and object attribute access
        custodian_org = None
        if isinstance(admin_data, dict):
            custodian_org = admin_data.get('custodian_organization')
        elif hasattr(admin_data, 'custodian_organization'):
            custodian_org = getattr(admin_data, 'custodian_organization')
        
        if custodian_org:
            # Extract organization name - handle both dict and object
            if isinstance(custodian_org, dict):
                org_name = custodian_org.get('name', 'Unknown Organization')
                addresses = custodian_org.get('addresses', [])
            elif hasattr(custodian_org, 'name'):
                org_name = getattr(custodian_org, 'name', 'Unknown Organization')
                addresses = getattr(custodian_org, 'addresses', []) if hasattr(custodian_org, 'addresses') else []
            else:
                org_name = str(custodian_org) 
                addresses = []
            
            location = 'Unknown Location'
            if addresses:
                addr = addresses[0]
                if isinstance(addr, dict):
                    city = addr.get('city', '')
                    country = addr.get('country', '')
                elif hasattr(addr, 'city') and hasattr(addr, 'country'):
                    city = getattr(addr, 'city', '')
                    country = getattr(addr, 'country', '')
                else:
                    city = country = ''
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
                'medical_devices': clinical_arrays.get('medical_devices', []),
                'past_illness': clinical_arrays.get('past_illness', []),
                'pregnancy_history': clinical_arrays.get('pregnancy_history', []),
                'social_history': clinical_arrays.get('social_history', []),
                'advance_directives': clinical_arrays.get('advance_directives', []),
                'functional_status': clinical_arrays.get('functional_status', []),
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
    
    def finalize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Finalize context with computed values and validation
        
        CRITICAL FIX: Extract individual fields from administrative_data dict/dataclass
        so templates can access author_hcp, custodian_organization, guardians, etc. directly
        
        Args:
            context: Context dictionary to finalize
            
        Returns:
            Finalized context dictionary
        """
        # CRITICAL: Extract individual administrative fields for template access
        # If administrative_data exists in context, extract its individual fields
        if 'administrative_data' in context and context['administrative_data']:
            admin_data = context['administrative_data']
            logger.info(f"[FINALIZE] Extracting individual fields from administrative_data (type: {type(admin_data).__name__})")
            self.add_administrative_data(context, admin_data)
        
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