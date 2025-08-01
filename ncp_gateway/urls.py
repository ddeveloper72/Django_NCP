# API URLs for Java Portal Integration
from django.urls import path
from . import api_views

urlpatterns = [
    # API endpoints for Java OpenNCP Portal integration
    path("countries/", api_views.get_available_countries, name="api_countries"),
    path("patient/lookup/", api_views.patient_lookup, name="api_patient_lookup"),
    path(
        "patient/<str:patient_id>/document/<str:document_type>/",
        api_views.get_patient_document,
        name="api_patient_document",
    ),
]
