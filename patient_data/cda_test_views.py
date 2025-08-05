"""
CDA Test Data Management Views

Views for managing and displaying available test CDA documents
for demonstration purposes.
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .services.cda_document_index import get_cda_indexer
import logging

logger = logging.getLogger(__name__)


def test_patients_view(request):
    """Display all available test patients from CDA index"""

    try:
        indexer = get_cda_indexer()
        patients = indexer.get_all_patients()

        # Group patients by country for better organization
        patients_by_country = {}
        for patient in patients:
            country = patient["country_code"]
            if country not in patients_by_country:
                patients_by_country[country] = []
            patients_by_country[country].append(patient)

        # Sort countries and patients
        for country in patients_by_country:
            patients_by_country[country].sort(
                key=lambda p: f"{p['family_name']}, {p['given_name']}"
            )

        context = {
            "patients_by_country": dict(sorted(patients_by_country.items())),
            "total_patients": len(patients),
            "total_countries": len(patients_by_country),
        }

        return render(
            request, "patient_data/test_patients.html", context, using="jinja2"
        )

    except Exception as e:
        logger.error(f"Error loading test patients: {e}")
        messages.error(request, "Error loading test patient data.")
        return render(
            request,
            "patient_data/test_patients.html",
            {
                "patients_by_country": {},
                "total_patients": 0,
                "total_countries": 0,
            },
            using="jinja2",
        )


@require_http_methods(["POST"])
def refresh_cda_index_view(request):
    """AJAX endpoint to refresh the CDA index"""

    try:
        indexer = get_cda_indexer()
        index = indexer.refresh_index()

        total_patients = len(index)
        total_documents = sum(len(docs) for docs in index.values())

        return JsonResponse(
            {
                "success": True,
                "message": f"Index refreshed: {total_patients} patients, {total_documents} documents",
                "total_patients": total_patients,
                "total_documents": total_documents,
            }
        )

    except Exception as e:
        logger.error(f"Error refreshing CDA index: {e}")
        return JsonResponse(
            {
                "success": False,
                "message": f"Error refreshing index: {str(e)}",
            }
        )
