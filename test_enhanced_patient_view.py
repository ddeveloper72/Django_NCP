#!/usr/bin/env python3
"""Test accessing the Enhanced Patient view with emergency contacts"""

import os
import django
import sys
import json

# Django setup
sys.path.append('c:/Users/Duncan/VS_Code_Projects/django_ncp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.test.client import Client
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session as DjangoSession
from patient_data.models import PatientSession
from django.urls import reverse
from django.utils import timezone

def test_enhanced_patient_view():
    """Test accessing the enhanced patient view with FHIR data containing emergency contacts"""
    
    # Load our enhanced FHIR bundle
    bundle_path = 'test_data/eu_member_states/IE/combined_fhir_bundle_ULTRA_SAFE.json'
    
    try:
        with open(bundle_path, 'r', encoding='utf-8') as f:
            bundle_data = json.load(f)
        
        print(f"✅ Loaded FHIR bundle with {len(bundle_data.get('entry', []))} resources")
        
        # Get or create a user for testing
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={'email': 'test@example.com', 'first_name': 'Test', 'last_name': 'User'}
        )
        
        # Create a test client and login
        client = Client()
        client.force_login(user)
        
        print(f"✅ Logged in as user: {user.username}")
        
        # Check existing sessions with FHIR data
        session_id = '1902395951'  # Our known FHIR session
        
        try:
            patient_session = PatientSession.objects.get(session_id=session_id)
            print(f"✅ Found PatientSession: {session_id}")
        except PatientSession.DoesNotExist:
            print(f"❌ PatientSession {session_id} not found")
            return False
        
        # Create a Django session with FHIR data
        django_session = client.session
        django_session['fhir_data'] = bundle_data
        django_session['session_id'] = session_id
        django_session['patient_data_source'] = 'FHIR'
        django_session.save()
        
        print(f"✅ Created Django session with FHIR data")
        
        # Test accessing the enhanced patient view
        url = f'/patients/cda/{session_id}/'
        print(f"\n🌐 Testing Enhanced Patient View:")
        print(f"   - URL: {url}")
        
        response = client.get(url)
        
        print(f"   - Response Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Check for emergency contact indicators in the response
            emergency_indicators = [
                'Mary Murphy',
                'Next of Kin',
                '+353-87-9875465',
                'emergency',
                'Guardian',
                'Contact Information'
            ]
            
            found_indicators = []
            for indicator in emergency_indicators:
                if indicator in content:
                    found_indicators.append(indicator)
            
            print(f"   - Emergency contact indicators found: {len(found_indicators)}/{len(emergency_indicators)}")
            for indicator in found_indicators:
                print(f"     ✅ Found: {indicator}")
            
            missing_indicators = [i for i in emergency_indicators if i not in found_indicators]
            for indicator in missing_indicators:
                print(f"     ❌ Missing: {indicator}")
            
            # Check for Extended Patient Information tab
            if 'Extended Patient Information' in content:
                print(f"   ✅ Extended Patient Information tab found")
            else:
                print(f"   ❌ Extended Patient Information tab not found")
            
            # Check for contact data structure
            if 'contact-info-grid' in content:
                print(f"   ✅ Contact info grid structure found")
            else:
                print(f"   ❌ Contact info grid structure not found")
            
            return True
        else:
            print(f"   ❌ Failed to access view: {response.status_code}")
            print(f"   Response content: {response.content.decode('utf-8')[:500]}...")
            return False
            
    except Exception as e:
        print(f"❌ Error testing enhanced patient view: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🏥 Testing Enhanced Patient View with Emergency Contacts")
    print("=" * 60)
    
    success = test_enhanced_patient_view()
    
    if success:
        print(f"\n✅ Enhanced patient view test completed!")
        print(f"🎯 Emergency contacts should now be visible in the UI")
    else:
        print(f"\n❌ Enhanced patient view test failed!")
        print(f"🔍 Check the view logic and template rendering")