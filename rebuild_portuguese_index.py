#!/usr/bin/env python3
"""
Rebuild CDA Document Index for Portuguese Patients

This script adds Portuguese patients to the CDA document index so they can be
found by the Django NCP portal.
"""

import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path

def extract_patient_info_from_cda(file_path):
    """Extract patient information from CDA XML file"""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Define namespaces
        namespaces = {
            'ns': 'urn:hl7-org:v3',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
        
        # Extract patient ID
        patient_id_elem = root.find('.//ns:patientRole/ns:id', namespaces)
        patient_id = patient_id_elem.get('extension') if patient_id_elem is not None else None
        
        # Extract patient name
        name_elem = root.find('.//ns:patientRole/ns:patient/ns:name', namespaces)
        if name_elem is not None:
            family = name_elem.find('ns:family', namespaces)
            given = name_elem.find('ns:given', namespaces)
            family_name = family.text if family is not None else ''
            given_name = given.text if given is not None else ''
            full_name = f'{family_name}, {given_name}' if family_name and given_name else patient_id
        else:
            full_name = patient_id or 'Unknown'
            
        return {
            'id': patient_id,
            'name': full_name,
            'file_path': str(file_path)
        }
    except Exception as e:
        print(f'Error parsing {file_path}: {e}')
        return None

def rebuild_portuguese_index():
    """Rebuild the CDA index to include Portuguese patients"""
    
    print("🔧 REBUILDING CDA INDEX FOR PORTUGUESE PATIENTS")
    print("=" * 50)
    
    # Load existing index
    try:
        with open('cda_document_index.json', 'r') as f:
            index = json.load(f)
        print("✅ Loaded existing CDA document index")
    except:
        index = {}
        print("⚠️  Creating new CDA document index")
    
    # Initialize PT section if not exists
    if 'PT' not in index:
        index['PT'] = {}
        print("📁 Created PT section in index")
    
    # Scan Portuguese CDA files
    pt_folder = Path('test_data/eu_member_states/PT')
    if pt_folder.exists():
        xml_files = list(pt_folder.glob('*.xml'))
        print(f"📋 Found {len(xml_files)} XML files in Portuguese folder")
        
        for xml_file in xml_files:
            print(f'📄 Processing: {xml_file.name}')
            
            patient_info = extract_patient_info_from_cda(xml_file)
            if patient_info and patient_info['id']:
                patient_id = patient_info['id']
                
                # Add to index
                index['PT'][patient_id] = {
                    'name': patient_info['name'],
                    'country': 'PT',
                    'documents': {
                        'L3': {
                            'file': str(xml_file),
                            'type': 'CDA'
                        }
                    }
                }
                
                print(f'   ✅ Added patient: {patient_id} - {patient_info["name"]}')
            else:
                print(f'   ❌ Could not extract patient info from {xml_file.name}')
    else:
        print(f"❌ Portuguese folder not found: {pt_folder}")
        return False
    
    # Save updated index
    try:
        with open('cda_document_index.json', 'w') as f:
            json.dump(index, f, indent=2)
        print(f"\n✅ Updated CDA document index")
    except Exception as e:
        print(f"\n❌ Error saving index: {e}")
        return False
    
    print(f"🇵🇹 Portuguese patients now in index: {len(index.get('PT', {}))}")
    
    # List all Portuguese patients
    if 'PT' in index:
        print("\n📋 Portuguese patients in index:")
        for patient_id, patient_data in index['PT'].items():
            print(f"   • {patient_id}: {patient_data['name']}")
    
    # Verify the target patient
    if '2-1234-W7' in index.get('PT', {}):
        print(f"\n🎯 SUCCESS: Patient 2-1234-W7 now in index!")
        target_patient = index['PT']['2-1234-W7']
        print(f"   Name: {target_patient['name']}")
        print(f"   Country: {target_patient['country']}")
        print(f"   Documents: {list(target_patient['documents'].keys())}")
        return True
    else:
        print(f"\n❌ Patient 2-1234-W7 still not found")
        return False

if __name__ == "__main__":
    success = rebuild_portuguese_index()
    if success:
        print(f"\n🎉 Ready to search for patient 2-1234-W7 in Django NCP portal!")
    else:
        print(f"\n⚠️  Index rebuild completed but target patient not found")