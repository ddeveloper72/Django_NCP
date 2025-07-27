from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

# FHIR Services Admin Configuration


class FHIRServiceAdmin(admin.ModelAdmin):
    """Base admin class for FHIR services"""

    list_per_page = 25
    show_full_result_count = False

    def view_fhir_document(self, obj):
        if hasattr(obj, "fhir_document") and obj.fhir_document:
            return format_html(
                '<a href="#" onclick="showFHIRModal(\'{}\'); return false;">View FHIR</a>',
                obj.id,
            )
        return "No FHIR data"

    view_fhir_document.short_description = "FHIR Document"

    def view_cda_document(self, obj):
        if hasattr(obj, "cda_document") and obj.cda_document:
            return format_html(
                '<a href="#" onclick="showCDAModal(\'{}\'); return false;">View CDA</a>',
                obj.id,
            )
        return "No CDA data"

    view_cda_document.short_description = "CDA Document"


# Placeholder admin classes for future FHIR service models
class PatientSummaryAdmin(FHIRServiceAdmin):
    list_display = [
        "patient",
        "created_date",
        "status",
        "view_fhir_document",
        "view_cda_document",
    ]
    list_filter = ["status", "created_date"]
    search_fields = [
        "patient__national_id",
        "patient__first_name",
        "patient__last_name",
    ]


class ePrescriptionAdmin(FHIRServiceAdmin):
    list_display = [
        "patient",
        "prescription_id",
        "medication",
        "prescriber",
        "status",
        "view_fhir_document",
    ]
    list_filter = ["status", "created_date"]
    search_fields = ["prescription_id", "patient__national_id", "medication"]


class eDispensationAdmin(FHIRServiceAdmin):
    list_display = [
        "patient",
        "dispensation_id",
        "pharmacy",
        "dispense_date",
        "status",
        "view_fhir_document",
    ]
    list_filter = ["status", "dispense_date"]
    search_fields = ["dispensation_id", "patient__national_id", "pharmacy"]


# Register a simple info page for now
from django.shortcuts import render
from django.http import HttpResponse


def fhir_services_info(request):
    return HttpResponse(
        """
    <h1>EU eHealth FHIR Services Administration</h1>
    <p>This section will contain administration interfaces for:</p>
    <ul>
        <li><strong>Patient Summary (PS)</strong> - International Patient Summary documents</li>
        <li><strong>ePrescription (eP)</strong> - Cross-border prescription management</li>
        <li><strong>eDispensation (eD)</strong> - Cross-border dispensation tracking</li>
        <li><strong>Laboratory Results</strong> - Cross-border lab data exchange</li>
        <li><strong>Hospital Discharge Reports</strong> - Cross-border discharge summaries</li>
        <li><strong>Medical Imaging</strong> - Cross-border imaging reports</li>
    </ul>
    <p>Models and admin interfaces will be created as services are implemented.</p>
    <p><a href="/admin/">Back to Admin</a></p>
    """
    )


# Note: Models will be registered here as they are created
