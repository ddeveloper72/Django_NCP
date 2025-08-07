"""
Patient Data URL Configuration

URL patterns for patient search, data retrieval, and document request functionality.
"""

from django.urls import path
from patient_data import views as main_views
from .cda_test_views import test_patients_view, refresh_cda_index_view
from .debug_views import debug_cda_index
from .view_modules.enhanced_cda_view import (
    EnhancedCDADocumentView,
    toggle_translation_view,
    get_section_translation,
    export_translated_cda,
)
from .enhanced_cda_display import EnhancedCDADisplayView
from .view_modules.cda_views import (
    cda_translation_display,
    cda_translation_api,
    available_cda_files,
    patient_search_with_cda,
)
from .view_modules import enhanced_cda_translation_views

app_name = "patient_data"

urlpatterns = [
    # Debug views
    path("debug/cda-index/", debug_cda_index, name="debug_cda_index"),
    # Test CDA Documents Management
    path("test-patients/", test_patients_view, name="test_patients"),
    path("refresh-cda-index/", refresh_cda_index_view, name="refresh_cda_index"),
    # Patient data form and search
    path("", main_views.patient_data_view, name="patient_data_form"),
    path(
        "details/<int:patient_id>/",
        main_views.patient_details_view,
        name="patient_details",
    ),
    path("cda/<int:patient_id>/", main_views.patient_cda_view, name="patient_cda_view"),
    path(
        "cda/translation-toggle/<int:patient_id>/",
        main_views.cda_translation_toggle,
        name="cda_translation_toggle",
    ),
    path(
        "download/<int:patient_id>/",
        main_views.download_cda_pdf,
        name="download_cda_pdf",
    ),
    # New CDA/ORCD views based on requirements
    path(
        "download/html/<int:patient_id>/",
        main_views.download_cda_html,
        name="download_cda_html",
    ),
    path(
        "download/patient-summary-pdf/<int:patient_id>/",
        main_views.download_patient_summary_pdf,
        name="download_patient_summary_pdf",
    ),
    path(
        "orcd/<int:patient_id>/",
        main_views.patient_orcd_view,
        name="patient_orcd_view",
    ),
    path(
        "orcd/<int:patient_id>/download/",
        main_views.download_orcd_pdf,
        name="download_orcd_pdf",
    ),
    path(
        "orcd/<int:patient_id>/view/",
        main_views.view_orcd_pdf,
        name="view_orcd_pdf",
    ),
    path(
        "orcd/<int:patient_id>/debug/",
        main_views.debug_orcd_pdf,
        name="debug_orcd_pdf",
    ),
    path(
        "orcd/<int:patient_id>/base64/",
        main_views.orcd_pdf_base64,
        name="orcd_pdf_base64",
    ),
    path(
        "orcd/<int:patient_id>/download/<int:attachment_index>/",
        main_views.download_orcd_pdf,
        name="download_orcd_pdf_indexed",
    ),
    # Enhanced CDA Display with Multi-European Language Support
    path(
        "enhanced_cda_display/",
        main_views.enhanced_cda_display,
        name="enhanced_cda_display",
    ),
    # Enhanced CDA Display with Patient ID (using our working view)
    path(
        "cda/enhanced_display/<int:patient_id>/",
        EnhancedCDADisplayView.as_view(),
        name="enhanced_cda_display_with_id",
    ),
    # Enhanced CDA Translation Views
    path(
        "cda/enhanced/<int:patient_id>/",
        EnhancedCDADocumentView.as_view(),
        name="enhanced_cda_view",
    ),
    path(
        "cda/translate-toggle/<int:patient_id>/",
        toggle_translation_view,
        name="toggle_translation_view",
    ),
    path(
        "cda/section/<int:patient_id>/<str:section_id>/",
        get_section_translation,
        name="get_section_translation",
    ),
    path(
        "cda/export/<int:patient_id>/",
        export_translated_cda,
        name="export_translated_cda",
    ),
    path(
        "cda/translated/<int:patient_id>/",
        enhanced_cda_translation_views.patient_cda_translated_view,
        name="patient_cda_translated_view",
    ),
    path(
        "cda/translate-section/",
        enhanced_cda_translation_views.translate_cda_section_ajax,
        name="translate_cda_section_ajax",
    ),
    path(
        "cda/download-translated/<int:patient_id>/",
        enhanced_cda_translation_views.download_translated_cda,
        name="download_translated_cda",
    ),
    path(
        "translation/api-status/",
        enhanced_cda_translation_views.translation_api_status,
        name="translation_api_status",
    ),
    path(
        "translation/batch/",
        enhanced_cda_translation_views.batch_translate_documents,
        name="batch_translate_documents",
    ),
    # Legacy search interface (can be removed if not needed)
    path("search/", main_views.patient_search_view, name="patient_search"),
    path(
        "search/results/",
        main_views.patient_search_results,
        name="patient_search_results",
    ),
    # New CDA Translation Views (Country-based)
    path(
        "cda/country/<str:country_code>/",
        cda_translation_display,
        name="cda_country_display",
    ),
    path(
        "cda/country/<str:country_code>/<str:patient_id>/",
        cda_translation_display,
        name="cda_country_patient_display",
    ),
    # CDA Translation API Endpoints
    path(
        "api/cda/country/<str:country_code>/",
        cda_translation_api,
        name="cda_country_api",
    ),
    path(
        "api/cda/country/<str:country_code>/<str:patient_id>/",
        cda_translation_api,
        name="cda_country_patient_api",
    ),
    path("api/cda/available/", available_cda_files, name="cda_available"),
    # Enhanced Patient Search with CDA Links
    path("search/enhanced/", patient_search_with_cda, name="patient_search_enhanced"),
    # CDA Document Upload
    path("upload-cda/", main_views.upload_cda_document, name="upload_cda_document"),
    path(
        "uploaded-documents/",
        main_views.uploaded_documents_view,
        name="uploaded_documents",
    ),
    path(
        "process-document/<int:doc_index>/",
        main_views.process_uploaded_document,
        name="process_uploaded_document",
    ),
    path(
        "view-document/<int:doc_index>/",
        main_views.view_uploaded_document,
        name="view_uploaded_document",
    ),
    # PS Display Guidelines Table Rendering Test
    path("test/ps-tables/", main_views.test_ps_table_rendering, name="test_ps_tables"),
    # Patient data display (if function exists)
    # path("patient/<str:patient_id>/", views.patient_data_view, name="patient_data"),
    # Demo and testing (comment out until views exist)
    # path("demo/", demo_views.patient_demo_view, name="patient_demo"),
    # path("demo/sample-data/", demo_views.sample_data_view, name="sample_data"),
]
