"""
Test view to isolate the ModuleNotFoundError issue
"""

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from .models import Country, InternationalSearchMask


def test_patient_search(request, country_code):
    """Simple test view to isolate the import error"""
    try:
        # Step 1: Get country
        country = get_object_or_404(Country, code=country_code.upper())

        # Step 2: Get search mask
        search_mask = country.search_mask

        # Step 3: Prepare minimal context like the original view
        context = {
            "country": country,
            "country_code": country_code.upper(),
            "search_mask": search_mask,
            "form_fields": [],
            "page_title": f"Patient Search - {country.name}",
        }

        # Step 4: Try to render the template
        return render(request, "ehealth_portal/patient_search.html", context)

    except Exception as e:
        return HttpResponse(f"Error: {str(e)} - Type: {type(e).__name__}")
