"""
Patient Data URL Configuration
URL patterns for patient search and data management
"""

from django.urls import path
from . import views
from .demo_views import patient_demo_view
from . import document_views
from . import eadc_views
from . import test_data_views
from . import clinical_document_views

app_name = "patient_data"

urlpatterns = [
    # Patient demo page
    path("demo/", patient_demo_view, name="patient_demo"),
    # Patient search
    path("search/", views.patient_search_view, name="patient_search"),
    path(
        "search/results/<int:patient_id>/",
        views.patient_search_results,
        name="patient_search_results",
    ),
    # AJAX endpoints
    path(
        "api/request-service/",
        views.request_patient_service,
        name="request_patient_service",
    ),
    # Patient data viewing
    path(
        "data/<int:patient_data_id>/", views.patient_data_view, name="patient_data_view"
    ),
    # Local CDA document viewing
    path(
        "local-cda/<int:patient_id>/",
        views.local_cda_document_view,
        name="local_cda_document_view",
    ),
    path(
        "local-cda/<int:patient_id>/<int:document_index>/",
        views.local_cda_document_view,
        name="local_cda_document_view_indexed",
    ),
    # Consent management
    path(
        "consent/<int:patient_identifier_id>/",
        views.consent_management,
        name="consent_management",
    ),
    # Clinical Document Management
    path(
        "documents/request/<int:patient_data_id>/",
        document_views.request_clinical_documents,
        name="request_clinical_documents",
    ),
    path(
        "documents/view/<int:request_id>/",
        document_views.view_clinical_document,
        name="view_clinical_document",
    ),
    path(
        "documents/download/pdf/<int:request_id>/",
        document_views.download_document_pdf,
        name="download_document_pdf",
    ),
    path(
        "documents/download/raw/<int:request_id>/",
        document_views.download_document_raw,
        name="download_document_raw",
    ),
    path(
        "documents/history/<int:patient_data_id>/",
        document_views.clinical_document_history,
        name="clinical_document_history",
    ),
    # Enhanced Clinical Document Processing
    path(
        "clinical-documents/request/<int:patient_data_id>/",
        clinical_document_views.request_clinical_documents,
        name="request_clinical_documents",
    ),
    path(
        "clinical-documents/detail/<int:clinical_document_id>/",
        clinical_document_views.clinical_document_detail,
        name="clinical_document_detail",
    ),
    path(
        "clinical-documents/download/pdf/<int:clinical_document_id>/",
        clinical_document_views.download_summary_pdf,
        name="download_summary_pdf",
    ),
    path(
        "clinical-documents/download/html/<int:clinical_document_id>/",
        clinical_document_views.download_summary_html,
        name="download_summary_html",
    ),
    path(
        "clinical-documents/download/original/<int:clinical_document_id>/",
        clinical_document_views.download_original_document,
        name="download_original_document",
    ),
    # Document API endpoints
    path(
        "api/translate-section/",
        document_views.translate_document_section,
        name="translate_document_section",
    ),
    path(
        "api/document-status/",
        document_views.document_api_status,
        name="document_api_status",
    ),
    # EADC Integration URLs
    path(
        "eadc/",
        eadc_views.eadc_dashboard,
        name="eadc_dashboard",
    ),
    path(
        "eadc/validate/",
        eadc_views.validate_cda_document,
        name="validate_cda_document",
    ),
    path(
        "eadc/transform/",
        eadc_views.transform_document,
        name="transform_document",
    ),
    path(
        "eadc/demo/<str:demo_type>/",
        eadc_views.process_demo_document,
        name="process_demo_document",
    ),
    path(
        "eadc/patient/<str:patient_id>/",
        eadc_views.eadc_patient_documents,
        name="eadc_patient_documents",
    ),
    path(
        "eadc/process_document/<int:document_id>/",
        eadc_views.process_patient_document,
        name="process_patient_document",
    ),
    path(
        "eadc/history/",
        eadc_views.eadc_transformation_history,
        name="eadc_transformation_history",
    ),
    path(
        "eadc/download/<int:document_id>/<str:format_type>/",
        eadc_views.download_eadc_document,
        name="download_eadc_document",
    ),
    # EU Test Data Management (Admin-only)
    path(
        "admin/test-data/dashboard/",
        test_data_views.test_data_dashboard,
        name="test_data_dashboard",
    ),
    path(
        "admin/test-data/list/",
        test_data_views.test_data_list,
        name="test_data_list",
    ),
    path(
        "admin/test-data/patient/<int:patient_data_id>/",
        test_data_views.test_data_patient_view,
        name="test_data_patient_view",
    ),
    path(
        "admin/test-data/document/<int:document_id>/",
        test_data_views.test_data_document_view,
        name="test_data_document_view",
    ),
    path(
        "admin/test-data/document/<int:document_id>/pdf/",
        test_data_views.test_data_document_pdf,
        name="test_data_document_pdf",
    ),
    path(
        "admin/test-data/document/<int:document_id>/translated/",
        test_data_views.test_data_translated_view,
        name="test_data_translated_view",
    ),
    path(
        "admin/test-data/import/",
        test_data_views.import_external_test_data,
        name="import_external_test_data",
    ),
    path(
        "admin/test-data/api/stats/",
        test_data_views.test_data_stats_api,
        name="test_data_stats_api",
    ),
]
