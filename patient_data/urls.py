"""
Patient Data URL Configuration

URL patterns for patient search, data retrieval, and document request functionality.
"""

from django.urls import path
from . import views, demo_views

app_name = "patient_data"

urlpatterns = [
    # Patient search interface
    path("search/", views.patient_search_view, name="patient_search"),
    path(
        "search/results/",
        views.patient_search_results_view,
        name="patient_search_results",
    ),
    # Patient data display
    path("patient/<str:patient_id>/", views.patient_data_view, name="patient_data"),
    path(
        "patient/<str:patient_id>/documents/",
        views.patient_documents_view,
        name="patient_documents",
    ),
    # Document requests
    path(
        "request/",
        views.request_clinical_documents_view,
        name="request_clinical_documents",
    ),
    path(
        "request/submit/",
        views.submit_document_request_view,
        name="submit_document_request",
    ),
    # Demo and testing
    path("demo/", demo_views.patient_demo_view, name="patient_demo"),
    path("demo/sample-data/", demo_views.sample_data_view, name="sample_data"),
    # API endpoints for AJAX calls
    path(
        "api/search/", views.PatientSearchAPIView.as_view(), name="api_patient_search"
    ),
    path(
        "api/patient/<str:patient_id>/",
        views.PatientDataAPIView.as_view(),
        name="api_patient_data",
    ),
    path(
        "api/documents/request/",
        views.DocumentRequestAPIView.as_view(),
        name="api_document_request",
    ),
]
