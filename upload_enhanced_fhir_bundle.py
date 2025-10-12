#!/usr/bin/env python3
"""Upload enhanced FHIR bundle with emergency contacts to HAPI server"""

import json
import requests
import os
import django
import sys

# Django setup
sys.path.append('c:/Users/Duncan/VS_Code_Projects/django_ncp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from patient_data.models import PatientSession
from django.utils import timezone

def upload_enhanced_bundle():
    """Upload the FHIR bundle with emergency contacts to HAPI server"""
    
    bundle_path = 'test_data/eu_member_states/IE/combined_fhir_bundle_ULTRA_SAFE.json'
    hapi_url = 'http://localhost:8080/fhir'
    
    try:
        # Load the enhanced bundle
        with open(bundle_path, 'r', encoding='utf-8') as f:
            bundle_data = json.load(f)
        
        print(f"✅ Loaded enhanced FHIR bundle with {len(bundle_data.get('entry', []))} resources")
        
        # Check for RelatedPerson resource
        related_persons = [
            entry['resource'] for entry in bundle_data.get('entry', [])
            if entry.get('resource', {}).get('resourceType') == 'RelatedPerson'
        ]
        
        print(f"👥 Emergency contacts in bundle: {len(related_persons)}")
        for rp in related_persons:
            name = rp.get('name', [{}])[0] if rp.get('name') else {}
            full_name = name.get('text', '') or f"{' '.join(name.get('given', []))} {name.get('family', '')}".strip()
            print(f"   - {full_name}")
        
        # Upload to HAPI server
        print(f"\n🚀 Uploading to HAPI FHIR server: {hapi_url}")
        
        headers = {
            'Content-Type': 'application/fhir+json',
            'Accept': 'application/fhir+json'
        }
        
        response = requests.post(f"{hapi_url}/Bundle", json=bundle_data, headers=headers)
        
        if response.status_code in [200, 201]:
            response_data = response.json()
            bundle_id = response_data.get('id', 'unknown')
            print(f"✅ Successfully uploaded bundle to HAPI server!")
            print(f"   - Bundle ID: {bundle_id}")
            print(f"   - Location: {response.headers.get('Location', 'N/A')}")
            
            # Create a new patient session with emergency contacts
            create_patient_session_with_contacts(bundle_id, bundle_data)
            
            return bundle_id
        else:
            print(f"❌ Failed to upload bundle: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except FileNotFoundError:
        print(f"❌ Bundle file not found: {bundle_path}")
        return None
    except requests.RequestException as e:
        print(f"❌ Network error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error uploading bundle: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_patient_session_with_contacts(bundle_id: str, bundle_data: dict):
    """Create a new patient session with emergency contact data"""
    
    try:
        # Extract patient info from bundle
        patient_resource = None
        for entry in bundle_data.get('entry', []):
            if entry.get('resource', {}).get('resourceType') == 'Patient':
                patient_resource = entry['resource']
                break
        
        if not patient_resource:
            print("❌ No Patient resource found in bundle")
            return
        
        # Get patient name
        names = patient_resource.get('name', [])
        patient_name = "Unknown Patient"
        if names:
            name = names[0]
            given = ' '.join(name.get('given', []))
            family = name.get('family', '')
            patient_name = f"{given} {family}".strip()
        
        # Create session
        session = PatientSession.objects.create(
            session_id=f"enhanced_fhir_{bundle_id}",
            patient_id=patient_resource.get('id', 'unknown'),
            origin_country_code='IE',
            data_type='FHIR',
            fhir_data=json.dumps(bundle_data),
            is_active=True,
            created_at=timezone.now()
        )
        
        print(f"\n📋 Created new patient session:")
        print(f"   - Session ID: {session.session_id}")
        print(f"   - Patient: {patient_name}")
        print(f"   - Data Type: FHIR with Emergency Contacts")
        print(f"   - Access URL: /ehealth-portal/patient/{session.session_id}/")
        
        return session
        
    except Exception as e:
        print(f"❌ Error creating patient session: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🏥 Uploading Enhanced FHIR Bundle with Emergency Contacts")
    print("=" * 60)
    
    bundle_id = upload_enhanced_bundle()
    
    if bundle_id:
        print(f"\n✅ Enhanced FHIR bundle upload completed successfully!")
        print(f"📋 Bundle ID: {bundle_id}")
        print(f"👥 Emergency contacts now available in FHIR Patient Summary")
    else:
        print("\n❌ Enhanced FHIR bundle upload failed!")