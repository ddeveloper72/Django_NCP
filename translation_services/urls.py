"""
Translation Services URL Configuration

REST API endpoints for medical terminology translation services.
"""

from django.urls import path
from . import views

app_name = "translation_services"

urlpatterns = [
    # Core translation endpoints
    path("concept/", views.TranslateConceptView.as_view(), name="translate_concept"),
    path("fhir/", views.TranslateFHIRView.as_view(), name="translate_fhir"),
    path("cda/", views.TranslateCDAView.as_view(), name="translate_cda"),
    # Information endpoints
    path(
        "terminology-systems/",
        views.terminology_systems_view,
        name="terminology_systems",
    ),
    path("languages/", views.supported_languages_view, name="supported_languages"),
    path("status/", views.translation_status_view, name="translation_status"),
]
