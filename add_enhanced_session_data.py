#!/usr/bin/env python3

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
import json

def create_enhanced_allergies_data():
    """Create comprehensive allergy data with clinical_table structure"""
    return [
        {
            'title': 'Allergies and adverse reactions',
            'observation_code': '420134006',
            'observation_code_system': '2.16.840.1.113883.6.96',
            'observation_oid': '2.16.840.1.113883.6.96',
            'observation_code_with_oid': '420134006 (2.16.840.1.113883.6.96)',
            'clinical_table': {
                'headers': [
                    {'key': 'allergen', 'label': 'Allergen', 'primary': True, 'type': 'text'},
                    {'key': 'type', 'label': 'Type', 'primary': False, 'type': 'text'},
                    {'key': 'manifestation', 'label': 'Manifestation', 'primary': False, 'type': 'reaction'},
                    {'key': 'severity', 'label': 'Severity', 'primary': False, 'type': 'text'},
                    {'key': 'status', 'label': 'Status', 'primary': False, 'type': 'text'},
                    {'key': 'onset_date', 'label': 'Onset Date', 'primary': False, 'type': 'date'},
                    {'key': 'criticality', 'label': 'Criticality', 'primary': False, 'type': 'text'},
                    {'key': 'category', 'label': 'Category', 'primary': False, 'type': 'text'}
                ],
                'rows': [
                    {
                        'data': {
                            'allergen': {
                                'value': 'penicillin',
                                'display_value': 'Penicillin',
                                'code': '91936005',
                                'code_system': '2.16.840.1.113883.6.96'
                            },
                            'type': {
                                'value': 'drug_allergy',
                                'display_value': 'Drug Allergy'
                            },
                            'manifestation': {
                                'value': 'skin_rash',
                                'display_value': 'Skin rash with urticaria',
                                'code': '271807003',
                                'code_system': '2.16.840.1.113883.6.96'
                            },
                            'severity': {
                                'value': 'moderate',
                                'display_value': 'Moderate'
                            },
                            'status': {
                                'value': 'active',
                                'display_value': 'Active'
                            },
                            'onset_date': {
                                'value': '2023-05-10',
                                'display_value': '10 May 2023'
                            },
                            'criticality': {
                                'value': 'medium',
                                'display_value': 'Medium'
                            },
                            'category': {
                                'value': 'medication',
                                'display_value': 'Medication'
                            }
                        },
                        'has_medical_codes': True
                    },
                    {
                        'data': {
                            'allergen': {
                                'value': 'shellfish',
                                'display_value': 'Shellfish (Crustaceans)',
                                'code': '44027008',
                                'code_system': '2.16.840.1.113883.6.96'
                            },
                            'type': {
                                'value': 'food_allergy',
                                'display_value': 'Food Allergy'
                            },
                            'manifestation': {
                                'value': 'anaphylaxis',
                                'display_value': 'Anaphylaxis',
                                'code': '39579001',
                                'code_system': '2.16.840.1.113883.6.96'
                            },
                            'severity': {
                                'value': 'severe',
                                'display_value': 'Severe'
                            },
                            'status': {
                                'value': 'active',
                                'display_value': 'Active'
                            },
                            'onset_date': {
                                'value': '2021-08-10',
                                'display_value': '10 August 2021'
                            },
                            'criticality': {
                                'value': 'high',
                                'display_value': 'High'
                            },
                            'category': {
                                'value': 'food',
                                'display_value': 'Food'
                            }
                        },
                        'has_medical_codes': True
                    }
                ]
            },
            'has_enhanced_data': True,
            'enhanced_data_source': 'django_session_storage'
        }
    ]

def create_enhanced_procedures_data():
    """Create comprehensive procedure data with clinical_table structure"""
    return [
        {
            'title': 'Medical Procedures',
            'observation_code': '47519-4',
            'observation_code_system': '2.16.840.1.113883.6.12',
            'observation_oid': '2.16.840.1.113883.6.12',
            'observation_code_with_oid': '47519-4 (2.16.840.1.113883.6.12)',
            'clinical_table': {
                'headers': [
                    {'key': 'procedure', 'label': 'Procedure', 'primary': True, 'type': 'text'},
                    {'key': 'date', 'label': 'Date', 'primary': False, 'type': 'date'},
                    {'key': 'target_site', 'label': 'Target Site', 'primary': False, 'type': 'text'},
                    {'key': 'status', 'label': 'Status', 'primary': False, 'type': 'text'},
                    {'key': 'performer', 'label': 'Performer', 'primary': False, 'type': 'text'}
                ],
                'rows': [
                    {
                        'data': {
                            'procedure': {
                                'value': 'heart_assist_implant',
                                'display_value': 'Implantation of heart assist system',
                                'code': '64253000',
                                'code_system': '2.16.840.1.113883.6.96'
                            },
                            'date': {
                                'value': '2014-10-20',
                                'display_value': '20 October 2014'
                            },
                            'target_site': {
                                'value': 'heart',
                                'display_value': 'Heart (Left ventricle)',
                                'code': '87878005',
                                'code_system': '2.16.840.1.113883.6.96'
                            },
                            'status': {
                                'value': 'completed',
                                'display_value': 'Completed'
                            },
                            'performer': {
                                'value': 'cardiac_surgeon',
                                'display_value': 'Dr. Johnson, Cardiac Surgeon'
                            }
                        },
                        'has_medical_codes': True
                    }
                ]
            },
            'has_enhanced_data': True,
            'enhanced_data_source': 'django_session_storage'
        }
    ]

def add_enhanced_data_to_session():
    """Add enhanced data to the first available session"""
    
    sessions = Session.objects.all()
    target_patient = '3402173624'
    
    for session in sessions:
        store = SessionStore(session_key=session.session_key)
        data = store.load()
        
        if f'patient_match_{target_patient}' in data:
            print(f'=== ADDING ENHANCED DATA TO SESSION: {session.session_key} ===')
            
            # Add enhanced allergies using Django session storage pattern
            enhanced_allergies = create_enhanced_allergies_data()
            data['enhanced_allergies'] = enhanced_allergies
            
            # Add enhanced procedures using Django session storage pattern  
            enhanced_procedures = create_enhanced_procedures_data()
            data['enhanced_procedures'] = enhanced_procedures
            
            # Save back to session
            store.update(data)
            store.save()
            
            print(f'✅ Added {len(enhanced_allergies)} enhanced allergies')
            print(f'✅ Added {len(enhanced_procedures)} enhanced procedures')
            print(f'🔍 Enhanced allergies structure:')
            print(f'   - First allergy: {enhanced_allergies[0]["clinical_table"]["rows"][0]["data"]["allergen"]["display_value"]}')
            print(f'   - Manifestation: {enhanced_allergies[0]["clinical_table"]["rows"][0]["data"]["manifestation"]["display_value"]}')
            print(f'   - Has medical codes: {enhanced_allergies[0]["clinical_table"]["rows"][0]["has_medical_codes"]}')
            
            return True
    
    print('❌ No sessions found for target patient')
    return False

if __name__ == '__main__':
    print('🚀 Adding enhanced allergies and procedures data to session...')
    success = add_enhanced_data_to_session()
    if success:
        print('\n🎉 Enhanced data successfully added!')
        print('📋 Data structure matches Django session storage pattern')
        print('🧪 Ready to test allergies template with both data formats')
    else:
        print('\n❌ Failed to add enhanced data')