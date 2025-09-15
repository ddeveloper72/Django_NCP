"""
Patient Session Security Middleware

This middleware ensures that patient data is properly secured and cleaned up:
1. Removes patient data from expired sessions
2. Removes patient data when users log out
3. Adds security headers for patient data access
4. Tracks patient session activity and enforces timeouts
5. Provides automatic cleanup based on various triggers
"""

import logging
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import logout
from django.utils import timezone
from django.shortcuts import redirect
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class PatientSessionSecurityMiddleware:
    """Middleware to enforce patient session security policies"""

    def __init__(self, get_response):
        self.get_response = get_response
        # Patient session timeout (in minutes)
        self.patient_session_timeout = getattr(settings, "PATIENT_SESSION_TIMEOUT", 30)
        # Maximum inactive time before forced cleanup (in minutes)
        self.max_inactive_time = getattr(settings, "PATIENT_MAX_INACTIVE_TIME", 60)

    def __call__(self, request):
        # Check session security before processing request
        cleanup_result = self.enforce_patient_session_security(request)

        # If we performed cleanup due to timeout, log it
        if cleanup_result.get("cleaned_due_to_timeout"):
            logger.warning(
                f"Patient session timeout cleanup: {cleanup_result.get('cleaned_keys', 0)} items removed "
                f"from session {request.session.session_key[:20] if hasattr(request, 'session') else 'unknown'}"
            )

        response = self.get_response(request)

        # Add security headers for patient data pages
        if self.is_patient_data_request(request):
            response["X-Content-Type-Options"] = "nosniff"
            response["X-Frame-Options"] = "DENY"
            response["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"
            response["X-Patient-Data-Page"] = "true"

        # Update patient session activity tracking
        if self.has_patient_data(request) and self.is_patient_data_request(request):
            request.session["patient_last_activity"] = timezone.now().isoformat()
            request.session.save()

        return response

    def enforce_patient_session_security(self, request):
        """Enforce security policies for patient session data"""
        if not hasattr(request, "session"):
            return {"action": "no_session"}

        # Get patient-related session keys
        patient_keys = [
            key for key in request.session.keys() if "patient" in key.lower()
        ]

        if not patient_keys:
            return {"action": "no_patient_data"}

        # Check for timeout conditions
        cleanup_reasons = []
        should_cleanup = False

        # Check if user is no longer authenticated but has patient data
        if patient_keys and not (
            hasattr(request, "user") and request.user.is_authenticated
        ):
            cleanup_reasons.append("unauthenticated_with_patient_data")
            should_cleanup = True

        # Check for session timeout based on last activity
        if "patient_last_activity" in request.session:
            try:
                last_activity = timezone.datetime.fromisoformat(
                    request.session["patient_last_activity"]
                )
                if timezone.is_naive(last_activity):
                    last_activity = timezone.make_aware(last_activity)

                inactive_time = timezone.now() - last_activity

                if inactive_time > timedelta(minutes=self.patient_session_timeout):
                    cleanup_reasons.append("patient_session_timeout")
                    should_cleanup = True
                elif inactive_time > timedelta(minutes=self.max_inactive_time):
                    cleanup_reasons.append("max_inactive_time_exceeded")
                    should_cleanup = True

            except (ValueError, TypeError) as e:
                logger.error(f"Error parsing patient_last_activity: {e}")
                cleanup_reasons.append("invalid_activity_timestamp")
                should_cleanup = True

        # Perform cleanup if needed
        if should_cleanup:
            cleaned_keys = self.clear_patient_session_data(request)
            logger.info(
                f"Patient session security cleanup triggered by: {', '.join(cleanup_reasons)}. "
                f"Cleared {cleaned_keys} patient data items."
            )
            return {
                "action": "cleanup_performed",
                "reasons": cleanup_reasons,
                "cleaned_keys": cleaned_keys,
                "cleaned_due_to_timeout": "timeout" in " ".join(cleanup_reasons),
            }

        return {"action": "no_cleanup_needed"}

    def has_patient_data(self, request):
        """Check if the session contains any patient data"""
        if not hasattr(request, "session"):
            return False

        patient_keys = [
            key for key in request.session.keys() if "patient" in key.lower()
        ]
        return len(patient_keys) > 0

    def clear_patient_session_data(self, request):
        """Clear all patient-related data from the session for security"""
        if not hasattr(request, "session"):
            return 0

        # Get all session keys that contain patient data
        patient_keys = [
            key for key in request.session.keys() if "patient" in key.lower()
        ]

        # Remove all patient-related session data
        for key in patient_keys:
            if key in request.session:
                del request.session[key]
                logger.debug(f"Removed patient session key: {key}")

        # Also clear patient activity tracking
        if "patient_last_activity" in request.session:
            del request.session["patient_last_activity"]

        # Force session save
        if hasattr(request.session, "save"):
            request.session.save()

        return len(patient_keys)

    def is_patient_data_request(self, request):
        """Check if the request is for patient data pages"""
        path = request.path.lower()
        return any(
            pattern in path
            for pattern in [
                "/patients/",
                "/cda/",
                "/patient_data/",
                "/clinical/",
                "/health",
            ]
        )


class PatientSessionCleanupMiddleware:
    """Middleware to clean up patient sessions on logout"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store initial authentication state
        was_authenticated = (
            request.user.is_authenticated if hasattr(request, "user") else False
        )

        response = self.get_response(request)

        # Check if user logged out during this request
        is_authenticated = (
            request.user.is_authenticated if hasattr(request, "user") else False
        )

        if was_authenticated and not is_authenticated:
            # User logged out - clear patient data
            self.clear_patient_session_data(request)
            logger.info("Patient session data cleared on logout")

        return response

    def clear_patient_session_data(self, request):
        """Clear all patient-related data from the session"""
        if not hasattr(request, "session"):
            return 0

        patient_keys = [
            key for key in request.session.keys() if "patient" in key.lower()
        ]

        for key in patient_keys:
            if key in request.session:
                del request.session[key]

        # Also clear patient activity tracking
        if "patient_last_activity" in request.session:
            del request.session["patient_last_activity"]

        # Force session save
        if hasattr(request.session, "save"):
            request.session.save()

        return len(patient_keys)
