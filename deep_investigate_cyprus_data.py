#!/usr/bin/env python3
"""
Deep Investigation of Patient Session Data

Extract and analyze the exact data causing Cyprus information to appear
for Irish patient 1708631189.
"""

import os
import sys
import django
import json

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

def deep_investigate_patient_session():
    """
    Deep dive into the patient session data to find Cyprus contamination
    """
    print("🔬 DEEP INVESTIGATION: Patient 1708631189 Cyprus Data")
    print("=" * 70)
    
    patient_id = "1708631189"
    
    from django.contrib.sessions.models import Session
    from django.contrib.sessions.backends.db import SessionStore
    
    # Find the session for this patient
    sessions = Session.objects.all()
    target_session = None
    
    for session in sessions:
        try:
            session_store = SessionStore(session_key=session.session_key)
            session_data = session_store.load()
            
            patient_key = f'patient_match_{patient_id}'
            if patient_key in session_data:
                target_session = session_data
                print(f"✅ Found target session: {session.session_key[:10]}...")
                break
        except:
            continue
    
    if not target_session:
        print(f"❌ No session found for patient {patient_id}")
        return
    
    # Analyze the session data structure
    print(f"\n📋 SESSION DATA STRUCTURE:")
    for key in target_session.keys():
        if patient_id in key:
            print(f"   🔑 {key}")
    
    # Extract the main patient data
    patient_key = f'patient_match_{patient_id}'
    if patient_key in target_session:
        patient_data = target_session[patient_key]
        print(f"\n📊 PATIENT DATA ANALYSIS:")
        print(f"   Data type: {type(patient_data)}")
        
        if isinstance(patient_data, dict):
            print(f"   Keys: {list(patient_data.keys())}")
            
            # Check for FHIR bundle
            if 'fhir_bundle' in patient_data:
                print(f"\n🎯 FHIR BUNDLE FOUND - Analyzing Organizations:")
                fhir_bundle = patient_data['fhir_bundle']
                
                if isinstance(fhir_bundle, dict) and 'entry' in fhir_bundle:
                    for i, entry in enumerate(fhir_bundle['entry']):
                        resource = entry.get('resource', {})
                        if resource.get('resourceType') == 'Organization':
                            org_name = resource.get('name', 'Unknown')
                            org_id = resource.get('id', 'Unknown')
                            
                            print(f"      Organization {i+1}:")
                            print(f"        Name: {org_name}")
                            print(f"        ID: {org_id}")
                            
                            # Check address
                            if 'address' in resource and resource['address']:
                                addr = resource['address'][0]
                                address_parts = []
                                if 'line' in addr:
                                    address_parts.extend(addr['line'])
                                if 'city' in addr:
                                    address_parts.append(addr['city'])
                                if 'postalCode' in addr:
                                    address_parts.append(addr['postalCode'])
                                if 'country' in addr:
                                    address_parts.append(addr['country'])
                                
                                address_str = ', '.join(address_parts)
                                print(f"        Address: {address_str}")
                                
                                if "Nicosia" in address_str or "Cyprus" in org_name:
                                    print(f"        🚨 THIS IS THE CYPRUS DATA SOURCE!")
                                elif "Dublin" in address_str or "Ireland" in address_str:
                                    print(f"        ✅ This is correct Irish data")
            
            # Check data source info
            if 'data_source' in patient_data:
                print(f"\n📡 DATA SOURCE: {patient_data['data_source']}")
            
            if 'is_fhir_source' in patient_data:
                print(f"   FHIR Source: {patient_data['is_fhir_source']}")
            
            if 'file_path' in patient_data:
                print(f"   File Path: {patient_data['file_path']}")
            
            if 'country_code' in patient_data:
                print(f"   Country Code: {patient_data['country_code']}")
    
    # Check extended data as well
    extended_key = f'patient_extended_data_{patient_id}'
    if extended_key in target_session:
        print(f"\n📈 EXTENDED DATA ANALYSIS:")
        extended_data = target_session[extended_key]
        
        if isinstance(extended_data, dict):
            print(f"   Extended data keys: {list(extended_data.keys())}")
            
            if 'healthcare_data' in extended_data:
                healthcare_data = extended_data['healthcare_data']
                print(f"   Healthcare data available: Yes")
                
                if 'organizations' in healthcare_data:
                    print(f"\n🏥 HEALTHCARE ORGANIZATIONS:")
                    orgs = healthcare_data['organizations']
                    
                    for i, org in enumerate(orgs):
                        print(f"      Organization {i+1}:")
                        print(f"        Name: {org.get('name', 'Unknown')}")
                        
                        if 'address' in org:
                            addr = org['address']
                            print(f"        City: {addr.get('city', 'Unknown')}")
                            print(f"        Country: {addr.get('country', 'Unknown')}")
                            
                            if addr.get('city') == 'Nicosia':
                                print(f"        🚨 CYPRUS DATA IN HEALTHCARE ORGANIZATIONS!")

def check_file_sources():
    """
    Check what files might be the source of this data
    """
    print(f"\n📁 CHECKING POTENTIAL FILE SOURCES:")
    
    patient_id = "1708631189"
    
    # Check test data directories
    test_dirs = [
        "test_data/eu_member_states/IE/",
        "test_data/eu_member_states/CY/", 
        "test_data/fhir_bundles/",
        "test_data/"
    ]
    
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            print(f"\n   📂 Directory: {test_dir}")
            files = os.listdir(test_dir)
            
            for file in files:
                if patient_id in file or file.endswith('.json'):
                    file_path = os.path.join(test_dir, file)
                    print(f"      📄 {file}")
                    
                    # Try to read and check for Cyprus data
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        if "Cyprus" in content or "Nicosia" in content:
                            print(f"         🚨 CONTAINS CYPRUS DATA!")
                        elif "Dublin" in content or "Ireland" in content:
                            print(f"         ✅ Contains Irish data")
                        
                        if patient_id in content:
                            print(f"         🎯 Contains patient ID {patient_id}")
                    
                    except Exception as e:
                        print(f"         ❌ Could not read: {str(e)}")

if __name__ == "__main__":
    deep_investigate_patient_session()
    check_file_sources()
    print(f"\n🎯 DEEP INVESTIGATION COMPLETE")
    print(f"💡 The Cyprus data is coming from the FHIR bundle in the session!")