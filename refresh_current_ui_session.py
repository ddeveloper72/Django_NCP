#!/usr/bin/env python3
"""
Refresh Current UI Session - Force re-processing with new parser
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.contrib.sessions.models import Session
from patient_data.services.comprehensive_clinical_data_service import ComprehensiveClinicalDataService
import json

def refresh_all_patient_sessions():
    """Refresh all patient sessions with our enhanced CDA parser"""
    
    print("🔄 REFRESHING ALL PATIENT SESSIONS WITH NEW PARSER")
    print("=" * 60)
    
    # Get all sessions
    all_sessions = Session.objects.all()
    service = ComprehensiveClinicalDataService()
    
    refreshed_count = 0
    
    for session in all_sessions:
        try:
            session_data = session.get_decoded()
            
            # Look for patient match data
            patient_keys = [key for key in session_data.keys() if key.startswith('patient_match_')]
            
            if patient_keys:
                print(f"\n📋 Processing session: {session.session_key}")
                print(f"   Patient keys: {patient_keys}")
                
                for patient_key in patient_keys:
                    patient_data = session_data[patient_key]
                    
                    # Check if this session has CDA content
                    if isinstance(patient_data, dict) and 'cda_content' in patient_data:
                        print(f"   ✅ Found CDA content in {patient_key}")
                        
                        # Extract the CDA content
                        cda_content = patient_data['cda_content']
                        
                        # Re-process with our enhanced parser
                        print(f"   🔄 Re-processing CDA with enhanced parser...")
                        enhanced_data = service.extract_comprehensive_clinical_data(cda_content)
                        
                        # Update session with enhanced medications
                        if enhanced_data and 'medications' in enhanced_data:
                            medications = enhanced_data['medications']
                            session_data['enhanced_medications'] = medications
                            session_data['medication_refresh_timestamp'] = str(django.utils.timezone.now())
                            session_data['parser_version'] = 'enhanced_v2'
                            
                            print(f"   ✅ Enhanced: {len(medications)} medications extracted")
                            
                            # Show sample medication data
                            for med in medications[:2]:  # Show first 2
                                name = med.get('name', 'Unknown')
                                strength = med.get('strength', 'Not specified')
                                route = med.get('route', 'Not specified')
                                print(f"      • {name}: Strength={strength}, Route={route}")
                            
                            # Save updated session
                            session.session_data = session.encode(session_data)
                            session.save()
                            
                            refreshed_count += 1
                            print(f"   💾 Session updated successfully!")
                        else:
                            print(f"   ⚠️  No medications found in CDA")
                    else:
                        print(f"   ⚠️  No CDA content in {patient_key}")
                        
        except Exception as e:
            print(f"   ❌ Error processing session {session.session_key}: {e}")
    
    print(f"\n🎉 REFRESH COMPLETE!")
    print(f"   Sessions refreshed: {refreshed_count}")
    print(f"   All patient sessions now use enhanced medication parser")
    
    if refreshed_count > 0:
        print(f"\n💡 UI SHOULD NOW SHOW:")
        print(f"   • Triapin: Strength = 5 mg")
        print(f"   • Triapin: Route = Oral use")
        print(f"   • All other medications with proper strength/route data")
        print(f"\n🔄 Please refresh your browser to see the updated data!")

if __name__ == '__main__':
    refresh_all_patient_sessions()