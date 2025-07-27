# Django NCP API Views for Java Portal Integration
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.conf import settings
from ehealth_portal.models import Country, InternationalSearchMask
import logging

logger = logging.getLogger("ehealth")
audit_logger = logging.getLogger("audit")


@api_view(["GET"])
@permission_classes([AllowAny])  # Allow access for Java portal integration
def get_available_countries(request):
    """
    API endpoint for Java portal to get available countries for patient lookup
    Returns dynamic list of countries from database with their connectivity status
    """
    try:
        # Get all countries from database
        countries_db = Country.objects.all().order_by("name")
        countries = []

        for country in countries_db:
            # Check if country has ISM configuration (indicates readiness)
            has_ism = InternationalSearchMask.objects.filter(country=country).exists()

            # Determine available services based on country configuration
            available_services = []
            if has_ism:
                available_services.extend(
                    ["PS"]
                )  # Patient Summary always available if ISM exists

                # Add other services based on country capabilities
                if country.code in ["IE", "BE", "AT"]:  # Major implementations
                    available_services.extend(
                        ["eP", "eD"]
                    )  # ePrescription, eDispensation
                if country.code in ["IE", "AT", "DE"]:  # Countries with lab integration
                    available_services.append("LAB")  # Laboratory reports
                if country.code in ["IE", "HU"]:  # Countries with hospital discharge
                    available_services.append("HD")  # Hospital Discharge
                if country.code == "IE":  # Ireland - most comprehensive
                    available_services.append("MI")  # Medical Images

            country_data = {
                "code": country.code,
                "name": country.name,
                "flag_url": f"/static/flags/{country.code.lower()}.webp",
                "ncp_endpoint": country.ncp_url
                or f"https://{country.code.lower()}-ncp.ehealth.{country.code.lower()}",
                "smp_endpoint": country.smp_url,
                "available": country.is_available and has_ism,
                "available_services": available_services,
                "has_ism": has_ism,
                "last_updated": (
                    country.updated_at.isoformat()
                    if hasattr(country, "updated_at")
                    else None
                ),
            }
            countries.append(country_data)

        user_info = (
            request.user.username
            if request.user.is_authenticated
            else f"anonymous_{request.META.get('REMOTE_ADDR', 'unknown')}"
        )
        audit_logger.info(
            f"Country list requested by user: {user_info} - {len(countries)} countries returned"
        )

        return Response(
            {
                "countries": countries,
                "total_countries": len(countries),
                "available_countries": len([c for c in countries if c["available"]]),
                "timestamp": settings.USE_TZ
                and __import__("datetime").datetime.now().isoformat()
                or None,
            }
        )

    except Exception as e:
        logger.error(f"Error fetching countries for API: {e}")
        return Response(
            {"error": "Failed to fetch countries", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])  # Allow access for Java portal integration
def patient_lookup(request):
    """
    API endpoint for cross-border patient lookup from Java portal
    Uses dynamic country validation and ISM-based lookup
    """
    try:
        data = request.data
        country_code = data.get("country_code", "").upper()
        patient_id = data.get("patient_id")
        id_type = data.get("id_type", "national_id")

        # Validate country exists and is available
        try:
            country = Country.objects.get(code=country_code, is_available=True)
        except Country.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "error": f"Country {country_code} not available for patient lookup",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if country has ISM configuration
        ism = InternationalSearchMask.objects.filter(country=country).first()
        if not ism:
            return Response(
                {
                    "success": False,
                    "error": f"No International Search Mask configured for {country.name}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Audit log the patient lookup attempt
        user_info = (
            request.user.username
            if request.user.is_authenticated
            else f"anonymous_{request.META.get('REMOTE_ADDR', 'unknown')}"
        )
        audit_logger.info(
            f"Patient lookup attempted: country={country_code}, "
            f"patient_id={patient_id}, user={user_info}"
        )

        # Validate required fields based on ISM configuration
        required_fields = ism.fields.filter(is_required=True)
        missing_fields = []
        for field in required_fields:
            if not data.get(field.field_code):
                missing_fields.append(field.label)

        if missing_fields:
            return Response(
                {
                    "success": False,
                    "error": f"Missing required fields: {', '.join(missing_fields)}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Mock patient data - replace with actual NCP lookup
        if patient_id:
            # Determine available documents based on country services
            available_documents = []

            # Always include Patient Summary if available
            available_documents.append(
                {
                    "type": "PS",
                    "title": "Patient Summary",
                    "date": "2024-12-01",
                    "format": "CDA",
                    "endpoint": f"/api/patient/{patient_id}/document/PS/",
                }
            )

            # Add other documents based on country capabilities
            if country.code in ["IE", "BE", "AT"]:
                available_documents.extend(
                    [
                        {
                            "type": "eP",
                            "title": "ePrescription",
                            "date": "2024-11-15",
                            "format": "FHIR",
                            "endpoint": f"/api/patient/{patient_id}/document/eP/",
                        },
                        {
                            "type": "eD",
                            "title": "eDispensation",
                            "date": "2024-11-20",
                            "format": "FHIR",
                            "endpoint": f"/api/patient/{patient_id}/document/eD/",
                        },
                    ]
                )

            if country.code in ["IE", "AT"]:
                available_documents.append(
                    {
                        "type": "LAB",
                        "title": "Laboratory Report",
                        "date": "2024-11-10",
                        "format": "CDA",
                        "endpoint": f"/api/patient/{patient_id}/document/LAB/",
                    }
                )

            patient_data = {
                "patient_id": patient_id,
                "country_code": country_code,
                "country_name": country.name,
                "name": f"{data.get('first_name', 'John')} {data.get('last_name', 'Doe')}",
                "birth_date": data.get("birth_date", "1980-01-01"),
                "gender": data.get("gender", "M"),
                "lookup_timestamp": __import__("datetime").datetime.now().isoformat(),
                "ism_version": ism.mask_version,
                "available_documents": available_documents,
            }

            return Response({"success": True, "patient": patient_data})
        else:
            return Response(
                {"success": False, "error": "Patient ID required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except Exception as e:
        logger.error(f"Error in patient lookup: {e}")
        return Response(
            {"success": False, "error": "Internal server error", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([AllowAny])  # Allow access for Java portal integration
def get_patient_document(request, patient_id, document_type):
    """
    API endpoint to retrieve specific patient document (CDA or FHIR)
    """
    # Audit log document access
    user_info = (
        request.user.username
        if request.user.is_authenticated
        else f"anonymous_{request.META.get('REMOTE_ADDR', 'unknown')}"
    )
    audit_logger.info(
        f"Document access: patient={patient_id}, type={document_type}, "
        f"user={user_info}"
    )

    # Mock document data - replace with actual document retrieval
    if document_type == "PS":
        # Return CDA Patient Summary
        document = {
            "format": "CDA",
            "content_type": "application/xml",
            "document": """<?xml version="1.0" encoding="UTF-8"?>
            <ClinicalDocument xmlns="urn:hl7-org:v3">
                <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
                <templateId root="1.3.6.1.4.1.12559.11.10.1.3.1.1.3"/>
                <id extension="{}" root="1.3.6.1.4.1.12559.11.10.1.3.1.1.3"/>
                <title>Patient Summary</title>
                <!-- CDA content here -->
            </ClinicalDocument>""".format(
                patient_id
            ),
        }
    elif document_type == "eP":
        # Return FHIR Bundle
        document = {
            "format": "FHIR",
            "content_type": "application/fhir+json",
            "document": {
                "resourceType": "Bundle",
                "type": "document",
                "entry": [
                    {
                        "resource": {
                            "resourceType": "MedicationRequest",
                            "id": f"{patient_id}-prescription-1",
                            "status": "active",
                            "medicationCodeableConcept": {"text": "Aspirin 100mg"},
                        }
                    }
                ],
            },
        }
    else:
        return Response(
            {"error": "Document type not supported"}, status=status.HTTP_404_NOT_FOUND
        )

    return Response({"success": True, "document": document})
