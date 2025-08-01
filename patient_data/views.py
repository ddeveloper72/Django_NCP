"""
Patient Search Views
Django views for cross-border patient search functionality
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import (
    MemberState,
    PatientIdentifier,
    PatientData,
    AvailableService,
    PatientServiceRequest,
)

# Import translation services
from translation_services.core import TranslationServiceFactory
from .patient_loader import patient_loader
from .services.local_patient_search import LocalPatientSearchService
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@login_required
def patient_search_view(request):
    """Enhanced patient search page with dynamic ISM support"""

    # Get all active member states for country selection
    member_states = MemberState.objects.filter(is_active=True).order_by("country_name")

    # Get ISM configurations for enhanced countries
    from ehealth_portal.models import Country, InternationalSearchMask

    ism_countries = []
    try:
        ism_configs = InternationalSearchMask.objects.filter(
            is_active=True
        ).select_related("country")
        for ism in ism_configs:
            ism_countries.append(
                {
                    "code": ism.country.code,
                    "name": ism.country.name,
                    "has_ism": True,
                    "ism_version": ism.mask_version,
                    "description": ism.mask_description,
                }
            )
    except Exception as e:
        logger.warning(f"Error loading ISM configurations: {e}")

    context = {
        "member_states": member_states,
        "ism_countries": ism_countries,
        "current_user": request.user,
    }

    if request.method == "POST":
        return handle_patient_search(request, context)

    return render(request, "patient_data/patient_search.html", context, using="jinja2")


def handle_patient_search(request, context):
    """Enhanced patient search form submission with ISM support"""

    try:
        logger.info("Starting enhanced patient search form handling")

        # Extract basic form data
        member_state_id = request.POST.get("member_state_id")
        break_glass = request.POST.get("break_glass") == "on"
        break_glass_reason = request.POST.get("break_glass_reason", "").strip()
        use_local_search = request.POST.get("use_local_search") == "on"

        # Get member state
        member_state = None
        if member_state_id:
            try:
                member_state = MemberState.objects.get(
                    id=member_state_id, is_active=True
                )
                logger.info(
                    f"Found member state: {member_state.country_name} ({member_state.country_code})"
                )
            except MemberState.DoesNotExist:
                logger.error(f"Invalid member state ID: {member_state_id}")

        # Initialize patient search parameters
        patient_search_params = {}
        errors = []

        # Extract dynamic ISM fields or fallback to default fields
        if member_state:
            # Try to get ISM configuration
            from ehealth_portal.models import Country, InternationalSearchMask

            try:
                country = Country.objects.get(code=member_state.country_code)
                ism = InternationalSearchMask.objects.get(
                    country=country, is_active=True
                )

                # Extract ISM fields
                for field in ism.fields.all():
                    field_value = request.POST.get(field.field_code, "").strip()

                    # Validate required fields
                    if field.is_required and not field_value:
                        errors.append(f"{field.label} is required")
                        continue

                    # Validate field format
                    if field_value and field.validation_pattern:
                        import re

                        pattern = f"^{field.validation_pattern}$"
                        if not re.match(pattern, field_value):
                            errors.append(f"Invalid {field.label} format")
                            continue

                    # Store validated field
                    patient_search_params[field.field_code] = field_value

                    # Special handling for common field mappings
                    if field.field_code == "patient_id":
                        patient_search_params["national_person_id"] = field_value
                    elif field.field_code == "birth_date":
                        patient_search_params["birthdate"] = field_value

                logger.info(
                    f"Using ISM fields for {member_state.country_name}: {list(patient_search_params.keys())}"
                )

            except (Country.DoesNotExist, InternationalSearchMask.DoesNotExist):
                # Fallback to traditional fields
                logger.info(
                    f"No ISM configuration found for {member_state.country_code}, using default fields"
                )

                national_person_id = request.POST.get("national_person_id", "").strip()
                birthdate_str = request.POST.get("birthdate", "").strip()

                if not national_person_id:
                    errors.append("National Person Identifier is required")
                if not birthdate_str:
                    errors.append("Birthdate is required")

                patient_search_params = {
                    "national_person_id": national_person_id,
                    "birthdate": birthdate_str,
                }
        else:
            errors.append("Please select a member state")

        # Parse birthdate if provided
        birthdate = None
        birthdate_str = patient_search_params.get(
            "birthdate"
        ) or patient_search_params.get("birth_date")
        if birthdate_str:
            try:
                # Handle different date formats
                for date_format in ["%Y/%m/%d", "%Y-%m-%d", "%d/%m/%Y"]:
                    try:
                        birthdate = datetime.strptime(birthdate_str, date_format).date()
                        break
                    except ValueError:
                        continue

                if not birthdate:
                    errors.append("Invalid birthdate format. Please use yyyy/MM/dd")
            except Exception as e:
                errors.append("Invalid birthdate format")
                logger.warning(f"Date parsing error: {e}")

        # Validate break-the-glass
        if break_glass and not break_glass_reason:
            errors.append("Break-the-glass reason is required for emergency access")

        # Get patient identifier for search
        patient_id = patient_search_params.get(
            "national_person_id"
        ) or patient_search_params.get("patient_id")

        logger.info(
            f"Search parameters: patient_id={patient_id}, birthdate={birthdate_str}, member_state={member_state.country_code if member_state else None}, use_local_search={use_local_search}"
        )

        # Search for patient in both old sample data and new EU test data
        patient_found = False
        sample_patient_info = None

        if not errors and member_state and patient_id:
            logger.info(
                f"Searching for patient {patient_id} in {member_state.country_name}, use_local_search={use_local_search}"
            )

            # NEW: Local CDA document search if enabled
            if use_local_search:
                logger.info(
                    f"Using local CDA document search for {member_state.country_code}"
                )
                try:
                    local_search_service = LocalPatientSearchService()
                    found, cda_documents, message = (
                        local_search_service.search_patient_summaries(
                            country_code=member_state.country_code,
                            patient_id=patient_id,
                        )
                    )

                    if found and cda_documents:
                        patient_found = True
                        # Create patient info from first matching CDA document
                        first_doc = cda_documents[0]
                        sample_patient_info = type(
                            "PatientInfo",
                            (),
                            {
                                "family_name": first_doc.get("patient_family_name", ""),
                                "given_name": first_doc.get("patient_given_name", ""),
                                "administrative_gender": first_doc.get(
                                    "patient_gender", ""
                                ),
                                "birth_date_formatted": birthdate_str
                                or first_doc.get("patient_birth_time", ""),
                                "street": "",
                                "city": first_doc.get("patient_city", ""),
                                "postal_code": "",
                                "country": first_doc.get(
                                    "patient_country", member_state.country_name
                                ),
                                "telephone": "",
                                "email": "",
                                "oid": f"LOCAL_CDA_{member_state.country_code}",
                                "cda_documents": cda_documents,  # Store CDA documents for later use
                            },
                        )()
                        logger.info(
                            f"Patient {patient_id} found in local CDA documents: {message}"
                        )
                    else:
                        logger.info(
                            f"Patient {patient_id} not found in local CDA documents: {message}"
                        )
                except Exception as e:
                    logger.warning(f"Error in local CDA search: {e}")

            # If not found in local CDA and not using local search only, try EU test data
            if not patient_found and not use_local_search:
                try:
                    # Look for patient in PatientData table
                    eu_patient_data = PatientData.objects.filter(
                        patient_identifier__patient_id=patient_id,
                        patient_identifier__home_member_state=member_state,
                    )

                    # Add birthdate filter if provided
                    if birthdate:
                        eu_patient_data = eu_patient_data.filter(birth_date=birthdate)

                    eu_patient_data = eu_patient_data.first()

                    if eu_patient_data:
                        patient_found = True
                        # Create compatible patient info object for session storage
                        sample_patient_info = type(
                            "PatientInfo",
                            (),
                            {
                                "family_name": eu_patient_data.family_name or "",
                                "given_name": eu_patient_data.given_name or "",
                                "administrative_gender": eu_patient_data.administrative_gender
                                or "",
                                "birth_date_formatted": birthdate_str or "",
                                "street": eu_patient_data.street or "",
                                "city": eu_patient_data.city or "",
                                "postal_code": eu_patient_data.postal_code or "",
                                "country": eu_patient_data.country
                                or member_state.country_name,
                                "telephone": eu_patient_data.telephone or "",
                                "email": eu_patient_data.email or "",
                                "oid": f"EU_TEST_DATA_{member_state.country_code}",
                            },
                        )()
                        logger.info(
                            f"Patient {patient_id} found in EU test data: {eu_patient_data.given_name} {eu_patient_data.family_name}"
                        )
                    else:
                        logger.info(f"Patient {patient_id} not found in EU test data")
                except Exception as e:
                    logger.warning(f"Error searching EU test data: {e}")

                # If not found in EU test data, try old sample data files
                if not patient_found and member_state.sample_data_oid:
                    logger.info(
                        f"Searching for patient {patient_id} in legacy sample data OID {member_state.sample_data_oid}"
                    )

                    # Try to find patient in old sample data
                    found, patient_info, message = patient_loader.search_patient(
                        member_state.sample_data_oid, patient_id, birthdate_str or ""
                    )

                    logger.info(
                        f"Legacy search result: found={found}, message='{message}'"
                    )

                    if found:
                        patient_found = True
                        sample_patient_info = patient_info
                        logger.info(
                            f"Patient {patient_id} found in legacy sample data: {message}"
                        )
                    else:
                        if patient_info:  # Patient exists but birth date doesn't match
                            logger.info(
                                f"Patient found in legacy data but {message.lower()}"
                            )

            # If patient not found in either source
            if not patient_found:
                if member_state.sample_data_oid:
                    errors.append(
                        f"Patient {patient_id} not found in {member_state.country_name} (searched both EU test data and legacy sample data)"
                    )
                else:
                    errors.append(
                        f"Patient {patient_id} not found in {member_state.country_name} EU test data"
                    )
        else:
            logger.warning(
                f"Validation failed: errors={errors}, member_state={member_state}"
            )

        if errors:
            for error in errors:
                messages.error(request, error)

            # Update context with form values for re-display
            context.update(
                {
                    "member_state_id": (
                        int(member_state_id)
                        if member_state_id and member_state_id.isdigit()
                        else member_state_id
                    ),
                    "break_glass": break_glass,
                    "break_glass_reason": break_glass_reason,
                    "use_local_search": use_local_search,
                }
            )

            # Add all patient search parameters back to context
            for key, value in patient_search_params.items():
                context[key] = value

            # Maintain backwards compatibility with old field names
            if "national_person_id" in patient_search_params:
                context["national_person_id"] = patient_search_params[
                    "national_person_id"
                ]
            if "birthdate" in patient_search_params:
                context["birthdate"] = patient_search_params["birthdate"]

            return render(
                request, "patient_data/patient_search.html", context, using="jinja2"
            )

        # Check if patient identifier already exists
        logger.info(
            f"Creating patient identifier for {national_person_id} in {member_state.country_name}"
        )

        patient_identifier, created = PatientIdentifier.objects.get_or_create(
            patient_id=national_person_id,
            home_member_state=member_state,
            defaults={
                "id_root": member_state.home_community_id,
                "id_extension": sample_patient_info.oid if sample_patient_info else "",
            },
        )

        logger.info(
            f"Patient identifier {'created' if created else 'found'}: ID={patient_identifier.id}"
        )

        # Store the sample patient info in session for use in results page
        if sample_patient_info:
            request.session[f"patient_info_{patient_identifier.id}"] = {
                "family_name": sample_patient_info.family_name,
                "given_name": sample_patient_info.given_name,
                "administrative_gender": sample_patient_info.administrative_gender,
                "birth_date": sample_patient_info.birth_date_formatted,
                "street": sample_patient_info.street,
                "city": sample_patient_info.city,
                "postal_code": sample_patient_info.postal_code,
                "country": sample_patient_info.country,
                "telephone": sample_patient_info.telephone,
                "email": sample_patient_info.email,
                "oid": sample_patient_info.oid,
            }

        # Log the search attempt
        logger.info(
            f"Patient search initiated by {request.user.username} for "
            f"patient {national_person_id} from {member_state.country_code}. "
            f"Break glass: {break_glass}"
        )

        # In a real implementation, this would query the member state's NCP
        # For now, we'll simulate the search and redirect to results
        return redirect(
            "patient_data:patient_search_results", patient_id=patient_identifier.id
        )

    except Exception as e:
        logger.error(f"Error in patient search: {str(e)}", exc_info=True)
        messages.error(request, f"An error occurred during patient search: {str(e)}")
        return render(request, "patient_data/patient_search.html", context)


@login_required
def patient_search_results(request, patient_id):
    """Display patient search results"""

    try:
        patient_identifier = PatientIdentifier.objects.get(id=patient_id)
        member_state = patient_identifier.home_member_state

        # Get available services for this member state
        available_services = AvailableService.objects.filter(
            member_state=member_state, is_active=True
        ).order_by("service_type")

        # Check if we already have data for this patient
        existing_data = PatientData.objects.filter(
            patient_identifier=patient_identifier
        ).order_by("-access_timestamp")

        # Get sample patient info from session
        sample_patient_info = request.session.get(
            f"patient_info_{patient_identifier.id}"
        )

        # Check if this is a local CDA search result
        is_local_cda_search = (
            sample_patient_info
            and sample_patient_info.get("oid", "").startswith("LOCAL_CDA_")
            and "cda_documents" in sample_patient_info
        )

        context = {
            "patient_identifier": patient_identifier,
            "member_state": member_state,
            "available_services": available_services,
            "existing_data": existing_data,
            "sample_patient_info": sample_patient_info,
            "current_user": request.user,
            "is_local_cda_search": is_local_cda_search,
        }

        return render(
            request, "patient_data/patient_search_results.html", context, using="jinja2"
        )

    except PatientIdentifier.DoesNotExist:
        messages.error(request, "Patient identifier not found.")
        return redirect("patient_search")


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def request_patient_service(request):
    """AJAX endpoint to request a specific patient service"""

    try:
        data = json.loads(request.body)
        patient_identifier_id = data.get("patient_identifier_id")
        service_id = data.get("service_id")
        consent_method = data.get("consent_method", "EXPLICIT")
        break_glass_reason = data.get("break_glass_reason", "")

        # Validate inputs
        try:
            patient_identifier = PatientIdentifier.objects.get(id=patient_identifier_id)
            service = AvailableService.objects.get(id=service_id, is_active=True)
        except (PatientIdentifier.DoesNotExist, AvailableService.DoesNotExist):
            return JsonResponse(
                {"success": False, "error": "Invalid patient identifier or service"}
            )

        # Create service request
        service_request = PatientServiceRequest.objects.create(
            patient_identifier=patient_identifier,
            requested_service=service,
            requested_by=request.user,
            consent_method=consent_method,
            consent_required=consent_method != "BREAK_GLASS",
            consent_obtained=consent_method == "BREAK_GLASS",
            status="PENDING",
        )

        # If break glass, create patient data record immediately
        if consent_method == "BREAK_GLASS":
            patient_data = PatientData.objects.create(
                patient_identifier=patient_identifier,
                accessed_by=request.user,
                break_glass_access=True,
                break_glass_reason=break_glass_reason,
                break_glass_by=request.user,
                break_glass_timestamp=timezone.now(),
                # In real implementation, this would contain actual patient data
                # from the member state's NCP
                raw_patient_summary="<!-- Simulated patient data for break glass access -->",
            )

            service_request.status = "COMPLETED"
            service_request.response_timestamp = timezone.now()
            service_request.save()

        # Log the request
        logger.info(
            f"Service request {service_request.request_id} created by {request.user.username} "
            f"for {service.service_name} from {patient_identifier.home_member_state.country_code}. "
            f"Consent method: {consent_method}"
        )

        return JsonResponse(
            {
                "success": True,
                "request_id": str(service_request.request_id),
                "status": service_request.status,
                "message": f"{service.service_name} request submitted successfully",
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON data"})
    except Exception as e:
        logger.error(f"Error in service request: {str(e)}")
        return JsonResponse(
            {"success": False, "error": "An error occurred processing your request"}
        )


@login_required
def patient_data_view(request, patient_data_id):
    """View patient data with translations"""

    try:
        patient_data = PatientData.objects.get(id=patient_data_id)

        # Check if user has permission to view this data
        if patient_data.accessed_by != request.user and not request.user.is_staff:
            messages.error(
                request, "You don't have permission to view this patient data."
            )
            return redirect("patient_search")

        context = {
            "patient_data": patient_data,
            "member_state": patient_data.patient_identifier.home_member_state,
            "current_user": request.user,
        }

        return render(
            request, "patient_data/patient_data_view.html", context, using="jinja2"
        )

    except PatientData.DoesNotExist:
        messages.error(request, "Patient data not found.")
        return redirect("patient_search")


@login_required
def consent_management(request, patient_identifier_id):
    """Manage patient consent for data access"""

    try:
        patient_identifier = PatientIdentifier.objects.get(id=patient_identifier_id)

        if request.method == "POST":
            consent_given = request.POST.get("consent_given") == "on"

            # Update or create patient data record with consent
            patient_data, created = PatientData.objects.get_or_create(
                patient_identifier=patient_identifier,
                accessed_by=request.user,
                defaults={
                    "consent_given": consent_given,
                    "consent_timestamp": timezone.now() if consent_given else None,
                    "consent_given_by": request.user if consent_given else None,
                },
            )

            if not created:
                patient_data.consent_given = consent_given
                patient_data.consent_timestamp = (
                    timezone.now() if consent_given else None
                )
                patient_data.consent_given_by = request.user if consent_given else None
                patient_data.save()

            messages.success(
                request,
                f"Consent {'granted' if consent_given else 'revoked'} for patient {patient_identifier.patient_id}",
            )

            return redirect("patient_search_results", patient_id=patient_identifier.id)

        context = {
            "patient_identifier": patient_identifier,
            "current_user": request.user,
        }

        return render(request, "patient_data/consent_management.html", context)

    except PatientIdentifier.DoesNotExist:
        messages.error(request, "Patient identifier not found.")
        return redirect("patient_search")


def patient_data_view(request, patient_data_id):
    """
    Display translated patient summary document
    Integrates with translation services to show original and translated clinical data
    """
    try:
        patient_data = get_object_or_404(PatientData, id=patient_data_id)
        member_state = patient_data.patient_identifier.home_member_state

        # Get translation service
        terminology_service = TranslationServiceFactory.get_terminology_service()

        # Sample FHIR data for demonstration (in real implementation, this would come from the NCP)
        sample_fhir_bundle = {
            "resourceType": "Bundle",
            "id": f"patient-summary-{patient_data.patient_identifier.patient_id}",
            "type": "document",
            "entry": [
                {
                    "resource": {
                        "resourceType": "AllergyIntolerance",
                        "id": "allergy-1",
                        "code": {
                            "coding": [
                                {
                                    "system": "ICD-10",
                                    "code": "T78.40",
                                    "display": "Allergy, unspecified",
                                }
                            ]
                        },
                        "reaction": [
                            {
                                "manifestation": [
                                    {
                                        "coding": [
                                            {
                                                "system": "SNOMED-CT",
                                                "code": "294505008",
                                                "display": "Penicillin allergy",
                                            }
                                        ]
                                    }
                                ]
                            }
                        ],
                    }
                }
            ],
        }

        # Translate FHIR bundle to target language (English for demo)
        fhir_service = TranslationServiceFactory.get_fhir_translation_service()
        translation_response = fhir_service.translate_fhir_bundle(
            sample_fhir_bundle, "en-GB"
        )

        context = {
            "patient_data": patient_data,
            "member_state": member_state,
            "translation_response": translation_response,
            "fhir_bundle": translation_response.translated_document,
            "translation_errors": translation_response.errors,
            "translation_warnings": translation_response.warnings,
        }

        return render(request, "patient_data/patient_data_view.html", context)

    except PatientData.DoesNotExist:
        messages.error(request, "Patient data not found.")
        return redirect("patient_data:patient_search")


# @login_required  # Temporarily disabled for testing
def local_cda_document_view(request, patient_id, document_index=0):
    """
    View for displaying local CDA documents with PS Display Guidelines compliance
    """
    try:
        patient_identifier = PatientIdentifier.objects.get(id=patient_id)
        member_state = patient_identifier.home_member_state

        # Get sample patient info from session
        sample_patient_info = request.session.get(
            f"patient_info_{patient_identifier.id}"
        )

        if not sample_patient_info or "cda_documents" not in sample_patient_info:
            messages.error(request, "No local CDA documents found for this patient.")
            return redirect(
                "patient_data:patient_search_results", patient_id=patient_id
            )

        cda_documents = sample_patient_info["cda_documents"]

        if document_index >= len(cda_documents):
            messages.error(request, "Document not found.")
            return redirect(
                "patient_data:patient_search_results", patient_id=patient_id
            )

        selected_document = cda_documents[document_index]

        # Render document with PS Display Guidelines
        local_search_service = LocalPatientSearchService()
        rendered_result = local_search_service.render_patient_summary_with_guidelines(
            selected_document["file_path"],
            target_language="en",  # Can be made configurable
        )

        # Enhanced CDA parsing for structured clinical sections
        cda_parsed_data = None
        try:
            from .services.cda_parser_service import CDAParserService

            cda_parser = CDAParserService()

            # Read and parse the CDA document
            with open(selected_document["file_path"], "r", encoding="utf-8") as f:
                cda_content = f.read()

            cda_parsed_data = cda_parser.parse_cda_document(cda_content)
            logger.info(
                f"Successfully parsed CDA document with {len(cda_parsed_data.get('clinical_sections', []))} clinical sections"
            )

        except Exception as e:
            logger.warning(f"Error parsing CDA document for structured display: {e}")
            cda_parsed_data = None

        # Experimental FHIR conversion (if requested)
        fhir_conversion = None
        fhir_clinical_sections = None
        convert_to_fhir = request.GET.get("fhir", "").lower() == "true"

        if convert_to_fhir:
            try:
                from .services.cda_to_fhir_service import CDAToFHIRService

                fhir_service = CDAToFHIRService()
                fhir_conversion = fhir_service.convert_cda_to_fhir(
                    selected_document["file_path"]
                )

                if fhir_conversion.get("success"):
                    fhir_clinical_sections = fhir_service.extract_clinical_sections(
                        fhir_conversion["fhir_bundle"]
                    )
                    logger.info(
                        f"Successfully converted CDA to FHIR for document {document_index}"
                    )
                else:
                    logger.warning(
                        f"FHIR conversion failed: {fhir_conversion.get('error')}"
                    )

            except Exception as e:
                logger.error(
                    f"Error during experimental FHIR conversion: {e}", exc_info=True
                )
                fhir_conversion = {
                    "success": False,
                    "error": f"Experimental FHIR conversion failed: {str(e)}",
                }

        context = {
            "patient_identifier": patient_identifier,
            "member_state": member_state,
            "selected_document": selected_document,
            "all_documents": cda_documents,
            "document_index": document_index,
            "rendered_result": rendered_result,
            "cda_parsed_data": cda_parsed_data,  # Enhanced CDA parsing data
            "sample_patient_info": sample_patient_info,
            "current_user": request.user,
            "fhir_conversion": fhir_conversion,
            "fhir_clinical_sections": fhir_clinical_sections,
            "convert_to_fhir": convert_to_fhir,
        }

        return render(
            request,
            "patient_data/local_cda_document_view.html",
            context,
            using="jinja2",
        )

    except PatientIdentifier.DoesNotExist:
        messages.error(request, "Patient identifier not found.")
        return redirect("patient_data:patient_search")
    except Exception as e:
        logger.error(f"Error displaying local CDA document: {e}", exc_info=True)
        messages.error(request, f"Error displaying document: {str(e)}")
        return redirect("patient_data:patient_search_results", patient_id=patient_id)
