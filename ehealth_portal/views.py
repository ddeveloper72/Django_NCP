"""
eHealth Portal Views - Dynamic International Search Mask (ISM) Support
Renders country-specific patient search forms based on SMP-provided ISM configurations
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from .models import Country, InternationalSearchMask, SearchField, PatientSearchResult
from .european_smp_client import european_smp_client
import logging
import json
import requests
from datetime import datetime

logger = logging.getLogger("ehealth")


def country_selection(request):
    """
    Main country selection page - equivalent to Java portal
    Shows available EU member states with their current ISM status
    """
    # Get countries from database or create default ones
    countries = Country.objects.filter(is_available=True).order_by("name")

    # If no countries exist, create some defaults
    if not countries.exists():
        default_countries = [
            {
                "code": "BE",
                "name": "Belgium",
                "ncp_url": "https://ncp.belgium.eu/",
                "smp_url": "https://smp.belgium.eu/",
            },
            {
                "code": "AT",
                "name": "Austria",
                "ncp_url": "https://ncp.austria.gv.at/",
                "smp_url": "https://smp.austria.gv.at/",
            },
            {
                "code": "HU",
                "name": "Hungary",
                "ncp_url": "https://ncp.hungary.hu/",
                "smp_url": "https://smp.hungary.hu/",
            },
            {
                "code": "IE",
                "name": "Ireland",
                "ncp_url": "https://ncp.ireland.ie/",
                "smp_url": "https://smp.ireland.ie/",
            },
            {
                "code": "EU",
                "name": "European Commission (Test)",
                "ncp_url": "https://smp-ehealth-trn.acc.edelivery.tech.ec.europa.eu/",
                "smp_url": "https://smp-ehealth-trn.acc.edelivery.tech.ec.europa.eu/",
            },
        ]

        for country_data in default_countries:
            Country.objects.get_or_create(
                code=country_data["code"],
                defaults={
                    "name": country_data["name"],
                    "ncp_url": country_data["ncp_url"],
                    "smp_url": country_data["smp_url"],
                    "flag_image": f"flags/{country_data['code'].lower()}.png",
                },
            )

        countries = Country.objects.filter(is_available=True).order_by("name")

    # Convert to list for template
    countries_list = []
    for country in countries:
        # Check if ISM is available and up-to-date
        ism_status = "available"
        ism_last_updated = None

        try:
            ism = country.search_mask
            ism_last_updated = ism.last_synchronized
            if not ism.is_active:
                ism_status = "inactive"
        except InternationalSearchMask.DoesNotExist:
            ism_status = "not_configured"

        countries_list.append(
            {
                "code": country.code,
                "name": country.name,
                "flag_image": country.flag_image,
                "available": country.is_available,
                "ism_status": ism_status,
                "ism_last_updated": ism_last_updated,
                "ncp_url": country.ncp_url,
            }
        )

    context = {
        "countries": countries_list,
        "page_title": "eHealth OpenNCP Portal",
        "step": "STEP 1: COUNTRY SELECTION",
        "total_countries": len(countries_list),
        "available_countries": len([c for c in countries_list if c["available"]]),
    }

    return render(request, "ehealth_portal/country_selection.html", context)


# @login_required
def patient_search(request, country_code):
    """
    Dynamic patient search page based on country's International Search Mask (ISM)
    Renders different forms based on each country's specific requirements from SMP
    """
    # Get country configuration
    country = get_object_or_404(Country, code=country_code.upper())

    # Get or create/update ISM for this country
    try:
        search_mask = country.search_mask
        # Check if ISM needs updating (older than 24 hours)
        if (
            not search_mask.last_synchronized
            or (timezone.now() - search_mask.last_synchronized).days >= 1
        ):
            update_ism_from_smp(country)
            search_mask.refresh_from_db()
    except InternationalSearchMask.DoesNotExist:
        # Create default ISM if none exists
        search_mask = create_default_ism(country)

    if request.method == "POST":
        # Process search form submission
        search_fields = {}
        use_local_search = request.POST.get("use_local_search") == "on"

        # Collect all search field values
        for field in search_mask.fields.all():
            field_value = request.POST.get(field.field_code, "").strip()
            if field_value:
                search_fields[field.field_code] = field_value

        # Validate required fields
        missing_fields = []
        for field in search_mask.fields.filter(is_required=True):
            if not search_fields.get(field.field_code):
                missing_fields.append(field.label)

        if missing_fields:
            messages.error(
                request, f"Required fields missing: {', '.join(missing_fields)}"
            )
        else:
            # Perform patient search (with local CDA option)
            result = perform_patient_search(
                country, search_fields, request.user, use_local_search
            )

            if result.patient_found:
                # Redirect to patient data view with search result ID
                return redirect(
                    "patient_data", country_code=country_code, patient_id=result.id
                )
            else:
                messages.error(
                    request,
                    result.error_message
                    or "No patient found with the provided criteria.",
                )

    # Prepare form fields for rendering
    form_fields = []
    for field in search_mask.fields.all():
        field_data = {
            "code": field.field_code,
            "label": field.label,
            "type": field.field_type.type_code,
            "html_type": field.field_type.html_input_type,
            "placeholder": field.placeholder,
            "help_text": field.help_text,
            "required": field.is_required,
            "options": field.field_options,
            "default_value": field.default_value,
            "css_classes": field.css_classes,
            "group": field.field_group,
            "validation_pattern": field.validation_pattern,
            "error_message": field.error_message,
        }
        form_fields.append(field_data)

    # Group fields by field_group
    grouped_fields = {}
    for field in form_fields:
        group = field.get("group", "main")
        if group not in grouped_fields:
            grouped_fields[group] = []
        grouped_fields[group].append(field)

    # DEBUG: Print context data - Updated at 21:52
    print(f"DEBUG: Country: {country}")
    print(f"DEBUG: Search mask: {search_mask}")
    print(f"DEBUG: Form fields count: {len(form_fields)}")
    print(f"DEBUG: First few fields: {form_fields[:2] if form_fields else 'No fields'}")
    print(f"DEBUG: Grouped fields keys: {list(grouped_fields.keys())}")

    context = {
        "country": country,
        "country_code": country_code.upper(),
        "search_mask": search_mask,
        "form_fields": form_fields,
        "grouped_fields": grouped_fields,
        "page_title": f"Patient Search - {country.name}",
        "step": "PATIENT SEARCH",
        "ism_last_updated": search_mask.last_synchronized,
    }

    return render(request, "ehealth_portal/patient_search.html", context)


def update_ism_from_smp(country):
    """
    Update International Search Mask from country's SMP server using European SMP infrastructure
    """
    try:
        logger.info(f"Fetching ISM for {country.code} from European SMP")

        # Fetch ISM from real European SMP infrastructure
        ism_data = european_smp_client.fetch_international_search_mask(country.code)

        if not ism_data:
            logger.warning(f"No ISM data received for {country.code}, using fallback")
            return False

        # Update or create ISM
        search_mask, created = InternationalSearchMask.objects.get_or_create(
            country=country,
            defaults={
                "mask_name": f"{country.name} Patient Search",
                "mask_version": ism_data.get("version", "1.0"),
                "source_smp_url": country.smp_url,
                "raw_ism_data": ism_data,
            },
        )

        if not created:
            search_mask.mask_version = ism_data.get("version", "1.0")
            search_mask.raw_ism_data = ism_data
            search_mask.last_updated = timezone.now()
            search_mask.save()

        # Clear existing search fields for this ISM
        SearchField.objects.filter(international_search_mask=search_mask).delete()

        # Create new search fields from ISM data
        for field_data in ism_data.get("fields", []):
            SearchField.objects.create(
                international_search_mask=search_mask,
                field_name=field_data["name"],
                field_label=field_data["label"],
                field_type=field_data["field_type"],
                is_required=field_data.get("required", False),
                max_length=field_data.get("max_length", 255),
                validation_pattern=field_data.get("validation_pattern", ""),
                help_text=field_data.get("description", ""),
                field_order=field_data.get("order", 0),
            )

        logger.info(
            f"Successfully updated ISM for {country.code} with {len(ism_data.get('fields', []))} fields"
        )
        return True

    except Exception as e:
        logger.error(f"Error updating ISM for {country.code}: {e}")
        return False

        logger.info(f"Updated ISM for {country.code} from SMP")

    except Exception as e:
        logger.error(f"Failed to update ISM for {country.code}: {str(e)}")


def create_default_ism(country):
    """Create a default ISM if none exists"""
    search_mask = InternationalSearchMask.objects.create(
        country=country,
        mask_name=f"Default {country.name} Search",
        mask_version="1.0",
        source_smp_url=country.smp_url or "default",
        raw_ism_data=get_mock_ism_data(country.code),
    )

    # Create default search fields
    create_search_fields_from_ism(search_mask, search_mask.raw_ism_data)

    return search_mask


def get_mock_ism_data(country_code):
    """
    Mock ISM data - different for each country to demonstrate dynamic rendering
    In production, this would come from actual SMP API calls
    """
    ism_configs = {
        "BE": {  # Belgium - Comprehensive form
            "fields": [
                {
                    "code": "national_id",
                    "type": "ssn",
                    "label": "National ID Number (NISS)",
                    "placeholder": "XX.XX.XX-XXX.XX",
                    "required": True,
                    "validation_pattern": r"^\d{2}\.\d{2}\.\d{2}-\d{3}\.\d{2}$",
                    "help_text": "Belgian national identification number",
                    "group": "identity",
                },
                {
                    "code": "first_name",
                    "type": "text",
                    "label": "First Name",
                    "placeholder": "Enter first name",
                    "required": True,
                    "group": "identity",
                },
                {
                    "code": "last_name",
                    "type": "text",
                    "label": "Last Name",
                    "placeholder": "Enter last name",
                    "required": True,
                    "group": "identity",
                },
                {
                    "code": "birth_date",
                    "type": "date",
                    "label": "Date of Birth",
                    "required": True,
                    "group": "identity",
                },
                {
                    "code": "gender",
                    "type": "select",
                    "label": "Gender",
                    "options": [("M", "Male"), ("F", "Female"), ("O", "Other")],
                    "required": False,
                    "group": "demographics",
                },
                {
                    "code": "insurance_number",
                    "type": "text",
                    "label": "Health Insurance Number",
                    "placeholder": "Enter insurance number",
                    "required": False,
                    "group": "healthcare",
                },
            ]
        },
        "AT": {  # Austria - Simplified form
            "fields": [
                {
                    "code": "social_security",
                    "type": "ssn",
                    "label": "Social Security Number",
                    "placeholder": "XXXX XXXXXX",
                    "required": True,
                    "validation_pattern": r"^\d{4}\s\d{6}$",
                    "help_text": "Austrian social security number",
                    "group": "main",
                },
                {
                    "code": "family_name",
                    "type": "text",
                    "label": "Family Name",
                    "placeholder": "Familienname",
                    "required": True,
                    "group": "main",
                },
                {
                    "code": "given_name",
                    "type": "text",
                    "label": "Given Name",
                    "placeholder": "Vorname",
                    "required": True,
                    "group": "main",
                },
                {
                    "code": "birth_date",
                    "type": "date",
                    "label": "Geburtsdatum",
                    "required": True,
                    "group": "main",
                },
            ]
        },
        "HU": {  # Hungary - Different requirements
            "fields": [
                {
                    "code": "taj_number",
                    "type": "text",
                    "label": "TAJ Number",
                    "placeholder": "XXX XXX XXX",
                    "required": True,
                    "validation_pattern": r"^\d{3}\s\d{3}\s\d{3}$",
                    "help_text": "Hungarian social insurance number",
                    "group": "identification",
                },
                {
                    "code": "surname",
                    "type": "text",
                    "label": "Surname (Vezetéknév)",
                    "required": True,
                    "group": "identification",
                },
                {
                    "code": "forename",
                    "type": "text",
                    "label": "Forename (Keresztnév)",
                    "required": True,
                    "group": "identification",
                },
                {
                    "code": "mothers_name",
                    "type": "text",
                    "label": "Mother's Name (Anyja neve)",
                    "required": False,
                    "group": "additional",
                },
                {
                    "code": "place_of_birth",
                    "type": "text",
                    "label": "Place of Birth (Születési hely)",
                    "required": False,
                    "group": "additional",
                },
            ]
        },
        "IE": {  # Ireland - Minimal form
            "fields": [
                {
                    "code": "pps_number",
                    "type": "text",
                    "label": "PPS Number",
                    "placeholder": "1234567A",
                    "required": True,
                    "validation_pattern": r"^\d{7}[A-Z]$",
                    "help_text": "Personal Public Service Number",
                    "group": "main",
                },
                {
                    "code": "surname",
                    "type": "text",
                    "label": "Surname",
                    "required": True,
                    "group": "main",
                },
                {
                    "code": "first_name",
                    "type": "text",
                    "label": "First Name",
                    "required": True,
                    "group": "main",
                },
            ]
        },
        "EU": {  # European Commission Test - Comprehensive test form
            "fields": [
                {
                    "code": "patient_id",
                    "type": "text",
                    "label": "Patient ID",
                    "placeholder": "EU-TEST-12345",
                    "required": True,
                    "help_text": "European test patient identifier",
                    "group": "test",
                },
                {
                    "code": "id_type",
                    "type": "select",
                    "label": "ID Type",
                    "options": [
                        ("passport", "Passport"),
                        ("national_id", "National ID"),
                        ("ehic", "European Health Insurance Card"),
                        ("test_id", "Test ID"),
                    ],
                    "required": True,
                    "group": "test",
                },
                {
                    "code": "family_name",
                    "type": "text",
                    "label": "Family Name",
                    "required": True,
                    "group": "identity",
                },
                {
                    "code": "given_names",
                    "type": "text",
                    "label": "Given Names",
                    "required": True,
                    "group": "identity",
                },
                {
                    "code": "birth_date",
                    "type": "date",
                    "label": "Date of Birth",
                    "required": True,
                    "group": "identity",
                },
                {
                    "code": "test_scenario",
                    "type": "select",
                    "label": "Test Scenario",
                    "options": [
                        ("basic", "Basic Patient Data"),
                        ("with_documents", "Patient with Documents"),
                        ("cross_border", "Cross-border Scenario"),
                        ("error_test", "Error Handling Test"),
                    ],
                    "required": False,
                    "group": "testing",
                },
            ]
        },
    }

    return ism_configs.get(country_code, ism_configs["EU"])


def create_search_fields_from_ism(search_mask, ism_data):
    """Create SearchField objects from ISM configuration data"""
    from .models import SearchFieldType

    # Ensure field types exist
    field_types = {}
    for field_config in ism_data.get("fields", []):
        field_type_code = field_config.get("type", "text")
        if field_type_code not in field_types:
            field_type, created = SearchFieldType.objects.get_or_create(
                type_code=field_type_code,
                defaults={
                    "display_name": field_type_code.replace("_", " ").title(),
                    "html_input_type": (
                        field_type_code
                        if field_type_code in ["text", "email", "date", "number"]
                        else "text"
                    ),
                },
            )
            field_types[field_type_code] = field_type

    # Create search fields
    for order, field_config in enumerate(ism_data.get("fields", [])):
        field_type = field_types[field_config.get("type", "text")]

        SearchField.objects.create(
            search_mask=search_mask,
            field_code=field_config["code"],
            field_type=field_type,
            label=field_config["label"],
            placeholder=field_config.get("placeholder", ""),
            help_text=field_config.get("help_text", ""),
            is_required=field_config.get("required", False),
            validation_pattern=field_config.get("validation_pattern", ""),
            field_options=field_config.get("options", []),
            default_value=field_config.get("default_value", ""),
            field_order=order,
            field_group=field_config.get("group", "main"),
        )


def perform_patient_search(country, search_fields, user, use_local_search=False):
    """
    Perform patient search using NCP or local CDA documents
    Returns PatientSearchResult object
    """
    # Create search result record
    result = PatientSearchResult.objects.create(
        country=country,
        searched_by=user,
        search_fields=search_fields,
        search_mask_version="1.0",
    )

    try:
        # NEW: Local CDA document search if enabled
        if use_local_search:
            logger.info(f"Using local CDA document search for {country.code}")

            # Extract patient ID from search fields
            patient_id_value = (
                search_fields.get("patient_id")
                or search_fields.get("national_id")
                or search_fields.get("identifier")
                or search_fields.get("pps_number")
                or search_fields.get("social_security_number")
                or search_fields.get("health_card_number")
            )

            if patient_id_value:
                try:
                    from patient_data.services.local_patient_search import (
                        LocalPatientSearchService,
                    )

                    local_search_service = LocalPatientSearchService()
                    found, cda_documents, message = (
                        local_search_service.search_patient_summaries(
                            country_code=country.code, patient_id=patient_id_value
                        )
                    )

                    if found and cda_documents:
                        # Use data from first matching CDA document
                        first_doc = cda_documents[0]
                        result.patient_found = True
                        result.patient_data = {
                            "id": patient_id_value,
                            "name": f"{first_doc.get('patient_given_name', '')} {first_doc.get('patient_family_name', '')}".strip(),
                            "birth_date": first_doc.get("patient_birth_time", ""),
                            "gender": first_doc.get("patient_gender", ""),
                            "country": first_doc.get("patient_country", country.name),
                            "city": first_doc.get("patient_city", ""),
                            "document_format": first_doc.get("document_format", ""),
                            "validation_level": first_doc.get("validation_level", ""),
                            "file_name": first_doc.get("file_name", ""),
                            "cda_documents": cda_documents,  # Store all CDA documents
                            "source": "LOCAL_CDA_SEARCH",
                        }
                        result.available_documents = []
                        for doc in cda_documents:
                            result.available_documents.append(
                                {
                                    "type": "PS",
                                    "title": f"Patient Summary ({doc.get('validation_level', 'Unknown')} - {doc.get('document_format', 'Unknown')})",
                                    "date": doc.get("effective_time", ""),
                                    "available": True,
                                    "file_path": doc.get("file_path", ""),
                                    "extracted_pdfs": doc.get("extracted_pdfs", []),
                                }
                            )
                        result.ncp_response_time = 0.1  # Local search is fast
                        result.ncp_status_code = "200"
                        result.save()
                        logger.info(
                            f"Patient {patient_id_value} found in local CDA documents: {message}"
                        )
                        return result
                    else:
                        logger.info(
                            f"Patient {patient_id_value} not found in local CDA documents"
                        )
                except Exception as e:
                    logger.warning(f"Error in local CDA search: {e}")

        # In production, this would make actual NCP API calls
        # For demo, we'll check both simulated test data and actual database

        # First check actual database for patient data
        from patient_data.models import PatientData, PatientIdentifier, MemberState

        found_patient = False
        database_patient = None

        # Try to find patient in database
        patient_id_value = (
            search_fields.get("patient_id")
            or search_fields.get("national_id")
            or search_fields.get("identifier")
            or search_fields.get("pps_number")
        )
        birth_date_value = search_fields.get("birth_date") or search_fields.get(
            "birthdate"
        )

        if patient_id_value:
            try:
                # Find patient identifier matching the search
                patient_identifier = PatientIdentifier.objects.get(
                    patient_id=patient_id_value,
                    home_member_state__country_code=country.code.upper(),
                )

                # Find patient data
                database_patient = PatientData.objects.get(
                    patient_identifier=patient_identifier
                )
                found_patient = True

                logger.info(
                    f"Found patient in database: {database_patient.given_name} {database_patient.family_name}"
                )

            except (PatientIdentifier.DoesNotExist, PatientData.DoesNotExist):
                logger.info(
                    f"Patient {patient_id_value} not found in database for country {country.code}"
                )

        # If not found in database, check simulated test IDs
        if not found_patient:
            test_ids = ["EU-TEST-12345", "1234567A", "XX.XX.XX-XXX.XX"]
            for field_value in search_fields.values():
                if any(test_id in str(field_value) for test_id in test_ids):
                    found_patient = True
                    break

        if found_patient:
            # Use database patient data if available, otherwise simulate
            if database_patient:
                result.patient_found = True
                result.patient_data = {
                    "id": database_patient.patient_identifier.patient_id,
                    "name": f"{database_patient.given_name} {database_patient.family_name}",
                    "birth_date": database_patient.birth_date.strftime("%Y-%m-%d"),
                    "gender": database_patient.gender,
                    "country": database_patient.patient_identifier.home_member_state.country_code,
                    "address": f"{database_patient.address_line}, {database_patient.city}, {database_patient.postal_code}",
                    "last_updated": database_patient.access_timestamp.isoformat(),
                    "database_id": database_patient.id,  # Store for later use
                }
            else:
                # Simulate successful patient data for test IDs
                result.patient_found = True
                result.patient_data = {
                    "id": list(search_fields.values())[
                        0
                    ],  # Use first search field as ID
                    "name": f"{search_fields.get('first_name', search_fields.get('given_name', 'John'))} {search_fields.get('last_name', search_fields.get('surname', search_fields.get('family_name', 'Doe')))}",
                    "birth_date": search_fields.get("birth_date", "1980-01-01"),
                    "country": country.code,
                    "last_updated": timezone.now().isoformat(),
                }

            result.available_documents = [
                {
                    "type": "PS",
                    "title": "Patient Summary",
                    "date": "2024-12-01",
                    "available": True,
                },
                {
                    "type": "eP",
                    "title": "ePrescription",
                    "date": "2024-11-28",
                    "available": True,
                },
            ]
            result.ncp_response_time = 1.2
            result.ncp_status_code = "200"
        else:
            result.patient_found = False
            result.error_message = f"Patient {patient_id_value} not found in {country.name} (searched both EU test data and legacy sample data)"
            result.ncp_status_code = "404"

        result.save()

    except Exception as e:
        result.patient_found = False
        result.error_message = f"Search error: {str(e)}"
        result.ncp_status_code = "500"
        result.save()
        logger.error(f"Patient search error for {country.code}: {str(e)}")

    return result


@login_required
def patient_data(request, country_code, patient_id):
    """
    Display patient data and available documents from search results
    """
    country = get_object_or_404(Country, code=country_code.upper())

    # Get search result by ID (patient_id is actually search result ID)
    try:
        search_result = PatientSearchResult.objects.get(
            id=patient_id, country=country, patient_found=True
        )
        patient_data = search_result.patient_data
        available_documents = search_result.available_documents

        # Check if this is from local CDA search and process PDF extractions
        is_local_cda_search = patient_data.get("source") == "LOCAL_CDA_SEARCH"

        if is_local_cda_search:
            # Process documents for PDF viewing
            from patient_data.services.clinical_pdf_service import ClinicalPDFService

            pdf_service = ClinicalPDFService()

            for doc in available_documents:
                file_path = doc.get("file_path")
                if file_path and not doc.get("extracted_pdfs"):
                    # Extract PDFs from CDA document
                    extracted_pdfs = pdf_service.extract_pdfs_from_cda(file_path)
                    doc["extracted_pdfs"] = extracted_pdfs
                    doc["has_pdfs"] = len(extracted_pdfs) > 0

    except (PatientSearchResult.DoesNotExist, ValueError):
        # Fallback to mock data for direct access
        patient_data = {
            "id": patient_id,
            "name": "John Doe",
            "birth_date": "1980-01-01",
            "country": country_code,
            "last_updated": timezone.now().isoformat(),
        }
        available_documents = [
            {
                "type": "PS",
                "title": "Patient Summary",
                "date": "2024-12-01",
                "available": True,
            },
            {
                "type": "eP",
                "title": "ePrescription",
                "date": "2024-11-28",
                "available": True,
            },
        ]
        search_result = None
        is_local_cda_search = False

    context = {
        "country": country,
        "country_code": country_code.upper(),
        "patient": patient_data,
        "documents": available_documents,
        "search_result": search_result,
        "is_local_cda_search": is_local_cda_search,
        "page_title": f"Patient Data - {country.name}",
        "step": "PATIENT DATA",
    }

    return render(request, "ehealth_portal/patient_data.html", context)

    return render(request, "ehealth_portal/patient_data.html", context)


@login_required
def document_viewer(request, country_code, patient_id, document_type):
    """
    View specific document (CDA or FHIR)
    """
    # Mock document retrieval
    document_data = {
        "type": document_type,
        "patient_id": patient_id,
        "format": "CDA" if document_type == "PS" else "FHIR",
        "content": "Document content would be displayed here...",
    }

    context = {
        "document": document_data,
        "patient_id": patient_id,
        "country_code": country_code,
        "page_title": f"Document Viewer - {document_type}",
    }

    return render(request, "ehealth_portal/document_viewer.html", context)


@login_required
def smp_status(request):
    """
    Display detailed SMP connectivity and certificate status
    """
    from .european_smp_client import european_smp_client

    # Get connectivity test results
    connectivity_results = european_smp_client.test_connectivity()

    # Get certificate info
    cert_info = connectivity_results.get("certificate_config", {})

    context = {
        "page_title": "European SMP Status",
        "connectivity_results": connectivity_results,
        "cert_configured": cert_info.get("configured", False),
        "cert_name": cert_info.get("config_name"),
        "cert_path": cert_info.get("cert_path"),
        "ca_cert_path": cert_info.get("ca_cert_path"),
        "smp_admin": connectivity_results.get("smp_admin", {}),
        "country_smps": connectivity_results.get("country_smps", {}),
    }

    return render(request, "ehealth_portal/smp_status.html", context)


@login_required
def european_smp_test(request):
    """
    Test connectivity to European SMP infrastructure
    """
    if request.method == "POST":
        # Run connectivity test
        results = european_smp_client.test_connectivity()
        return JsonResponse(results)

    context = {
        "page_title": "European SMP Connectivity Test",
        "step": "SMP TEST",
        "countries": european_smp_client.EU_COUNTRIES,
        "sml_domain": european_smp_client.SML_DOMAIN,
        "smp_admin_url": european_smp_client.SMP_ADMIN_URL,
    }

    return render(request, "ehealth_portal/smp_test.html", context)


@login_required
def refresh_country_ism(request, country_code):
    """
    Manually refresh ISM data for a specific country from European SMP
    """
    try:
        country = get_object_or_404(Country, code=country_code.upper())

        # Force refresh ISM from European SMP
        success = update_ism_from_smp(country)

        if success:
            messages.success(
                request,
                f"Successfully updated ISM for {country.name} from European SMP",
            )
        else:
            # Check if certificates are configured
            from .european_smp_client import european_smp_client

            if european_smp_client.cert_config:
                cert_name = european_smp_client.cert_config.get("name", "Unknown")
                messages.info(
                    request,
                    f"Using enhanced fallback ISM for {country.name}. Certificates configured ({cert_name}) but European SMP infrastructure requires VPN access to EU internal networks.",
                )
            else:
                messages.info(
                    request,
                    f"Using enhanced fallback ISM for {country.name}. European SMP requires client certificates and VPN access to EU internal networks.",
                )

        return redirect("patient_search", country_code=country_code)

    except Exception as e:
        logger.error(f"Error refreshing ISM for {country_code}: {e}")
        messages.error(request, f"Error refreshing ISM: {e}")
        return redirect("country_selection")
