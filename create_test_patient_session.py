#!/usr/bin/env python3
"""
Create Patient Session for Testing
Creates a proper PatientSession record for testing the medication display
"""

import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.contrib.auth.models import User
from patient_data.models import PatientSession
import hashlib

def create_test_patient_session():
    """Create a test PatientSession for our medication testing"""
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'is_active': True
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print("✓ Created test user")
    else:
        print("✓ Test user already exists")
    
    # Create PatientSession with session_id = 9999999999
    session_id = "9999999999"
    
    # Check if session already exists
    if PatientSession.objects.filter(session_id=session_id).exists():
        print(f"✓ PatientSession {session_id} already exists")
        return session_id
    
    # Create new session
    expires_at = timezone.now() + timedelta(hours=24)
    
    patient_session = PatientSession.objects.create(
        session_id=session_id,
        user=user,
        expires_at=expires_at,
        status='active',
        encryption_key_version=1,
        is_active=True,
        country_code='IE',  # Ireland
        search_criteria_hash=hashlib.sha256(f"test_patient_{session_id}".encode()).hexdigest(),
        access_count=0,
        last_action="Created for medication testing",
        client_ip='127.0.0.1',
        user_agent_hash=hashlib.sha256("Test Agent".encode()).hexdigest()
    )
    
    print(f"✓ Created PatientSession: {session_id}")
    print(f"  - User: {user.username}")
    print(f"  - Expires: {expires_at}")
    print(f"  - Status: {patient_session.status}")
    
    return session_id

if __name__ == "__main__":
    session_id = create_test_patient_session()
    print(f"\n🎯 Ready to test! Navigate to: http://localhost:8000/patient_data/cda/{session_id}/")