"""
Django views for CDA translation and display
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, Http404
from django.conf import settings
from pathlib import Path
import json

from patient_data.services.cda_translation_service import (
    CDATranslationService,
    process_cda_file,
)


def cda_translation_display(request, country_code, patient_id=None):
    """
    Display CDA document with original and English translation side-by-side
    """
    try:
        # Construct path to CDA file
        if patient_id:
            # Specific patient CDA file
            cda_file_path = (
                Path(settings.BASE_DIR)
                / "test_data"
                / "eu_member_states"
                / country_code.upper()
                / f"{patient_id}.htm"
            )
        else:
            # Default CDA file for country
            cda_file_path = (
                Path(settings.BASE_DIR)
                / "test_data"
                / "eu_member_states"
                / country_code.upper()
                / "DefaultXsltOutput.htm"
            )

        if not cda_file_path.exists():
            raise Http404(f"CDA file not found for {country_code}")

        # Process the CDA file
        bilingual_data = process_cda_file(str(cda_file_path))

        context = {
            "country_code": country_code.upper(),
            "patient_id": patient_id,
            "bilingual_data": bilingual_data,
            "source_language": bilingual_data["source_language"],
            "patient_info": bilingual_data["patient_info"],
            "sections": bilingual_data["sections"],
            "document_info": bilingual_data["document_info"],
        }

        return render(request, "patient_data/cda_bilingual_display.html", context)

    except Exception as e:
        context = {
            "error": f"Error processing CDA file: {str(e)}",
            "country_code": country_code,
            "patient_id": patient_id,
        }
        return render(request, "patient_data/cda_error.html", context)


def cda_translation_api(request, country_code, patient_id=None):
    """
    API endpoint to get CDA translation data as JSON
    """
    try:
        # Construct path to CDA file
        if patient_id:
            cda_file_path = (
                Path(settings.BASE_DIR)
                / "test_data"
                / "eu_member_states"
                / country_code.upper()
                / f"{patient_id}.htm"
            )
        else:
            cda_file_path = (
                Path(settings.BASE_DIR)
                / "test_data"
                / "eu_member_states"
                / country_code.upper()
                / "DefaultXsltOutput.htm"
            )

        if not cda_file_path.exists():
            return JsonResponse(
                {"error": f"CDA file not found for {country_code}"}, status=404
            )

        # Process the CDA file
        bilingual_data = process_cda_file(str(cda_file_path))

        return JsonResponse(bilingual_data)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def available_cda_files(request):
    """
    List all available CDA files by country
    """
    try:
        test_data_path = Path(settings.BASE_DIR) / "test_data" / "eu_member_states"

        if not test_data_path.exists():
            return JsonResponse({"error": "Test data directory not found"}, status=404)

        available_files = {}

        for country_dir in test_data_path.iterdir():
            if country_dir.is_dir():
                country_code = country_dir.name
                files = []

                # Look for CDA HTML files
                for file_path in country_dir.glob("*.htm"):
                    files.append(
                        {
                            "filename": file_path.name,
                            "display_url": f"/patient_data/cda/{country_code.lower()}/",
                            "api_url": f"/patient_data/api/cda/{country_code.lower()}/",
                        }
                    )

                if files:
                    available_files[country_code] = files

        return JsonResponse(available_files)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def patient_search_with_cda(request):
    """
    Enhanced patient search that includes CDA document links
    """
    from patient_data.services.patient_search_service import PatientSearchService

    search_service = PatientSearchService()

    if request.method == "POST":
        # Handle search form submission
        search_criteria = {
            "name": request.POST.get("patient_name", ""),
            "dob": request.POST.get("date_of_birth", ""),
            "id": request.POST.get("patient_id", ""),
            "country": request.POST.get("country", ""),
        }

        # Perform search
        search_results = search_service.search_patients(search_criteria)

        # Add CDA document links to results
        for result in search_results:
            if result.get("country_code"):
                result["cda_url"] = (
                    f"/patient_data/cda/{result['country_code'].lower()}/"
                )
                result["cda_api_url"] = (
                    f"/patient_data/api/cda/{result['country_code'].lower()}/"
                )

        context = {
            "search_criteria": search_criteria,
            "search_results": search_results,
            "countries": search_service.get_available_countries(),
        }
        return render(request, "patient_data/patient_search_results.html", context)

    # Display search form
    context = {
        "countries": (
            search_service.get_available_countries()
            if hasattr(search_service, "get_available_countries")
            else []
        )
    }
    return render(request, "patient_data/patient_search.html", context)
