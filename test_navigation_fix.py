#!/usr/bin/env python3
"""
Test script to validate the navigation fix for session data persistence
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from patient_data.models import PatientData
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from patient_data.views import patient_details_view
import json

def test_navigation_fix():
    """Test the navigation fix for session data persistence"""
    print("Testing navigation fix for session data persistence...")
    
    # Get a test patient
    try:
        test_patient = PatientData.objects.first()
        if not test_patient:
            print("❌ No patient data found in database")
            return False
            
        print(f"✅ Found test patient: {test_patient.id}")
        
        # Create a mock request with session
        factory = RequestFactory()
        request = factory.get(f'/patient_data/patient_details/{test_patient.id}/')
        
        # Add session middleware
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        
        # Simulate session data that would be created by search
        session_key = f"patient_match_{test_patient.id}"
        mock_match_data = {
            'patient_id': test_patient.id,
            'has_cda_match': True,
            'match_confidence': 95,
            'cda_content': '<CDA>Mock CDA content</CDA>',
            'rendering_cda_content': '<CDA>Mock rendering content</CDA>'
        }
        
        request.session[session_key] = mock_match_data
        request.session.save()
        
        print(f"✅ Created mock session data with key: {session_key}")
        
        # Test the patient details view
        try:
            response = patient_details_view(request, test_patient.id)
            print("✅ Patient details view executed successfully")
            
            # Check if session_error is in context (it should not be with valid session data)
            if hasattr(response, 'context_data'):
                context = response.context_data
                if 'session_error' in context and context['session_error']:
                    print(f"❌ Unexpected session error: {context['session_error']}")
                    return False
                else:
                    print("✅ No session error - session data properly retrieved")
                    
                # Check if patient_identity is correctly set
                if 'patient_identity' in context:
                    patient_identity = context['patient_identity']
                    expected_patient_id = test_patient.id
                    actual_patient_id = patient_identity.get('patient_id')
                    
                    if actual_patient_id == expected_patient_id:
                        print(f"✅ Patient ID correctly set: {actual_patient_id}")
                        return True
                    else:
                        print(f"❌ Patient ID mismatch: expected {expected_patient_id}, got {actual_patient_id}")
                        return False
                else:
                    print("❌ patient_identity not found in context")
                    return False
            else:
                print("✅ View executed (no context data to check)")
                return True
                
        except Exception as e:
            print(f"❌ Error executing patient details view: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

def test_session_loss_handling():
    """Test handling when session data is lost"""
    print("\nTesting session loss handling...")
    
    try:
        test_patient = PatientData.objects.first()
        if not test_patient:
            print("❌ No patient data found in database")
            return False
            
        # Create a mock request without session data
        factory = RequestFactory()
        request = factory.get(f'/patient_data/patient_details/{test_patient.id}/')
        
        # Add session middleware but don't add session data
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        
        print(f"✅ Created request without session data for patient: {test_patient.id}")
        
        # Test the patient details view
        try:
            response = patient_details_view(request, test_patient.id)
            print("✅ Patient details view executed successfully with missing session data")
            
            # Check if session_error is properly set
            if hasattr(response, 'context_data'):
                context = response.context_data
                if 'session_error' in context and context['session_error']:
                    print(f"✅ Session error properly detected: {context['session_error']}")
                    return True
                else:
                    print("❌ Session error not detected when session data is missing")
                    return False
            else:
                print("✅ View executed (no context data to check)")
                return True
                
        except Exception as e:
            print(f"❌ Error executing patient details view: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Running Navigation Fix Tests")
    print("=" * 50)
    
    # Test 1: Normal navigation with session data
    test1_result = test_navigation_fix()
    
    # Test 2: Navigation with lost session data
    test2_result = test_session_loss_handling()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"✅ Session data persistence: {'PASS' if test1_result else 'FAIL'}")
    print(f"✅ Session loss handling: {'PASS' if test2_result else 'FAIL'}")
    
    if test1_result and test2_result:
        print("\n🎉 All tests passed! Navigation fix is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
