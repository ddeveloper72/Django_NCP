"""
Enhanced CDA Translation Views
Views for handling translated CDA document display and processing
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from ..models import PatientData
from ..services.enhanced_cda_translation_service import EnhancedCDATranslationService
from translation_services.terminology_translator import (
    get_available_translation_languages,
)
from ..translation_utils import get_template_translations, detect_document_language

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def translate_cda_section_ajax(request):
    """
    AJAX endpoint for translating individual CDA sections on demand
    """
    try:
        data = json.loads(request.body)

        section_content = data.get("section_content", "")
        source_language = data.get("source_language", "fr")
        target_language = data.get("target_language", "en")
        section_id = data.get("section_id", "")

        if not section_content:
            return JsonResponse({"error": "No section content provided"}, status=400)

        # Initialize translation service
        translation_service = EnhancedCDATranslationService(
            target_language=target_language
        )

        # For section-level translation, we'll use the terminology translator
        from translation_services.terminology_translator import TerminologyTranslator

        terminology_translator = TerminologyTranslator(target_language=target_language)

        # Translate the section content
        translation_result = terminology_translator.translate_clinical_document(
            document_content=section_content, source_language=source_language
        )

        return JsonResponse(
            {
                "success": True,
                "translated_content": translation_result["content"],
                "translations_applied": translation_result["translations_applied"],
                "terminology_map": translation_result["terminology_map"],
                "section_id": section_id,
                "target_language": target_language,
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        logger.error(f"Error in AJAX section translation: {e}")
        return JsonResponse({"error": f"Translation failed: {str(e)}"}, status=500)


@login_required
def download_translated_cda(request, patient_id):
    """
    Download translated CDA document in various formats
    """
    try:
        patient_data = PatientData.objects.get(id=patient_id)
        match_data = request.session.get(f"patient_match_{patient_id}")

        if not match_data:
            messages.error(request, "No CDA document found for this patient.")
            return redirect("patient_data:patient_details", patient_id=patient_id)

        # Get translation parameters
        source_language = request.GET.get("source_language", "fr")
        target_language = request.GET.get("target_language", "en")
        format_type = request.GET.get("format", "json")  # json, xml, pdf

        # Initialize translation service
        translation_service = EnhancedCDATranslationService(
            target_language=target_language
        )

        # Translate the document
        translated_document = translation_service.translate_cda_document(
            xml_content=match_data["cda_content"], source_language=source_language
        )

        if format_type == "json":
            # Return JSON format
            response_data = {
                "patient_info": translated_document.patient_info,
                "header_info": translated_document.header_info,
                "sections": [
                    {
                        "section_id": section.section_id,
                        "title": section.title,
                        "original_title": section.original_title,
                        "content": section.content,
                        "original_content": section.original_content,
                        "translation_status": section.translation_status,
                        "codes": section.translated_codes,
                    }
                    for section in translated_document.sections
                ],
                "translation_summary": translated_document.translation_summary,
                "translation_quality": translated_document.translation_quality,
            }

            response = HttpResponse(
                json.dumps(response_data, indent=2), content_type="application/json"
            )
            response["Content-Disposition"] = (
                f'attachment; filename="translated_cda_{patient_id}_{target_language}.json"'
            )

        elif format_type == "xml":
            # Return translated XML
            response = HttpResponse(
                translated_document.translated_xml, content_type="application/xml"
            )
            response["Content-Disposition"] = (
                f'attachment; filename="translated_cda_{patient_id}_{target_language}.xml"'
            )

        elif format_type == "pdf":
            # Generate PDF (would need additional PDF generation service)
            # For now, return a placeholder
            response = HttpResponse(
                "PDF generation not yet implemented", content_type="text/plain"
            )
            response["Content-Disposition"] = (
                f'attachment; filename="translated_cda_{patient_id}_{target_language}.txt"'
            )

        else:
            return JsonResponse({"error": "Invalid format type"}, status=400)

        return response

    except PatientData.DoesNotExist:
        messages.error(request, "Patient data not found.")
        return redirect("patient_data:patient_data_form")
    except Exception as e:
        logger.error(f"Error downloading translated CDA: {e}")
        messages.error(request, f"Download failed: {str(e)}")
        return redirect("patient_data:patient_cda_view", patient_id=patient_id)


@login_required
def translation_api_status(request):
    """
    API endpoint to check translation service status and capabilities
    """
    try:
        # Check available languages
        available_languages = get_available_translation_languages()

        # Test terminology service
        from translation_services.terminology_translator import TerminologyTranslator

        translator = TerminologyTranslator()

        # Basic health check
        status = {
            "translation_service_available": True,
            "terminology_service_available": True,
            "available_languages": available_languages,
            "supported_formats": ["CDA", "FHIR"],
            "features": [
                "section_by_section_translation",
                "terminology_mapping",
                "multiple_output_formats",
                "translation_quality_assessment",
                "comparative_display",
            ],
        }

        return JsonResponse(status)

    except Exception as e:
        logger.error(f"Error checking translation API status: {e}")
        return JsonResponse(
            {"translation_service_available": False, "error": str(e)}, status=500
        )


@login_required
def batch_translate_documents(request):
    """
    View for batch translation of multiple CDA documents
    """
    if request.method == "POST":
        try:
            # Get list of patient IDs to translate
            patient_ids = request.POST.getlist("patient_ids")
            target_language = request.POST.get("target_language", "en")
            source_language = request.POST.get("source_language", "fr")

            translation_results = []

            for patient_id in patient_ids:
                try:
                    patient_data = PatientData.objects.get(id=patient_id)
                    match_data = request.session.get(f"patient_match_{patient_id}")

                    if match_data:
                        translation_service = EnhancedCDATranslationService(
                            target_language=target_language
                        )
                        translated_document = (
                            translation_service.translate_cda_document(
                                xml_content=match_data["cda_content"],
                                source_language=source_language,
                            )
                        )

                        translation_results.append(
                            {
                                "patient_id": patient_id,
                                "patient_name": f"{patient_data.given_name} {patient_data.family_name}",
                                "status": "success",
                                "quality": translated_document.translation_quality,
                                "sections_translated": translated_document.translation_summary[
                                    "translated_sections"
                                ],
                                "coverage": f"{translated_document.translation_summary['translation_coverage'] * 100:.1f}%",
                            }
                        )
                    else:
                        translation_results.append(
                            {
                                "patient_id": patient_id,
                                "status": "no_document",
                                "error": "No CDA document found",
                            }
                        )

                except PatientData.DoesNotExist:
                    translation_results.append(
                        {
                            "patient_id": patient_id,
                            "status": "not_found",
                            "error": "Patient not found",
                        }
                    )
                except Exception as e:
                    translation_results.append(
                        {"patient_id": patient_id, "status": "error", "error": str(e)}
                    )

            context = {
                "translation_results": translation_results,
                "target_language": target_language,
                "source_language": source_language,
            }

            return render(
                request,
                "patient_data/batch_translation_results.html",
                context,
                using="jinja2",
            )

        except Exception as e:
            logger.error(f"Error in batch translation: {e}")
            messages.error(request, f"Batch translation failed: {str(e)}")
            return redirect("patient_data:patient_search")

    else:
        # Show batch translation form
        return render(
            request, "patient_data/batch_translation_form.html", using="jinja2"
        )
