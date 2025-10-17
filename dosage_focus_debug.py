#!/usr/bin/env python3
"""
Focus on Dosage Field Mapping
"""

import os
import sys
import django

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from patient_data.services.comprehensive_clinical_data_service import ComprehensiveClinicalDataService
from patient_data.services.cda_parser_service import CDAParserService
import xml.etree.ElementTree as ET
import logging

# Enable debug logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("FOCUS ON DOSAGE FIELD MAPPING")
print("=" * 40)

# Test with Diana CDA file directly
cda_file_path = "test_data/eu_member_states/PT/2-1234-W7.xml"

try:
    with open(cda_file_path, 'r', encoding='utf-8') as f:
        cda_content = f.read()
    
    print(f"CDA file loaded: {len(cda_content)} chars")
    
    # Create service instance  
    service = ComprehensiveClinicalDataService()
    
    # Use the manual process to get medications directly
    cda_parser = CDAParserService()
    parsed_data = cda_parser.parse_cda_document(cda_content)
    
    # Get medications using the correct methods
    cda_parser.root = ET.fromstring(cda_content)
    structured_body = cda_parser._extract_structured_body()
    cda_medications = structured_body.get("medications", [])
    
    print(f"CDA Parser extracted {len(cda_medications)} medications")
    
    if cda_medications:
        med = cda_medications[0]
        print(f"\nFIRST MEDICATION ANALYSIS:")
        print(f"  Type: {type(med)}")
        
        # Check current doseQuantity
        print(f"\n  ORIGINAL DOSAGE DATA:")
        if hasattr(med, 'doseQuantity'):
            print(f"    doseQuantity (attr): {med.doseQuantity}")
        elif isinstance(med, dict) and 'doseQuantity' in med:
            print(f"    doseQuantity (dict): {med['doseQuantity']}")
        else:
            print(f"    doseQuantity: NOT FOUND")
        
        # Show all attributes with 'dose' or 'quantity'
        print(f"\n  ALL DOSE/QUANTITY ATTRIBUTES:")
        found_dose_attrs = []
        if hasattr(med, '__dict__'):
            for attr in med.__dict__:
                if 'dose' in attr.lower() or 'quantity' in attr.lower():
                    found_dose_attrs.append((attr, getattr(med, attr)))
        elif isinstance(med, dict):
            for key in med:
                if 'dose' in key.lower() or 'quantity' in key.lower():
                    found_dose_attrs.append((key, med[key]))
        
        if found_dose_attrs:
            for attr, value in found_dose_attrs:
                print(f"    {attr}: {value}")
        else:
            print(f"    No dose/quantity attributes found")
        
        # Show first 10 attributes
        print(f"\n  FIRST 10 ATTRIBUTES:")
        if hasattr(med, '__dict__'):
            for i, (attr, value) in enumerate(med.__dict__.items()):
                if i >= 10:
                    print(f"    ... (showing first 10 of {len(med.__dict__)} total)")
                    break
                print(f"    {attr}: {str(value)[:100]}")
        elif isinstance(med, dict):
            for i, (key, value) in enumerate(med.items()):
                if i >= 10:
                    print(f"    ... (showing first 10 of {len(med)} total)")
                    break
                print(f"    {key}: {str(value)[:100]}")
        
        # Test the compatibility function directly
        print(f"\n  TESTING COMPATIBILITY FUNCTION:")
        
        print(f"  Before fix:")
        if hasattr(med, 'dose_quantity'):
            print(f"    dose_quantity exists: {med.dose_quantity}")
        else:
            print(f"    dose_quantity: NOT FOUND")
        
        # Apply the dosage fix
        service._fix_dosage_field_compatibility(med)
        
        print(f"  After dosage fix:")
        if hasattr(med, 'dose_quantity'):
            print(f"    dose_quantity created: {med.dose_quantity}")
        elif isinstance(med, dict) and 'dose_quantity' in med:
            print(f"    dose_quantity (dict): {med['dose_quantity']}")
        else:
            print(f"    dose_quantity: STILL NOT FOUND")
        
        # Also test schedule fix
        print(f"\n  TESTING SCHEDULE FIX:")
        service._fix_schedule_field_compatibility(med)
        
        if hasattr(med, 'schedule'):
            print(f"    schedule created: {med.schedule}")
        elif isinstance(med, dict) and 'schedule' in med:
            print(f"    schedule (dict): {med['schedule']}")
        else:
            print(f"    schedule: NOT FOUND")
        
        # Show final state
        print(f"\n  FINAL MEDICATION STATE:")
        target_fields = ['dose_quantity', 'route', 'schedule']
        for field in target_fields:
            if hasattr(med, field):
                value = getattr(med, field)
                print(f"    {field}: {value}")
            elif isinstance(med, dict) and field in med:
                value = med[field]
                print(f"    {field} (dict): {value}")
            else:
                print(f"    {field}: NOT FOUND")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\nDOSAGE FOCUS COMPLETE")