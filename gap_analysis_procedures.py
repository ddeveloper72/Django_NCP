#!/usr/bin/env python
"""
Gap Analysis: Procedures Display Issue
=====================================

This script analyzes why the UI is showing placeholder procedures
instead of our enhanced procedures data.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

def analyze_procedures_gap():
    """Comprehensive gap analysis of procedures display"""
    print("=" * 80)
    print("GAP ANALYSIS: PROCEDURES DISPLAY ISSUE")
    print("=" * 80)
    
    try:
        from patient_data.models import PatientSession, PatientDataCache
        import json
        
        print("1. ANALYZING ALL CURRENT SESSIONS:")
        print("─" * 50)
        
        # Get all recent sessions
        sessions = PatientSession.objects.filter(is_active=True).order_by('-created_at')[:10]
        print(f"Found {sessions.count()} active sessions:")
        
        for session in sessions:
            cache_count = session.cached_data.count()
            print(f"  • {session.session_id[:20]}... (Cache: {cache_count} items, Status: {session.status})")
            
            # Check if this session has procedures data
            procedures_cache = session.cached_data.filter(data_type='clinical_data').first()
            if procedures_cache:
                try:
                    clinical_data = json.loads(procedures_cache.encrypted_content)
                    procedures = clinical_data.get('procedures', [])
                    print(f"    → Procedures: {len(procedures)} items")
                    if procedures:
                        for proc in procedures[:2]:  # Show first 2
                            name = proc.get('name', 'N/A')
                            print(f"      - {name}")
                    else:
                        print(f"      - No procedures data")
                except:
                    print(f"    → Error parsing cached data")
            else:
                print(f"    → No clinical cache data")
        
        print("\n2. CHECKING OUR ENHANCED SESSION:")
        print("─" * 50)
        
        try:
            enhanced_session = PatientSession.objects.get(session_id='enhanced_pt_procedures_demo')
            print(f"✓ Enhanced session exists: {enhanced_session.session_id}")
            print(f"  Status: {enhanced_session.status}")
            print(f"  Active: {enhanced_session.is_active}")
            print(f"  Cache count: {enhanced_session.cached_data.count()}")
            
            # Get the procedures from enhanced session
            cache_data = enhanced_session.cached_data.filter(data_type='clinical_data').first()
            if cache_data:
                clinical_data = json.loads(cache_data.encrypted_content)
                procedures = clinical_data.get('procedures', [])
                print(f"  Enhanced procedures: {len(procedures)} items")
                for proc in procedures:
                    print(f"    - {proc.get('name')} (Code: {proc.get('procedure_code')})")
            
        except PatientSession.DoesNotExist:
            print("❌ Enhanced session not found!")
        
        print("\n3. IDENTIFYING THE UI SESSION:")
        print("─" * 50)
        
        # Look for sessions that might match "Bob" or similar
        potential_ui_sessions = []
        for session in sessions:
            # Check if this session has patient data that might indicate it's "Bob's" session
            if session.encrypted_patient_data:
                try:
                    patient_data = json.loads(session.encrypted_patient_data)
                    print(f"Session {session.session_id[:15]}... patient data: {patient_data}")
                    potential_ui_sessions.append(session)
                except:
                    pass
        
        print(f"Found {len(potential_ui_sessions)} sessions with patient data")
        
        print("\n4. CHECKING PROCEDURES TEMPLATE:")
        print("─" * 50)
        
        # Check if procedures_section_new.html exists and is being used
        template_path = 'templates/patient_data/sections/procedures_section_new.html'
        if os.path.exists(template_path):
            print(f"✓ Enhanced procedures template exists: {template_path}")
            
            # Check template content
            with open(template_path, 'r') as f:
                content = f.read()
                if 'section_data.procedures' in content:
                    print("  ✓ Template expects section_data.procedures")
                if 'procedure.name' in content:
                    print("  ✓ Template accesses procedure.name")
                if 'procedure.procedure_code' in content:
                    print("  ✓ Template accesses procedure.procedure_code")
        else:
            print(f"❌ Enhanced procedures template not found: {template_path}")
        
        # Check parent template
        parent_template = 'templates/patient_data/clinical_information_content_modular.html'
        if os.path.exists(parent_template):
            print(f"✓ Parent template exists: {parent_template}")
            with open(parent_template, 'r') as f:
                content = f.read()
                if 'procedures_section_new.html' in content:
                    print("  ✓ Parent includes procedures_section_new.html")
                else:
                    print("  ❌ Parent does NOT include procedures_section_new.html")
        
        print("\n5. GAP ANALYSIS SUMMARY:")
        print("─" * 50)
        
        gaps = []
        
        # Check if enhanced session exists
        try:
            PatientSession.objects.get(session_id='enhanced_pt_procedures_demo')
            print("✓ Enhanced session with procedures data exists")
        except:
            gaps.append("Enhanced session missing or inactive")
        
        # Check if UI is using the right session
        if len([s for s in sessions if s.cached_data.count() > 0]) == 0:
            gaps.append("No active sessions have cached clinical data")
        
        # Check template integration
        if not os.path.exists(template_path):
            gaps.append("Enhanced procedures template missing")
        
        if gaps:
            print("\n❌ IDENTIFIED GAPS:")
            for i, gap in enumerate(gaps, 1):
                print(f"   {i}. {gap}")
        else:
            print("\n✓ No obvious gaps found - investigating further...")
        
        print("\n6. NEXT INVESTIGATION STEPS:")
        print("─" * 50)
        print("1. Check which session ID the UI is actually using")
        print("2. Verify if the enhanced session can be accessed via URL")
        print("3. Check Django view logic for session retrieval")
        print("4. Verify template inclusion chain")
        
        return len(gaps) == 0
        
    except Exception as e:
        print(f"❌ Error during gap analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = analyze_procedures_gap()
    sys.exit(0 if success else 1)