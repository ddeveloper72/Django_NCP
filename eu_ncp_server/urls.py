"""
URL configuration for eu_ncp_server project.

EU eHealth NCP Server - Django implementation
Provides both API endpoints for Java portal integration and Django frontend
"""

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import logout
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json


def home_view(request):
    """Home page with SMP source configuration and system status"""
    from smp_client.models import SMPConfiguration
    from .services import SystemStatusService

    # Get current SMP configuration
    try:
        smp_config = SMPConfiguration.objects.first()
        if smp_config:
            current_smp_name = "European SMP (Test Environment)"
            current_smp_ui_url = smp_config.european_smp_url
            current_smp_api_url = smp_config.european_smp_url
        else:
            current_smp_name = "No SMP configured"
            current_smp_ui_url = "#"
            current_smp_api_url = "#"
    except Exception as e:
        current_smp_name = "SMP configuration loading..."
        current_smp_ui_url = "#"
        current_smp_api_url = "#"

    # Get system status
    system_status = SystemStatusService.get_system_status()

    context = {
        "current_smp_name": current_smp_name,
        "current_smp_ui_url": current_smp_ui_url,
        "current_smp_api_url": current_smp_api_url,
        "system_status": system_status,
    }
    return render(request, "home.html", context)


@csrf_exempt
@require_http_methods(["POST"])
def update_smp_source(request):
    """API endpoint to update SMP source configuration"""
    from smp_client.models import SMPConfiguration

    try:
        data = json.loads(request.body)
        source_type = data.get("source_type")

        if source_type not in ["european", "localhost"]:
            return JsonResponse({"success": False, "error": "Invalid source type"})

        # Get or create default configuration
        smp_config, created = SMPConfiguration.objects.get_or_create(
            id=1,
            defaults={
                "european_smp_url": "https://smp-ehealth-trn.acc.edelivery.tech.ec.europa.eu",
                "sync_enabled": True,
                "local_smp_enabled": source_type == "localhost",
            },
        )

        # Update based on source type
        if source_type == "localhost":
            smp_config.local_smp_enabled = True
            active_url = "http://localhost:8290/smp"
            message = "SMP source updated to localhost"
        else:
            smp_config.local_smp_enabled = False
            active_url = smp_config.european_smp_url
            message = "SMP source updated to European SMP"

        smp_config.save()

        return JsonResponse(
            {
                "success": True,
                "message": message,
                "active_url": active_url,
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def clear_patient_session_data(request):
    """Clear all patient-related data from the session for security"""
    if hasattr(request, "session"):
        # Get all session keys that contain patient data
        patient_keys = [
            key for key in request.session.keys() if "patient" in key.lower()
        ]

        # Remove all patient-related session data
        for key in patient_keys:
            if key in request.session:
                del request.session[key]

        # Also clear any extended data
        if "patient_extended_data" in request.session:
            del request.session["patient_extended_data"]

        # Force session save
        request.session.save()

        return len(patient_keys)  # Return number of keys cleared
    return 0


def custom_admin_logout_view(request):
    """Custom admin logout view that redirects to home page"""
    # Clear patient data before logout
    cleared_keys = clear_patient_session_data(request)

    logout(request)

    # Add security message if patient data was cleared
    if cleared_keys > 0:
        from django.contrib import messages

        messages.info(
            request,
            f"Patient session data cleared for security ({cleared_keys} items).",
        )

    return redirect("/")  # Redirect to home page instead of admin logout page


def custom_logout_view(request):
    """Custom logout view for regular users"""
    # Clear patient data before logout
    cleared_keys = clear_patient_session_data(request)

    logout(request)

    # Add a success message
    from django.contrib import messages

    messages.success(request, "You have been successfully logged out.")

    if cleared_keys > 0:
        messages.info(
            request,
            f"Patient session data cleared for security ({cleared_keys} items).",
        )

    return redirect("/")  # Redirect to home page


@csrf_exempt
@require_POST
def clear_patient_session_api(request):
    """API endpoint to manually clear patient session data"""
    try:
        # Clear patient session data
        cleared_keys = clear_patient_session_data(request)

        # Log the cleanup action
        if hasattr(request, "user") and request.user.is_authenticated:
            user_info = f"user {request.user.username}"
        else:
            user_info = "anonymous user"

        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            f"Manual patient session cleanup requested by {user_info}: {cleared_keys} items cleared"
        )

        return JsonResponse(
            {
                "success": True,
                "message": f"Patient session data cleared successfully ({cleared_keys} items)",
                "cleared_keys": cleared_keys,
            }
        )

    except Exception as e:
        return JsonResponse(
            {
                "success": False,
                "error": f"Failed to clear patient session data: {str(e)}",
            },
            status=500,
        )


@csrf_exempt
@require_POST
def emergency_session_cleanup(request):
    """Emergency API endpoint to clear ALL session data (not just patient data)"""
    try:
        if not hasattr(request, "session"):
            return JsonResponse(
                {"success": False, "error": "No session available"}, status=400
            )

        # Store session key for logging
        session_key = request.session.session_key

        # Clear all session data
        request.session.flush()

        # Log the emergency cleanup
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Emergency session cleanup performed on session {session_key}")

        return JsonResponse(
            {"success": True, "message": "All session data cleared (emergency cleanup)"}
        )

    except Exception as e:
        return JsonResponse(
            {"success": False, "error": f"Emergency cleanup failed: {str(e)}"},
            status=500,
        )


urlpatterns = [
    path("", home_view, name="home"),
    path("api/update-smp-source/", update_smp_source, name="update_smp_source"),
    # Patient session cleanup API endpoints
    path(
        "api/clear-patient-session/",
        clear_patient_session_api,
        name="clear_patient_session_api",
    ),
    path(
        "api/emergency-session-cleanup/",
        emergency_session_cleanup,
        name="emergency_session_cleanup",
    ),
    # Custom admin logout that redirects to home
    path("admin/logout/", custom_admin_logout_view, name="admin_logout"),
    path("admin/", admin.site.urls),
    # Custom logout view for regular users
    path("accounts/logout/", custom_logout_view, name="logout"),
    # Custom authentication URLs with HSE theming
    path("accounts/", include("authentication.urls")),
    # Redirects for old auth URLs to new accounts URLs
    path("auth/login/", RedirectView.as_view(url="/accounts/login/", permanent=True)),
    path(
        "auth/register/",
        RedirectView.as_view(url="/accounts/register/", permanent=True),
    ),
    path("auth/", RedirectView.as_view(url="/accounts/login/", permanent=True)),
    # Option 1: API endpoints for Java portal integration
    path("api/", include("ncp_gateway.urls")),
    # Option 2: Django frontend portal (replicating Java portal)
    path("portal/", include("ehealth_portal.urls")),
    # FHIR services
    path("fhir/", include("fhir_services.urls")),
    # SMP client integration
    path("smp/", include("smp_client.urls")),
    # Patient data management
    path("patients/", include("patient_data.urls")),
    # Translation services API (temporarily disabled due to import errors)
    # path("api/translation/", include("translation_services.urls")),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
