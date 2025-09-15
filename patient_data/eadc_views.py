"""
EADC Integration Views
Provides web interface for EADC document processing and validation
ADMIN/DELEGATED SERVICE - Requires proper authentication and authorization
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import PermissionDenied
import json
import logging

from .models import PatientData
from .clinical_models import ClinicalDocument, ClinicalDocumentRequest
from .eadc_integration import EADCProcessor, EADCDocumentManager
from .document_services import CDAProcessor

logger = logging.getLogger(__name__)


def is_eadc_admin(user):
    """
    Check if user has EADC administration privileges
    - Staff members (is_staff=True)
    - Superusers (is_superuser=True)
    - Users in 'eadc_administrators' group
    """
    if user.is_superuser or user.is_staff:
        return True

    # Check if user is in EADC administrators group
    return user.groups.filter(name="eadc_administrators").exists()


def is_eadc_operator(user):
    """
    Check if user has EADC operation privileges (can view but limited processing)
    - All admin privileges
    - Users in 'eadc_operators' group
    """
    if is_eadc_admin(user):
        return True

    # Check if user is in EADC operators group
    return user.groups.filter(name="eadc_operators").exists()


@login_required
@user_passes_test(is_eadc_operator, login_url="/admin/login/")
def eadc_dashboard(request):
    """
    EADC Dashboard showing transformation capabilities and statistics
    """
    processor = EADCProcessor()
    manager = EADCDocumentManager()

    # Get demo documents
    demo_documents = processor.get_demo_documents()

    # Get recent transformations (if any)
    recent_documents = ClinicalDocument.objects.filter(
        document_format__in=["CDA_L3", "EPSOS_CDA"]
    ).order_by("-created_at")[:10]

    context = {
        "processor": processor,
        "supported_transformations": processor.supported_transformations,
        "demo_documents": demo_documents,
        "recent_documents": recent_documents,
        "eadc_config_path": processor.eadc_config_path,
        "page_title": "EADC Integration Dashboard",
        "user_is_admin": is_eadc_admin(request.user),
        "user_is_operator": is_eadc_operator(request.user),
    }

    return render(request, "patient_data/eadc_dashboard.html", context)


@require_http_methods(["POST"])
@csrf_exempt
@login_required
@user_passes_test(is_eadc_operator, login_url="/admin/login/")
def validate_cda_document(request):
    """
    Validate CDA document via AJAX
    """
    try:
        data = json.loads(request.body)
        document_content = data.get("document_content", "")
        document_type = data.get("document_type", "PS")

        if not document_content:
            return JsonResponse(
                {"success": False, "error": "Document content is required"}
            )

        processor = EADCProcessor()
        validation_result = processor.validate_cda_document(
            document_content, document_type
        )

        return JsonResponse({"success": True, "validation": validation_result})

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON data"})
    except Exception as e:
        logger.error(f"Error validating CDA document: {e}")
        return JsonResponse({"success": False, "error": str(e)})


@require_http_methods(["POST"])
@csrf_exempt
@login_required
@user_passes_test(is_eadc_admin, login_url="/admin/login/")
def transform_document(request):
    """
    Transform document between national and epSOS formats
    """
    try:
        data = json.loads(request.body)
        document_content = data.get("document_content", "")
        document_type = data.get("document_type", "PS")
        transformation_type = data.get("transformation_type", "national_to_epsos")
        country_code = data.get("country_code", "GR")

        if not document_content:
            return JsonResponse(
                {"success": False, "error": "Document content is required"}
            )

        processor = EADCProcessor()

        if transformation_type == "national_to_epsos":
            result = processor.transform_national_to_epsos(
                document_content, document_type, country_code
            )
        elif transformation_type == "epsos_to_national":
            target_country = data.get("target_country", country_code)
            result = processor.transform_epsos_to_national(
                document_content, document_type, target_country
            )
        else:
            return JsonResponse(
                {"success": False, "error": "Invalid transformation type"}
            )

        # Create audit trail
        audit_entry = processor.create_audit_trail(result, data.get("request_id", ""))

        return JsonResponse(
            {
                "success": result["success"],
                "transformation_result": result,
                "audit_entry": audit_entry,
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON data"})
    except Exception as e:
        logger.error(f"Error transforming document: {e}")
        return JsonResponse({"success": False, "error": str(e)})


@login_required
@user_passes_test(is_eadc_operator, login_url="/admin/login/")
def process_demo_document(request, demo_type):
    """
    Process demo document through EADC pipeline
    """
    try:
        processor = EADCProcessor()
        manager = EADCDocumentManager()

        # Get demo documents
        demo_documents = processor.get_demo_documents()

        if not demo_documents:
            messages.error(request, "No demo documents available")
            return render(
                request,
                "patient_data/eadc_processing_result.html",
                {"success": False, "error": "No demo documents found"},
            )

        # Use the first demo document
        demo_doc = demo_documents[0]

        # Process through EADC pipeline
        processing_result = manager.process_incoming_document(
            demo_doc["content"], demo_doc["type"], "GR"  # Greece as source country
        )

        # If processing was successful, save as clinical document
        if processing_result["success"] and processing_result["epsos_compliant"]:
            try:
                # Create a dummy patient for demo
                from datetime import date

                patient_data, created = PatientData.objects.get_or_create(
                    patient_id="DEMO_EADC_001",
                    defaults={
                        "given_name": "EADC",
                        "family_name": "Demo Patient",
                        "date_of_birth": date.today().strftime(
                            "%Y-%m-%d"
                        ),  # Use current date instead of hardcoded
                        "gender": "U",
                        "country_code": "GR",
                        "original_filename": "eadc_demo.properties",
                    },
                )

                # Create clinical document
                clinical_doc = ClinicalDocument.objects.create(
                    patient=patient_data,
                    document_type="PS",
                    document_format="EPSOS_CDA",
                    country_code="GR",
                    content=processing_result["processed_document"],
                    status="available",
                    metadata={
                        "source": "EADC_Demo",
                        "processing_id": processing_result["processing_id"],
                        "transformation_applied": processing_result[
                            "transformation_applied"
                        ],
                        "validation_status": processing_result["final_validation"],
                    },
                )

                processing_result["clinical_document_id"] = clinical_doc.id

            except Exception as e:
                logger.error(f"Error saving demo document: {e}")

        context = {
            "success": processing_result["success"],
            "processing_result": processing_result,
            "demo_document": demo_doc,
            "page_title": "EADC Demo Processing Result",
        }

        return render(request, "patient_data/eadc_processing_result.html", context)

    except Exception as e:
        logger.error(f"Error processing demo document: {e}")
        messages.error(request, f"Error processing demo document: {str(e)}")
        return render(
            request,
            "patient_data/eadc_processing_result.html",
            {"success": False, "error": str(e)},
        )


@login_required
@user_passes_test(is_eadc_operator, login_url="/admin/login/")
def eadc_patient_documents(request, patient_id):
    """
    Show EADC processing options for a specific patient
    """
    patient = get_object_or_404(PatientData, patient_id=patient_id)

    # Get existing clinical documents
    clinical_docs = ClinicalDocument.objects.filter(patient=patient)

    # Check if any documents need EADC processing
    processor = EADCProcessor()
    documents_analysis = []

    for doc in clinical_docs:
        if doc.content:
            validation = processor.validate_cda_document(doc.content, doc.document_type)
            documents_analysis.append(
                {
                    "document": doc,
                    "validation": validation,
                    "needs_transformation": not validation.get(
                        "epsos_compliant", False
                    ),
                }
            )

    context = {
        "patient": patient,
        "documents_analysis": documents_analysis,
        "supported_transformations": processor.supported_transformations,
        "page_title": f"EADC Processing - {patient.given_name} {patient.family_name}",
    }

    return render(request, "patient_data/eadc_patient_documents.html", context)


@require_http_methods(["POST"])
@login_required
@user_passes_test(is_eadc_admin, login_url="/admin/login/")
def process_patient_document(request, document_id):
    """
    Process a patient's clinical document through EADC
    """
    try:
        clinical_doc = get_object_or_404(ClinicalDocument, id=document_id)

        if not clinical_doc.content:
            return JsonResponse(
                {"success": False, "error": "Document has no content to process"}
            )

        manager = EADCDocumentManager()

        # Process the document
        processing_result = manager.process_incoming_document(
            clinical_doc.content, clinical_doc.document_type, clinical_doc.country_code
        )

        if processing_result["success"]:
            # Update the document with processed content
            clinical_doc.content = processing_result["processed_document"]
            clinical_doc.document_format = "EPSOS_CDA"
            clinical_doc.metadata.update(
                {
                    "eadc_processing_id": processing_result["processing_id"],
                    "transformation_applied": processing_result[
                        "transformation_applied"
                    ],
                    "epsos_compliant": processing_result["epsos_compliant"],
                    "processed_at": timezone.now().isoformat(),
                }
            )
            clinical_doc.save()

            messages.success(request, "Document successfully processed through EADC")
        else:
            messages.error(
                request,
                f'EADC processing failed: {processing_result.get("error", "Unknown error")}',
            )

        return JsonResponse(
            {
                "success": processing_result["success"],
                "processing_result": processing_result,
                "redirect_url": reverse(
                    "eadc_patient_documents", args=[clinical_doc.patient.patient_id]
                ),
            }
        )

    except Exception as e:
        logger.error(f"Error processing patient document through EADC: {e}")
        return JsonResponse({"success": False, "error": str(e)})


@login_required
@user_passes_test(is_eadc_operator, login_url="/admin/login/")
def eadc_transformation_history(request):
    """
    Show history of EADC transformations
    """
    # Get documents that have been processed through EADC
    eadc_documents = ClinicalDocument.objects.filter(
        metadata__has_key="eadc_processing_id"
    ).order_by("-created_at")

    context = {
        "eadc_documents": eadc_documents,
        "page_title": "EADC Transformation History",
    }

    return render(request, "patient_data/eadc_transformation_history.html", context)


@login_required
@user_passes_test(is_eadc_operator, login_url="/admin/login/")
def download_eadc_document(request, document_id, format_type="epsos"):
    """
    Download EADC processed document in specified format
    """
    try:
        clinical_doc = get_object_or_404(ClinicalDocument, id=document_id)

        if not clinical_doc.content:
            messages.error(request, "Document has no content available")
            return HttpResponse("No content available", status=404)

        processor = EADCProcessor()

        if format_type == "national":
            # Transform back to national format
            transformation_result = processor.transform_epsos_to_national(
                clinical_doc.content,
                clinical_doc.document_type,
                clinical_doc.country_code,
            )

            if transformation_result["success"]:
                content = transformation_result["national_document"]
                filename_suffix = f"_national_{clinical_doc.country_code}"
            else:
                content = clinical_doc.content
                filename_suffix = "_epsos"
        else:
            # Use epSOS format
            content = clinical_doc.content
            filename_suffix = "_epsos"

        # Create response
        response = HttpResponse(content, content_type="application/xml")
        filename = f"{clinical_doc.patient.patient_id}_{clinical_doc.document_type}{filename_suffix}.xml"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response

    except Exception as e:
        logger.error(f"Error downloading EADC document: {e}")
        messages.error(request, f"Error downloading document: {str(e)}")
        return HttpResponse("Error downloading document", status=500)
