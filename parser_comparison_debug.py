#!/usr/bin/env python3
"""
Debug Enhanced vs CDA Parser Medications
"""

import os
import sys
import django

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from patient_data.services.enhanced_cda_xml_parser import EnhancedCDAXMLParser
from patient_data.services.cda_parser_service import CDAParserService
import logging

# Enable debug logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("ENHANCED vs CDA PARSER COMPARISON")
print("=" * 40)

# Test with Diana CDA file
cda_file_path = "test_data/eu_member_states/PT/2-1234-W7.xml"

try:
    with open(cda_file_path, 'r', encoding='utf-8') as f:
        cda_content = f.read()
    
    print(f"CDA file loaded: {len(cda_content)} chars")
    
    # Test Enhanced Parser
    print(f"\n--- ENHANCED PARSER ---")
    enhanced_parser = EnhancedCDAXMLParser()
    enhanced_data = enhanced_parser.parse_cda_content(cda_content)
    
    print(f"Enhanced data keys: {enhanced_data.keys()}")
    
    enhanced_sections = enhanced_data.get('sections', [])
    print(f"Enhanced sections: {len(enhanced_sections)}")
    
    enhanced_med_count = 0
    for section in enhanced_sections:
        if "structured_data" in section:
            for entry in section["structured_data"]:
                entry_type = entry.get("type", "")
                section_type = entry.get("section_type", "")
                
                if section_type == "medication":
                    enhanced_med_count += 1
                    print(f"  Enhanced med #{enhanced_med_count}:")
                    print(f"    Type: {entry_type}")
                    print(f"    Entry keys: {entry.keys()}")
                    
                    # Check for dosage data
                    if entry_type == "valueset_entry":
                        entry_fields = entry.get("fields", {})
                        print(f"    Fields: {list(entry_fields.keys())}")
                        
                        # Look for dose-related fields
                        for key in entry_fields:
                            if 'dose' in key.lower() or 'quantity' in key.lower():
                                print(f"    Dose field {key}: {entry_fields[key]}")
                    elif "data" in entry:
                        data = entry["data"]
                        print(f"    Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not dict'}")
                        if isinstance(data, dict):
                            for key in data:
                                if 'dose' in key.lower() or 'quantity' in key.lower():
                                    print(f"    Dose field {key}: {data[key]}")
    
    print(f"Enhanced parser medications: {enhanced_med_count}")
    
    # Test CDA Parser
    print(f"\n--- CDA PARSER ---")
    cda_parser = CDAParserService()
    
    # Parse using full extract (what the service uses)
    cda_parsed_data = cda_parser.parse_cda_document(cda_content)
    
    # Now test the extract_all_data method (what might be used by structured extractor)
    structured_data = cda_parser.extract_all_data(cda_content)
    cda_medications = structured_data.get('medications', [])
    
    print(f"CDA Parser structured medications: {len(cda_medications)}")
    
    if cda_medications:
        med = cda_medications[0]
        print(f"  First CDA med:")
        print(f"    Type: {type(med)}")
        
        # Check for dosage fields
        dose_fields = []
        if hasattr(med, '__dict__'):
            for attr in med.__dict__:
                if 'dose' in attr.lower() or 'quantity' in attr.lower():
                    dose_fields.append((attr, getattr(med, attr)))
        elif isinstance(med, dict):
            for key in med:
                if 'dose' in key.lower() or 'quantity' in key.lower():
                    dose_fields.append((key, med[key]))
        
        print(f"    Dose fields found: {len(dose_fields)}")
        for field_name, field_value in dose_fields:
            print(f"      {field_name}: {field_value}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\nCOMPARISON COMPLETE")