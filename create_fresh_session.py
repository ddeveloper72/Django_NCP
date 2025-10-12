#!/usr/bin/env python3
"""Force clear all sessions and create fresh session with enhanced FHIR bundle"""

import os
import django
import sys
import json

# Django setup
sys.path.append('c:/Users/Duncan/VS_Code_Projects/django_ncp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.contrib.sessions.models import Session as DjangoSession
from patient_data.models import PatientSession
from django.utils import timezone

def create_fresh_session_with_emergency_contacts():
    """Create a completely fresh session with enhanced FHIR bundle"""
    
    bundle_path = 'test_data/eu_member_states/IE/combined_fhir_bundle_ULTRA_SAFE.json'
    
    try:
        # Load enhanced bundle
        with open(bundle_path, 'r', encoding='utf-8') as f:
            enhanced_bundle = json.load(f)
        
        print(f"✅ Loaded enhanced FHIR bundle with {len(enhanced_bundle.get('entry', []))} resources")
        
        # Verify RelatedPerson is present
        related_persons = [
            entry['resource'] for entry in enhanced_bundle.get('entry', [])
            if entry.get('resource', {}).get('resourceType') == 'RelatedPerson'
        ]
        print(f"👥 RelatedPerson resources verified: {len(related_persons)}")
        for rp in related_persons:
            name = rp.get('name', [{}])[0] if rp.get('name') else {}
            full_name = name.get('text', '') or f"{' '.join(name.get('given', []))} {name.get('family', '')}".strip()
            print(f"   - {full_name}")
        
        # Clear all existing sessions for this patient
        session_id = '1902395951'
        print(f"\n🧹 Clearing existing sessions for patient {session_id}...")
        
        django_sessions = DjangoSession.objects.all()
        cleared_count = 0
        for ds in django_sessions:
            try:
                session_data = ds.get_decoded()
                if f'patient_match_{session_id}' in session_data:
                    ds.delete()
                    cleared_count += 1
                    print(f"   ✅ Cleared session: {ds.session_key}")
            except:
                continue
        
        print(f"   - Total sessions cleared: {cleared_count}")
        
        # Create new Django session with enhanced bundle
        from django.contrib.sessions.backends.db import SessionStore
        
        new_session = SessionStore()
        new_session[f'patient_match_{session_id}'] = {
            'fhir_bundle': enhanced_bundle,
            'patient_id': session_id,
            'data_source': 'FHIR_Enhanced',
            'has_emergency_contacts': True,
            'emergency_contact_count': len(related_persons),
            'timestamp': timezone.now().isoformat()
        }
        new_session.save()
        session_key = new_session.session_key
        
        print(f"\n✅ Created fresh session: {session_key}")
        print(f"   - FHIR bundle resources: {len(enhanced_bundle.get('entry', []))}")
        print(f"   - Emergency contacts: {len(related_persons)}")
        print(f"   - Data source: FHIR_Enhanced")
        
        # Test the FHIR parser directly on this bundle
        print(f"\n🧪 Testing FHIR parser on enhanced bundle...")
        from patient_data.services.fhir_bundle_parser import FHIRBundleParser
        
        parser = FHIRBundleParser()
        parsed_data = parser.parse_patient_summary_bundle(enhanced_bundle)
        
        print(f"   - Parsed successfully: {parsed_data.get('success', False)}")
        print(f"   - Sections: {parsed_data.get('sections_count', 0)}")
        print(f"   - Resources: {parsed_data.get('bundle_metadata', {}).get('resource_count', 0)}")
        
        emergency_contacts = parsed_data.get('emergency_contacts', [])
        print(f"   - Emergency contacts extracted: {len(emergency_contacts)}")
        
        contact_data = parsed_data.get('contact_data', {})
        contact_emergency = contact_data.get('emergency_contacts', [])
        print(f"   - Emergency contacts in contact_data: {len(contact_emergency)}")
        
        if emergency_contacts:
            for contact in emergency_contacts:
                name = contact.get('name', {}).get('full_name', 'Unknown')
                print(f"     • {name}")
        
        return session_key
        
    except Exception as e:
        print(f"❌ Error creating fresh session: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🆕 Creating Fresh Session with Emergency Contacts")
    print("=" * 55)
    
    session_key = create_fresh_session_with_emergency_contacts()
    
    if session_key:
        print(f"\n✅ Fresh session created successfully!")
        print(f"📋 Session Key: {session_key}")
        print(f"🎯 Emergency contacts ready for testing!")
        print(f"\n🌐 Test URL: /patients/cda/1902395951/")
    else:
        print(f"\n❌ Fresh session creation failed!")