#!/usr/bin/env python3
"""
Update current FHIR session with enhanced parsing to fix missing contact data
"""
import os
import sys
import django

# Add Django project to path
sys.path.append('/c/Users/Duncan/VS_Code_Projects/django_ncp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.contrib.sessions.models import Session
from django.utils import timezone
from patient_data.services.fhir_agent_service import FHIRAgentService
from patient_data.services.fhir_bundle_parser import FHIRBundleParser
import json

def update_fhir_session_with_enhanced_parsing():
    """Update current FHIR session with enhanced contact data extraction"""
    
    print("=== UPDATING FHIR SESSION WITH ENHANCED PARSING ===")
    print()
    
    # Find the current FHIR session
    patient_id = "2891165241"
    current_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    
    session_to_update = None
    session_key = f"patient_match_{patient_id}"
    
    for session in current_sessions:
        try:
            session_data = session.get_decoded()
            if session_key in session_data:
                session_to_update = session
                break
        except:
            continue
    
    if not session_to_update:
        print(f"❌ No session found for patient {patient_id}")
        return
    
    print(f"🎯 Found session to update: {session_to_update.session_key}")
    
    # Get current session data
    session_data = session_to_update.get_decoded()
    current_patient_data = session_data[session_key]
    
    # Extract FHIR bundle
    fhir_bundle = current_patient_data.get('fhir_bundle')
    if not fhir_bundle:
        print(f"❌ No FHIR bundle found in session")
        return
    
    print(f"✅ Found FHIR bundle in session")
    
    # Use enhanced FHIR parsing
    print(f"🔄 Processing FHIR bundle with enhanced parser...")
    
    # Method 1: Use FHIRBundleParser directly
    parser = FHIRBundleParser()
    try:
        enhanced_result = parser.parse_patient_summary_bundle(fhir_bundle)
        
        if not enhanced_result.get('success', False):
            print(f"❌ Enhanced parsing failed: {enhanced_result.get('error')}")
            return
        
        print(f"✅ Enhanced parsing successful!")
        
        # Extract the enhanced data
        patient_identity = enhanced_result.get('patient_identity', {})
        contact_data = enhanced_result.get('contact_data', {})
        administrative_data = enhanced_result.get('administrative_data', {})
        healthcare_data = enhanced_result.get('healthcare_data', {})
        
        print(f"📋 Enhanced Data Extracted:")
        print(f"  - Patient Identity: {patient_identity.get('full_name', 'Unknown')}")
        print(f"  - Contact Addresses: {len(contact_data.get('addresses', []))}")
        print(f"  - Contact Telecoms: {len(contact_data.get('telecoms', []))}")
        print(f"  - Administrative Data: {bool(administrative_data)}")
        print(f"  - Healthcare Data: {bool(healthcare_data)}")
        
        # Update the session data with enhanced information
        current_patient_data.update({
            'patient_identity': patient_identity,
            'contact_data': contact_data,
            'administrative_data': administrative_data,
            'healthcare_data': healthcare_data,
            'patient_extended_data': {
                'patient_identity': patient_identity,
                'contact_data': contact_data,
                'administrative_data': administrative_data,
                'healthcare_data': healthcare_data,
            },
            'enhanced_parsing_applied': True,
            'enhanced_parsing_timestamp': timezone.now().isoformat(),
        })
        
        # Update patient_data with enhanced information
        if contact_data.get('addresses'):
            addr = contact_data['addresses'][0]
            current_patient_data['patient_data'].update({
                'address': addr.get('full_address', ''),
                'city': addr.get('city', ''),
                'postal_code': addr.get('postal_code', ''),
                'country': addr.get('country', ''),
            })
        
        # Save updated session using direct session modification
        from django.contrib.sessions.backends.db import SessionStore
        
        # Create a new session store with the existing session key
        store = SessionStore(session_key=session_to_update.session_key)
        
        # Load existing data
        store.load()
        
        # Update with our enhanced data
        store[session_key] = current_patient_data
        
        # Force save
        store.save(must_create=False)
        
        print(f"✅ Session updated with enhanced FHIR parsing!")
        
        # Verify the update
        print(f"\n🔍 Verification:")
        updated_session_data = session_to_update.get_decoded()
        updated_patient_data = updated_session_data[session_key]
        
        if 'contact_data' in updated_patient_data:
            contact = updated_patient_data['contact_data']
            if contact.get('addresses'):
                addr = contact['addresses'][0]
                print(f"  ✅ Contact data saved successfully")
                print(f"     Full Address: {addr.get('full_address', 'N/A')}")
                print(f"     City: {addr.get('city', 'N/A')}")
                print(f"     Postal Code: {addr.get('postal_code', 'N/A')}")
                print(f"     Country: {addr.get('country', 'N/A')}")
            else:
                print(f"  ❌ No addresses in saved contact data")
        else:
            print(f"  ❌ No contact_data in updated session")
        
        if 'patient_identity' in updated_patient_data:
            identity = updated_patient_data['patient_identity']
            print(f"  ✅ Patient identity saved: {identity.get('full_name', 'Unknown')}")
        
        print(f"\n🎉 Update complete! The UI should now show complete patient data.")
        
    except Exception as e:
        print(f"❌ Error during enhanced parsing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_fhir_session_with_enhanced_parsing()