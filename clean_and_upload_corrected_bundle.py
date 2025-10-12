#!/usr/bin/env python3
"""
Clean HAPI FHIR Server and Upload Corrected Irish Bundle

This script will:
1. Remove all contaminated Cyprus organizations from HAPI server
2. Remove old Irish patient data with non-namespaced IDs
3. Upload the corrected Irish bundle with proper IE- namespacing
"""

import requests
import json
import time

def clean_hapi_fhir_server():
    """
    Clean contaminated data from HAPI FHIR server
    """
    print("🧹 CLEANING HAPI FHIR SERVER")
    print("=" * 60)
    
    base_url = "http://hapi.fhir.org/baseR4"
    
    # Step 1: Remove all Cyprus organizations
    print(f"\n1️⃣ REMOVING CYPRUS ORGANIZATIONS:")
    
    cyprus_queries = [
        f"{base_url}/Organization?name=eHealthLab",
        f"{base_url}/Organization?address-city=Nicosia"
    ]
    
    deleted_cyprus_orgs = 0
    
    for query_url in cyprus_queries:
        try:
            print(f"   🔍 Searching: {query_url}")
            response = requests.get(query_url, timeout=10, headers={
                'Accept': 'application/fhir+json'
            })
            
            if response.status_code == 200:
                data = response.json()
                total = data.get('total', 0)
                print(f"   📋 Found {total} Cyprus organizations")
                
                if 'entry' in data:
                    for entry in data['entry']:
                        org_resource = entry.get('resource', {})
                        if org_resource.get('resourceType') == 'Organization':
                            org_id = org_resource.get('id', 'Unknown')
                            org_name = org_resource.get('name', 'Unknown')
                            
                            print(f"   🗑️  Deleting: {org_name} (ID: {org_id})")
                            
                            # Delete the organization
                            delete_url = f"{base_url}/Organization/{org_id}"
                            delete_response = requests.delete(delete_url, timeout=10)
                            
                            if delete_response.status_code in [200, 204, 404]:
                                print(f"      ✅ Deleted successfully")
                                deleted_cyprus_orgs += 1
                            else:
                                print(f"      ❌ Delete failed: {delete_response.status_code}")
                            
                            time.sleep(0.5)  # Be nice to the server
        
        except Exception as e:
            print(f"   ❌ Error cleaning Cyprus orgs: {str(e)}")
    
    print(f"   📊 Total Cyprus organizations deleted: {deleted_cyprus_orgs}")
    
    # Step 2: Remove old Irish patient with non-namespaced ID
    print(f"\n2️⃣ REMOVING OLD IRISH PATIENT DATA:")
    
    old_patient_id = "patrick-murphy-test"
    
    try:
        # Check if old patient exists
        patient_url = f"{base_url}/Patient/{old_patient_id}"
        response = requests.get(patient_url, timeout=10)
        
        if response.status_code == 200:
            print(f"   🔍 Found old patient: {old_patient_id}")
            
            # Delete old patient
            delete_response = requests.delete(patient_url, timeout=10)
            
            if delete_response.status_code in [200, 204, 404]:
                print(f"   ✅ Old patient deleted successfully")
            else:
                print(f"   ❌ Failed to delete old patient: {delete_response.status_code}")
        else:
            print(f"   ℹ️  Old patient not found (already deleted or doesn't exist)")
    
    except Exception as e:
        print(f"   ❌ Error checking/deleting old patient: {str(e)}")
    
    # Step 3: Remove any resources with old non-namespaced IDs
    print(f"\n3️⃣ REMOVING OLD NON-NAMESPACED RESOURCES:")
    
    old_resource_ids = [
        "6afe0b93-89f1-494a-b270-a567bbd77d7d",  # Old composition
        "66b404e7-6769-41f3-be7a-a5253d0f1afd",  # Old patient
        "a7c45450-105a-43aa-985c-ea8bd5b0b1cc",  # Old organization
        "ab4763e2-669f-4ff9-a8a8-98f24ce72c26"   # Old practitioner
    ]
    
    resource_types = ["Composition", "Patient", "Organization", "Practitioner"]
    
    for resource_type in resource_types:
        for resource_id in old_resource_ids:
            try:
                resource_url = f"{base_url}/{resource_type}/{resource_id}"
                response = requests.get(resource_url, timeout=10)
                
                if response.status_code == 200:
                    print(f"   🗑️  Deleting old {resource_type}: {resource_id}")
                    
                    delete_response = requests.delete(resource_url, timeout=10)
                    
                    if delete_response.status_code in [200, 204, 404]:
                        print(f"      ✅ Deleted successfully")
                    else:
                        print(f"      ❌ Delete failed: {delete_response.status_code}")
                
                time.sleep(0.3)  # Rate limiting
            
            except Exception as e:
                continue  # Resource doesn't exist, continue
    
    print(f"   ✅ Old resource cleanup completed")

def upload_corrected_bundle():
    """
    Upload the corrected Irish bundle with proper namespacing
    """
    print(f"\n📤 UPLOADING CORRECTED IRISH BUNDLE")
    print("=" * 60)
    
    base_url = "http://hapi.fhir.org/baseR4"
    bundle_path = "test_data/eu_member_states/IE/539305455995368085_EPSOS_PS_CORRECTED.json"
    
    try:
        # Load the corrected bundle
        with open(bundle_path, 'r', encoding='utf-8') as f:
            bundle_data = json.load(f)
        
        print(f"📁 Loaded corrected bundle: {bundle_path}")
        print(f"📦 Bundle ID: {bundle_data.get('id', 'No ID')}")
        
        # Upload the bundle
        upload_url = f"{base_url}/"
        
        headers = {
            'Content-Type': 'application/fhir+json',
            'Accept': 'application/fhir+json'
        }
        
        print(f"🚀 Uploading to: {upload_url}")
        
        response = requests.post(upload_url, 
                               json=bundle_data, 
                               headers=headers, 
                               timeout=30)
        
        if response.status_code in [200, 201]:
            print(f"✅ Bundle uploaded successfully!")
            print(f"   Status: {response.status_code}")
            
            # Parse response to see what was created
            try:
                response_data = response.json()
                if 'entry' in response_data:
                    print(f"   📊 Resources created:")
                    for entry in response_data['entry']:
                        response_entry = entry.get('response', {})
                        status = response_entry.get('status', 'Unknown')
                        location = response_entry.get('location', 'Unknown')
                        print(f"      • {status}: {location}")
            except:
                pass
        
        else:
            print(f"❌ Upload failed!")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:500]}...")
    
    except FileNotFoundError:
        print(f"❌ Bundle file not found: {bundle_path}")
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")

def verify_corrected_data():
    """
    Verify that the corrected data is now on the server
    """
    print(f"\n✅ VERIFYING CORRECTED DATA")
    print("=" * 60)
    
    base_url = "http://hapi.fhir.org/baseR4"
    
    # Test queries for the corrected data
    verification_queries = [
        ("Irish Patient", f"{base_url}/Patient/IE-patient-66b404e7-6769-41f3-be7a-a5253d0f1afd"),
        ("Irish Organization", f"{base_url}/Organization/IE-org-a7c45450-105a-43aa-985c-ea8bd5b0b1cc"),
        ("Irish Practitioner", f"{base_url}/Practitioner/IE-pract-ab4763e2-669f-4ff9-a8a8-98f24ce72c26"),
        ("Cyprus Organizations", f"{base_url}/Organization?name=eHealthLab"),
        ("Irish HSE", f"{base_url}/Organization?name=Health Service Executive")
    ]
    
    for test_name, url in verification_queries:
        try:
            print(f"🔍 Testing: {test_name}")
            response = requests.get(url, timeout=10, headers={
                'Accept': 'application/fhir+json'
            })
            
            if response.status_code == 200:
                data = response.json()
                
                if 'resourceType' in data:
                    # Single resource
                    resource_type = data.get('resourceType', 'Unknown')
                    resource_id = data.get('id', 'Unknown')
                    print(f"   ✅ Found: {resource_type} {resource_id}")
                    
                    if resource_type == 'Organization':
                        org_name = data.get('name', 'Unknown')
                        address = data.get('address', {})
                        city = address.get('city', 'Unknown') if isinstance(address, dict) else 'Unknown'
                        country = address.get('country', 'Unknown') if isinstance(address, dict) else 'Unknown'
                        print(f"      Name: {org_name}")
                        print(f"      Location: {city}, {country}")
                        
                        if 'IE-org-' in resource_id:
                            print(f"      ✅ Proper Irish namespacing confirmed")
                
                elif 'total' in data:
                    # Search results
                    total = data.get('total', 0)
                    print(f"   📊 Found {total} resources")
                    
                    if "Cyprus" in test_name and total == 0:
                        print(f"   ✅ Cyprus contamination successfully removed")
                    elif "Irish" in test_name and total > 0:
                        print(f"   ✅ Irish data successfully uploaded")
            
            else:
                print(f"   ❌ Status: {response.status_code}")
        
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

def main():
    """
    Main execution function
    """
    print("🔧 HAPI FHIR SERVER CLEANUP AND CORRECTED UPLOAD")
    print("=" * 70)
    print("⚠️  This will DELETE contaminated data and upload corrected bundle")
    
    confirmation = input("\nProceed? (yes/no): ").lower().strip()
    
    if confirmation not in ['yes', 'y']:
        print("❌ Operation cancelled")
        return
    
    # Execute the cleanup and upload process
    clean_hapi_fhir_server()
    
    print(f"\n⏱️  Waiting 5 seconds for server to process deletions...")
    time.sleep(5)
    
    upload_corrected_bundle()
    
    print(f"\n⏱️  Waiting 5 seconds for server to process uploads...")
    time.sleep(5)
    
    verify_corrected_data()
    
    print(f"\n🎯 CLEANUP AND UPLOAD COMPLETE!")
    print(f"💡 You can now test the patient page - should show Irish data only")
    print(f"🔄 Remember to clear your Django session cache too!")

if __name__ == "__main__":
    main()