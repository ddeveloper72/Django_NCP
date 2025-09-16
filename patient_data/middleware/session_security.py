"""
Industry Standard Session Management Middleware
EU NCP Portal - Healthcare Session Security

Provides automatic session management, security enforcement, and audit logging
for patient data access sessions with healthcare-specific security requirements.
"""

import logging
import hashlib
import time
from typing import Optional, Dict, Any
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.urls import reverse
from datetime import timedelta

from patient_data.models import PatientSession, SessionAuditLog

logger = logging.getLogger(__name__)


class PatientSessionMiddleware(MiddlewareMixin):
    """
    Middleware for secure patient session management.

    Handles:
    - Session validation and expiration
    - Security checks and rate limiting
    - Audit logging
    - Automatic session rotation
    - PHI access protection
    """

    # Paths that require patient session
    PROTECTED_PATHS = [
        "/patients/cda/",
        "/patients/details/",
        "/patient_data/",
    ]

    # Paths that should be excluded from session management
    EXCLUDED_PATHS = [
        "/admin/",
        "/static/",
        "/media/",
        "/login/",
        "/logout/",
        "/api/health/",
    ]

    # Maximum requests per session per minute
    RATE_LIMIT_REQUESTS = 60
    RATE_LIMIT_WINDOW = 60  # seconds

    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Process incoming request for session management."""

        # Skip middleware for excluded paths
        if self._is_excluded_path(request.path):
            return None

        # Skip for anonymous users on non-protected paths
        if isinstance(request.user, AnonymousUser) and not self._is_protected_path(
            request.path
        ):
            return None

        # Process patient session if on protected path
        if self._is_protected_path(request.path):
            return self._handle_patient_session(request)

        return None

    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        """Process response to update session data."""

        # Update session access time and audit log
        patient_session = getattr(request, "patient_session", None)
        if patient_session:
            self._update_session_access(request, patient_session, response)

        return response

    def _is_protected_path(self, path: str) -> bool:
        """Check if path requires patient session protection."""
        return any(path.startswith(protected) for protected in self.PROTECTED_PATHS)

    def _is_excluded_path(self, path: str) -> bool:
        """Check if path should be excluded from session management."""
        return any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS)

    def _handle_patient_session(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Handle patient session validation and management."""

        # Extract session ID from URL or headers
        session_id = self._extract_session_id(request)
        if not session_id:
            logger.warning(f"No session ID found in request to {request.path}")
            return self._handle_missing_session(request)

        # Get and validate patient session
        patient_session = PatientSession.objects.get_active_session(session_id)
        if not patient_session:
            logger.warning(
                f"Invalid or expired session {session_id} for path {request.path}"
            )
            return self._handle_invalid_session(request, session_id)

        # Validate session ownership
        if patient_session.user != request.user:
            logger.error(f"Session {session_id} does not belong to user {request.user}")
            SessionAuditLog.log_action(
                session=patient_session,
                action="unauthorized_access_attempt",
                success=False,
                error_message=f"User {request.user} attempted to access session owned by {patient_session.user}",
                client_ip=self._get_client_ip(request),
                resource=request.path,
            )
            raise PermissionDenied("Session access denied")

        # Check rate limiting
        if self._is_rate_limited(patient_session, request):
            logger.warning(f"Rate limit exceeded for session {session_id}")
            return JsonResponse(
                {"error": "Rate limit exceeded", "retry_after": 60}, status=429
            )

        # Check if session needs rotation
        if patient_session.requires_rotation:
            new_token = patient_session.rotate_session()
            logger.info(f"Session {session_id} rotated, new token: {new_token}")

        # Attach session to request
        request.patient_session = patient_session

        # Record session access
        patient_session.record_access(
            action=f"{request.method} {request.path}",
            client_ip=self._get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        # Log access for audit
        SessionAuditLog.log_action(
            session=patient_session,
            action="session_access",
            resource=request.path,
            client_ip=self._get_client_ip(request),
            method=request.method,
            user_agent_hash=hashlib.sha256(
                request.META.get("HTTP_USER_AGENT", "").encode()
            ).hexdigest(),
        )

        return None

    def _extract_session_id(self, request: HttpRequest) -> Optional[str]:
        """Extract session ID from URL path or headers."""

        # Try to extract from URL path (e.g., /patients/cda/session_id/L3/)
        path_parts = request.path.strip("/").split("/")
        for i, part in enumerate(path_parts):
            if part == "cda" and i + 1 < len(path_parts):
                return path_parts[i + 1]
            elif part == "details" and i + 1 < len(path_parts):
                return path_parts[i + 1]

        # Try to extract from headers
        return request.META.get("HTTP_X_PATIENT_SESSION_ID")

    def _handle_missing_session(self, request: HttpRequest) -> HttpResponse:
        """Handle requests without valid session ID."""

        # Log missing session attempt
        logger.warning(f"Missing session ID for protected path: {request.path}")

        # Redirect to patient search if possible
        if "patients" in request.path:
            return redirect(reverse("patient_data:patient_search"))

        # Return JSON error for API requests
        if request.content_type == "application/json" or "api" in request.path:
            return JsonResponse(
                {
                    "error": "Session required",
                    "redirect_url": reverse("patient_data:patient_search"),
                },
                status=401,
            )

        # Redirect to login for other requests
        return redirect(reverse("login"))

    def _handle_invalid_session(
        self, request: HttpRequest, session_id: str
    ) -> HttpResponse:
        """Handle requests with invalid or expired session."""

        # Log invalid session attempt
        logger.warning(f"Invalid session {session_id} for path {request.path}")

        # Clean up expired session if it exists
        try:
            expired_session = PatientSession.objects.get(session_id=session_id)
            if expired_session.is_expired():
                expired_session.mark_expired()
                SessionAuditLog.log_action(
                    session=expired_session,
                    action="session_expired",
                    resource=request.path,
                    client_ip=self._get_client_ip(request),
                )
        except PatientSession.DoesNotExist:
            pass

        # Return appropriate response
        if request.content_type == "application/json" or "api" in request.path:
            return JsonResponse(
                {
                    "error": "Session expired or invalid",
                    "redirect_url": reverse("patient_data:patient_search"),
                },
                status=401,
            )

        return redirect(reverse("patient_data:patient_search"))

    def _is_rate_limited(self, session: PatientSession, request: HttpRequest) -> bool:
        """Check if session has exceeded rate limits."""

        # Simple rate limiting based on access count and time
        time_window = timezone.now() - timedelta(seconds=self.RATE_LIMIT_WINDOW)

        # Count recent audit logs for this session
        recent_accesses = SessionAuditLog.objects.filter(
            session=session, timestamp__gte=time_window, action="session_access"
        ).count()

        return recent_accesses >= self.RATE_LIMIT_REQUESTS

    def _update_session_access(
        self, request: HttpRequest, session: PatientSession, response: HttpResponse
    ) -> None:
        """Update session with response information."""

        # Record response status in metadata if it's an error
        if response.status_code >= 400:
            SessionAuditLog.log_action(
                session=session,
                action="request_error",
                success=False,
                resource=request.path,
                error_message=f"HTTP {response.status_code}",
                response_status=response.status_code,
                client_ip=self._get_client_ip(request),
            )

        # Check if session should be rotated based on security flags
        if self._should_rotate_session(session, request, response):
            session.requires_rotation = True
            session.save()  # Save without update_fields to avoid database constraint issues

    def _should_rotate_session(
        self, session: PatientSession, request: HttpRequest, response: HttpResponse
    ) -> bool:
        """Determine if session should be rotated for security."""

        # Rotate on first access after creation
        if session.access_count == 1:
            return True

        # Rotate if client IP has changed
        current_ip = self._get_client_ip(request)
        if session.client_ip and session.client_ip != current_ip:
            logger.info(
                f"IP address changed for session {session.session_id}: {session.client_ip} -> {current_ip}"
            )
            return True

        # Rotate after certain number of accesses
        rotation_threshold = getattr(
            settings, "PATIENT_SESSION_ROTATION_THRESHOLD", 100
        )
        if session.access_count % rotation_threshold == 0:
            return True

        return False

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address from request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "")
        return ip


class SessionSecurityMiddleware(MiddlewareMixin):
    """
    Additional security middleware for patient sessions.

    Provides:
    - Content Security Policy headers
    - XSS protection
    - Clickjacking protection for patient data
    - Security headers for PHI protection
    """

    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        """Add security headers to response."""

        # Only add headers for patient data requests
        if not hasattr(request, "patient_session"):
            return response

        # Strict CSP for patient data pages - Updated for Bootstrap CDN
        response["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "img-src 'self' data:; "
            "connect-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "frame-ancestors 'none';"
        )

        # Prevent XSS attacks
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["X-XSS-Protection"] = "1; mode=block"

        # Prevent caching of sensitive data
        response["Cache-Control"] = "no-cache, no-store, must-revalidate, private"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"

        # Add custom headers for patient data
        response["X-Patient-Data-Protection"] = "active"
        response["X-Session-Secured"] = "true"

        return response


class SessionCleanupMiddleware(MiddlewareMixin):
    """
    Middleware for automatic session cleanup.

    Periodically cleans up expired sessions and cached data.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.last_cleanup = 0
        super().__init__(get_response)

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Perform periodic cleanup of expired sessions."""

        # Only run cleanup every 5 minutes
        cleanup_interval = getattr(
            settings, "SESSION_CLEANUP_INTERVAL", 300
        )  # 5 minutes
        current_time = time.time()

        if current_time - self.last_cleanup > cleanup_interval:
            self._cleanup_expired_sessions()
            self.last_cleanup = current_time

        return None

    def _cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions and cached data."""
        try:
            # Clean up expired sessions
            expired_count = PatientSession.objects.cleanup_expired_sessions()
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired patient sessions")

            # Clean up expired cache entries
            from patient_data.models import PatientDataCache

            expired_cache = PatientDataCache.objects.filter(
                expires_at__lt=timezone.now()
            )
            cache_count = expired_cache.count()
            if cache_count > 0:
                expired_cache.delete()
                logger.info(f"Cleaned up {cache_count} expired cache entries")

        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")


class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Middleware for comprehensive audit logging of patient data access.

    Logs all access to patient data for compliance and security monitoring.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Log request start time for performance monitoring."""
        request._audit_start_time = time.time()
        return None

    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        """Log detailed audit information."""

        # Only log for patient data requests
        if not hasattr(request, "patient_session"):
            return response

        session = request.patient_session
        duration = time.time() - getattr(request, "_audit_start_time", time.time())

        # Create detailed audit log
        SessionAuditLog.log_action(
            session=session,
            action="request_completed",
            resource=request.path,
            client_ip=self._get_client_ip(request),
            method=request.method,
            response_status=response.status_code,  # Fixed: Changed from status_code to response_status
            duration_ms=int(duration * 1000),
            user_agent_hash=hashlib.sha256(
                request.META.get("HTTP_USER_AGENT", "").encode()
            ).hexdigest(),
            content_length=len(response.content) if hasattr(response, "content") else 0,
        )

        return response

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address from request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "")
        return ip
