"""
URL configuration for eu_ncp_server project.

EU eHealth NCP Server - Django implementation
Provides both API endpoints for Java portal integration and Django frontend
"""

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json


def home_view(request):
    """Home page with SMP source configuration"""
    from ehealth_portal.models import SMPSourceConfiguration

    # Get current SMP configuration
    smp_config = SMPSourceConfiguration.get_current_config()

    context = {
        "smp_config": smp_config,
        "smp_choices": SMPSourceConfiguration.SMP_SOURCE_CHOICES,
        "current_smp_name": smp_config.get_active_smp_name(),
        "current_smp_ui_url": smp_config.get_active_smp_ui_url(),
        "current_smp_api_url": smp_config.get_active_smp_api_url(),
    }
    return render(request, "home.html", context)


@csrf_exempt
@require_http_methods(["POST"])
def update_smp_source(request):
    """API endpoint to update SMP source configuration"""
    from ehealth_portal.models import SMPSourceConfiguration

    try:
        data = json.loads(request.body)
        source_type = data.get("source_type")

        if source_type not in ["european", "localhost"]:
            return JsonResponse({"success": False, "error": "Invalid source type"})

        # Update the default configuration
        smp_config = SMPSourceConfiguration.get_default_config()
        smp_config.source_type = source_type
        smp_config.save()

        return JsonResponse(
            {
                "success": True,
                "message": f"SMP source updated to {smp_config.get_source_type_display()}",
                "active_url": smp_config.get_active_smp_url(),
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


urlpatterns = [
    path("", home_view, name="home"),
    path("api/update-smp-source/", update_smp_source, name="update_smp_source"),
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
]

# Serve media files during development
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
