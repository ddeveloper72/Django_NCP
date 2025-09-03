"""
Django NCP Translation API Views

REST API endpoints for medical terminology translation services
implementing the Java NCP TSAM architecture.
"""

import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
from .core import TranslationServiceFactory, TSAMError

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class TranslateConceptView(View):
    """
    API endpoint for translating individual medical concepts

    POST /api/translation/concept/
    {
        "source_code": "I25.9",
        "source_system": "ICD-10",
        "target_language": "en-GB",
        "target_system": "epSOS"
    }
    """

    def post(self, request):
        try:
            data = json.loads(request.body)

            # Validate required parameters
            required_fields = ["source_code", "source_system", "target_language"]
            for field in required_fields:
                if field not in data:
                    return JsonResponse(
                        {"error": f"Missing required field: {field}"}, status=400
                    )

            source_code = data["source_code"]
            source_system = data["source_system"]
            target_language = data["target_language"]
            target_system = data.get("target_system", "epSOS")

            # Get terminology service
            terminology_service = TranslationServiceFactory.get_terminology_service()

            # Translate concept
            translated_term, errors = terminology_service.translate_concept(
                source_code, source_system, target_language, target_system
            )

            response_data = {
                "source_code": source_code,
                "source_system": source_system,
                "target_language": target_language,
                "target_system": target_system,
                "translated_term": translated_term,
                "errors": [error.to_dict() for error in errors],
                "status": "success" if translated_term else "not_found",
            }

            return JsonResponse(response_data)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.error(f"Error translating concept: {str(e)}")
            return JsonResponse({"error": "Internal server error"}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
class TranslateFHIRView(View):
    """
    API endpoint for translating FHIR Bundle documents

    POST /api/translation/fhir/
    {
        "fhir_bundle": { ... FHIR Bundle JSON ... },
        "target_language": "en-GB"
    }
    """

    def post(self, request):
        try:
            data = json.loads(request.body)

            # Validate required parameters
            if "fhir_bundle" not in data:
                return JsonResponse({"error": "Missing fhir_bundle"}, status=400)
            if "target_language" not in data:
                return JsonResponse({"error": "Missing target_language"}, status=400)

            fhir_bundle = data["fhir_bundle"]
            target_language = data["target_language"]

            # Get FHIR translation service
            fhir_service = TranslationServiceFactory.get_fhir_translation_service()

            # Translate FHIR bundle
            translation_response = fhir_service.translate_fhir_bundle(
                fhir_bundle, target_language
            )

            return JsonResponse(translation_response.to_dict())

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.error(f"Error translating FHIR document: {str(e)}")
            return JsonResponse({"error": "Internal server error"}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
class TranslateCDAView(View):
    """
    API endpoint for translating CDA documents

    POST /api/translation/cda/
    {
        "cda_document": "<ClinicalDocument>...</ClinicalDocument>",
        "target_language": "en-GB"
    }
    """

    def post(self, request):
        try:
            data = json.loads(request.body)

            # Validate required parameters
            if "cda_document" not in data:
                return JsonResponse({"error": "Missing cda_document"}, status=400)
            if "target_language" not in data:
                return JsonResponse({"error": "Missing target_language"}, status=400)

            cda_document = data["cda_document"]
            target_language = data["target_language"]

            # Get CDA translation service
            cda_service = TranslationServiceFactory.get_cda_translation_service()

            # Translate CDA document
            translation_response = cda_service.translate_cda_document(
                cda_document, target_language
            )

            return JsonResponse(translation_response.to_dict())

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.error(f"Error translating CDA document: {str(e)}")
            return JsonResponse({"error": "Internal server error"}, status=500)


@require_http_methods(["GET"])
def terminology_systems_view(request):
    """
    Get available terminology systems

    GET /api/translation/terminology-systems/
    """
    try:
        from translation_manager.models import TerminologySystem

        systems = TerminologySystem.objects.filter(is_active=True).values(
            "name", "version", "description", "oid", "url"
        )

        return JsonResponse(
            {"terminology_systems": list(systems), "count": len(systems)}
        )

    except Exception as e:
        logger.error(f"Error getting terminology systems: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)


@require_http_methods(["GET"])
def supported_languages_view(request):
    """
    Get supported languages for translation

    GET /api/translation/languages/
    """
    try:
        from translation_manager.models import LanguageTranslation

        languages = (
            LanguageTranslation.objects.filter(is_active=True)
            .values_list("language_code", flat=True)
            .distinct()
        )

        return JsonResponse(
            {"supported_languages": list(languages), "count": len(languages)}
        )

    except Exception as e:
        logger.error(f"Error getting supported languages: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)


@require_http_methods(["GET"])
def translation_status_view(request):
    """
    Get translation service status and statistics

    GET /api/translation/status/
    """
    try:
        from translation_manager.models import (
            TerminologySystem,
            ConceptMapping,
            LanguageTranslation,
        )

        status_data = {
            "service_status": "operational",
            "terminology_systems": TerminologySystem.objects.filter(
                is_active=True
            ).count(),
            "concept_mappings": ConceptMapping.objects.filter(is_active=True).count(),
            "language_translations": LanguageTranslation.objects.filter(
                is_active=True
            ).count(),
            "supported_languages": LanguageTranslation.objects.filter(is_active=True)
            .values_list("language_code", flat=True)
            .distinct()
            .count(),
            "cache_status": "enabled" if hasattr(settings, "CACHES") else "disabled",
        }

        return JsonResponse(status_data)

    except Exception as e:
        logger.error(f"Error getting translation status: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)
