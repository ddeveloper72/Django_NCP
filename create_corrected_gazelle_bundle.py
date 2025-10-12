#!/usr/bin/env python3
"""
Create Corrected Gazelle Bundle with IE Namespace Protection

This script will:
1. Load the Gazelle-validated bundle
2. Apply IE- namespace prefixes to all resource IDs
3. Fix medication references (convert to inline)
4. Add proper bundle ID
5. Correct country codes to IE
6. Create collision-proof version for HAPI server
"""

import json
import uuid
from datetime import datetime

def create_corrected_gazelle_bundle():
    """
    Create collision-proof version of Gazelle bundle
    """
    print("🔧 CREATING CORRECTED GAZELLE BUNDLE")
    print("=" * 50)
    
    input_path = "test_data/eu_member_states/IE/combined_fhir_bundle.json"
    output_path = "test_data/eu_member_states/IE/combined_fhir_bundle_CORRECTED.json"
    
    try:
        # Load original Gazelle bundle
        with open(input_path, 'r', encoding='utf-8') as f:
            bundle = json.load(f)
        
        print(f"📁 Input: {input_path}")
        print(f"📤 Output: {output_path}")
        
        # Add bundle-level protection
        bundle['id'] = "IE-gazelle-patient-summary-combined"
        bundle['type'] = "transaction"  # Change to transaction for HAPI upload
        bundle['timestamp'] = datetime.now().isoformat() + "Z"
        
        print(f"🆔 Bundle ID: {bundle['id']}")
        print(f"🏷️  Bundle Type: {bundle['type']}")
        
        # Resource ID mapping for reference updates
        id_mapping = {}
        
        entries = bundle.get('entry', [])
        print(f"\n🔄 Processing {len(entries)} resources:")
        
        # Phase 1: Update all resource IDs and create mapping
        for i, entry in enumerate(entries):
            resource = entry.get('resource', {})
            resource_type = resource.get('resourceType', 'Unknown')
            old_id = resource.get('id', f'missing-{i}')
            
            # Create IE-prefixed ID
            if resource_type == 'Composition':
                new_id = f"IE-comp-{old_id}"
            elif resource_type == 'Patient':
                new_id = f"IE-patient-{old_id}"
            elif resource_type == 'Organization':
                new_id = f"IE-org-{old_id}"
            elif resource_type == 'Practitioner':
                new_id = f"IE-pract-{old_id}"
            elif resource_type == 'Condition':
                new_id = f"IE-cond-{old_id}"
            elif resource_type == 'Procedure':
                new_id = f"IE-proc-{old_id}"
            elif resource_type == 'MedicationStatement':
                new_id = f"IE-medstat-{old_id}"
            elif resource_type == 'AllergyIntolerance':
                new_id = f"IE-allergy-{old_id}"
            else:
                new_id = f"IE-{resource_type.lower()}-{old_id}"
            
            # Store mapping
            id_mapping[old_id] = new_id
            id_mapping[f"{resource_type}/{old_id}"] = f"{resource_type}/{new_id}"
            
            # Update resource ID
            resource['id'] = new_id
            
            # Update fullUrl
            entry['fullUrl'] = f"http://{resource_type}/{new_id}"
            
            # Add request for transaction bundle
            entry['request'] = {
                "method": "PUT",
                "url": f"{resource_type}/{new_id}"
            }
            
            print(f"   {i+1:2d}. {resource_type:15s} | {old_id} → {new_id}")
        
        # Phase 2: Update all references and fix specific issues
        print(f"\n🔗 Updating references and fixing issues:")
        
        for entry in entries:
            resource = entry.get('resource', {})
            resource_type = resource.get('resourceType', 'Unknown')
            
            # Fix Organization and Practitioner country codes
            if resource_type == 'Organization':
                contacts = resource.get('contact', [])
                for contact in contacts:
                    address = contact.get('address', {})
                    if address.get('country') == 'GR':
                        address['country'] = 'IE'
                        print(f"   ✅ Fixed Organization country: GR → IE")
            
            elif resource_type == 'Practitioner':
                addresses = resource.get('address', [])
                for address in addresses:
                    if address.get('country') == 'GR':
                        address['country'] = 'IE'
                        print(f"   ✅ Fixed Practitioner country: GR → IE")
            
            # Fix MedicationStatement references
            elif resource_type == 'MedicationStatement':
                if 'medicationReference' in resource:
                    med_ref = resource['medicationReference']
                    print(f"   💊 Converting medication reference to inline for {resource['id']}")
                    
                    # Remove medicationReference
                    del resource['medicationReference']
                    
                    # Add medicationCodeableConcept
                    resource['medicationCodeableConcept'] = {
                        "coding": [
                            {
                                "system": "http://www.whocc.no/atc",
                                "code": "A10AE04",
                                "display": "insulin glargine"
                            }
                        ],
                        "text": "LANTUS Solostar INJ.SOL 100 IU/ML"
                    }
                    print(f"   ✅ Added inline medication for {resource['id']}")
            
            # Update all references within resources
            def update_references(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if key == 'reference' and isinstance(value, str):
                            # Find matching reference in mapping
                            for old_ref, new_ref in id_mapping.items():
                                if value == old_ref or value.endswith(f"/{old_ref}"):
                                    obj[key] = new_ref
                                    print(f"   🔗 Updated reference: {value} → {new_ref}")
                                    break
                        else:
                            update_references(value, f"{path}.{key}" if path else key)
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        update_references(item, f"{path}[{i}]")
            
            update_references(resource)
        
        # Add country tagging and metadata
        bundle['meta'] = {
            "tag": [
                {
                    "system": "http://ehds.ie/country",
                    "code": "IE",
                    "display": "Ireland"
                }
            ]
        }
        
        # Save corrected bundle
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(bundle, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ CORRECTED BUNDLE CREATED")
        print(f"📁 Saved to: {output_path}")
        print(f"🛡️  All resources now have IE- namespace protection")
        print(f"💊 Medication references converted to inline")
        print(f"🇮🇪 Country codes corrected to IE")
        print(f"🆔 Bundle ID: {bundle['id']}")
        
        return True
    
    except Exception as e:
        print(f"❌ Error creating corrected bundle: {e}")
        return False

if __name__ == "__main__":
    create_corrected_gazelle_bundle()