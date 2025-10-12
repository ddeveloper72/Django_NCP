#!/usr/bin/env python3
"""
Reload FHIR Bundle for Testing Healthcare Provider

This script loads the FHIR bundle directly and stores it in a Django session
for testing the healthcare provider fallback logic.
"""

import sys
import os
import json

# Add Django project to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
import django
django.setup()

from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
from patient_data.services.fhir_agent_service import FHIRAgentService

def reload_fhir_bundle():
    """Reload FHIR bundle and test healthcare provider extraction"""
    print("🔄 RELOADING FHIR BUNDLE FOR TESTING")
    print("=" * 60)
    
    session_id = "6816436119"
    
    # Load the FHIR bundle from file
    bundle_path = "test_data/eu_member_states/IE/combined_fhir_bundle_ULTRA_SAFE.json"
    
    try:
        with open(bundle_path, 'r', encoding='utf-8') as f:
            fhir_bundle_data = json.load(f)
        
        print(f"✅ Loaded FHIR bundle from {bundle_path}")
        
        # Process with FHIR Agent Service
        fhir_agent = FHIRAgentService()
        context_data = fhir_agent.extract_patient_context_data(fhir_bundle_data, session_id)
        
        print(f"✅ Processed with FHIR Agent Service")
        
        # Create new Django session
        session = SessionStore()
        session_key = f"patient_match_{session_id}"
        
        # Store the processed data - just the basic data that can be serialized
        session[session_key] = {
            'data_source': 'FHIR',
            'fhir_bundle': fhir_bundle_data,
            'patient_identity': context_data.get('patient_identity', {}),
            'timestamp': '2025-10-12T10:20:00Z'
        }
        
        session.save()
        
        print(f"✅ Stored session data with key: {session.session_key}")
        print(f"📋 Session ID for browser: {session.session_key}")
        
        # Test healthcare provider extraction
        healthcare_data = context_data.get('healthcare_data', {})
        print(f"\n🏥 HEALTHCARE PROVIDER TEST RESULTS:")
        print(f"  Practitioners: {len(healthcare_data.get('practitioners', []))}")
        print(f"  Organizations: {len(healthcare_data.get('organizations', []))}")
        print(f"  Healthcare Team: {len(healthcare_data.get('healthcare_team', []))}")
        
        practitioners = healthcare_data.get('practitioners', [])
        if practitioners:
            print(f"\n👨‍⚕️ PRACTITIONER DETAILS:")
            for i, practitioner in enumerate(practitioners):
                print(f"    {i+1}. {practitioner.get('name', 'Unknown')}")
                print(f"       Source: {practitioner.get('source', 'standard')}")
                if practitioner.get('qualification'):
                    for qual in practitioner['qualification']:
                        print(f"       Qualification: {qual.get('text', 'Unknown')}")
        
        print(f"\n🌐 URL to test: http://127.0.0.1:8000/patients/cda/{session_id}/l3/")
        
    except Exception as e:
        print(f"❌ Error reloading FHIR bundle: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reload_fhir_bundle()