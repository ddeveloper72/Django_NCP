"""
FHIR Pipeline Manager

Orchestration system for FHIR clinical section extractors.
Coordinates extraction of all clinical sections from FHIR R4 bundles.

Part of the FHIR-CDA architecture separation initiative.

Author: Django_NCP Development Team
Date: November 2025
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class FHIRPipelineManager:
    """
    Pipeline manager for coordinating FHIR clinical section extractors.
    
    Singleton pattern ensures consistent extractor registry across the application.
    Manages extraction workflow from FHIR bundles through all registered extractors.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super(FHIRPipelineManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the pipeline manager (singleton pattern)."""
        if not self._initialized:
            self._extractor_registry: Dict[str, Any] = {}  # section_id -> extractor instance
            self._cached_results: Dict[str, Dict[str, Any]] = {}  # Cache results by session_id
            logger.info("[FHIR PIPELINE] Initialized (Singleton)")
            FHIRPipelineManager._initialized = True
        else:
            logger.debug("[FHIR PIPELINE] Using existing singleton instance")
    
    def register_extractor(self, extractor: Any) -> None:
        """
        Register a FHIR clinical section extractor.
        
        Args:
            extractor: Instance of FHIRSectionServiceBase subclass
        """
        section_id = extractor.section_id
        section_title = extractor.section_title
        
        if section_id in self._extractor_registry:
            logger.warning(f"[FHIR PIPELINE] Overwriting existing extractor for section: {section_id}")
        
        self._extractor_registry[section_id] = extractor
        
        logger.info(
            f"[FHIR PIPELINE] Registered: {section_title} "
            f"(section_id: {section_id}, total: {len(self._extractor_registry)})"
        )
    
    def get_extractor(self, section_id: str) -> Optional[Any]:
        """
        Get a registered extractor by section ID.
        
        Args:
            section_id: Section identifier (e.g., 'allergies', 'medications')
            
        Returns:
            Extractor instance or None if not found
        """
        return self._extractor_registry.get(section_id)
    
    def get_all_extractors(self) -> Dict[str, Any]:
        """
        Get all registered extractors.
        
        Returns:
            Dict mapping section_id to extractor instance
        """
        return self._extractor_registry.copy()
    
    def process_fhir_bundle(
        self, 
        fhir_bundle: Dict[str, Any],
        session_id: Optional[str] = None,
        sections_to_extract: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process FHIR bundle through all (or specified) registered extractors.
        
        Args:
            fhir_bundle: FHIR R4 Bundle resource
            session_id: Optional session identifier for caching (defaults to 'fhir_session')
            sections_to_extract: Optional list of section IDs to extract (None = all)
            
        Returns:
            Dict containing extracted data from all sections:
            {
                'sections': {
                    'allergies': {...section_data...},
                    'medications': {...section_data...},
                    ...
                },
                'summary': {
                    'total_sections': int,
                    'sections_with_data': int,
                    'total_entries': int
                }
            }
        """
        session_id = session_id or "fhir_session"
        
        logger.info(f"[FHIR PIPELINE] Processing FHIR bundle for session: {session_id}")
        
        # Determine which extractors to use
        if sections_to_extract:
            extractors_to_run = {
                sid: ext for sid, ext in self._extractor_registry.items()
                if sid in sections_to_extract
            }
            logger.info(f"[FHIR PIPELINE] Running {len(extractors_to_run)} specified extractors: {list(extractors_to_run.keys())}")
        else:
            extractors_to_run = self._extractor_registry
            logger.info(f"[FHIR PIPELINE] Running all {len(extractors_to_run)} registered extractors")
        
        # Extract data from each section
        sections = {}
        sections_with_data = 0
        total_entries = 0
        
        for section_id, extractor in extractors_to_run.items():
            try:
                logger.info(f"[FHIR PIPELINE] Extracting section: {section_id} ({extractor.section_title})")
                
                # Extract section data using the extractor
                section_data = extractor.extract_section(fhir_bundle)
                
                sections[section_id] = section_data
                
                # Track statistics
                if section_data.get("has_entries"):
                    sections_with_data += 1
                    total_entries += section_data.get("entry_count", 0)
                
                logger.info(
                    f"[FHIR PIPELINE] Section {section_id}: "
                    f"{section_data.get('entry_count', 0)} entries extracted"
                )
                
            except Exception as e:
                logger.error(f"[FHIR PIPELINE] Error extracting section {section_id}: {e}", exc_info=True)
                
                # Create error section data
                sections[section_id] = {
                    "section_id": section_id,
                    "title": getattr(extractor, 'section_title', 'Unknown'),
                    "has_entries": False,
                    "entry_count": 0,
                    "clinical_table": {
                        "entries": [],
                        "columns": [],
                        "display_config": {}
                    },
                    "clinical_codes": [],
                    "is_coded_section": False,
                    "error": str(e)
                }
        
        # Build result structure
        result = {
            "sections": sections,
            "summary": {
                "total_sections": len(sections),
                "sections_with_data": sections_with_data,
                "total_entries": total_entries,
                "bundle_type": fhir_bundle.get("type", "unknown"),
                "bundle_id": fhir_bundle.get("id", "unknown")
            }
        }
        
        logger.info(
            f"[FHIR PIPELINE] Completed bundle processing: "
            f"{sections_with_data}/{len(sections)} sections with data, "
            f"{total_entries} total entries"
        )
        
        # Cache the results for this session
        self._cached_results[session_id] = result
        
        return result
    
    def get_template_context(
        self,
        session_id: Optional[str] = None,
        fhir_bundle: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get template context from processed FHIR bundle data.
        
        Either retrieves cached results by session_id or processes a new bundle.
        
        Args:
            session_id: Session identifier for cached results (defaults to 'fhir_session')
            fhir_bundle: FHIR bundle to process if not using cached results
            
        Returns:
            Dict containing template context data compatible with CDA templates:
            {
                'allergies': [...entries...],
                'medications': [...entries...],
                'problems': [...entries...],
                'procedures': [...entries...],
                ...
            }
        """
        session_id = session_id or "fhir_session"
        
        # Process bundle if provided, otherwise use cached results
        if fhir_bundle:
            logger.info(f"[FHIR PIPELINE] Building template context from new bundle for session: {session_id}")
            results = self.process_fhir_bundle(fhir_bundle, session_id)
        else:
            logger.info(f"[FHIR PIPELINE] Building template context from cached results for session: {session_id}")
            results = self._cached_results.get(session_id)
            
            if not results:
                logger.warning(f"[FHIR PIPELINE] No cached results found for session: {session_id}")
                return {}
        
        # Extract sections data
        sections = results.get("sections", {})
        
        # Build template context (compatible with CDA template structure)
        context = {
            # Clinical sections
            'allergies': sections.get('allergies', {}).get('clinical_table', {}).get('entries', []),
            'medications': sections.get('medications', {}).get('clinical_table', {}).get('entries', []),
            'problems': sections.get('problems', {}).get('clinical_table', {}).get('entries', []),
            'procedures': sections.get('procedures', {}).get('clinical_table', {}).get('entries', []),
            'immunizations': sections.get('immunizations', {}).get('clinical_table', {}).get('entries', []),
            'results': sections.get('results', {}).get('clinical_table', {}).get('entries', []),
            'vital_signs': sections.get('vital_signs', {}).get('clinical_table', {}).get('entries', []),
            'observations': sections.get('observations', {}).get('clinical_table', {}).get('entries', []),
            
            # Section metadata (for display configuration)
            'sections_metadata': {
                section_id: {
                    'title': section_data.get('title'),
                    'has_entries': section_data.get('has_entries', False),
                    'entry_count': section_data.get('entry_count', 0),
                    'is_coded_section': section_data.get('is_coded_section', False),
                    'display_config': section_data.get('clinical_table', {}).get('display_config', {}),
                    'columns': section_data.get('clinical_table', {}).get('columns', []),
                    'icon_class': section_data.get('icon_class'),
                    'data_source': 'FHIR'
                }
                for section_id, section_data in sections.items()
            },
            
            # Summary statistics
            'data_source': 'FHIR',
            'bundle_processed': True,
            'sections_processed': list(sections.keys()),
            'total_entries': results.get('summary', {}).get('total_entries', 0),
        }
        
        # Log extraction summary
        for section_id in ['allergies', 'medications', 'problems', 'procedures']:
            count = len(context.get(section_id, []))
            if count > 0:
                logger.info(f"[FHIR PIPELINE] Template context: {section_id} = {count} entries")
        
        return context
    
    def get_section_summary(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get summary statistics for processed FHIR bundle.
        
        Args:
            session_id: Session identifier for cached results (defaults to 'fhir_session')
            
        Returns:
            Dict containing summary statistics
        """
        session_id = session_id or "fhir_session"
        results = self._cached_results.get(session_id)
        
        if not results:
            return {
                "error": "No cached results found",
                "session_id": session_id
            }
        
        return results.get("summary", {})
    
    def clear_cache(self, session_id: Optional[str] = None) -> None:
        """
        Clear cached results for a session or all sessions.
        
        Args:
            session_id: Specific session to clear, or None to clear all
        """
        if session_id:
            if session_id in self._cached_results:
                del self._cached_results[session_id]
                logger.info(f"[FHIR PIPELINE] Cleared cache for session: {session_id}")
        else:
            self._cached_results.clear()
            logger.info(f"[FHIR PIPELINE] Cleared all cached results")


# Global singleton pipeline manager instance
fhir_pipeline_manager = FHIRPipelineManager()
