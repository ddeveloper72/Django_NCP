"""
Session Management Configuration
Flexible session handling for development vs production environments
"""

import os
from typing import Any, Dict, Optional

from django.conf import settings
from django.contrib.sessions.backends.db import SessionStore

# Development vs Production Session Configuration
DEVELOPMENT_SESSION_CONFIG = {
    # Extended session lifetimes for development
    "SESSION_COOKIE_AGE": 60 * 60 * 24 * 7,  # 7 days instead of 2 weeks default
    "SESSION_EXPIRE_AT_BROWSER_CLOSE": False,  # Keep sessions alive
    "SESSION_SAVE_EVERY_REQUEST": True,  # Refresh session on every request
    # Development-friendly session access
    "ALLOW_ADMIN_SESSION_ACCESS": True,  # Allow admin to view session data
    "ENABLE_SESSION_DEBUG_TOOLS": True,  # Enable debug endpoints
    "CREATE_DEFAULT_SESSIONS": True,  # Auto-create test sessions
    # Relaxed security for development
    "SESSION_COOKIE_SECURE": False,  # Allow HTTP in development
    "SESSION_COOKIE_HTTPONLY": True,  # Still prevent XSS
}

PRODUCTION_SESSION_CONFIG = {
    # Standard secure session settings
    "SESSION_COOKIE_AGE": 60 * 60 * 2,  # 2 hours
    "SESSION_EXPIRE_AT_BROWSER_CLOSE": True,  # Close with browser
    "SESSION_SAVE_EVERY_REQUEST": False,  # Standard behavior
    # Production security
    "ALLOW_ADMIN_SESSION_ACCESS": False,  # No admin session access
    "ENABLE_SESSION_DEBUG_TOOLS": False,  # No debug endpoints
    "CREATE_DEFAULT_SESSIONS": False,  # No auto-creation
    # Full security
    "SESSION_COOKIE_SECURE": True,  # HTTPS only
    "SESSION_COOKIE_HTTPONLY": True,  # Prevent XSS
    "SESSION_COOKIE_SAMESITE": "Lax",  # CSRF protection
}


def get_session_config(debug_mode: bool = False) -> Dict[str, Any]:
    """Get session configuration based on environment"""
    if debug_mode:
        return DEVELOPMENT_SESSION_CONFIG
    return PRODUCTION_SESSION_CONFIG


def configure_session_settings(django_settings_dict):
    """Apply session configuration to Django settings"""
    # Get DEBUG from the settings dict being configured, not from django.conf.settings
    debug_mode = django_settings_dict.get("DEBUG", False)
    config = get_session_config(debug_mode=debug_mode)

    # Apply session settings
    for key, value in config.items():
        if key.startswith("SESSION_"):
            django_settings_dict[key] = value


class DevelopmentSessionManager:
    """Development-friendly session management utilities"""

    @staticmethod
    def create_test_session_with_patient_data(
        patient_id: str, cda_content: str = None
    ) -> str:
        """Create a test session with patient data for development"""
        if not settings.DEBUG:
            raise ValueError("Test sessions only available in development mode")

        session = SessionStore()

        # Create comprehensive test data
        patient_data = {
            "file_path": f"test_data/patient_{patient_id}.xml",
            "country_code": "MT",
            "confidence_score": 0.95,
            "patient_data": {
                "given_name": "Test",
                "family_name": "Patient",
                "birth_date": "1980-01-01",
                "gender": "M",
            },
            "cda_content": cda_content or _get_sample_cda_content(),
            "l1_cda_content": _get_sample_l1_content(),
            "l3_cda_content": cda_content or _get_sample_l3_content(),
            "l1_cda_path": f"test_data/patient_l1_{patient_id}.xml",
            "l3_cda_path": f"test_data/patient_l3_{patient_id}.xml",
            "preferred_cda_type": "L3",
            "has_l1": True,
            "has_l3": True,
        }

        session[f"patient_match_{patient_id}"] = patient_data
        session.save()

        return session.session_key

    @staticmethod
    def get_or_create_development_session(patient_id: str) -> str:
        """Get existing session or create new one for development"""
        if not settings.DEBUG:
            return None

        # Try to find existing session
        from django.contrib.sessions.models import Session

        for session_obj in Session.objects.all():
            session_data = session_obj.get_decoded()
            if f"patient_match_{patient_id}" in session_data:
                return session_obj.session_key

        # Create new session if none found
        return DevelopmentSessionManager.create_test_session_with_patient_data(
            patient_id
        )

    @staticmethod
    def list_available_sessions() -> Dict[str, Dict]:
        """List all available sessions for development debugging"""
        if not settings.DEBUG:
            return {}

        from django.contrib.sessions.models import Session

        sessions = {}

        for session_obj in Session.objects.all():
            try:
                session_data = session_obj.get_decoded()
                patient_keys = [
                    k for k in session_data.keys() if k.startswith("patient_match_")
                ]
                if patient_keys:
                    sessions[session_obj.session_key] = {
                        "expiry": session_obj.expire_date,
                        "patients": [
                            k.replace("patient_match_", "") for k in patient_keys
                        ],
                        "patient_count": len(patient_keys),
                    }
            except:
                continue

        return sessions


class FlexibleSessionMixin:
    """Mixin for views to handle session data flexibly"""

    def get_patient_data_from_session(self, request, patient_id: str) -> Optional[Dict]:
        """Get patient data from session with fallback mechanisms"""

        # Method 1: Direct session access (current approach)
        session_key = f"patient_match_{patient_id}"
        if session_key in request.session:
            return request.session[session_key]

        # Method 2: Development fallback - find any session with this patient
        if settings.DEBUG and get_session_config().get("CREATE_DEFAULT_SESSIONS"):
            session_key = DevelopmentSessionManager.get_or_create_development_session(
                patient_id
            )
            if session_key:
                # Load the session data
                session_store = SessionStore(session_key=session_key)
                if f"patient_match_{patient_id}" in session_store:
                    return session_store[f"patient_match_{patient_id}"]

        # Method 3: Direct patient ID lookup (future: database-backed patient storage)
        # This would be where you'd query a PatientSession model or similar

        return None

    def ensure_patient_session_exists(self, request, patient_id: str) -> bool:
        """Ensure a valid session exists for the patient"""

        # Check if session already has patient data
        if self.get_patient_data_from_session(request, patient_id):
            return True

        # Development mode: auto-create missing sessions
        if settings.DEBUG and get_session_config().get("CREATE_DEFAULT_SESSIONS"):
            try:
                session_key = (
                    DevelopmentSessionManager.create_test_session_with_patient_data(
                        patient_id
                    )
                )
                # Update current request session to include this data
                session_store = SessionStore(session_key=session_key)
                for key, value in session_store.items():
                    request.session[key] = value
                request.session.save()
                return True
            except Exception as e:
                print(f"Failed to create development session: {e}")

        return False


def _get_sample_cda_content():
    """Sample CDA content for testing"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <title>Test Patient Summary</title>
    <component>
        <structuredBody>
            <component>
                <section>
                    <title>Allergies and Adverse Reactions</title>
                    <entry>
                        <observation>
                            <value displayName="Test allergy" code="123" codeSystem="2.16.840.1.113883.6.88"/>
                        </observation>
                    </entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""


def _get_sample_l1_content():
    """Sample L1 CDA content"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <title>Original Clinical Document</title>
</ClinicalDocument>"""


def _get_sample_l3_content():
    """Sample L3 CDA content"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <title>European Patient Summary</title>
    <component>
        <structuredBody>
            <component>
                <section>
                    <title>Medications</title>
                    <entry>
                        <substanceAdministration>
                            <consumable>
                                <manufacturedProduct>
                                    <manufacturedMaterial>
                                        <name displayName="Test Medication 10mg"/>
                                    </manufacturedMaterial>
                                </manufacturedProduct>
                            </consumable>
                        </substanceAdministration>
                    </entry>
                </section>
            </component>
            <component>
                <section>
                    <title>Allergies and Adverse Reactions</title>
                    <entry>
                        <observation>
                            <value displayName="Test allergy to penicillin" code="7980" codeSystem="2.16.840.1.113883.6.88"/>
                        </observation>
                    </entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""
