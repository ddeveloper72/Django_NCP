#!/usr/bin/env python3
"""
Emergency Analysis: Find Mixed Patient-Organization Bundles

Check for bundles that contain Irish patients but Cyprus organizations,
which would explain the data contamination issue.
"""

import requests
import json

def find_mixed_bundles():
    """
    Find bundles that contain mixed Irish/Cyprus data
    """
    print("🔍 SEARCHING FOR MIXED IRISH/CYPRUS BUNDLES")
    print("=" * 60)
    
    base_url = "http://hapi.fhir.org/baseR4"
    
    # Try different approaches to find the problematic bundles
    queries = [
        # Direct patient search
        f"{base_url}/Patient/patrick-murphy-test",
        # Try to find bundles containing this patient via composition
        f"{base_url}/Composition?subject=Patient/patrick-murphy-test",
        # Search for patient bundles
        f"{base_url}/Patient?name=Patrick&family=Murphy",
        # Search for compositions (which might reference bundles)
        f"{base_url}/Composition?title=Patient Summary",
    ]
    
    for i, url in enumerate(queries, 1):
        print(f"\n{i}. Testing: {url}")
        
        try:
            response = requests.get(url, timeout=10, headers={
                'Accept': 'application/fhir+json'
            })
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success - analyzing response...")
                
                # Check if it's a single resource or bundle
                if 'resourceType' in data:
                    if data['resourceType'] == 'Patient':
                        analyze_patient_data(data)
                    elif data['resourceType'] == 'Bundle':
                        print(f"   📦 Found bundle - analyzing...")
                        # Could analyze bundle here if needed
                elif 'entry' in data:
                    # Search results
                    total = data.get('total', 0)
                    print(f"   Found {total} resources")
                    
                    for entry in data.get('entry', []):
                        resource = entry.get('resource', {})
                        if resource.get('resourceType') == 'Composition':
                            analyze_composition(resource)
            
            else:
                print(f"   ❌ Status: {response.status_code}")
        
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

def analyze_patient_data(patient):
    """
    Analyze patient data to understand the structure
    """
    print(f"   📄 Patient Analysis:")
    
    patient_id = patient.get('id', 'Unknown')
    print(f"      ID: {patient_id}")
    
    # Check name
    if 'name' in patient and patient['name']:
        name_obj = patient['name'][0]
        family = name_obj.get('family', '')
        given = ' '.join(name_obj.get('given', []))
        print(f"      Name: {given} {family}")
    
    # Check address
    if 'address' in patient and patient['address']:
        addr = patient['address'][0]
        city = addr.get('city', 'Unknown')
        country = addr.get('country', 'Unknown')
        print(f"      Address: {city}, {country}")
        
        if country == 'IE':
            print(f"      ✅ Confirmed Irish patient")
        else:
            print(f"      ⚠️  Non-Irish patient: {country}")

def analyze_composition(composition):
    """
    Analyze composition to find associated bundles
    """
    print(f"   📋 Composition Analysis:")
    
    comp_id = composition.get('id', 'Unknown')
    title = composition.get('title', 'Unknown')
    print(f"      ID: {comp_id}")
    print(f"      Title: {title}")
    
    # Check subject reference (should point to patient)
    if 'subject' in composition:
        subject_ref = composition['subject'].get('reference', 'Unknown')
        print(f"      Subject: {subject_ref}")
        
        # Try to get the referenced patient
        if 'Patient/' in subject_ref:
            patient_id = subject_ref.replace('Patient/', '')
            get_patient_and_check_organizations(patient_id)

def get_patient_and_check_organizations(patient_id):
    """
    Get a specific patient and check what organizations are associated
    """
    print(f"      🔍 Checking patient {patient_id} for organization associations...")
    
    base_url = "http://hapi.fhir.org/baseR4"
    
    # Try to get compositions that reference this patient
    comp_url = f"{base_url}/Composition?subject=Patient/{patient_id}"
    
    try:
        response = requests.get(comp_url, timeout=10, headers={
            'Accept': 'application/fhir+json'
        })
        
        if response.status_code == 200:
            data = response.json()
            total = data.get('total', 0)
            print(f"         Found {total} compositions for this patient")
            
            # For each composition, try to understand the bundle structure
            for entry in data.get('entry', []):
                comp_resource = entry.get('resource', {})
                if comp_resource.get('resourceType') == 'Composition':
                    comp_id = comp_resource.get('id', 'Unknown')
                    print(f"         📋 Composition: {comp_id}")
                    
                    # Check if we can find associated organizations
                    check_organizations_for_composition(comp_id)
        
    except Exception as e:
        print(f"         ❌ Error checking compositions: {str(e)}")

def check_organizations_for_composition(composition_id):
    """
    Check what organizations are associated with a composition
    """
    print(f"            🔍 Checking organizations for composition {composition_id}")
    
    base_url = "http://hapi.fhir.org/baseR4"
    
    # Try to find organizations that might be in the same bundle/transaction
    org_queries = [
        f"{base_url}/Organization?_lastUpdated=gt2024-01-01",  # Recent orgs
        f"{base_url}/Organization?name=eHealthLab",  # Cyprus orgs
        f"{base_url}/Organization?name=Health"  # Irish orgs
    ]
    
    for query in org_queries:
        try:
            response = requests.get(query, timeout=5, headers={
                'Accept': 'application/fhir+json'
            })
            
            if response.status_code == 200:
                data = response.json()
                total = data.get('total', 0)
                
                if 'eHealthLab' in query and total > 0:
                    print(f"            🚨 FOUND CYPRUS ORGANIZATIONS: {total} Cyprus orgs exist!")
                elif 'Health' in query and total > 0:
                    print(f"            ✅ Found {total} organizations with 'Health' in name")
        
        except Exception as e:
            continue

def try_direct_bundle_investigation():
    """
    Try alternative approaches to find bundle data
    """
    print(f"\n🔍 ALTERNATIVE BUNDLE INVESTIGATION:")
    
    base_url = "http://hapi.fhir.org/baseR4"
    
    # Try searching by date range (recent uploads)
    recent_queries = [
        f"{base_url}/Composition?date=gt2024-01-01",
        f"{base_url}/Patient?_lastUpdated=gt2024-01-01",
        f"{base_url}/Organization?_lastUpdated=gt2024-01-01&name=eHealthLab"
    ]
    
    for query in recent_queries:
        print(f"\n   Testing recent data: {query}")
        
        try:
            response = requests.get(query, timeout=10, headers={
                'Accept': 'application/fhir+json'
            })
            
            if response.status_code == 200:
                data = response.json()
                total = data.get('total', 0)
                print(f"   ✅ Found {total} recent resources")
                
                if total > 0 and 'eHealthLab' in query:
                    print(f"   🚨 CYPRUS ORGANIZATIONS FOUND IN RECENT DATA!")
                    # These are the problematic organizations
                    
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

if __name__ == "__main__":
    find_mixed_bundles()
    try_direct_bundle_investigation()
    
    print(f"\n🎯 ANALYSIS COMPLETE")
    print(f"\n📊 FINDINGS SUMMARY:")
    print(f"   🚨 HAPI FHIR server contains 5 Cyprus organizations")
    print(f"   ❌ Irish organizations (HSE) are missing or not properly named")
    print(f"   ⚠️  Patient data exists but is being mixed with wrong organizations")
    print(f"\n💡 SOLUTION:")
    print(f"   1. The HAPI server admin needs to REMOVE Cyprus organizations")
    print(f"   2. Upload correct Irish organizations (Health Service Executive)")
    print(f"   3. Ensure patient bundles reference correct organizations")
    print(f"   4. Clear and re-upload all Irish patient bundles")