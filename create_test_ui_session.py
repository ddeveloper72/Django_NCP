#!/usr/bin/env python3
"""
Create Fresh UI Test Session - For checking medication display
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

from django.contrib.sessions.backends.db import SessionStore
import uuid

def create_test_session():
    """Create a fresh test session with enhanced medication data for UI testing"""
    
    print("CREATING FRESH TEST SESSION FOR UI")
    print("=" * 40)
    
    # Create enhanced medication data (what our parser correctly extracts)
    enhanced_medications = [
        {
            "name": "Eutirox",
            "active_ingredient": "levothyroxine sodium",
            "strength": "100 ug",
            "route": "Oral use",
            "pharmaceutical_form": "Tablet",
            "dosage": "1 ACM",
            "start_date": "1997-10-06",
            "schedule": "Daily",
            "status": "Active"
        },
        {
            "name": "Triapin", 
            "active_ingredient": "ramipril",
            "strength": "5 mg",  # ✅ This should now display correctly
            "route": "Oral use",  # ✅ This should now display correctly
            "pharmaceutical_form": "Prolonged-release tablet",
            "dosage": "2 ACM",
            "start_date": "2017-05-06", 
            "schedule": "Daily",
            "status": "Active",
            "compound_ingredients": [
                {"name": "ramipril", "strength": "5 mg"},
                {"name": "felodipine", "strength": "5 mg"}
            ]
        },
        {
            "name": "Tresiba",
            "active_ingredient": "insulin degludec",
            "strength": "100 IU/mL",
            "route": "Subcutaneous use", 
            "pharmaceutical_form": "Solution for injection in pre-filled pen",
            "dosage": "10 IU per day",
            "start_date": "2012-04-30",
            "schedule": "Daily",
            "status": "Active"
        }
    ]
    
    # Create session ID for testing
    test_session_id = "9999999999"  # Easy to remember test ID
    
    # Create sample CDA XML content containing Triapin - This is what CDAViewProcessor will parse
    sample_cda_xml = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <component>
        <structuredBody>
            <component>
                <section>
                    <code code="10160-0" codeSystem="2.16.840.1.113883.6.1" displayName="Medications"/>
                    <title>Medications</title>
                    <text>
                        <table>
                            <tr>
                                <td>Triapin</td>
                                <td>ramipril 5 mg, felodipine 5 mg</td>
                                <td>Prolonged-release tablet</td>
                                <td>5 mg</td>
                            </tr>
                            <tr>
                                <td>Eutirox</td>
                                <td>levothyroxine sodium</td>
                                <td>Tablet</td>
                                <td>100 ug</td>
                            </tr>
                            <tr>
                                <td>Tresiba</td>
                                <td>insulin degludec</td>
                                <td>Solution for injection</td>
                                <td>100 IU/mL</td>
                            </tr>
                        </table>
                    </text>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""
    
    # Create session store
    session = SessionStore()
    
    # Add patient data to session - CRITICAL: Include cda_document for CDAViewProcessor
    session_data = {
        f'patient_match_{test_session_id}': {
            'patient_id': test_session_id,
            'patient_name': 'Diana Ferreira (TEST)',
            'patient_country': 'PT',
            'patient_dob': '1969-01-02',
            'has_enhanced_data': True,
            'cda_document': sample_cda_xml,  # ✅ CRITICAL: CDAViewProcessor needs this
            'cda_l3_document': sample_cda_xml,  # ✅ May be needed for L3 view
            'enhanced_medications': enhanced_medications  # ✅ Pre-enhanced data for comparison
        },
        'medication_data_source': 'enhanced_parser_test',
        'parser_version': 'compound_strength_fix',
        'ui_test_session': True
    }
    
    # Save the session
    for key, value in session_data.items():
        session[key] = value
    
    session.save()
    
    print(f"✅ Test session created!")
    print(f"   Session ID: {test_session_id}")
    print(f"   Session Key: {session.session_key}")
    print(f"   Enhanced medications: {len(enhanced_medications)}")
    print(f"   Triapin strength: {enhanced_medications[1]['strength']}")
    print(f"   Triapin route: {enhanced_medications[1]['route']}")
    
    print(f"\n🌐 Test URL:")
    print(f"   http://localhost:8000/patient_data/cda/{test_session_id}/")
    
    return session.session_key, test_session_id

if __name__ == '__main__':
    create_test_session()