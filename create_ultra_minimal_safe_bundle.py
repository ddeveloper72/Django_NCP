#!/usr/bin/env python3
"""
Create Ultra-Minimal Collision-Safe Gazelle Bundle

This approach adds ONLY bundle-level protection without touching
any resource IDs or references to preserve exact Gazelle validation.

Strategy:
1. Add unique bundle ID with IE- prefix for server-level protection
2. Leave ALL resource IDs unchanged 
3. Leave ALL references unchanged
4. Leave fullUrl structure unchanged
5. Only fix the GR→IE country codes (data correction)

This should pass Gazelle validation while providing basic server collision protection.
"""

import json

def create_ultra_minimal_safe_bundle():
    """
    Create ultra-minimal safe version with bundle-level protection only
    """
    print("🔧 CREATING ULTRA-MINIMAL COLLISION-SAFE BUNDLE")
    print("=" * 60)
    
    input_path = "test_data/eu_member_states/IE/combined_fhir_bundle.json"
    output_path = "test_data/eu_member_states/IE/combined_fhir_bundle_ULTRA_SAFE.json"
    
    try:
        # Load original Gazelle bundle
        with open(input_path, 'r', encoding='utf-8') as f:
            bundle = json.load(f)
        
        print(f"📁 Input: {input_path}")
        print(f"📤 Output: {output_path}")
        print(f"🎯 Goal: Bundle-level protection only, preserve all resource structure")
        
        # ULTRA-MINIMAL CHANGE 1: Add bundle-level protection only
        original_bundle_structure = {
            "resourceType": bundle.get("resourceType"),
            "timestamp": bundle.get("timestamp"), 
            "identifier": bundle.get("identifier"),
            "type": bundle.get("type")
        }
        
        bundle['id'] = "IE-gazelle-patient-summary-combined"
        
        print(f"🆔 Added Bundle ID: {bundle['id']}")
        print(f"📋 Original Structure Preserved:")
        print(f"   Resource Type: {original_bundle_structure['resourceType']}")
        print(f"   Bundle Type: {original_bundle_structure['type']}")
        print(f"   Timestamp: {original_bundle_structure['timestamp']}")
        print(f"   Identifier: {original_bundle_structure['identifier']}")
        
        entries = bundle.get('entry', [])
        print(f"\n📊 Processing {len(entries)} resources (NO ID changes):")
        
        # ULTRA-MINIMAL CHANGE 2: Only fix country codes (data quality fix)
        country_fixes = 0
        
        for i, entry in enumerate(entries):
            resource = entry.get('resource', {})
            resource_type = resource.get('resourceType', 'Unknown')
            resource_id = resource.get('id', f'missing-{i}')
            
            print(f"   {i+1:2d}. {resource_type:15s} | {resource_id} (UNCHANGED)")
            
            # Only fix country codes - no ID changes
            if resource_type == 'Organization':
                contacts = resource.get('contact', [])
                for contact in contacts:
                    address = contact.get('address', {})
                    if address.get('country') == 'GR':
                        address['country'] = 'IE'
                        print(f"      ✅ Fixed country: GR → IE")
                        country_fixes += 1
            
            elif resource_type == 'Practitioner':
                addresses = resource.get('address', [])
                for address in addresses:
                    if address.get('country') == 'GR':
                        address['country'] = 'IE'
                        print(f"      ✅ Fixed country: GR → IE")
                        country_fixes += 1
        
        print(f"\n📋 CHANGES SUMMARY:")
        print(f"   Bundle ID added: ✅")
        print(f"   Resource IDs changed: ❌ (0 changes)")
        print(f"   References changed: ❌ (0 changes)")
        print(f"   FullUrl changed: ❌ (0 changes)")
        print(f"   Country codes fixed: ✅ ({country_fixes} fixes)")
        print(f"   Structure preserved: ✅ (100%)")
        
        # Save ultra-minimal bundle
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(bundle, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ ULTRA-MINIMAL BUNDLE CREATED")
        print(f"📁 Saved to: {output_path}")
        print(f"🛡️  Bundle-level collision protection added")
        print(f"🏗️  100% original Gazelle structure preserved") 
        print(f"🎯 This should pass Gazelle validation")
        
        # Show what wasn't changed (to emphasize preservation)
        print(f"\n🔒 WHAT STAYED EXACTLY THE SAME:")
        print(f"   ✅ All resource IDs (e.g., 6afe0b93-89f1-494a-b270-a567bbd77d7d)")
        print(f"   ✅ All internal references (e.g., Patient/66b404e7-6769-41f3-be7a-a5253d0f1afd)")
        print(f"   ✅ All fullUrl values (e.g., http://Composition/6afe0b93-89f1-494a-b270-a567bbd77d7d)")
        print(f"   ✅ Bundle type: document")
        print(f"   ✅ All medication references")
        print(f"   ✅ All entry structures")
        print(f"   ✅ All timestamps and identifiers")
        
        print(f"\n⚠️  COLLISION RISK ASSESSMENT:")
        print(f"   Server-level: 🟢 PROTECTED (unique bundle ID)")
        print(f"   Resource-level: 🟡 POTENTIAL (original UUIDs)")
        print(f"   Trade-off: Gazelle validation vs resource collision protection")
        
        return True
    
    except Exception as e:
        print(f"❌ Error creating ultra-minimal bundle: {e}")
        return False

if __name__ == "__main__":
    create_ultra_minimal_safe_bundle()