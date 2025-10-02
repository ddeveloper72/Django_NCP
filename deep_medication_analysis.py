#!/usr/bin/env python3
"""
Deep Medication Object Analysis
Check the exact structure of converted medication objects
"""

import os
import sys
import django
import json
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from patient_data.services.comprehensive_clinical_data_service import ComprehensiveClinicalDataService

def analyze_medication_objects():
    """Analyze the exact structure of medication objects after conversion"""
    
    print("=== Deep Medication Object Analysis ===\n")
    
    service = ComprehensiveClinicalDataService()
    cda_file_path = "test_data/eu_member_states/PT/2-1234-W7.xml"
    
    with open(cda_file_path, 'r', encoding='utf-8') as f:
        cda_content = f.read()
        
    print(f"✅ Processing CDA file: {len(cda_content)} characters")
    
    # Get clinical arrays for display
    clinical_arrays = service.get_clinical_arrays_for_display(cda_content)
    medications = clinical_arrays.get('medications', [])
    print(f"💊 Found {len(medications)} medication objects for display")
    
    # Analyze each medication object
    for i, med in enumerate(medications, 1):
        print(f"\n🔍 Medication Object #{i}:")
        print(f"   Type: {type(med)}")
        
        if isinstance(med, dict):
            print(f"   Dictionary with keys: {list(med.keys())}")
            
            # Check for name fields
            possible_name_fields = ['name', 'medication_name', 'substance_name']
            for field in possible_name_fields:
                if field in med:
                    print(f"   ✅ {field}: {med[field]}")
                    
            # Check data substructure
            if 'data' in med:
                data = med['data']
                print(f"   Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                
                # Look for Triapin specifically
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, str) and 'triapin' in value.lower():
                            print(f"   🎯 FOUND TRIAPIN in data.{key}: {value}")
                        elif key in ['medication_name', 'substance_name', 'name']:
                            print(f"   Name field data.{key}: {value}")
                            
            # Check medication substructure
            if 'medication' in med:
                medication = med['medication']
                print(f"   Medication keys: {list(medication.keys()) if isinstance(medication, dict) else 'Not a dict'}")
                if isinstance(medication, dict) and 'name' in medication:
                    print(f"   ✅ medication.name: {medication['name']}")
                    
            # Print full structure for first few meds
            if i <= 2:
                print(f"   Full JSON structure:")
                print(f"   {json.dumps(med, indent=4, default=str)}")
        else:
            print(f"   Not a dictionary: {med}")
            # Check if it's an object with attributes
            if hasattr(med, '__dict__'):
                print(f"   Object attributes: {list(vars(med).keys())}")
                for attr in ['name', 'medication_name', 'substance_name']:
                    if hasattr(med, attr):
                        value = getattr(med, attr)
                        print(f"   ✅ {attr}: {value}")

if __name__ == "__main__":
    analyze_medication_objects()