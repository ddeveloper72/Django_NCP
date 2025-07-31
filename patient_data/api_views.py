"""
API Views for Patient Data
Dynamic ISM-based patient search functionality
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from ehealth_portal.models import Country, InternationalSearchMask
from patient_data.models import MemberState
import json
import logging

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def get_country_ism_config(request, country_code):
    """
    API endpoint to get ISM configuration for a specific country
    Returns the search fields and validation rules for dynamic form generation
    """
    try:
        # Get the country ISM configuration
        try:
            country = Country.objects.get(code=country_code.upper())
            ism = InternationalSearchMask.objects.get(country=country, is_active=True)
        except (Country.DoesNotExist, InternationalSearchMask.DoesNotExist):
            # Fallback to MemberState if ISM not configured
            member_state = get_object_or_404(
                MemberState, country_code=country_code.upper()
            )
            return JsonResponse(
                {
                    "success": True,
                    "country_code": country_code.upper(),
                    "country_name": member_state.country_name,
                    "has_ism": False,
                    "fields": [
                        {
                            "field_code": "patient_id",
                            "field_type": "text",
                            "label": "National Person Identifier",
                            "placeholder": "Enter patient identifier",
                            "help_text": "Patient identifier for this country",
                            "is_required": True,
                            "validation_pattern": "",
                            "error_message": "Please enter a valid patient identifier",
                            "field_order": 1,
                            "field_group": "identification",
                        },
                        {
                            "field_code": "birth_date",
                            "field_type": "date",
                            "label": "Date of Birth",
                            "placeholder": "yyyy/mm/dd",
                            "help_text": "Patient date of birth",
                            "is_required": True,
                            "validation_pattern": "",
                            "error_message": "Please enter a valid date of birth",
                            "field_order": 2,
                            "field_group": "identification",
                        },
                    ],
                }
            )

        # Build field configuration from ISM
        fields = []
        for field in ism.fields.all().order_by("field_order"):
            field_config = {
                "field_code": field.field_code,
                "field_type": field.field_type.html_input_type,
                "label": field.label,
                "placeholder": field.placeholder,
                "help_text": field.help_text,
                "is_required": field.is_required,
                "validation_pattern": field.validation_pattern or "",
                "error_message": field.error_message
                or f"Please enter a valid {field.label}",
                "field_order": field.field_order,
                "field_group": field.field_group or "identification",
            }

            # Add options for select fields
            if field.field_options:
                field_config["options"] = field.field_options

            fields.append(field_config)

        # Add ISM-specific metadata
        ism_metadata = ism.raw_ism_data.get("specifications", {})

        response_data = {
            "success": True,
            "country_code": country_code.upper(),
            "country_name": country.name,
            "has_ism": True,
            "ism_version": ism.mask_version,
            "ism_description": ism.mask_description,
            "fields": fields,
            "metadata": {
                "domain": ism_metadata.get("domain", ""),
                "scope": ism_metadata.get("scope", ""),
                "patient_id_format": ism_metadata.get("patient_id_format", ""),
                "requires_birth_date": ism_metadata.get("requires_birth_date", True),
            },
        }

        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"Error getting ISM config for {country_code}: {e}", exc_info=True)
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@require_http_methods(["GET"])
def validate_patient_id(request, country_code):
    """
    API endpoint to validate patient ID format for a specific country
    """
    patient_id = request.GET.get("patient_id", "").strip()

    if not patient_id:
        return JsonResponse(
            {"success": False, "valid": False, "message": "Patient ID is required"}
        )

    try:
        # Get country ISM configuration
        country = Country.objects.get(code=country_code.upper())
        ism = InternationalSearchMask.objects.get(country=country, is_active=True)

        # Get patient_id field configuration
        patient_id_field = ism.fields.filter(field_code="patient_id").first()

        if patient_id_field and patient_id_field.validation_pattern:
            import re

            pattern = patient_id_field.validation_pattern

            if re.match(f"^{pattern}$", patient_id):
                return JsonResponse(
                    {
                        "success": True,
                        "valid": True,
                        "message": f"Valid {patient_id_field.label}",
                        "formatted_value": patient_id,
                    }
                )
            else:
                return JsonResponse(
                    {
                        "success": True,
                        "valid": False,
                        "message": patient_id_field.error_message
                        or f"Invalid {patient_id_field.label} format",
                        "expected_format": patient_id_field.help_text,
                    }
                )
        else:
            # No specific validation pattern
            return JsonResponse(
                {
                    "success": True,
                    "valid": True,
                    "message": "Patient ID accepted",
                    "formatted_value": patient_id,
                }
            )

    except (Country.DoesNotExist, InternationalSearchMask.DoesNotExist):
        # Fallback validation for countries without ISM
        return JsonResponse(
            {
                "success": True,
                "valid": len(patient_id) > 0,
                "message": (
                    "Patient ID accepted"
                    if len(patient_id) > 0
                    else "Patient ID is required"
                ),
                "formatted_value": patient_id,
            }
        )
    except Exception as e:
        logger.error(
            f"Error validating patient ID for {country_code}: {e}", exc_info=True
        )
        return JsonResponse({"success": False, "error": str(e)}, status=500)
