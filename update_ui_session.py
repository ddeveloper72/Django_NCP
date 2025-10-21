#!/usr/bin/env python3
"""
Debug Current UI Session - Check what the actual UI session contains
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
import json

def debug_ui_session():
    """Debug the actual UI session to understand the data structure"""
    
    print("🔍 Debugging UI Session Data...")
    print("=" * 50)
    
    # Get the UI session
    session_key = "mgndqphov2r1vkz2asp5s0v1j5wjl112"
    
    try:
        session = Session.objects.get(session_key=session_key)
        print(f"✅ Found UI session: {session.session_key}")
        
        # Decode session data
        session_data = session.get_decoded()
        
        print(f"\n📋 UI Session Data Keys: {list(session_data.keys())}")
        
        # Look for patient data
        if 'patient_match_1703098729' in session_data:
            patient_data = session_data['patient_match_1703098729']
            print(f"\n👤 Patient Data Type: {type(patient_data)}")
            
            if isinstance(patient_data, dict):
                print(f"   Patient Data Keys: {list(patient_data.keys())}")
                
                # Look for clinical data or medications
                for key, value in patient_data.items():
                    print(f"   • {key}: {type(value).__name__}")
                    if 'clinical' in key.lower() or 'medication' in key.lower():
                        print(f"     → {key} contains: {str(value)[:200]}...")
            
        print(f"\n💡 The UI session doesn't contain our enhanced medication data!")
        print(f"   We need to inject the enhanced data into the existing session structure.")
        
    except Session.DoesNotExist:
        print(f"❌ UI session {session_key} not found")

def update_ui_session_with_enhanced_data():
    """Update the UI session with our enhanced medication data"""
    
    print(f"\n🔧 Updating UI Session with Enhanced Data...")
    print("=" * 50)
    
    # Get our Portuguese session data
    portuguese_session_key = "xr3aymrr6c5hvmkh075qcvnkcfk6nvf6" 
    ui_session_key = "mgndqphov2r1vkz2asp5s0v1j5wjl112"
    
    try:
        # Get both sessions
        portuguese_session = Session.objects.get(session_key=portuguese_session_key)
        ui_session = Session.objects.get(session_key=ui_session_key)
        
        # Get the enhanced medication data
        portuguese_data = portuguese_session.get_decoded()
        enhanced_medications = portuguese_data.get('enhanced_medications', [])
        
        # Get the UI session data
        ui_data = ui_session.get_decoded()
        
        # Inject enhanced medications into UI session
        ui_data['enhanced_medications'] = enhanced_medications
        ui_data['medication_count'] = len(enhanced_medications)
        ui_data['has_enhanced_data'] = True
        ui_data['enhanced_data_source'] = 'portuguese_cda_parser'
        
        # Save updated UI session
        ui_session.session_data = ui_session.encode(ui_data)
        ui_session.save()
        
        print(f"✅ Updated UI session with {len(enhanced_medications)} enhanced medications")
        print(f"   Enhanced medications from Portuguese CDA now available in UI session")
        
        # Verify the update
        updated_ui_data = ui_session.get_decoded()
        if 'enhanced_medications' in updated_ui_data:
            print(f"✅ Verification: Enhanced medications successfully added to UI session")
            print(f"   First medication: {updated_ui_data['enhanced_medications'][0]['name']}")
        
    except Session.DoesNotExist as e:
        print(f"❌ Session not found: {e}")

if __name__ == "__main__":
    debug_ui_session()
    update_ui_session_with_enhanced_data()