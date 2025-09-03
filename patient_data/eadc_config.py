"""
EADC Configuration Settings
Configuration file for EADC integration and security settings
"""

from django.conf import settings
import os

# EADC Integration Settings
EADC_CONFIG = {
    # Path to EADC resources directory
    "EADC_RESOURCES_PATH": getattr(
        settings,
        "EADC_RESOURCES_PATH",
        "C:\\Users\\Duncan\\VS_Code_Projects\\ehealth-2\\openncp-docker\\openncp-configuration\\EADC_resources",
    ),
    # Supported document types and their configurations
    "SUPPORTED_DOCUMENT_TYPES": {
        "PS": {
            "name": "Patient Summary",
            "template_id": "1.3.6.1.4.1.12559.11.10.1.3.1.1.3",
            "schema_file": "CDA_extended.xsd",
            "transformation_priority": 1,
        },
        "EP": {
            "name": "ePrescription",
            "template_id": "1.3.6.1.4.1.12559.11.10.1.3.1.1.1",
            "schema_file": "CDA_Pharma.xsd",
            "transformation_priority": 2,
        },
        "ED": {
            "name": "eDispensation",
            "template_id": "1.3.6.1.4.1.12559.11.10.1.3.1.1.2",
            "schema_file": "CDA_Pharma.xsd",
            "transformation_priority": 3,
        },
    },
    # Security settings
    "SECURITY": {
        "REQUIRE_STAFF_ACCESS": True,
        "REQUIRE_GROUP_MEMBERSHIP": True,
        "ADMIN_GROUP_NAME": "eadc_administrators",
        "OPERATOR_GROUP_NAME": "eadc_operators",
        "LOG_ALL_ACTIVITIES": True,
        "AUDIT_RETENTION_DAYS": 90,
    },
    # Processing settings
    "PROCESSING": {
        "MAX_DOCUMENT_SIZE_MB": 50,
        "TIMEOUT_SECONDS": 300,
        "ENABLE_VALIDATION": True,
        "ENABLE_TRANSFORMATION": True,
        "AUTO_SAVE_PROCESSED": True,
    },
    # Member state mappings for transformations
    "MEMBER_STATE_MAPPINGS": {
        "AT": {"name": "Austria", "locale": "de_AT"},
        "BE": {"name": "Belgium", "locale": "fr_BE"},
        "BG": {"name": "Bulgaria", "locale": "bg_BG"},
        "CY": {"name": "Cyprus", "locale": "el_CY"},
        "CZ": {"name": "Czech Republic", "locale": "cs_CZ"},
        "DE": {"name": "Germany", "locale": "de_DE"},
        "DK": {"name": "Denmark", "locale": "da_DK"},
        "EE": {"name": "Estonia", "locale": "et_EE"},
        "ES": {"name": "Spain", "locale": "es_ES"},
        "FI": {"name": "Finland", "locale": "fi_FI"},
        "FR": {"name": "France", "locale": "fr_FR"},
        "GR": {"name": "Greece", "locale": "el_GR"},
        "HR": {"name": "Croatia", "locale": "hr_HR"},
        "HU": {"name": "Hungary", "locale": "hu_HU"},
        "IE": {"name": "Ireland", "locale": "en_IE"},
        "IT": {"name": "Italy", "locale": "it_IT"},
        "LT": {"name": "Lithuania", "locale": "lt_LT"},
        "LU": {"name": "Luxembourg", "locale": "fr_LU"},
        "LV": {"name": "Latvia", "locale": "lv_LV"},
        "MT": {"name": "Malta", "locale": "mt_MT"},
        "NL": {"name": "Netherlands", "locale": "nl_NL"},
        "PL": {"name": "Poland", "locale": "pl_PL"},
        "PT": {"name": "Portugal", "locale": "pt_PT"},
        "RO": {"name": "Romania", "locale": "ro_RO"},
        "SE": {"name": "Sweden", "locale": "sv_SE"},
        "SI": {"name": "Slovenia", "locale": "sl_SI"},
        "SK": {"name": "Slovakia", "locale": "sk_SK"},
    },
}

# Validation settings
EADC_VALIDATION_CONFIG = {
    "REQUIRED_CDA_ELEMENTS": [
        "ClinicalDocument",
        "recordTarget/patientRole",
        "author",
        "custodian",
    ],
    "REQUIRED_PS_SECTIONS": [
        "48765-2",  # Allergies and adverse reactions
        "10160-0",  # History of medication use
        "11450-4",  # Problem list
    ],
    "EPSOS_NAMESPACES": {
        "cda": "urn:hl7-org:v3",
        "epsos": "urn:epsos-org:ep:medication",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    },
}

# Audit configuration
EADC_AUDIT_CONFIG = {
    "LOG_LEVEL": "INFO",
    "LOG_FORMAT": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "AUDIT_EVENTS": [
        "document_validation",
        "document_transformation",
        "user_access",
        "admin_action",
        "error_occurred",
    ],
}


def get_eadc_setting(key, default=None):
    """
    Get EADC configuration setting
    """
    keys = key.split(".")
    value = EADC_CONFIG

    try:
        for k in keys:
            value = value[k]
        return value
    except (KeyError, TypeError):
        return default


def is_eadc_enabled():
    """
    Check if EADC integration is enabled and properly configured
    """
    resources_path = get_eadc_setting("EADC_RESOURCES_PATH")

    if not resources_path:
        return False

    return os.path.exists(resources_path)


def get_member_state_info(country_code):
    """
    Get member state information by country code
    """
    return get_eadc_setting(
        f"MEMBER_STATE_MAPPINGS.{country_code}",
        {"name": country_code, "locale": "en_US"},
    )
