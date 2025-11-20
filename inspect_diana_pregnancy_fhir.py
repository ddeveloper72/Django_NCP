"""
Inspect Diana's FHIR Pregnancy Observations from Azure
"""
import os
import sys
import django
import json

# Fix Unicode encoding issues on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from eu_ncp_server.services.fhir_service_factory import get_fhir_service

print("=" * 80)
print("DIANA'S FHIR PREGNANCY OBSERVATIONS")
print("=" * 80)

fhir_service = get_fhir_service()
patient_id = "98ce4472-30a5-43b2-8b37-85c86fc53772"

print(f"\n1. Fetching FHIR Bundle for Diana...")
result = fhir_service.get_patient_summary(patient_id, requesting_user="inspection")

if result and isinstance(result, dict) and 'entry' in result:
    print(f"✅ Bundle retrieved: {result.get('total', 0)} resources\n")
    
    # Find all Observation resources
    observations = []
    for entry in result.get('entry', []):
        resource = entry.get('resource', {})
        if resource.get('resourceType') == 'Observation':
            observations.append(resource)
    
    print(f"📋 Total Observations: {len(observations)}\n")
    
    # Filter pregnancy-related observations
    pregnancy_codes = ['93857-1', '11636-8', '11612-9', '82810-3', '11778-8', 
                       '281050002', '57797005', '49051-6', '11884-4']
    
    pregnancy_obs = []
    for obs in observations:
        code = obs.get('code', {})
        coding_list = code.get('coding', [])
        
        for coding in coding_list:
            obs_code = coding.get('code', '')
            if obs_code in pregnancy_codes:
                pregnancy_obs.append(obs)
                break
    
    print(f"🤰 Pregnancy-Related Observations: {len(pregnancy_obs)}\n")
    print("=" * 80)
    
    for i, obs in enumerate(pregnancy_obs, 1):
        print(f"\n{i}. Observation ID: {obs.get('id')}")
        
        # Code
        code = obs.get('code', {})
        coding_list = code.get('coding', [])
        if coding_list:
            coding = coding_list[0]
            print(f"   Code: {coding.get('code')} ({coding.get('display', 'No display')})")
            print(f"   System: {coding.get('system', 'No system')}")
        
        # Value
        if 'valueQuantity' in obs:
            value_qty = obs['valueQuantity']
            print(f"   Value: {value_qty.get('value')} {value_qty.get('unit', '')}")
        elif 'valueCodeableConcept' in obs:
            value_cc = obs['valueCodeableConcept']
            value_coding = value_cc.get('coding', [{}])[0]
            print(f"   ValueCodeableConcept: {value_coding.get('display', 'No display')}")
            print(f"   ValueCode: {value_coding.get('code', 'No code')}")
        elif 'valueDateTime' in obs:
            print(f"   ValueDateTime: {obs['valueDateTime']}")
        elif 'valueString' in obs:
            print(f"   ValueString: {obs['valueString']}")
        
        # Effective date
        if 'effectiveDateTime' in obs:
            print(f"   EffectiveDateTime: {obs['effectiveDateTime']}")
        
        # Status
        print(f"   Status: {obs.get('status', 'unknown')}")
        
        print("   " + "-" * 76)
    
    print("\n" + "=" * 80)
    print("DETAILED JSON OF PREGNANCY OBSERVATIONS")
    print("=" * 80)
    
    for i, obs in enumerate(pregnancy_obs, 1):
        print(f"\n{'=' * 80}")
        print(f"Observation #{i}")
        print(f"{'=' * 80}")
        print(json.dumps(obs, indent=2))

else:
    print("❌ Failed to retrieve FHIR bundle")
