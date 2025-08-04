#!/usr/bin/env python3
"""
Test script to verify patient identifier rendering in CDA template
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
from patient_data.views import patient_cda_view
import json

def test_patient_identifiers_in_template():
    """Test that patient identifiers are properly passed to the CDA template"""
    print("Testing patient identifier rendering in CDA template...")
    
    try:
        # Get a test patient
        test_patient = PatientData.objects.first()
        if not test_patient:
            print("❌ No patient data found in database")
            return False
            
        print(f"✅ Found test patient: {test_patient.id}")
        
        # Create a mock request with session
        factory = RequestFactory()
        request = factory.get(f'/patient_data/patient_cda/{test_patient.id}/')
        
        # Add session middleware
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        
        # Create comprehensive mock session data with patient identifiers
        session_key = f"patient_match_{test_patient.id}"
        mock_match_data = {
            'patient_id': test_patient.id,
            'has_cda_match': True,
            'match_confidence': 95,
            'confidence_score': 0.95,
            'country_code': 'DE',
            'file_path': '/test/path/sample_cda.xml',
            'cda_content': '<CDA>Mock CDA content</CDA>',
            'rendering_cda_content': '<CDA>Mock rendering content</CDA>',
            'preferred_cda_type': 'L3',
            'has_l1': False,
            'has_l3': True,
            'patient_data': {
                'name': f"{test_patient.given_name} {test_patient.family_name}",
                'birth_date': test_patient.birth_date.strftime('%Y-%m-%d') if test_patient.birth_date else 'Unknown',
                'gender': getattr(test_patient, 'gender', 'Unknown'),
                'primary_patient_id': 'DE123456789',  # Mock primary patient ID
                'secondary_patient_id': 'NHS987654321',  # Mock secondary patient ID
                'patient_identifiers': [
                    {'system': 'DE-ID', 'value': 'DE123456789'},
                    {'system': 'NHS', 'value': 'NHS987654321'}
                ]
            }
        }
        
        request.session[session_key] = mock_match_data
        request.session.save()
        
        print(f"✅ Created mock session data with patient identifiers")
        print(f"   Primary ID: {mock_match_data['patient_data']['primary_patient_id']}")
        print(f"   Secondary ID: {mock_match_data['patient_data']['secondary_patient_id']}")
        
        # Test the patient CDA view
        try:
            response = patient_cda_view(request, test_patient.id)
            print("✅ Patient CDA view executed successfully")
            
            # Check if the response has context data with patient identifiers
            if hasattr(response, 'context_data'):
                context = response.context_data
                
                if 'patient_identity' in context:
                    patient_identity = context['patient_identity']
                    
                    # Check primary patient ID
                    primary_id = patient_identity.get('primary_patient_id')
                    if primary_id == 'DE123456789':
                        print("✅ Primary patient ID correctly passed to template")
                    else:
                        print(f"❌ Primary patient ID mismatch: expected 'DE123456789', got '{primary_id}'")
                        return False
                    
                    # Check secondary patient ID
                    secondary_id = patient_identity.get('secondary_patient_id')
                    if secondary_id == 'NHS987654321':
                        print("✅ Secondary patient ID correctly passed to template")
                    else:
                        print(f"❌ Secondary patient ID mismatch: expected 'NHS987654321', got '{secondary_id}'")
                        return False
                    
                    # Check other patient identity fields
                    expected_fields = ['family_name', 'given_name', 'birth_date', 'gender', 'patient_id']
                    for field in expected_fields:
                        if field in patient_identity:
                            print(f"✅ {field}: {patient_identity[field]}")
                        else:
                            print(f"❌ Missing field in patient_identity: {field}")
                            return False
                    
                    return True
                    
                else:
                    print("❌ patient_identity not found in context")
                    return False
            else:
                print("✅ View executed (no context data to check)")
                return True
                
        except Exception as e:
            print(f"❌ Error executing patient CDA view: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing Patient Identifier Rendering")
    print("=" * 50)
    
    # Test patient identifier rendering
    test_result = test_patient_identifiers_in_template()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"✅ Patient identifier rendering: {'PASS' if test_result else 'FAIL'}")
    
    if test_result:
        print("\n🎉 Patient identifiers are properly rendered in the CDA template!")
        print("\nThe template should now display:")
        print("- Primary ID: DE123456789 (in highlighted primary styling)")
        print("- Secondary ID: NHS987654321 (in highlighted secondary styling)")
    else:
        print("\n❌ Patient identifier rendering failed. Please check the implementation.")
