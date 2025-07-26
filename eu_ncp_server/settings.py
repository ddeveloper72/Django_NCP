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

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # EU eHealth NCP Applications
    "ncp_gateway",
    "ehealth_portal",
    "smp_client",
    "fhir_services",
    # Third-party apps for eHealth functionality
    "rest_framework",
    "corsheaders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "eu_ncp_server.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "eu_ncp_server.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


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
    "handlers": {
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
    },
    "root": {
        "handlers": ["console", "file"],
        "level": os.getenv("LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "audit": {
            "handlers": ["audit_file"],
            "level": "INFO",
            "propagate": False,
        },
        "ehealth": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
