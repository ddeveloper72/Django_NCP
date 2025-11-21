"""
Django settings for eu_ncp_server project.

EU eHealth NCP Server - Django implementation
Based on analysis of DomiSMP and OpenNCP Java implementations
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-change-me-in-production")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "True") == "True"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")

# Configure session management based on environment
from patient_data.session_management import configure_session_settings

configure_session_settings(globals())


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "compressor",
    # EU eHealth NCP Applications
    "ncp_gateway",
    "ehealth_portal",
    "smp_client",
    "fhir_services",
    # Authentication and User Management
    "authentication",
    # Patient Data and Translation Services
    "patient_data",
    "translation_manager",
    "translation_services",
    # Third-party apps for eHealth functionality
    "rest_framework",
    "corsheaders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # CRITICAL: GDPR Patient Session Isolation Middleware (MUST BE FIRST)
    "patient_data.middleware.session_isolation.PatientSessionIsolationMiddleware",
    # Patient Session Management Middleware
    "patient_data.middleware.session_security.PatientSessionMiddleware",
    "patient_data.middleware.session_security.SessionSecurityMiddleware",
    "patient_data.middleware.session_security.SessionCleanupMiddleware",
    "patient_data.middleware.session_security.AuditLoggingMiddleware",
    # NEW: Patient Session Security Middleware for automatic cleanup
    "patient_data.middleware.patient_session_security.PatientSessionSecurityMiddleware",
    "patient_data.middleware.patient_session_security.PatientSessionCleanupMiddleware",
]

ROOT_URLCONF = "eu_ncp_server.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.csrf",
            ],
        },
    },
]

WSGI_APPLICATION = "eu_ncp_server.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Configure database based on environment
DEVELOPMENT = os.getenv("DEVELOPMENT", "True") == "True"

if os.getenv("DATABASE_URL"):
    # Heroku PostgreSQL or Azure SQL via DATABASE_URL (Production)
    import dj_database_url
    DATABASES = {
        "default": dj_database_url.config(
            default=os.getenv("DATABASE_URL"),
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True,
        )
    }
elif not DEVELOPMENT and os.getenv("DATABASE_URL"):
    # Heroku Postgres configuration (standard for Heroku deployments)
    import dj_database_url
    DATABASES = {
        "default": dj_database_url.config(
            default=os.getenv("DATABASE_URL"),
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True,
        )
    }
    print(f"🗄️  Using Heroku Postgres Database (Production Mode)")
elif not DEVELOPMENT and os.getenv("AZURE_SQL_SERVER"):
    # Azure SQL Database configuration (for local development or Azure deployments)
    DATABASES = {
        "default": {
            "ENGINE": "mssql",
            "NAME": os.getenv("AZURE_SQL_DATABASE", "eHealth"),
            "USER": os.getenv("AZURE_SQL_USER"),
            "PASSWORD": os.getenv("AZURE_SQL_PASSWORD"),
            "HOST": os.getenv("AZURE_SQL_SERVER"),
            "PORT": os.getenv("AZURE_SQL_PORT", "1433"),
            "OPTIONS": {
                "driver": "ODBC Driver 18 for SQL Server",
                "extra_params": "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;",
            },
        }
    }
    print(f"🗄️  Using Azure SQL Database (Development Mode): {os.getenv('AZURE_SQL_DATABASE')}")
else:
    # Local SQLite for development (DEVELOPMENT=True)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
    print("📝 Using SQLite database (Development Mode)")


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Django Compressor settings for SASS compilation (local development only)
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# Only add compressor in development (requires native dependencies)
if DEVELOPMENT:
    STATICFILES_FINDERS.append("compressor.finders.CompressorFinder")
    COMPRESS_PRECOMPILERS = (("text/x-scss", "django_libsass.SassCompiler"),)
    COMPRESS_ENABLED = False  # Disabled in development
    COMPRESS_OFFLINE = False
    COMPRESS_CSS_HASHING_METHOD = "mtime"

# WhiteNoise configuration for production static files
# Use simpler storage on Heroku to avoid manifest issues
if DEVELOPMENT:
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
else:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

# Media files
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==============================================================================
# EU eHealth NCP Configuration
# ==============================================================================

# eHealth Services Configuration
EHEALTH_CONFIG = {
    "COUNTRY_CODE": os.getenv("COUNTRY_CODE", "IE"),
    "NCP_IDENTIFIER": os.getenv("NCP_IDENTIFIER", "ie-ncp-01"),
    "ORGANIZATION_NAME": os.getenv(
        "ORGANIZATION_NAME", "Ireland Health Service Executive"
    ),
    "ORGANIZATION_ID": os.getenv("ORGANIZATION_ID", "ie-hse"),
}

# SMP Integration (DomiSMP Connection)
SMP_CONFIG = {
    "BASE_URL": os.getenv("SMP_BASE_URL", "http://localhost:8290/smp"),
    "USERNAME": os.getenv("SMP_USERNAME", "iesmpuser"),
    "PASSWORD": os.getenv("SMP_PASSWORD", ""),
    "DOMAIN": os.getenv("SMP_DOMAIN", "domain1"),
    "KEYSTORE_PATH": os.getenv("SMP_KEYSTORE_PATH", ""),
    "KEYSTORE_PASSWORD": os.getenv("SMP_KEYSTORE_PASSWORD", ""),
    "TRUSTSTORE_PATH": os.getenv("SMP_TRUSTSTORE_PATH", ""),
    "TRUSTSTORE_PASSWORD": os.getenv("SMP_TRUSTSTORE_PASSWORD", ""),
}

# FHIR Configuration
FHIR_CONFIG = {
    "BASE_URL": os.getenv("FHIR_BASE_URL", "http://localhost:8000/fhir"),
    "VERSION": os.getenv("FHIR_VERSION", "R4"),
    "SERVICES": {
        "PATIENT_SUMMARY": os.getenv("ENABLE_PATIENT_SUMMARY", "True") == "True",
        "EPRESCRIPTION": os.getenv("ENABLE_EPRESCRIPTION", "True") == "True",
        "EDISPENSATION": os.getenv("ENABLE_EDISPENSATION", "True") == "True",
        "LABORATORY_RESULTS": os.getenv("ENABLE_LABORATORY_RESULTS", "True") == "True",
        "HOSPITAL_DISCHARGE": os.getenv("ENABLE_HOSPITAL_DISCHARGE", "True") == "True",
        "MEDICAL_IMAGING": os.getenv("ENABLE_MEDICAL_IMAGING", "True") == "True",
    },
}

# FHIR Provider Selection (HAPI or AZURE)
FHIR_PROVIDER = os.getenv("FHIR_PROVIDER", "HAPI").upper()

# HAPI FHIR Server Configuration
HAPI_FHIR_BASE_URL = os.getenv("HAPI_FHIR_BASE_URL", "https://hapi.fhir.org/baseR4")
HAPI_FHIR_TIMEOUT = int(os.getenv("HAPI_FHIR_TIMEOUT", "30"))
HAPI_FHIR_CACHE_TIMEOUT = int(os.getenv("HAPI_FHIR_CACHE_TIMEOUT", "300"))  # 5 minutes

# Azure FHIR Service Configuration
AZURE_FHIR_BASE_URL = os.getenv("AZURE_FHIR_BASE_URL", "")
AZURE_FHIR_TENANT_ID = os.getenv("AZURE_FHIR_TENANT_ID", "")
AZURE_FHIR_SUBSCRIPTION_ID = os.getenv("AZURE_FHIR_SUBSCRIPTION_ID", "")
AZURE_FHIR_RESOURCE_GROUP = os.getenv("AZURE_FHIR_RESOURCE_GROUP", "")
AZURE_FHIR_WORKSPACE = os.getenv("AZURE_FHIR_WORKSPACE", "")
AZURE_FHIR_SERVICE_NAME = os.getenv("AZURE_FHIR_SERVICE_NAME", "")
AZURE_FHIR_TIMEOUT = int(os.getenv("AZURE_FHIR_TIMEOUT", "30"))
AZURE_FHIR_CACHE_TIMEOUT = int(os.getenv("AZURE_FHIR_CACHE_TIMEOUT", "300"))  # 5 minutes

# Patient Portal Configuration
PORTAL_CONFIG = {
    "TITLE": os.getenv("PORTAL_TITLE", "Ireland eHealth Portal"),
    "ORGANIZATION": os.getenv("PORTAL_ORGANIZATION", "Health Service Executive"),
    "CONTACT_EMAIL": os.getenv("PORTAL_CONTACT_EMAIL", "support@hse.ie"),
    "PATIENT_LOGIN_ENABLED": os.getenv("PATIENT_LOGIN_ENABLED", "True") == "True",
    "PROFESSIONAL_LOGIN_ENABLED": os.getenv("PROFESSIONAL_LOGIN_ENABLED", "True")
    == "True",
}

# Cross-Border Services
CROSS_BORDER_CONFIG = {
    "PATIENT_LOOKUP_ENABLED": os.getenv("PATIENT_LOOKUP_ENABLED", "True") == "True",
    "AUTH_ENABLED": os.getenv("CROSS_BORDER_AUTH_ENABLED", "True") == "True",
    "CONSENT_REQUIRED": os.getenv("PATIENT_CONSENT_REQUIRED", "True") == "True",
}

# Security Configuration
SECURITY_CONFIG = {
    "USE_TLS": os.getenv("USE_TLS", "False") == "True",
    "TLS_CERT_FILE": os.getenv("TLS_CERT_FILE", ""),
    "TLS_KEY_FILE": os.getenv("TLS_KEY_FILE", ""),
    "AUDIT_LOG_ENABLED": os.getenv("AUDIT_LOG_ENABLED", "True") == "True",
    "AUDIT_LOG_FILE": os.getenv("AUDIT_LOG_FILE", "logs/audit.log"),
}

# Django REST Framework configuration
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# CORS settings for cross-border communication
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React frontend
    "http://localhost:8290",  # DomiSMP
    "https://localhost:8443",  # HTTPS DomiSMP
]

CORS_ALLOW_ALL_ORIGINS = DEBUG  # Only in development

# Logging configuration
# Use console logging on Heroku (ephemeral filesystem), file logging in development
if DEVELOPMENT:
    # Development: use file handlers
    log_handlers = {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.getenv("LOG_FILE", "logs/django_ncp.log"),
            "formatter": "verbose",
        },
        "audit_file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": SECURITY_CONFIG["AUDIT_LOG_FILE"],
            "formatter": "verbose",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    }
else:
    # Production/Heroku: console only (logs captured by platform)
    log_handlers = {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    }

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": log_handlers,
    "root": {
        "handlers": ["console"] if not DEVELOPMENT else ["console", "file"],
        "level": os.getenv("LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "audit": {
            "handlers": ["console"] if not DEVELOPMENT else ["audit_file"],
            "level": "INFO",
            "propagate": False,
        },
        "ehealth": {
            "handlers": ["console"] if not DEVELOPMENT else ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "patient_data.session": {
            "handlers": ["console"] if not DEVELOPMENT else ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "patient_data.security": {
            "handlers": ["console"] if not DEVELOPMENT else ["console", "file"],
            "level": "WARNING",
            "propagate": False,
        },
        # CRITICAL: GDPR Session Isolation Audit Logging
        "patient_data.middleware.session_isolation": {
            "handlers": ["console"] if not DEVELOPMENT else ["console", "file", "audit_file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.template": {
            "handlers": ["console"] if not DEVELOPMENT else ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "jinja2": {
            "handlers": ["console"] if not DEVELOPMENT else ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# European SMP Configuration
EUROPEAN_SMP_CONFIG = {
    "API_URL": os.getenv(
        "EUROPEAN_SMP_API_URL",
        "https://smp-ehealth-trn.acc.edelivery.tech.ec.europa.eu",
    ),
    "UI_URL": os.getenv(
        "EUROPEAN_SMP_UI_URL",
        "https://smp-ehealth-trn.acc.edelivery.tech.ec.europa.eu/ui/index.html",
    ),
    "SML_DOMAIN": os.getenv(
        "EUROPEAN_SML_DOMAIN", "ehealth-trn.acc.edelivery.tech.ec.europa.eu"
    ),
    "TIMEOUT": int(os.getenv("API_TIMEOUT_SECONDS", "30")),
}

# Local SMP Configuration
LOCALHOST_SMP_CONFIG = {
    "API_URL": os.getenv("LOCALHOST_SMP_API_URL", "http://localhost:8290/smp"),
    "UI_URL": os.getenv("LOCALHOST_SMP_UI_URL", "http://localhost:8290/smp"),
    "TIMEOUT": int(os.getenv("API_TIMEOUT_SECONDS", "30")),
}

# Certificate Configuration
CERTIFICATE_CONFIG = {
    "EPSOS_TLS_CERT": os.getenv(
        "EPSOS_TLS_CERT_PATH",
        "C:/Users/Duncan/VS_Code_Projects/Certificates/Epsos_TLS_2024.pem",
    ),
    "EPSOS_TLS_KEY": os.getenv(
        "EPSOS_TLS_KEY_PATH",
        "C:/Users/Duncan/VS_Code_Projects/Certificates/Epsos_TLS_2024.key",
    ),
    "EPSOS_CA_CERT": os.getenv(
        "EPSOS_CA_CERT_PATH",
        "C:/Users/Duncan/VS_Code_Projects/Certificates/Epsos_CA_2024.pem",
    ),
}

# API Rate Limiting
API_RATE_LIMIT = int(os.getenv("API_RATE_LIMIT", "1000"))

# Authentication Settings
# Redirect to welcome page after logout instead of admin logout page
LOGOUT_REDIRECT_URL = "/"  # Redirect to home/welcome page
LOGIN_REDIRECT_URL = "/"  # Redirect to home page after login
LOGIN_URL = "/accounts/login/"  # Use our custom login page

# ==============================================================================
# Patient Session Management Configuration
# ==============================================================================

# Patient Session Security Settings
PATIENT_SESSION_TIMEOUT = int(os.getenv("PATIENT_SESSION_TIMEOUT", "30"))  # minutes
PATIENT_SESSION_ROTATION_THRESHOLD = int(
    os.getenv("PATIENT_SESSION_ROTATION_THRESHOLD", "100")
)
MAX_CONCURRENT_PATIENT_SESSIONS = int(os.getenv("MAX_CONCURRENT_PATIENT_SESSIONS", "3"))
PATIENT_SESSION_RATE_LIMIT = int(
    os.getenv("PATIENT_SESSION_RATE_LIMIT", "60")
)  # requests per minute

# Session Encryption Configuration
SESSION_ENCRYPTION_ALGORITHM = "Fernet"
SESSION_KEY_ROTATION_HOURS = int(os.getenv("SESSION_KEY_ROTATION_HOURS", "24"))
PATIENT_SESSION_MASTER_KEY = os.getenv("PATIENT_SESSION_MASTER_KEY", "")

# Session Cleanup Configuration
SESSION_CLEANUP_INTERVAL = int(
    os.getenv("SESSION_CLEANUP_INTERVAL", "300")
)  # 5 minutes

# Security Alert Configuration
SECURITY_ALERT_RECIPIENTS = (
    os.getenv("SECURITY_ALERT_RECIPIENTS", "").split(",")
    if os.getenv("SECURITY_ALERT_RECIPIENTS")
    else []
)

# PHI Protection Settings
PHI_ENCRYPTION_ENABLED = os.getenv("PHI_ENCRYPTION_ENABLED", "True") == "True"
PHI_AUDIT_LOGGING = os.getenv("PHI_AUDIT_LOGGING", "True") == "True"

# Session Cache Configuration
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "patient-session-cache",
        "TIMEOUT": 3600,  # 1 hour
        "OPTIONS": {
            "MAX_ENTRIES": 1000,
        },
    }
}

# Session Management API Configuration
SESSION_API_ENABLED = os.getenv("SESSION_API_ENABLED", "True") == "True"
SESSION_MONITORING_ENABLED = os.getenv("SESSION_MONITORING_ENABLED", "True") == "True"

# ==============================================================================
# Common Terminology Services (CTS) Configuration
# ==============================================================================

# CTS Integration Settings
CTS_ENABLED = os.getenv("CTS_ENABLED", "False") == "True"
CTS_BASE_URL = os.getenv("CTS_BASE_URL", "")  # e.g., "https://cts.healthcare.gov/api/v1"
CTS_API_KEY = os.getenv("CTS_API_KEY", "")
CTS_CACHE_TIMEOUT = int(os.getenv("CTS_CACHE_TIMEOUT", "3600"))  # 1 hour default

# Medical Code System Configuration
SUPPORTED_CODE_SYSTEMS = {
    'icd10': '2.16.840.1.113883.6.3',
    'icd9': '2.16.840.1.113883.6.103',
    'snomed': '2.16.840.1.113883.6.96',
    'atc': '2.16.840.1.113883.6.73',
    'loinc': '2.16.840.1.113883.6.1',
    'orpha': '1.3.6.1.4.1.12559.11.10.1.3.1.44.5'
}

# Clinical Data Enhancement Settings
CLINICAL_DATA_ENHANCEMENT_ENABLED = os.getenv("CLINICAL_DATA_ENHANCEMENT_ENABLED", "True") == "True"
TEMPORAL_DATA_EXTRACTION_ENABLED = os.getenv("TEMPORAL_DATA_EXTRACTION_ENABLED", "True") == "True"
SEVERITY_EXTRACTION_ENABLED = os.getenv("SEVERITY_EXTRACTION_ENABLED", "True") == "True"
CRITICALITY_EXTRACTION_ENABLED = os.getenv("CRITICALITY_EXTRACTION_ENABLED", "True") == "True"

# Medical Terminology Cache Configuration
TERMINOLOGY_CACHE_ENABLED = os.getenv("TERMINOLOGY_CACHE_ENABLED", "True") == "True"
TERMINOLOGY_CACHE_TTL = int(os.getenv("TERMINOLOGY_CACHE_TTL", "86400"))  # 24 hours
TERMINOLOGY_NEGATIVE_CACHE_TTL = int(os.getenv("TERMINOLOGY_NEGATIVE_CACHE_TTL", "300"))  # 5 minutes
