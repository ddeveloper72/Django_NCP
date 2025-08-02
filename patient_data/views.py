"""
Patient Data Views
EU NCP Portal Patient Search and Document Retrieval
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .forms import PatientDataForm
from .models import PatientData
from .services import EUPatientSearchService, PatientCredentials
from .services.clinical_pdf_service import ClinicalDocumentPDFService
import logging
import os
import base64

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


def patient_data_view(request):
    """View for patient data form submission and display"""

    if request.method == "POST":
        form = PatientDataForm(request.POST)
        if form.is_valid():
            # Save the patient data
            patient_data = form.save()

            # Log the submission
            logger.info(
                "Patient data submitted: %s %s",
                patient_data.given_name,
                patient_data.family_name,
            )

            # Create search credentials
            credentials = PatientCredentials(
                given_name=patient_data.given_name,
                family_name=patient_data.family_name,
                birth_date=(
                    patient_data.birth_date.strftime("%Y%m%d")
                    if patient_data.birth_date
                    else ""
                ),
                gender=patient_data.gender,
                country_code=form.cleaned_data.get("country_code", ""),
                patient_id=form.cleaned_data.get("patient_id", ""),
            )

            # Search for matching CDA documents
            search_service = EUPatientSearchService()
            matches = search_service.search_patient(credentials)

            if matches:
                # Get the first (best) match
                match = matches[0]

                # Store the CDA match in session for later use with L1/L3 support
                request.session[f"patient_match_{patient_data.id}"] = {
                    "file_path": match.file_path,
                    "country_code": match.country_code,
                    "confidence_score": match.confidence_score,
                    "patient_data": match.patient_data,
                    "cda_content": match.cda_content,
                    # Enhanced L1/L3 CDA support
                    "l1_cda_content": match.l1_cda_content,
                    "l3_cda_content": match.l3_cda_content,
                    "l1_cda_path": match.l1_cda_path,
                    "l3_cda_path": match.l3_cda_path,
                    "preferred_cda_type": match.preferred_cda_type,
                    "has_l1": match.has_l1_cda(),
                    "has_l3": match.has_l3_cda(),
                }

                # Add success message
                messages.success(
                    request,
                    f"Patient found with {match.confidence_score*100:.1f}% confidence in {match.country_code} records!",
                )
            else:
                # No match found
                messages.warning(
                    request,
                    "No matching patient records found in EU member states database.",
                )

            # Redirect to patient details view
            return redirect("patient_data:patient_details", patient_id=patient_data.id)
        else:
            # Form has errors
            messages.error(request, "Please correct the errors below.")
    else:
        form = PatientDataForm()

    return render(
        request, "patient_data/patient_form.html", {"form": form}, using="jinja2"
    )


def patient_details_view(request, patient_id):
    """View for displaying patient details and CDA documents"""

    try:
        patient_data = PatientData.objects.get(id=patient_id)

        # Get CDA match from session
        match_data = request.session.get(f"patient_match_{patient_id}")

        context = {
            "patient_data": patient_data,
            "has_cda_match": match_data is not None,
        }

        if match_data:
            # Get patient summary from search service
            search_service = EUPatientSearchService()

            # Reconstruct match object for summary
            from .services import PatientMatch

            # Extract required fields from patient_data or use defaults
            patient_info = match_data.get("patient_data", {})
            patient_name_parts = patient_info.get("name", "Unknown Unknown").split(
                " ", 1
            )
            given_name = (
                patient_name_parts[0] if len(patient_name_parts) > 0 else "Unknown"
            )
            family_name = (
                patient_name_parts[1] if len(patient_name_parts) > 1 else "Unknown"
            )

            match = PatientMatch(
                patient_id=patient_info.get("id", "unknown"),
                given_name=given_name,
                family_name=family_name,
                birth_date=patient_info.get("birth_date", "unknown"),
                gender=patient_info.get("gender", "unknown"),
                country_code=match_data["country_code"],
                confidence_score=match_data["confidence_score"],
                file_path=match_data["file_path"],
                patient_data=match_data["patient_data"],
                cda_content=match_data["cda_content"],
                # Include L1/L3 CDA data
                l1_cda_content=match_data.get("l1_cda_content"),
                l3_cda_content=match_data.get("l3_cda_content"),
                l1_cda_path=match_data.get("l1_cda_path"),
                l3_cda_path=match_data.get("l3_cda_path"),
                preferred_cda_type=match_data.get("preferred_cda_type", "L3"),
            )

            patient_summary = search_service.get_patient_summary(match)

            # Get country display name
            from .forms import COUNTRY_CHOICES

            country_display = next(
                (
                    name
                    for code, name in COUNTRY_CHOICES
                    if code == match_data["country_code"]
                ),
                match_data["country_code"],
            )

            context.update(
                {
                    "patient_summary": patient_summary,
                    "match_confidence": round(match_data["confidence_score"] * 100, 1),
                    "source_country": match_data["country_code"],
                    "source_country_display": country_display,
                    "cda_file_name": os.path.basename(match_data["file_path"]),
                    # L1/L3 CDA availability information
                    "l1_available": match_data.get("has_l1", False),
                    "l3_available": match_data.get("has_l3", False),
                    "preferred_cda_type": match_data.get("preferred_cda_type", "L3"),
                }
            )

        return render(
            request, "patient_data/patient_details.html", context, using="jinja2"
        )

    except PatientData.DoesNotExist:
        messages.error(request, "Patient data not found.")
        return redirect("patient_data:patient_data_form")


def patient_cda_view(request, patient_id):
    """View for displaying CDA document in L3 browser format"""

    try:
        patient_data = PatientData.objects.get(id=patient_id)

        # Get CDA match from session
        match_data = request.session.get(f"patient_match_{patient_id}")

        if not match_data:
            messages.error(request, "No CDA document found for this patient.")
            return redirect("patient_data:patient_details", patient_id=patient_id)

        # For rendering, prefer L3 CDA as it has structured clinical content
        # Fall back to L1 CDA if L3 is not available
        l3_cda_content = match_data.get("l3_cda_content")
        l1_cda_content = match_data.get("l1_cda_content")

        rendering_cda_content = (
            l3_cda_content or l1_cda_content or match_data.get("cda_content", "")
        )
        rendering_cda_type = (
            "L3" if l3_cda_content else ("L1" if l1_cda_content else "Unknown")
        )
        rendering_file_path = (
            match_data.get("l3_cda_path")
            if l3_cda_content
            else (match_data.get("l1_cda_path") or match_data.get("file_path", ""))
        )

        context = {
            "patient_data": patient_data,
            "cda_content": rendering_cda_content,
            "source_country": match_data["country_code"],
            "confidence": round(match_data["confidence_score"] * 100, 1),
            "file_name": os.path.basename(rendering_file_path),
            "cda_type": rendering_cda_type,
            "l1_available": bool(l1_cda_content),
            "l3_available": bool(l3_cda_content),
            "is_l3_rendering": bool(l3_cda_content),
        }

        return render(request, "patient_data/patient_cda.html", context, using="jinja2")

    except PatientData.DoesNotExist:
        messages.error(request, "Patient data not found.")
        return redirect("patient_data:patient_data_form")


def download_cda_pdf(request, patient_id):
    """Download CDA document as XML file"""

    try:
        patient_data = PatientData.objects.get(id=patient_id)
        match_data = request.session.get(f"patient_match_{patient_id}")

        if not match_data:
            messages.error(request, "No CDA document found for this patient.")
            return redirect("patient_data:patient_details", patient_id=patient_id)

        # Return the XML content for download
        response = HttpResponse(
            match_data["cda_content"], content_type="application/xml"
        )
        response["Content-Disposition"] = (
            f'attachment; filename="patient_cda_{patient_id}.xml"'
        )

        return response

    except PatientData.DoesNotExist:
        messages.error(request, "Patient data not found.")
        return redirect("patient_data:patient_data_form")


def download_cda_html(request, patient_id):
    """Download CDA document as HTML transcoded view"""

    try:
        patient_data = PatientData.objects.get(id=patient_id)
        match_data = request.session.get(f"patient_match_{patient_id}")

        if not match_data:
            messages.error(request, "No CDA document found for this patient.")
            return redirect("patient_data:patient_details", patient_id=patient_id)

        # Return the HTML content for download
        # The CDA content should already be in HTML format from the L3 transformation
        response = HttpResponse(match_data["cda_content"], content_type="text/html")
        response["Content-Disposition"] = (
            f'attachment; filename="patient_cda_{patient_id}.html"'
        )

        return response

    except PatientData.DoesNotExist:
        messages.error(request, "Patient data not found.")
        return redirect("patient_data:patient_data_form")


def patient_orcd_view(request, patient_id):
    """View for displaying ORCD (Original Clinical Document) PDF preview"""

    try:
        patient_data = PatientData.objects.get(id=patient_id)
        match_data = request.session.get(f"patient_match_{patient_id}")

        if not match_data:
            messages.error(request, "No CDA document found for this patient.")
            return redirect("patient_data:patient_details", patient_id=patient_id)

        # Initialize PDF service
        pdf_service = ClinicalDocumentPDFService()

        # For ORCD, we prefer L1 CDA as it typically contains the embedded PDF
        # Fall back to L3 CDA if L1 is not available
        l1_cda_content = match_data.get("l1_cda_content")
        l3_cda_content = match_data.get("l3_cda_content")

        # Try L1 first for ORCD extraction
        orcd_cda_content = (
            l1_cda_content or l3_cda_content or match_data.get("cda_content", "")
        )
        cda_type_used = (
            "L1" if l1_cda_content else ("L3" if l3_cda_content else "Unknown")
        )

        pdf_attachments = []
        orcd_available = False

        if orcd_cda_content:
            try:
                pdf_attachments = pdf_service.extract_pdfs_from_xml(orcd_cda_content)
                orcd_available = len(pdf_attachments) > 0
                logger.info(
                    f"ORCD extraction from {cda_type_used} CDA: {len(pdf_attachments)} PDFs found"
                )
            except Exception as e:
                logger.error(f"Error extracting PDFs from {cda_type_used} CDA: {e}")

        context = {
            "patient_data": patient_data,
            "source_country": match_data["country_code"],
            "confidence": round(match_data["confidence_score"] * 100, 1),
            "file_name": os.path.basename(
                match_data.get("l1_cda_path") or match_data.get("file_path", "")
            ),
            "orcd_available": orcd_available,
            "pdf_attachments": pdf_attachments,
            "cda_type_used": cda_type_used,
            "l1_available": bool(l1_cda_content),
            "l3_available": bool(l3_cda_content),
        }

        return render(
            request, "patient_data/patient_orcd.html", context, using="jinja2"
        )

    except PatientData.DoesNotExist:
        messages.error(request, "Patient data not found.")
        return redirect("patient_data:patient_data_form")


def download_orcd_pdf(request, patient_id, attachment_index=0):
    """Download ORCD PDF attachment"""

    try:
        patient_data = PatientData.objects.get(id=patient_id)
        match_data = request.session.get(f"patient_match_{patient_id}")

        if not match_data:
            messages.error(request, "No CDA document found for this patient.")
            return redirect("patient_data:patient_details", patient_id=patient_id)

        # Initialize PDF service and extract PDFs
        pdf_service = ClinicalDocumentPDFService()

        # For ORCD download, prefer L1 CDA
        l1_cda_content = match_data.get("l1_cda_content")
        l3_cda_content = match_data.get("l3_cda_content")
        orcd_cda_content = (
            l1_cda_content or l3_cda_content or match_data.get("cda_content", "")
        )
        cda_type_used = (
            "L1" if l1_cda_content else ("L3" if l3_cda_content else "Unknown")
        )

        if not orcd_cda_content:
            messages.error(request, "No CDA content available.")
            return redirect("patient_data:patient_orcd_view", patient_id=patient_id)

        try:
            pdf_attachments = pdf_service.extract_pdfs_from_xml(orcd_cda_content)

            if not pdf_attachments or attachment_index >= len(pdf_attachments):
                messages.error(
                    request, f"PDF attachment not found in {cda_type_used} CDA."
                )
                return redirect("patient_data:patient_orcd_view", patient_id=patient_id)

            # Get the requested PDF attachment
            pdf_attachment = pdf_attachments[attachment_index]
            pdf_data = pdf_attachment["data"]
            filename = f"{patient_data.given_name}_{patient_data.family_name}_ORCD_{cda_type_used}.pdf"

            logger.info(
                f"Downloaded ORCD PDF from {cda_type_used} CDA for patient {patient_id}"
            )

            # Return PDF response
            return pdf_service.get_pdf_response(
                pdf_data, filename, disposition="attachment"
            )

        except Exception as e:
            logger.error(f"Error downloading PDF: {e}")
            messages.error(request, "Error extracting PDF from document.")
            return redirect("patient_data:patient_orcd_view", patient_id=patient_id)

    except PatientData.DoesNotExist:
        messages.error(request, "Patient data not found.")
        return redirect("patient_data:patient_data_form")


def view_orcd_pdf(request, patient_id, attachment_index=0):
    """View ORCD PDF inline for fullscreen preview"""

    try:
        patient_data = PatientData.objects.get(id=patient_id)
        match_data = request.session.get(f"patient_match_{patient_id}")

        if not match_data:
            return HttpResponse(
                "<html><body><h1>No CDA document found</h1><p>Please return to the patient details page.</p></body></html>",
                status=404
            )

        # Initialize PDF service and extract PDFs
        pdf_service = ClinicalDocumentPDFService()

        # For ORCD viewing, prefer L1 CDA
        l1_cda_content = match_data.get("l1_cda_content")
        l3_cda_content = match_data.get("l3_cda_content")
        orcd_cda_content = (
            l1_cda_content or l3_cda_content or match_data.get("cda_content", "")
        )
        cda_type_used = (
            "L1" if l1_cda_content else ("L3" if l3_cda_content else "Unknown")
        )

        if not orcd_cda_content:
            return HttpResponse(
                "<html><body><h1>No CDA content available</h1><p>No document content could be retrieved.</p></body></html>",
                status=404
            )

        try:
            pdf_attachments = pdf_service.extract_pdfs_from_xml(orcd_cda_content)

            if not pdf_attachments or attachment_index >= len(pdf_attachments):
                return HttpResponse(
                    f"<html><body><h1>PDF not found</h1><p>PDF attachment not found in {cda_type_used} CDA.</p></body></html>",
                    status=404
                )

            # Get the requested PDF attachment
            pdf_attachment = pdf_attachments[attachment_index]
            pdf_data = pdf_attachment["data"]
            filename = f"{patient_data.given_name}_{patient_data.family_name}_ORCD_{cda_type_used}.pdf"

            logger.info(
                f"Viewing ORCD PDF inline from {cda_type_used} CDA for patient {patient_id}"
            )

            # Return PDF response for inline viewing
            return pdf_service.get_pdf_response(
                pdf_data, filename, disposition="inline"
            )

        except Exception as e:
            logger.error(f"Error viewing PDF: {e}")
            return HttpResponse(
                f"<html><body><h1>Error loading PDF</h1><p>Error extracting PDF from document: {e}</p></body></html>",
                status=500
            )

    except PatientData.DoesNotExist:
        return HttpResponse(
            "<html><body><h1>Patient not found</h1><p>Patient data not found.</p></body></html>",
            status=404
        )


# ========================================
# Legacy Views (Minimal Implementation)
# ========================================


@login_required
def patient_search_view(request):
    """Legacy patient search view - redirect to new form"""
    return redirect("patient_data:patient_data_form")


@login_required
def patient_search_results(request):
    """Legacy patient search results view"""
    return render(
        request,
        "patient_data/search_results.html",
        {"message": "Please use the new patient search form."},
        using="jinja2",
    )
