#!/usr/bin/env python3
"""
Simplified Clinical Data View
Provides clean, accessible data structures for flexible template rendering
"""

import logging
from typing import Any, Dict, List, Optional

from django.contrib.sessions.models import Session
from django.http import Http404
from django.shortcuts import render
from django.views import View

logger = logging.getLogger(__name__)


class SimplifiedClinicalDataView(View):
    """Django view that provides clean, simple clinical data for flexible template rendering"""

    def get(self, request, patient_id):
        """Handle GET request for simplified clinical data view"""
        print(f"\n" + "="*80)
        print(f"� SIMPLIFIED VIEW CALLED! Patient ID: {patient_id}")
        print(f"🚀 Request method: {request.method}")
        print(f"🚀 Request path: {request.path}")
        print(f"="*80 + "\n")
        try:
            # Get simplified clinical data
            data_extractor = SimplifiedDataExtractor()
            simplified_data = data_extractor.get_simplified_clinical_data(patient_id)
            print(f"🔍 DEBUG: Simplified data success: {simplified_data.get('success', False)}")
            print(f"🔍 DEBUG: Sections count: {len(simplified_data.get('sections', []))}")

            # Get patient identity for header
            patient_identity = self._get_patient_identity(patient_id)
            print(f"🔍 DEBUG: Patient identity found: {bool(patient_identity)}")

            context = {
                "patient_id": patient_id,
                "simplified_data": simplified_data,
                "patient_identity": patient_identity,
                "debug": request.GET.get("debug", False),
            }

            return render(
                request, "patient_data/simplified_clinical_view.html", context
            )

        except Exception as e:
            print(f"❌ DEBUG: Error in SimplifiedClinicalDataView: {e}")
            logger.error(f"Error in SimplifiedClinicalDataView: {e}")
            raise Http404("Patient data not found")

    def _get_patient_identity(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get basic patient identity information"""
        try:
            # Use the same session lookup logic as other views
            session_key = f"patient_match_{patient_id}"

            try:
                session = Session.objects.get(session_key=session_key)
                session_data = session.get_decoded()
                cda_content = session_data.get("cda_content", "")

                if cda_content:
                    # Extract patient identity
                    from patient_data.services.enhanced_cda_processor import (
                        EnhancedCDAProcessor,
                    )

                    processor = EnhancedCDAProcessor(target_language="en")
                    result = processor.process_administrative_data(cda_content)

                    if result.get("success") and result.get("patient_identity"):
                        return result["patient_identity"]
            except Session.DoesNotExist:
                logger.warning(f"No session found for patient {patient_id}")

            return None

        except Exception as e:
            logger.error(f"Error getting patient identity for {patient_id}: {e}")
            return None


class SimplifiedDataExtractor:
    """Extracts and simplifies clinical data from CDA documents"""

    def get_simplified_clinical_data(self, patient_id: str) -> Dict[str, Any]:
        """
        Get clean, simple clinical data organized by section type
        Returns simple dictionaries and lists that templates can easily work with
        """
        try:
            # Get patient CDA content using the same session lookup as debugger
            cda_content = self._get_patient_cda_content(patient_id)
            if not cda_content:
                return {"error": "No patient data found", "success": False}

            # Process with enhanced processor to get raw data
            from patient_data.services.enhanced_cda_processor import (
                EnhancedCDAProcessor,
            )

            processor = EnhancedCDAProcessor(target_language="en")
            enhanced_result = processor.process_clinical_sections(cda_content)

            if not enhanced_result.get("success"):
                return {"error": "Failed to process clinical data", "success": False}

            # Convert to simple, accessible format
            simplified_data = {
                "success": True,
                "patient_id": patient_id,
                "sections": [],
            }

            for section in enhanced_result.get("sections", []):
                simplified_section = self._simplify_section(section)
                if simplified_section:
                    simplified_data["sections"].append(simplified_section)

            logger.info(
                f"Simplified {len(simplified_data['sections'])} sections for patient {patient_id}"
            )
            return simplified_data

        except Exception as e:
            logger.error(f"Error getting simplified clinical data: {e}")
            return {"error": str(e), "success": False}

    def _simplify_section(self, section: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert complex section data to simple, accessible format"""
        try:
            # Get basic section info
            simplified = {
                "section_code": section.get("section_code", ""),
                "title": self._get_section_title(section),
                "type": self._determine_section_type(section.get("section_code", "")),
                "entries": [],
            }

            # Process entries from different possible sources
            entries_data = []

            # Try to get from table_data (country-specific extraction)
            if "table_data" in section:
                entries_data.extend(section["table_data"])

            # Try to get from structured_data
            elif "structured_data" in section:
                entries_data.extend(section["structured_data"])

            # Process each entry into simple format
            for entry_data in entries_data:
                simplified_entry = self._simplify_entry(entry_data, simplified["type"])
                if simplified_entry:
                    simplified["entries"].append(simplified_entry)

            # Only return section if it has entries
            if simplified["entries"]:
                logger.info(
                    f"Simplified section {simplified['section_code']}: {len(simplified['entries'])} entries"
                )
                return simplified

            return None

        except Exception as e:
            logger.error(f"Error simplifying section: {e}")
            return None

    def _simplify_entry(
        self, entry_data: Dict[str, Any], section_type: str
    ) -> Optional[Dict[str, Any]]:
        """Convert complex entry data to simple, clean format"""
        try:
            if "data" not in entry_data:
                return None

            data = entry_data["data"]
            simplified = {
                "original_data": data,  # Keep original for debugging
            }

            # Extract based on section type
            if section_type == "problems":
                simplified.update(self._extract_problem_data(data))
            elif section_type == "medications":
                simplified.update(self._extract_medication_data(data))
            elif section_type == "allergies":
                simplified.update(self._extract_allergy_data(data))
            else:
                simplified.update(self._extract_generic_data(data))

            return simplified

        except Exception as e:
            logger.error(f"Error simplifying entry: {e}")
            return None

    def _extract_problem_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract clean problem/diagnosis data"""
        return {
            # Main fields - extract both code and description from nested structures
            "problem_code": self._extract_code(
                data.get("condition_code") or data.get("agent_code")
            ),
            "problem_description": self._extract_description(
                data.get("condition_display") or data.get("agent_display")
            ),
            "problem_full": self._extract_any_value(data.get("value")),
            # Additional fields
            "onset_date": self._clean_date(data.get("onset_date") or data.get("date")),
            "status": self._extract_any_value(data.get("status")),
            "severity": self._extract_any_value(data.get("severity")),
            "code_system": data.get("code_system", ""),
        }

    def _extract_medication_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract clean medication data"""
        return {
            # Main fields
            "medication_name": self._extract_description(
                data.get("medication_display")
            ),
            "medication_code": self._extract_code(data.get("medication_code")),
            "active_ingredient": self._extract_description(
                data.get("ingredient_display")
            ),
            "ingredient_code": self._extract_code(data.get("ingredient_code")),
            # Additional fields
            "dosage": self._extract_any_value(data.get("dosage")),
            "route": self._extract_any_value(data.get("posology")),
            "start_date": self._clean_date(data.get("date")),
            "status": self._extract_any_value(data.get("status")),
            "code_system": data.get("code_system", ""),
        }

    def _extract_allergy_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract clean allergy data"""
        return {
            # Main fields
            "allergen_name": self._extract_description(data.get("agent_display")),
            "allergen_code": self._extract_code(data.get("agent_code")),
            "reaction": self._extract_description(data.get("manifestation_display")),
            # Additional fields
            "severity": self._extract_any_value(data.get("severity")),
            "status": self._extract_any_value(data.get("status")),
            "onset_date": self._clean_date(data.get("date")),
            "code_system": data.get("code_system", ""),
        }

    def _extract_generic_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract generic clinical data"""
        extracted = {}

        # Extract all fields we can find
        for key, value in data.items():
            if key.endswith("_code"):
                # This is a code field
                base_name = key.replace("_code", "")
                extracted[f"{base_name}_code"] = self._extract_code(value)
            elif key.endswith("_display"):
                # This is a description field
                base_name = key.replace("_display", "")
                extracted[f"{base_name}_description"] = self._extract_description(value)
            else:
                # Generic field
                extracted[key] = self._extract_any_value(value)

        return extracted

    def _extract_code(self, value: Any) -> str:
        """Extract code from potentially nested structure"""
        if not value:
            return ""

        if isinstance(value, dict):
            # Try different code keys
            return value.get("code") or value.get("value") or str(value)

        return str(value)

    def _extract_description(self, value: Any) -> str:
        """Extract description from potentially nested structure"""
        if not value:
            return ""

        if isinstance(value, dict):
            # Try different description keys
            return (
                value.get("displayName")
                or value.get("display_name")
                or value.get("value")
                or str(value)
            )

        return str(value)

    def _extract_any_value(self, value: Any) -> str:
        """Extract any value, trying description first then code"""
        if not value:
            return ""

        if isinstance(value, dict):
            return (
                value.get("displayName")
                or value.get("display_name")
                or value.get("value")
                or value.get("code")
                or str(value)
            )

        return str(value)

    def _clean_date(self, date_value: Any) -> str:
        """Clean up date formatting"""
        if not date_value:
            return ""

        date_str = str(date_value).strip()

        # Basic date cleaning - you can enhance this
        import re

        # Try to extract date patterns
        date_match = re.search(r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})", date_str)
        if date_match:
            return date_match.group(1)

        # Try ISO format
        iso_match = re.search(r"(\d{4}-\d{2}-\d{2})", date_str)
        if iso_match:
            return iso_match.group(1)

        return date_str

    def _get_section_title(self, section: Dict[str, Any]) -> str:
        """Get clean section title"""
        title_data = section.get("title", {})
        if isinstance(title_data, dict):
            return (
                title_data.get("coded")
                or title_data.get("original")
                or title_data.get("translated")
                or "Clinical Section"
            )
        return str(title_data) or "Clinical Section"

    def _determine_section_type(self, section_code: str) -> str:
        """Determine section type from code"""
        type_mapping = {
            "11450-4": "problems",
            "46240-8": "problems",
            "10160-0": "medications",
            "29549-3": "medications",
            "48765-2": "allergies",
            "10155-0": "allergies",
        }
        return type_mapping.get(section_code, "generic")

    def _get_patient_cda_content(self, patient_id: str) -> Optional[str]:
        """Get patient CDA content - same logic as clinical debugger"""
        if not patient_id:
            return None

        try:
            session_key = f"patient_match_{patient_id}"
            match_data = None

            # Search across all Django sessions
            all_sessions = Session.objects.all()
            for db_session in all_sessions:
                try:
                    db_session_data = db_session.get_decoded()
                    if session_key in db_session_data:
                        match_data = db_session_data[session_key]
                        logger.info(f"Found patient {patient_id} data in session")
                        break
                except Exception:
                    continue

            if not match_data:
                return None

            # Get CDA content based on selection
            selected_cda_type = match_data.get("cda_type") or match_data.get(
                "preferred_cda_type", "L3"
            )

            if selected_cda_type == "L3":
                cda_content = match_data.get("l3_cda_content")
            elif selected_cda_type == "L1":
                cda_content = match_data.get("l1_cda_content")
            else:
                cda_content = (
                    match_data.get("l3_cda_content")
                    or match_data.get("l1_cda_content")
                    or match_data.get("cda_content")
                )

            return cda_content

        except Exception as e:
            logger.error(f"Error retrieving CDA content: {e}")
            return None
