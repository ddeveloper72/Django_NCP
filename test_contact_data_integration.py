#!/usr/bin/env python3
"""Test contact data extraction including emergency contacts"""

import json
import os
import django
import sys

# Django setup
sys.path.append('c:/Users/Duncan/VS_Code_Projects/django_ncp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from patient_data.services.fhir_bundle_parser import FHIRBundleParser

def test_contact_data_with_emergency_contacts():
    """Test contact data extraction includes emergency contacts"""
    
    bundle_path = 'test_data/eu_member_states/IE/combined_fhir_bundle_ULTRA_SAFE.json'
    
    try:
        with open(bundle_path, 'r', encoding='utf-8') as f:
            bundle_data = json.load(f)
        
        print(f"✅ Successfully loaded FHIR bundle with {len(bundle_data.get('entry', []))} resources")
        
        # Initialize parser
        parser = FHIRBundleParser()
        
        # Parse the bundle
        parsed_data = parser.parse_patient_summary_bundle(bundle_data)
        
        print(f"\n📋 Testing Contact Data Integration:")
        
        # Check contact_data structure
        contact_data = parsed_data.get('contact_data', {})
        print(f"   - Contact data available: {bool(contact_data)}")
        print(f"   - Contact data keys: {list(contact_data.keys())}")
        
        # Check for emergency contacts in contact_data
        emergency_contacts_in_contact_data = contact_data.get('emergency_contacts', [])
        print(f"   - Emergency contacts in contact_data: {len(emergency_contacts_in_contact_data)}")
        
        # Check general contacts (should include emergency contacts)
        general_contacts = contact_data.get('contacts', [])
        print(f"   - Total contacts (including emergency): {len(general_contacts)}")
        
        # Display emergency contacts from contact_data
        for i, contact in enumerate(emergency_contacts_in_contact_data, 1):
            print(f"\n   Emergency Contact #{i} (from contact_data):")
            print(f"     - Name: {contact.get('name', {}).get('full_name', 'N/A')}")
            
            relationships = contact.get('relationship', [])
            for rel in relationships:
                if rel.get('display'):
                    print(f"     - Relationship: {rel.get('display', 'N/A')}")
                elif rel.get('text'):
                    print(f"     - Relationship: {rel.get('text', 'N/A')}")
            
            telecoms = contact.get('telecom', [])
            for telecom in telecoms:
                print(f"     - {telecom.get('system', 'phone').title()}: {telecom.get('value', 'N/A')}")
            
            addresses = contact.get('address', [])
            for address in addresses:
                print(f"     - Address: {address.get('full_address', 'N/A')}")
        
        # Check if emergency contacts are also in general contacts
        emergency_in_general = [c for c in general_contacts if c.get('type') == 'emergency_contact']
        print(f"\n   - Emergency contacts in general contacts list: {len(emergency_in_general)}")
        
        # Test administrative data as well
        administrative_data = parsed_data.get('administrative_data', {})
        admin_guardian = administrative_data.get('guardian')
        print(f"\n🔍 Administrative Data:")
        print(f"   - Guardian data available: {bool(admin_guardian)}")
        if admin_guardian:
            print(f"   - Guardian name: {admin_guardian.get('full_name', 'N/A')}")
        
        # Check extended data structure
        patient_extended_data = parsed_data.get('patient_extended_data', {})
        extended_emergency = patient_extended_data.get('emergency_contacts', [])
        print(f"\n🏥 Extended Patient Data:")
        print(f"   - Emergency contacts in extended data: {len(extended_emergency)}")
        
        return parsed_data
        
    except Exception as e:
        print(f"❌ Error testing contact data: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🧪 Testing Contact Data with Emergency Contacts Integration")
    print("=" * 65)
    
    parsed_data = test_contact_data_with_emergency_contacts()
    
    if parsed_data:
        print("\n✅ Contact data integration test completed successfully!")
    else:
        print("\n❌ Contact data integration test failed!")