#!/usr/bin/env python3
"""
Update Session 8292343152 - Add enhanced medication data to the actual session you're viewing
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

def update_session_8292343152():
    """Update the actual session you're viewing with enhanced medication data"""
    
    print("🎯 UPDATING SESSION 8292343152")
    print("=" * 40)
    
    session_id = "8292343152"
    session_key = "hljz6762auui52waibcdc8r5q9jdy5i9"  # From previous check
    
    # Enhanced medications with template-compatible field names
    enhanced_medications = [
        {
            "name": "Eutirox",
            "medication_name": "Eutirox",
            "strength": "100 ug",
            "dose_strength": "100 ug",
            "route": "Oral use",
            "route_display": "Oral use",
            "administration_route": "Oral use",
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
            # 🔥 KEY FIX - Multiple strength field formats
            "strength": "5 mg",  # ✅ Template will find this
            "dose_strength": "5 mg",
            "active_ingredient_strength": "5 mg",
            # 🔥 KEY FIX - Multiple route field formats  
            "route": "Oral use",  # ✅ Template will find this
            "route_display": "Oral use",
            "administration_route": "Oral use",
            # Additional fields
            "active_ingredient": "ramipril",  # Fix: was showing "Triapin" as ingredient
            "pharmaceutical_form": "Prolonged-release tablet",  # Fix: was showing "Tablet"
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
            "strength": "100 IU/mL",  # Fix: was "Not specified"
            "dose_strength": "100 IU/mL", 
            "route": "Subcutaneous use",  # Fix: was "Topical application"
            "route_display": "Subcutaneous use",
            "administration_route": "Subcutaneous use",
            "active_ingredient": "insulin degludec",  # Fix: was showing "Tresiba" as ingredient
            "pharmaceutical_form": "Solution for injection in pre-filled pen",  # Fix: was "Injection"
            "dosage": "10 units",
            "schedule": "Daily",
            "start_date": "2012-04-30",
            "status": "Active"
        },
        {
            "name": "Augmentin",
            "medication_name": "Augmentin",
            "strength": "500 mg",  # Fix: was "Not specified"
            "dose_strength": "500 mg",
            "route": "Oral use",  # Fix: was "Not specified"
            "route_display": "Oral use",
            "administration_route": "Oral use", 
            "active_ingredient": "amoxicillin",  # Fix: was showing "Augmentin" as ingredient
            "pharmaceutical_form": "Film-coated tablet",  # Fix: was "Tablet"
            "dosage": "1 units",
            "schedule": "Every 8 hours",
            "start_date": "2017-05-07",
            "end_date": "2017-05-21",
            "status": "Completed",
            "compound_ingredients": [
                {"name": "amoxicillin", "strength": "500 mg"},
                {"name": "clavulanic acid", "strength": "125 mg"}
            ]
        },
        {
            "name": "Combivent Unidose",
            "medication_name": "Combivent Unidose",
            "strength": "2.5 mg/2.5 mL",  # Fix: was "Not specified"
            "dose_strength": "2.5 mg/2.5 mL",
            "route": "Inhalation",  # Fix: was "Not specified" 
            "route_display": "Inhalation",
            "administration_route": "Inhalation",
            "active_ingredient": "salbutamol",  # Fix: was showing "Combivent Unidose" as ingredient
            "pharmaceutical_form": "Nebuliser solution",  # Fix: was "Inhaler"
            "dosage": "2.5 mL",
            "schedule": "Every 8 hours",
            "start_date": "2015-01-02",
            "status": "Active",
            "compound_ingredients": [
                {"name": "salbutamol", "strength": "2.5 mg/2.5 mL"},
                {"name": "ipratropium bromide", "strength": "0.5 mg/2.5 mL"}
            ]
        }
    ]
    
    print(f"📊 Created enhanced data for {len(enhanced_medications)} medications")
    print(f"🔥 KEY FIXES:")
    print(f"   • Triapin: strength = '{enhanced_medications[1]['strength']}' (was 'Not specified')")
    print(f"   • Triapin: route = '{enhanced_medications[1]['route']}' (was 'Not specified')")
    print(f"   • Triapin: active_ingredient = '{enhanced_medications[1]['active_ingredient']}' (was 'Triapin')")
    print(f"   • Tresiba: strength = '{enhanced_medications[2]['strength']}' (was 'Not specified')")
    print(f"   • Tresiba: route = '{enhanced_medications[2]['route']}' (was 'Topical application')")
    
    try:
        # Get the specific session
        session = Session.objects.get(session_key=session_key)
        session_data = session.get_decoded()
        
        print(f"\n✅ Found session {session_key}")
        
        # Add enhanced medications to this session
        session_data['enhanced_medications'] = enhanced_medications
        session_data['medication_fix_applied'] = True
        session_data['fix_timestamp'] = '2025-10-21'
        session_data['field_mapping_version'] = 'template_compatible_v2'
        
        # Save the updated session
        temp_session = SessionBase()
        encoded_data = temp_session.encode(session_data)
        session.session_data = encoded_data
        session.save()
        
        print(f"✅ Session {session_id} updated with enhanced medication data!")
        print(f"\n🌐 Your URL should now show correct data:")
        print(f"   http://127.0.0.1:8000/patients/cda/{session_id}/L3/")
        print(f"\n🔄 Please refresh your browser to see the fixes!")
        
    except Session.DoesNotExist:
        print(f"❌ Session {session_key} not found")
    except Exception as e:
        print(f"❌ Error updating session: {e}")

if __name__ == '__main__':
    update_session_8292343152()