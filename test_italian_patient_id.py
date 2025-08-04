#!/usr/bin/env python3
"""
Test patient identifier extraction with Italian CDA containing NCPNPH80A01H501K
"""
from xml.etree import ElementTree as ET

def extract_italian_patient_ids(cda_file):
    """Extract patient identifiers from Italian CDA"""
    
    with open(cda_file, 'r', encoding='utf-8') as f:
        cda_content = f.read()
    
    print(f"Testing Italian CDA: {cda_file}")
    print("=" * 60)
    
    try:
        root = ET.fromstring(cda_content)
        
        # Define namespace
        namespaces = {'hl7': 'urn:hl7-org:v3'}
        
        # Find all patient ID elements
        patient_ids = root.findall('.//hl7:recordTarget/hl7:patientRole/hl7:id', namespaces)
        
        print(f"Found {len(patient_ids)} patient ID elements:")
        
        for i, id_elem in enumerate(patient_ids, 1):
            extension = id_elem.get('extension', 'N/A')
            root_attr = id_elem.get('root', 'N/A')
            assigning_authority = id_elem.get('assigningAuthorityName', 'N/A')
            displayable = id_elem.get('displayable', 'N/A')
            
            print(f"  {i}. Extension: {extension}")
            print(f"     Root: {root_attr}")
            print(f"     Assigning Authority: {assigning_authority}")
            print(f"     Displayable: {displayable}")
            print()
        
        # Check for the specific Italian fiscal code
        search_id = "NCPNPH80A01H501K"
        found_search_id = any(id_elem.get('extension') == search_id for id_elem in patient_ids)
        
        print(f"Search ID '{search_id}' found: {found_search_id}")
        
        # Show how these would appear in our template
        print("\nHow these would appear in our CDA template:")
        for id_elem in patient_ids:
            extension = id_elem.get('extension', 'N/A')
            root_attr = id_elem.get('root', 'N/A')
            authority = id_elem.get('assigningAuthorityName', '')
            
            if authority:
                print(f"  Patient ID ({authority}): {extension}")
            else:
                print(f"  Patient ID ({root_attr}): {extension}")
    
    except Exception as e:
        print(f"Error processing CDA: {e}")

def test_italian_cda():
    """Test with Italian CDA files"""
    
    italian_cda = "test_data/eu_member_states/IT/2025-03-28T13-29-45.499822Z_CDA_EHDSI---PIVOT-CDA-(L1)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"
    
    extract_italian_patient_ids(italian_cda)

if __name__ == "__main__":
    test_italian_cda()
