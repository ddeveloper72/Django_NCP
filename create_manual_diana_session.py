#!/usr/bin/env python3
"""
Manually create Diana session data
Create a proper session entry for Diana Ferreira's clinical data
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.contrib.sessions.backends.db import SessionStore
from patient_data.services import EUPatientSearchService, PatientCredentials
from patient_data.services.comprehensive_clinical_data_service import ComprehensiveClinicalDataService

def create_manual_diana_session():
    """Manually create Diana's session data"""
    
    print("🔧 CREATING MANUAL DIANA SESSION")
    print("=" * 50)
    
    # Create credentials for Diana
    credentials = PatientCredentials(
        country_code="PT",
        patient_id="2-1234-W7"
    )
    credentials.given_name = "Diana"
    credentials.family_name = "Ferreira"
    credentials.birth_date = "1982-05-08"
    
    # Get search results
    search_service = EUPatientSearchService()
    search_result = search_service.search_patient(credentials)
    
    if not search_result:
        print("❌ No search results found")
        return
    
    # Get first result
    first_result = search_result[0] if isinstance(search_result, list) else search_result
    print(f"✅ Found patient data")
    
    # Extract clinical data
    service = ComprehensiveClinicalDataService()
    clinical_arrays = service.get_clinical_arrays_for_display(first_result.cda_content)
    
    print(f"📊 Clinical data: {len(clinical_arrays.get('medications', []))} medications")
    
    # Create new session
    session = SessionStore()
    
    # Create session data structure
    session_data = {
        'patient_id': '2-1234-W7',
        'given_name': 'Diana',
        'family_name': 'Ferreira',
        'birth_date': '1982-05-08',
        'country_code': 'PT',
        'cda_content': first_result.cda_content,
        'clinical_arrays': clinical_arrays,
        'confidence_score': first_result.confidence_score,
        'file_path': first_result.file_path
    }
    
    # Save to session with the key format the view expects
    session_key = f"patient_match_2-1234-W7"
    session[session_key] = session_data
    session['patient_last_activity'] = '2-1234-W7'
    session.save()
    
    print(f"✅ Session created with key: {session_key}")
    print(f"📝 Session ID: {session.session_key}")
    print(f"🔗 URL: http://localhost:8000/patients/cda/2-1234-W7/L3/")
    
    # Verify session data
    retrieved_data = session[session_key]
    print(f"✅ Verification: {len(retrieved_data['clinical_arrays']['medications'])} medications in session")

if __name__ == "__main__":
    create_manual_diana_session()