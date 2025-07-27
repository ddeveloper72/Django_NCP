from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from .models import SMPSourceConfiguration


@staff_member_required
def smp_config_admin(request):
    """Simple admin view for SMP configuration"""
    config = SMPSourceConfiguration.get_current_config()

    if request.method == "POST":
        source_type = request.POST.get("source_type")
        if source_type in ["european", "localhost"]:
            config.source_type = source_type
            config.save()
            messages.success(
                request, f"SMP source updated to {config.get_active_smp_name()}"
            )
            return redirect("smp_config_admin")
        else:
            messages.error(request, "Invalid source type selected")

    context = {
        "config": config,
        "choices": SMPSourceConfiguration.SMP_SOURCE_CHOICES,
        "current_api_url": config.get_active_smp_api_url(),
        "current_ui_url": config.get_active_smp_ui_url(),
    }

    return render(request, "admin/smp_config.html", context)
