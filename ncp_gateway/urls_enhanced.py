"""
Enhanced API Architecture for FHIR Integration Phase
Django NCP - European Healthcare Interoperability Platform
"""

from django.urls import path, include
from . import api_views

# Enhanced API URL patterns for FHIR integration
urlpatterns = [
    # Core NCP Gateway API (existing)
    path("countries/", api_views.get_available_countries, name="api_countries"),
    path("patient/lookup/", api_views.patient_lookup, name="api_patient_lookup"),
    path(
        "patient/<str:patient_id>/document/<str:document_type>/",
        api_views.get_patient_document,
        name="api_patient_document",
    ),
    
    # Enhanced FHIR Integration APIs
    path("fhir/", include([
        # FHIR Patient Summary endpoints
        path(
            "patient/<str:patient_id>/summary/",
            api_views.get_fhir_patient_summary,
            name="api_fhir_patient_summary"
        ),
        path(
            "patient/<str:patient_id>/summary/pdf/",
            api_views.get_patient_summary_pdf,
            name="api_patient_summary_pdf"
        ),
        
        # FHIR Resource conversion endpoints
        path(
            "convert/cda-to-fhir/",
            api_views.convert_cda_to_fhir,
            name="api_convert_cda_to_fhir"
        ),
        path(
            "convert/fhir-to-cda/",
            api_views.convert_fhir_to_cda,
            name="api_convert_fhir_to_cda"
        ),
        
        # FHIR Validation endpoints
        path(
            "validate/resource/",
            api_views.validate_fhir_resource,
            name="api_validate_fhir_resource"
        ),
    ])),
    
    # Health Provider Index (HPI) Integration
    path("hpi/", include([
        path(
            "provider/search/",
            api_views.search_healthcare_providers,
            name="api_hpi_provider_search"
        ),
        path(
            "provider/<str:provider_id>/",
            api_views.get_healthcare_provider,
            name="api_hpi_provider_detail"
        ),
        path(
            "organization/search/",
            api_views.search_healthcare_organizations,
            name="api_hpi_organization_search"
        ),
    ])),
    
    # Enhanced Document Processing
    path("document/", include([
        # Secure HTML processing
        path(
            "html/sanitize/",
            api_views.sanitize_clinical_html,
            name="api_sanitize_html"
        ),
        path(
            "html/validate/",
            api_views.validate_clinical_html,
            name="api_validate_html"
        ),
        
        # PDF generation endpoints
        path(
            "pdf/generate/",
            api_views.generate_clinical_pdf,
            name="api_generate_pdf"
        ),
        path(
            "pdf/template/<str:template_type>/",
            api_views.generate_templated_pdf,
            name="api_generate_templated_pdf"
        ),
        
        # Clinical narrative integration
        path(
            "narrative/extract/",
            api_views.extract_clinical_narrative,
            name="api_extract_narrative"
        ),
        path(
            "narrative/integrate/",
            api_views.integrate_clinical_narrative,
            name="api_integrate_narrative"
        ),
    ])),
    
    # Cross-border Healthcare Communication
    path("cross-border/", include([
        path(
            "consent/verify/",
            api_views.verify_patient_consent,
            name="api_verify_consent"
        ),
        path(
            "audit/log/",
            api_views.log_cross_border_access,
            name="api_audit_log"
        ),
        path(
            "member-state/<str:country_code>/capabilities/",
            api_views.get_member_state_capabilities,
            name="api_member_state_capabilities"
        ),
    ])),
    
    # API Health and Monitoring
    path("health/", include([
        path(
            "status/",
            api_views.api_health_status,
            name="api_health_status"
        ),
        path(
            "fhir/connectivity/",
            api_views.test_fhir_connectivity,
            name="api_test_fhir_connectivity"
        ),
        path(
            "hpi/connectivity/",
            api_views.test_hpi_connectivity,
            name="api_test_hpi_connectivity"
        ),
    ])),
]