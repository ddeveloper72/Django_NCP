"""
Enhanced CTS Service with Comprehensive MVC Integration

Provides structured responses from the Master Value Catalogue (MVC) including:
- Code System ID and Version tracking
- Multi-language support for EU cross-border healthcare  
- Complete clinical terminology data for UI flexibility
- Regulatory compliance and audit trail support

Author: EU NCP Portal Development Team
Date: October 2025
"""

import logging
from typing import Dict, List, Optional, Any, Union
from django.conf import settings
from django.core.cache import cache

from translation_services.cts_integration import CTSAPIClient, CTSTranslationService
from translation_services.mvc_models import ValueSetCatalogue, ValueSetConcept, ConceptTranslation

logger = logging.getLogger('ehealth')


class EnhancedCTSService:
    """
    Enhanced CTS Service providing comprehensive structured responses
    from the Master Value Catalogue with full MVC field coverage.
    """
    
    def __init__(self):
        """Initialize enhanced CTS service with MVC integration."""
        self.cts_client = CTSAPIClient()
        self.cts_translator = CTSTranslationService()
        self.cache_timeout = getattr(settings, 'CTS_CACHE_TIMEOUT', 3600)  # 1 hour default
        
    def get_comprehensive_code_data(
        self, 
        code: str, 
        code_system_oid: str, 
        target_language: str = 'en',
        include_all_languages: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive structured data for a clinical code from MVC.
        
        Args:
            code: The clinical code (e.g., 'H03AA01')
            code_system_oid: The code system OID (e.g., '2.16.840.1.113883.6.73')
            target_language: Primary language for display (default: 'en')
            include_all_languages: Include all available language translations
            
        Returns:
            Comprehensive structured response with all MVC fields:
            {
                'code': 'H03AA01',
                'code_name': 'levothyroxine sodium',
                'description': 'Thyroid hormones',
                'code_system_id': '2.16.840.1.113883.6.73',
                'code_system_name': 'ATC',
                'code_system_version': '2024-01-15',
                'version_date': '2024-01-15T00:00:00Z',
                'primary_language': 'en',
                'languages': {
                    'en': 'levothyroxine sodium',
                    'pt': 'levotiroxina sódica',
                    'es': 'levotiroxina sódica'
                },
                'display_value': 'levothyroxine sodium',
                'full_description': 'Thyroid hormone replacement therapy',
                'clinical_context': 'medication',
                'cts_metadata': {
                    'source': 'MVC',
                    'query_timestamp': '2025-10-17T17:35:00Z',
                    'confidence': 'high'
                }
            }
        """
        if not code or not code_system_oid:
            logger.warning("Enhanced CTS: Missing required parameters - code or code_system_oid")
            return None
            
        cache_key = f"enhanced_cts_{code}_{code_system_oid}_{target_language}"
        
        # Check cache first
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Enhanced CTS: Cache hit for {code} in {code_system_oid}")
            return cached_result
            
        try:
            # Try CTS translation
            cts_response = self.cts_translator.translate_concept(
                source_code=code,
                source_system_oid=code_system_oid,
                target_language=target_language
            )
            
            if not cts_response:
                logger.warning(f"Enhanced CTS: No CTS result for {code} in {code_system_oid}")
                return None
                
            # Get MVC catalogue information
            mvc_data = self._get_mvc_comprehensive_data(code, code_system_oid)
            
            # Get all language translations if requested
            language_data = {}
            if include_all_languages:
                language_data = self._get_all_language_translations(code, code_system_oid)
            
            # Build comprehensive structured response
            comprehensive_response = {
                # Core code information
                'code': code,
                'code_name': cts_response or '',
                'description': cts_response or '',
                
                # Code system metadata  
                'code_system_id': code_system_oid,
                'code_system_name': mvc_data.get('code_system_name', ''),
                'code_system_version': mvc_data.get('code_system_version', ''),
                'version_date': mvc_data.get('version_date', ''),
                
                # Language support
                'primary_language': target_language,
                'languages': language_data,
                'display_value': cts_response or '',
                'full_description': cts_response or '',
                
                # Clinical context
                'clinical_context': self._determine_clinical_context(code_system_oid),
                
                # CTS metadata for audit trails
                'cts_metadata': {
                    'source': 'MVC',
                    'query_timestamp': self._get_iso_timestamp(),
                    'confidence': 'medium',
                    'cache_key': cache_key
                }
            }
            
            # Cache the comprehensive response
            cache.set(cache_key, comprehensive_response, self.cache_timeout)
            
            logger.info(f"Enhanced CTS: Successfully resolved {code} with comprehensive MVC data")
            return comprehensive_response
            
        except Exception as e:
            logger.error(f"Enhanced CTS: Error resolving {code} in {code_system_oid}: {str(e)}")
            return None
    
    def _get_mvc_comprehensive_data(self, code: str, code_system_oid: str) -> Dict[str, Any]:
        """Get comprehensive data from MVC including version and system information."""
        try:
            # Get value set catalogue entry
            catalogue_entry = ValueSetCatalogue.objects.filter(
                code_system_oid=code_system_oid
            ).first()
            
            if not catalogue_entry:
                return {}
                
            # Get concept data
            concept = ValueSetConcept.objects.filter(
                value_set=catalogue_entry,
                concept_code=code
            ).first()
            
            if not concept:
                return {}
                
            return {
                'code_system_name': catalogue_entry.name or '',
                'code_system_version': catalogue_entry.version or '',
                'version_date': catalogue_entry.last_updated.isoformat() if catalogue_entry.last_updated else '',
                'concept_status': concept.status if hasattr(concept, 'status') else 'active'
            }
            
        except Exception as e:
            logger.error(f"Enhanced CTS: Error getting MVC data for {code}: {str(e)}")
            return {}
    
    def _get_all_language_translations(self, code: str, code_system_oid: str) -> Dict[str, str]:
        """Get all available language translations for a code."""
        try:
            translations = {}
            
            # Get all available language codes in the system
            available_languages = ['en', 'pt', 'es', 'fr', 'de', 'it', 'nl']  # EU languages
            
            for lang_code in available_languages:
                try:
                    # Get translation for this language
                    translation_result = self.cts_client.translate_code(
                        code=code,
                        code_system_oid=code_system_oid,
                        target_language=lang_code
                    )
                    
                    if translation_result and translation_result.get('display_value'):
                        translations[lang_code] = translation_result['display_value']
                        
                except Exception as lang_error:
                    # Don't fail entire request for one language
                    logger.debug(f"Enhanced CTS: Could not get {lang_code} translation for {code}: {str(lang_error)}")
                    continue
                    
            return translations
            
        except Exception as e:
            logger.error(f"Enhanced CTS: Error getting language translations for {code}: {str(e)}")
            return {}
    
    def _determine_clinical_context(self, code_system_oid: str) -> str:
        """Determine clinical context based on code system OID."""
        context_mapping = {
            '2.16.840.1.113883.6.73': 'medication',      # ATC
            '2.16.840.1.113883.6.96': 'clinical',        # SNOMED CT
            '2.16.840.1.113883.6.90': 'diagnosis',       # ICD-10
            '2.16.840.1.113883.6.4': 'procedure',        # ICD-10-PCS
            '2.16.840.1.113883.6.1': 'laboratory',       # LOINC
        }
        
        return context_mapping.get(code_system_oid, 'general')
    
    def _get_iso_timestamp(self) -> str:
        """Get current ISO timestamp for metadata."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'
    
    def get_bulk_code_data(
        self, 
        codes_and_systems: List[Dict[str, str]], 
        target_language: str = 'en'
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get comprehensive data for multiple codes efficiently.
        
        Args:
            codes_and_systems: List of {'code': 'H03AA01', 'code_system_oid': '2.16.840.1.113883.6.73'}
            target_language: Target language for translations
            
        Returns:
            Dictionary keyed by 'code_codesystem' with comprehensive data
        """
        results = {}
        
        for item in codes_and_systems:
            code = item.get('code')
            code_system_oid = item.get('code_system_oid')
            
            if code and code_system_oid:
                key = f"{code}_{code_system_oid}"
                result = self.get_comprehensive_code_data(
                    code=code,
                    code_system_oid=code_system_oid,
                    target_language=target_language
                )
                
                if result:
                    results[key] = result
                    
        return results
    
    def enhance_clinical_section_data(
        self, 
        clinical_data: List[Dict[str, Any]], 
        code_field: str = 'code',
        oid_field: str = 'code_system_oid',
        target_language: str = 'en'
    ) -> List[Dict[str, Any]]:
        """
        Enhance entire clinical section data with comprehensive CTS information.
        
        Args:
            clinical_data: List of clinical items with codes
            code_field: Field name containing the code
            oid_field: Field name containing the code system OID  
            target_language: Target language for enhancement
            
        Returns:
            Enhanced clinical data with 'cts_enhanced' field containing comprehensive data
        """
        enhanced_data = []
        
        for item in clinical_data:
            enhanced_item = item.copy()
            
            code = item.get(code_field)
            oid = item.get(oid_field)
            
            if code and oid:
                comprehensive_data = self.get_comprehensive_code_data(
                    code=code,
                    code_system_oid=oid,
                    target_language=target_language
                )
                
                if comprehensive_data:
                    enhanced_item['cts_enhanced'] = comprehensive_data
                    # Also add direct access fields for template convenience
                    enhanced_item['enhanced_display'] = comprehensive_data.get('display_value', '')
                    enhanced_item['enhanced_description'] = comprehensive_data.get('description', '')
                    enhanced_item['enhanced_code'] = comprehensive_data.get('code', '')
                    
            enhanced_data.append(enhanced_item)
            
        return enhanced_data


# Global instance for application use
enhanced_cts_service = EnhancedCTSService()