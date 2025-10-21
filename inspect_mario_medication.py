#!/usr/bin/env python
"""
Inspect medication data structure from Mario Pino session
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from patient_data.services.comprehensive_clinical_data_service import ComprehensiveClinicalDataService
from patient_data.models import PatientDataCache

def inspect_mario_medication_data():
    """Inspect the medication data structure for Mario Pino"""
    
    # Get Mario Pino's session
    try:
        # List all available sessions first
        all_sessions = PatientDataCache.objects.all()[:5]
        print(f"📋 Available sessions ({PatientDataCache.objects.count()} total):")
        for session in all_sessions:
            print(f"   - {session.session_id} | {session.cache_key} | {session.data_type}")
        
        # Try to find Mario session by looking for recent sessions
        mario_session = PatientDataCache.objects.filter(
            data_type='CDA'
        ).order_by('-last_accessed').first()
        
        if not mario_session:
            print("❌ No CDA session found")
            return
            
        print(f"✅ Found session: {mario_session.session_id}")
        print(f"   Cache key: {mario_session.cache_key}")
        print(f"   Data type: {mario_session.data_type}")
        
        # Extract clinical data
        service = ComprehensiveClinicalDataService()
        # Get the CDA content from the encrypted field
        cda_content = mario_session.get_decrypted_content()
        clinical_arrays = service.get_clinical_arrays_for_display(cda_content)
        
        print(f"\n📊 CLINICAL DATA EXTRACTED:")
        print(f"   Medications: {len(clinical_arrays['medications'])}")
        
        if clinical_arrays['medications']:
            print(f"\n💊 FIRST MEDICATION DATA STRUCTURE:")
            med = clinical_arrays['medications'][0]
            
            print(f"\n🔍 TOP-LEVEL KEYS:")
            for key in sorted(med.keys()):
                value = med[key]
                if isinstance(value, dict):
                    print(f"   {key}: {type(value).__name__} with {len(value)} keys")
                elif isinstance(value, list):
                    print(f"   {key}: {type(value).__name__} with {len(value)} items")
                else:
                    print(f"   {key}: {repr(value)}")
            
            # Inspect data sub-object if it exists
            if 'data' in med and isinstance(med['data'], dict):
                print(f"\n🔍 DATA SUB-OBJECT KEYS:")
                for key in sorted(med['data'].keys()):
                    value = med['data'][key]
                    if isinstance(value, dict):
                        print(f"   data.{key}: {type(value).__name__} with {len(value)} keys")
                    elif isinstance(value, list):
                        print(f"   data.{key}: {type(value).__name__} with {len(value)} items")
                    else:
                        print(f"   data.{key}: {repr(value)}")
            
            # Look for CDA-specific structures
            cda_fields = [
                'statusCode', 'doseQuantity', 'routeCode', 'entryRelationship',
                'manufactured_material', 'medication', 'dose'
            ]
            
            print(f"\n🔍 CDA-SPECIFIC FIELDS:")
            for field in cda_fields:
                if field in med:
                    value = med[field]
                    if isinstance(value, dict):
                        print(f"   {field}: {type(value).__name__}")
                        # Show sub-keys for dict values
                        for subkey in sorted(value.keys()):
                            subvalue = value[subkey]
                            print(f"     └─ {subkey}: {repr(subvalue) if not isinstance(subvalue, dict) else f'{type(subvalue).__name__} with {len(subvalue)} keys'}")
                    else:
                        print(f"   {field}: {repr(value)}")
                else:
                    print(f"   {field}: NOT_FOUND")
                    
    except Exception as e:
        print(f"❌ Error inspecting medication data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    inspect_mario_medication_data()