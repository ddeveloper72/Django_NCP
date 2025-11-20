"""
Trace pregnancy data flow from FHIR parsing to session storage
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
from patient_data.services.fhir_bundle_parser import FHIRBundleParser

print("=" * 80)
print("TRACING PREGNANCY DATA FLOW")
print("=" * 80)

fhir_service = get_fhir_service()
parser = FHIRBundleParser()
patient_id = "98ce4472-30a5-43b2-8b37-85c86fc53772"

print(f"\n1. Fetching FHIR Bundle...")
result = fhir_service.get_patient_summary(patient_id, requesting_user="trace")

if result and isinstance(result, dict) and 'entry' in result:
    print(f"✅ Bundle retrieved: {result.get('total', 0)} resources\n")
    
    print(f"2. Parsing bundle with FHIRBundleParser...")
    parsed_data = parser.parse_patient_summary_bundle(result)
    
    if parsed_data and parsed_data.get('success'):
        clinical_arrays = parsed_data.get('clinical_arrays', {})
        pregnancy_history = clinical_arrays.get('pregnancy_history', [])
        
        print(f"✅ Parsed successfully\n")
        print(f"📋 Pregnancy History Records: {len(pregnancy_history)}\n")
        print("=" * 80)
        
        for i, record in enumerate(pregnancy_history, 1):
            print(f"\n{i}. Pregnancy Record:")
            print(f"   Type: {record.get('pregnancy_type')}")
            print(f"   Outcome: {record.get('outcome')}")
            print(f"   Outcome Code: {record.get('outcome_code')}")
            print(f"   Delivery Date: {record.get('delivery_date')}")
            print(f"   Delivery Date Raw: {record.get('delivery_date_raw')}")
            print(f"   Status: {record.get('status')}")
            print(f"   Observation Date: {record.get('observation_date')}")
            print(f"   Is Placeholder: {record.get('_is_placeholder', False)}")
            print(f"   Observation ID: {record.get('observation_id')}")
            print(f"   Resource Type: {record.get('resource_type')}")
        
        print("\n" + "=" * 80)
        print("FILTERING BY PREGNANCY TYPE")
        print("=" * 80)
        
        current_pregnancies = [r for r in pregnancy_history if r.get('pregnancy_type') == 'current']
        past_pregnancies = [r for r in pregnancy_history if r.get('pregnancy_type') == 'past']
        
        print(f"\n✅ Current Pregnancies: {len(current_pregnancies)}")
        print(f"✅ Past Pregnancies: {len(past_pregnancies)}")
        
        if past_pregnancies:
            print(f"\nPast Pregnancies Breakdown:")
            livebirths = [r for r in past_pregnancies if r.get('outcome') == 'Livebirth']
            terminations = [r for r in past_pregnancies if r.get('outcome') == 'Termination of pregnancy']
            
            print(f"  - Livebirths: {len(livebirths)}")
            print(f"  - Terminations: {len(terminations)}")
            
            print(f"\nDetailed Past Pregnancies:")
            for i, preg in enumerate(past_pregnancies, 1):
                print(f"\n  {i}. {preg.get('outcome', 'Unknown')} - {preg.get('delivery_date', 'No date')}")
                print(f"     Placeholder: {preg.get('_is_placeholder', False)}")
                print(f"     SNOMED: {preg.get('outcome_code', 'No code')}")
    else:
        print("❌ Parsing failed")
        print(f"Error: {parsed_data.get('error', 'Unknown error')}")
else:
    print("❌ Failed to retrieve FHIR bundle")
