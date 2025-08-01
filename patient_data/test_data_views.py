"""
EU Test Data Management Views
Views for managing and displaying EU member state test data
"""

import json
import base64
import logging
from pathlib import Path
from typing import Dict, Any, List
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q, Count

from .models import PatientData, MemberState
from .clinical_models import ClinicalDocument

# from .services.clinical_pdf_service import (  # Temporarily disabled
#     ClinicalDocumentPDFService,
#     TranslatedDocumentRenderer,
#     TestDataManager,
# )

# Import translation services
try:
    from translation_services.terminology_translator import (
        TerminologyTranslator,
        get_available_translation_languages,
    )

    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False

logger = logging.getLogger(__name__)


@staff_member_required
def test_data_dashboard(request):
    """Dashboard for EU test data management"""
    try:
        test_manager = TestDataManager()

        # Get test data statistics
        stats = {
            "total_patients": PatientData.objects.filter(source="EU_TEST_DATA").count(),
            "countries": PatientData.objects.filter(source="EU_TEST_DATA")
            .values("member_state__country_code")
            .annotate(count=Count("id"))
            .order_by("member_state__country_code"),
            "documents_with_pdf": ClinicalDocument.objects.filter(
                patient_data__source="EU_TEST_DATA", has_embedded_pdf=True
            ).count(),
            "total_documents": ClinicalDocument.objects.filter(
                patient_data__source="EU_TEST_DATA"
            ).count(),
        }

        # Get external test data directory info
        external_path = getattr(settings, "EU_TEST_DATA_PATH", None)
        external_stats = None
        if external_path:
            try:
                external_stats = test_manager.get_external_directory_stats(
                    external_path
                )
            except Exception as e:
                logger.warning(f"Could not read external test data directory: {e}")
                messages.warning(
                    request, f"Could not access external test data directory: {e}"
                )

        # Get recent imports
        recent_patients = PatientData.objects.filter(source="EU_TEST_DATA").order_by(
            "-created_at"
        )[:10]

        context = {
            "stats": stats,
            "external_stats": external_stats,
            "external_path": external_path,
            "recent_patients": recent_patients,
            "translation_available": TRANSLATION_AVAILABLE,
        }

        return render(request, "admin/patient_data/test_data_dashboard.html", context)

    except Exception as e:
        logger.error(f"Error loading test data dashboard: {e}")
        messages.error(request, f"Error loading dashboard: {e}")
        return redirect("admin:index")


@staff_member_required
def test_data_list(request):
    """List all EU test data patients with filtering"""
    try:
        # Base queryset
        patients = PatientData.objects.filter(source="EU_TEST_DATA")

        # Filtering
        country_filter = request.GET.get("country")
        has_pdf_filter = request.GET.get("has_pdf")
        search_query = request.GET.get("search")

        if country_filter:
            patients = patients.filter(member_state__country_code=country_filter)

        if has_pdf_filter == "true":
            patients = patients.filter(
                clinicaldocument__has_embedded_pdf=True
            ).distinct()
        elif has_pdf_filter == "false":
            patients = patients.exclude(
                clinicaldocument__has_embedded_pdf=True
            ).distinct()

        if search_query:
            patients = patients.filter(
                Q(patient_id__icontains=search_query)
                | Q(given_name__icontains=search_query)
                | Q(family_name__icontains=search_query)
                | Q(member_state__country_name__icontains=search_query)
            )

        # Ordering
        patients = patients.order_by("-created_at")

        # Pagination
        paginator = Paginator(patients, 25)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        # Get available countries for filter
        countries = (
            PatientData.objects.filter(source="EU_TEST_DATA")
            .values_list("member_state__country_code", "member_state__country_name")
            .distinct()
            .order_by("member_state__country_code")
        )

        context = {
            "page_obj": page_obj,
            "countries": countries,
            "current_filters": {
                "country": country_filter,
                "has_pdf": has_pdf_filter,
                "search": search_query,
            },
            "total_count": patients.count(),
        }

        return render(request, "admin/patient_data/test_data_list.html", context)

    except Exception as e:
        logger.error(f"Error loading test data list: {e}")
        messages.error(request, f"Error loading test data: {e}")
        return redirect("admin:patient_data_test_data_dashboard")


@staff_member_required
def test_data_patient_view(request, patient_data_id):
    """View detailed information for a test data patient"""
    try:
        patient_data = get_object_or_404(
            PatientData.objects.select_related("member_state"),
            id=patient_data_id,
            source="EU_TEST_DATA",
        )

        # Get all clinical documents for this patient
        documents = ClinicalDocument.objects.filter(patient_data=patient_data).order_by(
            "-created_at"
        )

        # Get translation languages if available
        available_languages = []
        if TRANSLATION_AVAILABLE:
            available_languages = get_available_translation_languages()

        context = {
            "patient_data": patient_data,
            "documents": documents,
            "translation_available": TRANSLATION_AVAILABLE,
            "available_languages": available_languages,
        }

        return render(
            request, "admin/patient_data/test_data_patient_view.html", context
        )

    except Exception as e:
        logger.error(f"Error viewing test data patient: {e}")
        messages.error(request, f"Error loading patient data: {e}")
        return redirect("admin:patient_data_test_data_list")


@staff_member_required
def test_data_document_view(request, document_id):
    """View a clinical document with translation options"""
    try:
        document = get_object_or_404(
            ClinicalDocument.objects.select_related("patient_data__member_state"),
            id=document_id,
            patient_data__source="EU_TEST_DATA",
        )

        # Get translation parameters
        target_language = request.GET.get("translate_to")
        source_language = request.GET.get("source_lang", "en")

        # Initialize services
        pdf_service = ClinicalDocumentPDFService()
        renderer = TranslatedDocumentRenderer()

        # Process document
        rendered_html = None
        translation_result = None
        translation_summary = None
        available_languages = []

        if TRANSLATION_AVAILABLE:
            available_languages = get_available_translation_languages()

        try:
            # Render document content
            rendered_html = pdf_service.render_document_content(
                document.content, document.document_type
            )

            # Apply translation if requested
            if (
                target_language
                and TRANSLATION_AVAILABLE
                and target_language != source_language
            ):
                translator = TerminologyTranslator(target_language=target_language)
                translation_result = translator.translate_clinical_document(
                    document_content=document.content,
                    source_language=source_language,
                )

                if translation_result["translations_applied"] > 0:
                    # Re-render with translated content
                    rendered_html = pdf_service.render_document_content(
                        translation_result["content"], document.document_type
                    )

                translation_summary = translator.get_translation_summary(
                    translation_result
                )

        except Exception as e:
            logger.error(f"Error processing document: {e}")
            rendered_html = (
                f"<div class='alert alert-danger'>Error processing document: {e}</div>"
            )

        context = {
            "document": document,
            "rendered_html": rendered_html,
            "can_download_pdf": document.has_embedded_pdf
            and document.embedded_pdf_base64,
            "translation_available": TRANSLATION_AVAILABLE,
            "available_languages": available_languages,
            "current_target_language": target_language,
            "source_language": source_language,
            "translation_result": translation_result,
            "translation_summary": translation_summary,
        }

        return render(
            request, "admin/patient_data/test_data_document_view.html", context
        )

    except Exception as e:
        logger.error(f"Error viewing test data document: {e}")
        messages.error(request, f"Error loading document: {e}")
        return redirect("admin:patient_data_test_data_list")


@staff_member_required
def test_data_document_pdf(request, document_id):
    """Download PDF from test data clinical document"""
    try:
        document = get_object_or_404(
            ClinicalDocument, id=document_id, patient_data__source="EU_TEST_DATA"
        )

        if not document.has_embedded_pdf or not document.embedded_pdf_base64:
            raise Http404("PDF not available for this document")

        # Decode PDF
        try:
            pdf_data = base64.b64decode(document.embedded_pdf_base64)
        except Exception as e:
            logger.error(f"Error decoding PDF: {e}")
            messages.error(request, "Error extracting PDF from document")
            return redirect("admin:patient_data_test_data_document_view", document_id)

        # Create response
        response = HttpResponse(pdf_data, content_type="application/pdf")
        filename = f"test_data_{document.patient_data.patient_identifier.home_member_state.country_code}_{document.patient_data.patient_id}_{document.document_type}.pdf"

        # Check if this is a download or preview request
        if request.GET.get("preview") == "true":
            response["Content-Disposition"] = f'inline; filename="{filename}"'
        else:
            response["Content-Disposition"] = f'attachment; filename="{filename}"'

        logger.info(f"Served PDF for test document {document.id}")
        return response

    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error serving test data PDF: {e}")
        messages.error(request, f"Error downloading PDF: {e}")
        return redirect("admin:patient_data_test_data_list")


@staff_member_required
def test_data_translated_view(request, document_id):
    """View translated version of test data document"""
    try:
        document = get_object_or_404(
            ClinicalDocument.objects.select_related("patient_data__member_state"),
            id=document_id,
            patient_data__source="EU_TEST_DATA",
        )

        target_language = request.GET.get("language", "en")
        source_language = request.GET.get("source_lang", "en")

        if not TRANSLATION_AVAILABLE:
            messages.error(request, "Translation services not available")
            return redirect("admin:patient_data_test_data_document_view", document_id)

        try:
            # Initialize renderer
            renderer = TranslatedDocumentRenderer()

            # Render translated document
            rendered_content = renderer.render_translated_document(
                document=document,
                target_language=target_language,
                source_language=source_language,
            )

            context = {
                "document": document,
                "rendered_content": rendered_content,
                "target_language": target_language,
                "source_language": source_language,
                "available_languages": get_available_translation_languages(),
            }

            return render(
                request, "admin/patient_data/test_data_translated_view.html", context
            )

        except Exception as e:
            logger.error(f"Error rendering translated document: {e}")
            messages.error(request, f"Translation failed: {e}")
            return redirect("admin:patient_data_test_data_document_view", document_id)

    except Exception as e:
        logger.error(f"Error viewing translated test data: {e}")
        messages.error(request, f"Error loading translated document: {e}")
        return redirect("admin:patient_data_test_data_list")


@staff_member_required
@require_http_methods(["POST"])
def import_external_test_data(request):
    """Import test data from external directory"""
    try:
        external_path = getattr(settings, "EU_TEST_DATA_PATH", None)
        if not external_path:
            messages.error(request, "EU test data path not configured")
            return redirect("admin:patient_data_test_data_dashboard")

        # Get import options
        dry_run = request.POST.get("dry_run") == "true"
        force_reimport = request.POST.get("force_reimport") == "true"

        # Initialize test manager
        test_manager = TestDataManager()

        # Run import (this would typically be done via management command in background)
        try:
            from django.core.management import call_command
            from io import StringIO

            # Capture command output
            out = StringIO()

            command_args = [external_path]
            command_options = {
                "dry_run": dry_run,
                "force_reimport": force_reimport,
                "stdout": out,
                "verbosity": 2,
            }

            call_command("import_eu_test_data", *command_args, **command_options)

            output = out.getvalue()

            if dry_run:
                messages.info(request, f"Dry run completed successfully. {output}")
            else:
                messages.success(request, f"Import completed successfully. {output}")

        except Exception as e:
            logger.error(f"Error running import command: {e}")
            messages.error(request, f"Import failed: {e}")

        return redirect("admin:patient_data_test_data_dashboard")

    except Exception as e:
        logger.error(f"Error importing external test data: {e}")
        messages.error(request, f"Import error: {e}")
        return redirect("admin:patient_data_test_data_dashboard")


@staff_member_required
@require_http_methods(["GET"])
def test_data_stats_api(request):
    """API endpoint for test data statistics"""
    try:
        # Get basic stats
        stats = {
            "total_patients": PatientData.objects.filter(source="EU_TEST_DATA").count(),
            "total_documents": ClinicalDocument.objects.filter(
                patient_data__source="EU_TEST_DATA"
            ).count(),
            "documents_with_pdf": ClinicalDocument.objects.filter(
                patient_data__source="EU_TEST_DATA", has_embedded_pdf=True
            ).count(),
        }

        # Get country breakdown
        country_stats = list(
            PatientData.objects.filter(source="EU_TEST_DATA")
            .values("member_state__country_code", "member_state__country_name")
            .annotate(patient_count=Count("id"))
            .order_by("member_state__country_code")
        )

        stats["countries"] = country_stats

        return JsonResponse(stats)

    except Exception as e:
        logger.error(f"Error getting test data stats: {e}")
        return JsonResponse({"error": str(e)}, status=500)
