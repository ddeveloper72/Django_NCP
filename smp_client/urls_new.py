"""
SMP Client URL Configuration
URL patterns for SMP service metadata management
"""

from django.urls import path
from . import views

app_name = "smp_client"

urlpatterns = [
    # SMP Management Interface
    path("", views.smp_dashboard, name="dashboard"),
    path("participants/", views.participant_search, name="participant_search"),
    path(
        "participants/<uuid:participant_id>/",
        views.participant_detail,
        name="participant_detail",
    ),
    path("sync/european/", views.european_smp_sync, name="european_smp_sync"),
    # SMP API Endpoints (OASIS BDXR SMP v1.0 compatible)
    path(
        "api/participants/", views.smp_participants_list, name="api_participants_list"
    ),
    path(
        "<str:participant_scheme>::<str:participant_id>/",
        views.smp_service_group,
        name="smp_service_group",
    ),
    path(
        "<str:participant_scheme>::<str:participant_id>/services/<str:document_type_id>/",
        views.smp_service_metadata,
        name="smp_service_metadata",
    ),
]
