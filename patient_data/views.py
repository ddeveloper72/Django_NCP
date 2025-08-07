"""
Patient Data Views
EU NCP Portal Patient Search and Document Retrieval
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.conf import settings
from .forms import PatientDataForm
from .models import PatientData
from .services import EUPatientSearchService, PatientCredentials
from .services.clinical_pdf_service import ClinicalDocumentPDFService
from xhtml2pdf import pisa
from io import BytesIO
import logging
import os
import base64
import json
import re
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


# REFACTOR: Data processing functions (moved from template for proper MVC separation)
def prepare_enhanced_section_data(sections):
    """
    Pre-process sections for template display
    Handles all value set lookups and field processing in Python
    
    Args:
        sections: Raw sections from enhanced CDA processor
    
    Returns:
        dict: Processed sections ready for simple template display
    """
    processed_sections = []
    
    for section in sections:
        processed_section = {
            'title': section.get('title', 'Unknown Section'),
            'type': section.get('type', 'unknown'),
            'section_code': section.get('section_code', ''),
            'entries': [],
            'has_entries': False,
            'medical_terminology_count': 0,
            'coded_entries_count': 0
        }
        
        # Process entries with proper field lookups
        if section.get('table_data'):
            for entry in section.get('table_data', []):
                processed_entry = process_entry_for_display(entry, section.get('section_code', ''))
                processed_section['entries'].append(processed_entry)
                
                # Update metrics
                if processed_entry.get('has_medical_terminology'):
                    processed_section['medical_terminology_count'] += 1
                if processed_entry.get('is_coded'):
                    processed_section['coded_entries_count'] += 1
        
        processed_section['has_entries'] = len(processed_section['entries']) > 0
        processed_sections.append(processed_section)
    
    return processed_sections


def process_entry_for_display(entry, section_code):
    """
    Process a single entry for template display
    Handles all field lookups and terminology resolution in Python
    
    Args:
        entry: Raw entry from CDA processor
        section_code: Section code for specialized processing
    
    Returns:
        dict: Processed entry with resolved terminology and display fields
    """
    processed_entry = {
        'original_entry': entry,
        'display_fields': {},
        'has_medical_terminology': False,
        'is_coded': False,
        'display_name': 'Unknown Item',
        'additional_info': {}
    }
    
    fields = entry.get('fields', {})
    
    # Handle different section types with specialized processing
    if section_code == "48765-2":  # Allergies
        processed_entry.update(process_allergy_entry(fields))
    elif section_code == "10160-0":  # Medications
        processed_entry.update(process_medication_entry(fields))
    elif section_code == "11450-4":  # Problems
        processed_entry.update(process_problem_entry(fields))
    else:
        processed_entry.update(process_generic_entry(fields))
    
    return processed_entry


def process_allergy_entry(fields):
    """Process allergy-specific fields with proper terminology lookup"""
    result = {
        'display_name': 'Unknown Allergen',
        'reaction': 'Unknown Reaction',
        'severity': 'Unknown Severity',
        'status': 'Active',
        'has_medical_terminology': False,
        'original_value': None
    }
    
    # Try multiple field name patterns for allergen (handles multilingual field names)
    allergen_patterns = ['Allergen DisplayName', 'Allergen Code', 'Allergène']
    for pattern in allergen_patterns:
        if pattern in fields:
            field_data = fields[pattern]
            if isinstance(field_data, dict):
                # Check if this field has value set information
                if field_data.get('has_valueset'):
                    result['has_medical_terminology'] = True
                    result['original_value'] = field_data.get('original_value')
                
                display_name = field_data.get('value') or field_data.get('display_name')
                if display_name and display_name not in ['Unknown', 'Unknown Allergen']:
                    result['display_name'] = display_name
                    break
            elif isinstance(field_data, str) and field_data not in ['Unknown', 'Unknown Allergen']:
                result['display_name'] = field_data
                break
    
    # Process reaction information
    reaction_patterns = ['Reaction DisplayName', 'Reaction Code', 'Réaction']
    for pattern in reaction_patterns:
        if pattern in fields:
            reaction_data = fields[pattern]
            if isinstance(reaction_data, dict):
                if reaction_data.get('has_valueset'):
                    result['has_medical_terminology'] = True
                
                reaction_name = reaction_data.get('value') or reaction_data.get('display_name')
                if reaction_name and reaction_name not in ['Unknown', 'Unknown Reaction']:
                    result['reaction'] = reaction_name
                    break
            elif isinstance(reaction_data, str) and reaction_data not in ['Unknown', 'Unknown Reaction']:
                result['reaction'] = reaction_data
                break
    
    # Process severity
    severity_patterns = ['Severity', 'Sévérité']
    for pattern in severity_patterns:
        if pattern in fields:
            severity_data = fields[pattern]
            if isinstance(severity_data, dict):
                severity_value = severity_data.get('value') or severity_data.get('display_name')
                if severity_value and severity_value != 'Unknown':
                    result['severity'] = severity_value
                    break
            elif isinstance(severity_data, str) and severity_data != 'Unknown':
                result['severity'] = severity_data
                break
    
    # Process status
    status_patterns = ['Status', 'Statut']
    for pattern in status_patterns:
        if pattern in fields:
            status_data = fields[pattern]
            if isinstance(status_data, dict):
                status_value = status_data.get('value') or status_data.get('display_name')
                if status_value:
                    result['status'] = status_value
                    break
            elif isinstance(status_data, str):
                result['status'] = status_data
                break
    
    return result


def process_medication_entry(fields):
    """Process medication-specific fields with proper terminology lookup"""
    result = {
        'display_name': 'Unknown Medication',
        'dosage': 'Not specified',
        'frequency': 'Not specified',
        'status': 'Active',
        'has_medical_terminology': False,
        'original_value': None
    }
    
    # Try multiple field name patterns for medication
    medication_patterns = ['Medication DisplayName', 'Medication Code', 'Médicament']
    for pattern in medication_patterns:
        if pattern in fields:
            field_data = fields[pattern]
            if isinstance(field_data, dict):
                if field_data.get('has_valueset'):
                    result['has_medical_terminology'] = True
                    result['original_value'] = field_data.get('original_value')
                
                display_name = field_data.get('value') or field_data.get('display_name')
                if display_name and display_name not in ['Unknown', 'Unknown Medication']:
                    result['display_name'] = display_name
                    break
            elif isinstance(field_data, str) and field_data not in ['Unknown', 'Unknown Medication']:
                result['display_name'] = field_data
                break
    
    # Process dosage
    if 'Dosage' in fields:
        dosage_data = fields['Dosage']
        if isinstance(dosage_data, dict):
            dosage_value = dosage_data.get('value') or dosage_data.get('display_name')
            if dosage_value:
                result['dosage'] = dosage_value
        elif isinstance(dosage_data, str):
            result['dosage'] = dosage_data
    
    # Process frequency
    frequency_patterns = ['Frequency', 'Fréquence']
    for pattern in frequency_patterns:
        if pattern in fields:
            frequency_data = fields[pattern]
            if isinstance(frequency_data, dict):
                frequency_value = frequency_data.get('value') or frequency_data.get('display_name')
                if frequency_value:
                    result['frequency'] = frequency_value
                    break
            elif isinstance(frequency_data, str):
                result['frequency'] = frequency_data
                break
    
    # Process status
    status_patterns = ['Status', 'Statut']
    for pattern in status_patterns:
        if pattern in fields:
            status_data = fields[pattern]
            if isinstance(status_data, dict):
                status_value = status_data.get('value') or status_data.get('display_name')
                if status_value:
                    result['status'] = status_value
                    break
            elif isinstance(status_data, str):
                result['status'] = status_data
                break
    
    return result


def process_problem_entry(fields):
    """Process problem/condition-specific fields with proper terminology lookup"""
    result = {
        'display_name': 'Unknown Condition',
        'onset_date': 'Not specified',
        'status': 'Active',
        'code': 'No Code',
        'has_medical_terminology': False,
        'original_value': None
    }
    
    # Try multiple field name patterns for problems/conditions
    problem_patterns = ['Problem DisplayName', 'Problem Code', 'Condition']
    for pattern in problem_patterns:
        if pattern in fields:
            field_data = fields[pattern]
            if isinstance(field_data, dict):
                if field_data.get('has_valueset'):
                    result['has_medical_terminology'] = True
                    result['original_value'] = field_data.get('original_value')
                
                display_name = field_data.get('value') or field_data.get('display_name')
                if display_name and display_name not in ['Unknown', 'Unknown Condition']:
                    result['display_name'] = display_name
                    break
            elif isinstance(field_data, str) and field_data not in ['Unknown', 'Unknown Condition']:
                result['display_name'] = field_data
                break
    
    # Process onset date
    onset_patterns = ['Onset Date', 'Date de diagnostic']
    for pattern in onset_patterns:
        if pattern in fields:
            onset_data = fields[pattern]
            if isinstance(onset_data, dict):
                onset_value = onset_data.get('value') or onset_data.get('display_name')
                if onset_value:
                    result['onset_date'] = onset_value
                    break
            elif isinstance(onset_data, str):
                result['onset_date'] = onset_data
                break
    
    # Process status
    status_patterns = ['Status', 'Statut']
    for pattern in status_patterns:
        if pattern in fields:
            status_data = fields[pattern]
            if isinstance(status_data, dict):
                status_value = status_data.get('value') or status_data.get('display_name')
                if status_value:
                    result['status'] = status_value
                    break
            elif isinstance(status_data, str):
                result['status'] = status_data
                break
    
    # Process code
    code_patterns = ['Code', 'Code ICD-10']
    for pattern in code_patterns:
        if pattern in fields:
            code_data = fields[pattern]
            if isinstance(code_data, dict):
                code_value = code_data.get('value') or code_data.get('display_name')
                if code_value:
                    result['code'] = code_value
                    break
            elif isinstance(code_data, str):
                result['code'] = code_data
                break
    
    return result


def process_generic_entry(fields):
    """Process generic entry fields with basic terminology lookup"""
    result = {
        'display_name': 'Unknown Item',
        'has_medical_terminology': False,
        'field_data': []
    }
    
    # Try common field patterns
    common_patterns = ['DisplayName', 'Name', 'Title', 'Description', 'Value']
    
    for pattern in common_patterns:
        if pattern in fields:
            field_data = fields[pattern]
            if isinstance(field_data, dict):
                if field_data.get('has_valueset'):
                    result['has_medical_terminology'] = True
                
                display_name = field_data.get('value') or field_data.get('display_name')
                if display_name and display_name != 'Unknown':
                    result['display_name'] = display_name
                    break
            elif isinstance(field_data, str) and field_data != 'Unknown':
                result['display_name'] = field_data
                break
    
    # Collect first 4 fields for generic display
    field_count = 0
    for field_name, field_info in fields.items():
        if field_count >= 4:
            break
        
        field_value = 'Unknown'
        has_valueset = False
        original_value = None
        
        if isinstance(field_info, dict):
            field_value = field_info.get('value') or field_info.get('display_name') or 'Unknown'
            has_valueset = field_info.get('has_valueset', False)
            original_value = field_info.get('original_value')
        elif isinstance(field_info, str):
            field_value = field_info
        
        result['field_data'].append({
            'name': field_name,
            'value': field_value,
            'has_valueset': has_valueset,
            'original_value': original_value
        })
        
        field_count += 1
    
    return result


def patient_data_view(request):
    """View for patient data form submission and display"""

    if request.method == "POST":
        form = PatientDataForm(request.POST)
        if form.is_valid():
            # Extract the NCP query parameters
            country_code = form.cleaned_data["country_code"]
            patient_id = form.cleaned_data["patient_id"]

            # Log the NCP query
            logger.info(
                "NCP Document Query: Patient ID %s from %s",
                patient_id,
                country_code,
            )

            # Create search credentials for NCP-to-NCP query
            credentials = PatientCredentials(
                country_code=country_code,
                patient_id=patient_id,
            )

            # Search for matching CDA documents
            search_service = EUPatientSearchService()
            matches = search_service.search_patient(credentials)

            if matches:
                # Get the first (best) match
                match = matches[0]

                # Create a temporary PatientData record for session storage
                # In real NCP workflow, this would be extracted from CDA response
                from .models import PatientData

                temp_patient = PatientData(
                    given_name=match.given_name,
                    family_name=match.family_name,
                    birth_date=match.birth_date,
                    gender=match.gender,
                )
                # Don't save to database - just use for ID generation
                temp_patient.id = hash(f"{country_code}_{patient_id}") % 1000000

                # Store the CDA match in session for later use with L1/L3 support
                request.session[f"patient_match_{temp_patient.id}"] = {
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
                    f"Patient documents found with {match.confidence_score*100:.1f}% confidence in {match.country_code} NCP!",
                )

                # Redirect to patient details view
                return redirect(
                    "patient_data:patient_details", patient_id=temp_patient.id
                )
            else:
                # No match found
                messages.warning(
                    request,
                    f"No patient documents found for ID '{patient_id}' in {country_code} NCP.",
                )
        else:
            # Form has errors
            messages.error(request, "Please correct the errors below.")
    else:
        # GET request - check for URL parameters to pre-fill form
        initial_data = {}

        # Check for country and patient_id parameters from test patient links
        country_param = request.GET.get("country")
        patient_id_param = request.GET.get("patient_id")

        if country_param and patient_id_param:
            initial_data["country_code"] = country_param
            initial_data["patient_id"] = patient_id_param
            logger.info(
                f"Pre-filling form with country={country_param}, patient_id={patient_id_param}"
            )

            # Auto-trigger search if both parameters are provided
            # This makes "Test NCP Query" buttons work seamlessly
            auto_search = request.GET.get("auto_search", "true")
            if auto_search.lower() == "true":
                # Create form with the data and validate it
                form = PatientDataForm(initial_data)
                if form.is_valid():
                    # Create search credentials for NCP-to-NCP query
                    credentials = PatientCredentials(
                        country_code=country_param,
                        patient_id=patient_id_param,
                    )

                    # Search for matching CDA documents
                    search_service = EUPatientSearchService()
                    matches = search_service.search_patient(credentials)

                    if matches:
                        # Get the first (best) match
                        match = matches[0]

                        # Create a temporary PatientData record for session storage
                        from .models import PatientData

                        temp_patient = PatientData(
                            given_name=match.given_name,
                            family_name=match.family_name,
                            birth_date=match.birth_date,
                            gender=match.gender,
                        )
                        # Don't save to database - just use for ID generation
                        temp_patient.id = (
                            hash(f"{country_param}_{patient_id_param}") % 1000000
                        )

                        # Store the match information in session for patient details view
                        session_key = f"patient_match_{temp_patient.id}"
                        request.session[session_key] = {
                            "patient_data": match.patient_data,
                            "match_score": match.match_score,
                            "confidence_score": match.confidence_score,
                            "l1_cda_content": match.l1_cda_content,
                            "l3_cda_content": match.l3_cda_content,
                            "l1_cda_path": match.l1_cda_path,
                            "l3_cda_path": match.l3_cda_path,
                            "available_documents": match.available_documents,
                            "file_path": getattr(match, "file_path", ""),
                        }

                        # Success message with match information
                        messages.success(
                            request,
                            f"Found patient: {match.given_name} {match.family_name} (ID: {match.patient_id}) "
                            f"from {match.country_code} NCP. Confidence: {match.confidence_score:.1%}",
                        )

                        # Redirect to patient details
                        return redirect(
                            "patient_data:patient_details", patient_id=temp_patient.id
                        )
                    else:
                        # No match found
                        messages.warning(
                            request,
                            f"No patient documents found for ID '{patient_id_param}' in {country_param} NCP.",
                        )

        form = PatientDataForm(initial=initial_data)

    return render(
        request, "patient_data/patient_form.html", {"form": form}, using="jinja2"
    )


def patient_details_view(request, patient_id):
    """View for displaying patient details and CDA documents"""

    # Check if this is an NCP query result (session data exists but no DB record)
    session_key = f"patient_match_{patient_id}"
    match_data = request.session.get(session_key)

    if match_data and not PatientData.objects.filter(id=patient_id).exists():
        # This is an NCP query result - create temp patient from session data
        patient_info = match_data["patient_data"]

        # Debug: Log what's in the session patient data
        logger.info(f"DEBUG: Session patient_info keys: {list(patient_info.keys())}")
        logger.info(
            f"DEBUG: Session given_name: '{patient_info.get('given_name', 'NOT_FOUND')}'"
        )
        logger.info(
            f"DEBUG: Session family_name: '{patient_info.get('family_name', 'NOT_FOUND')}'"
        )
        logger.info(
            f"DEBUG: Session birth_date: '{patient_info.get('birth_date', 'NOT_FOUND')}'"
        )
        logger.info(
            f"DEBUG: Session gender: '{patient_info.get('gender', 'NOT_FOUND')}'"
        )

        # Create a temporary patient object (not saved to DB)
        patient_data = PatientData(
            id=patient_id,
            given_name=patient_info.get("given_name", "Unknown"),
            family_name=patient_info.get("family_name", "Patient"),
            birth_date=patient_info.get("birth_date") or None,
            gender=patient_info.get("gender", ""),
        )

        logger.info(
            f"Created temporary patient object: {patient_data.given_name} {patient_data.family_name} for NCP query result: {patient_id}"
        )
    else:
        # Standard database lookup
        try:
            patient_data = PatientData.objects.get(id=patient_id)
        except PatientData.DoesNotExist:
            messages.error(request, "Patient data not found.")
            return redirect("patient_data:patient_data_form")

    # Debug session data
    logger.info("Looking for session data with key: %s", session_key)
    logger.info("Available session keys: %s", list(request.session.keys()))

    # Get CDA match from session
    if not match_data:
        match_data = request.session.get(session_key)

    if match_data:
        logger.info("Found session data for patient %s", patient_id)
    else:
        logger.warning("No session data found for patient %s", patient_id)

    context = {
        "patient_data": patient_data,
        "has_cda_match": match_data is not None,
    }

    if match_data:
        # Build patient summary directly from match data

        # Check if patient identifiers are missing from session data (backwards compatibility)
        patient_data_dict = match_data["patient_data"]
        if not patient_data_dict.get(
            "primary_patient_id"
        ) and not patient_data_dict.get("secondary_patient_id"):
            logger.info(
                "Patient identifiers missing from session data, re-extracting..."
            )
            try:
                # Re-extract patient identifiers from CDA content
                import xml.etree.ElementTree as ET

                root = ET.fromstring(match_data["cda_content"])
                namespaces = {
                    "hl7": "urn:hl7-org:v3",
                    "ext": "urn:hl7-EE-DL-Ext:v1",
                }

                # Find patient role
                patient_role = root.find(".//hl7:patientRole", namespaces)
                if patient_role is not None:
                    # Extract patient IDs
                    id_elements = patient_role.findall("hl7:id", namespaces)
                    primary_patient_id = ""
                    secondary_patient_id = ""
                    patient_identifiers = []

                    for idx, id_elem in enumerate(id_elements):
                        extension = id_elem.get("extension", "")
                        root_attr = id_elem.get("root", "")
                        assigning_authority = id_elem.get("assigningAuthorityName", "")
                        displayable = id_elem.get("displayable", "")

                        if extension:
                            identifier_info = {
                                "extension": extension,
                                "root": root_attr,
                                "assigningAuthorityName": assigning_authority,
                                "displayable": displayable,
                                "type": "primary" if idx == 0 else "secondary",
                            }
                            patient_identifiers.append(identifier_info)

                            if idx == 0:
                                primary_patient_id = extension
                            elif idx == 1:
                                secondary_patient_id = extension

                    # Update the patient data with extracted identifiers
                    patient_data_dict["primary_patient_id"] = primary_patient_id
                    patient_data_dict["secondary_patient_id"] = secondary_patient_id
                    patient_data_dict["patient_identifiers"] = patient_identifiers

                    # Update the session data
                    match_data["patient_data"] = patient_data_dict
                    request.session[session_key] = match_data

                    logger.info(
                        f"Re-extracted identifiers: primary={primary_patient_id}, secondary={secondary_patient_id}"
                    )
            except Exception as e:
                logger.error(f"Error re-extracting patient identifiers: {e}")

        # Build patient summary directly from match data instead of using service
        patient_summary = {
            "patient_name": match_data["patient_data"].get("name", "Unknown"),
            "birth_date": match_data["patient_data"].get("birth_date", "Unknown"),
            "gender": match_data["patient_data"].get("gender", "Unknown"),
            "primary_patient_id": match_data["patient_data"].get(
                "primary_patient_id", ""
            ),
            "secondary_patient_id": match_data["patient_data"].get(
                "secondary_patient_id", ""
            ),
            "patient_identifiers": match_data["patient_data"].get(
                "patient_identifiers", []
            ),
            "address": match_data["patient_data"].get("address", {}),
            "contact_info": match_data["patient_data"].get("contact_info", {}),
            "cda_type": match_data.get("preferred_cda_type", "L3"),
            "file_path": match_data["file_path"],
            "confidence_score": match_data["confidence_score"],
        }

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
    else:
        # Session data is missing - provide fallback with clear message
        logger.warning(
            "Session data lost for patient %s, showing basic patient info only",
            patient_id,
        )

        # Add a helpful message to the user
        messages.warning(
            request,
            "Patient search data has expired. Please search again to view CDA documents and detailed information.",
        )

        # Provide basic context without CDA match data
        context.update(
            {
                "session_expired": True,
                "show_search_again_message": True,
                "session_error": "Patient search data has expired. Please search again to view CDA documents and detailed information.",
            }
        )

        return render(
            request, "patient_data/patient_details.html", context, using="jinja2"
        )


def patient_cda_view(request, patient_id):
    """View for displaying CDA document in L3 browser format with enhanced translation"""

    logger.info(f"🔥 PATIENT_CDA_VIEW CALLED for patient_id: {patient_id}")
    logger.info(f"🔥 Request method: {request.method}")
    logger.info(f"🔥 Request path: {request.path}")
    logger.info(f"🔥 User: {request.user}")
    logger.info(f"🔥 User authenticated: {request.user.is_authenticated}")

    try:
        # Debug: Check what's in the session
        session_key = f"patient_match_{patient_id}"
        match_data = request.session.get(session_key)

        logger.info(f"DEBUG: Looking for session key: {session_key}")
        logger.info(f"DEBUG: Match data found: {match_data is not None}")
        logger.info(f"DEBUG: All session keys: {list(request.session.keys())}")

        # Check if this is an NCP query result (session data exists but no DB record)
        if match_data and not PatientData.objects.filter(id=patient_id).exists():
            # This is an NCP query result - create temp patient from session data
            patient_info = match_data["patient_data"]

            # Create a temporary patient object (not saved to DB)
            patient_data = PatientData(
                id=patient_id,
                given_name=patient_info.get("given_name", "Unknown"),
                family_name=patient_info.get("family_name", "Patient"),
                birth_date=patient_info.get("birth_date") or None,
                gender=patient_info.get("gender", ""),
            )

            logger.info(
                f"Created temporary patient object for CDA display: {patient_id}"
            )
        else:
            # Standard database lookup
            try:
                patient_data = PatientData.objects.get(id=patient_id)
                logger.info(
                    f"Found database patient: {patient_data.given_name} {patient_data.family_name}"
                )
            except PatientData.DoesNotExist:
                logger.warning(f"Patient {patient_id} not found in database")
                messages.error(request, "Patient data not found.")
                return redirect("patient_data:patient_data_form")

            # Get CDA match from session for database patients
            if not match_data:
                match_data = request.session.get(session_key)
                logger.info(
                    f"Session data for database patient: {match_data is not None}"
                )

                # If no session data exists for database patient, create minimal session data
                # This allows viewing of database patients with basic info
                if not match_data:
                    logger.info(
                        f"Creating minimal session data for database patient {patient_id}"
                    )
                    # Create minimal match data for database patients without session data
                    match_data = {
                        "file_path": f"database_patient_{patient_id}.xml",
                        "country_code": "TEST",
                        "confidence_score": 1.0,
                        "patient_data": {
                            "given_name": patient_data.given_name,
                            "family_name": patient_data.family_name,
                            "birth_date": (
                                str(patient_data.birth_date)
                                if patient_data.birth_date
                                else ""
                            ),
                            "gender": patient_data.gender,
                        },
                        "cda_content": None,  # No CDA content for database-only patients
                        "l1_cda_content": None,
                        "l3_cda_content": None,
                        "l1_cda_path": None,
                        "l3_cda_path": None,
                        "preferred_cda_type": "L3",
                        "has_l1": False,
                        "has_l3": False,
                    }
                    # Store in session for this request
                    request.session[session_key] = match_data

        if not match_data:
            # Debug: Try to find any patient_match session data
            logger.info("DEBUG: No direct match found, searching all session keys...")
            for key, value in request.session.items():
                if key.startswith("patient_match_"):
                    logger.info(f"DEBUG: Found session key: {key}")
                    if isinstance(value, dict) and "patient_data" in value:
                        patient_data_info = value["patient_data"]
                        logger.info(
                            f"DEBUG: Patient data in session: {patient_data_info}"
                        )
                        # Try to match by patient info instead of exact ID
                        # This is a fallback for when URLs don't match session keys exactly
                        match_data = value
                        logger.info(f"DEBUG: Using fallback match data from key: {key}")
                        break

        if not match_data:
            # Final fallback: create empty session data for any valid patient
            # This allows the CDA view to display even without search session data
            logger.info(f"Creating fallback session data for patient {patient_id}")
            match_data = {
                "file_path": f"fallback_patient_{patient_id}.xml",
                "country_code": "UNKNOWN",
                "confidence_score": 0.5,
                "patient_data": {
                    "given_name": (
                        patient_data.given_name
                        if "patient_data" in locals()
                        else "Unknown"
                    ),
                    "family_name": (
                        patient_data.family_name
                        if "patient_data" in locals()
                        else "Patient"
                    ),
                    "birth_date": (
                        str(patient_data.birth_date)
                        if "patient_data" in locals() and patient_data.birth_date
                        else ""
                    ),
                    "gender": patient_data.gender if "patient_data" in locals() else "",
                },
                "cda_content": "<!-- No CDA content available -->",
                "l1_cda_content": None,
                "l3_cda_content": None,
                "l1_cda_path": None,
                "l3_cda_path": None,
                "preferred_cda_type": "L3",
                "has_l1": False,
                "has_l3": False,
            }
            # Store in session
            request.session[session_key] = match_data

            # Show warning message but continue to display page
            messages.warning(
                request,
                f"No CDA document data available for patient {patient_id}. "
                "Displaying basic patient information only.",
            )

        # Initialize Enhanced CDA Processor with JSON Field Mapping enhancement (hybrid approach)
        from .services.enhanced_cda_processor import EnhancedCDAProcessor
        from .services.enhanced_cda_field_mapper import EnhancedCDAFieldMapper
        from .services.patient_search_service import PatientMatch
        from .translation_utils import (
            get_template_translations,
            detect_document_language,
        )

        # Determine source language from country code with enhanced mapping
        source_language = "fr"  # Default to French
        country_code = match_data.get("country_code", "").upper()

        # Enhanced country-to-language mapping for all EU NCP countries
        country_language_map = {
            # Western Europe
            "BE": "nl",  # Belgium (Dutch/Flemish primary, French secondary)
            "DE": "de",  # Germany
            "FR": "fr",  # France
            "IE": "en",  # Ireland (English)
            "LU": "fr",  # Luxembourg (French primary, German/Luxembourgish secondary)
            "NL": "nl",  # Netherlands
            "AT": "de",  # Austria (German)
            # Southern Europe
            "ES": "es",  # Spain
            "IT": "it",  # Italy
            "PT": "pt",  # Portugal
            "GR": "el",  # Greece (Greek)
            "CY": "el",  # Cyprus (Greek primary, Turkish secondary)
            "MT": "en",  # Malta (English and Maltese)
            # Central/Eastern Europe
            "PL": "pl",  # Poland
            "CZ": "cs",  # Czech Republic (Czech)
            "SK": "sk",  # Slovakia (Slovak)
            "HU": "hu",  # Hungary (Hungarian)
            "SI": "sl",  # Slovenia (Slovenian)
            "HR": "hr",  # Croatia (Croatian)
            "RO": "ro",  # Romania (Romanian)
            "BG": "bg",  # Bulgaria (Bulgarian)
            # Baltic States
            "LT": "lt",  # Lithuania (Lithuanian)
            "LV": "lv",  # Latvia (Latvian)
            "EE": "et",  # Estonia (Estonian)
            # Nordic Countries
            "DK": "da",  # Denmark (Danish)
            "FI": "fi",  # Finland (Finnish)
            "SE": "sv",  # Sweden (Swedish)
            # Special codes
            "EU": "en",  # European Union documents (English)
            "CH": "de",  # Switzerland (German primary, but multilingual)
        }

        if country_code in country_language_map:
            source_language = country_language_map[country_code]

        # Create TWO processors for dual language support
        # 1. Original language processor - preserves source language content
        original_processor = EnhancedCDAProcessor(target_language=source_language)
        # 2. Translation processor - translates to English
        translation_processor = EnhancedCDAProcessor(target_language="en")

        # Shared field mapper
        field_mapper = EnhancedCDAFieldMapper()

        # Reconstruct PatientMatch object from session data for translation service
        # This provides the translation service with the proper search result context
        patient_info = match_data.get("patient_data", {})
        search_result = PatientMatch(
            patient_id=patient_id,
            given_name=patient_info.get("given_name", patient_data.given_name),
            family_name=patient_info.get("family_name", patient_data.family_name),
            birth_date=patient_info.get(
                "birth_date",
                str(patient_data.birth_date) if patient_data.birth_date else "",
            ),
            gender=patient_info.get("gender", patient_data.gender),
            country_code=country_code,
            confidence_score=match_data.get("confidence_score", 0.95),
            file_path=match_data.get("file_path"),
            l1_cda_content=match_data.get("l1_cda_content"),
            l3_cda_content=match_data.get("l3_cda_content"),
            l1_cda_path=match_data.get("l1_cda_path"),
            l3_cda_path=match_data.get("l3_cda_path"),
            cda_content=match_data.get("cda_content"),
            patient_data=patient_info,
            preferred_cda_type="L3",  # For clinical sections, prefer L3
        )

        # Process CDA content for clinical sections using the search result
        translation_result = {"sections": []}
        sections_count = 0
        medical_terms_count = 0
        coded_sections_count = 0
        coded_sections_percentage = 0
        uses_coded_sections = False
        translation_quality = "Basic"

        # Get the appropriate CDA content for processing
        cda_content, cda_type = search_result.get_rendering_cda()

        # Detect source language from CDA content if available
        detected_source_language = source_language  # Default from country code
        if cda_content and cda_content.strip():
            detected_source_language = detect_document_language(cda_content)
            logger.info(
                f"Detected source language: {detected_source_language} (country: {country_code})"
            )

        # Special handling for English documents - no dual language needed
        if detected_source_language == "en":
            logger.info(
                f"Document is already in English (detected: {detected_source_language}), using single-language processing"
            )

            # For English documents, just process once without dual language
            english_processor = EnhancedCDAProcessor(target_language="en")

            enhanced_processing_result = english_processor.process_clinical_sections(
                cda_content=cda_content,
                source_language="en",
            )

            # Mark as single language (no original/translated split)
            if enhanced_processing_result.get("success"):
                enhanced_processing_result["dual_language_active"] = False
                enhanced_processing_result["source_language"] = "en"
                enhanced_processing_result["is_single_language"] = True

                logger.info(
                    f"✅ Single-language English processing: {enhanced_processing_result.get('sections_count', 0)} sections"
                )
        else:
            logger.info(
                f"Document requires translation from {detected_source_language} to English"
            )

        if (
            cda_content
            and cda_content.strip()
            and "<!-- No CDA content available -->" not in cda_content
        ):
            try:
                logger.info(
                    f"Processing {cda_type} CDA content with Enhanced CDA Processor (length: {len(cda_content)}, patient: {patient_id})"
                )

                # Check if document needs dual language processing
                if detected_source_language != "en":
                    logger.info(
                        f"Processing DUAL LANGUAGE content: {detected_source_language} → en"
                    )

                    # Create TWO processors for dual language support
                    # 1. Original language processor - preserves source language content
                    original_processor = EnhancedCDAProcessor(
                        target_language=detected_source_language
                    )
                    # 2. Translation processor - translates to English
                    translation_processor = EnhancedCDAProcessor(target_language="en")

                    # Process with DUAL LANGUAGE support
                    # 1. Process for original language (source language preservation)
                    logger.info(
                        f"Processing original content in {detected_source_language}"
                    )
                    original_processing_result = (
                        original_processor.process_clinical_sections(
                            cda_content=cda_content,
                            source_language=detected_source_language,
                        )
                    )

                    # 2. Process for English translation
                    logger.info(f"Processing translated content to English")
                    translation_processing_result = (
                        translation_processor.process_clinical_sections(
                            cda_content=cda_content,
                            source_language=detected_source_language,
                        )
                    )

                    # Combine both results into dual language sections
                    enhanced_processing_result = _create_dual_language_sections(
                        original_processing_result,
                        translation_processing_result,
                        detected_source_language,
                    )

                else:
                    logger.info(
                        f"Processing SINGLE LANGUAGE content: document is already in English"
                    )

                    # For English documents, just process once without dual language
                    english_processor = EnhancedCDAProcessor(target_language="en")

                    enhanced_processing_result = (
                        english_processor.process_clinical_sections(
                            cda_content=cda_content,
                            source_language="en",
                        )
                    )

                    # Mark as single language (no original/translated split)
                    if enhanced_processing_result.get("success"):
                        enhanced_processing_result["dual_language_active"] = False
                        enhanced_processing_result["source_language"] = "en"
                        enhanced_processing_result["is_single_language"] = True

                # Enhance result with JSON field mapping data
                if enhanced_processing_result.get("success"):
                    try:
                        import xml.etree.ElementTree as ET

                        root = ET.fromstring(cda_content)
                        namespaces = {"hl7": "urn:hl7-org:v3"}

                        # Add patient demographic mapping
                        patient_data_mapped = field_mapper.map_patient_data(
                            root, namespaces
                        )
                        enhanced_processing_result["patient_data"] = patient_data_mapped
                        enhanced_processing_result["field_mapping_active"] = True

                        # Add section field mapping for available sections
                        sections = root.findall(".//hl7:section", namespaces)
                        mapped_sections = {}

                        for section in sections:
                            code_elem = section.find("hl7:code", namespaces)
                            if code_elem is not None:
                                section_code = code_elem.get("code")
                                if field_mapper.get_section_mapping(section_code):
                                    try:
                                        section_data = (
                                            field_mapper.map_clinical_section(
                                                section, section_code, root, namespaces
                                            )
                                        )
                                        mapped_sections[section_code] = section_data
                                    except Exception as mapping_error:
                                        logger.warning(
                                            f"Section mapping failed for {section_code}: {mapping_error}"
                                        )

                        enhanced_processing_result["mapped_sections"] = mapped_sections

                        logger.info(
                            f"Enhanced with JSON field mapping: {len(patient_data_mapped)} patient fields, {len(mapped_sections)} mapped sections"
                        )

                    except Exception as enhancement_error:
                        logger.warning(
                            f"JSON field mapping enhancement failed: {enhancement_error}"
                        )
                        # Continue with original result if enhancement fails

                if enhanced_processing_result.get("success"):
                    # Enhanced CDA Processor with JSON Field Mapping results (hybrid approach)
                    translation_result = enhanced_processing_result

                    # Use original sections structure but enhance with field mapping data
                    clinical_sections = enhanced_processing_result.get("sections", [])
                    mapped_sections = enhanced_processing_result.get(
                        "mapped_sections", {}
                    )
                    patient_data_mapped = enhanced_processing_result.get(
                        "patient_data", {}
                    )

                    # Calculate metrics from original structure
                    sections_count = enhanced_processing_result.get(
                        "sections_count", len(clinical_sections)
                    )
                    coded_sections_count = enhanced_processing_result.get(
                        "coded_sections_count", 0
                    )
                    medical_terms_count = enhanced_processing_result.get(
                        "medical_terms_count", 0
                    )
                    coded_sections_percentage = enhanced_processing_result.get(
                        "coded_sections_percentage", 0
                    )
                    uses_coded_sections = enhanced_processing_result.get(
                        "uses_coded_sections", False
                    )

                    # Enhance translation quality if JSON mapping is active
                    translation_quality = enhanced_processing_result.get(
                        "translation_quality", "Basic"
                    )
                    if enhanced_processing_result.get("field_mapping_active"):
                        translation_quality = (
                            "High"  # JSON mapping provides high quality
                        )

                    # Update translation_result with enhanced data
                    translation_result["field_mapping_active"] = (
                        enhanced_processing_result.get("field_mapping_active", False)
                    )
                    translation_result["translation_quality"] = translation_quality

                    logger.info(
                        f"✅ Enhanced CDA Processor + JSON Field Mapping (hybrid): {sections_count} sections, "
                        f"{coded_sections_count} coded, {medical_terms_count} medical terms, "
                        f"quality: {translation_quality}, JSON mapping: {'Active' if enhanced_processing_result.get('field_mapping_active') else 'Inactive'}, "
                        f"patient fields: {len(patient_data_mapped)}, mapped sections: {len(mapped_sections)}"
                    )

                else:
                    logger.warning(
                        f"Enhanced CDA processing failed: {enhanced_processing_result.get('error', 'Unknown error')}"
                    )
                    # Fallback to empty sections if processing fails
                    translation_result = {"sections": []}
                    sections_count = 0
                    coded_sections_count = 0
                    medical_terms_count = 0

            except Exception as e:
                logger.error(
                    f"Error processing CDA content with Enhanced CDA Processor: {e}"
                )
                import traceback

                logger.error(traceback.format_exc())
                # Fallback to empty sections on error
                translation_result = {"sections": []}
                sections_count = 0
                coded_sections_count = 0
                medical_terms_count = 0
        else:
            logger.warning(
                f"No CDA content available for patient {patient_id} - search result may be incomplete"
            )

        # Build complete context for Enhanced CDA Display
        context = {
            "patient_identity": {
                "patient_id": patient_id,
                "given_name": patient_data.given_name,
                "family_name": patient_data.family_name,
                "birth_date": patient_data.birth_date,
                "gender": patient_data.gender,
                "patient_identifiers": [],
                "primary_patient_id": patient_id,
                "secondary_patient_id": None,
            },
            "source_country": match_data.get("country_code", "Unknown"),
            "source_language": source_language,
            "cda_type": (
                cda_type
                if "cda_type" in locals()
                else ("L3" if match_data.get("l3_cda_content") else "L1")
            ),
            "confidence": int(match_data.get("confidence_score", 0.95) * 100),
            "file_name": match_data.get("file_path", "unknown.xml"),
            "translation_quality": translation_quality,
            "sections_count": sections_count,
            "medical_terms_count": medical_terms_count,
            "coded_sections_count": coded_sections_count,
            "coded_sections_percentage": coded_sections_percentage,
            "uses_coded_sections": uses_coded_sections,
            "translation_result": translation_result,
            "safety_alerts": [],
            "allergy_alerts": [],
            "has_safety_alerts": False,
            "administrative_data": {
                "document_creation_date": None,
                "document_last_update_date": None,
                "document_version_number": None,
                "patient_contact_info": {"addresses": [], "telecoms": []},
                "author_hcp": {"family_name": None, "organization": {"name": None}},
                "legal_authenticator": {
                    "family_name": None,
                    "organization": {"name": None},
                },
                "custodian_organization": {"name": None},
                "preferred_hcp": {"name": None},
                "guardian": {"family_name": None},
                "other_contacts": [],
            },
            "has_administrative_data": False,
        }

        # Override with Enhanced CDA Processor data if available
        if enhanced_processing_result and enhanced_processing_result.get("success"):
            # Extract enhanced patient identity if available
            enhanced_patient_identity = enhanced_processing_result.get(
                "patient_identity", {}
            )
            enhanced_admin_data = enhanced_processing_result.get(
                "administrative_data", {}
            )

            # Update patient identity with enhanced data while preserving URL patient_id
            if enhanced_patient_identity:
                original_patient_id = context["patient_identity"]["patient_id"]
                context["patient_identity"].update(enhanced_patient_identity)
                context["patient_identity"]["patient_id"] = original_patient_id

            # Update administrative data with enhanced data
            if enhanced_admin_data:
                context["administrative_data"] = enhanced_admin_data
                context["has_administrative_data"] = enhanced_processing_result.get(
                    "has_administrative_data", False
                )

        # Add single language flag to context if available
        if enhanced_processing_result and enhanced_processing_result.get("success"):
            context["is_single_language"] = enhanced_processing_result.get(
                "is_single_language", False
            )
        else:
            context["is_single_language"] = False

        # Add template translations for dynamic UI text
        template_translations = get_template_translations(
            source_language=detected_source_language, target_language="en"
        )
        context["template_translations"] = template_translations
        context["detected_source_language"] = detected_source_language

        logger.info(
            f"Added template translations for {detected_source_language} → en with {len(template_translations)} strings"
        )

        # REFACTOR: Process sections for template display (move complex logic from template to Python)
        if translation_result and translation_result.get('sections'):
            processed_sections = prepare_enhanced_section_data(
                translation_result.get('sections', [])
            )
            context['processed_sections'] = processed_sections
            logger.info(f"Processed {len(processed_sections)} sections for simplified template display")
        else:
            context['processed_sections'] = []

        return render(request, "patient_data/patient_cda.html", context, using="jinja2")

    except Exception as e:
        logger.error(
            f"CRITICAL ERROR in patient_cda_view for patient {patient_id}: {e}"
        )
        import traceback

        full_traceback = traceback.format_exc()
        logger.error(f"Full traceback:\n{full_traceback}")

        # Try to provide a more helpful error page instead of immediate redirect
        try:
            context = {
                "patient_identity": {
                    "patient_id": patient_id,
                    "given_name": "Error",
                    "family_name": "Loading Patient",
                    "birth_date": "Unknown",
                    "gender": "Unknown",
                    "patient_identifiers": [],
                    "primary_patient_id": patient_id,
                },
                "source_country": "ERROR",
                "source_language": "en",
                "cda_type": "ERROR",
                "confidence": 0,
                "file_name": "error.xml",
                "translation_quality": "Failed",
                "sections_count": 0,
                "medical_terms_count": 0,
                "coded_sections_count": 0,
                "coded_sections_percentage": 0,
                "uses_coded_sections": False,
                "translation_result": {"sections": []},
                "safety_alerts": [],
                "allergy_alerts": [],
                "has_safety_alerts": False,
                "administrative_data": {},
                "has_administrative_data": False,
                "error_message": str(e),
                "error_traceback": full_traceback,
                "template_translations": get_template_translations(),  # Default English translations for error page
                "detected_source_language": "en",
            }

            messages.error(request, f"Technical error loading CDA document: {str(e)}")

            return render(
                request, "patient_data/patient_cda.html", context, using="jinja2"
            )

        except Exception as render_error:
            logger.error(f"Even error rendering failed: {render_error}")
            messages.error(request, f"Critical error loading CDA document: {str(e)}")
            return redirect("patient_data:patient_details", patient_id=patient_id)


@login_required
@require_http_methods(["POST"])
def cda_translation_toggle(request, patient_id):
    """AJAX endpoint for toggling CDA translation sections"""
    try:
        data = json.loads(request.body)
        section_id = data.get("section_id")
        show_translation = data.get("show_translation", True)
        target_language = data.get("target_language", "en")

        # Get patient data and CDA content
        patient_data = PatientData.objects.get(id=patient_id)
        match_data = request.session.get(f"patient_match_{patient_id}")

        if not match_data:
            return JsonResponse({"error": "No CDA document found"}, status=404)

        # Initialize translation manager
        from .services.cda_translation_manager import CDATranslationManager

        translation_manager = CDATranslationManager(target_language=target_language)

        # Process the specific section if section_id provided
        if section_id:
            # Get section-specific translation
            cda_content = match_data.get("l3_cda_content") or match_data.get(
                "cda_content", ""
            )
            translation_data = translation_manager.process_cda_for_viewer(cda_content)

            # Find the specific section
            section_data = None
            for section in translation_data.get("clinical_sections", []):
                if section["id"] == section_id:
                    section_data = section
                    break

            if section_data:
                return JsonResponse(
                    {
                        "success": True,
                        "section": section_data,
                        "show_translation": show_translation,
                    }
                )
            else:
                return JsonResponse({"error": "Section not found"}, status=404)

        # Return general translation status
        return JsonResponse(
            {
                "success": True,
                "translation_status": translation_manager.get_translation_status(),
            }
        )

    except PatientData.DoesNotExist:
        return JsonResponse({"error": "Patient not found"}, status=404)
    except Exception as e:
        logger.error(f"Error in CDA translation toggle: {e}")
        return JsonResponse({"error": str(e)}, status=500)


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


def download_patient_summary_pdf(request, patient_id):
    """Download Patient Summary as PDF generated from structured patient summary data"""

    try:
        patient_data = PatientData.objects.get(id=patient_id)
        match_data = request.session.get(f"patient_match_{patient_id}")

        if not match_data:
            messages.error(request, "No CDA document found for this patient.")
            return redirect("patient_data:patient_details", patient_id=patient_id)

        # Get patient summary using the same logic as the details view
        search_service = EUPatientSearchService()

        # Reconstruct match object for summary
        # Define result class directly to avoid import conflicts
        from dataclasses import dataclass
        from typing import Dict

        @dataclass
        class SimplePatientResult:
            """Simple patient result for views"""

            file_path: str
            country_code: str
            confidence_score: float
            patient_data: Dict
            cda_content: str

        # Extract required fields from patient_data or use defaults
        patient_info = match_data.get("patient_data", {})
        patient_name_parts = patient_info.get("name", "Unknown Unknown").split(" ", 1)
        given_name = patient_name_parts[0] if len(patient_name_parts) > 0 else "Unknown"
        family_name = (
            patient_name_parts[1] if len(patient_name_parts) > 1 else "Unknown"
        )

        match = SimplePatientResult(
            file_path=match_data["file_path"],
            country_code=match_data["country_code"],
            confidence_score=match_data["confidence_score"],
            patient_data=match_data["patient_data"],
            cda_content=match_data["cda_content"],
        )

        patient_summary = search_service.get_patient_summary(match)

        if not patient_summary:
            messages.error(request, "No patient summary content available.")
            return redirect("patient_data:patient_details", patient_id=patient_id)

        try:
            # Get the CDA content from patient summary
            cda_content = patient_summary.get("cda_content", "")

            # If we have L3 content (HTML), prefer that
            l3_cda_content = match_data.get("l3_cda_content")
            if l3_cda_content:
                cda_content = l3_cda_content

            # Clean up and structure the content for PDF
            sections_html = ""
            if cda_content:
                # Clean up the CDA content for better PDF display
                import re
                from html import unescape

                # Remove XML declaration and root elements if present
                clean_content = re.sub(r"<\?xml[^>]*\?>", "", cda_content)
                clean_content = re.sub(r"<ClinicalDocument[^>]*>", "", clean_content)
                clean_content = re.sub(r"</ClinicalDocument>", "", clean_content)
                clean_content = re.sub(r"<component[^>]*>", "", clean_content)
                clean_content = re.sub(r"</component>", "", clean_content)
                clean_content = re.sub(r"<structuredBody[^>]*>", "", clean_content)
                clean_content = re.sub(r"</structuredBody>", "", clean_content)

                # Unescape HTML entities
                clean_content = unescape(clean_content)

                # If it's mostly tables and structured content, use it as-is
                sections_html = f"""
                <div class="section">
                    <h2>Patient Summary Content</h2>
                    <div class="content">
                        {clean_content}
                    </div>
                </div>
                """
            else:
                sections_html = """
                <div class="section">
                    <p>No detailed patient summary content available.</p>
                </div>
                """  # Prepare HTML content with proper structure and inline CSS
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Patient Summary - {patient_data.given_name} {patient_data.family_name}</title>
                <style>
                    @page {{
                        size: A4;
                        margin: 2cm;
                    }}
                    
                    body {{
                        font-family: Arial, sans-serif;
                        font-size: 10pt;
                        line-height: 1.4;
                        color: #333;
                        margin: 0;
                        padding: 0;
                    }}
                    
                    h1, h2, h3, h4, h5, h6 {{
                        color: #2c3e50;
                        margin-top: 1.5em;
                        margin-bottom: 0.5em;
                    }}
                    
                    h1 {{ font-size: 16pt; }}
                    h2 {{ font-size: 14pt; }}
                    h3 {{ font-size: 12pt; }}
                    
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 1em 0;
                    }}
                    
                    th, td {{
                        border: 1px solid #ddd;
                        padding: 8px;
                        text-align: left;
                        vertical-align: top;
                    }}
                    
                    th {{
                        background-color: #f8f9fa;
                        font-weight: bold;
                        color: #2c3e50;
                    }}
                    
                    .patient-header {{
                        background-color: #e8f4f8;
                        padding: 15px;
                        border-radius: 5px;
                        margin-bottom: 20px;
                    }}
                    
                    .section {{
                        margin-bottom: 20px;
                    }}

                    ul {{
                        padding-left: 20px;
                    }}

                    li {{
                        margin-bottom: 5px;
                    }}
                </style>
            </head>
            <body>
                <div class="patient-header">
                    <h1>Patient Summary</h1>
                    <p><strong>Patient:</strong> {patient_summary.get('patient_name', 'Unknown')}</p>
                    <p><strong>Date of Birth:</strong> {patient_summary.get('birth_date', 'Not specified')}</p>
                    <p><strong>Gender:</strong> {patient_summary.get('gender', 'Not specified')}</p>
                    <p><strong>Primary Patient ID:</strong> {patient_summary.get('primary_patient_id', 'Not specified')}</p>
                    {f'<p><strong>Secondary Patient ID:</strong> {patient_summary.get("secondary_patient_id")}</p>' if patient_summary.get('secondary_patient_id') else ''}
                    <p><strong>Generated:</strong> {timezone.now().strftime('%Y-%m-%d %H:%M')}</p>
                </div>
                
                <div class="content">
                    {sections_html}
                </div>
            </body>
            </html>
            """

            # Generate PDF using xhtml2pdf
            result = BytesIO()
            pdf = pisa.pisaDocument(BytesIO(html_content.encode("UTF-8")), result)

            if not pdf.err:
                pdf_bytes = result.getvalue()
                result.close()

                # Create filename
                filename = f"{patient_data.given_name}_{patient_data.family_name}_Patient_Summary.pdf"

                # Return PDF response
                response = HttpResponse(pdf_bytes, content_type="application/pdf")
                response["Content-Disposition"] = f'attachment; filename="{filename}"'

                logger.info(f"Generated patient summary PDF for patient {patient_id}")
                return response
            else:
                logger.error(f"Error generating PDF: {pdf.err}")
                messages.error(request, "Error generating PDF document.")
                return redirect("patient_data:patient_details", patient_id=patient_id)

        except Exception as e:
            logger.error(f"Error generating patient summary PDF: {e}")
            messages.error(request, "Error generating PDF document.")
            return redirect("patient_data:patient_details", patient_id=patient_id)

    except PatientData.DoesNotExist:
        messages.error(request, "Patient data not found.")
        return redirect("patient_data:patient_data_form")


def patient_orcd_view(request, patient_id):
    """View for displaying ORCD (Original Clinical Document) PDF preview"""

    try:
        # Check if this is an NCP query result (session data exists but no DB record)
        session_key = f"patient_match_{patient_id}"
        match_data = request.session.get(session_key)

        if match_data and not PatientData.objects.filter(id=patient_id).exists():
            # This is an NCP query result - create temp patient from session data
            patient_info = match_data["patient_data"]

            # Create a temporary patient object (not saved to DB)
            patient_data = PatientData(
                id=patient_id,
                given_name=patient_info.get("given_name", "Unknown"),
                family_name=patient_info.get("family_name", "Patient"),
                birth_date=patient_info.get("birth_date") or None,
                gender=patient_info.get("gender", ""),
            )

            logger.info(
                f"Created temporary patient object for ORCD display: {patient_id}"
            )
        else:
            # Standard database lookup
            try:
                patient_data = PatientData.objects.get(id=patient_id)
            except PatientData.DoesNotExist:
                messages.error(request, "Patient data not found.")
                return redirect("patient_data:patient_data_form")

            # Get CDA match from session for database patients
            if not match_data:
                match_data = request.session.get(session_key)

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
                logger.info(
                    f"Attempting ORCD PDF extraction from {cda_type_used} CDA (content length: {len(orcd_cda_content)})"
                )
                pdf_attachments = pdf_service.extract_pdfs_from_xml(orcd_cda_content)
                orcd_available = len(pdf_attachments) > 0
                logger.info(
                    f"ORCD extraction from {cda_type_used} CDA: {len(pdf_attachments)} PDFs found"
                )

                # Log more details about the extracted PDFs
                for i, pdf_info in enumerate(pdf_attachments):
                    logger.info(
                        f"PDF {i}: {pdf_info['filename']} ({pdf_info['size']} bytes, media_type: {pdf_info.get('media_type', 'unknown')})"
                    )

            except Exception as e:
                logger.error(f"Error extracting PDFs from {cda_type_used} CDA: {e}")
                import traceback

                logger.error(traceback.format_exc())

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
        # Check if this is an NCP query result (session data exists but no DB record)
        session_key = f"patient_match_{patient_id}"
        match_data = request.session.get(session_key)

        if match_data and not PatientData.objects.filter(id=patient_id).exists():
            # This is an NCP query result - create temp patient from session data
            patient_info = match_data["patient_data"]

            # Create a temporary patient object (not saved to DB)
            patient_data = PatientData(
                id=patient_id,
                given_name=patient_info.get("given_name", "Unknown"),
                family_name=patient_info.get("family_name", "Patient"),
                birth_date=patient_info.get("birth_date") or None,
                gender=patient_info.get("gender", ""),
            )

            logger.info(
                f"Created temporary patient object for ORCD download: {patient_id}"
            )
        else:
            # Standard database lookup
            try:
                patient_data = PatientData.objects.get(id=patient_id)
            except PatientData.DoesNotExist:
                messages.error(request, "Patient data not found.")
                return redirect("patient_data:patient_data_form")

            # Get CDA match from session for database patients
            if not match_data:
                match_data = request.session.get(session_key)

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
            logger.info(
                f"Attempting ORCD PDF download from {cda_type_used} CDA (content length: {len(orcd_cda_content)})"
            )
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
                f"Downloaded ORCD PDF from {cda_type_used} CDA for patient {patient_id} ({len(pdf_data)} bytes)"
            )

            # Return PDF response
            return pdf_service.get_pdf_response(
                pdf_data, filename, disposition="attachment"
            )

        except Exception as e:
            logger.error(f"Error downloading PDF: {e}")
            import traceback

            logger.error(traceback.format_exc())
            messages.error(request, "Error extracting PDF from document.")
            return redirect("patient_data:patient_orcd_view", patient_id=patient_id)

    except PatientData.DoesNotExist:
        messages.error(request, "Patient data not found.")
        return redirect("patient_data:patient_data_form")


def view_orcd_pdf(request, patient_id, attachment_index=0):
    """View ORCD PDF inline for fullscreen preview"""

    try:
        # Check if this is an NCP query result (session data exists but no DB record)
        session_key = f"patient_match_{patient_id}"
        match_data = request.session.get(session_key)

        if match_data and not PatientData.objects.filter(id=patient_id).exists():
            # This is an NCP query result - create temp patient from session data
            patient_info = match_data["patient_data"]

            # Create a temporary patient object (not saved to DB)
            patient_data = PatientData(
                id=patient_id,
                given_name=patient_info.get("given_name", "Unknown"),
                family_name=patient_info.get("family_name", "Patient"),
                birth_date=patient_info.get("birth_date") or None,
                gender=patient_info.get("gender", ""),
            )

            logger.info(
                f"Created temporary patient object for ORCD inline view: {patient_id}"
            )
        else:
            # Standard database lookup
            try:
                patient_data = PatientData.objects.get(id=patient_id)
            except PatientData.DoesNotExist:
                return HttpResponse(
                    "<html><body><h1>Patient not found</h1><p>Please return to the patient data form.</p></body></html>",
                    status=404,
                )

            # Get CDA match from session for database patients
            if not match_data:
                match_data = request.session.get(session_key)

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
            logger.info(
                f"Attempting ORCD PDF inline viewing from {cda_type_used} CDA (content length: {len(orcd_cda_content)})"
            )
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
                f"Viewing ORCD PDF inline from {cda_type_used} CDA for patient {patient_id} ({len(pdf_data)} bytes)"
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
            logger.error(f"Error creating base64 PDF: {e}")
            return HttpResponse(f"Error processing PDF: {str(e)}", status=500)

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


def test_ps_table_rendering(request):
    """Test view for PS Display Guidelines table rendering"""
    print("DEBUG: test_ps_table_rendering function called!")
    from .services.cda_translation_service import CDATranslationService

    # Sample CDA HTML content with medication section
    sample_cda_html = """
    <html>
        <body>
            <div class="section">
                <h3 id="section-10160-0" data-code="10160-0">History of Medication use</h3>
                <div class="section-content">
                    <table>
                        <thead>
                            <tr>
                                <th>Brand Name</th>
                                <th>Active Ingredient</th>
                                <th>Dosage</th>
                                <th>Posology</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>RETROVIR</td>
                                <td>zidovudine</td>
                                <td>10.0mg/ml</td>
                                <td>300 mg every 12 hours</td>
                            </tr>
                            <tr>
                                <td>VIREAD</td>
                                <td>tenofovir disoproxil fumarate</td>
                                <td>245.0mg</td>
                                <td>1 tablet daily</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            <div class="section">
                <h3 id="section-48765-2" data-code="48765-2">Allergies et intolérances</h3>
                <div class="section-content">
                    <table>
                        <thead>
                            <tr>
                                <th>Type d'allergie</th>
                                <th>Agent causant</th>
                                <th>Manifestation</th>
                                <th>Sévérité</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Allergie médicamenteuse</td>
                                <td>Pénicilline</td>
                                <td>Éruption cutanée</td>
                                <td>Modérée</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </body>
    </html>
    """

    # Create translation service and parse the CDA
    service = CDATranslationService(
        target_language="en"
    )  # Default to English for debug view
    cda_data = service.parse_cda_html(sample_cda_html)

    # Create bilingual document with PS Display Guidelines tables
    bilingual_data = service.create_bilingual_document(cda_data)

    # Debug: Check if badges were created
    print("DEBUG TEST: Checking bilingual data for badges...")
    for i, section in enumerate(bilingual_data.get("sections", [])):
        ps_html = section.get("ps_table_html", "")
        if ps_html:
            print(f"DEBUG TEST: Section {i} ps_table_html (first 200 chars):")
            print(f"  Content: {ps_html[:200]}...")
            print(f"  Contains badges: {'code-system-badge' in ps_html}")
            print(f"  HTML escaped: {'&lt;' in ps_html or '&gt;' in ps_html}")

    context = {
        "original_sections": cda_data["sections"],
        "translated_sections": bilingual_data["sections"],
        "source_language": bilingual_data["source_language"],
    }

    return render(request, "patient_data/test_ps_tables.html", context, using="jinja2")


def generate_dynamic_ps_sections(sections):
    """
    Generate dynamic PS Display Guidelines sections with enhanced table rendering

    This function creates structured sections that combine:
    - Original language content
    - Code-based translations
    - PS Guidelines compliant tables
    - Interactive comparison views
    """

    enhanced_sections = []

    for section in sections:
        # Create base enhanced section
        enhanced_section = section.copy()

        # Generate dynamic subsections based on content type
        subsections = []

        # 1. Original Content Subsection
        if section.get("content", {}).get("original"):
            subsections.append(
                {
                    "type": "original_content",
                    "title": f"Original Content ({section.get('source_language', 'fr').upper()})",
                    "icon": "fas fa-flag",
                    "content": section["content"]["original"],
                    "priority": 1,
                }
            )

        # 2. PS Guidelines Table Subsection (Priority!)
        if section.get("ps_table_html"):
            # Determine section type for better labeling
            section_code = section.get("section_code", "")
            section_type_names = {
                "10160-0": "Medication History",
                "48765-2": "Allergies & Adverse Reactions",
                "11450-4": "Problem List",
                "47519-4": "Procedures History",
                "30954-2": "Laboratory Results",
                "10157-6": "Immunization History",
                "18776-5": "Treatment Plan",
            }

            ps_section_name = section_type_names.get(
                section_code, "Clinical Information"
            )

            subsections.append(
                {
                    "type": "ps_guidelines_table",
                    "title": f"PS Guidelines Standardized Table - {ps_section_name}",
                    "icon": "fas fa-table",
                    "content": section["ps_table_html"],
                    "section_code": section_code,
                    "priority": 0,  # Highest priority
                    "compliance_note": "This table follows EU Patient Summary Display Guidelines for interoperability",
                }
            )

        # 3. Code-based Translation Subsection
        if section.get("is_coded_section") and section.get("title", {}).get("coded"):
            subsections.append(
                {
                    "type": "coded_translation",
                    "title": "Code-based Medical Translation",
                    "icon": "fas fa-code",
                    "content": section["content"].get("translated", ""),
                    "coded_title": section["title"]["coded"],
                    "section_code": section.get("section_code", ""),
                    "priority": 2,
                }
            )

        # 4. Free-text Translation Subsection
        elif section.get("content", {}).get("translated"):
            subsections.append(
                {
                    "type": "free_text_translation",
                    "title": "Free-text Translation",
                    "icon": "fas fa-language",
                    "content": section["content"]["translated"],
                    "priority": 3,
                }
            )

        # 5. Original Tables Comparison (if different from PS Guidelines)
        if section.get("original_tables") and section.get("ps_table_html"):
            subsections.append(
                {
                    "type": "original_tables",
                    "title": "Original Document Tables (Comparison)",
                    "icon": "fas fa-table",
                    "content": section["original_tables"],
                    "priority": 4,
                    "note": "These are the original tables as they appeared in the source document",
                }
            )

        # Sort subsections by priority (PS Guidelines tables first)
        subsections.sort(key=lambda x: x.get("priority", 99))

        # Add subsections to enhanced section
        enhanced_section["subsections"] = subsections
        enhanced_section["has_subsections"] = len(subsections) > 0
        enhanced_section["subsection_count"] = len(subsections)

        # Add section-level metadata for better organization
        enhanced_section["section_metadata"] = {
            "has_ps_table": bool(section.get("ps_table_html")),
            "has_coded_translation": section.get("is_coded_section", False),
            "has_original_content": bool(section.get("content", {}).get("original")),
            "clinical_importance": _get_clinical_importance(
                section.get("section_code", "")
            ),
            "display_priority": _get_display_priority(section.get("section_code", "")),
        }

        enhanced_sections.append(enhanced_section)

    # Sort sections by clinical importance (medications, allergies, problems first)
    enhanced_sections.sort(key=lambda x: x["section_metadata"]["display_priority"])

    return enhanced_sections


def _get_clinical_importance(section_code):
    """Determine clinical importance level for section ordering"""
    high_importance_codes = [
        "10160-0",
        "48765-2",
        "11450-4",
    ]  # Medications, Allergies, Problems
    medium_importance_codes = [
        "47519-4",
        "30954-2",
        "10157-6",
    ]  # Procedures, Labs, Immunizations

    if section_code in high_importance_codes:
        return "high"
    elif section_code in medium_importance_codes:
        return "medium"
    else:
        return "low"


def _get_display_priority(section_code):
    """Get numeric display priority (lower = displayed first)"""
    priority_map = {
        "10160-0": 1,  # Medication History (most critical)
        "48765-2": 2,  # Allergies (safety critical)
        "11450-4": 3,  # Problems/Conditions
        "47519-4": 4,  # Procedures
        "30954-2": 5,  # Laboratory Results
        "10157-6": 6,  # Immunizations
        "18776-5": 7,  # Treatment Plan
    }
    return priority_map.get(section_code, 99)  # Unknown sections go last


def enhanced_cda_display(request):
    """
    Enhanced CDA Display endpoint for multi-European language processing
    Handles both GET (render template) and POST (AJAX processing) requests
    """

    from .services.enhanced_cda_processor import EnhancedCDAProcessor
    from .translation_utils import detect_document_language
    import json

    if request.method == "POST":
        try:
            # AJAX request for CDA processing
            cda_content = request.POST.get("cda_content", "")
            source_language = request.POST.get("source_language", "")
            target_language = request.POST.get("target_language", "en")
            country_code = request.POST.get("country_code", "").upper()

            if not cda_content.strip():
                return JsonResponse(
                    {"success": False, "error": "No CDA content provided"}
                )

            # Enhanced multi-European language detection
            detected_source_language = None

            # Method 1: Use provided source_language if valid
            supported_languages = [
                "de",
                "it",
                "es",
                "pt",
                "lv",
                "lt",
                "et",
                "en",
                "fr",
                "nl",
                "el",
                "mt",
                "cs",
                "sk",
                "hu",
                "sl",
                "hr",
                "ro",
                "bg",
                "da",
                "fi",
                "sv",
                "pl",
            ]

            if source_language and source_language in supported_languages:
                detected_source_language = source_language
                logger.info(f"Using provided source language: {source_language}")

            # Method 2: Derive from country code if provided
            elif country_code:
                country_language_map = {
                    # Western Europe
                    "BE": "nl",  # Belgium (Dutch/Flemish primary, French secondary)
                    "DE": "de",  # Germany
                    "FR": "fr",  # France
                    "IE": "en",  # Ireland (English)
                    "LU": "fr",  # Luxembourg (French primary, German/Luxembourgish secondary)
                    "NL": "nl",  # Netherlands
                    "AT": "de",  # Austria (German)
                    # Southern Europe
                    "ES": "es",  # Spain
                    "IT": "it",  # Italy
                    "PT": "pt",  # Portugal
                    "GR": "el",  # Greece (Greek)
                    "CY": "el",  # Cyprus (Greek primary, Turkish secondary)
                    "MT": "en",  # Malta (English and Maltese)
                    # Central/Eastern Europe
                    "PL": "pl",  # Poland
                    "CZ": "cs",  # Czech Republic (Czech)
                    "SK": "sk",  # Slovakia (Slovak)
                    "HU": "hu",  # Hungary (Hungarian)
                    "SI": "sl",  # Slovenia (Slovenian)
                    "HR": "hr",  # Croatia (Croatian)
                    "RO": "ro",  # Romania (Romanian)
                    "BG": "bg",  # Bulgaria (Bulgarian)
                    # Baltic States
                    "LT": "lt",  # Lithuania (Lithuanian)
                    "LV": "lv",  # Latvia (Latvian)
                    "EE": "et",  # Estonia (Estonian)
                    # Nordic Countries
                    "DK": "da",  # Denmark (Danish)
                    "FI": "fi",  # Finland (Finnish)
                    "SE": "sv",  # Sweden (Swedish)
                    # Special codes
                    "EU": "en",  # European Union documents (English)
                    "CH": "de",  # Switzerland (German primary, but multilingual)
                }

                if country_code in country_language_map:
                    detected_source_language = country_language_map[country_code]
                    logger.info(
                        f"Derived source language from country {country_code}: {detected_source_language}"
                    )

            # Method 3: Auto-detect from CDA content
            if not detected_source_language:
                detected_source_language = detect_document_language(cda_content)
                logger.info(
                    f"Auto-detected source language from content: {detected_source_language}"
                )

            # Method 4: Ultimate fallback to French (for backwards compatibility)
            if not detected_source_language:
                detected_source_language = "fr"
                logger.warning(
                    "Could not detect source language, falling back to French"
                )

            # Initialize Enhanced CDA Processor with JSON Field Mapping
            processor = EnhancedCDAProcessor(target_language=target_language)

            # Process CDA content with comprehensive field mapping
            result = processor.process_clinical_sections(
                cda_content=cda_content, source_language=detected_source_language
            )

            # Add language detection info to result
            result["detected_source_language"] = detected_source_language
            result["language_detection_method"] = (
                "provided"
                if source_language
                else (
                    "country_code"
                    if country_code
                    else (
                        "auto_detected"
                        if detected_source_language != "fr"
                        else "fallback"
                    )
                )
            )

            logger.info(
                f"Enhanced CDA processing result: success={result.get('success')}, "
                f"sections={result.get('sections_count', 0)}, "
                f"source_lang={detected_source_language}, target_lang={target_language}"
            )

            return JsonResponse(result)

        except Exception as e:
            logger.error(f"Error in enhanced CDA display AJAX processing: {e}")
            return JsonResponse({"success": False, "error": str(e)})

    else:
        # GET request - render template with multi-language support info
        supported_languages = {
            "de": "German (Deutschland, Österreich, Schweiz)",
            "it": "Italian (Italia, San Marino, Vaticano)",
            "es": "Spanish (España, Andorra)",
            "pt": "Portuguese (Portugal)",
            "lv": "Latvian (Latvija)",
            "lt": "Lithuanian (Lietuva)",
            "et": "Estonian (Eesti)",
            "en": "English (Malta, Ireland)",
            "fr": "French (France, Luxembourg)",
            "nl": "Dutch (Nederland, België)",
            "el": "Greek (Ελλάδα)",
        }

        context = {
            "page_title": "Enhanced CDA Display Tool",
            "description": "Multi-European Language CDA Document Processor with CTS Compliance",
            "supported_languages": supported_languages,
            "default_target_language": "en",
        }

        return render(
            request, "patient_data/enhanced_patient_cda.html", context, using="jinja2"
        )


def _create_dual_language_sections(original_result, translated_result, source_language):
    """
    Create dual language sections by combining original and translated processing results

    Args:
        original_result: Processing result with source language content
        translated_result: Processing result with English translation
        source_language: Source language code (pt, fr, de, etc.)

    Returns:
        Combined result with dual language sections
    """
    if not original_result.get("success") or not translated_result.get("success"):
        logger.warning(
            "One or both processing results failed, falling back to single language"
        )
        return (
            translated_result if translated_result.get("success") else original_result
        )

    # Start with the translated result structure
    dual_result = dict(translated_result)

    original_sections = original_result.get("sections", [])
    translated_sections = translated_result.get("sections", [])

    # Create dual language sections
    dual_sections = []

    for i, translated_section in enumerate(translated_sections):
        # Find corresponding original section
        original_section = None
        if i < len(original_sections):
            original_section = original_sections[i]

        # Create dual language section
        dual_section = dict(translated_section)

        # Preserve original content structure while adding dual language content
        original_content = (
            original_section.get("content", "") if original_section else ""
        )
        translated_content = translated_section.get("content", "")

        # Handle content that might be a dict (with medical_terms) or string
        if isinstance(translated_content, dict):
            # Keep all the metadata from translated content
            dual_section["content"] = dict(translated_content)
            dual_section["content"]["translated"] = translated_content.get(
                "content", str(translated_content)
            )
            dual_section["content"]["original"] = (
                original_content.get("content", str(original_content))
                if isinstance(original_content, dict)
                else str(original_content)
            )
        else:
            # Simple string content
            dual_section["content"] = {
                "translated": str(translated_content),
                "original": str(original_content),
                "medical_terms": 0,  # Default for compatibility
            }

        # Add source language info
        dual_section["source_language"] = source_language
        dual_section["has_dual_language"] = True

        # Handle PS table content for both languages if available
        if translated_section.get("has_ps_table"):
            dual_section["ps_table_html"] = translated_section.get("ps_table_html", "")
            if original_section and original_section.get("has_ps_table"):
                dual_section["ps_table_html_original"] = original_section.get(
                    "ps_table_html", ""
                )
            else:
                dual_section["ps_table_html_original"] = ""

        dual_sections.append(dual_section)

    # Update the result with dual language sections
    dual_result["sections"] = dual_sections
    dual_result["dual_language_active"] = True
    dual_result["source_language"] = source_language

    # Ensure medical_terms_count is preserved for template compatibility
    if "medical_terms_count" not in dual_result:
        dual_result["medical_terms_count"] = translated_result.get(
            "medical_terms_count", 0
        )

    logger.info(
        f"Created {len(dual_sections)} dual language sections ({source_language} | en)"
    )

    return dual_result


@require_http_methods(["POST"])
def upload_cda_document(request):
    """Handle CDA document upload and processing"""
    from django.core.files.storage import default_storage
    from django.core.files.base import ContentFile
    from pathlib import Path
    import uuid
    from .services.enhanced_cda_processor import EnhancedCDAProcessor

    try:
        if "cda_file" not in request.FILES:
            messages.error(request, "No file was uploaded. Please select a CDA file.")
            return redirect("patient_data:patient_search_enhanced")

        uploaded_file = request.FILES["cda_file"]
        auto_process = request.POST.get("auto_process") == "on"

        # Validate file type
        if not uploaded_file.name.lower().endswith((".xml", ".cda")):
            messages.error(
                request, "Invalid file type. Please upload an XML or CDA file."
            )
            return redirect("patient_data:patient_search_enhanced")

        # Generate unique filename
        file_extension = Path(uploaded_file.name).suffix
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"

        # Save file to uploads directory
        uploads_dir = Path(settings.BASE_DIR) / "media" / "uploads" / "cda_documents"
        uploads_dir.mkdir(parents=True, exist_ok=True)

        file_path = uploads_dir / unique_filename

        # Save the uploaded file
        with open(file_path, "wb+") as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        logger.info(f"CDA file uploaded: {uploaded_file.name} -> {unique_filename}")

        if auto_process:
            try:
                # Process the CDA document
                processor = EnhancedCDAProcessor()
                result = processor.process_cda_file(str(file_path))

                if result and "patient_info" in result:
                    patient_info = result["patient_info"]
                    patient_name = f"{patient_info.get('given_name', '')} {patient_info.get('family_name', '')}".strip()
                    patient_id = patient_info.get("patient_id", "Unknown")

                    # Store in session for search results
                    if "uploaded_cda_documents" not in request.session:
                        request.session["uploaded_cda_documents"] = []

                    document_info = {
                        "original_filename": uploaded_file.name,
                        "stored_filename": unique_filename,
                        "file_path": str(file_path),
                        "patient_name": patient_name,
                        "patient_id": patient_id,
                        "upload_date": timezone.now().isoformat(),
                        "processed": True,
                        "processing_result": result,
                    }

                    request.session["uploaded_cda_documents"].append(document_info)
                    request.session.modified = True

                    messages.success(
                        request,
                        f"Document '{uploaded_file.name}' uploaded and processed successfully. "
                        f"Patient: {patient_name} (ID: {patient_id})",
                    )

                    # Redirect to search results showing the uploaded document
                    return redirect("patient_data:uploaded_documents")

                else:
                    messages.warning(
                        request,
                        f"Document '{uploaded_file.name}' was uploaded but could not be processed. "
                        "The file may not contain valid patient data.",
                    )

            except Exception as e:
                logger.error(f"Error processing uploaded CDA document: {str(e)}")
                messages.error(
                    request,
                    f"Document '{uploaded_file.name}' was uploaded but processing failed: {str(e)}",
                )
        else:
            # Just store file info without processing
            if "uploaded_cda_documents" not in request.session:
                request.session["uploaded_cda_documents"] = []

            document_info = {
                "original_filename": uploaded_file.name,
                "stored_filename": unique_filename,
                "file_path": str(file_path),
                "upload_date": timezone.now().isoformat(),
                "processed": False,
            }

            request.session["uploaded_cda_documents"].append(document_info)
            request.session.modified = True

            messages.success(
                request,
                f"Document '{uploaded_file.name}' uploaded successfully. "
                "Use the process button to extract patient information.",
            )

        return redirect("patient_data:patient_search_enhanced")

    except Exception as e:
        logger.error(f"Error uploading CDA document: {str(e)}")
        messages.error(request, f"Upload failed: {str(e)}")
        return redirect("patient_data:patient_search_enhanced")


def uploaded_documents_view(request):
    """Display uploaded CDA documents"""
    uploaded_docs = request.session.get("uploaded_cda_documents", [])

    context = {
        "uploaded_documents": uploaded_docs,
        "total_documents": len(uploaded_docs),
    }

    return render(
        request, "patient_data/uploaded_documents.html", context, using="jinja2"
    )


def process_uploaded_document(request, doc_index):
    """Process a specific uploaded document"""
    try:
        uploaded_docs = request.session.get("uploaded_cda_documents", [])

        if doc_index >= len(uploaded_docs):
            messages.error(request, "Document not found.")
            return redirect("patient_data:uploaded_documents")

        document_info = uploaded_docs[doc_index]

        if document_info.get("processed"):
            messages.info(request, "Document has already been processed.")
            return redirect("patient_data:uploaded_documents")

        from .services.enhanced_cda_processor import EnhancedCDAProcessor

        processor = EnhancedCDAProcessor()
        result = processor.process_cda_file(document_info["file_path"])

        if result and "patient_info" in result:
            patient_info = result["patient_info"]
            patient_name = f"{patient_info.get('given_name', '')} {patient_info.get('family_name', '')}".strip()
            patient_id = patient_info.get("patient_id", "Unknown")

            # Update document info
            document_info.update(
                {
                    "patient_name": patient_name,
                    "patient_id": patient_id,
                    "processed": True,
                    "processing_result": result,
                }
            )

            request.session["uploaded_cda_documents"] = uploaded_docs
            request.session.modified = True

            messages.success(
                request,
                f"Document processed successfully. Patient: {patient_name} (ID: {patient_id})",
            )
        else:
            messages.error(
                request,
                "Failed to process document. The file may not contain valid patient data.",
            )

        return redirect("patient_data:uploaded_documents")

    except Exception as e:
        logger.error(f"Error processing uploaded document: {str(e)}")
        messages.error(request, f"Processing failed: {str(e)}")
        return redirect("patient_data:uploaded_documents")


def view_uploaded_document(request, doc_index):
    """View details of an uploaded CDA document"""
    try:
        uploaded_docs = request.session.get("uploaded_cda_documents", [])

        if doc_index >= len(uploaded_docs):
            messages.error(request, "Document not found.")
            return redirect("patient_data:uploaded_documents")

        document_info = uploaded_docs[doc_index]

        if not document_info.get("processed"):
            messages.error(request, "Document has not been processed yet.")
            return redirect("patient_data:uploaded_documents")

        processing_result = document_info.get("processing_result")
        if not processing_result:
            messages.error(request, "No processing result available for this document.")
            return redirect("patient_data:uploaded_documents")

        # Create dual language sections if needed (but not for English documents)
        if processing_result.get("sections"):
            # Check if this is already marked as single language (English documents)
            if processing_result.get("is_single_language"):
                logger.info(
                    "Document is single-language (English), skipping dual language processing"
                )
                # Keep processing_result as is for single language display
            else:
                # Use the dual language processor for non-English documents
                dual_result = _create_dual_language_sections(
                    processing_result, processing_result, "en"
                )
                processing_result = dual_result

        context = {
            "document_info": document_info,
            "processing_result": processing_result,
            "patient_info": processing_result.get("patient_info", {}),
            "sections": processing_result.get("sections", []),
            "doc_index": doc_index,
            "is_single_language": processing_result.get("is_single_language", False),
        }

        return render(
            request, "patient_data/view_uploaded_document.html", context, using="jinja2"
        )

    except Exception as e:
        logger.error(f"Error viewing uploaded document: {str(e)}")
        messages.error(request, f"Error loading document: {str(e)}")
        return redirect("patient_data:uploaded_documents")
