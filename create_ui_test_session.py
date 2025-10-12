#!/usr/bin/env python3
"""
Fixed Browser Test Session Creator
==================================

This script creates a properly structured test session that matches what the 
Django view expects, then provides a URL to test emergency contact rendering.
"""

import os
import sys
import django
from datetime import datetime

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.contrib.sessions.backends.db import SessionStore
from patient_data.services.fhir_bundle_parser import FHIRBundleParser

def create_working_test_session():
    """Create a test session with the complete data structure the view expects"""
    
    print("=== Creating Working Test Session for Emergency Contact UI ===\n")
    
    test_session_id = "ui_test_" + str(int(datetime.now().timestamp()))
    
    # Create FHIR bundle similar to working sessions
    fhir_bundle = {
        'resourceType': 'Bundle',
        'id': 'ui-test-bundle',
        'type': 'document',
        'timestamp': datetime.now().isoformat() + 'Z',
        'entry': [
            {
                'fullUrl': 'urn:uuid:composition-1',
                'resource': {
                    'resourceType': 'Composition',
                    'id': 'composition-1',
                    'status': 'final',
                    'type': {
                        'coding': [{
                            'system': 'http://loinc.org',
                            'code': '60591-5',
                            'display': 'Patient Summary Document'
                        }]
                    },
                    'subject': {'reference': 'urn:uuid:patient-test'},
                    'date': datetime.now().isoformat() + 'Z',
                    'author': [{'display': 'Test Healthcare Provider'}],
                    'title': 'Patient Summary - UI Test'
                }
            },
            {
                'fullUrl': 'urn:uuid:patient-test',
                'resource': {
                    'resourceType': 'Patient',
                    'id': 'patient-test',
                    'identifier': [{
                        'system': 'urn:oid:1.2.372.980010.1.2',
                        'value': test_session_id
                    }],
                    'name': [{'given': ['UI'], 'family': 'TestPatient'}],
                    'telecom': [{'system': 'phone', 'value': '+353-87-1111111'}],
                    'address': [{
                        'line': ['123 Test Street'],
                        'city': 'Test City',
                        'postalCode': '12345',
                        'country': 'Ireland'
                    }],
                    'gender': 'male',
                    'birthDate': '1990-01-01'
                }
            },
            {
                'fullUrl': 'urn:uuid:emergency-mary',
                'resource': {
                    'resourceType': 'RelatedPerson',
                    'id': 'emergency-mary',
                    'patient': {'reference': 'urn:uuid:patient-test'},
                    'relationship': [{'text': 'Emergency Contact'}],
                    'name': [{'given': ['Mary'], 'family': 'UITestContact'}],
                    'telecom': [
                        {'system': 'phone', 'value': '+353-87-9999999'},
                        {'system': 'email', 'value': 'mary.ui.test@example.ie'}
                    ],
                    'address': [{
                        'line': ['456 Emergency Avenue'],
                        'city': 'Dublin',
                        'country': 'Ireland'
                    }],
                    'gender': 'female'
                }
            }
        ]
    }
    
    # Parse FHIR bundle
    parser = FHIRBundleParser()
    parsed_data = parser.parse_patient_summary_bundle(fhir_bundle)
    
    # Verify guardian was created
    guardian = parsed_data.get('administrative_data', {}).get('guardian')
    if not guardian:
        print("❌ Failed to create guardian from emergency contact")
        return None
    
    print(f"✅ Guardian created: {guardian.get('given_name')} {guardian.get('family_name')}")
    print(f"✅ Relationship: {guardian.get('relationship')}")
    
    # Create session with COMPLETE data structure matching working sessions
    session_store = SessionStore()
    session_store.create()
    
    # Build the session data structure that the view expects
    session_data = {
        # FHIR parsed data (what we want to test)
        'patient_identity': parsed_data.get('patient_identity', {}),
        'administrative_data': parsed_data.get('administrative_data', {}),
        'contact_data': parsed_data.get('contact_data', {}),
        'healthcare_data': parsed_data.get('healthcare_data', {}),
        'clinical_sections': parsed_data.get('clinical_sections', {}),
        'fhir_bundle_data': fhir_bundle,
        
        # REQUIRED: Patient match data that view expects
        f'patient_match_{test_session_id}': {
            'session_id': test_session_id,
            'patient_name': 'UI TestPatient',
            'source_country': 'IE',
            'timestamp': datetime.now().isoformat(),
            'patient_id': test_session_id,
            'status': 'active'
        },
        
        # REQUIRED: Patient info structure that view looks for
        'patient_info': {
            'patient_id': test_session_id,
            'given_name': 'UI',
            'family_name': 'TestPatient',
            'birth_date': '1990-01-01',
            'gender': 'male',
            'source_country': 'IE',
            'identifiers': [{'system': 'urn:oid:1.2.372.980010.1.2', 'value': test_session_id}],
            'addresses': [{'line': ['123 Test Street'], 'city': 'Test City', 'country': 'Ireland'}],
            'telecoms': [{'system': 'phone', 'value': '+353-87-1111111'}]
        },
        
        # Session management
        'patient_last_activity': datetime.now().isoformat(),
        'session_created': datetime.now().isoformat(),
        'active_patient_sessions': [test_session_id]
    }
    
    # Save all session data
    for key, value in session_data.items():
        session_store[key] = value
    
    session_store.save()
    
    test_url = f'http://127.0.0.1:8000/patients/cda/{test_session_id}/L3/'
    
    print(f"✅ Test session created: {session_store.session_key}")
    print(f"✅ Session ID: {test_session_id}")
    print(f"✅ Test URL: {test_url}")
    
    return {
        'session_key': session_store.session_key,
        'session_id': test_session_id,
        'url': test_url,
        'guardian': guardian
    }

def main():
    """Create working test session and provide testing instructions"""
    
    print("🚀 Creating Working Browser Test Session for Emergency Contact UI")
    print("=" * 80)
    
    session_info = create_working_test_session()
    
    if not session_info:
        print("❌ Failed to create test session")
        return False
    
    guardian = session_info['guardian']
    
    print("\n=== Test Information ===")
    print(f"URL: {session_info['url']}")
    print(f"Expected Guardian: {guardian.get('given_name')} {guardian.get('family_name')}")
    print(f"Expected Relationship: {guardian.get('relationship')}")
    print(f"Expected Phone: {guardian.get('contact_info', {}).get('telecoms', [{}])[0].get('value', 'N/A')}")
    
    print("\n📋 Manual Testing Steps:")
    print("1. Open the URL above in your browser")
    print("2. Look for the 'Extended Patient Information' tab")
    print("3. Click on the tab to open the extended view")
    print("4. Scroll to find 'Guardian/Next of Kin' section")
    print("5. Verify emergency contact information appears correctly")
    
    print("\n🎯 Success Criteria:")
    print("✓ Guardian section should be visible (not 'No guardian information')")
    print("✓ Name should show: Mary UITestContact")
    print("✓ Relationship should show: Emergency Contact")
    print("✓ Phone should show: +353-87-9999999")
    print("✓ Contact information should be properly formatted")
    
    print("\n🔧 For Autonomous Testing:")
    print("- This session contains properly structured data")
    print("- Emergency contact should display as guardian in UI")
    print("- Can be used to test template changes automatically")
    print("- Reproduces the complete user workflow")
    
    return True

if __name__ == "__main__":
    main()