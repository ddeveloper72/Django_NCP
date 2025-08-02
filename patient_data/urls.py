"""
Patient Data URL Configuration

URL patterns for patient search, data retrieval, and document request functionality.
"""

from django.urls import path
from . import views
from .views import enhanced_cda_translation_views

app_name = "patient_data"

urlpatterns = [
    # Patient data form and search
    path("", views.patient_data_view, name="patient_data_form"),
    path(
        "details/<int:patient_id>/", views.patient_details_view, name="patient_details"
    ),
    path("cda/<int:patient_id>/", views.patient_cda_view, name="patient_cda_view"),
    path("download/<int:patient_id>/", views.download_cda_pdf, name="download_cda_pdf"),
    
    # Enhanced CDA Translation Views
    path(
        "cda/translated/<int:patient_id>/", 
        enhanced_cda_translation_views.patient_cda_translated_view, 
        name="patient_cda_translated_view"
    ),
    path(
        "cda/translate-section/", 
        enhanced_cda_translation_views.translate_cda_section_ajax, 
        name="translate_cda_section_ajax"
    ),
    path(
        "cda/download-translated/<int:patient_id>/", 
        enhanced_cda_translation_views.download_translated_cda, 
        name="download_translated_cda"
    ),
    path(
        "translation/api-status/", 
        enhanced_cda_translation_views.translation_api_status, 
        name="translation_api_status"
    ),
    path(
        "translation/batch/", 
        enhanced_cda_translation_views.batch_translate_documents, 
        name="batch_translate_documents"
    ),
    
    # Legacy search interface (can be removed if not needed)
    path("search/", views.patient_search_view, name="patient_search"),
    path(
        "search/results/",
        views.patient_search_results,
        name="patient_search_results",
    ),
    # Patient data display (if function exists)
    # path("patient/<str:patient_id>/", views.patient_data_view, name="patient_data"),
    # Demo and testing (comment out until views exist)
    # path("demo/", demo_views.patient_demo_view, name="patient_demo"),
    # path("demo/sample-data/", demo_views.sample_data_view, name="sample_data"),
]
