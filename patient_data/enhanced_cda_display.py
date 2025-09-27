"""
CDA Display Tool Integration
Integrates the CTS-compliant Enhanced CDA Processor with the main CDA display system
"""

import json
import logging
from typing import Any, Dict, Optional

from django.contrib.sessions.models import Session
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from patient_data.services.enhanced_cda_processor import EnhancedCDAProcessor
from patient_data.simplified_clinical_view import (
    SimplifiedClinicalDataView,
    SimplifiedDataExtractor,
)
from patient_data.translation_utils import (
    detect_document_language,
    get_template_translations,
)

logger = logging.getLogger(__name__)


class EnhancedCDADisplayView(View):
    """Enhanced CDA display view with CTS-compliant clinical sections"""

    def get(self, request, patient_id=None):
        """Display CDA document with enhanced clinical sections"""
        print(f"\n" + "="*80)
        print(f"� ENHANCED CDA VIEW CALLED! Patient ID: {patient_id}")
        print(f"[ROCKET] Request method: {request.method}")
        print(f"[ROCKET] Request path: {request.path}")
        print(f"="*80 + "\n")
        try:
            # Get patient CDA data (this would come from your existing patient data service)
            cda_content = self._get_patient_cda_content(patient_id)
            print(f"[SEARCH] DEBUG: CDA content found: {bool(cda_content)}")
            if not cda_content:
                print(f"[ERROR] DEBUG: No CDA content for patient {patient_id}")
                return JsonResponse({"error": "Patient CDA data not found"}, status=404)

            # Detect document language
            source_language = detect_document_language(cda_content)
            target_language = request.GET.get("lang", "en")

            # Initialize enhanced processor
            processor = EnhancedCDAProcessor(target_language=target_language)

            # Process clinical sections with CTS compliance
            logger.info(f"Processing CDA content for patient {patient_id}")
            logger.info(
                f"Content type: {'XML' if '<?xml' in cda_content or '<ClinicalDocument' in cda_content else 'HTML'}"
            )
            logger.info(f"Content length: {len(cda_content)} characters")

            # Get both enhanced sections (for compatibility) and simplified data (for flexible rendering)
            enhanced_sections = processor.process_clinical_sections(
                cda_content=cda_content, source_language=source_language
            )

            # Get simplified clinical data for flexible template rendering
            simplified_extractor = SimplifiedDataExtractor()
            simplified_data = simplified_extractor.get_simplified_clinical_data(
                patient_id
            )
            logger.info(f"Simplified data result: success={simplified_data.get('success')}, sections={len(simplified_data.get('sections', []))}")
            if not simplified_data.get('success'):
                logger.warning(f"Simplified data failed for patient {patient_id}: {simplified_data.get('error')}")

            logger.info(f"Enhanced sections result: {enhanced_sections.keys()}")
            logger.info(
                f"Sections processed: {enhanced_sections.get('sections_count', 0)}"
            )
            logger.info(
                f"Content type detected: {enhanced_sections.get('content_type', 'unknown')}"
            )

            # Log each section for debugging
            for i, section in enumerate(enhanced_sections.get("sections", [])):
                section_code = section.get("section_code", "No code")
                title = section.get("title", {}).get("original", "No title")
                has_ps_table = section.get("has_ps_table", False)
                logger.info(
                    f"Section {i+1}: Code={section_code}, Title='{title}', Has_PS_Table={has_ps_table}"
                )

                # Check if section has value set data
                if "table_data" in section:
                    table_entries = len(section.get("table_data", []))
                    logger.info(f"  Table data entries: {table_entries}")

                    # Check first entry for value set fields
                    if table_entries > 0:
                        first_entry = section["table_data"][0]
                        entry_type = first_entry.get("type", "unknown")
                        logger.info(f"  First entry type: {entry_type}")

                        if "fields" in first_entry:
                            field_count = len(first_entry.get("fields", {}))
                            logger.info(
                                f"  Value set fields in first entry: {field_count}"
                            )
                            for field_name, field_info in first_entry.get(
                                "fields", {}
                            ).items():
                                has_valueset = field_info.get("has_valueset", False)
                                value = field_info.get("value", "No value")
                                logger.info(
                                    f"    {field_name}: {value} (has_valueset: {has_valueset})"
                                )
                else:
                    logger.info(f"  No table_data found in section")

            # Get template translations
            template_translations = get_template_translations(
                source_language=source_language, target_language=target_language
            )

            # Get patient identity from enhanced sections
            patient_identity_data = enhanced_sections.get("patient_identity", {})

            # Create patient_identity object for template compatibility
            patient_identity = type(
                "PatientIdentity",
                (object,),
                {
                    "patient_id": patient_identity_data.get(
                        "primary_patient_id", patient_id
                    ),
                    "url_patient_id": patient_id,  # Use the URL patient_id for navigation
                    "given_name": patient_identity_data.get("given_name", ""),
                    "family_name": patient_identity_data.get("family_name", ""),
                    "birth_date": patient_identity_data.get("birth_date", ""),
                    "gender": patient_identity_data.get("gender", ""),
                },
            )()

            # Prepare context for template
            context = {
                "patient_id": patient_id,
                "patient_identity": patient_identity,
                "enhanced_sections": enhanced_sections,
                "simplified_data": simplified_data,  # Add simplified data for flexible rendering
                "template_translations": template_translations,
                "source_language": source_language,
                "target_language": target_language,
                "document_metadata": {
                    "success": enhanced_sections.get("success", False),
                    "content_type": enhanced_sections.get("content_type", "unknown"),
                    "sections_count": enhanced_sections.get("sections_count", 0),
                    "coded_sections_count": enhanced_sections.get(
                        "coded_sections_count", 0
                    ),
                    "medical_terms_count": enhanced_sections.get(
                        "medical_terms_count", 0
                    ),
                    "translation_quality": enhanced_sections.get(
                        "translation_quality", "Basic"
                    ),
                    "uses_coded_sections": enhanced_sections.get(
                        "uses_coded_sections", False
                    ),
                },
            }

            return render(request, "patient_data/enhanced_patient_cda.html", context)

        except Exception as e:
            logger.error(f"Error in enhanced CDA display: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    def _get_patient_cda_content(self, patient_id: str) -> Optional[str]:
        """Get patient CDA content from Django sessions - same logic as clinical debugger"""
        if not patient_id:
            return None

        try:
            # Use the same session lookup logic as clinical debugger
            session_key = f"patient_match_{patient_id}"
            match_data = None

            # Search across all Django sessions for the patient data
            all_sessions = Session.objects.all()
            for db_session in all_sessions:
                try:
                    db_session_data = db_session.get_decoded()
                    if session_key in db_session_data:
                        match_data = db_session_data[session_key]
                        logger.info(
                            f"Found patient {patient_id} data in session: {db_session.session_key}"
                        )
                        break
                except Exception:
                    continue  # Skip corrupted sessions

            if not match_data:
                logger.warning(f"No session data found for patient {patient_id}")
                return None

            # Get CDA content based on user's current selection (same as debugger)
            selected_cda_type = match_data.get("cda_type") or match_data.get(
                "preferred_cda_type", "L3"
            )

            if selected_cda_type == "L3":
                cda_content = match_data.get("l3_cda_content")
            elif selected_cda_type == "L1":
                cda_content = match_data.get("l1_cda_content")
            else:
                # Fallback to original priority if no clear selection
                cda_content = (
                    match_data.get("l3_cda_content")
                    or match_data.get("l1_cda_content")
                    or match_data.get("cda_content")
                )

            if cda_content:
                logger.info(
                    f"Retrieved {selected_cda_type} CDA content for patient {patient_id}: {len(cda_content)} characters"
                )
                return cda_content
            else:
                logger.warning(f"No CDA content found for patient {patient_id}")
                return None

        except Exception as e:
            logger.error(f"Error retrieving CDA content for patient {patient_id}: {e}")
            return None


@method_decorator(csrf_exempt, name="dispatch")
class CDALanguageToggleView(View):
    """API endpoint for toggling between source and target language display"""

    def post(self, request):
        """Toggle language display for CDA sections"""
        try:
            data = json.loads(request.body)
            patient_id = data.get("patient_id")
            target_language = data.get("target_language", "en")
            section_id = data.get("section_id")

            if not patient_id or not section_id:
                return JsonResponse(
                    {"error": "Missing required parameters"}, status=400
                )

            # Get CDA content
            cda_content = self._get_patient_cda_content(patient_id)
            if not cda_content:
                return JsonResponse({"error": "Patient data not found"}, status=404)

            # Detect source language
            source_language = detect_document_language(cda_content)

            # Process with enhanced processor
            processor = EnhancedCDAProcessor(target_language=target_language)
            enhanced_sections = processor.process_clinical_sections(
                cda_content=cda_content, source_language=source_language
            )

            # Find the specific section
            section_data = None
            for section in enhanced_sections.get("sections", []):
                if section.get("section_id") == section_id:
                    section_data = section
                    break

            if not section_data:
                return JsonResponse({"error": "Section not found"}, status=404)

            return JsonResponse(
                {
                    "success": True,
                    "section_data": section_data,
                    "metadata": {
                        "source_language": source_language,
                        "target_language": target_language,
                        "has_ps_table": section_data.get("has_ps_table", False),
                        "is_coded_section": section_data.get("is_coded_section", False),
                    },
                }
            )

        except Exception as e:
            logger.error(f"Error in language toggle: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    def _get_patient_cda_content(self, patient_id: str) -> Optional[str]:
        """Get patient CDA content - same as above"""
        # This should integrate with your existing patient data service
        return EnhancedCDADisplayView()._get_patient_cda_content(patient_id)


def get_enhanced_clinical_sections_api(request, patient_id):
    """API endpoint to get enhanced clinical sections data"""
    try:
        target_language = request.GET.get("lang", "en")

        # Get CDA content
        display_view = EnhancedCDADisplayView()
        cda_content = display_view._get_patient_cda_content(patient_id)

        if not cda_content:
            return JsonResponse({"error": "Patient data not found"}, status=404)

        # Detect source language and process
        source_language = detect_document_language(cda_content)
        processor = EnhancedCDAProcessor(target_language=target_language)

        enhanced_sections = processor.process_clinical_sections(
            cda_content=cda_content, source_language=source_language
        )

        return JsonResponse(
            {
                "success": True,
                "data": enhanced_sections,
                "metadata": {
                    "patient_id": patient_id,
                    "source_language": source_language,
                    "target_language": target_language,
                    "processing_timestamp": "2025-08-05T12:00:00Z",
                },
            }
        )

    except Exception as e:
        logger.error(f"Error in enhanced sections API: {e}")
        return JsonResponse({"error": str(e)}, status=500)
