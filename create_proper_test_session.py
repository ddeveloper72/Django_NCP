#!/usr/bin/env python3
"""
Create a proper test session that matches the expected format for patient_cda_view
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

def create_proper_test_session():
    """Create a test session with proper patient data structure"""
    
    print("🔧 Creating proper test session with expected patient data format...")
    print("=" * 60)
    
    try:
        from django.contrib.sessions.backends.db import SessionStore
        
        # Create test CDA with pregnancy data
        sample_cda = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <component>
        <structuredBody>
            <component>
                <section>
                    <templateId root="1.3.6.1.4.1.12559.11.10.1.3.1.2.4" />
                    <code code="10162-6" codeSystem="2.16.840.1.113883.6.1" displayName="History of pregnancies"/>
                    <title>History of pregnancies</title>
                    <entry>
                        <observation classCode="OBS" moodCode="EVN">
                            <code code="82810-3" codeSystem="2.16.840.1.113883.6.1" displayName="Pregnancy status"/>
                            <value xsi:type="CD" code="77386006" codeSystem="2.16.840.1.113883.6.96" displayName="Pregnant"/>
                        </observation>
                    </entry>
                    <entry>
                        <observation classCode="OBS" moodCode="EVN">
                            <code code="281050002" codeSystem="2.16.840.1.113883.6.96" displayName="Livebirth"/>
                            <value xsi:type="IVL_TS">
                                <low value="20200205"/>
                            </value>
                        </observation>
                    </entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""
        
        # Create session
        session_store = SessionStore()
        session_key = session_store.session_key if session_store.session_key else session_store._get_new_session_key()
        
        # Set up patient data in the expected format
        patient_data = {
            'patient_id': 'TEST-DIANA-PREGNANCY',
            'cda_content': sample_cda,
            'name': 'Diana Test Pregnancy',
            'birth_date': '1982-05-08',
            'gender': 'female'
        }
        
        # Set up the complete expected structure
        patient_match_data = {
            'patient_data': patient_data,
            'cda_content': sample_cda,
            'country_code': 'PT',
            'match_type': 'test'
        }
        
        # Store data with multiple possible key formats the view might look for
        session_store[f'patient_match_{session_key}'] = patient_match_data
        session_store['cda_xml'] = sample_cda
        session_store['patient_id'] = 'TEST-DIANA-PREGNANCY'
        session_store['translation_result'] = {
            'patient_identity': patient_data,
            'administrative_data': {},
            'clinical_data': {}
        }
        
        session_store.save()
        
        print(f"✅ Created test session: {session_key}")
        print(f"📋 Session contains keys:")
        for key in session_store.keys():
            print(f"   - {key}")
        
        print(f"\n🌐 Test URL: http://127.0.0.1:8000/patients/cda/{session_key}/L3/")
        
        return session_key
        
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    create_proper_test_session()