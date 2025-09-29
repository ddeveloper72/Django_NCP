#!/usr/bin/env python3
"""
Simplified Clinical Data View
Provides clean, accessible data structures for flexible template rendering
"""

import logging
from typing import Any, Dict, List, Optional

from django.contrib.sessions.models import Session
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views import View

logger = logging.getLogger(__name__)


class SimplifiedClinicalDataView(View):
    """Django view that provides clean, simple clinical data for flexible template rendering"""

    def get(self, request, patient_id):
        """Handle GET request for simplified clinical data view"""
        print(f"\n" + "=" * 80)
        print(f"🟢 SIMPLIFIED VIEW CALLED! Patient ID: {patient_id}")
        print(f"[ROCKET] Request method: {request.method}")
        print(f"[ROCKET] Request path: {request.path}")
        print(f"[ROCKET] Full URL: {request.build_absolute_uri()}")
        print(f"=" * 80 + "\n")

        try:
            # Get simplified clinical data
            data_extractor = SimplifiedDataExtractor()
            print(f"[SEARCH] DEBUG: Created SimplifiedDataExtractor instance")

            simplified_data = data_extractor.get_simplified_clinical_data(patient_id)
            print(f"[SEARCH] DEBUG: Got simplified data: {bool(simplified_data)}")

            if simplified_data:
                print(
                    f"[SEARCH] DEBUG: Sections count: {len(simplified_data.get('sections', []))}"
                )

            # Get patient identity for header
            patient_identity = self._get_patient_identity(patient_id)
            print(f"[SEARCH] DEBUG: Patient identity found: {bool(patient_identity)}")

            context = {
                "patient_id": patient_id,
                "simplified_data": simplified_data,
                "patient_identity": patient_identity,
                "debug": request.GET.get("debug", False),
            }

            print(
                f"[SEARCH] DEBUG: Rendering template with context keys: {list(context.keys())}"
            )
            return render(
                request, "patient_data/simplified_clinical_view.html", context
            )

        except Exception as e:
            print(f"[ERROR] ERROR in simplified clinical view: {e}")
            import traceback

            traceback.print_exc()
            return render(
                request,
                "patient_data/clinical_view_error.html",
                {
                    "patient_id": patient_id,
                    "error": str(e),
                    "debug": True,
                },
            )

    def _get_patient_identity(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get basic patient identity information"""
        try:
            # Find session with patient data
            sessions = Session.objects.all()
            for session in sessions:
                data = session.get_decoded()
                patient_key = f"patient_match_{patient_id}"
                if patient_key in data:
                    patient_data = data[patient_key]
                    return {
                        "name": patient_data.get("name", "Unknown Patient"),
                        "birth_date": patient_data.get("birth_date", ""),
                        "gender": patient_data.get("gender", ""),
                        "id": patient_id,
                    }
            return None
        except Exception as e:
            logger.error(f"Error getting patient identity for {patient_id}: {e}")
            return None


class SimplifiedDataExtractor:
    """Extract and transform clinical data to simple, accessible format"""

    def get_simplified_clinical_data(self, patient_id: str) -> Dict[str, Any]:
        """Get all clinical data in simplified format"""
        try:
            logger.info(f"Starting simplified data extraction for patient {patient_id}")

            # Get the CDA content
            cda_content = self._get_patient_cda_content(patient_id)
            if not cda_content:
                logger.warning(f"No CDA content found for patient {patient_id}")
                return {"sections": []}

            # Process with Enhanced CDA Processor
            try:
                from patient_data.services.enhanced_cda_processor import (
                    EnhancedCDAProcessor,
                )

                processor = EnhancedCDAProcessor(target_language="en")
                enhanced_result = processor.process_clinical_sections(cda_content)

                if not enhanced_result.get("success"):
                    logger.error(
                        f"Enhanced CDA processing failed: {enhanced_result.get('error', 'Unknown error')}"
                    )
                    return {"sections": []}

                # Convert to simplified format
                enhanced_sections = enhanced_result.get("sections", [])
                simplified_sections = []

                for section in enhanced_sections:
                    simplified_section = self._simplify_section(section)
                    if simplified_section:
                        simplified_sections.append(simplified_section)

                logger.info(
                    f"Simplified {len(simplified_sections)} sections for patient {patient_id}"
                )

                return {
                    "sections": simplified_sections,
                    "patient_id": patient_id,
                    "total_sections": len(simplified_sections),
                }

            except ImportError as e:
                logger.error(f"Could not import Enhanced CDA Processor: {e}")
                return {"sections": []}

        except Exception as e:
            logger.error(f"Error in simplified data extraction: {e}")
            return {"sections": []}

    def _get_patient_cda_content(self, patient_id: str) -> Optional[str]:
        """Get patient CDA content using same logic as working debugger"""
        try:
            # Find session with patient data (matching clinical_data_debugger pattern)
            sessions = Session.objects.all()
            for session in sessions:
                data = session.get_decoded()
                patient_key = f"patient_match_{patient_id}"

                if patient_key in data:
                    logger.info(f"Found patient {patient_id} data in session")

                    # Try L3 first, then L1 (same as debugger)
                    for content_type in ["l3_cda_content", "l1_cda_content"]:
                        if content_type in data and data[content_type]:
                            cda_content = data[content_type]
                            cda_type = (
                                "L3" if content_type == "l3_cda_content" else "L1"
                            )
                            logger.info(
                                f"Successfully retrieved CDA content for patient {patient_id}, type: {cda_type}"
                            )
                            return cda_content

                    logger.warning(
                        f"Patient {patient_id} found but no CDA content available"
                    )
                    return None

            logger.warning(f"No session found with patient {patient_id} data")
            return None

        except Exception as e:
            logger.error(f"Error retrieving CDA content for patient {patient_id}: {e}")
            return None

    def _simplify_section(self, section: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert enhanced section to simple, accessible format"""
        try:
            # Enhanced CDA Processor returns sections with 'title' and 'structured_data'
            section_title = section.get("title", section.get("name", "Unknown Section"))

            # Handle title that might be a dict with translation info
            if isinstance(section_title, dict):
                # Use 'translated' or 'coded' or 'original' from title dict
                section_name = (
                    section_title.get("translated")
                    or section_title.get("coded")
                    or section_title.get("original")
                    or "Unknown Section"
                )
            else:
                section_name = (
                    str(section_title) if section_title else "Unknown Section"
                )

            section_items = section.get("structured_data", section.get("items", []))

            if not section_items:
                logger.debug(
                    f"Section '{section_name}' has no structured_data or items"
                )
                return None

            # Create simplified section structure
            simplified_section = {
                "name": section_name,
                "display_name": self._get_display_name(section_name),
                "items": [],
            }

            for item in section_items:
                simplified_item = self._simplify_item(item)
                if simplified_item:
                    simplified_section["items"].append(simplified_item)

            logger.debug(
                f"Section '{section_name}' simplified to {len(simplified_section['items'])} items"
            )
            return simplified_section if simplified_section["items"] else None

        except Exception as e:
            logger.error(f"Error simplifying section: {e}")
            return None

    def _simplify_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert enhanced item to simple format"""
        try:
            # Handle both enhanced processor format and original format
            if isinstance(item, dict):
                # Enhanced processor format has 'fields' with detailed data
                if "fields" in item and item["fields"]:
                    item_data = item["fields"]  # Use fields data
                elif "data" in item and item["data"]:
                    item_data = item["data"]  # Use nested data
                else:
                    item_data = item  # Use item directly

                # Extract key information - handle multiple possible structures
                simplified_item = {
                    "text": self._extract_text(item_data),
                    "code": self._extract_code(item_data),
                    "date": self._extract_date(item_data),
                    "status": self._extract_status(item_data),
                }

                # Clean up empty fields
                simplified_item = {k: v for k, v in simplified_item.items() if v}

                return simplified_item if simplified_item else None
            else:
                return None

        except Exception as e:
            logger.error(f"Error simplifying item: {e}")
            return None

    def _extract_text(self, item_data: Dict[str, Any]) -> str:
        """Extract display text from item data"""
        # Enhanced CDA processor uses nested field structure with 'value' keys
        # Try fields that typically contain display text
        display_fields = [
            "Medication DisplayName",
            "Medication Name",
            "Procedure DisplayName",
            "Problem DisplayName",
            "Reaction DisplayName",
            "Device DisplayName",
            "displayName",
            "text",
            "display_text",
            "value",
            "description",
            "content",
        ]

        for field in display_fields:
            if field in item_data:
                field_data = item_data[field]
                if isinstance(field_data, dict) and "value" in field_data:
                    return str(field_data["value"])
                elif field_data:
                    return str(field_data)

        # Fallback - try to get any meaningful text
        for key, value in item_data.items():
            if isinstance(value, dict) and "value" in value and value["value"]:
                text_value = str(value["value"]).strip()
                if text_value and not text_value.isdigit():  # Prefer text over numbers
                    return text_value

        return ""

    def _extract_code(self, item_data: Dict[str, Any]) -> str:
        """Extract code from item data"""
        # Enhanced CDA processor uses nested field structure with 'value' keys
        code_fields = [
            "Medication Code",
            "Procedure Code",
            "Problem Code",
            "Reaction Code",
            "Device Code",
            "Status Code",
            "code",
            "codeValue",
            "concept_code",
        ]

        for field in code_fields:
            if field in item_data:
                field_data = item_data[field]
                if isinstance(field_data, dict) and "value" in field_data:
                    return str(field_data["value"])
                elif field_data:
                    return str(field_data)
        return ""

    def _extract_date(self, item_data: Dict[str, Any]) -> str:
        """Extract date from item data"""
        # Enhanced CDA processor uses nested field structure with 'value' keys
        date_fields = [
            "Treatment Start Date",
            "Treatment End Date",
            "Procedure Start Date",
            "effectiveTime",
            "date",
            "effective_time",
            "timestamp",
            "time",
        ]

        for field in date_fields:
            if field in item_data:
                field_data = item_data[field]
                if isinstance(field_data, dict) and "value" in field_data:
                    return str(field_data["value"])
                elif field_data:
                    return str(field_data)
        return ""

    def _extract_status(self, item_data: Dict[str, Any]) -> str:
        """Extract status from item data"""
        # Enhanced CDA processor uses nested field structure with 'value' keys
        status_fields = [
            "Status Code",
            "Procedure Status Code",
            "status",
            "statusCode",
            "state",
        ]

        for field in status_fields:
            if field in item_data:
                field_data = item_data[field]
                if isinstance(field_data, dict) and "value" in field_data:
                    return str(field_data["value"])
                elif field_data:
                    return str(field_data)
        return ""

    def _get_display_name(self, section_name: str) -> str:
        """Get user-friendly display name for section"""
        # Ensure section_name is a string
        if not isinstance(section_name, str):
            section_name = str(section_name) if section_name else "Unknown Section"

        display_names = {
            "conditions": "Medical Conditions",
            "medications": "Current Medications",
            "allergies": "Allergies & Intolerances",
            "procedures": "Medical Procedures",
            "immunizations": "Vaccinations",
            "vital_signs": "Vital Signs",
            "lab_results": "Laboratory Results",
        }
        return display_names.get(section_name.lower(), section_name.title())
