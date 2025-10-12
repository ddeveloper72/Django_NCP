#!/usr/bin/env python3
"""Create complete patient session data with all required fields"""

import os
import django
import sys
import json

# Django setup
sys.path.append('c:/Users/Duncan/VS_Code_Projects/django_ncp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.contrib.sessions.backends.db import SessionStore
from django.utils import timezone

def create_complete_patient_session():
    """Create complete patient session with all required fields for the view"""
    
    bundle_path = 'test_data/eu_member_states/IE/combined_fhir_bundle_ULTRA_SAFE.json'
    session_id = '1902395951'
    
    try:
        # Load enhanced bundle
        with open(bundle_path, 'r', encoding='utf-8') as f:
            enhanced_bundle = json.load(f)
        
        print(f"✅ Loaded enhanced FHIR bundle with {len(enhanced_bundle.get('entry', []))} resources")
        
        # Extract patient info from FHIR bundle
        patient_resource = None
        for entry in enhanced_bundle.get('entry', []):
            if entry.get('resource', {}).get('resourceType') == 'Patient':
                patient_resource = entry['resource']
                break
        
        if not patient_resource:
            print("❌ No Patient resource found in bundle")
            return None
        
        # Extract patient details
        names = patient_resource.get('name', [])
        patient_name = "Unknown Patient"
        given_name = ""
        family_name = ""
        
        if names:
            name = names[0]
            given_names = name.get('given', [])
            family_name = name.get('family', '')
            given_name = ' '.join(given_names)
            patient_name = f"{given_name} {family_name}".strip()
        
        # Extract birth date
        birth_date = patient_resource.get('birthDate', '')
        
        # Extract identifiers
        identifiers = patient_resource.get('identifier', [])
        government_id = None
        for identifier in identifiers:
            if identifier.get('use') == 'official':
                government_id = identifier.get('value', '')
                break
        
        if not government_id and identifiers:
            government_id = identifiers[0].get('value', '')
        
        # Create complete session data structure
        new_session = SessionStore()
        
        complete_patient_data = {
            'fhir_bundle': enhanced_bundle,
            'patient_identity': {  # Changed from patient_info to patient_identity
                'given_name': given_name,
                'family_name': family_name,
                'full_name': patient_name,
                'birth_date': birth_date,
                'government_id': government_id or session_id,
                'patient_id': patient_resource.get('id', session_id),
                'identifiers': identifiers,
                'source_country': 'IE',
                'data_source': 'FHIR_Enhanced'
            },
            'patient_data': {  # Also add patient_data for compatibility
                'given_name': given_name,
                'family_name': family_name,
                'full_name': patient_name,
                'birth_date': birth_date,
                'government_id': government_id or session_id,
                'patient_id': patient_resource.get('id', session_id),
                'identifiers': identifiers,
                'source_country': 'IE',
                'data_source': 'FHIR_Enhanced'
            },
            'patient_id': session_id,
            'data_source': 'FHIR_Enhanced',
            'has_emergency_contacts': True,
            'emergency_contact_count': 1,
            'timestamp': timezone.now().isoformat(),
            # Additional fields that the view might expect
            'search_results': {
                'patient_found': True,
                'documents_available': True,
                'last_updated': timezone.now().isoformat()
            }
        }
        
        new_session[f'patient_match_{session_id}'] = complete_patient_data
        new_session.save()
        session_key = new_session.session_key
        
        print(f"\n✅ Created complete patient session: {session_key}")
        print(f"   - Patient Name: {patient_name}")
        print(f"   - Birth Date: {birth_date}")
        print(f"   - Government ID: {government_id}")
        print(f"   - FHIR Resources: {len(enhanced_bundle.get('entry', []))}")
        print(f"   - Emergency Contacts: Available")
        
        return session_key
        
    except Exception as e:
        print(f"❌ Error creating complete session: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🆕 Creating Complete Patient Session with Emergency Contacts")
    print("=" * 65)
    
    session_key = create_complete_patient_session()
    
    if session_key:
        print(f"\n✅ Complete patient session created successfully!")
        print(f"📋 Session Key: {session_key}")
        print(f"🎯 Ready for patient view testing!")
        print(f"\n🌐 Test URL: /patients/cda/1902395951/")
    else:
        print(f"\n❌ Complete patient session creation failed!")