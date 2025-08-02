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
                status=404,
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
                status=404,
            )

        try:
            pdf_attachments = pdf_service.extract_pdfs_from_xml(orcd_cda_content)

            if not pdf_attachments or attachment_index >= len(pdf_attachments):
                return HttpResponse(
                    f"<html><body><h1>PDF not found</h1><p>PDF attachment not found in {cda_type_used} CDA.</p></body></html>",
                    status=404,
                )

            # Get the requested PDF attachment
            pdf_attachment = pdf_attachments[attachment_index]
            pdf_data = pdf_attachment["data"]
            filename = f"{patient_data.given_name}_{patient_data.family_name}_ORCD_{cda_type_used}.pdf"

            logger.info(
                f"Viewing ORCD PDF inline from {cda_type_used} CDA for patient {patient_id}"
            )

            # Return PDF response for inline viewing with enhanced headers
            response = pdf_service.get_pdf_response(
                pdf_data, filename, disposition="inline"
            )

            # Add headers to help with PDF display
            response["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"
            response["X-Content-Type-Options"] = "nosniff"
            response["X-Frame-Options"] = "SAMEORIGIN"

            return response

        except Exception as e:
            logger.error(f"Error viewing PDF: {e}")
            return HttpResponse(
                f"<html><body><h1>Error loading PDF</h1><p>Error extracting PDF from document: {e}</p></body></html>",
                status=500,
            )

    except PatientData.DoesNotExist:
        return HttpResponse(
            "<html><body><h1>Patient not found</h1><p>Patient data not found.</p></body></html>",
            status=404,
        )


def debug_orcd_pdf(request, patient_id):
    """Debug ORCD PDF extraction and display"""

    try:
        patient_data = PatientData.objects.get(id=patient_id)
        match_data = request.session.get(f"patient_match_{patient_id}")

        debug_info = []
        debug_info.append(f"<h2>PDF Debug Information for Patient {patient_id}</h2>")
        debug_info.append(
            f"<p><strong>Patient:</strong> {patient_data.given_name} {patient_data.family_name}</p>"
        )

        if not match_data:
            debug_info.append(
                "<p><strong>Error:</strong> No CDA document found in session</p>"
            )
        else:
            debug_info.append("<p><strong>Session data found:</strong> ✓</p>")

            # Check CDA content
            l1_cda_content = match_data.get("l1_cda_content")
            l3_cda_content = match_data.get("l3_cda_content")
            debug_info.append(
                f"<p><strong>L1 CDA Available:</strong> {'✓' if l1_cda_content else '✗'}</p>"
            )
            debug_info.append(
                f"<p><strong>L3 CDA Available:</strong> {'✓' if l3_cda_content else '✗'}</p>"
            )

            if l1_cda_content:
                debug_info.append(
                    f"<p><strong>L1 CDA Length:</strong> {len(l1_cda_content)} characters</p>"
                )
            if l3_cda_content:
                debug_info.append(
                    f"<p><strong>L3 CDA Length:</strong> {len(l3_cda_content)} characters</p>"
                )

            # Test PDF extraction
            pdf_service = ClinicalDocumentPDFService()
            orcd_cda_content = l1_cda_content or l3_cda_content or ""
            cda_type_used = (
                "L1" if l1_cda_content else ("L3" if l3_cda_content else "Unknown")
            )

            if orcd_cda_content:
                try:
                    pdf_attachments = pdf_service.extract_pdfs_from_xml(
                        orcd_cda_content
                    )
                    debug_info.append(
                        f"<p><strong>PDF Attachments Found:</strong> {len(pdf_attachments)}</p>"
                    )
                    debug_info.append(
                        f"<p><strong>CDA Type Used:</strong> {cda_type_used}</p>"
                    )

                    for i, pdf in enumerate(pdf_attachments):
                        debug_info.append(f"<p><strong>PDF {i + 1}:</strong></p>")
                        debug_info.append(f"<ul>")
                        debug_info.append(f"  <li>Size: {pdf['size']} bytes</li>")
                        debug_info.append(f"  <li>Filename: {pdf['filename']}</li>")
                        debug_info.append(
                            f"  <li>Valid PDF header: {'✓' if pdf['data'].startswith(b'%PDF') else '✗'}</li>"
                        )
                        debug_info.append(
                            f"  <li>First 100 bytes: {pdf['data'][:100]}</li>"
                        )
                        debug_info.append(f"</ul>")

                        # Create download link for this PDF
                        debug_info.append(
                            f"<p><a href='/patients/orcd/{patient_id}/download/{i}/' target='_blank'>Download PDF {i + 1}</a></p>"
                        )
                        debug_info.append(
                            f"<p><a href='/patients/orcd/{patient_id}/view/' target='_blank'>View PDF {i + 1} Inline</a></p>"
                        )

                except Exception as e:
                    debug_info.append(
                        f"<p><strong>PDF Extraction Error:</strong> {str(e)}</p>"
                    )
            else:
                debug_info.append(
                    "<p><strong>Error:</strong> No CDA content available</p>"
                )

        debug_info.append("<hr>")
        debug_info.append(
            f"<p><a href='/patients/{patient_id}/details/'>← Back to Patient Details</a></p>"
        )
        debug_info.append(
            f"<p><a href='/patients/{patient_id}/orcd/'>← Back to ORCD Viewer</a></p>"
        )

        html_content = f"""
        <html>
        <head>
            <title>ORCD PDF Debug - {patient_data.given_name} {patient_data.family_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h2 {{ color: #2c3e50; }}
                p {{ margin: 10px 0; }}
                ul {{ margin: 10px 0; }}
                a {{ color: #3498db; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            {''.join(debug_info)}
        </body>
        </html>
        """

        return HttpResponse(html_content)

    except PatientData.DoesNotExist:
        return HttpResponse(
            "<html><body><h1>Patient not found</h1><p>Patient data not found.</p></body></html>",
            status=404,
        )
    except Exception as e:
        return HttpResponse(
            f"<html><body><h1>Debug Error</h1><p>Error during debug: {str(e)}</p></body></html>",
            status=500,
        )


def orcd_pdf_base64(request, patient_id, attachment_index=0):
    """Return ORCD PDF as base64 data URL for direct embedding"""

    try:
        patient_data = PatientData.objects.get(id=patient_id)
        match_data = request.session.get(f"patient_match_{patient_id}")

        if not match_data:
            return HttpResponse("No CDA document found", status=404)

        # Initialize PDF service and extract PDFs
        pdf_service = ClinicalDocumentPDFService()
        l1_cda_content = match_data.get("l1_cda_content")
        l3_cda_content = match_data.get("l3_cda_content")
        orcd_cda_content = (
            l1_cda_content or l3_cda_content or match_data.get("cda_content", "")
        )

        if not orcd_cda_content:
            return HttpResponse("No CDA content available", status=404)

        try:
            pdf_attachments = pdf_service.extract_pdfs_from_xml(orcd_cda_content)

            if not pdf_attachments or attachment_index >= len(pdf_attachments):
                return HttpResponse("PDF attachment not found", status=404)

            # Get the PDF data
            pdf_attachment = pdf_attachments[attachment_index]
            pdf_data = pdf_attachment["data"]

            # Convert to base64
            import base64

            pdf_base64 = base64.b64encode(pdf_data).decode("utf-8")

            # Create HTML page with embedded PDF using data URL
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>ORCD PDF - {patient_data.given_name} {patient_data.family_name}</title>
                <style>
                    body {{ 
                        margin: 0; 
                        padding: 20px; 
                        font-family: Arial, sans-serif; 
                        background: #f5f5f5;
                    }}
                    .pdf-container {{ 
                        background: white; 
                        border-radius: 8px; 
                        padding: 20px; 
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    .pdf-header {{
                        margin-bottom: 20px;
                        padding-bottom: 15px;
                        border-bottom: 1px solid #eee;
                    }}
                    .pdf-viewer {{
                        width: 100%;
                        height: 800px;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                    }}
                    .fallback {{
                        text-align: center;
                        padding: 40px;
                        background: #f8f9fa;
                        border-radius: 4px;
                        border: 2px dashed #dee2e6;
                    }}
                    .btn {{
                        display: inline-block;
                        padding: 8px 16px;
                        background: #007bff;
                        color: white;
                        text-decoration: none;
                        border-radius: 4px;
                        margin: 5px;
                    }}
                    .btn:hover {{
                        background: #0056b3;
                    }}
                </style>
            </head>
            <body>
                <div class="pdf-container">
                    <div class="pdf-header">
                        <h2>ORCD PDF Document</h2>
                        <p><strong>Patient:</strong> {patient_data.given_name} {patient_data.family_name}</p>
                        <p><strong>Document Size:</strong> {len(pdf_data):,} bytes</p>
                        <a href="javascript:history.back()" class="btn">← Back</a>
                        <a href="/patients/orcd/{patient_id}/download/" class="btn">Download PDF</a>
                    </div>
                    
                    <!-- Primary: Object with data URL -->
                    <object 
                        class="pdf-viewer" 
                        data="data:application/pdf;base64,{pdf_base64}" 
                        type="application/pdf">
                        
                        <!-- Fallback: Embed with data URL -->
                        <embed 
                            src="data:application/pdf;base64,{pdf_base64}" 
                            type="application/pdf" 
                            width="100%" 
                            height="800px" />
                        
                        <!-- Final fallback -->
                        <div class="fallback">
                            <h3>PDF Preview Not Available</h3>
                            <p>Your browser doesn't support inline PDF viewing.</p>
                            <a href="/patients/orcd/{patient_id}/download/" class="btn">Download PDF Instead</a>
                        </div>
                    </object>
                </div>
                
                <script>
                    // Try to detect if PDF loaded successfully
                    setTimeout(function() {{
                        console.log('PDF data URL length: {len(pdf_base64)} characters');
                        console.log('PDF starts with valid header: {str(pdf_data.startswith(b"%PDF")).lower()}');
                    }}, 1000);
                </script>
            </body>
            </html>
            """

            return HttpResponse(html_content)

        except Exception as e:
            logger.error(f"Error creating base64 PDF: {{e}}")
            return HttpResponse(f"Error processing PDF: {{str(e)}}", status=500)

    except PatientData.DoesNotExist:
        return HttpResponse("Patient not found", status=404)


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
