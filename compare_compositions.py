"""
Compare compositions to find which one has all 5 pregnancy observations
"""
import os
import sys
import django

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from eu_ncp_server.services.fhir_service_factory import get_fhir_service
import json

print("=" * 80)
print("COMPARING COMPOSITIONS FOR DIANA")
print("=" * 80)

fhir_service = get_fhir_service()

# Search for all compositions for Diana
print("\nSearching for all Compositions with subject=Patient/2-1234-W7...")
result = fhir_service._make_request(
    'GET',
    f'Composition?subject=Patient/2-1234-W7'
)

if result and result.get('entry'):
    compositions = [entry['resource'] for entry in result['entry']]
    print(f"✅ Found {len(compositions)} Composition(s)\n")
    print("=" * 80)
    
    for i, comp in enumerate(compositions, 1):
        comp_id = comp.get('id')
        comp_date = comp.get('date')
        comp_status = comp.get('status')
        comp_title = comp.get('title', 'No title')
        
        print(f"\nComposition #{i}:")
        print(f"  ID: {comp_id}")
        print(f"  Date: {comp_date}")
        print(f"  Status: {comp_status}")
        print(f"  Title: {comp_title}")
        
        # Get sections
        sections = comp.get('section', [])
        print(f"  Sections: {len(sections)}")
        
        # Check for pregnancy-related sections
        pregnancy_entries = []
        for section in sections:
            section_code = section.get('code', {}).get('coding', [{}])[0].get('code', '')
            section_title = section.get('title', 'Unknown')
            entries = section.get('entry', [])
            
            # Check if this is pregnancy-related
            if any(keyword in section_title.lower() for keyword in ['pregnan', 'obstet', 'history of pregnan']):
                print(f"\n  📋 Pregnancy Section: {section_title} (Code: {section_code})")
                print(f"     Entries: {len(entries)}")
                
                for entry in entries:
                    ref = entry.get('reference', '')
                    if 'Observation' in ref:
                        obs_id = ref.split('/')[-1]
                        pregnancy_entries.append(obs_id)
                        print(f"     - {ref}")
        
        if pregnancy_entries:
            print(f"\n  ✅ This composition has {len(pregnancy_entries)} pregnancy observation references")
            
            # Now fetch each observation to see what it is
            print(f"\n  🔍 Checking what these observations are...")
            for obs_id in pregnancy_entries:
                try:
                    obs = fhir_service._make_request('GET', f'Observation/{obs_id}')
                    if obs:
                        code = obs.get('code', {}).get('coding', [{}])[0]
                        loinc_code = code.get('code', 'Unknown')
                        display = code.get('display', 'Unknown')
                        print(f"     {obs_id}: {loinc_code} - {display}")
                except Exception as e:
                    print(f"     {obs_id}: ERROR - {e}")
        else:
            print(f"\n  ⚠️ This composition has NO pregnancy observation references")
    
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    
    # Expected pregnancy observation IDs from our inspection
    expected_obs_ids = [
        '9374cc95-6bba-49a9-8a7d-9ed3d1544166',  # 93857-1 Termination
        '4890feba-2c4b-4129-bae9-2496fcfedff1',  # 11612-9 Abortions count
        'ec975220-bf9c-4e42-b4a1-4360489a0b1a',  # 11636-8 Live births count
        '16e323bc-e55e-449b-a772-020d79f6bea6',  # 82810-3 Pregnancy status
        'f96b572b-542d-41c9-9574-9834e3b26c6c',  # 11778-8 Estimated delivery
    ]
    
    print(f"\n📊 Expected Pregnancy Observations (from direct query):")
    for obs_id in expected_obs_ids:
        print(f"   - {obs_id}")
    
    print(f"\n🔍 Checking which composition references these...")
    for i, comp in enumerate(compositions, 1):
        comp_id = comp.get('id')
        sections = comp.get('section', [])
        
        found_obs = []
        for section in sections:
            for entry in section.get('entry', []):
                ref = entry.get('reference', '')
                if 'Observation' in ref:
                    obs_id = ref.split('/')[-1]
                    if obs_id in expected_obs_ids:
                        found_obs.append(obs_id)
        
        print(f"\n   Composition {i} ({comp_id}):")
        print(f"      Date: {comp.get('date')}")
        print(f"      Found {len(found_obs)} of 5 expected pregnancy observations")
        if found_obs:
            print(f"      IDs: {found_obs}")
    
else:
    print("❌ No compositions found")

print("\n" + "=" * 80)
print("CHECK COMPLETE")
print("=" * 80)
