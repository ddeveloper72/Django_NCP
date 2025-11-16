"""
FHIR Service Factory

Factory pattern to instantiate the correct FHIR integration service
based on Django settings (HAPI vs Azure)
"""

import logging
from django.conf import settings

logger = logging.getLogger("ehealth")


def get_fhir_service():
    """
    Get the configured FHIR integration service instance
    
    Returns appropriate service based on FHIR_PROVIDER setting:
    - 'HAPI': HAPIFHIRIntegrationService (public test server)
    - 'AZURE': AzureFHIRIntegrationService (Azure Healthcare APIs)
    
    Returns:
        HAPIFHIRIntegrationService or AzureFHIRIntegrationService instance
    """
    fhir_provider = getattr(settings, 'FHIR_PROVIDER', 'HAPI').upper()
    
    if fhir_provider == 'AZURE':
        logger.info("Using Azure FHIR integration service")
        from .azure_fhir_integration import AzureFHIRIntegrationService
        return AzureFHIRIntegrationService()
    else:
        logger.info("Using HAPI FHIR integration service")
        from .fhir_integration import HAPIFHIRIntegrationService
        return HAPIFHIRIntegrationService()


# Singleton instance for convenience
_fhir_service_instance = None


def get_fhir_service_singleton():
    """Get cached singleton instance of FHIR service"""
    global _fhir_service_instance
    
    if _fhir_service_instance is None:
        _fhir_service_instance = get_fhir_service()
        logger.info(f"Initialized FHIR service: {type(_fhir_service_instance).__name__}")
    
    return _fhir_service_instance


# Convenience alias for backward compatibility
fhir_service = get_fhir_service_singleton()
