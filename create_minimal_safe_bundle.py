#!/usr/bin/env python3
"""
Create Minimal Collision-Safe Gazelle Bundle

This script will ONLY add IE- namespace prefixes to resource IDs
while preserving the exact Gazelle-validated structure.

Changes made:
1. Add bundle ID with IE- prefix
2. Add IE- prefixes to all resource IDs  
3. Update internal references to use IE- prefixed IDs
4. Fix country codes (GR → IE)

Changes NOT made (to preserve Gazelle validation):
- Keep bundle type as "document" 
- Keep original fullUrl structure
- Keep medicationReference structure
- Keep original entry structure
- No transaction requests added
- No metadata changes
"""

import json
from datetime import datetime

def create_minimal_collision_safe_bundle():
    """
    Create minimal collision-safe version preserving Gazelle validation
    """
    print("🔧 CREATING MINIMAL COLLISION-SAFE GAZELLE BUNDLE")
    print("=" * 60)
    
    input_path = "test_data/eu_member_states/IE/combined_fhir_bundle.json"
    output_path = "test_data/eu_member_states/IE/combined_fhir_bundle_SAFE.json"
    
    try:
        # Load original Gazelle bundle
        with open(input_path, 'r', encoding='utf-8') as f:
            bundle = json.load(f)
        
        print(f"📁 Input: {input_path}")
        print(f"📤 Output: {output_path}")
        print(f"🎯 Goal: Minimal changes to prevent HAPI server collisions")
        
        # MINIMAL CHANGE 1: Add bundle-level protection only
        bundle['id'] = "IE-gazelle-patient-summary-combined"
        
        print(f"🆔 Added Bundle ID: {bundle['id']}")
        print(f"🏷️  Preserved Bundle Type: {bundle['type']}")
        
        # Resource ID mapping for reference updates
        id_mapping = {}
        
        entries = bundle.get('entry', [])
        print(f"\n🔄 Processing {len(entries)} resources (minimal changes only):")
        
        # Phase 1: Update only resource IDs (preserve everything else)
        for i, entry in enumerate(entries):
            resource = entry.get('resource', {})
            resource_type = resource.get('resourceType', 'Unknown')
            old_id = resource.get('id', f'missing-{i}')
            
            # Create IE-prefixed ID (same logic as before)
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
            
            # Store mapping for reference updates
            id_mapping[old_id] = new_id
            id_mapping[f"{resource_type}/{old_id}"] = f"{resource_type}/{new_id}"
            
            # ONLY update resource ID (preserve everything else)
            resource['id'] = new_id
            
            # Update fullUrl to match (preserve structure)
            entry['fullUrl'] = f"http://{resource_type}/{new_id}"
            
            print(f"   {i+1:2d}. {resource_type:15s} | {old_id} → {new_id}")
        
        # Phase 2: Update internal references only
        print(f"\n🔗 Updating internal references (preserve structure):")
        
        for entry in entries:
            resource = entry.get('resource', {})
            resource_type = resource.get('resourceType', 'Unknown')
            
            # MINIMAL CHANGE 2: Fix only country codes 
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
            
            # Update all internal references (preserve medicationReference structure)
            def update_references(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if key == 'reference' and isinstance(value, str):
                            # Special handling for medication references
                            if value.startswith("Medication/"):
                                med_id = value.replace("Medication/", "")
                                new_med_ref = f"Medication/IE-med-{med_id}"
                                obj[key] = new_med_ref
                                print(f"   💊 Updated medication ref: {value} → {new_med_ref}")
                            else:
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
        
        # Save minimal collision-safe bundle
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(bundle, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ MINIMAL COLLISION-SAFE BUNDLE CREATED")
        print(f"📁 Saved to: {output_path}")
        print(f"🛡️  IE- namespace prefixes added for collision protection")
        print(f"🏗️  Original Gazelle structure preserved")
        print(f"📋 Bundle type: {bundle['type']} (unchanged)")
        print(f"💊 MedicationReference structure preserved")
        print(f"🔗 Internal references updated to IE- prefixes")
        print(f"🇮🇪 Country codes corrected to IE")
        
        print(f"\n🎯 KEY DIFFERENCES FROM PREVIOUS VERSION:")
        print(f"   ❌ NO bundle type change (kept 'document')")
        print(f"   ❌ NO transaction requests added")
        print(f"   ❌ NO medication structure changes")
        print(f"   ❌ NO metadata additions")
        print(f"   ✅ ONLY resource ID prefixing for collision safety")
        
        return True
    
    except Exception as e:
        print(f"❌ Error creating minimal safe bundle: {e}")
        return False

if __name__ == "__main__":
    create_minimal_collision_safe_bundle()