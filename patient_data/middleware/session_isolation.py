"""
GDPR Patient Session Isolation Middleware

This middleware ensures that each patient session is completely isolated,
preventing any mixing of patient data between sessions which could cause
serious GDPR data breaches.

Key Features:
- Enforces one patient per session
- Clears conflicting patient data automatically
- Logs session isolation events for audit
- Maintains session security for healthcare data
"""

import logging
from django.utils.deprecation import MiddlewareMixin
from django.contrib.sessions.backends.db import SessionStore

logger = logging.getLogger(__name__)

class PatientSessionIsolationMiddleware(MiddlewareMixin):
    """
    Middleware to enforce patient session isolation for GDPR compliance
    
    This middleware ensures that:
    1. Only one patient's data exists per session
    2. New patient access clears any existing patient data
    3. All session isolation events are logged for audit
    4. Healthcare data privacy is maintained
    """
    
    def process_request(self, request):
        """
        Process incoming request to enforce patient session isolation
        """
        # Only process if user has a session
        if not hasattr(request, 'session') or not request.session.session_key:
            return None
            
        # Extract patient ID from the URL if present
        current_patient_id = self._extract_patient_id_from_path(request.path)
        
        if current_patient_id:
            # Enforce session isolation for this patient
            self._enforce_session_isolation(request.session, current_patient_id)
        
        return None
    
    def _extract_patient_id_from_path(self, path):
        """
        Extract patient ID from URL path
        
        Supports patterns like:
        - /patients/cda/2165116870/L3/
        - /patients/match/2165116870/
        - /patients/data/2165116870/
        """
        import re
        
        # Pattern to match patient ID in URLs
        patient_patterns = [
            r'/patients/cda/(\d+)/',
            r'/patients/match/(\d+)/',
            r'/patients/data/(\d+)/',
            r'/patients/(\d+)/',
        ]
        
        for pattern in patient_patterns:
            match = re.search(pattern, path)
            if match:
                return match.group(1)
        
        return None
    
    def _enforce_session_isolation(self, session, current_patient_id):
        """
        Enforce patient session isolation
        
        This method:
        1. Identifies all existing patient data in session
        2. Checks if it conflicts with current patient
        3. Clears conflicting data to prevent mixing
        4. Logs all isolation actions for audit
        """
        session_data = dict(session)
        patient_keys = []
        existing_patient_ids = set()
        
        # Find all patient-related keys in session
        for key in session_data.keys():
            if any(prefix in key for prefix in [
                'patient_match_', 'patient_extended_data_', 
                'patient_', 'fhir_', 'cda_', 'healthcare_'
            ]):
                patient_keys.append(key)
                
                # Extract patient ID from key
                if 'patient_match_' in key:
                    patient_id = key.replace('patient_match_', '')
                    existing_patient_ids.add(patient_id)
                elif 'patient_extended_data_' in key:
                    patient_id = key.replace('patient_extended_data_', '')
                    existing_patient_ids.add(patient_id)
        
        # Check if we need to clear conflicting data
        conflicting_patients = existing_patient_ids - {current_patient_id}
        
        if conflicting_patients:
            # GDPR CRITICAL: Clear all conflicting patient data
            cleared_keys = []
            
            for key in list(session.keys()):
                # Clear any data that doesn't belong to current patient
                should_clear = False
                
                if any(prefix in key for prefix in [
                    'patient_match_', 'patient_extended_data_', 
                    'patient_', 'fhir_', 'cda_', 'healthcare_'
                ]):
                    # Check if this key belongs to current patient
                    if f'_{current_patient_id}' not in key and key != f'patient_match_{current_patient_id}':
                        should_clear = True
                    
                    # Also clear general patient keys that might cause confusion
                    if key in ['patient_id', 'patient_last_activity', 'cda_xml']:
                        should_clear = True
                
                if should_clear:
                    del session[key]
                    cleared_keys.append(key)
            
            # Save the cleaned session
            session.save()
            
            # Log the isolation action for audit trail
            logger.warning(
                f"GDPR Session Isolation: Cleared conflicting patient data. "
                f"Current patient: {current_patient_id}, "
                f"Conflicting patients: {list(conflicting_patients)}, "
                f"Cleared keys: {cleared_keys}, "
                f"Session: {session.session_key[:10]}..."
            )
            
            # Log for security audit
            logger.info(
                f"Patient session isolation enforced: "
                f"patient_id={current_patient_id}, "
                f"session_key={session.session_key[:10]}..., "
                f"cleared_patients={list(conflicting_patients)}"
            )
    
    def process_response(self, request, response):
        """
        Log session state after response for audit trail
        """
        if hasattr(request, 'session') and request.session.session_key:
            current_patient_id = self._extract_patient_id_from_path(request.path)
            
            if current_patient_id:
                # Count patient data in session after processing
                patient_count = 0
                session_data = dict(request.session)
                
                for key in session_data.keys():
                    if 'patient_match_' in key:
                        patient_count += 1
                
                # Log session state for audit
                if patient_count > 1:
                    logger.error(
                        f"GDPR VIOLATION: Multiple patients in session after processing! "
                        f"Patient count: {patient_count}, "
                        f"Current patient: {current_patient_id}, "
                        f"Session: {request.session.session_key[:10]}..."
                    )
                elif patient_count == 1:
                    logger.debug(
                        f"Session isolation verified: "
                        f"patient_id={current_patient_id}, "
                        f"session_key={request.session.session_key[:10]}..."
                    )
        
        return response