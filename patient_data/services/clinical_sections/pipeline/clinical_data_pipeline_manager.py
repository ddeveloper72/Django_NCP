"""
Clinical Data Pipeline Manager

Coordination system for specialized clinical section service agents.

Author: Django_NCP Development Team
Date: October 2025
"""

import logging
from typing import Dict, List, Any, Optional
from django.http import HttpRequest
from ..base.section_service_interface import ClinicalSectionServiceInterface

logger = logging.getLogger(__name__)


class ClinicalDataPipelineManager:
    """Pipeline manager for coordinating clinical section services."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ClinicalDataPipelineManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the pipeline manager (singleton pattern)."""
        if not self._initialized:
            self._service_registry: Dict[str, ClinicalSectionServiceInterface] = {}
            self._cached_results: Dict[str, Dict[str, Any]] = {}  # Cache results by session_id
            logger.info("[PIPELINE MANAGER] Initialized (Singleton)")
            ClinicalDataPipelineManager._initialized = True
        else:
            logger.debug("[PIPELINE MANAGER] Using existing singleton instance")
    
    def register_service(self, service: ClinicalSectionServiceInterface) -> None:
        """Register a clinical section service."""
        section_code = service.get_section_code()
        section_name = service.get_section_name().lower().replace(' ', '_')
        
        self._service_registry[section_code] = service
        self._service_registry[section_name] = service
        
        logger.info(f"[PIPELINE MANAGER] Registered: {service.get_section_name()} (Total: {len(self.get_all_services())})")
    
    def get_service(self, section_identifier: str) -> Optional[ClinicalSectionServiceInterface]:
        """Get a registered service."""
        return self._service_registry.get(section_identifier)
    
    def get_all_services(self) -> Dict[str, ClinicalSectionServiceInterface]:
        """Get unique services."""
        unique_services = {}
        for key, service in self._service_registry.items():
            if service.get_section_code() not in unique_services:
                unique_services[service.get_section_code()] = service
        return unique_services
    
    def process_cda_content(self, request_or_cda=None, session_id=None, cda_content=None) -> Dict[str, Any]:
        """
        Process CDA content through all registered services.
        
        Supports two calling patterns:
        1. process_cda_content(request, session_id, cda_content) - full API
        2. process_cda_content(cda_content) - simple API for backward compatibility
        
        Args:
            request_or_cda: Either Django HTTP request or CDA content string
            session_id: Session identifier (optional, None for simple API)
            cda_content: CDA XML content (optional, None for simple API)
            
        Returns:
            Dict containing results from all services by section code
        """
        # Determine calling pattern
        if session_id is None and cda_content is None:
            # Simple API: process_cda_content(cda_content)
            cda_content = request_or_cda
            session_id = "browser_session"
            request = None
            logger.info(f"[PIPELINE MANAGER] Processing CDA content via simple API")
        else:
            # Full API: process_cda_content(request, session_id, cda_content)
            request = request_or_cda
            logger.info(f"[PIPELINE MANAGER] Processing CDA content for session {session_id}")
        
        results = {}
        unique_services = self.get_all_services()
        
        for section_code, service in unique_services.items():
            try:
                logger.info(f"[PIPELINE MANAGER] Processing section {section_code} ({service.get_section_name()})")
                
                # Extract data using the service
                section_data = service.extract_from_cda(cda_content)
                
                # Enhance and store data if we have a request object (full API mode)
                if request is not None and section_data:
                    try:
                        enhanced_data = service.enhance_and_store(request, session_id, section_data)
                        section_data = enhanced_data  # Use enhanced data for results
                        logger.info(f"[PIPELINE MANAGER] Enhanced and stored {len(enhanced_data)} items for section {section_code}")
                    except Exception as enhance_error:
                        logger.warning(f"[PIPELINE MANAGER] Could not enhance section {section_code}: {enhance_error}")
                        # Continue with raw data if enhancement fails
                
                results[section_code] = {
                    'section_name': service.get_section_name(),
                    'section_code': section_code,
                    'items': section_data,
                    'item_count': len(section_data)
                }
                
                logger.info(f"[PIPELINE MANAGER] Section {section_code}: {len(section_data)} items extracted")
                
            except Exception as e:
                logger.error(f"[PIPELINE MANAGER] Error processing section {section_code}: {e}")
                results[section_code] = {
                    'section_name': service.get_section_name(),
                    'section_code': section_code,
                    'items': [],
                    'item_count': 0,
                    'error': str(e)
                }
        
        logger.info(f"[PIPELINE MANAGER] Completed CDA processing: {len(results)} sections processed")
        
        # Cache the results for this session
        self._cached_results[session_id] = results
        
        return results
    
    def get_template_context(self, request=None, session_id=None) -> Dict[str, Any]:
        """
        Get template context from processed CDA data.
        
        Supports two calling patterns:
        1. get_template_context(request, session_id) - full API
        2. get_template_context() - simple API for backward compatibility
        
        Args:
            request: Django HTTP request (optional, None for simple API)
            session_id: Session identifier (optional, None for simple API)
            
        Returns:
            Dict containing template context data
        """
        # Determine calling pattern
        if request is None and session_id is None:
            # Simple API: get_template_context()
            session_id = "browser_session"
            logger.info(f"[PIPELINE MANAGER] Building template context via simple API")
        else:
            # Full API: get_template_context(request, session_id)
            logger.info(f"[PIPELINE MANAGER] Building template context for session {session_id}")
        
        # Get cached results from process_cda_content
        cached_results = self._cached_results.get(session_id, {})
        
        # Build template context from cached results
        context = {
            'sections_processed': list(cached_results.keys()),
            'medications': cached_results.get('10160-0', {}).get('items', []),
            'allergies': cached_results.get('48765-2', {}).get('items', []),
            'problems': cached_results.get('11450-4', {}).get('items', []),
            'vital_signs': cached_results.get('8716-3', {}).get('items', []),
            'procedures': cached_results.get('47519-4', {}).get('items', []),  # CRITICAL: Enhanced procedures mapping
            'immunizations': cached_results.get('11369-6', {}).get('items', []),
            'results': cached_results.get('30954-2', {}).get('items', []),
            'medical_devices': cached_results.get('46264-8', {}).get('items', []),
            'past_illness': cached_results.get('11348-0', {}).get('items', []),
            'pregnancy_history': cached_results.get('10162-6', {}).get('items', []),
            'social_history': cached_results.get('29762-2', {}).get('items', []),
            'advance_directives': cached_results.get('42348-3', {}).get('items', []),
            'functional_status': cached_results.get('47420-5', {}).get('items', [])
        }
        
        # Log the procedures specifically for debugging
        procedures_count = len(context['procedures'])
        logger.info(f"[PIPELINE MANAGER] Template context built with {procedures_count} procedures for session {session_id}")
        
        if procedures_count > 0:
            logger.info(f"[PIPELINE MANAGER] *** PROCEDURES FOUND: {[p.get('name', 'Unknown') for p in context['procedures']]} ***")
        
        return context


# Global singleton pipeline manager instance
clinical_pipeline_manager = ClinicalDataPipelineManager()
