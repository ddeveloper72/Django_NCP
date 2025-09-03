"""
Central Terminology Server (CTS) Configuration
Settings for CTS integration with MVC/MTC synchronization
"""

from django.conf import settings
import os

# CTS Environment Configuration
CTS_CONFIG = {
    "ENVIRONMENTS": {
        "training": {
            "base_url": "https://webgate.training.ec.europa.eu/ehealth-term-portal/",
            "description": "Training environment for testing and development",
        },
        "acceptance": {
            "base_url": "https://webgate.acceptance.ec.europa.eu/ehealth-term-portal/",
            "description": "Acceptance environment for pre-production testing",
        },
        "production": {
            "base_url": "https://webgate.ec.europa.eu/ehealth-term-portal/",
            "description": "Production environment for live operations",
        },
    },
    # Default environment (should be 'training' for development)
    "DEFAULT_ENVIRONMENT": getattr(settings, "CTS_ENVIRONMENT", "training"),
    # Member State Configuration
    "COUNTRY_CODE": getattr(settings, "CTS_COUNTRY_CODE", "IE"),  # Ireland
    "COUNTRY_NAME": getattr(settings, "CTS_COUNTRY_NAME", "Ireland"),
    # API Configuration
    "REQUEST_TIMEOUT": getattr(settings, "CTS_REQUEST_TIMEOUT", 30),
    "MAX_RETRIES": getattr(settings, "CTS_MAX_RETRIES", 3),
    "BACKOFF_FACTOR": getattr(settings, "CTS_BACKOFF_FACTOR", 1),
    # Synchronization Configuration
    "SYNC_SCHEDULE": {
        "MVC_INTERVAL_HOURS": getattr(settings, "CTS_MVC_SYNC_INTERVAL", 24),  # Daily
        "MTC_INTERVAL_HOURS": getattr(settings, "CTS_MTC_SYNC_INTERVAL", 168),  # Weekly
        "AUTO_SYNC_ENABLED": getattr(settings, "CTS_AUTO_SYNC_ENABLED", False),
    },
    # Language Configuration
    "SUPPORTED_LANGUAGES": [
        "en",  # English
        "fr",  # French
        "de",  # German
        "es",  # Spanish
        "it",  # Italian
        "pt",  # Portuguese
        "nl",  # Dutch
        "da",  # Danish
        "sv",  # Swedish
        "fi",  # Finnish
        "pl",  # Polish
        "cs",  # Czech
        "sk",  # Slovak
        "hu",  # Hungarian
        "sl",  # Slovenian
        "hr",  # Croatian
        "bg",  # Bulgarian
        "ro",  # Romanian
        "el",  # Greek
        "et",  # Estonian
        "lv",  # Latvian
        "lt",  # Lithuanian
        "mt",  # Maltese
    ],
    # Default languages for synchronization
    "DEFAULT_SYNC_LANGUAGES": getattr(
        settings, "CTS_DEFAULT_LANGUAGES", ["en", "fr", "de", "es", "it"]
    ),
}

# Standard Terminology Systems for Healthcare
TERMINOLOGY_SYSTEMS = {
    "ICD10": {
        "name": "International Classification of Diseases 10th Revision",
        "oid": "2.16.840.1.113883.6.3",
        "description": "WHO International Classification of Diseases",
        "priority": 1,
    },
    "ICD11": {
        "name": "International Classification of Diseases 11th Revision",
        "oid": "2.16.840.1.113883.6.344",
        "description": "WHO International Classification of Diseases 11th Revision",
        "priority": 1,
    },
    "SNOMED_CT": {
        "name": "SNOMED Clinical Terms",
        "oid": "2.16.840.1.113883.6.96",
        "description": "Systematized Nomenclature of Medicine Clinical Terms",
        "priority": 1,
    },
    "LOINC": {
        "name": "Logical Observation Identifiers Names and Codes",
        "oid": "2.16.840.1.113883.6.1",
        "description": "LOINC database for laboratory data",
        "priority": 1,
    },
    "ATC": {
        "name": "Anatomical Therapeutic Chemical Classification",
        "oid": "2.16.840.1.113883.6.73",
        "description": "WHO Collaborating Centre for Drug Statistics Methodology",
        "priority": 2,
    },
    "RXNORM": {
        "name": "RxNorm",
        "oid": "2.16.840.1.113883.6.88",
        "description": "US National Library of Medicine normalized drug names",
        "priority": 2,
    },
    "UCUM": {
        "name": "Unified Code for Units of Measure",
        "oid": "2.16.840.1.113883.6.8",
        "description": "Units of measure for healthcare",
        "priority": 2,
    },
    "HL7_FHIR": {
        "name": "HL7 FHIR Code Systems",
        "oid": "2.16.840.1.113883.4.642",
        "description": "HL7 Fast Healthcare Interoperability Resources",
        "priority": 2,
    },
}

# epSOS Specific Value Sets (used in cross-border healthcare)
EPSOS_VALUE_SETS = {
    "COUNTRY_CODES": {
        "oid": "1.3.6.1.4.1.12559.11.10.1.3.1.42.1",
        "name": "epSOS Country Codes",
        "description": "ISO 3166-1 alpha-2 country codes used in epSOS",
    },
    "LANGUAGE_CODES": {
        "oid": "1.3.6.1.4.1.12559.11.10.1.3.1.42.2",
        "name": "epSOS Language Codes",
        "description": "ISO 639-1 language codes used in epSOS",
    },
    "DOCUMENT_TYPES": {
        "oid": "1.3.6.1.4.1.12559.11.10.1.3.1.42.3",
        "name": "epSOS Document Types",
        "description": "Clinical document types supported by epSOS",
    },
    "HEALTHCARE_PROFESSIONAL_ROLES": {
        "oid": "1.3.6.1.4.1.12559.11.10.1.3.1.42.4",
        "name": "Healthcare Professional Roles",
        "description": "Roles of healthcare professionals in epSOS",
    },
    "ALLERGY_INTOLERANCE": {
        "oid": "1.3.6.1.4.1.12559.11.10.1.3.1.42.5",
        "name": "Allergy and Intolerance",
        "description": "Allergy and intolerance types for Patient Summary",
    },
    "MEDICAL_DEVICES": {
        "oid": "1.3.6.1.4.1.12559.11.10.1.3.1.42.6",
        "name": "Medical Devices",
        "description": "Medical devices for Patient Summary",
    },
}

# CTS API Endpoints Configuration
CTS_API_ENDPOINTS = {
    "value_sets": "api/v1/valuesets",
    "concepts": "api/v1/concepts",
    "translations": "api/v1/translations",
    "mappings": "api/v1/mappings",
    "sync_status": "api/v1/sync/status",
    "member_state_config": "api/v1/memberstate/{country_code}",
    "mvc_sync": "api/v1/mvc/sync",
    "mtc_sync": "api/v1/mtc/sync",
    "search": "api/v1/search",
    "validate": "api/v1/validate",
}

# Logging Configuration for CTS
CTS_LOGGING_CONFIG = {
    "LOG_LEVEL": getattr(settings, "CTS_LOG_LEVEL", "INFO"),
    "LOG_FORMAT": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "LOG_FILE": getattr(settings, "CTS_LOG_FILE", None),  # None = console only
    "AUDIT_ENABLED": getattr(settings, "CTS_AUDIT_ENABLED", True),
    "AUDIT_EVENTS": [
        "sync_started",
        "sync_completed",
        "sync_failed",
        "api_request",
        "api_response",
        "terminology_updated",
        "mapping_updated",
        "translation_updated",
    ],
}

# Cache Configuration for CTS Data
CTS_CACHE_CONFIG = {
    "ENABLED": getattr(settings, "CTS_CACHE_ENABLED", True),
    "TIMEOUT_SECONDS": getattr(settings, "CTS_CACHE_TIMEOUT", 3600),  # 1 hour
    "KEY_PREFIX": "cts_",
    "VERSION": 1,
}

# Validation Configuration
CTS_VALIDATION_CONFIG = {
    "VALIDATE_ON_SYNC": getattr(settings, "CTS_VALIDATE_ON_SYNC", True),
    "STRICT_MODE": getattr(settings, "CTS_STRICT_MODE", False),
    "ALLOW_UNKNOWN_SYSTEMS": getattr(settings, "CTS_ALLOW_UNKNOWN_SYSTEMS", True),
    "MIN_CONFIDENCE_SCORE": getattr(settings, "CTS_MIN_CONFIDENCE_SCORE", 0.7),
}


def get_cts_setting(key: str, default=None):
    """
    Get CTS configuration setting with dot notation

    Args:
        key: Setting key with dot notation (e.g., 'SYNC_SCHEDULE.MVC_INTERVAL_HOURS')
        default: Default value if setting not found

    Returns:
        Setting value or default
    """
    keys = key.split(".")
    value = CTS_CONFIG

    try:
        for k in keys:
            value = value[k]
        return value
    except (KeyError, TypeError):
        return default


def get_environment_config(environment: str = None) -> dict:
    """
    Get configuration for specified CTS environment

    Args:
        environment: Environment name ('training', 'acceptance', 'production')

    Returns:
        Environment configuration dictionary
    """
    env = environment or CTS_CONFIG["DEFAULT_ENVIRONMENT"]
    return CTS_CONFIG["ENVIRONMENTS"].get(env, CTS_CONFIG["ENVIRONMENTS"]["training"])


def is_cts_enabled() -> bool:
    """
    Check if CTS integration is enabled and properly configured

    Returns:
        True if CTS is enabled and configured
    """
    return getattr(settings, "CTS_ENABLED", True)


def get_terminology_system_oid(system_name: str) -> str:
    """
    Get OID for a standard terminology system

    Args:
        system_name: Name of the terminology system

    Returns:
        OID string or empty string if not found
    """
    system = TERMINOLOGY_SYSTEMS.get(system_name.upper())
    return system["oid"] if system else ""


def get_epsos_value_set_oid(value_set_name: str) -> str:
    """
    Get OID for an epSOS value set

    Args:
        value_set_name: Name of the epSOS value set

    Returns:
        OID string or empty string if not found
    """
    value_set = EPSOS_VALUE_SETS.get(value_set_name.upper())
    return value_set["oid"] if value_set else ""
