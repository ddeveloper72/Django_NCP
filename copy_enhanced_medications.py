#!/usr/bin/env python3
"""
Copy enhanced medication data from the Portuguese session to the active UI session.
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/mnt/c/Users/Duncan/VS_Code_Projects/django_ncp')

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
import json
from datetime import datetime

def copy_enhanced_medications():
    """Copy enhanced medications from Portuguese session to UI session."""
    
    # Source session with enhanced medications
    source_session_key = "xr3aymrr6c5hvmkh075qcvnkcfk6nvf6"
    
    # Target UI session
    target_session_key = "mgndqphov2r1vkz2asp5s0v1j5wjl112"
    
    print(f"🔄 Copying enhanced medications from {source_session_key} to {target_session_key}")
    
    try:
        # Get source session data
        source_store = SessionStore(session_key=source_session_key)
        source_data = source_store.load()
        
        if not source_data:
            print("❌ Source session not found or empty")
            return False
            
        enhanced_medications = source_data.get('enhanced_medications')
        if not enhanced_medications:
            print("❌ No enhanced_medications found in source session")
            return False
            
        print(f"✅ Found {len(enhanced_medications)} enhanced medications in source session")
        
        # Get target session data
        target_store = SessionStore(session_key=target_session_key)
        target_data = target_store.load()
        
        if not target_data:
            print("❌ Target session not found or empty")
            return False
            
        print(f"📊 Target session keys: {list(target_data.keys())}")
        
        # Add enhanced medications to target session
        target_data['enhanced_medications'] = enhanced_medications
        
        # Save the target session
        target_store.update(target_data)
        target_store.save()
        
        print("✅ Enhanced medications copied successfully!")
        
        # Verify the copy
        verification_store = SessionStore(session_key=target_session_key)
        verification_data = verification_store.load()
        
        if 'enhanced_medications' in verification_data:
            copied_meds = verification_data['enhanced_medications']
            print(f"✅ Verification successful: {len(copied_meds)} medications in target session")
            
            # Show sample medication
            if copied_meds:
                sample_med = copied_meds[0]
                print(f"📋 Sample medication: {sample_med.get('medication_name', 'Unknown')}")
                print(f"   - Dose: {sample_med.get('dose_quantity', 'N/A')}")
                print(f"   - Route: {sample_med.get('route', 'N/A')}")
                print(f"   - Schedule: {sample_med.get('schedule', 'N/A')}")
            
            return True
        else:
            print("❌ Verification failed: enhanced_medications not found in target session")
            return False
            
    except Exception as e:
        print(f"❌ Error copying enhanced medications: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = copy_enhanced_medications()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Enhanced medications copy operation")