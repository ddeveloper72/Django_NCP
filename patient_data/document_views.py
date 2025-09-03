"""
Clinical Document Views
Views for requesting, retrieving, and displaying clinical documents
"""

import json
import base64
import logging
from typing import Dict, Any
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings

from .models import PatientIdentifier, PatientData, MemberState
from .clinical_models import (
    ClinicalDocumentRequest,
    ClinicalDocument,
    DocumentTranslation,
)
from .document_services import NCPDocumentRetriever, CDAProcessor, FHIRProcessor

# Import translation services
try:
    from translation_services.terminology_translator import (
        TerminologyTranslator,
        get_available_translation_languages,
    )

    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False
    logger.warning("Translation services not available")

logger = logging.getLogger(__name__)


def request_clinical_documents(request, patient_data_id):
    """Display form to request clinical documents for a patient"""
    try:
        # Get patient details - this will raise 404 if no patient data exists
        patient_data = get_object_or_404(PatientData, id=patient_data_id)
        patient_identifier = patient_data.patient_identifier
    except:
        messages.error(
            request,
            "Patient data not found. Please ensure patient data has been retrieved before requesting clinical documents.",
        )
        return redirect("patient_data:patient_search")

    if request.method == "GET":
        try:
            # Get available document types
            document_types = [
                {
                    "code": "PS",
                    "name": "Patient Summary",
                    "description": "Comprehensive patient summary",
                },
                {
                    "code": "ED",
                    "name": "Emergency Data",
                    "description": "Emergency medical information",
                },
                {
                    "code": "ePrescription",
                    "name": "ePrescription",
                    "description": "Electronic prescription",
                },
                {
                    "code": "eDispensation",
                    "name": "eDispensation",
                    "description": "Electronic dispensation",
                },
            ]

            # Get consent methods
            consent_methods = [
                {
                    "code": "EXPLICIT",
                    "name": "Explicit Consent",
                    "description": "Patient must explicitly consent",
                },
                {
                    "code": "IMPLIED",
                    "name": "Implied Consent",
                    "description": "Consent is implied by emergency",
                },
                {
                    "code": "EMERGENCY",
                    "name": "Emergency Override",
                    "description": "Emergency access without consent",
                },
            ]

            context = {
                "patient_data": patient_data,
                "patient_identifier": patient_identifier,
                "document_types": document_types,
                "consent_methods": consent_methods,
                "member_state": patient_identifier.home_member_state,
            }

            return render(request, "patient_data/request_documents.html", context)

        except Exception as e:
            logger.error(f"Error displaying document request form: {e}")
            messages.error(request, f"Error loading document request form: {e}")
            return redirect("patient_data:patient_search")

    elif request.method == "POST":
        try:
            # Get form data
            patient_data = get_object_or_404(PatientData, id=patient_data_id)
            document_type = request.POST.get("document_type")
            consent_method = request.POST.get("consent_method")
            purpose_of_use = request.POST.get("purpose_of_use", "TREATMENT")

            logger.info(
                f"Requesting {document_type} for patient {patient_data.id} from {patient_data.patient_identifier.home_member_state.country_name}"
            )

            # Create document request record
            doc_request = ClinicalDocumentRequest.objects.create(
                patient_data=patient_data,
                document_type=document_type,
                consent_method=consent_method,
                purpose_of_use=purpose_of_use,
                requesting_organization="Sample Healthcare Provider",
                request_date=timezone.now(),
                status="PENDING",
            )

            # Simulate document retrieval
            retriever = NCPDocumentRetriever()
            result = retriever.retrieve_patient_summary(
                patient_id=patient_data.patient_identifier.patient_id,
                member_state_oid=patient_data.patient_identifier.home_member_state.home_community_id,
                consent_method=consent_method,
            )

            if result["success"]:
                # Create clinical document record
                clinical_doc = ClinicalDocument.objects.create(
                    request=doc_request,
                    document_id=result["document_id"],
                    title=result["title"],
                    document_type=result["document_type"],
                    content=result["content"],
                    mime_type=result["mime_type"],
                    creation_date=result["creation_date"],
                    has_embedded_pdf=result.get("has_embedded_pdf", False),
                )

                # Process the document to extract PDF if present
                if clinical_doc.has_embedded_pdf:
                    try:
                        # In real implementation, extract base64 PDF from CDA
                        # For demo, create a placeholder
                        clinical_doc.embedded_pdf_base64 = (
                            "JVBERi0xLjQKJcOkw7zDtsKkw7bCpA=="  # Placeholder
                        )
                        clinical_doc.save()
                    except Exception as e:
                        logger.warning(f"Could not extract PDF: {e}")

                # Update request status
                doc_request.status = "COMPLETED"
                doc_request.save()

                messages.success(
                    request, f"Successfully retrieved {document_type} document"
                )
                return redirect("patient_data:view_clinical_document", doc_request.id)
            else:
                doc_request.status = "FAILED"
                doc_request.save()
                messages.error(request, "Failed to retrieve clinical document")
                return redirect(
                    "patient_data:patient_search_results",
                    patient_data.patient_identifier.id,
                )

        except Exception as e:
            logger.error(f"Error requesting clinical documents: {e}")
            messages.error(request, f"Error requesting documents: {e}")
            return redirect(
                "patient_data:patient_search_results",
                patient_data.patient_identifier.id,
            )


def view_clinical_document(request, request_id):
    """View clinical document details and content with optional terminology translation"""
    try:
        doc_request = get_object_or_404(ClinicalDocumentRequest, id=request_id)
        clinical_doc = get_object_or_404(ClinicalDocument, request=doc_request)

        # Get translation language from request (if specified)
        target_language = request.GET.get("translate_to", None)
        source_language = request.GET.get("source_lang", "en")

        # Process document for display
        rendered_html = None
        document_metadata = {}
        translation_result = None
        translation_summary = None
        available_languages = []

        # Get available translation languages
        if TRANSLATION_AVAILABLE:
            available_languages = get_available_translation_languages()

        try:
            if clinical_doc.document_type in ["CDA_L1", "CDA_L3"]:
                processor = CDAProcessor()
                rendered_html = processor.render_as_html(clinical_doc.content)
                document_metadata = processor.parse_cda_document(clinical_doc.content)
            elif clinical_doc.document_type == "FHIR_BUNDLE":
                processor = FHIRProcessor()
                rendered_html = processor.render_as_html(clinical_doc.content)
                document_metadata = processor.parse_fhir_bundle(clinical_doc.content)

            # Apply terminology translation if requested and available
            if (
                target_language
                and TRANSLATION_AVAILABLE
                and target_language != source_language
            ):
                try:
                    translator = TerminologyTranslator(target_language=target_language)
                    translation_result = translator.translate_clinical_document(
                        document_content=clinical_doc.content,
                        source_language=source_language,
                    )

                    # Update rendered HTML with translations
                    if translation_result["translations_applied"] > 0:
                        # Re-render with translated content
                        if clinical_doc.document_type in ["CDA_L1", "CDA_L3"]:
                            rendered_html = processor.render_as_html(
                                translation_result["content"]
                            )
                        elif clinical_doc.document_type == "FHIR_BUNDLE":
                            rendered_html = processor.render_as_html(
                                translation_result["content"]
                            )

                    # Generate translation summary for UI
                    translation_summary = translator.get_translation_summary(
                        translation_result
                    )

                    logger.info(
                        f"Applied {translation_result['translations_applied']} terminology translations"
                    )

                except Exception as e:
                    logger.error(f"Error applying terminology translation: {e}")
                    messages.warning(request, f"Translation partially failed: {e}")

        except Exception as e:
            logger.error(f"Error processing document: {e}")
            rendered_html = (
                f"<div class='alert alert-danger'>Error processing document: {e}</div>"
            )

        context = {
            "doc_request": doc_request,
            "clinical_doc": clinical_doc,
            "rendered_html": rendered_html,
            "document_metadata": document_metadata,
            "can_download_pdf": clinical_doc.has_embedded_pdf
            and clinical_doc.embedded_pdf_base64,
            # Translation context
            "translation_available": TRANSLATION_AVAILABLE,
            "available_languages": available_languages,
            "current_target_language": target_language,
            "source_language": source_language,
            "translation_result": translation_result,
            "translation_summary": translation_summary,
        }

        return render(request, "patient_data/view_document.html", context)

    except Exception as e:
        logger.error(f"Error viewing clinical document: {e}")
        messages.error(request, f"Error loading document: {e}")
        return redirect("patient_search")


def download_document_pdf(request, request_id):
    """Download embedded PDF from clinical document"""
    try:
        doc_request = get_object_or_404(ClinicalDocumentRequest, id=request_id)
        clinical_doc = get_object_or_404(ClinicalDocument, request=doc_request)

        if not clinical_doc.has_embedded_pdf or not clinical_doc.embedded_pdf_base64:
            raise Http404("PDF not available for this document")

        # Decode base64 PDF
        try:
            pdf_data = base64.b64decode(clinical_doc.embedded_pdf_base64)
        except Exception as e:
            logger.error(f"Error decoding PDF: {e}")
            messages.error(request, "Error extracting PDF from document")
            return redirect("view_clinical_document", request_id)

        # Create HTTP response with PDF
        response = HttpResponse(pdf_data, content_type="application/pdf")
        filename = f"{clinical_doc.document_type}_{clinical_doc.document_id}.pdf"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        logger.info(f"Downloaded PDF for document {clinical_doc.document_id}")
        return response

    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error downloading PDF: {e}")
        messages.error(request, f"Error downloading PDF: {e}")
        return redirect("view_clinical_document", request_id)


def download_document_raw(request, request_id):
    """Download raw document content (CDA XML or FHIR JSON)"""
    try:
        doc_request = get_object_or_404(ClinicalDocumentRequest, id=request_id)
        clinical_doc = get_object_or_404(ClinicalDocument, request=doc_request)

        # Create HTTP response with raw content
        response = HttpResponse(
            clinical_doc.content, content_type=clinical_doc.mime_type
        )

        # Determine file extension
        if clinical_doc.document_type in ["CDA_L1", "CDA_L3"]:
            extension = "xml"
        elif clinical_doc.document_type == "FHIR_BUNDLE":
            extension = "json"
        else:
            extension = "txt"

        filename = (
            f"{clinical_doc.document_type}_{clinical_doc.document_id}.{extension}"
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        logger.info(f"Downloaded raw document {clinical_doc.document_id}")
        return response

    except Exception as e:
        logger.error(f"Error downloading raw document: {e}")
        messages.error(request, f"Error downloading document: {e}")
        return redirect("view_clinical_document", request_id)


def clinical_document_history(request, patient_data_id):
    """View history of clinical document requests for a patient"""
    try:
        # Get patient details - this will raise 404 if no patient data exists
        patient_data = get_object_or_404(PatientData, id=patient_data_id)

        # Get all document requests for this patient
        doc_requests = ClinicalDocumentRequest.objects.filter(
            patient_data=patient_data
        ).order_by("-request_date")

        context = {
            "patient_data": patient_data,
            "patient_identifier": patient_data.patient_identifier,
            "doc_requests": doc_requests,
        }

        return render(request, "patient_data/document_history.html", context)

    except PatientData.DoesNotExist:
        messages.error(
            request,
            "Patient data not found. Please ensure patient data has been retrieved before accessing document history.",
        )
        return redirect("patient_data:patient_search")
    except Exception as e:
        logger.error(f"Error viewing document history: {e}")
        messages.error(request, f"Error loading document history: {e}")
        return redirect("patient_data:patient_search")


@require_http_methods(["POST"])
@csrf_exempt
def translate_document_section(request):
    """AJAX endpoint to translate document sections"""
    try:
        data = json.loads(request.body)
        text = data.get("text", "")
        target_language = data.get("target_language", "en")

        if not text:
            return JsonResponse({"error": "No text provided"}, status=400)

        # Simulate translation (in real implementation, use actual translation service)
        translated_text = f"[TRANSLATED TO {target_language.upper()}] {text}"

        # Save translation if it's significant
        if len(text) > 50:
            DocumentTranslation.objects.create(
                original_text=text,
                translated_text=translated_text,
                source_language="auto",
                target_language=target_language,
                translation_service="demo_service",
            )

        return JsonResponse(
            {"translated_text": translated_text, "target_language": target_language}
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Error translating text: {e}")
        return JsonResponse({"error": str(e)}, status=500)


def document_api_status(request):
    """API endpoint to check document service status"""
    try:
        # Check database connectivity
        pending_requests = ClinicalDocumentRequest.objects.filter(
            status="PENDING"
        ).count()
        completed_requests = ClinicalDocumentRequest.objects.filter(
            status="COMPLETED"
        ).count()

        status = {
            "status": "operational",
            "timestamp": timezone.now().isoformat(),
            "pending_requests": pending_requests,
            "completed_requests": completed_requests,
            "services": {
                "cda_processor": "available",
                "fhir_processor": "available",
                "ncp_retriever": "simulated",
                "translation_service": "demo",
            },
        }

        return JsonResponse(status)

    except Exception as e:
        logger.error(f"Error checking service status: {e}")
        return JsonResponse(
            {
                "status": "error",
                "error": str(e),
                "timestamp": timezone.now().isoformat(),
            },
            status=500,
        )
