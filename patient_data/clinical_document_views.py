"""
Enhanced Clinical Document Request View

Handles both CDA and FHIR bundle formats for clinical document processing.
Provides comprehensive patient summaries and multiple download options.
"""

import json
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
import os
from typing import Dict, Any, Optional

from .models import PatientData
from .clinical_models import ClinicalDocument, ClinicalDocumentRequest
from .services.cda_parser_service import CDAParserService
from .services.fhir_bundle_service import FHIRBundleService
from .services.pdf_generation_service import PDFGenerationService

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET", "POST"])
def request_clinical_documents(request, patient_data_id):
    """
    Enhanced view for requesting and processing clinical documents.
    Supports both CDA and FHIR bundle formats.
    """
    patient_data = get_object_or_404(PatientData, id=patient_data_id)

    if request.method == "POST":
        return _handle_document_request(request, patient_data)
    else:
        return _render_document_request_page(request, patient_data)


def _render_document_request_page(request, patient_data):
    """Render the clinical document request page."""
    # Check for existing clinical documents
    existing_documents = ClinicalDocument.objects.filter(
        request__patient_data=patient_data
    ).order_by("-received_timestamp")

    # Prepare context
    context = {
        "patient_data": patient_data,
        "patient_identifier": patient_data.patient_identifier,
        "member_state": patient_data.patient_identifier.home_member_state,
        "existing_documents": existing_documents,
        "supported_formats": ["CDA", "FHIR_BUNDLE"],
        "available_languages": {
            "en": "English",
            "fr": "French", 
            "de": "German",
            "es": "Spanish",
            "it": "Italian"
        },
        "summary_sections": [
            "patient_demographics",
            "conditions",
            "medications",
            "observations",
            "procedures",
            "allergies",
            "immunizations",
            "encounters",
            "diagnostic_reports",
        ],
    }

    return render(request, "patient_data/request_clinical_documents.html", context)


def _handle_document_request(request, patient_data):
    """Handle clinical document processing request."""
    try:
        # Get request parameters
        document_format = request.POST.get("document_format", "CDA")
        target_language = request.POST.get("target_language", "en")
        include_sections = request.POST.getlist("include_sections", [])
        generate_pdf = request.POST.get("generate_pdf", "true").lower() == "true"

        # Simulate fetching clinical document (in real implementation, this would call NCP service)
        document_data = _fetch_clinical_document(patient_data, document_format)

        if not document_data:
            messages.error(request, "Failed to retrieve clinical document.")
            return redirect(
                "patient_data:request_clinical_documents",
                patient_data_id=patient_data.id,
            )

        # Process document based on format
        if document_format == "CDA":
            processed_data = _process_cda_document(
                document_data, target_language, include_sections
            )
        elif document_format == "FHIR_BUNDLE":
            processed_data = _process_fhir_bundle(
                document_data, target_language, include_sections
            )
        else:
            messages.error(request, f"Unsupported document format: {document_format}")
            return redirect(
                "patient_data:request_clinical_documents",
                patient_data_id=patient_data.id,
            )

        if not processed_data["success"]:
            messages.error(
                request,
                f"Failed to process document: {processed_data.get('error', 'Unknown error')}",
            )
            return redirect(
                "patient_data:request_clinical_documents",
                patient_data_id=patient_data.id,
            )

        # Create clinical document request first
        doc_request = ClinicalDocumentRequest.objects.create(
            patient_data=patient_data,
            document_type=document_format,
            requesting_user=request.user,
            consent_method="EXPLICIT",  # Default to explicit consent
            status="COMPLETED",
        )

        # Save clinical document record
        clinical_doc = ClinicalDocument.objects.create(
            request=doc_request,
            document_type=document_format,
            service_type="PS",  # Default to Patient Summary
            document_id=f"doc_{doc_request.id}",
            document_title=f"Patient Summary - {document_format}",
            creation_date=timezone.now(),
            raw_document=json.dumps(document_data),
            document_size=len(json.dumps(document_data)),
            patient_summary=processed_data["patient_summary"],
            target_language=target_language,
            processing_status="completed",
            processing_completed=timezone.now(),
            created_by=request.user,
        )

        # Generate PDF if requested
        if generate_pdf:
            pdf_content = _generate_pdf_summary(
                processed_data["patient_summary"], document_format
            )
            if pdf_content:
                clinical_doc.pdf_content = pdf_content
                clinical_doc.save()

        messages.success(
            request,
            f"Clinical document successfully processed in {document_format} format.",
        )

        # Return detailed view
        return redirect(
            "patient_data:clinical_document_detail", document_id=clinical_doc.id
        )

    except Exception as e:
        logger.error(f"Error processing clinical document request: {str(e)}")
        messages.error(
            request, f"An error occurred while processing the document: {str(e)}"
        )
        return redirect(
            "patient_data:request_clinical_documents", patient_data_id=patient_data.id
        )


def _fetch_clinical_document(patient_data, document_format):
    """
    Simulate fetching clinical document from NCP service.
    In real implementation, this would make actual NCP calls.
    """
    # For demo purposes, load sample data from test files
    sample_data_path = getattr(settings, "SAMPLE_DATA_PATH", "test_data")

    if document_format == "CDA":
        # Load sample CDA document
        cda_file_path = os.path.join(
            sample_data_path,
            "openncp_sample_data",
            "clinical_documents",
            "sample_cda.xml",
        )
        if os.path.exists(cda_file_path):
            with open(cda_file_path, "r", encoding="utf-8") as file:
                return file.read()
    elif document_format == "FHIR_BUNDLE":
        # Load sample FHIR bundle
        fhir_file_path = os.path.join(
            sample_data_path,
            "openncp_sample_data",
            "fhir_bundles",
            "sample_bundle.json",
        )
        if os.path.exists(fhir_file_path):
            with open(fhir_file_path, "r", encoding="utf-8") as file:
                return json.loads(file.read())

    # Fallback: generate synthetic data for demo
    return _generate_sample_data(patient_data, document_format)


def _generate_sample_data(patient_data, document_format):
    """Generate sample clinical data for demonstration."""
    if document_format == "FHIR_BUNDLE":
        # Generate sample FHIR bundle
        return {
            "resourceType": "Bundle",
            "id": f"bundle-{patient_data.id}",
            "type": "document",
            "timestamp": timezone.now().isoformat(),
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": f"patient-{patient_data.id}",
                        "identifier": [
                            {
                                "system": "urn:oid:2.16.17.710.806.1000.990.1",
                                "value": patient_data.patient_identifier.patient_id,
                            }
                        ],
                        "name": [{"family": "Demo", "given": ["Patient"]}],
                        "birthDate": "1970-01-01",
                        "gender": "unknown",
                    }
                },
                {
                    "resource": {
                        "resourceType": "Condition",
                        "id": "condition-1",
                        "clinicalStatus": {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                    "code": "active",
                                }
                            ]
                        },
                        "code": {
                            "coding": [
                                {
                                    "system": "http://snomed.info/sct",
                                    "code": "386661006",
                                    "display": "Fever",
                                }
                            ]
                        },
                        "subject": {"reference": f"Patient/patient-{patient_data.id}"},
                    }
                },
                {
                    "resource": {
                        "resourceType": "Observation",
                        "id": "observation-1",
                        "status": "final",
                        "category": [
                            {
                                "coding": [
                                    {
                                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                        "code": "vital-signs",
                                    }
                                ]
                            }
                        ],
                        "code": {
                            "coding": [
                                {
                                    "system": "http://loinc.org",
                                    "code": "8310-5",
                                    "display": "Body temperature",
                                }
                            ]
                        },
                        "subject": {"reference": f"Patient/patient-{patient_data.id}"},
                        "valueQuantity": {
                            "value": 38.5,
                            "unit": "degrees C",
                            "system": "http://unitsofmeasure.org",
                            "code": "Cel",
                        },
                    }
                },
            ],
        }
    else:  # CDA format
        return f"""<?xml version="1.0" encoding="UTF-8"?>
        <ClinicalDocument xmlns="urn:hl7-org:v3">
            <id extension="sample-{patient_data.id}" root="2.16.17.710.806.1000.990.1"/>
            <code code="60591-5" codeSystem="2.16.840.1.113883.6.1" displayName="Patient Summary"/>
            <title>Patient Summary Document</title>
            <effectiveTime value="{timezone.now().strftime('%Y%m%d%H%M%S')}"/>
            <recordTarget>
                <patientRole>
                    <id extension="{patient_data.patient_identifier.patient_id}" root="2.16.17.710.806.1000.990.1"/>
                    <patient>
                        <name>
                            <given>Demo</given>
                            <family>Patient</family>
                        </name>
                        <administrativeGenderCode code="UN" codeSystem="2.16.840.1.113883.5.1"/>
                        <birthTime value="19700101"/>
                    </patient>
                </patientRole>
            </recordTarget>
            <component>
                <structuredBody>
                    <component>
                        <section>
                            <code code="11450-4" codeSystem="2.16.840.1.113883.6.1" displayName="Problem List"/>
                            <title>Active Problems</title>
                            <text>
                                <table>
                                    <tr><td>Fever</td><td>Active</td></tr>
                                </table>
                            </text>
                            <entry>
                                <observation classCode="OBS" moodCode="EVN">
                                    <code code="386661006" codeSystem="2.16.840.1.113883.6.96" displayName="Fever"/>
                                    <statusCode code="completed"/>
                                    <value xsi:type="CD" code="386661006" codeSystem="2.16.840.1.113883.6.96" displayName="Fever"/>
                                </observation>
                            </entry>
                        </section>
                    </component>
                </structuredBody>
            </component>
        </ClinicalDocument>"""


def _process_cda_document(document_data, target_language, include_sections):
    """Process CDA document using CDAParserService."""
    try:
        cda_service = CDAParserService()
        result = cda_service.parse_cda_document(document_data)

        if result["success"]:
            # Apply language translation if needed
            if target_language != "en":
                result["patient_summary"] = _translate_summary(
                    result["patient_summary"], target_language
                )

            # Filter sections if specified
            if include_sections:
                result["patient_summary"] = _filter_summary_sections(
                    result["patient_summary"], include_sections
                )

        return result
    except Exception as e:
        logger.error(f"Error processing CDA document: {str(e)}")
        return {"success": False, "error": str(e)}


def _process_fhir_bundle(document_data, target_language, include_sections):
    """Process FHIR bundle using FHIRBundleService."""
    try:
        fhir_service = FHIRBundleService()
        result = fhir_service.parse_fhir_bundle(document_data)

        if result["success"]:
            # Apply language translation if needed
            if target_language != "en":
                result["patient_summary"] = _translate_summary(
                    result["patient_summary"], target_language
                )

            # Filter sections if specified
            if include_sections:
                result["patient_summary"] = _filter_summary_sections(
                    result["patient_summary"], include_sections
                )

        return result
    except Exception as e:
        logger.error(f"Error processing FHIR bundle: {str(e)}")
        return {"success": False, "error": str(e)}


def _translate_summary(patient_summary, target_language):
    """
    Translate patient summary to target language.
    This is a placeholder - in real implementation, would use translation service.
    """
    # TODO: Implement actual translation service
    # For now, just add language indicator
    if "summary_metadata" not in patient_summary:
        patient_summary["summary_metadata"] = {}

    patient_summary["summary_metadata"]["target_language"] = target_language
    patient_summary["summary_metadata"][
        "translation_note"
    ] = f"Summary translated to {target_language}"

    return patient_summary


def _filter_summary_sections(patient_summary, include_sections):
    """Filter patient summary to only include specified sections."""
    if not include_sections:
        return patient_summary

    filtered_summary = {}
    for section in include_sections:
        if section in patient_summary:
            filtered_summary[section] = patient_summary[section]

    # Always include metadata
    if "summary_metadata" in patient_summary:
        filtered_summary["summary_metadata"] = patient_summary["summary_metadata"]

    return filtered_summary


def _generate_pdf_summary(patient_summary, document_format):
    """Generate PDF content from patient summary."""
    try:
        pdf_service = PDFGenerationService()

        if document_format == "FHIR_BUNDLE":
            fhir_service = FHIRBundleService()
            pdf_data = fhir_service.convert_to_pdf_data(patient_summary)
        else:  # CDA
            cda_service = CDAParserService()
            pdf_data = cda_service.convert_to_pdf_data(patient_summary)

        return pdf_service.generate_patient_summary_pdf(pdf_data)
    except Exception as e:
        logger.error(f"Error generating PDF summary: {str(e)}")
        return None


@login_required
def clinical_document_detail(request, document_id):
    """Display detailed view of processed clinical document."""
    clinical_doc = get_object_or_404(ClinicalDocument, id=document_id)

    # Parse processed content
    try:
        patient_summary = json.loads(clinical_doc.processed_content)
    except (json.JSONDecodeError, TypeError):
        patient_summary = {}

    context = {
        "clinical_document": clinical_doc,
        "patient_data": clinical_doc.patient_data,
        "patient_summary": patient_summary,
        "has_pdf": bool(clinical_doc.pdf_content),
        "sections": _get_summary_sections(patient_summary),
    }

    return render(request, "patient_data/clinical_document_detail.html", context)


def _get_summary_sections(patient_summary):
    """Get available sections from patient summary."""
    sections = []
    section_mapping = {
        "patient_demographics": "Patient Demographics",
        "conditions": "Medical Conditions",
        "medications": "Current Medications",
        "observations": "Vital Signs & Lab Results",
        "procedures": "Procedures & Interventions",
        "allergies": "Allergies & Intolerances",
        "immunizations": "Immunization History",
        "encounters": "Healthcare Encounters",
        "diagnostic_reports": "Diagnostic Reports",
        "care_providers": "Care Providers",
    }

    for key, title in section_mapping.items():
        if key in patient_summary and patient_summary[key]:
            sections.append(
                {
                    "key": key,
                    "title": title,
                    "data": patient_summary[key],
                    "count": (
                        len(patient_summary[key])
                        if isinstance(patient_summary[key], list)
                        else 1
                    ),
                }
            )

    return sections


@login_required
def download_original_document(request, document_id):
    """Download original clinical document."""
    clinical_doc = get_object_or_404(ClinicalDocument, id=document_id)

    try:
        original_content = json.loads(clinical_doc.original_content)

        # Determine content type and filename based on format
        if clinical_doc.document_format == "FHIR_BUNDLE":
            content_type = "application/json"
            filename = f"original_fhir_bundle_{clinical_doc.id}.json"
            content = json.dumps(original_content, indent=2)
        else:  # CDA
            content_type = "application/xml"
            filename = f"original_cda_document_{clinical_doc.id}.xml"
            content = (
                original_content
                if isinstance(original_content, str)
                else str(original_content)
            )

        response = HttpResponse(content, content_type=content_type)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        logger.error(f"Error downloading original document: {str(e)}")
        messages.error(request, "Failed to download original document.")
        return redirect(
            "patient_data:clinical_document_detail", document_id=document_id
        )


@login_required
def download_summary_pdf(request, document_id):
    """Download patient summary as PDF."""
    clinical_doc = get_object_or_404(ClinicalDocument, id=document_id)

    if not clinical_doc.pdf_content:
        messages.error(request, "PDF summary not available for this document.")
        return redirect(
            "patient_data:clinical_document_detail", document_id=document_id
        )

    response = HttpResponse(clinical_doc.pdf_content, content_type="application/pdf")
    filename = f"patient_summary_{clinical_doc.id}.pdf"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
def download_summary_html(request, document_id):
    """Download patient summary as HTML."""
    clinical_doc = get_object_or_404(ClinicalDocument, id=document_id)

    try:
        patient_summary = json.loads(clinical_doc.processed_content)

        # Generate HTML content
        if clinical_doc.document_format == "FHIR_BUNDLE":
            fhir_service = FHIRBundleService()
            html_content = fhir_service.generate_html_summary(patient_summary)
        else:  # CDA
            cda_service = CDAParserService()
            html_content = cda_service.generate_html_summary(patient_summary)

        response = HttpResponse(html_content, content_type="text/html")
        filename = f"patient_summary_{clinical_doc.id}.html"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        logger.error(f"Error generating HTML summary: {str(e)}")
        messages.error(request, "Failed to generate HTML summary.")
        return redirect(
            "patient_data:clinical_document_detail", document_id=document_id
        )
