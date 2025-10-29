#!/usr/bin/env python
"""
Refresh Patient Session with Enhanced Pipeline
==============================================

This script will create a new patient session using the PT CDA file
and process it through our enhanced procedures pipeline.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

def create_enhanced_patient_session():
    """Create a new patient session with enhanced procedures data"""
    print("=" * 80)
    print("CREATING ENHANCED PATIENT SESSION")
    print("=" * 80)
    
    try:
        import json
        import hashlib
        from datetime import timedelta
        from django.utils import timezone
        from patient_data.models import PatientSession, PatientDataCache
        from patient_data.services.clinical_sections.pipeline.clinical_data_pipeline_manager import ClinicalDataPipelineManager
        
        # Load the PT CDA file with procedures
        cda_path = 'test_data/eu_member_states/PT/2-1234-W7.xml'
        
        if not os.path.exists(cda_path):
            print(f"❌ CDA file not found: {cda_path}")
            return False
        
        with open(cda_path, 'r', encoding='utf-8') as f:
            cda_content = f.read()
        
        print(f"✓ Loaded CDA file: {cda_path}")
        print(f"  File size: {len(cda_content):,} characters")
        
        # Process through enhanced pipeline
        pipeline_manager = ClinicalDataPipelineManager()
        
        print("\n" + "─" * 60)
        print("PROCESSING THROUGH ENHANCED PIPELINE")
        print("─" * 60)
        
        # Process CDA content
        pipeline_results = pipeline_manager.process_cda_content(cda_content)
        template_context = pipeline_manager.get_template_context()
        
        # Check procedures
        procedures = template_context.get('procedures', [])
        procedures_count = len(procedures)
        
        print(f"✓ Pipeline processing completed")
        print(f"  Procedures extracted: {procedures_count}")
        
        if procedures_count > 0:
            print("  Enhanced procedures:")
            for i, proc in enumerate(procedures, 1):
                name = proc.get('name', 'Unknown')
                code = proc.get('procedure_code', 'N/A')
                date = proc.get('date', 'N/A')
                print(f"    {i}. {name} (Code: {code}, Date: {date})")
        
        # Create a new patient session
        print("\n" + "─" * 60)
        print("CREATING PATIENT SESSION")
        print("─" * 60)
        
        session_id = "enhanced_pt_procedures_demo"
        
        # Delete existing session if it exists
        existing_sessions = PatientSession.objects.filter(session_id=session_id)
        if existing_sessions.exists():
            existing_sessions.delete()
            print(f"✓ Deleted existing session: {session_id}")
        
        # Create new session
        from django.contrib.auth.models import User
        import hashlib
        
        # Get or create a user for the session
        user = User.objects.first()
        if not user:
            user = User.objects.create_user(username='demo_user', password='demo_pass')
            
        # Generate required hashes
        search_hash = hashlib.sha256("demo_search_criteria".encode()).hexdigest()
        cda_hash = hashlib.sha256(cda_content.encode()).hexdigest()
        
        patient_session = PatientSession.objects.create(
            session_id=session_id,
            user=user,
            country_code="PT", 
            search_criteria_hash=search_hash,
            encrypted_patient_data='{}',
            cda_content_hash=cda_hash,
            client_ip="127.0.0.1",
            last_action="Enhanced session created with procedures data",
            encryption_key_version=20385,  # Use standard encryption key version
            status="active"
        )
        
        print(f"✓ Created new patient session: {session_id}")
        
        # Create cached data with enhanced procedures
        import uuid
        from datetime import timedelta
        
        # Generate unique cache key
        cache_key = f"procedures_{session_id}_{uuid.uuid4().hex[:8]}"
        
        # Prepare clinical data for caching
        clinical_data = {
            'procedures': procedures,
            'medications': template_context.get('medications', []),
            'allergies': template_context.get('allergies', []),
            'problems': template_context.get('problems', []),
            'vital_signs': template_context.get('vital_signs', [])
        }
        clinical_json = json.dumps(clinical_data)
        content_hash = hashlib.sha256(clinical_json.encode()).hexdigest()
        
        cache_data = PatientDataCache.objects.create(
            session=patient_session,
            cache_key=cache_key,
            data_type="clinical_data",
            encrypted_content=clinical_json,  # In production this would be encrypted
            content_hash=content_hash,
            expires_at=timezone.now() + timedelta(hours=8),
            encryption_key_version=20385
        )
        
        print(f"✓ Created cached data with {procedures_count} enhanced procedures")
        
        # Store CDA content in session for processing
        print("\n" + "─" * 60)
        print("SESSION SETUP COMPLETE")
        print("─" * 60)
        
        print(f"🎉 Enhanced patient session created successfully!")
        print(f"   Session ID: {session_id}")
        print(f"   Enhanced procedures: {procedures_count}")
        print(f"   Cache data ID: {cache_data.id}")
        print()
        print(f"💡 To view this enhanced session in the UI:")
        print(f"   1. Navigate to the patient view in Django")
        print(f"   2. Use session ID: {session_id}")
        print(f"   3. You should see enhanced procedures with actual names and SNOMED codes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating enhanced session: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_enhanced_patient_session()
    sys.exit(0 if success else 1)