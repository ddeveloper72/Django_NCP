#!/usr/bin/env python
"""
Enhanced View Integration Solution
=================================

This script shows how to modify the Django view to prioritize
enhanced cached data over the comprehensive service.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

def demonstrate_enhanced_view_logic():
    """Demonstrate how to enhance view logic for procedures"""
    print("=" * 80)
    print("ENHANCED VIEW INTEGRATION SOLUTION")
    print("=" * 80)
    
    try:
        from patient_data.models import PatientSession, PatientDataCache
        from patient_data.services.comprehensive_clinical_data_service import ComprehensiveClinicalDataService
        import json
        
        # Simulate view context - getting session (in real view this would be passed)
        session_id = 'enhanced_pt_procedures_demo'
        session = PatientSession.objects.get(session_id=session_id)
        
        print(f"✓ Simulating view for session: {session.session_id}")
        
        print("\n1. ENHANCED VIEW LOGIC IMPLEMENTATION:")
        print("─" * 60)
        
        # Step 1: Check for enhanced cached data first
        enhanced_cache = session.cached_data.filter(data_type='clinical_data').first()
        enhanced_procedures = []
        
        if enhanced_cache:
            try:
                cached_clinical_data = json.loads(enhanced_cache.encrypted_content)
                enhanced_procedures = cached_clinical_data.get('procedures', [])
                print(f"✓ Found enhanced cached procedures: {len(enhanced_procedures)} items")
                
                for proc in enhanced_procedures:
                    name = proc.get('name', 'N/A')
                    code = proc.get('procedure_code', 'N/A')
                    print(f"   • {name} (Code: {code})")
                    
            except Exception as e:
                print(f"❌ Error parsing enhanced cache: {e}")
                enhanced_procedures = []
        else:
            print("❌ No enhanced cached data found")
        
        # Step 2: Fallback to comprehensive service if no enhanced data
        if not enhanced_procedures:
            print("\n   → Falling back to ComprehensiveClinicalDataService...")
            # This is what the current view does
            comprehensive_service = ComprehensiveClinicalDataService()
            # In real implementation this would use match_data CDA content
            fallback_procedures = []  # Would be populated from comprehensive service
            print(f"   → Fallback procedures: {len(fallback_procedures)} items")
        else:
            print(f"   → Using enhanced cached data: {len(enhanced_procedures)} procedures")
        
        print("\n2. PROPOSED VIEW CODE ENHANCEMENT:")
        print("─" * 60)
        
        view_code = '''
# Enhanced view logic for procedures (add to patient_details view)
def get_enhanced_procedures(session, match_data):
    """Get procedures with enhanced data priority"""
    
    # Step 1: Check for enhanced cached clinical data
    enhanced_cache = session.cached_data.filter(data_type='clinical_data').first()
    if enhanced_cache:
        try:
            cached_clinical_data = json.loads(enhanced_cache.encrypted_content)
            enhanced_procedures = cached_clinical_data.get('procedures', [])
            
            if enhanced_procedures:
                logger.info(f"[ENHANCED_PROCEDURES] Using {len(enhanced_procedures)} cached procedures")
                return enhanced_procedures
                
        except Exception as e:
            logger.warning(f"[ENHANCED_PROCEDURES] Cache parsing failed: {e}")
    
    # Step 2: Fallback to comprehensive service
    logger.info("[ENHANCED_PROCEDURES] Falling back to comprehensive service")
    comprehensive_service = ComprehensiveClinicalDataService()
    
    cda_content = match_data.get("cda_content")
    if cda_content:
        comprehensive_data = comprehensive_service.extract_comprehensive_clinical_data(
            cda_content, match_data["country_code"]
        )
        
        if comprehensive_data:
            clinical_arrays = comprehensive_service.get_clinical_arrays_for_display(
                comprehensive_data
            )
            return clinical_arrays.get('procedures', [])
    
    return []  # No procedures found

# In the patient_details view, replace:
# procedures = clinical_arrays["procedures"]
# With:
procedures = get_enhanced_procedures(session, match_data)
clinical_arrays["procedures"] = procedures  # Update clinical_arrays for template
'''
        
        print(view_code)
        
        print("\n3. IMPLEMENTATION BENEFITS:")
        print("─" * 60)
        
        benefits = [
            "✅ Prioritizes high-quality enhanced procedures data",
            "✅ Maintains backward compatibility with existing views",
            "✅ Graceful fallback to comprehensive service",
            "✅ No template changes required",
            "✅ Works with existing session management",
            "✅ Preserves SNOMED CT codes and enhanced details"
        ]
        
        for benefit in benefits:
            print(f"   {benefit}")
        
        print("\n4. TESTING STRATEGY:")
        print("─" * 60)
        
        print("A. Test with enhanced session (should show 3 quality procedures)")
        print("B. Test with legacy session (should fallback to comprehensive service)")
        print("C. Test error handling (cache corruption, service failures)")
        print("D. Verify template receives correct data structure")
        
        print("\n5. NEXT STEPS:")
        print("─" * 60)
        
        print("1. Implement get_enhanced_procedures() function in patient_data/views.py")
        print("2. Modify patient_details view to use enhanced procedure logic")  
        print("3. Test with both enhanced and legacy sessions")
        print("4. Verify UI displays correct procedure names instead of placeholders")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = demonstrate_enhanced_view_logic()
    sys.exit(0 if success else 1)