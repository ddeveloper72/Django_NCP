#!/usr/bin/env python3
"""
Debug script to find Diana's session and check pregnancy history
"""

import os
import sys
import django
from django.conf import settings

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')

# Setup Django
django.setup()

from patient_data.services.pregnancy_history_extractor import PregnancyHistoryExtractor

def find_diana_session():
    """Find session containing Diana's data"""
    
    print("🔍 Searching for Diana's session...")
    print("=" * 60)
    
    try:
        from django.contrib.sessions.models import Session
        
        # Search through all sessions for Diana's name
        for session in Session.objects.all():
            try:
                session_data = session.get_decoded()
                cda_xml = session_data.get('cda_xml', '')
                
                # Check if this session contains Diana's data
                if 'Diana' in cda_xml or 'Ferreira' in cda_xml:
                    print(f"✅ Found Diana's session: {session.session_key}")
                    
                    # Extract pregnancy history
                    extractor = PregnancyHistoryExtractor()
                    pregnancy_data = extractor.extract_pregnancy_history(cda_xml)
                    
                    if pregnancy_data:
                        print("✅ Pregnancy history extracted successfully!")
                        print(f"📊 Current Pregnancy: {pregnancy_data.current_pregnancy}")
                        print(f"📊 Previous Pregnancies: {len(pregnancy_data.previous_pregnancies) if pregnancy_data.previous_pregnancies else 0}")
                        print(f"📊 Pregnancy Overview: {len(pregnancy_data.pregnancy_overview) if pregnancy_data.pregnancy_overview else 0}")
                        
                        # Show current pregnancy details
                        if pregnancy_data.current_pregnancy:
                            current = pregnancy_data.current_pregnancy
                            print(f"\n👶 Current Pregnancy Details:")
                            print(f"   Status: {current.status}")
                            print(f"   Code: {current.status_code}")
                            print(f"   Display Name: {current.status_display_name}")
                            print(f"   Expected Due Date: {current.expected_due_date}")
                            print(f"   Gestational Age: {current.gestational_age}")
                        
                        # Show previous pregnancies
                        if pregnancy_data.previous_pregnancies:
                            print(f"\n📝 Previous Pregnancies ({len(pregnancy_data.previous_pregnancies)}):")
                            for i, pregnancy in enumerate(pregnancy_data.previous_pregnancies, 1):
                                print(f"   {i}. Outcome: {pregnancy.outcome}")
                                print(f"      Date: {pregnancy.outcome_date}")
                                print(f"      Gestational Age: {pregnancy.gestational_age}")
                        
                        # Show pregnancy overview
                        if pregnancy_data.pregnancy_overview:
                            print(f"\n📊 Pregnancy Overview ({len(pregnancy_data.pregnancy_overview)}):")
                            for i, overview in enumerate(pregnancy_data.pregnancy_overview, 1):
                                print(f"   {i}. Code: {overview.outcome_code}")
                                print(f"      Display: {overview.outcome_display_name}")
                                print(f"      Count: {overview.outcome_count}")
                                print(f"      Date: {overview.outcome_date}")
                    else:
                        print("❌ No pregnancy history extracted")
                    
                    return session.session_key
                    
            except Exception as e:
                # Skip problematic sessions
                continue
        
        print("❌ Diana's session not found")
        return None
        
    except Exception as e:
        print(f"❌ Error during search: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    find_diana_session()