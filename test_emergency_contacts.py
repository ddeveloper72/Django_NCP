#!/usr/bin/env python3
"""Test emergency contact extraction from FHIR bundle with RelatedPerson resources"""

import json
import os
import django
import sys

# Django setup
sys.path.append('c:/Users/Duncan/VS_Code_Projects/django_ncp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from patient_data.services.fhir_bundle_parser import FHIRBundleParser

def test_emergency_contacts():
    """Test emergency contact extraction from updated FHIR bundle"""
    
    bundle_path = 'test_data/eu_member_states/IE/combined_fhir_bundle_ULTRA_SAFE.json'
    
    try:
        with open(bundle_path, 'r', encoding='utf-8') as f:
            bundle_data = json.load(f)
        
        print(f"✅ Successfully loaded FHIR bundle with {len(bundle_data.get('entry', []))} resources")
        
        # Initialize parser
        parser = FHIRBundleParser()
        
        # Parse the bundle
        parsed_data = parser.parse_patient_summary_bundle(bundle_data)
        
        print(f"\n📊 Parsed FHIR Bundle Summary:")
        print(f"   - Patient ID: {parsed_data.get('patient', {}).get('id', 'N/A')}")
        print(f"   - Patient Name: {parsed_data.get('patient', {}).get('name', {}).get('full_name', 'N/A')}")
        
        # Check for emergency contacts
        emergency_contacts = parsed_data.get('emergency_contacts', [])
        print(f"\n👥 Emergency Contacts Found: {len(emergency_contacts)}")
        
        for i, contact in enumerate(emergency_contacts, 1):
            print(f"\n   Contact #{i}:")
            print(f"   - Name: {contact.get('name', {}).get('full_name', 'N/A')}")
            print(f"   - ID: {contact.get('id', 'N/A')}")
            
            relationships = contact.get('relationship', [])
            if relationships:
                for rel in relationships:
                    if rel.get('display'):
                        print(f"   - Relationship: {rel.get('display', 'N/A')}")
                    elif rel.get('text'):
                        print(f"   - Relationship: {rel.get('text', 'N/A')}")
            
            telecoms = contact.get('telecom', [])
            for telecom in telecoms:
                print(f"   - {telecom.get('system', 'phone').title()}: {telecom.get('value', 'N/A')}")
            
            addresses = contact.get('address', [])
            for address in addresses:
                print(f"   - Address: {address.get('full_address', 'N/A')}")
        
        # Check which resource types were found
        print(f"\n🔍 Resource Analysis:")
        related_person_resources = [
            entry['resource'] for entry in bundle_data.get('entry', [])
            if entry.get('resource', {}).get('resourceType') == 'RelatedPerson'
        ]
        print(f"   - RelatedPerson resources found: {len(related_person_resources)}")
        
        if related_person_resources:
            for rp in related_person_resources:
                name = rp.get('name', [{}])[0] if rp.get('name') else {}
                full_name = name.get('text', '') or f"{' '.join(name.get('given', []))} {name.get('family', '')}".strip()
                print(f"     • {full_name} (ID: {rp.get('id', 'N/A')})")
        
        return parsed_data
        
    except FileNotFoundError:
        print(f"❌ FHIR bundle file not found: {bundle_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        return None
    except Exception as e:
        print(f"❌ Error testing emergency contacts: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🧪 Testing Emergency Contact Extraction from FHIR Bundle")
    print("=" * 60)
    
    parsed_data = test_emergency_contacts()
    
    if parsed_data:
        print("\n✅ Emergency contact extraction test completed successfully!")
    else:
        print("\n❌ Emergency contact extraction test failed!")