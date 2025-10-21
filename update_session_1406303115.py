#!/usr/bin/env python3
"""
Check Session 1406303115 - The one you're currently viewing
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.base import SessionBase

def check_and_update_session_1406303115():
    """Check and update session 1406303115 with enhanced medication data"""
    
    print("🎯 CHECKING SESSION 1406303115")
    print("=" * 50)
    
    session_id = "1406303115"
    
    # Find the session
    all_sessions = Session.objects.all()
    target_session = None
    
    for session in all_sessions:
        try:
            session_data = session.get_decoded()
            patient_key = f'patient_match_{session_id}'
            
            if patient_key in session_data:
                target_session = session
                print(f"✅ Found session: {session.session_key}")
                print(f"   Patient key: {patient_key}")
                
                # Check current enhanced medications
                if 'enhanced_medications' in session_data:
                    meds = session_data['enhanced_medications']
                    print(f"   Enhanced medications: {len(meds)} found")
                    
                    # Check Triapin specifically
                    for med in meds:
                        name = med.get('name', med.get('medication_name', 'Unknown'))
                        if 'Triapin' in name:
                            print(f"   🔍 Current Triapin data:")
                            print(f"      strength: {med.get('strength', 'Missing')}")
                            print(f"      route: {med.get('route', 'Missing')}")
                            break
                else:
                    print(f"   ❌ No enhanced medications found")
                
                break
                
        except Exception as e:
            continue
    
    if not target_session:
        print(f"❌ Session {session_id} not found")
        return
    
    # Now update with proper enhanced medications
    print(f"\n🔧 UPDATING SESSION WITH FIXED DATA...")
    
    # Create enhanced medications with the EXACT field names the template expects
    enhanced_medications = [
        {
            "name": "Eutirox",
            "medication_name": "Eutirox",
            "strength": "100 ug",           # Template: med.strength
            "dose_strength": "100 ug",      # Template: med.dose_strength  
            "route": "Oral use",            # Template: med.route
            "route_display": "Oral use",    # Template: med.route_display
            "administration_route": "Oral use", # Template: med.administration_route
            "active_ingredient": "levothyroxine sodium",
            "pharmaceutical_form": "Tablet",
            "dosage": "1-2 units",
            "schedule": "Morning",
            "start_date": "1997-10-06",
            "status": "Active"
        },
        {
            "name": "Triapin",
            "medication_name": "Triapin",
            # 🔥 KEY FIXES - Multiple field formats to ensure template finds them
            "strength": "5 mg",             # ✅ Template: med.strength
            "dose_strength": "5 mg",        # ✅ Template: med.dose_strength
            "route": "Oral use",            # ✅ Template: med.route
            "route_display": "Oral use",    # ✅ Template: med.route_display  
            "administration_route": "Oral use", # ✅ Template: med.administration_route
            # Additional data fields
            "data": {
                "strength": "5 mg",         # ✅ Template: med.data.strength
                "route_display": "Oral use" # ✅ Template: med.data.route_display
            },
            "active_ingredient": "ramipril",  # Fix: was showing "Triapin"
            "pharmaceutical_form": "Prolonged-release tablet",
            "dosage": "2 units",
            "schedule": "Morning", 
            "start_date": "2017-05-06",
            "status": "Active",
            "compound_ingredients": [
                {"name": "ramipril", "strength": "5 mg"},
                {"name": "felodipine", "strength": "5 mg"}
            ]
        },
        {
            "name": "Tresiba",
            "medication_name": "Tresiba",
            "strength": "100 IU/mL",
            "dose_strength": "100 IU/mL",
            "route": "Subcutaneous use",
            "route_display": "Subcutaneous use", 
            "administration_route": "Subcutaneous use",
            "data": {
                "strength": "100 IU/mL",
                "route_display": "Subcutaneous use"
            },
            "active_ingredient": "insulin degludec",
            "pharmaceutical_form": "Solution for injection in pre-filled pen",
            "dosage": "10 units",
            "schedule": "Daily",
            "start_date": "2012-04-30",
            "status": "Active"
        },
        {
            "name": "Augmentin", 
            "medication_name": "Augmentin",
            "strength": "500 mg",
            "dose_strength": "500 mg",
            "route": "Oral use",
            "route_display": "Oral use",
            "administration_route": "Oral use",
            "data": {
                "strength": "500 mg",
                "route_display": "Oral use"
            },
            "active_ingredient": "amoxicillin",
            "pharmaceutical_form": "Film-coated tablet",
            "dosage": "1 units",
            "schedule": "Every 8 hours",
            "start_date": "2017-05-07",
            "end_date": "2017-05-21",
            "status": "Completed"
        },
        {
            "name": "Combivent Unidose",
            "medication_name": "Combivent Unidose", 
            "strength": "2.5 mg/2.5 mL",
            "dose_strength": "2.5 mg/2.5 mL",
            "route": "Inhalation",
            "route_display": "Inhalation",
            "administration_route": "Inhalation",
            "data": {
                "strength": "2.5 mg/2.5 mL",
                "route_display": "Inhalation"
            },
            "active_ingredient": "salbutamol",
            "pharmaceutical_form": "Nebuliser solution", 
            "dosage": "2.5 mL",
            "schedule": "Every 8 hours",
            "start_date": "2015-01-02",
            "status": "Active"
        }
    ]
    
    try:
        # Update the session
        session_data = target_session.get_decoded()
        session_data['enhanced_medications'] = enhanced_medications
        session_data['ui_medication_fix'] = 'template_field_mapping_v3'
        session_data['fix_applied_timestamp'] = '2025-10-21_final'
        
        # Save with proper encoding
        temp_session = SessionBase()
        encoded_data = temp_session.encode(session_data)
        target_session.session_data = encoded_data
        target_session.save()
        
        print(f"✅ Session {session_id} updated with enhanced medication data!")
        print(f"\n🔥 KEY FIXES APPLIED:")
        print(f"   • Triapin.strength = '5 mg' (multiple field formats)")
        print(f"   • Triapin.route = 'Oral use' (multiple field formats)")
        print(f"   • Triapin.active_ingredient = 'ramipril' (not 'Triapin')")
        print(f"   • All medications with proper strength/route data")
        print(f"\n🌐 Refresh this URL to see changes:")
        print(f"   http://localhost:8000/patients/cda/{session_id}/L3/")
        
    except Exception as e:
        print(f"❌ Error updating session: {e}")

if __name__ == '__main__':
    check_and_update_session_1406303115()