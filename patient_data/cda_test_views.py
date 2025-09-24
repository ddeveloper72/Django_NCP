"""
CDA Test Data Management Views

Views for managing and displaying available test CDA documents
for demonstration purposes.
"""

import logging

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .services.cda_document_index import get_cda_indexer

logger = logging.getLogger(__name__)
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

        return render(request, "patient_data/test_patients.html", context)

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


def smart_patient_search_view(request, patient_id):
    """
    Smart patient search that pre-fills and auto-submits patient search form

    This view takes a patient ID (which could be either a session ID or actual patient ID),
    looks up existing session data, and automatically renders the patient session view.

    Much better UX than sending users to an empty search form!

    UPDATE: Fixed to handle both session ID (url_patient_id) and actual patient ID correctly.
    """

    # Debug logging to see if this view is being called
    print(f"=== SMART SEARCH VIEW CALLED ===")
    print(f"Patient ID: {patient_id}")
    print(f"Patient ID type: {type(patient_id)}")
    print(f"Patient ID length: {len(str(patient_id))}")
    print(f"Request method: {request.method}")
    print(f"Request path: {request.path}")
    logger.info(f"Smart patient search called for patient_id: {patient_id}")

    # Safety check to prevent infinite loops
    referrer = request.META.get("HTTP_REFERER", "")
    if "smart-search" in referrer and str(patient_id) in referrer:
        print(f"=== POTENTIAL REDIRECT LOOP DETECTED ===")
        print(f"Referrer: {referrer}")
        messages.warning(
            request,
            f"Navigation loop detected. Redirecting to search form.",
        )
        return redirect("patient_data:patient_data_form")

    # Validate patient_id format
    if not patient_id or not str(patient_id).strip():
        print(f"=== INVALID PATIENT ID ===")
        messages.error(request, "Invalid patient ID provided.")
        return redirect("patient_data:patient_data_form")

    # First, check if we already have session data for this patient ID
    # This could be stored under either the session ID or the actual patient ID
    session_key = f"patient_match_{patient_id}"
    existing_match_data = request.session.get(session_key)

    # If not found, search all patient_match_ sessions to find matching data
    if not existing_match_data:
        print(f"=== NO DIRECT SESSION MATCH - SEARCHING ALL SESSIONS ===")
        for key, value in request.session.items():
            if key.startswith("patient_match_") and isinstance(value, dict):
                patient_data = value.get("patient_data", {})
                stored_patient_id = patient_data.get("patient_id")
                stored_url_patient_id = patient_data.get("url_patient_id")

                print(
                    f"Checking session {key}: patient_id={stored_patient_id}, url_patient_id={stored_url_patient_id}"
                )

                # Check if this patient_id matches either the stored patient_id or url_patient_id
                if (
                    stored_patient_id == patient_id
                    or stored_url_patient_id == patient_id
                ):
                    existing_match_data = value
                    session_key = key
                    print(f"=== FOUND MATCHING SESSION: {key} ===")
                    break

    print(f"=== SESSION DEBUG INFO ===")
    print(f"Session key used: {session_key}")
    print(f"Session exists: {existing_match_data is not None}")
    if existing_match_data:
        print(f"Session data keys: {list(existing_match_data.keys())}")
        print(
            f"Patient data keys: {list(existing_match_data.get('patient_data', {}).keys())}"
        )
        print(f"Has L1: {existing_match_data.get('has_l1')}")
        print(f"Has L3: {existing_match_data.get('has_l3')}")
    print(f"=== END SESSION DEBUG ===")

    if existing_match_data:
        print(f"=== FOUND EXISTING SESSION DATA ===")
        print(f"Session key: {session_key}")
        logger.info(f"Found existing session data for patient {patient_id}")

        # Session data exists - redirect to patient details page
        # This will show the proper patient details interface (Image 2)
        print(f"=== REDIRECTING TO PATIENT DETAILS ===")
        return redirect("patient_data:patient_details", patient_id=patient_id)

    print(f"=== NO EXISTING SESSION DATA - PERFORMING NEW SEARCH ===")
    logger.info(
        f"No existing session data found for patient {patient_id}, performing new search"
    )

    try:
        print(f"=== TRYING CDA INDEX LOOKUP ===")
        # Get patient data from CDA index
        indexer = get_cda_indexer()
        patients = indexer.get_all_patients()
        print(f"Found {len(patients)} patients in CDA index")

        # Find the specific patient
        target_patient = None
        for patient in patients:
            if patient["patient_id"] == patient_id:
                target_patient = patient
                break

        if not target_patient:
            print(f"=== PATIENT {patient_id} NOT FOUND IN CDA INDEX ===")
            print("Available patient IDs:")
            for i, p in enumerate(patients[:5]):  # Show first 5
                print(f"  {i+1}. {p['patient_id']}")
            messages.error(
                request, f"Test patient '{patient_id}' not found in CDA index."
            )
            return redirect("patient_data:test_patients")

        print(f"=== FOUND PATIENT IN INDEX: {target_patient['given_name']} {target_patient['family_name']} ===")

        # Import the search service and form
        from .forms import PatientDataForm
        from .services.patient_search_service import (
            EUPatientSearchService,
            PatientCredentials,
        )

        # Create search credentials
        print(f"=== CREATING SEARCH CREDENTIALS ===")
        credentials = PatientCredentials(
            country_code=target_patient["country_code"], patient_id=patient_id
        )
        print(f"Credentials: country_code={target_patient['country_code']}, patient_id={patient_id}")

        logger.info(
            f"Smart search: Searching for patient_id='{patient_id}' in country='{target_patient['country_code']}'"
        )

        # Perform the search
        print(f"=== PERFORMING PATIENT SEARCH ===")
        search_service = EUPatientSearchService()
        matches = search_service.search_patient(credentials)
        print(f"Search completed. Found {len(matches) if matches else 0} matches")

        if matches:
            # Store the search results in session for patient_details_view
            match_data = {
                "patient_data": {
                    "given_name": matches[0].given_name,
                    "family_name": matches[0].family_name,
                    "birth_date": matches[0].birth_date,  # birth_date is already a string
                    "gender": matches[0].gender,
                    "primary_patient_id": patient_id,
                    "country_code": target_patient["country_code"],
                },
                "cda_content": (
                    matches[0].cda_content
                    if hasattr(matches[0], "cda_content")
                    else None
                ),
                "search_timestamp": timezone.now().isoformat(),
            }

            # Store in session using the same key format as regular searches
            session_key = f"patient_match_{patient_id}"
            request.session[session_key] = match_data

            # Add success message
            messages.success(
                request,
                f"Found patient data for {matches[0].given_name} {matches[0].family_name} from {target_patient['country_code']}",
            )

            # Redirect to patient details page to show the proper patient interface
            print(f"=== NEW SEARCH SUCCESSFUL - REDIRECTING TO PATIENT DETAILS ===")
            return redirect("patient_data:patient_details", patient_id=patient_id)

        else:
            # No matches found, redirect to search form with pre-filled data
            messages.warning(
                request,
                f"No patient data found for ID '{patient_id}' in country '{target_patient['country_code']}'. "
                f"Try searching manually below.",
            )

            # Create form with pre-filled data
            form_data = {
                "country_code": target_patient["country_code"],
                "patient_identifier": patient_id,
            }

            # Store form data in session to pre-fill the form
            request.session["prefill_search_form"] = form_data

            return redirect("patient_data:patient_data_form")

    except Exception as e:
        logger.error(
            f"Error in smart patient search for {patient_id}: {str(e)}", exc_info=True
        )
        print(f"=== SMART SEARCH ERROR ===")
        print(f"Patient ID: {patient_id}")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {e}")
        import traceback

        traceback.print_exc()
        print("=== END ERROR ===")

        # More descriptive error message with fallback navigation
        if existing_match_data:
            # We had session data but search still failed - redirect to patient details with existing data
            messages.warning(
                request,
                f"Unable to refresh patient data for '{patient_id}'. Using cached data.",
            )
            # Redirect directly to patient details with existing session data
            return redirect("patient_data:patient_details", patient_id=patient_id)
        else:
            # No session data and search failed - go back to search form
            messages.error(
                request,
                f"Unable to find or load patient '{patient_id}'. Please try searching manually.",
            )
            return redirect("patient_data:patient_data_form")
