#!/usr/bin/env python3
"""
Re-upload Portuguese Composition to Fix FHIR Integration

The Composition (document) failed to upload initially because it referenced
the Patient before the Patient was created. Now we re-upload it.
"""

import requests
import json

def reupload_portuguese_composition():
    """Re-upload the Composition for Portuguese patient"""
    
    print("🔧 RE-UPLOADING PORTUGUESE COMPOSITION")
    print("=" * 40)
    
    base_url = "http://hapi.fhir.org/baseR4"
    
    # Load the bundle to get the Composition
    try:
        with open('test_data/eu_member_states/PT/2-1234-W7_enhanced_fhir_bundle_pre_gazelle_fix_backup.json', 'r') as f:
            bundle_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading bundle: {e}")
        return False
    
    # Find the Composition entry
    composition = None
    for entry in bundle_data.get('entry', []):
        resource = entry.get('resource', {})
        if resource.get('resourceType') == 'Composition':
            composition = resource
            break
    
    if not composition:
        print("❌ No Composition found in bundle")
        return False
    
    composition_id = composition.get('id')
    subject_ref = composition.get('subject', {}).get('reference', 'Unknown')
    title = composition.get('title', 'Unknown')
    
    print(f"📄 Composition ID: {composition_id}")
    print(f"📋 Title: {title}")
    print(f"👤 Subject: {subject_ref}")
    
    # Upload the Composition
    url = f"{base_url}/Composition/{composition_id}"
    headers = {
        'Content-Type': 'application/fhir+json',
        'Accept': 'application/fhir+json'
    }
    
    print(f"\n📤 Uploading to: {url}")
    
    try:
        response = requests.put(url, json=composition, headers=headers, timeout=15)
        print(f"📊 Upload status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print("✅ Composition uploaded successfully!")
        else:
            print(f"❌ Failed to upload Composition: {response.status_code}")
            try:
                error_data = response.json()
                if 'issue' in error_data and error_data['issue']:
                    issue = error_data['issue'][0]
                    details = issue.get('diagnostics', 'No details')
                    print(f"   Error: {details}")
            except:
                print(f"   Error text: {response.text[:200]}")
                
    except Exception as e:
        print(f"❌ Error uploading Composition: {e}")
        return False
    
    # Now test if we can find the Composition
    print(f"\n🔍 Testing Composition search...")
    try:
        search_url = f"{base_url}/Composition?subject=Patient/2-1234-W7"
        response = requests.get(search_url, headers={'Accept': 'application/fhir+json'}, timeout=10)
        
        print(f"🔍 Search URL: {search_url}")
        print(f"📊 Search status: {response.status_code}")
        
        if response.status_code == 200:
            search_results = response.json()
            total = search_results.get('total', 0)
            print(f"📋 Found {total} compositions for patient 2-1234-W7")
            
            if total > 0:
                print("✅ SUCCESS: Composition now found!")
                
                # Show details of found compositions
                entries = search_results.get('entry', [])
                for i, entry in enumerate(entries):
                    resource = entry.get('resource', {})
                    comp_id = resource.get('id', 'Unknown')
                    comp_title = resource.get('title', 'Unknown')
                    comp_date = resource.get('date', 'Unknown')
                    
                    print(f"   Document {i+1}: {comp_id}")
                    print(f"      Title: {comp_title}")
                    print(f"      Date: {comp_date}")
                    
                return True
            else:
                print("❌ Still no compositions found")
                return False
        else:
            print(f"❌ Search failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Search error: {e}")
        return False

if __name__ == "__main__":
    success = reupload_portuguese_composition()
    
    if success:
        print(f"\n🎉 Portuguese patient documents should now be searchable!")
        print(f"🇵🇹 Patient ID: 2-1234-W7 (Diana Ferreira)")
        print(f"📄 Document type: International Patient Summary")
    else:
        print(f"\n⚠️  Composition upload may need manual investigation")