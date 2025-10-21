#!/usr/bin/env python
"""
Test to examine actual medication data structure being sent to templates
"""

import os
import sys
import django
import json

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from patient_data.services.comprehensive_clinical_data_service import ComprehensiveClinicalDataService

def examine_medication_structure():
    """Examine the exact medication data structure sent to templates"""
    print("="*60)
    print("EXAMINING MEDICATION DATA STRUCTURE FOR TEMPLATES")
    print("="*60)
    
    clinical_service = ComprehensiveClinicalDataService()
    
    # Sample medication data as it would come from CDA
    sample_medication_data = {
        'active_ingredient_code': 'H03AA01',
        'active_ingredient_code_system': '2.16.840.1.113883.6.73',
        'active_ingredient_display': 'levothyroxine sodium',
        'medication_name': 'Euthyrox',
        'dose_quantity': {
            'value': '100',
            'unit': 'ug'
        },
        'pharmaceutical_form': 'Tablet'
    }
    
    print(f"🔍 Processing medication data...")
    print(f"Input: {sample_medication_data['medication_name']}")
    print(f"Ingredient Code: {sample_medication_data['active_ingredient_code']}")
    print()
    
    # Process through comprehensive clinical data service
    result = clinical_service._convert_valueset_fields_to_medication_data(sample_medication_data)
    
    print(f"📋 RESULTING DATA STRUCTURE:")
    print("-" * 40)
    
    # Print key fields that templates expect
    print(f"medication_name: {result.get('medication_name', 'NOT SET')}")
    print(f"name: {result.get('name', 'NOT SET')}")
    print(f"display_name: {result.get('display_name', 'NOT SET')}")
    print()
    
    print(f"INGREDIENT FIELDS:")
    print(f"ingredient_code: {result.get('ingredient_code', 'NOT SET')}")
    print(f"ingredient_display: {result.get('ingredient_display', 'NOT SET')}")
    print()
    
    print(f"ACTIVE_INGREDIENT (singular) object:")
    active_ingredient = result.get('active_ingredient', {})
    if active_ingredient:
        print(f"  active_ingredient.code: {active_ingredient.get('code', 'NOT SET')}")
        print(f"  active_ingredient.coded: {active_ingredient.get('coded', 'NOT SET')}")  # THIS IS KEY
        print(f"  active_ingredient.display_name: {active_ingredient.get('display_name', 'NOT SET')}")
    else:
        print(f"  active_ingredient: NOT SET")
    print()
    
    print(f"ACTIVE_INGREDIENTS (plural) object:")
    active_ingredients = result.get('active_ingredients', {})
    if active_ingredients:
        print(f"  active_ingredients.code: {active_ingredients.get('code', 'NOT SET')}")
        print(f"  active_ingredients.coded: {active_ingredients.get('coded', 'NOT SET')}")  # TEMPLATE EXPECTS THIS
        print(f"  active_ingredients.display_name: {active_ingredients.get('display_name', 'NOT SET')}")
    else:
        print(f"  active_ingredients: NOT SET")
    print()
    
    print(f"🎯 TEMPLATE EXPECTATIONS:")
    print(f"Template looks for: item.active_ingredients.coded")
    print(f"We provide: item.active_ingredient.coded")
    print(f"Solution: Add active_ingredients field OR update template")
    print()
    
    print(f"📱 MOBILE TEMPLATE CODE DISPLAY:")
    # Simulate template access
    template_code_field = active_ingredients.get('coded') if active_ingredients else active_ingredient.get('coded', 'NOT AVAILABLE')
    print(f"Current template shows: 'Code: {template_code_field}'")
    
    if template_code_field == 'H03AA01':
        print(f"✅ SUCCESS: Would show actual CTS code!")
    elif template_code_field == 'NOT AVAILABLE':
        print(f"❌ ISSUE: Template can't find the coded field")
    else:
        print(f"❌ ISSUE: Showing {template_code_field} instead of H03AA01")

if __name__ == "__main__":
    examine_medication_structure()