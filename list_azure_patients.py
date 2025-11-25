#!/usr/bin/env python
"""
List all patients in Azure FHIR to find Patrick Murphy
"""

import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from eu_ncp_server.services.azure_fhir_integration import AzureFHIRIntegrationService

def list_all_patients():
    """List all patients in Azure FHIR"""
    
    print("=" * 80)
    print("ALL PATIENTS IN AZURE FHIR")
    print("=" * 80)
    
    service = AzureFHIRIntegrationService()
    
    try:
        # Fetch all patients (limit 100)
        patient_search = service._make_request('GET', 'Patient', params={'_count': '100'})
        
        if not patient_search or not patient_search.get('entry'):
            print("   ❌ No patients found")
            return
        
        entries = patient_search['entry']
        print(f"\n✅ Found {len(entries)} patient(s)")
        print(f"{'='*80}\n")
        
        for idx, entry in enumerate(entries, 1):
            resource = entry['resource']
            patient_id = resource.get('id')
            
            # Get name
            names = resource.get('name', [])
            if names:
                name = names[0]
                given = ' '.join(name.get('given', []))
                family = name.get('family', '')
                full_name = f"{given} {family}".strip()
            else:
                full_name = "NO NAME"
            
            # Get identifiers
            identifiers = resource.get('identifier', [])
            identifier_list = []
            for ident in identifiers:
                value = ident.get('value', 'NO VALUE')
                system = ident.get('system', 'NO SYSTEM')
                identifier_list.append(f"{value} ({system})")
            
            # Get birth date
            birth_date = resource.get('birthDate', 'UNKNOWN')
            
            # Get country from address
            country = "UNKNOWN"
            addresses = resource.get('address', [])
            if addresses:
                country = addresses[0].get('country', 'UNKNOWN')
            
            print(f"{idx}. {full_name}")
            print(f"   Azure ID: {patient_id}")
            print(f"   Country: {country}")
            print(f"   Birth Date: {birth_date}")
            if identifier_list:
                print(f"   Identifiers:")
                for ident in identifier_list:
                    print(f"      - {ident}")
            print()
        
        print(f"{'='*80}")
        print("PATIENT LIST COMPLETE")
        print(f"{'='*80}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    list_all_patients()
