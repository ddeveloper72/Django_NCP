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
import json


def home_view(request):
    """Home page with SMP source configuration"""
    from smp_client.models import SMPConfiguration

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

    context = {
        "current_smp_name": current_smp_name,
        "current_smp_ui_url": current_smp_ui_url,
        "current_smp_api_url": current_smp_api_url,
    }
    return render(request, "home.html", context, using="jinja2")


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


def custom_admin_logout_view(request):
    """Custom admin logout view that redirects to home page"""
    logout(request)
    return redirect("/")  # Redirect to home page instead of admin logout page


urlpatterns = [
    path("", home_view, name="home"),
    path("api/update-smp-source/", update_smp_source, name="update_smp_source"),
    # Custom admin logout that redirects to home
    path("admin/logout/", custom_admin_logout_view, name="admin_logout"),
    path("admin/", admin.site.urls),
    # Authentication URLs
    path("accounts/", include("django.contrib.auth.urls")),
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
