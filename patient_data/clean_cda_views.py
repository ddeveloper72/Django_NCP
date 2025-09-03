#!/usr/bin/env python3
"""
Clean CDA Views - Simple views using the new clinical data extraction system
Keeps templates simple by moving logic to Python services
"""

import os
import sys
import django
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from ncp_gateway.models import Patient
from cda_display_service import CDADisplayService

logger = logging.getLogger(__name__)


@login_required
def clean_patient_cda_view(request, patient_id):
    """
    Clean CDA view using the new clinical data extraction system

    Simple template logic - all complex processing done in Python services
    """

    try:
        # Initialize the display service
        display_service = CDADisplayService()

        # Get patient data
        try:
            patient = get_object_or_404(Patient, id=patient_id)
        except Exception as e:
            messages.error(request, f"Patient not found: {patient_id}")
            return render(
                request,
                "patient_data/error.html",
                {"error_message": f"Patient not found: {patient_id}"},
            )

        # Try to extract structured clinical data
        clinical_data = display_service.extract_patient_clinical_data(patient_id)

        if clinical_data:
            # Success - we have structured clinical data
            context = {
                "patient": patient,
                "clinical_data": clinical_data,
                "sections": clinical_data["sections"],
                "section_tables": clinical_data.get("section_tables", {}),
                "extraction_stats": clinical_data.get("stats", {}),
                "is_structured_cda": True,
                "page_title": f"Clinical Data - {patient.first_name} {patient.last_name}",
                "country_display": (
                    str(patient.country_of_origin)
                    if patient.country_of_origin
                    else "Unknown"
                ),
                "has_clinical_data": len(clinical_data["sections"]) > 0,
            }

            # Generate section summaries for easy template access
            section_summary = {}
            for section in clinical_data["sections"]:
                section_type = section["section_type"]
                section_summary[section_type] = {
                    "count": section["entry_count"],
                    "title": section["display_name"],
                    "has_entries": section["entry_count"] > 0,
                }

            context["section_summary"] = section_summary

            logger.info(
                f"Successfully extracted {len(clinical_data['sections'])} clinical sections for patient {patient_id}"
            )

        else:
            # No structured data available - show basic patient info
            context = {
                "patient": patient,
                "clinical_data": None,
                "sections": [],
                "section_tables": {},
                "extraction_stats": {},
                "is_structured_cda": False,
                "page_title": f"Patient Information - {patient.first_name} {patient.last_name}",
                "country_display": (
                    str(patient.country_of_origin)
                    if patient.country_of_origin
                    else "Unknown"
                ),
                "has_clinical_data": False,
                "section_summary": {},
            }

            messages.info(
                request,
                f"No structured clinical data available for {patient.first_name} {patient.last_name}. "
                "Displaying basic patient information only.",
            )

            logger.info(
                f"No structured clinical data available for patient {patient_id}"
            )

        # Render the clean template
        return render(
            request,
            "jinja2/patient_data/clean_cda_document.html",
            context,
            using="jinja2",
        )

    except Exception as e:
        logger.error(f"Error in clean_patient_cda_view for patient {patient_id}: {e}")
        messages.error(request, f"Error loading clinical data: {str(e)}")
        return render(
            request,
            "patient_data/error.html",
            {
                "error_message": f"Error loading clinical data: {str(e)}",
                "patient_id": patient_id,
            },
        )


def _get_country_display(country_code):
    """Get human-readable country name from code"""
    country_map = {
        "IE": "Ireland",
        "PT": "Portugal",
        "DE": "Germany",
        "FR": "France",
        "IT": "Italy",
        "ES": "Spain",
        "NL": "Netherlands",
        "BE": "Belgium",
        "AT": "Austria",
        "LU": "Luxembourg",
        "PL": "Poland",
        "CZ": "Czech Republic",
        "SK": "Slovakia",
        "HU": "Hungary",
        "SI": "Slovenia",
        "HR": "Croatia",
        "RO": "Romania",
        "BG": "Bulgaria",
        "LT": "Lithuania",
        "LV": "Latvia",
        "EE": "Estonia",
        "DK": "Denmark",
        "FI": "Finland",
        "SE": "Sweden",
        "GR": "Greece",
        "CY": "Cyprus",
        "MT": "Malta",
    }

    return country_map.get(country_code, country_code)


# For testing the clean view
if __name__ == "__main__":
    print("🧪 Testing Clean CDA Views")
    print("This module provides simple CDA views using clinical data extraction")
    print("Use: python manage.py runserver")
    print("Then navigate to: /patient_data/clean/<patient_id>/")
