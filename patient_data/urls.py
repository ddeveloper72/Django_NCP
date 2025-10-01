"""
Patient Data URL Configuration

URL patterns for patient search, data retrieval, and document request functionality.
"""

import os

# Import the debug session function
import sys

from django.urls import path

from patient_data import views as main_views

from .cda_test_views import (
    refresh_cda_index_view,
    smart_patient_search_view,
    test_patients_view,
)
from .debug_views import debug_cda_index

sys.path.append(os.path.dirname(__file__))
from debug_session_view import debug_session_view

from .clean_cda_views import clean_patient_cda_view
from .clinical_data_debugger import clinical_data_api, clinical_data_debugger
from .development_views import session_manager_view
from .enhanced_cda_display import EnhancedCDADisplayView
from .service_based_enhanced_cda_display import ServiceBasedEnhancedCDADisplayView
from .simplified_clinical_view import SimplifiedClinicalDataView
from .view_modules import enhanced_cda_translation_views
from .view_modules.cda_views import (
    available_cda_files,
    cda_translation_api,
    cda_translation_display,
    patient_search_with_cda,
)
from .view_modules.enhanced_cda_view import (
    EnhancedCDADocumentView,
    export_translated_cda,
    get_section_translation,
    toggle_translation_view,
)

app_name = "patient_data"

urlpatterns = [
    # Debug views
    path("debug/cda-index/", debug_cda_index, name="debug_cda_index"),
    path("debug/session/", debug_session_view, name="debug_session"),
    path("debug/session-manager/", session_manager_view, name="session_manager"),
    # Clinical Data Debugger
    path(
        "debug/clinical/<str:session_id>/",
        clinical_data_debugger,
        name="clinical_data_debugger",
    ),
    path("api/clinical/<str:session_id>/", clinical_data_api, name="clinical_data_api"),
    # Test CDA Documents Management
    path("test-patients/", test_patients_view, name="test_patients"),
    path("refresh-cda-index/", refresh_cda_index_view, name="refresh_cda_index"),
    path(
        "smart-search/<str:patient_id>/",
        smart_patient_search_view,
        name="smart_patient_search",
    ),
    # Patient data form and search
    path("", main_views.patient_data_view, name="patient_data_form"),
    path(
        "details/<str:patient_id>/",
        main_views.patient_details_view,
        name="patient_details",
    ),
    # Direct patient access from admin console (bypasses session middleware)
    path(
        "direct/<str:patient_id>/",
        main_views.direct_patient_view,
        name="direct_patient",
    ),
    # Default CDA view (L3 preferred)
    path("cda/<str:session_id>/", main_views.patient_cda_view, name="patient_cda_view"),
    # Document selection for multiple CDA documents
    path(
        "select-document/<str:patient_id>/",
        main_views.select_document_view,
        name="select_document",
    ),
    # Clean CDA view with structured data extraction
    path("clean/<str:patient_id>/", clean_patient_cda_view, name="clean_cda_view"),
    # Enhanced CDA Display with Patient ID (using our working view) - MUST BE BEFORE GENERIC PATTERN
    path(
        "cda/enhanced_display/<str:patient_id>/",
        EnhancedCDADisplayView.as_view(),
        name="enhanced_cda_display_with_id",
    ),
    # Service-Based Enhanced CDA Display (NEW) - Uses structured extraction services
    path(
        "cda/service_based/<str:patient_id>/",
        ServiceBasedEnhancedCDADisplayView.as_view(),
        name="service_based_enhanced_cda_display",
    ),
    # Interoperable Healthcare Data Service (NEWEST) - Complete CDA/FHIR interoperable service
    path(
        "healthcare/<str:patient_id>/",
        main_views.InteroperableHealthcareView.as_view(),
        name="interoperable_healthcare_data",
    ),
    path(
        "healthcare/<str:patient_id>/<str:resource_type>/",
        main_views.InteroperableHealthcareView.as_view(),
        name="interoperable_healthcare_data_typed",
    ),
    # Simplified Clinical Data View - MUST BE BEFORE GENERIC PATTERN
    path(
        "cda/simplified/<str:patient_id>/",
        SimplifiedClinicalDataView.as_view(),
        name="simplified_clinical_view",
    ),
    # Specific CDA type view (GENERIC PATTERN - KEEP AFTER SPECIFIC PATTERNS)
    path(
        "cda/<str:session_id>/<str:cda_type>/",
        main_views.patient_cda_view,
        name="patient_cda_view_typed",
    ),
    path(
        "cda/translation-toggle/<str:patient_id>/",
        main_views.cda_translation_toggle,
        name="cda_translation_toggle",
    ),
    path(
        "download/<str:patient_id>/",
        main_views.download_cda_pdf,
        name="download_cda_pdf",
    ),
    # PDF viewing endpoints for embedded PDFs
    path(
        "<str:patient_id>/pdf/<int:pdf_index>/",
        main_views.view_embedded_pdf,
        name="view_pdf",
    ),
    path(
        "<str:patient_id>/pdf/<int:pdf_index>/download/",
        main_views.download_embedded_pdf,
        name="download_pdf",
    ),
    # New CDA/ORCD views based on requirements
    path(
        "download/html/<str:patient_id>/",
        main_views.download_cda_html,
        name="download_cda_html",
    ),
    path(
        "download/patient-summary-pdf/<str:patient_id>/",
        main_views.download_patient_summary_pdf,
        name="download_patient_summary_pdf",
    ),
    path(
        "download/patient-summary-pdf-file/<str:patient_id>/",
        main_views.download_patient_summary_pdf_file,
        name="download_patient_summary_pdf_file",
    ),
    path(
        "orcd/<str:patient_id>/",
        main_views.patient_orcd_view,
        name="patient_orcd_view",
    ),
    path(
        "orcd/<str:patient_id>/download/",
        main_views.download_orcd_pdf,
        name="download_orcd_pdf",
    ),
    path(
        "orcd/<str:patient_id>/view/",
        main_views.view_orcd_pdf,
        name="view_orcd_pdf",
    ),
    path(
        "orcd/<str:patient_id>/debug/",
        main_views.debug_orcd_pdf,
        name="debug_orcd_pdf",
    ),
    path(
        "orcd/<str:patient_id>/base64/",
        main_views.orcd_pdf_base64,
        name="orcd_pdf_base64",
    ),
    path(
        "orcd/<str:patient_id>/download/<int:attachment_index>/",
        main_views.download_orcd_pdf,
        name="download_orcd_pdf_indexed",
    ),
    # Enhanced CDA Display with Multi-European Language Support
    path(
        "enhanced_cda_display/",
        main_views.enhanced_cda_display,
        name="enhanced_cda_display",
    ),
    # Enhanced CDA Translation Views
    path(
        "cda/enhanced/<str:patient_id>/",
        EnhancedCDADocumentView.as_view(),
        name="enhanced_cda_view",
    ),
    path(
        "cda/translate-toggle/<str:patient_id>/",
        toggle_translation_view,
        name="toggle_translation_view",
    ),
    path(
        "cda/section/<str:patient_id>/<str:section_id>/",
        get_section_translation,
        name="get_section_translation",
    ),
    path(
        "cda/export/<str:patient_id>/",
        export_translated_cda,
        name="export_translated_cda",
    ),
    path(
        "cda/translate-section/",
        enhanced_cda_translation_views.translate_cda_section_ajax,
        name="translate_cda_section_ajax",
    ),
    path(
        "cda/download-translated/<str:patient_id>/",
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
    # Patient data display (if function exists)
    # path("patient/<str:patient_id>/", views.patient_data_view, name="patient_data"),
    # Demo and testing (comment out until views exist)
    # path("demo/", demo_views.patient_demo_view, name="patient_demo"),
    # path("demo/sample-data/", demo_views.sample_data_view, name="sample_data"),
]
