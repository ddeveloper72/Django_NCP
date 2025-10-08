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
    # SMP Editor Interface
    path("editor/", views.smp_editor, name="smp_editor"),
    path("documents/generate/", views.generate_document, name="generate_document"),
    path("documents/", views.list_smp_documents, name="list_documents"),
    path(
        "documents/<uuid:document_id>/download/",
        views.download_document,
        name="download_document",
    ),
    path(
        "documents/<uuid:document_id>/sign/", views.sign_document, name="sign_document"
    ),
    path(
        "documents/<uuid:document_id>/upload-signed/",
        views.upload_signed_document,
        name="upload_signed_document",
    ),
    path(
        "documents/<uuid:document_id>/upload/",
        views.upload_to_smp_server,
        name="upload_to_smp_server",
    ),
    path("sync/", views.synchronize_from_smp, name="synchronize_from_smp"),
    
    # SMP Monitoring and Administration
    path("logs/", views.system_logs, name="system_logs"),
    path("performance/", views.performance_metrics, name="performance_metrics"),
    path("audit/", views.audit_trail, name="audit_trail"),
    
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
