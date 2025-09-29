"""
Session Data Service - Reusable session data retrieval for patient data views

This service provides standardized session data access patterns used by both
the debug clinical view and CDA display views. It implements comprehensive
session searching across both current request session and database sessions.
"""

import logging
from typing import Any, Dict, Optional, Tuple

from django.contrib.sessions.models import Session

logger = logging.getLogger(__name__)


class SessionDataService:
    """
    Centralized service for retrieving patient session data with robust search capabilities.

    This service implements the proven session search pattern from the clinical data debugger
    that successfully locates patient data across different session storage scenarios.
    """

    @staticmethod
    def get_patient_data(
        request, session_id: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Retrieve patient data using comprehensive session search strategy.

        This method replicates the successful session search logic from the clinical
        data debugger that reliably finds patient data.

        Args:
            request: Django request object with session
            session_id: Patient session ID to search for

        Returns:
            Tuple of (match_data, debug_info):
            - match_data: Patient data dictionary if found, None otherwise
            - debug_info: String with search details for debugging
        """
        session_key = f"patient_match_{session_id}"
        debug_steps = []

        # Step 1: Try current request session (fast path)
        debug_steps.append(
            f"Step 1: Checking current request session for key '{session_key}'"
        )
        match_data = request.session.get(session_key)

        if match_data:
            debug_steps.append(f"✓ Found patient data in current request session")
            return match_data, "\n".join(debug_steps)

        debug_steps.append("✗ Not found in current request session")

        # Step 2: Try to find session_id as direct Django session key
        debug_steps.append(
            f"Step 2: Checking database for direct session key '{session_id}'"
        )
        try:
            db_session = Session.objects.get(session_key=session_id)
            db_session_data = db_session.get_decoded()
            match_data = db_session_data.get(session_key)

            if match_data:
                debug_steps.append(
                    f"✓ Found patient data in database session with direct key"
                )
                return match_data, "\n".join(debug_steps)

            debug_steps.append("✗ Direct session key exists but no patient data found")

        except Session.DoesNotExist:
            debug_steps.append("✗ No database session with direct key found")

        # Step 3: Search all database sessions for patient_match_{session_id}
        debug_steps.append(
            f"Step 3: Searching all database sessions for key '{session_key}'"
        )
        all_sessions = Session.objects.all()
        sessions_checked = 0
        sessions_with_errors = 0

        for db_session in all_sessions:
            try:
                sessions_checked += 1
                db_session_data = db_session.get_decoded()
                if session_key in db_session_data:
                    match_data = db_session_data[session_key]
                    debug_steps.append(
                        f"✓ Found patient data in database session after checking {sessions_checked} sessions"
                    )
                    return match_data, "\n".join(debug_steps)

            except Exception as e:
                sessions_with_errors += 1
                # Skip corrupted sessions silently but track them
                continue

        debug_steps.append(
            f"✗ Searched {sessions_checked} database sessions, {sessions_with_errors} had errors"
        )
        debug_steps.append("❌ No patient data found in any session")

        return None, "\n".join(debug_steps)

    @staticmethod
    def get_cda_content(
        match_data: Dict[str, Any], preferred_type: str = "L3"
    ) -> Tuple[Optional[str], str]:
        """
        Extract CDA content from patient data with type preference.

        Args:
            match_data: Patient data dictionary
            preferred_type: Preferred CDA type ("L3", "L1", or "auto")

        Returns:
            Tuple of (cda_content, cda_type_used)
        """
        if not match_data:
            return None, "none"

        # Get CDA content based on preference (matching debug view logic)
        selected_cda_type = match_data.get("cda_type") or match_data.get(
            "preferred_cda_type", preferred_type
        )

        if selected_cda_type == "L3":
            cda_content = match_data.get("l3_cda_content")
            if cda_content:
                return cda_content, "L3"
        elif selected_cda_type == "L1":
            cda_content = match_data.get("l1_cda_content")
            if cda_content:
                return cda_content, "L1"

        # Fallback to priority search (L3 -> L1 -> generic)
        cda_content = (
            match_data.get("l3_cda_content")
            or match_data.get("l1_cda_content")
            or match_data.get("cda_content")
        )

        if cda_content:
            # Determine which type was actually used
            if match_data.get("l3_cda_content"):
                return cda_content, "L3"
            elif match_data.get("l1_cda_content"):
                return cda_content, "L1"
            else:
                return cda_content, "generic"

        return None, "none"

    @staticmethod
    def get_available_session_ids(request) -> list:
        """
        Get list of available patient session IDs from current request session.

        Args:
            request: Django request object

        Returns:
            List of available session IDs
        """
        return [
            key.replace("patient_match_", "")
            for key in request.session.keys()
            if key.startswith("patient_match_")
        ]

    @staticmethod
    def create_session_not_found_context(
        session_id: str, debug_info: str, request
    ) -> Dict[str, Any]:
        """
        Create standardized error context for missing session data.

        Args:
            session_id: The session ID that wasn't found
            debug_info: Debug information from search attempt
            request: Django request object

        Returns:
            Context dictionary for error template
        """
        return {
            "error_title": "Patient Data Not Found",
            "error_message": f"No patient data available for session ID: {session_id}",
            "error_details": [
                "The patient session may have expired",
                "You may need to search for the patient again",
                "The session ID in the URL may be invalid",
                "Session data might be stored in a different session",
            ],
            "suggested_actions": [
                "Go back to Patient Search",
                "Search for the patient again",
                "Check if the URL is correct",
                "Try the debug clinical view to verify data exists",
            ],
            "session_id": session_id,
            "available_sessions": SessionDataService.get_available_session_ids(request),
            "debug_info": debug_info,
            "debug_url": f"/patients/debug/clinical/{session_id}/",
        }
