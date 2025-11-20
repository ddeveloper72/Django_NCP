#!/usr/bin/env python
"""Check what observations are returned by patient search vs composition references"""

import os
import sys
import django

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from eu_ncp_server.services.fhir_service_factory import get_fhir_service

print("=" * 80)
print("COMPARING PATIENT SEARCH VS COMPOSITION REFERENCES")
print("=" * 80)

fhir_service = get_fhir_service()

# Get patient ID
patient_result = fhir_service._make_request('GET', 'Patient?identifier=2-1234-W7')
azure_patient_id = patient_result['entry'][0]['resource']['id']
print(f"\nPatient UUID: {azure_patient_id}")

# Get latest composition
comp_result = fhir_service._make_request('GET', f'Composition?subject=Patient/{azure_patient_id}&_sort=-_lastUpdated&_count=1')
composition = comp_result['entry'][0]['resource']
comp_id = composition['id']
print(f"Composition ID: {comp_id}")

# Extract pregnancy observation IDs from composition
comp_preg_obs_ids = set()
for section in composition.get('section', []):
    code = section.get('code', {}).get('coding', [{}])[0].get('code')
    if code == '10162-6':  # History of Pregnancies
        for entry_ref in section.get('entry', []):
            ref = entry_ref['reference']
            obs_id = ref.split('/')[-1] if '/' in ref else ref
            comp_preg_obs_ids.add(obs_id)

print(f"\nPregnancy observations in composition: {len(comp_preg_obs_ids)}")
for obs_id in comp_preg_obs_ids:
    print(f"  - {obs_id}")

# Get ALL observations by patient search
print(f"\nFetching ALL observations with patient search...")
obs_result = fhir_service._make_request('GET', f'Observation?patient={azure_patient_id}&_sort=-_lastUpdated&_count=100')
all_obs = obs_result.get('entry', [])

print(f"Total observations returned: {len(all_obs)}")

# Filter pregnancy-related observations
pregnancy_codes = ['93857-1', '82810-3', '11778-8', '11636-8', '11612-9']
preg_obs_from_search = []

for entry in all_obs:
    obs = entry['resource']
    obs_id = obs['id']
    code = obs['code']['coding'][0]['code']
    
    if code in pregnancy_codes:
        preg_obs_from_search.append(obs_id)
        in_comp = "✅ IN COMPOSITION" if obs_id in comp_preg_obs_ids else "❌ NOT IN COMPOSITION"
        print(f"  {code}: {obs_id[:8]}... {in_comp}")

print(f"\nPregnancy observations from search: {len(preg_obs_from_search)}")
print(f"Expected from composition: {len(comp_preg_obs_ids)}")

# Check if composition observations are accessible
print(f"\nChecking composition references directly...")
missing_count = 0
for obs_id in comp_preg_obs_ids:
    try:
        obs = fhir_service._make_request('GET', f'Observation/{obs_id}')
        code = obs['code']['coding'][0]['code']
        display = obs['code']['coding'][0].get('display', 'Unknown')
        print(f"  ✅ {obs_id[:8]}...: {code} - {display}")
    except Exception as e:
        print(f"  ❌ {obs_id[:8]}...: ERROR - {e}")
        missing_count += 1

if missing_count == 0:
    print(f"\n✅ All {len(comp_preg_obs_ids)} composition references are accessible!")
else:
    print(f"\n❌ {missing_count} composition references are broken!")

print("=" * 80)
