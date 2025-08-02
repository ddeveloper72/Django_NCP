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
import logging
import os

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

                # Store the CDA match in session for later use
                request.session[f"patient_match_{patient_data.id}"] = {
                    "file_path": match.file_path,
                    "country_code": match.country_code,
                    "confidence_score": match.confidence_score,
                    "patient_data": match.patient_data,
                    "cda_content": match.cda_content,
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

        context = {
            "patient_data": patient_data,
            "cda_content": match_data["cda_content"],
            "source_country": match_data["country_code"],
            "confidence": round(match_data["confidence_score"] * 100, 1),
            "file_name": os.path.basename(match_data["file_path"]),
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
        response = HttpResponse(
            match_data["cda_content"], content_type="text/html"
        )
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

        # For now, we'll create a placeholder ORCD view
        # In a real implementation, this would extract the base64 PDF from L1 CDA
        context = {
            "patient_data": patient_data,
            "source_country": match_data["country_code"],
            "confidence": round(match_data["confidence_score"] * 100, 1),
            "file_name": os.path.basename(match_data["file_path"]),
            "orcd_available": True,  # This would be determined by checking L1 CDA for base64 PDF
        }

        return render(request, "patient_data/patient_orcd.html", context, using="jinja2")

    except PatientData.DoesNotExist:
        messages.error(request, "Patient data not found.")
        return redirect("patient_data:patient_data_form")


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
