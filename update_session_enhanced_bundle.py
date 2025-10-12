#!/usr/bin/env python3
"""Update existing session with enhanced FHIR bundle containing emergency contacts"""

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

def update_session_with_enhanced_bundle():
    """Update the existing session with our enhanced FHIR bundle"""
    
    session_id = '1902395951'
    bundle_path = 'test_data/eu_member_states/IE/combined_fhir_bundle_ULTRA_SAFE.json'
    
    try:
        # Load enhanced bundle
        with open(bundle_path, 'r', encoding='utf-8') as f:
            enhanced_bundle = json.load(f)
        
        print(f"✅ Loaded enhanced FHIR bundle with {len(enhanced_bundle.get('entry', []))} resources")
        
        # Check for RelatedPerson resource
        related_persons = [
            entry['resource'] for entry in enhanced_bundle.get('entry', [])
            if entry.get('resource', {}).get('resourceType') == 'RelatedPerson'
        ]
        print(f"👥 RelatedPerson resources in enhanced bundle: {len(related_persons)}")
        for rp in related_persons:
            name = rp.get('name', [{}])[0] if rp.get('name') else {}
            full_name = name.get('text', '') or f"{' '.join(name.get('given', []))} {name.get('family', '')}".strip()
            print(f"   - {full_name}")
        
        # Find all Django sessions that might contain our patient data
        django_sessions = DjangoSession.objects.all()
        
        updated_sessions = []
        for ds in django_sessions:
            try:
                session_data = ds.get_decoded()
                if f'patient_match_{session_id}' in session_data:
                    print(f"\n📋 Found session with patient data: {ds.session_key}")
                    
                    # Update with enhanced FHIR bundle
                    patient_data = session_data[f'patient_match_{session_id}']
                    if 'fhir_bundle' in patient_data:
                        old_count = len(patient_data['fhir_bundle'].get('entry', []))
                        patient_data['fhir_bundle'] = enhanced_bundle
                        new_count = len(enhanced_bundle.get('entry', []))
                        
                        print(f"   - Updated FHIR bundle: {old_count} → {new_count} resources")
                        
                        # Save the updated session
                        session_data[f'patient_match_{session_id}'] = patient_data
                        ds.session_data = DjangoSession.objects.encode(session_data)
                        ds.save()
                        
                        updated_sessions.append(ds.session_key)
                        print(f"   ✅ Session {ds.session_key} updated successfully")
                    
                elif 'fhir_data' in session_data:
                    print(f"\n📋 Found session with direct FHIR data: {ds.session_key}")
                    
                    old_count = len(session_data['fhir_data'].get('entry', []))
                    session_data['fhir_data'] = enhanced_bundle
                    new_count = len(enhanced_bundle.get('entry', []))
                    
                    print(f"   - Updated direct FHIR data: {old_count} → {new_count} resources")
                    
                    # Save the updated session
                    ds.session_data = DjangoSession.objects.encode(session_data)
                    ds.save()
                    
                    updated_sessions.append(ds.session_key)
                    print(f"   ✅ Session {ds.session_key} updated successfully")
                    
            except Exception as e:
                # Skip invalid sessions
                continue
        
        print(f"\n🎯 Summary:")
        print(f"   - Total sessions updated: {len(updated_sessions)}")
        print(f"   - Enhanced bundle resources: {len(enhanced_bundle.get('entry', []))}")
        print(f"   - Emergency contacts included: {len(related_persons)}")
        
        if updated_sessions:
            print(f"\n✅ Sessions updated successfully!")
            print(f"   Patient session {session_id} now has emergency contacts")
            return True
        else:
            print(f"\n❌ No sessions found to update")
            return False
            
    except Exception as e:
        print(f"❌ Error updating session: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔄 Updating Patient Session with Enhanced FHIR Bundle")
    print("=" * 60)
    
    success = update_session_with_enhanced_bundle()
    
    if success:
        print(f"\n✅ Session update completed!")
        print(f"🎯 Emergency contacts are now available in patient view")
    else:
        print(f"\n❌ Session update failed!")