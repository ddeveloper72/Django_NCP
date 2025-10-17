import os
import sys
import django

# Setup Django
project_root = os.path.dirname(os.path.abspath('.'))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.messages import get_messages
from patient_data.views import patient_details_view
import logging

# Disable logging for cleaner output
logging.disable(logging.CRITICAL)

def simulate_patient_details_view():
    # Create a mock request
    factory = RequestFactory()
    request = factory.get('/patient/2-1234-W7/')
    request.user = AnonymousUser()
    
    # Add session middleware
    middleware = SessionMiddleware(lambda r: None)
    middleware.process_request(request)
    request.session.save()
    
    # Add messages middleware
    messages_middleware = MessageMiddleware(lambda r: None)
    messages_middleware.process_request(request)
    
    print("SIMULATING PATIENT DETAILS VIEW FOR DIANA (2-1234-W7)")
    print("=" * 60)
    
    try:
        # Call the view
        response = patient_details_view(request, '2-1234-W7')
        
        if hasattr(response, 'context_data'):
            context = response.context_data
        elif hasattr(response, 'context'):
            context = response.context
        else:
            # For redirect responses, try to get context from the response
            print(f"Response type: {type(response)}")
            if hasattr(response, 'url'):
                print(f"Redirect URL: {response.url}")
            return
            
        print(f"Response status: {response.status_code if hasattr(response, 'status_code') else 'unknown'}")
        
        # Check for medications in context
        if 'medications' in context:
            medications = context['medications']
            print(f"\nMEDICATIONS IN CONTEXT:")
            print(f"  Count: {len(medications)}")
            print(f"  Type: {type(medications)}")
            
            if medications:
                print(f"\nFIRST MEDICATION:")
                first_med = medications[0]
                for key, value in first_med.items():
                    if key == 'data' and isinstance(value, dict):
                        print(f"  {key}:")
                        for data_key, data_value in value.items():
                            print(f"    {data_key}: {data_value}")
                    else:
                        print(f"  {key}: {value}")
            
            print(f"\nALL MEDICATION NAMES:")
            for i, med in enumerate(medications, 1):
                name = med.get('medication_name') or med.get('name') or med.get('display_name', 'Unknown')
                dose = med.get('data', {}).get('dose_quantity', 'No dose')
                print(f"  {i}. {name} - {dose}")
        else:
            print("\nNO MEDICATIONS IN CONTEXT")
            print("Available context keys:", list(context.keys()))
            
        # Check for patient data
        if 'patient_data' in context:
            patient = context['patient_data']
            print(f"\nPATIENT DATA:")
            print(f"  Name: {getattr(patient, 'given_name', 'Unknown')} {getattr(patient, 'family_name', 'Unknown')}")
            print(f"  Has CDA Match: {context.get('has_cda_match', False)}")
        
        # Check for messages
        messages = get_messages(request)
        if messages:
            print(f"\nMESSAGES:")
            for message in messages:
                print(f"  {message.level_tag}: {message}")
                
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simulate_patient_details_view()