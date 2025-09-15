"""
Enhanced CDA Document View with Translation
Integrates with the enhanced CDA translation service for comprehensive document viewing
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
import json
import xml.etree.ElementTree as ET
import logging

from ..models import PatientData
from ..services.enhanced_cda_translation_service import EnhancedCDATranslationService
from ..services.enhanced_cda_processor import EnhancedCDAProcessor
from translation_services.core import TranslationServiceFactory

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
class EnhancedCDADocumentView(View):
    """Enhanced CDA document viewer with translation capabilities"""

    def get(self, request, patient_id):
        """Display CDA document with translation options"""
        try:
            # Get patient data
            patient_data = get_object_or_404(PatientData, id=patient_id)

            # Get CDA document from session or database
            cda_document = self._get_cda_document(request, patient_data)
            if not cda_document:
                messages.error(request, "No CDA document found for this patient.")
                return render(
                    request,
                    "patient_data/cda_not_found.html",
                    {"patient_data": patient_data},
                )

            # Get translation language preference
            target_language = request.GET.get("lang", "en")

            # Initialize translation service
            translation_service = EnhancedCDATranslationService(
                target_language=target_language
            )

            # Detect source language
            source_language = self._detect_source_language(cda_document)

            # Translate the document
            translated_document = translation_service.translate_cda_document(
                cda_document, source_language
            )

            # Process CDA for comprehensive clinical data extraction
            cda_processor = EnhancedCDAProcessor()
            clinical_sections = cda_processor.process_clinical_sections(
                cda_document, source_language
            )

            # Extract comprehensive patient summary including extended header data
            comprehensive_summary = cda_processor.get_comprehensive_patient_summary(
                cda_document
            )

            # Ensure the comprehensive summary is JSON serializable by converting any non-serializable objects
            def make_serializable(obj):
                """Recursively convert objects to JSON-serializable format"""
                if hasattr(obj, "__dict__"):
                    # Convert custom objects to dictionaries
                    return {
                        key: make_serializable(value)
                        for key, value in vars(obj).items()
                    }
                elif isinstance(obj, dict):
                    return {key: make_serializable(value) for key, value in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [make_serializable(item) for item in obj]
                else:
                    return obj

            # Make comprehensive summary JSON serializable
            serializable_summary = make_serializable(comprehensive_summary)

            # Extract medications specifically for enhanced display and create clinical tables
            medications = []
            if clinical_sections and "sections" in clinical_sections:
                # Import the clinical table creation function
                from ..views import create_clinical_table

                for section in clinical_sections["sections"]:
                    # Create clinical table structure for proper display
                    if "table_data" in section and section["table_data"]:
                        section["clinical_table"] = create_clinical_table(
                            section["table_data"],
                            section.get("section_code", ""),
                            section.get("title", "Clinical Data"),
                        )

                    # Extract medications for the separate comprehensive section
                    if "structured_data" in section:
                        section_title = section.get("title", {})
                        if isinstance(section_title, dict):
                            title_text = section_title.get("original", "")
                        else:
                            title_text = str(section_title)

                        if "medication" in title_text.lower():
                            medications.extend(section["structured_data"])

            # Prepare context for template
            context = {
                "patient_data": patient_data,
                "translated_document": translated_document,
                "clinical_sections": clinical_sections,
                "medications": medications,
                "source_language": source_language,
                "target_language": target_language,
                "available_languages": ["en", "fr", "de", "es", "it"],
                "translation_enabled": target_language != source_language,
                "show_original": request.GET.get("show_original", "false") == "true",
                "view_mode": request.GET.get(
                    "view", "side-by-side"
                ),  # 'side-by-side', 'toggle', 'translated-only'
                # Extended patient data for Extended Patient Information tabs
                "patient_extended_data": serializable_summary,
                "administrative_data": serializable_summary,
                # Additional context for template compatibility
                "patient_id": patient_id,
                "has_extended_data": bool(serializable_summary),
            }

            return render(
                request,
                "patient_data/enhanced_patient_cda.html",
                context,
            )

        except Exception as e:
            logger.error(f"Error in enhanced CDA view for patient {patient_id}: {e}")
            messages.error(request, f"Error loading CDA document: {str(e)}")
            return render(
                request,
                "patient_data/error.html",
                {"error_message": str(e), "patient_id": patient_id},
            )

    def _get_cda_document(self, request, patient_data):
        """Retrieve CDA document from session or database"""
        # Try to get from session first using the same key pattern as patient views
        match_data = request.session.get(f"patient_match_{patient_data.id}")

        if match_data and "cda_content" in match_data:
            return match_data["cda_content"]

        # Fallback: try old session structure for backwards compatibility
        cda_data = request.session.get("cda_documents", {})
        patient_cda = cda_data.get(str(patient_data.id))

        if patient_cda and "xml_content" in patient_cda:
            return patient_cda["xml_content"]

        # No CDA document found
        logger.warning(
            f"No CDA document found for patient {patient_data.id} in session"
        )
        return None

    def _detect_source_language(self, cda_document):
        """Detect the source language of the CDA document"""
        try:
            root = ET.fromstring(cda_document)

            # Check xml:lang attribute
            lang_attr = root.get("{http://www.w3.org/XML/1998/namespace}lang")
            if lang_attr:
                return lang_attr.lower()

            # Check html lang attribute for XSLT output
            if root.tag.lower() == "html":
                lang_attr = root.get("lang") or root.get(
                    "{http://www.w3.org/XML/1998/namespace}lang"
                )
                if lang_attr:
                    return lang_attr.lower()

            # Default assumption based on content analysis
            # You could implement more sophisticated language detection here
            return "fr"  # Default for European context

        except Exception as e:
            logger.warning(f"Could not detect source language: {e}")
            return "fr"


@login_required
@require_http_methods(["POST"])
def toggle_translation_view(request, patient_id):
    """AJAX endpoint to toggle between translation view modes"""
    try:
        view_mode = request.POST.get("view_mode", "side-by-side")
        show_original = request.POST.get("show_original", "false") == "true"
        target_language = request.POST.get("target_language", "en")

        # Store preferences in session
        if "cda_preferences" not in request.session:
            request.session["cda_preferences"] = {}

        request.session["cda_preferences"].update(
            {
                "view_mode": view_mode,
                "show_original": show_original,
                "target_language": target_language,
            }
        )
        request.session.modified = True

        return JsonResponse(
            {
                "status": "success",
                "view_mode": view_mode,
                "show_original": show_original,
                "target_language": target_language,
            }
        )

    except Exception as e:
        logger.error(f"Error toggling translation view: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@login_required
@require_http_methods(["GET"])
def get_section_translation(request, patient_id, section_id):
    """AJAX endpoint to get individual section translation"""
    try:
        patient_data = get_object_or_404(PatientData, id=patient_id)
        cda_document = (
            request.session.get("cda_documents", {})
            .get(str(patient_id), {})
            .get("xml_content")
        )

        if not cda_document:
            return JsonResponse(
                {"status": "error", "message": "CDA document not found"}, status=404
            )

        target_language = request.GET.get("lang", "en")
        translation_service = EnhancedCDATranslationService(
            target_language=target_language
        )

        # Get the specific section (this would need to be implemented in the service)
        # For now, return a placeholder response
        return JsonResponse(
            {
                "status": "success",
                "section_id": section_id,
                "translation": f"[Translation for section {section_id}]",
                "quality": "good",
            }
        )

    except Exception as e:
        logger.error(f"Error getting section translation: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@login_required
@require_http_methods(["GET"])
def export_translated_cda(request, patient_id):
    """Export translated CDA document in various formats"""
    try:
        format_type = request.GET.get("format", "html")  # html, xml, pdf
        target_language = request.GET.get("lang", "en")

        patient_data = get_object_or_404(PatientData, id=patient_id)
        cda_document = (
            request.session.get("cda_documents", {})
            .get(str(patient_id), {})
            .get("xml_content")
        )

        if not cda_document:
            return HttpResponse("CDA document not found", status=404)

        translation_service = EnhancedCDATranslationService(
            target_language=target_language
        )
        source_language = "fr"  # Could be detected

        translated_document = translation_service.translate_cda_document(
            cda_document, source_language
        )

        if format_type == "xml":
            response = HttpResponse(
                translated_document.translated_xml, content_type="application/xml"
            )
            response["Content-Disposition"] = (
                f'attachment; filename="cda_translated_{patient_id}_{target_language}.xml"'
            )
            return response

        elif format_type == "html":
            context = {
                "translated_document": translated_document,
                "patient_data": patient_data,
                "target_language": target_language,
                "export_mode": True,
            }
            html_content = render(
                request, "patient_data/cda_export.html", context
            ).content

            response = HttpResponse(html_content, content_type="text/html")
            response["Content-Disposition"] = (
                f'attachment; filename="cda_translated_{patient_id}_{target_language}.html"'
            )
            return response

        else:
            return HttpResponse("Unsupported format", status=400)

    except Exception as e:
        logger.error(f"Error exporting translated CDA: {e}")
        return HttpResponse(f"Export error: {str(e)}", status=500)
