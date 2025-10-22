"""
Clinical Data Pipeline Manager

Unified coordination system for specialized clinical section service agents.
Implements enterprise-grade architecture with:
- Specialized service agents for each clinical domain
- Consistent session management patterns
- Standardized template data structures
- Unified error handling and logging

Author: Django_NCP Development Team
Date: October 2025
Version: 1.0.0
"""

import logging
from typing import Dict, List, Any, Optional, Type, Union
from django.http import HttpRequest
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ClinicalSectionServiceInterface(ABC):
    """
    Abstract base class defining the contract for all clinical section services.
    
    This interface ensures:
    - Consistent method signatures across all clinical sections
    - Standardized session data patterns
    - Uniform template data structures
    - Common error handling approaches
    """
    
    @abstractmethod
    def get_section_code(self) -> str:
        """Return the standard section code (e.g., '10160-0' for medications)"""
        pass
    
    @abstractmethod
    def get_section_name(self) -> str:
        """Return the human-readable section name"""
        pass
    
    @abstractmethod
    def extract_from_session(self, request: HttpRequest, session_id: str) -> List[Dict[str, Any]]:
        """
        Extract clinical data from session storage.
        
        Args:
            request: Django HTTP request
            session_id: Session identifier
            
        Returns:
            List of standardized clinical data items with direct field access
        """
        pass
    
    @abstractmethod
    def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
        """
        Extract clinical data from CDA XML content.
        
        Args:
            cda_content: CDA XML content string
            
        Returns:
            List of standardized clinical data items
        """
        pass
    
    @abstractmethod
    def enhance_and_store(self, request: HttpRequest, session_id: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enhance raw clinical data and store in session.
        
        Args:
            request: Django HTTP request
            session_id: Session identifier
            raw_data: Raw clinical data from CDA extraction
            
        Returns:
            Enhanced clinical data with standardized fields
        """
        pass
    
    @abstractmethod
    def get_template_data(self, enhanced_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convert enhanced clinical data to template-ready format.
        
        Args:
            enhanced_data: Enhanced clinical data items
            
        Returns:
            Template context dictionary with direct field access patterns
        """
        pass


class ClinicalDataPipelineManager:
    """
    Unified manager for coordinating specialized clinical section service agents.
    
    Implements enterprise-grade patterns:
    - Service registry for dynamic agent management
    - Consistent session patterns across all clinical sections
    - Standardized template data structures
    - Centralized error handling and logging
    - Performance monitoring and caching
    """
    
    def __init__(self):
        """Initialize the pipeline manager with service registry."""
        self._service_registry: Dict[str, ClinicalSectionServiceInterface] = {}
        self._session_key_pattern = "enhanced_{section_name}"
        self._unified_session_key = "enhanced_clinical_data"
        logger.info("[PIPELINE MANAGER] Initialized clinical data pipeline manager")
    
    @property
    def services(self) -> Dict[str, ClinicalSectionServiceInterface]:
        """Access to registered services."""
        return self._service_registry
    
    def register_service(self, service: ClinicalSectionServiceInterface) -> None:
        """
        Register a specialized clinical section service.
        
        Args:
            service: Clinical section service implementing the interface
        """
        section_code = service.get_section_code()
        section_name = service.get_section_name().lower().replace(' ', '_')
        
        self._service_registry[section_code] = service
        self._service_registry[section_name] = service
        
        logger.info(f"[PIPELINE MANAGER] Registered service: {service.get_section_name()} ({section_code})")
    
    def get_service(self, section_identifier: str) -> Optional[ClinicalSectionServiceInterface]:
        """
        Get a registered clinical section service.
        
        Args:
            section_identifier: Section code or name
            
        Returns:
            Clinical section service or None if not found
        """
        return self._service_registry.get(section_identifier)
    
    def get_all_services(self) -> Dict[str, ClinicalSectionServiceInterface]:
        """Get all registered clinical section services."""
        return {key: service for key, service in self._service_registry.items() 
                if not key.startswith('10') and not key.startswith('48')}  # Filter out duplicate code entries
    
    def process_session_data(self, request: HttpRequest, session_id: str) -> Dict[str, Any]:
        """
        Process clinical data from session storage using all registered services.
        
        Args:
            request: Django HTTP request
            session_id: Session identifier
            
        Returns:
            Unified clinical data dictionary with all sections
        """
        logger.info(f"[PIPELINE MANAGER] Processing session data for session {session_id}")
        
        unified_data = {
            'clinical_sections': {},
            'template_data': {},
            'session_metadata': {
                'session_id': session_id,
                'processing_timestamp': self._get_current_timestamp(),
                'services_used': []
            }
        }
        
        # Process each registered service
        for service_name, service in self.get_all_services().items():
            try:
                logger.info(f"[PIPELINE MANAGER] Processing {service.get_section_name()} section")
                
                # Extract data from session
                section_data = service.extract_from_session(request, session_id)
                
                if section_data:
                    # Convert to template-ready format
                    template_data = service.get_template_data(section_data)
                    
                    # Store in unified structure
                    section_key = service.get_section_name().lower().replace(' ', '_')
                    unified_data['clinical_sections'][section_key] = section_data
                    unified_data['template_data'][section_key] = template_data
                    unified_data['session_metadata']['services_used'].append(service.get_section_name())
                    
                    logger.info(f"[PIPELINE MANAGER] Successfully processed {len(section_data)} {service.get_section_name()} items")
                else:
                    logger.info(f"[PIPELINE MANAGER] No {service.get_section_name()} data found in session")
                    
            except Exception as e:
                logger.error(f"[PIPELINE MANAGER] Error processing {service.get_section_name()}: {e}")
                # Continue processing other services even if one fails
                continue
        
        # Store unified data in session
        self._store_unified_data(request, session_id, unified_data)
        
        return unified_data
    
    def process_cda_content(self, request: HttpRequest, session_id: str, cda_content: str) -> Dict[str, Any]:
        """
        Process CDA content using all registered services and store enhanced data.
        
        Args:
            request: Django HTTP request
            session_id: Session identifier
            cda_content: CDA XML content
            
        Returns:
            Unified clinical data dictionary with enhanced information
        """
        logger.info(f"[PIPELINE MANAGER] Processing CDA content for session {session_id}")
        
        unified_data = {
            'clinical_sections': {},
            'template_data': {},
            'session_metadata': {
                'session_id': session_id,
                'processing_timestamp': self._get_current_timestamp(),
                'services_used': [],
                'source': 'cda_extraction'
            }
        }
        
        # Process each registered service
        for service_name, service in self.get_all_services().items():
            try:
                logger.info(f"[PIPELINE MANAGER] Extracting {service.get_section_name()} from CDA")
                
                # Extract data from CDA
                raw_data = service.extract_from_cda(cda_content)
                
                if raw_data:
                    # Enhance and store in session
                    enhanced_data = service.enhance_and_store(request, session_id, raw_data)
                    
                    # Convert to template-ready format
                    template_data = service.get_template_data(enhanced_data)
                    
                    # Store in unified structure
                    section_key = service.get_section_name().lower().replace(' ', '_')
                    unified_data['clinical_sections'][section_key] = enhanced_data
                    unified_data['template_data'][section_key] = template_data
                    unified_data['session_metadata']['services_used'].append(service.get_section_name())
                    
                    logger.info(f"[PIPELINE MANAGER] Successfully processed and stored {len(enhanced_data)} {service.get_section_name()} items")
                else:
                    logger.info(f"[PIPELINE MANAGER] No {service.get_section_name()} data found in CDA")
                    
            except Exception as e:
                logger.error(f"[PIPELINE MANAGER] Error processing {service.get_section_name()} from CDA: {e}")
                # Continue processing other services even if one fails
                continue
        
        # Store unified data in session
        self._store_unified_data(request, session_id, unified_data)
        
        return unified_data
    
    def get_template_context(self, request: HttpRequest, session_id: str) -> Dict[str, Any]:
        """
        Get complete template context for all clinical sections.
        
        Args:
            request: Django HTTP request
            session_id: Session identifier
            
        Returns:
            Complete template context with all clinical sections
        """
        # First try to get from unified session storage
        unified_data = self._get_unified_data(request, session_id)
        
        if not unified_data:
            # Fall back to processing session data
            unified_data = self.process_session_data(request, session_id)
        
        # Build template context
        context = {
            'clinical_data_available': bool(unified_data['clinical_sections']),
            'sections_processed': list(unified_data['clinical_sections'].keys()),
            'processing_metadata': unified_data['session_metadata']
        }
        
        # Add each section's template data
        for section_key, template_data in unified_data['template_data'].items():
            context[section_key] = template_data.get('items', [])
            context[f"{section_key}_metadata"] = template_data.get('metadata', {})
            context[f"has_{section_key}"] = len(template_data.get('items', [])) > 0
        
        logger.info(f"[PIPELINE MANAGER] Built template context with {len(unified_data['clinical_sections'])} sections")
        
        return context
    
    def _store_unified_data(self, request: HttpRequest, session_id: str, unified_data: Dict[str, Any]) -> None:
        """Store unified clinical data in session."""
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        match_data[self._unified_session_key] = unified_data
        request.session[session_key] = match_data
        request.session.modified = True
        
        logger.info(f"[PIPELINE MANAGER] Stored unified clinical data for session {session_id}")
    
    def _get_unified_data(self, request: HttpRequest, session_id: str) -> Optional[Dict[str, Any]]:
        """Get unified clinical data from session."""
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        return match_data.get(self._unified_session_key)
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp for metadata."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def process_section(self, section_code: str, request: HttpRequest, session_id: str, cda_content: str = None) -> Dict[str, Any]:
        """
        Process a specific clinical section using its specialized service agent.
        
        Args:
            section_code: Clinical section code (e.g., '10160-0' for medications)
            request: Django request object with session
            session_id: Patient session identifier  
            cda_content: Optional CDA XML content for extraction
            
        Returns:
            Template-ready clinical data with metadata
        """
        service = self.get_service(section_code)
        if not service:
            logger.warning(f"[PIPELINE MANAGER] No service found for section {section_code}")
            return {'items': [], 'metadata': {'section_name': 'Unknown', 'section_code': section_code, 'item_count': 0, 'has_items': False}}
        
        try:
            # Extract from session first
            session_data = service.extract_from_session(request, session_id)
            
            # If no session data and CDA content provided, extract from CDA
            if not session_data and cda_content:
                cda_data = service.extract_from_cda(cda_content)
                if cda_data:
                    session_data = cda_data
            
            # Enhance and store data
            if session_data:
                enhanced_data = service.enhance_and_store(request, session_id, session_data)
                return service.get_template_data(enhanced_data)
            else:
                # Return empty result with proper metadata
                return service.get_template_data([])
                
        except Exception as e:
            logger.error(f"[PIPELINE MANAGER] Error processing section {section_code}: {e}")
            return {'items': [], 'metadata': {'section_name': service.get_section_name(), 'section_code': section_code, 'item_count': 0, 'has_items': False, 'error': str(e)}}
    
    def process_all_sections(self, request: HttpRequest, session_id: str, cda_content: str = None) -> Dict[str, Dict[str, Any]]:
        """
        Process all registered clinical sections using their specialized service agents.
        
        Args:
            request: Django request object with session
            session_id: Patient session identifier
            cda_content: Optional CDA XML content for extraction
            
        Returns:
            Dictionary mapping section codes to template-ready clinical data
        """
        results = {}
        
        # Get unique services (avoid duplicates from registration issues)
        unique_services = {}
        for code, service in self._service_registry.items():
            service_key = f"{service.get_section_code()}_{service.get_section_name()}"
            if service_key not in unique_services:
                unique_services[service.get_section_code()] = service
        
        logger.info(f"[PIPELINE MANAGER] Processing {len(unique_services)} unique clinical sections")
        
        for section_code, service in unique_services.items():
            section_result = self.process_section(section_code, request, session_id, cda_content)
            results[section_code] = section_result
            
            item_count = section_result.get('metadata', {}).get('item_count', 0)
            section_name = section_result.get('metadata', {}).get('section_name', 'Unknown')
            logger.info(f"[PIPELINE MANAGER] Processed {section_name}: {item_count} items")
        
        return results


class MedicationSectionService(ClinicalSectionServiceInterface):
    """
    Specialized service for medication section data processing.
    
    Implements the working pattern from the existing CDAViewProcessor
    with enhanced session storage and template compatibility.
    """
    
    def get_section_code(self) -> str:
        return "10160-0"
    
    def get_section_name(self) -> str:
        return "Medications"
    
    def extract_from_session(self, request: HttpRequest, session_id: str) -> List[Dict[str, Any]]:
        """Extract medications from session using the proven working pattern."""
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        
        # Use the working enhanced medications pattern
        enhanced_medications = match_data.get('enhanced_medications', [])
        
        if enhanced_medications:
            logger.info(f"[MEDICATION SERVICE] Found {len(enhanced_medications)} enhanced medications in session")
            return enhanced_medications
        
        logger.info("[MEDICATION SERVICE] No enhanced medications found in session")
        return []
    
    def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
        """Extract medications from CDA content using specialized CDA parsing."""
        # Import the working CDA medication parsing logic
        from ..view_processors.cda_processor import CDAViewProcessor
        
        processor = CDAViewProcessor()
        
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(cda_content)
            
            # Find medication section
            namespaces = {'hl7': 'urn:hl7-org:v3'}
            sections = root.findall('.//hl7:section', namespaces)
            
            for section in sections:
                code_elem = section.find('hl7:code', namespaces)
                if code_elem is not None and code_elem.get('code') == '10160-0':
                    # Use the working _parse_medication_xml method
                    parsed_result = processor._parse_medication_xml(section)
                    
                    if parsed_result and 'clinical_table' in parsed_result:
                        medications = []
                        for row in parsed_result['clinical_table']['rows']:
                            if 'data' in row:
                                medications.append(row['data'])
                        
                        logger.info(f"[MEDICATION SERVICE] Extracted {len(medications)} medications from CDA")
                        return medications
            
            logger.info("[MEDICATION SERVICE] No medication section found in CDA")
            return []
            
        except Exception as e:
            logger.error(f"[MEDICATION SERVICE] Error extracting medications from CDA: {e}")
            return []
    
    def enhance_and_store(self, request: HttpRequest, session_id: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance medication data and store in session using proven pattern."""
        enhanced_medications = []
        
        for med_data in raw_data:
            # Apply the working enhancement pattern
            enhanced_med = {
                'name': self._extract_field_value(med_data, 'medication_name', 'Unknown Medication'),
                'display_name': self._extract_field_value(med_data, 'medication_name', 'Unknown Medication'),
                'active_ingredient': self._extract_field_value(med_data, 'active_ingredients', 'Not specified'),
                'pharmaceutical_form': self._extract_field_value(med_data, 'pharmaceutical_form', 'Tablet'),
                'strength': self._extract_field_value(med_data, 'strength', 'Not specified'),
                'dose_quantity': self._extract_field_value(med_data, 'dose_quantity', 'Dose not specified'),
                'route': self._extract_field_value(med_data, 'route', 'Administration route not specified'),
                'schedule': self._extract_field_value(med_data, 'schedule', 'Schedule not specified'),
                'period': self._extract_field_value(med_data, 'period', 'Treatment timing not specified'),
                'indication': self._extract_field_value(med_data, 'indication', 'Medical indication not specified'),
                'source': 'cda_extraction_enhanced'
            }
            enhanced_medications.append(enhanced_med)
        
        # Store in session using proven pattern
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        match_data['enhanced_medications'] = enhanced_medications
        request.session[session_key] = match_data
        request.session.modified = True
        
        logger.info(f"[MEDICATION SERVICE] Enhanced and stored {len(enhanced_medications)} medications")
        return enhanced_medications
    
    def get_template_data(self, enhanced_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert enhanced medications to template-ready format."""
        return {
            'items': enhanced_data,
            'metadata': {
                'section_name': 'Medications',
                'section_code': '10160-0',
                'item_count': len(enhanced_data),
                'has_items': len(enhanced_data) > 0,
                'template_pattern': 'direct_field_access'  # med.field_name
            }
        }
    
    def _extract_field_value(self, data: Dict[str, Any], field_name: str, default: str) -> str:
        """Extract field value handling both flat and nested structures."""
        value = data.get(field_name, default)
        
        if isinstance(value, dict):
            # Handle nested structures like {'value': 'X', 'display_value': 'Y'}
            return value.get('display_value', value.get('value', default))
        
        return str(value) if value else default


# Global pipeline manager instance
clinical_pipeline_manager = ClinicalDataPipelineManager()


# Initialize all clinical section services
def initialize_all_services():
    """Initialize and register all clinical section services with the pipeline manager."""
    # Register the medication service (already implemented)
    clinical_pipeline_manager.register_service(MedicationSectionService())
    
    # Import and register additional services
    try:
        from .allergies_section_service import AllergiesSectionService
        clinical_pipeline_manager.register_service(AllergiesSectionService())
    except ImportError:
        logger.warning("[CLINICAL PIPELINE] AllergiesSectionService not available")
    
    try:
        from .complete_clinical_services import (
            ProblemsSectionService,
            VitalSignsSectionService, 
            ProceduresSectionService,
            ImmunizationsSectionService,
            ResultsSectionService,
            MedicalDevicesSectionService
        )
        
        services = [
            ProblemsSectionService(),
            VitalSignsSectionService(),
            ProceduresSectionService(),
            ImmunizationsSectionService(),
            ResultsSectionService(),
            MedicalDevicesSectionService()
        ]
        
        for service in services:
            clinical_pipeline_manager.register_service(service)
            
    except ImportError as e:
        logger.warning(f"[CLINICAL PIPELINE] Some clinical services not available: {e}")
    
    try:
        from .pregnancy_history_service import PregnancyHistorySectionService
        clinical_pipeline_manager.register_service(PregnancyHistorySectionService())
    except ImportError:
        logger.warning("[CLINICAL PIPELINE] PregnancyHistorySectionService not available")
    
    registered_count = len(clinical_pipeline_manager._service_registry)
    logger.info(f"[CLINICAL PIPELINE] Initialized {registered_count} specialized clinical section services")
    return registered_count


# Initialize all services on module load
initialize_all_services()