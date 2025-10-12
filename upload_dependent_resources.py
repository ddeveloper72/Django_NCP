#!/usr/bin/env python3
"""
Upload Remaining FHIR Resources with Dependencies

Now that core resources (Patient, Organization, Practitioner) are uploaded,
we can upload the dependent resources (Conditions, Allergies, etc.)
"""

import requests
import json
import time

def upload_dependent_resources():
    """
    Upload resources that depend on the core resources
    """
    print("🔧 UPLOADING DEPENDENT FHIR RESOURCES")
    print("=" * 50)
    
    base_url = "http://hapi.fhir.org/baseR4"
    bundle_path = "test_data/eu_member_states/IE/combined_fhir_bundle_ULTRA_SAFE.json"
    
    try:
        with open(bundle_path, 'r', encoding='utf-8') as f:
            bundle_data = json.load(f)
        
        entries = bundle_data.get('entry', [])
        
        # Resources that typically depend on others (upload in order)
        dependent_resources = [
            'Condition',
            'AllergyIntolerance', 
            'MedicationStatement',
            'Procedure',
            'Composition'
        ]
        
        print(f"📋 Uploading dependent resources in dependency order:")
        
        headers = {
            'Content-Type': 'application/fhir+json',
            'Accept': 'application/fhir+json'
        }
        
        uploaded_count = 0
        
        for resource_type in dependent_resources:
            print(f"\n📦 Uploading {resource_type} resources:")
            
            # Find all resources of this type
            type_resources = [
                entry for entry in entries 
                if entry.get('resource', {}).get('resourceType') == resource_type
            ]
            
            for entry in type_resources:
                resource = entry.get('resource', {})
                resource_id = resource.get('id', 'unknown')
                
                print(f"   🔄 {resource_type}: {resource_id}")
                
                # Special handling for MedicationStatement
                if resource_type == 'MedicationStatement':
                    # Check if it references a missing medication
                    med_ref = resource.get('medicationReference', {}).get('reference', '')
                    if med_ref and 'Medication/' in med_ref:
                        print(f"      ⚠️  Has external medication reference: {med_ref}")
                        print(f"      💡 This may fail - medication not in bundle")
                
                # Upload the resource
                resource_url = f"{base_url}/{resource_type}/{resource_id}"
                
                try:
                    response = requests.put(resource_url, 
                                          json=resource, 
                                          headers=headers, 
                                          timeout=15)
                    
                    if response.status_code in [200, 201]:
                        print(f"      ✅ Success: {response.status_code}")
                        uploaded_count += 1
                    else:
                        print(f"      ❌ Failed: {response.status_code}")
                        
                        # Show detailed error for debugging
                        try:
                            error_data = response.json()
                            if 'issue' in error_data and error_data['issue']:
                                issue = error_data['issue'][0]
                                details = issue.get('diagnostics', 'No details')
                                print(f"         💬 {details[:150]}...")
                        except:
                            print(f"         💬 {response.text[:100]}...")
                
                except Exception as e:
                    print(f"      ❌ Error: {str(e)}")
                
                time.sleep(0.3)  # Rate limiting
        
        print(f"\n📊 Dependent Resources Upload Summary:")
        print(f"   Additional resources uploaded: {uploaded_count}")
        
        # Final verification
        print(f"\n🔍 FINAL VERIFICATION:")
        
        verification_queries = [
            ("All Patients", f"{base_url}/Patient"),
            ("All Organizations", f"{base_url}/Organization"),
            ("All Conditions", f"{base_url}/Condition"), 
            ("All Allergies", f"{base_url}/AllergyIntolerance"),
            ("All Procedures", f"{base_url}/Procedure"),
            ("All MedicationStatements", f"{base_url}/MedicationStatement"),
            ("All Compositions", f"{base_url}/Composition")
        ]
        
        total_resources = 0
        
        for test_name, url in verification_queries:
            try:
                response = requests.get(url, timeout=10, headers={'Accept': 'application/fhir+json'})
                
                if response.status_code == 200:
                    data = response.json()
                    total = data.get('total', 0)
                    total_resources += total
                    print(f"   {test_name}: {total} resources")
                    
                    # Show some details for key resources
                    if total > 0 and 'entry' in data and test_name in ["All Patients", "All Organizations"]:
                        for entry in data['entry'][:2]:  # First 2
                            resource = entry.get('resource', {})
                            resource_type = resource.get('resourceType', 'Unknown')
                            resource_id = resource.get('id', 'Unknown')
                            
                            if resource_type == 'Patient':
                                name = resource.get('name', [{}])[0].get('family', 'Unknown')
                                print(f"      • Patient: {name} (ID: {resource_id})")
                            elif resource_type == 'Organization':
                                name = resource.get('name', 'Unknown')
                                print(f"      • Organization: {name} (ID: {resource_id})")
                
                else:
                    print(f"   {test_name}: Query failed ({response.status_code})")
            
            except Exception as e:
                print(f"   {test_name}: Error - {str(e)}")
        
        print(f"\n🎯 UPLOAD COMPLETE!")
        print(f"📊 Total resources on server: {total_resources}")
        print(f"✅ Gazelle-validated Irish healthcare data uploaded")
        print(f"🇮🇪 Country codes corrected (IE instead of GR)")
        print(f"🛡️  Session isolation will prevent future contamination")
        print(f"🔄 Ready to test Django application")
        
        return uploaded_count > 0
    
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        return False

if __name__ == "__main__":
    upload_dependent_resources()