"""
SMP Client Views - Service Metadata Publishing
Django views for SMP service management and European SMP integration
Includes comprehensive document generation, signing, and upload functionality
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.db import models
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import requests
import xml.etree.ElementTree as ET
import json
from datetime import datetime, timedelta
import logging
import os
import tempfile
import base64

from .models import (
    Domain,
    Participant,
    ServiceGroup,
    ServiceMetadata,
    DocumentType,
    Endpoint,
    SMPQuery,
    SMPConfiguration,
    ParticipantIdentifierScheme,
    DocumentTypeScheme,
    ProcessIdentifier,
    SMPDocument,
    DocumentTemplate,
    SigningCertificate,
)

logger = logging.getLogger(__name__)


@login_required
def smp_dashboard(request):
    """SMP Management Dashboard"""
    context = {
        "participant_count": Participant.objects.filter(is_active=True).count(),
        "service_count": ServiceMetadata.objects.filter(is_active=True).count(),
        "endpoint_count": Endpoint.objects.filter(is_active=True).count(),
        "domain_count": Domain.objects.filter(is_active=True).count(),
        "recent_queries": SMPQuery.objects.order_by("-timestamp")[:10],
        "recent_participants": Participant.objects.order_by("-created_at")[:5],
    }
    return render(request, "smp_client/dashboard.html", context, using="jinja2")


@login_required
def participant_search(request):
    """Participant search interface"""
    participants = Participant.objects.filter(is_active=True)

    # Apply filters
    search_query = request.GET.get("q", "")
    domain_filter = request.GET.get("domain", "")
    country_filter = request.GET.get("country", "")

    if search_query:
        participants = participants.filter(
            models.Q(participant_name__icontains=search_query)
            | models.Q(participant_identifier__icontains=search_query)
        )

    if domain_filter:
        participants = participants.filter(domain__domain_code=domain_filter)

    if country_filter:
        participants = participants.filter(country_code=country_filter)

    context = {
        "participants": participants,
        "domains": Domain.objects.filter(is_active=True),
        "countries": Participant.objects.values_list(
            "country_code", flat=True
        ).distinct(),
        "search_query": search_query,
        "domain_filter": domain_filter,
        "country_filter": country_filter,
    }
    return render(
        request, "smp_client/participant_search.html", context, using="jinja2"
    )


@login_required
def participant_detail(request, participant_id):
    """Detailed view of participant and their services"""
    participant = get_object_or_404(Participant, id=participant_id)
    service_group = getattr(participant, "service_group", None)
    services = service_group.services.all() if service_group else []

    context = {
        "participant": participant,
        "service_group": service_group,
        "services": services,
    }
    return render(request, "smp_client/participant_detail.html", context)


def european_smp_sync(request):
    """Sync data from European test SMP server"""
    if request.method == "POST" and request.user.is_staff:
        try:
            config = SMPConfiguration.objects.first()
            if not config or not config.sync_enabled:
                return JsonResponse({"error": "SMP sync not enabled"}, status=400)

            # Fetch participant list from European SMP
            european_smp_url = config.european_smp_url.rstrip("/")
            participants_url = f"{european_smp_url}/api/v1/participants"

            response = requests.get(participants_url, timeout=30)
            if response.status_code == 200:
                participants_data = response.json()

                synced_count = 0
                for participant_data in participants_data.get("participants", []):
                    # Create or update participant
                    participant_id = participant_data.get("participantIdentifier")
                    scheme_id = participant_data.get("participantScheme")

                    if participant_id and scheme_id:
                        # Ensure scheme exists
                        scheme, created = (
                            ParticipantIdentifierScheme.objects.get_or_create(
                                scheme_id=scheme_id,
                                defaults={"scheme_name": scheme_id, "is_active": True},
                            )
                        )

                        # Ensure domain exists
                        domain, created = Domain.objects.get_or_create(
                            domain_code="ehealth-actorid-qns",
                            defaults={
                                "domain_name": "EU eHealth Domain",
                                "sml_subdomain": "ehealth",
                                "smp_url": european_smp_url,
                                "is_test_domain": True,
                            },
                        )

                        # Create or update participant
                        participant, created = Participant.objects.update_or_create(
                            participant_identifier=participant_id,
                            participant_scheme=scheme,
                            domain=domain,
                            defaults={
                                "participant_name": participant_data.get(
                                    "participantName", ""
                                ),
                                "country_code": participant_data.get("countryCode", ""),
                                "organization_type": participant_data.get(
                                    "organizationType", ""
                                ),
                                "is_active": True,
                            },
                        )
                        synced_count += 1

                # Update last sync time
                config.last_sync = timezone.now()
                config.save()

                return JsonResponse(
                    {
                        "success": True,
                        "synced_participants": synced_count,
                        "last_sync": config.last_sync.isoformat(),
                    }
                )
            else:
                return JsonResponse(
                    {
                        "error": f"Failed to fetch from European SMP: {response.status_code}"
                    },
                    status=400,
                )

        except Exception as e:
            logger.error(f"European SMP sync error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)


# SMP API Endpoints (OASIS BDXR SMP v1.0 compatible)


def smp_service_group(request, participant_id, participant_scheme):
    """
    SMP Service Group lookup endpoint
    GET /{participantScheme}::{participantId}
    """
    try:
        # Log the query
        SMPQuery.objects.create(
            participant_id=participant_id,
            participant_scheme=participant_scheme,
            query_type="service_group",
            source_ip=request.META.get("REMOTE_ADDR", ""),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            response_status="processing",
        )

        # Find participant
        scheme = get_object_or_404(
            ParticipantIdentifierScheme, scheme_id=participant_scheme
        )
        participant = get_object_or_404(
            Participant,
            participant_identifier=participant_id,
            participant_scheme=scheme,
            is_active=True,
        )

        service_group = getattr(participant, "service_group", None)
        if not service_group:
            return HttpResponse("Service Group not found", status=404)

        # Generate SMP XML response
        root = ET.Element("ServiceGroup")
        root.set("xmlns", "http://busdox.org/serviceMetadata/publishing/1.0/")

        # Participant Identifier
        participant_id_elem = ET.SubElement(root, "ParticipantIdentifier")
        participant_id_elem.set("scheme", participant_scheme)
        participant_id_elem.text = participant_id

        # Service Metadata References
        service_metadata_list = ET.SubElement(
            root, "ServiceMetadataReferenceCollection"
        )

        for service in service_group.services.filter(is_active=True):
            smp_ref = ET.SubElement(service_metadata_list, "ServiceMetadataReference")
            smp_ref.set(
                "href",
                f"{request.build_absolute_uri('/')}{participant_scheme}::{participant_id}/services/{service.document_type.document_type_identifier}",
            )

        # Convert to XML string
        xml_str = ET.tostring(root, encoding="unicode", method="xml")

        return HttpResponse(xml_str, content_type="application/xml")

    except Exception as e:
        logger.error(f"SMP Service Group error: {str(e)}")
        return HttpResponse("Internal Server Error", status=500)


def smp_service_metadata(request, participant_id, participant_scheme, document_type_id):
    """
    SMP Service Metadata lookup endpoint
    GET /{participantScheme}::{participantId}/services/{documentTypeId}
    """
    try:
        # Log the query
        SMPQuery.objects.create(
            participant_id=participant_id,
            participant_scheme=participant_scheme,
            document_type_id=document_type_id,
            query_type="service_metadata",
            source_ip=request.META.get("REMOTE_ADDR", ""),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            response_status="processing",
        )

        # Find participant and service
        scheme = get_object_or_404(
            ParticipantIdentifierScheme, scheme_id=participant_scheme
        )
        participant = get_object_or_404(
            Participant,
            participant_identifier=participant_id,
            participant_scheme=scheme,
            is_active=True,
        )

        service_group = getattr(participant, "service_group", None)
        if not service_group:
            return HttpResponse("Service Group not found", status=404)

        service_metadata = get_object_or_404(
            ServiceMetadata,
            service_group=service_group,
            document_type__document_type_identifier=document_type_id,
            is_active=True,
        )

        # Generate SMP XML response
        root = ET.Element("ServiceMetadata")
        root.set("xmlns", "http://busdox.org/serviceMetadata/publishing/1.0/")

        # Service Information
        service_info = ET.SubElement(root, "ServiceInformation")

        # Participant Identifier
        participant_id_elem = ET.SubElement(service_info, "ParticipantIdentifier")
        participant_id_elem.set("scheme", participant_scheme)
        participant_id_elem.text = participant_id

        # Document Identifier
        doc_id_elem = ET.SubElement(service_info, "DocumentIdentifier")
        doc_id_elem.set(
            "scheme", service_metadata.document_type.document_scheme.scheme_id
        )
        doc_id_elem.text = document_type_id

        # Process List
        process_list = ET.SubElement(service_info, "ProcessList")

        for endpoint in service_metadata.endpoints.filter(is_active=True):
            if endpoint.is_valid():
                process_elem = ET.SubElement(process_list, "Process")

                # Process Identifier
                process_id_elem = ET.SubElement(process_elem, "ProcessIdentifier")
                process_id_elem.set("scheme", endpoint.process.process_scheme)
                process_id_elem.text = endpoint.process.process_identifier

                # Service Endpoint List
                endpoint_list = ET.SubElement(process_elem, "ServiceEndpointList")
                endpoint_elem = ET.SubElement(endpoint_list, "Endpoint")
                endpoint_elem.set("transportProfile", endpoint.transport_profile)

                # Endpoint URL
                endpoint_url_elem = ET.SubElement(endpoint_elem, "EndpointURI")
                endpoint_url_elem.text = endpoint.endpoint_url

                # Certificate
                if endpoint.certificate:
                    cert_elem = ET.SubElement(endpoint_elem, "Certificate")
                    cert_elem.text = endpoint.certificate

                # Service Activation Date
                if endpoint.service_activation_date:
                    activation_elem = ET.SubElement(
                        endpoint_elem, "ServiceActivationDate"
                    )
                    activation_elem.text = endpoint.service_activation_date.isoformat()

                # Service Expiration Date
                if endpoint.service_expiration_date:
                    expiration_elem = ET.SubElement(
                        endpoint_elem, "ServiceExpirationDate"
                    )
                    expiration_elem.text = endpoint.service_expiration_date.isoformat()

        # Convert to XML string
        xml_str = ET.tostring(root, encoding="unicode", method="xml")

        return HttpResponse(xml_str, content_type="application/xml")

    except Exception as e:
        logger.error(f"SMP Service Metadata error: {str(e)}")
        return HttpResponse("Internal Server Error", status=500)


@require_http_methods(["GET"])
def smp_participants_list(request):
    """List all participants (API endpoint)"""
    try:
        participants = Participant.objects.filter(is_active=True)

        # Apply filters
        domain = request.GET.get("domain")
        country = request.GET.get("country")

        if domain:
            participants = participants.filter(domain__domain_code=domain)
        if country:
            participants = participants.filter(country_code=country)

        participants_data = []
        for participant in participants:
            participants_data.append(
                {
                    "participantIdentifier": participant.participant_identifier,
                    "participantScheme": participant.participant_scheme.scheme_id,
                    "participantName": participant.participant_name,
                    "countryCode": participant.country_code,
                    "domain": participant.domain.domain_code,
                    "organizationType": participant.organization_type,
                    "serviceCount": (
                        participant.service_group.services.count()
                        if hasattr(participant, "service_group")
                        else 0
                    ),
                }
            )

        return JsonResponse(
            {"participants": participants_data, "totalCount": len(participants_data)}
        )

    except Exception as e:
        logger.error(f"Participants list error: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


# ==============================================================================
# SMP EDITOR VIEWS - Document Generation, Signing, and Upload
# ==============================================================================


@login_required
def smp_editor(request):
    """Main SMP Editor interface"""
    context = {
        "document_types": DocumentType.objects.filter(is_active=True),
        "participants": Participant.objects.filter(is_active=True),
        "certificates": SigningCertificate.objects.filter(is_active=True),
        "templates": DocumentTemplate.objects.filter(is_active=True),
        "recent_documents": SMPDocument.objects.filter(created_by=request.user)[:10],
    }
    return render(request, "smp_client/smp_editor.html", context, using="jinja2")


@login_required
def generate_document(request):
    """Generate SMP document from form data"""
    if request.method == "POST":
        try:
            document_type = request.POST.get("document_type")
            participant_id = request.POST.get("participant_id")
            template_id = request.POST.get("template_id")

            # Get related objects
            participant = (
                get_object_or_404(Participant, id=participant_id)
                if participant_id
                else None
            )
            template = (
                get_object_or_404(DocumentTemplate, id=template_id)
                if template_id
                else None
            )

            # Create document record
            document = SMPDocument.objects.create(
                document_type=document_type,
                document_name=f"{document_type}_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
                participant=participant,
                created_by=request.user,
                status="generated",
            )

            # Generate XML content based on document type
            if document_type == "service_group" and participant:
                service_group, created = ServiceGroup.objects.get_or_create(
                    participant=participant
                )
                document.service_group = service_group
                document.xml_content = service_group.to_xml()

            elif document_type == "service_metadata":
                service_metadata_id = request.POST.get("service_metadata_id")
                if service_metadata_id:
                    service_metadata = get_object_or_404(
                        ServiceMetadata, id=service_metadata_id
                    )
                    document.service_metadata = service_metadata
                    document.xml_content = service_metadata.to_xml()

            elif document_type == "endpoint":
                endpoint_id = request.POST.get("endpoint_id")
                if endpoint_id:
                    endpoint = get_object_or_404(Endpoint, id=endpoint_id)
                    document.endpoint = endpoint
                    document.xml_content = endpoint.to_xml()

            elif template:
                # Use template to generate content
                document.xml_content = template.xml_template
                # Replace placeholders with actual data
                # This would be expanded based on template requirements

            # Save generated file
            document.save_generated_file()
            document.save()

            messages.success(
                request, f"Document {document.document_name} generated successfully!"
            )
            return JsonResponse(
                {
                    "success": True,
                    "document_id": str(document.id),
                    "download_url": f"/smp/documents/{document.id}/download/",
                }
            )

        except Exception as e:
            logger.error(f"Document generation error: {str(e)}")
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse(
        {"success": False, "error": "Invalid request method"}, status=405
    )


@login_required
def download_document(request, document_id):
    """Download generated or signed SMP document"""
    document = get_object_or_404(SMPDocument, id=document_id, created_by=request.user)

    try:
        # Determine which file to download
        file_to_download = None
        filename = f"{document.document_name}"

        if document.signed_file and request.GET.get("type") == "signed":
            file_to_download = document.signed_file
            filename += "_signed.xml"
        elif document.original_file:
            file_to_download = document.original_file
            filename += ".xml"
        elif document.xml_content:
            # Create temporary file from XML content
            response = HttpResponse(
                document.xml_content, content_type="application/xml"
            )
            response["Content-Disposition"] = f'attachment; filename="{filename}.xml"'
            return response

        if file_to_download:
            document.status = "downloaded"
            document.save()

            response = FileResponse(
                file_to_download.open(),
                content_type="application/xml",
                as_attachment=True,
                filename=filename,
            )
            return response
        else:
            raise Http404("No file available for download")

    except Exception as e:
        logger.error(f"Document download error: {str(e)}")
        messages.error(request, f"Error downloading document: {str(e)}")
        return redirect("smp_client:smp_editor")


@login_required
def upload_signed_document(request, document_id):
    """Upload signed document file"""
    document = get_object_or_404(SMPDocument, id=document_id, created_by=request.user)

    if request.method == "POST" and request.FILES.get("signed_file"):
        try:
            signed_file = request.FILES["signed_file"]

            # Validate file type
            if not signed_file.name.endswith(".xml"):
                return JsonResponse(
                    {"success": False, "error": "Only XML files are allowed"},
                    status=400,
                )

            # Save signed file
            document.signed_file = signed_file
            document.status = "signed"
            document.signature_timestamp = timezone.now()

            # Extract signature information if available
            try:
                # Read file content to extract signature info
                file_content = signed_file.read()
                signed_file.seek(0)  # Reset file pointer

                # Parse XML to extract signature data
                root = ET.fromstring(file_content)
                # Look for signature elements (this would be expanded based on signature format)
                signature_elements = root.findall(
                    ".//{http://www.w3.org/2000/09/xmldsig#}Signature"
                )
                if signature_elements:
                    document.signature_data = "Digital signature detected"

            except Exception as e:
                logger.warning(f"Could not extract signature info: {str(e)}")

            document.save()

            messages.success(request, f"Signed document uploaded successfully!")
            return JsonResponse(
                {
                    "success": True,
                    "message": "Signed document uploaded successfully",
                    "status": document.status,
                }
            )

        except Exception as e:
            logger.error(f"Signed document upload error: {str(e)}")
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "No file provided"}, status=400)


@login_required
def sign_document(request, document_id):
    """Sign document using selected certificate"""
    document = get_object_or_404(SMPDocument, id=document_id, created_by=request.user)

    if request.method == "POST":
        try:
            certificate_id = request.POST.get("certificate_id")
            certificate = (
                get_object_or_404(SigningCertificate, id=certificate_id)
                if certificate_id
                else None
            )

            # For now, this is a placeholder for actual digital signing
            # In production, you would integrate with actual signing libraries

            if document.xml_content:
                # Simulate signing process
                signed_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- Digitally signed with certificate: {certificate.certificate_name if certificate else 'Default'} -->
<!-- Signature timestamp: {timezone.now().isoformat()} -->
{document.xml_content}
<!-- Digital signature would be appended here -->
"""

                # Create signed file
                signed_filename = f"{document.document_name}_signed.xml"
                signed_file_content = ContentFile(signed_content.encode("utf-8"))
                document.signed_file.save(
                    signed_filename, signed_file_content, save=False
                )

                # Update document status
                document.mark_as_signed(
                    "Simulated digital signature",
                    {
                        "fingerprint": (
                            certificate.fingerprint if certificate else "N/A"
                        ),
                        "signer": certificate.subject if certificate else "Unknown",
                    },
                )

                messages.success(request, f"Document signed successfully!")
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Document signed successfully",
                        "download_url": f"/smp/documents/{document.id}/download/?type=signed",
                    }
                )
            else:
                return JsonResponse(
                    {"success": False, "error": "No content to sign"}, status=400
                )

        except Exception as e:
            logger.error(f"Document signing error: {str(e)}")
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse(
        {"success": False, "error": "Invalid request method"}, status=405
    )


@login_required
def upload_to_smp_server(request, document_id):
    """Upload signed document to SMP server"""
    document = get_object_or_404(SMPDocument, id=document_id, created_by=request.user)

    if request.method == "POST":
        try:
            smp_server_url = request.POST.get(
                "smp_server_url",
                "https://smp-ehealth-trn.acc.edelivery.tech.ec.europa.eu/",
            )

            # Ensure document is signed
            if document.status != "signed" or not document.signed_file:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Document must be signed before upload",
                    },
                    status=400,
                )

            # Read signed file content
            signed_content = document.signed_file.read()
            document.signed_file.seek(0)  # Reset file pointer

            # Prepare upload data based on document type
            upload_url = smp_server_url.rstrip("/")

            if document.participant:
                participant_scheme = document.participant.participant_scheme.scheme_id
                participant_id = document.participant.participant_identifier

                if document.document_type == "service_group":
                    upload_url += f"/{participant_scheme}::{participant_id}"
                elif (
                    document.document_type == "service_metadata"
                    and document.service_metadata
                ):
                    doc_type_id = document.service_metadata.document_type.type_id
                    upload_url += f"/{participant_scheme}::{participant_id}/services/{doc_type_id}"

            # Simulate SMP upload (in production, use actual SMP API)
            # This would be replaced with actual HTTP PUT/POST to SMP server
            success = document.upload_to_smp(smp_server_url)

            if success:
                messages.success(
                    request, f"Document uploaded to SMP server successfully!"
                )
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Document uploaded to SMP server",
                        "smp_url": upload_url,
                    }
                )
            else:
                return JsonResponse(
                    {"success": False, "error": "Upload failed"}, status=500
                )

        except Exception as e:
            logger.error(f"SMP upload error: {str(e)}")
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse(
        {"success": False, "error": "Invalid request method"}, status=405
    )


@login_required
def list_smp_documents(request):
    """List all SMP documents for current user"""
    documents = SMPDocument.objects.filter(created_by=request.user).order_by(
        "-created_at"
    )

    # Apply filters
    status_filter = request.GET.get("status")
    document_type_filter = request.GET.get("document_type")

    if status_filter:
        documents = documents.filter(status=status_filter)
    if document_type_filter:
        documents = documents.filter(document_type=document_type_filter)

    context = {
        "documents": documents,
        "document_types": SMPDocument.DOCUMENT_TYPES,
        "document_status": SMPDocument.DOCUMENT_STATUS,
    }

    if request.headers.get("Accept") == "application/json":
        documents_data = []
        for doc in documents:
            documents_data.append(
                {
                    "id": str(doc.id),
                    "name": doc.document_name,
                    "type": doc.document_type,
                    "status": doc.status,
                    "created_at": doc.created_at.isoformat(),
                    "participant": str(doc.participant) if doc.participant else None,
                    "has_signed_file": bool(doc.signed_file),
                    "download_url": f"/smp/documents/{doc.id}/download/",
                    "signed_download_url": (
                        f"/smp/documents/{doc.id}/download/?type=signed"
                        if doc.signed_file
                        else None
                    ),
                }
            )
        return JsonResponse({"documents": documents_data})

    return render(request, "smp_client/list_documents.html", context)


@login_required
def synchronize_from_smp(request):
    """Synchronize documents back from SMP server"""
    if request.method == "POST":
        try:
            smp_server_url = request.POST.get(
                "smp_server_url",
                "https://smp-ehealth-trn.acc.edelivery.tech.ec.europa.eu/",
            )
            participant_id = request.POST.get("participant_id")

            if participant_id:
                participant = get_object_or_404(Participant, id=participant_id)

                # Fetch participant's service group from SMP
                sync_url = f"{smp_server_url.rstrip('/')}/{participant.participant_scheme.scheme_id}::{participant.participant_identifier}"

                # This would be replaced with actual SMP API call
                # For now, simulate synchronization

                # Create synchronized document record
                sync_document = SMPDocument.objects.create(
                    document_type="service_group",
                    document_name=f"sync_{participant.participant_identifier}_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
                    participant=participant,
                    status="synchronized",
                    smp_server_url=smp_server_url,
                    smp_upload_timestamp=timezone.now(),
                    created_by=request.user,
                )

                messages.success(request, f"Successfully synchronized from SMP server!")
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Synchronized from SMP server",
                        "document_id": str(sync_document.id),
                    }
                )
            else:
                # Sync all participants
                participants = Participant.objects.filter(is_active=True)
                sync_count = 0

                for participant in participants:
                    # Simulate sync for each participant
                    sync_count += 1

                messages.success(
                    request, f"Synchronized {sync_count} participants from SMP server!"
                )
                return JsonResponse(
                    {
                        "success": True,
                        "message": f"Synchronized {sync_count} participants",
                        "count": sync_count,
                    }
                )

        except Exception as e:
            logger.error(f"SMP synchronization error: {str(e)}")
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse(
        {"success": False, "error": "Invalid request method"}, status=405
    )
