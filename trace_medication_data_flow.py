#!/usr/bin/env python3
"""
Trace the exact data flow from backend to template for Diana's medication active ingredients
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from patient_data.services.comprehensive_clinical_data_service import ComprehensiveClinicalDataService
from patient_data.models import PatientData
import logging

print("=== MEDICATION DATA FLOW TRACE ===")
print()

# Configure logging to see all internal logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Get Diana's patient record
    patient_id = "2482633793"
    patient = PatientData.objects.filter(patient_identifier=patient_id).first()
    if not patient:
        print(f"❌ Patient {patient_id} not found")
        sys.exit(1)
    print(f"✅ Found patient: {patient_id}")
    print()
    
    # Create comprehensive service
    service = ComprehensiveClinicalDataService()
    
    print("🔍 Step 1: Extract clinical data...")
    clinical_data = service.extract_comprehensive_clinical_data(patient)
    print(f"   Clinical data keys: {list(clinical_data.keys())}")
    print()
    
    print("🔍 Step 2: Check medications in clinical_data...")
    if 'medications' in clinical_data:
        medications = clinical_data['medications']
        print(f"   Medications count: {len(medications)}")
        print()
        
        for i, med in enumerate(medications, 1):
            print(f"   📍 Medication #{i}:")
            print(f"      Name: {med.get('name', med.get('medication_name', 'Unknown'))}")
            print(f"      Active Ingredients: {med.get('active_ingredients', 'Not found')}")
            print(f"      Type: {type(med.get('active_ingredients'))}")
            
            # Check if it's a DotDict with .coded access
            active_ing = med.get('active_ingredients')
            if hasattr(active_ing, 'coded'):
                print(f"      active_ingredients.coded: {active_ing.coded}")
            elif isinstance(active_ing, dict) and 'coded' in active_ing:
                print(f"      active_ingredients['coded']: {active_ing['coded']}")
            else:
                print(f"      Active ingredients structure: {active_ing}")
            print()
    else:
        print("   ❌ No medications found in clinical_data")
        print()
    
    print("🔍 Step 3: Check clinical arrays...")
    clinical_arrays = service.get_clinical_arrays(patient)
    print(f"   Clinical arrays keys: {list(clinical_arrays.keys())}")
    
    if 'medications' in clinical_arrays:
        array_medications = clinical_arrays['medications']
        print(f"   Array medications count: {len(array_medications)}")
        print()
        
        for i, med in enumerate(array_medications, 1):
            print(f"   📍 Array Medication #{i}:")
            print(f"      Name: {med.get('name', med.get('medication_name', 'Unknown'))}")
            print(f"      Active Ingredients: {med.get('active_ingredients', 'Not found')}")
            
            # Check template access patterns
            active_ing = med.get('active_ingredients')
            if hasattr(active_ing, 'coded'):
                print(f"      ✅ med.active_ingredients.coded: {active_ing.coded}")
            elif isinstance(active_ing, dict) and 'coded' in active_ing:
                print(f"      ✅ med.active_ingredients['coded']: {active_ing['coded']}")
            else:
                print(f"      ❌ Cannot access .coded: {active_ing}")
            print()
    else:
        print("   ❌ No medications found in clinical_arrays")
        print()
    
    print("🎯 SUMMARY:")
    print(f"   Backend extracted: {len(medications) if 'medications' in clinical_data else 0} medications")
    print(f"   Clinical arrays: {len(array_medications) if 'medications' in clinical_arrays else 0} medications")
    print(f"   Browser displays: 3 medications with 'Not specified' active ingredients")
    print()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("=== TRACE COMPLETE ===")