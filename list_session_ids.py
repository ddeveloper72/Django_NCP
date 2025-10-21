#!/usr/bin/env python3
"""
Simple script to list available session IDs.
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.insert(0, '/c/Users/Duncan/VS_Code_Projects/django_ncp')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from patient_data.models import PatientSession

def list_sessions():
    """List available session IDs."""
    print("🔍 Available Patient Sessions:")
    print("=" * 40)
    
    sessions = PatientSession.objects.all()[:20]  # Limit to first 20
    
    for session in sessions:
        print(f"Session ID: {session.session_id}")
        print(f"User: {session.user}")
        print(f"Status: {session.status}")
        print(f"Created: {session.created_at}")
        print("-" * 30)

if __name__ == "__main__":
    list_sessions()