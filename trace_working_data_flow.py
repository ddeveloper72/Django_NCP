#!/usr/bin/env python3
"""
Trace Working Data Flow - Patient Demographics
Trace how Patrick Murphy's name, address, and phone successfully display in the UI
to understand the working data mapping pattern.
"""

import os
import sys
import json
import django

# Add the project directory to Python path
sys.path.append(r'C:\Users\Duncan\VS_Code_Projects\django_ncp')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from patient_data.services.fhir_agent_service import FHIRAgentService

def trace_working_data_flow():
    """Trace the working patient demographics data flow"""
    
    session_id = "1902395951"
    
    print(f"🔍 [TRACE] Working Data Flow Analysis - Patient Demographics")
    print(f"Session: {session_id} (Patrick Murphy)")
    print("=" * 80)
    
    # Get the raw FHIR bundle to see the source data
    fhir_service = FHIRAgentService()
    fhir_bundle_content = fhir_service.get_fhir_bundle_from_session(session_id)
    
    print("📋 STEP 1: Raw FHIR Bundle Patient Resource")
    print("=" * 50)
    
    # Find the Patient resource in the bundle
    patient_resource = None
    related_person_resource = None
    
    if isinstance(fhir_bundle_content, dict):
        for entry in fhir_bundle_content.get('entry', []):
            resource = entry.get('resource', {})
            if resource.get('resourceType') == 'Patient':
                patient_resource = resource
            elif resource.get('resourceType') == 'RelatedPerson':
                related_person_resource = resource
    
    if patient_resource:
        print("✅ Patient Resource Found:")
        print(f"   ID: {patient_resource.get('id')}")
        
        # Extract name from raw FHIR
        names = patient_resource.get('name', [])
        if names:
            name = names[0]
            print(f"   Raw Name: {json.dumps(name, indent=2)}")
        
        # Extract telecom from raw FHIR
        telecoms = patient_resource.get('telecom', [])
        print(f"   Raw Telecoms: {json.dumps(telecoms, indent=2)}")
        
        # Extract address from raw FHIR
        addresses = patient_resource.get('address', [])
        print(f"   Raw Addresses: {json.dumps(addresses, indent=2)}")
    
    if related_person_resource:
        print(f"\n📞 RelatedPerson Resource Found:")
        print(f"   ID: {related_person_resource.get('id')}")
        
        # Extract name from raw FHIR RelatedPerson
        names = related_person_resource.get('name', [])
        if names:
            name = names[0]
            print(f"   Raw Name: {json.dumps(name, indent=2)}")
        
        # Extract telecom from raw FHIR RelatedPerson
        telecoms = related_person_resource.get('telecom', [])
        print(f"   Raw Telecoms: {json.dumps(telecoms, indent=2)}")
    
    print(f"\n📊 STEP 2: FHIR Agent Processing")
    print("=" * 50)
    
    # Get processed FHIR data
    fhir_data = fhir_service.extract_patient_context_data(fhir_bundle_content, session_id)
    
    # Check patient identity (what displays in UI)
    patient_identity = fhir_data.get('patient_identity', {})
    print("✅ Processed Patient Identity:")
    print(f"   Given Name: '{patient_identity.get('given_name')}'")
    print(f"   Family Name: '{patient_identity.get('family_name')}'")
    print(f"   Patient ID: '{patient_identity.get('patient_id')}'")
    print(f"   Full Structure: {json.dumps(patient_identity, indent=2, default=str)}")
    
    # Check contact data (what should contain emergency contacts)
    contact_data = fhir_data.get('contact_data', {})
    print(f"\n📞 Processed Contact Data:")
    print(f"   Keys: {list(contact_data.keys())}")
    
    # Patient contact info (what displays in UI)
    patient_telecoms = contact_data.get('telecoms', [])
    patient_addresses = contact_data.get('addresses', [])
    
    print(f"   Patient Telecoms: {len(patient_telecoms)} items")
    for i, telecom in enumerate(patient_telecoms):
        print(f"      Telecom {i+1}: {json.dumps(telecom, indent=2)}")
    
    print(f"   Patient Addresses: {len(patient_addresses)} items")
    for i, address in enumerate(patient_addresses):
        print(f"      Address {i+1}: {json.dumps(address, indent=2)}")
    
    # Emergency contacts (what's NOT displaying in UI)
    emergency_contacts = contact_data.get('emergency_contacts', [])
    print(f"   Emergency Contacts: {len(emergency_contacts)} items")
    for i, contact in enumerate(emergency_contacts):
        print(f"      Emergency Contact {i+1}: {json.dumps(contact, indent=2, default=str)}")
    
    print(f"\n🎯 STEP 3: Template Data Structure")
    print("=" * 50)
    
    # Show what the template receives
    print("✅ What Template Gets for Patient Demographics:")
    print(f"   patient_identity.given_name: '{patient_identity.get('given_name')}'")
    print(f"   patient_identity.family_name: '{patient_identity.get('family_name')}'")
    print(f"   contact_data.telecoms: {len(contact_data.get('telecoms', []))} items")
    print(f"   contact_data.addresses: {len(contact_data.get('addresses', []))} items")
    
    print(f"\n❌ What Template Should Get for Emergency Contacts:")
    print(f"   contact_data.emergency_contacts: {len(contact_data.get('emergency_contacts', []))} items")
    
    # Check if the mapping we added is working
    administrative_data = fhir_data.get('administrative_data', {})
    print(f"\n🔧 Administrative Data Mapping:")
    print(f"   administrative_data.guardian: {bool(administrative_data.get('guardian'))}")
    print(f"   administrative_data.other_contacts: {len(administrative_data.get('other_contacts', []))}")
    
    print(f"\n💡 ANALYSIS:")
    print(f"   Patient demographics work because they go: FHIR Patient → patient_identity/contact_data → Template")
    print(f"   Emergency contacts should work: FHIR RelatedPerson → contact_data.emergency_contacts → administrative_data → Template")
    print(f"   Issue might be: The view mapping runs AFTER FHIR processing, not during it!")

if __name__ == "__main__":
    trace_working_data_flow()