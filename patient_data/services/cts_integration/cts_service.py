"""
CTS Service Wrapper for Clinical Code Translation

Provides a simple interface for translating clinical codes using the CTS integration.
This wrapper provides a compatible interface for services expecting get_term_display().

Author: Django_NCP Development Team
Date: October 2025
"""

import logging
from typing import Optional
from translation_services.cts_integration import CTSTranslationService

logger = logging.getLogger(__name__)

# Local fallback for codes not in EU CTS Portal
# Only used when CTS API returns None or errors
FALLBACK_TRANSLATIONS = {
    # ICD-10 codes (1.3.6.1.4.1.12559.11.10.1.3.1.44.2)
    '1.3.6.1.4.1.12559.11.10.1.3.1.44.2': {
        'D09': 'Carcinoma in situ of other and unspecified sites',
        'O24': 'Diabetes mellitus arising in pregnancy',
    },
    # SNOMED CT codes (2.16.840.1.113883.6.96)
    '2.16.840.1.113883.6.96': {
        '73425007': 'Inactive',
        '765205004': 'Disorder in remission',
        '55561003': 'Active',
    }
}


class CTSService:
    """
    Wrapper service providing simple code translation interface.
    
    Maps get_term_display() calls to CTSTranslationService.translate_concept().
    Falls back to local dictionary when EU CTS Portal lacks specific codes.
    """
    
    def __init__(self):
        """Initialize CTS service with translation service."""
        self.translator = CTSTranslationService()
        
    def get_term_display(self, code: str, code_system_oid: str, language: str = 'en') -> Optional[str]:
        """
        Get display term for a clinical code.
        
        Args:
            code: The clinical code (e.g., 'D09', '73425007')
            code_system_oid: The code system OID (e.g., '2.16.840.1.113883.6.96' for SNOMED)
            language: Target language (default: 'en')
            
        Returns:
            Translated display term or None if not found
        """
        try:
            # Try CTS API first
            result = self.translator.translate_concept(
                source_code=code,
                source_system_oid=code_system_oid,
                target_language=language
            )
            
            if result:
                logger.debug(f"[CTS] Translated {code} ({code_system_oid}) -> {result}")
                return result
            
            # Fall back to local dictionary if CTS has no translation
            if code_system_oid in FALLBACK_TRANSLATIONS:
                fallback = FALLBACK_TRANSLATIONS[code_system_oid].get(code)
                if fallback:
                    logger.info(f"[CTS] Using fallback translation for {code}: {fallback}")
                    return fallback
            
            logger.debug(f"[CTS] No translation found for {code} ({code_system_oid})")
            return None
            
        except Exception as e:
            # On CTS error, try fallback before giving up
            if code_system_oid in FALLBACK_TRANSLATIONS:
                fallback = FALLBACK_TRANSLATIONS[code_system_oid].get(code)
                if fallback:
                    logger.info(f"[CTS] CTS error, using fallback for {code}: {fallback}")
                    return fallback
            
            logger.error(f"[CTS] Error translating {code}: {e}")
            return None
