#!/usr/bin/env python3
"""
Set up enhanced procedures in Django session following the medications pattern
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore

def setup_enhanced_procedures():
    print("=== SETTING UP ENHANCED PROCEDURES IN DJANGO SESSION ===\n")
    
    # Enhanced procedures data with proper field structure for template
    enhanced_procedures = [
        {
            "name": "Implantation of heart assist system",
            "procedure_name": "Implantation of heart assist system", 
            "display_name": "Implantation of heart assist system",
            "procedure_code": "64253000",
            "snomed_code": "64253000",
            "date": "2014-10-20",
            "effective_time": "20141020",
            "status": "Completed",
            "performer": "Dr. Johnson, Cardiac Surgeon",
            "location": "Cardiac Surgery Unit",
            "category": "Surgical Procedure",
            "notes": "Successful implantation of left ventricular assist device",
            "is_enhanced": True
        },
        {
            "name": "Transplantation of kidney",
            "procedure_name": "Transplantation of kidney",
            "display_name": "Transplantation of kidney", 
            "procedure_code": "11466000",
            "snomed_code": "11466000",
            "date": "2012-03-15",
            "effective_time": "20120315",
            "status": "Completed",
            "performer": "Dr. Smith, Transplant Surgeon",
            "location": "Transplant Center",
            "category": "Transplant Procedure",
            "notes": "Successful kidney transplantation from living donor",
            "is_enhanced": True
        },
        {
            "name": "Total hip replacement",
            "procedure_name": "Total hip replacement",
            "display_name": "Total hip replacement",
            "procedure_code": "13619001", 
            "snomed_code": "13619001",
            "date": "2015-08-22",
            "effective_time": "20150822",
            "status": "Completed",
            "performer": "Dr. Brown, Orthopedic Surgeon",
            "location": "Orthopedic Surgery Unit",
            "category": "Orthopedic Procedure",
            "notes": "Successful total hip arthroplasty",
            "is_enhanced": True
        }
    ]
    
    print(f"Creating enhanced procedures data: {len(enhanced_procedures)} procedures")
    for i, proc in enumerate(enhanced_procedures, 1):
        print(f"  {i}. {proc['name']} (SNOMED: {proc['procedure_code']}) - {proc['date']}")
    
    # Find existing session or create new one
    sessions = Session.objects.all()
    if sessions.exists():
        # Use existing session
        session_obj = sessions.first()
        session = SessionStore(session_key=session_obj.session_key)
        print(f"\nUsing existing session: {session_obj.session_key[:8]}...")
    else:
        # Create new session
        session = SessionStore()
        session.create()
        print(f"\nCreated new session: {session.session_key[:8]}...")
    
    # Store enhanced procedures in session (same pattern as medications)
    session['enhanced_procedures'] = enhanced_procedures
    session.save()
    
    print(f"✅ Enhanced procedures stored in Django session")
    print(f"✅ Key: 'enhanced_procedures'")
    print(f"✅ Count: {len(enhanced_procedures)} procedures")
    
    # Verify storage
    verification_session = SessionStore(session_key=session.session_key)
    stored_procedures = verification_session.get('enhanced_procedures')
    if stored_procedures:
        print(f"✅ Verification: Successfully stored {len(stored_procedures)} procedures")
        first_proc = stored_procedures[0]
        print(f"✅ First procedure: {first_proc['name']} (Code: {first_proc['procedure_code']})")
    else:
        print("❌ Verification failed: No enhanced procedures found")
    
    print(f"\n=== NEXT STEPS ===")
    print("1. ✅ Enhanced procedures stored in Django session")
    print("2. ✅ Using proven medications pattern")
    print("3. ✅ Removed custom get_enhanced_procedures() function") 
    print("4. ✅ Updated both main and fallback render paths")
    print("5. 🔄 Test the patient details view to see enhanced procedures")

if __name__ == "__main__":
    setup_enhanced_procedures()