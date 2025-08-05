"""
Debug views for testing CDA indexing system
"""

from django.http import JsonResponse
from django.shortcuts import render
from patient_data.services.cda_document_index import get_cda_indexer
from patient_data.services.patient_search_service import (
    PatientCredentials,
    EUPatientSearchService,
)
import logging

logger = logging.getLogger(__name__)


def debug_cda_index(request):
    """Debug view to test CDA indexing system"""

    try:
        # Test the indexer
        indexer = get_cda_indexer()
        index = indexer.build_index()

        # Get patient list
        patients = indexer.get_all_patients()

        # Test search for Mario PINO
        search_service = EUPatientSearchService()
        mario_credentials = PatientCredentials(
            country_code="IT", patient_id="NCPNPH80A01H501K"
        )
        mario_matches = search_service.search_patient(mario_credentials)

        # Test search for a non-existent patient
        fake_credentials = PatientCredentials(country_code="IT", patient_id="FAKE123")
        fake_matches = search_service.search_patient(fake_credentials)

        debug_info = {
            "index_status": "success",
            "total_patients_in_index": len(index),
            "patients_summary": patients[:5],  # First 5 patients
            "mario_pino_test": {
                "found": len(mario_matches) > 0,
                "match_count": len(mario_matches),
                "patient_name": (
                    f"{mario_matches[0].given_name} {mario_matches[0].family_name}"
                    if mario_matches
                    else None
                ),
                "has_l1": mario_matches[0].has_l1_cda() if mario_matches else False,
                "has_l3": mario_matches[0].has_l3_cda() if mario_matches else False,
            },
            "fake_patient_test": {
                "found": len(fake_matches) > 0,
                "match_count": len(fake_matches),
            },
        }

        return JsonResponse(debug_info, indent=2)

    except Exception as e:
        logger.error(f"Debug CDA index error: {e}")
        return JsonResponse({"index_status": "error", "error": str(e)})
