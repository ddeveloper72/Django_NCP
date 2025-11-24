"""
Inspect all Observation resources for patient Diana Ferreira to understand what clinical data exists
"""
import os
import sys
import django

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from eu_ncp_server.services.azure_fhir_integration import AzureFHIRIntegrationService

def inspect_observations():
    """Query Azure FHIR for all observations for Diana Ferreira"""
    service = AzureFHIRIntegrationService()
    
    # Search for patient to get Azure ID
    patient_search = service.search_patients({"identifier": "2-1234-W7"})
    if not patient_search or patient_search.get('total', 0) == 0:
        print("❌ Patient not found")
        return
    
    azure_patient_id = patient_search['entry'][0]['resource']['id']
    print(f"✅ Found patient Azure ID: {azure_patient_id}\n")
    
    # Query all observations for this patient
    observations = service.get_observations(azure_patient_id)
    
    if not observations or observations.get('total', 0) == 0:
        print("❌ No observations found")
        return
    
    print(f"📊 Found {observations.get('total', 0)} Observation(s)\n")
    print("=" * 80)
    
    # Group observations by category
    categories = {}
    
    for entry in observations.get('entry', []):
        obs = entry['resource']
        obs_id = obs.get('id')
        
        # Extract observation code
        code_obj = obs.get('code', {})
        coding = code_obj.get('coding', [{}])[0]
        code = coding.get('code', 'Unknown')
        display = coding.get('display', code)
        text = code_obj.get('text', '')
        
        # Extract category
        categories_list = obs.get('category', [])
        category = 'Uncategorized'
        if categories_list:
            cat_coding = categories_list[0].get('coding', [{}])[0]
            category = cat_coding.get('display', cat_coding.get('code', 'Uncategorized'))
        
        # Extract value
        value_display = 'No value'
        if obs.get('valueQuantity'):
            vq = obs['valueQuantity']
            value_display = f"{vq.get('value')} {vq.get('unit', '')}"
        elif obs.get('valueCodeableConcept'):
            vcc = obs['valueCodeableConcept']
            vcc_coding = vcc.get('coding', [{}])[0]
            value_display = vcc_coding.get('display', vcc.get('text', 'Unknown'))
        elif obs.get('valueString'):
            value_display = obs['valueString']
        elif obs.get('valueBoolean') is not None:
            value_display = str(obs['valueBoolean'])
        
        # Extract date
        effective_date = obs.get('effectiveDateTime', obs.get('effectivePeriod', {}).get('start', 'Unknown date'))
        
        # Group by category
        if category not in categories:
            categories[category] = []
        
        categories[category].append({
            'id': obs_id,
            'code': code,
            'display': display,
            'text': text,
            'value': value_display,
            'date': effective_date
        })
    
    # Print grouped observations
    for category, obs_list in categories.items():
        print(f"\n📋 {category} ({len(obs_list)} observations)")
        print("-" * 80)
        for obs in obs_list:
            print(f"  ID: {obs['id']}")
            print(f"  Code: {obs['code']}")
            print(f"  Display: {obs['display']}")
            if obs['text']:
                print(f"  Text: {obs['text']}")
            print(f"  Value: {obs['value']}")
            print(f"  Date: {obs['date']}")
            print()

if __name__ == '__main__':
    print("🔍 Inspecting Observations for Diana Ferreira (2-1234-W7)\n")
    inspect_observations()
