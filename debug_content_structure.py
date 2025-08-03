#!/usr/bin/env python
"""
Debug the actual content structure being passed to PSTableRenderer
"""

import os
import sys
import django

# Set up Django environment
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')

try:
    django.setup()
    
    from patient_data.services.cda_translation_service import CDATranslationService
    
    def debug_content_structure():
        """Debug what content structure is actually being created"""
        
        # Use a more realistic CDA sample with LOINC codes
        sample_cda_content = """
        <section>
            <code code="10160-0" codeSystem="2.16.840.1.113883.6.1" codeSystemName="LOINC" displayName="History of Medication use Narrative">
                <translation code="10160-0" codeSystem="2.16.840.1.113883.6.1" codeSystemName="LOINC" displayName="Historique de la prise médicamenteuse"/>
            </code>
            <title>History of Medication Use</title>
            <text>
                <table>
                    <thead>
                        <tr><th>Medication</th><th>Dosage</th><th>Frequency</th></tr>
                    </thead>
                    <tbody>
                        <tr><td>Aspirin</td><td>100mg</td><td>Once daily</td></tr>
                        <tr><td>Metformin</td><td>500mg</td><td>Twice daily</td></tr>
                    </tbody>
                </table>
            </text>
        </section>
        """
        
        print("=== Debugging Content Structure ===")
        
        # Test CDATranslationService parsing
        service = CDATranslationService(target_language="en")
        cda_data = service.parse_cda_html(sample_cda_content)
        
        print(f"Parsed {len(cda_data['sections'])} sections")
        
        for i, section in enumerate(cda_data['sections']):
            print(f"\n--- Section {i+1} ---")
            print(f"Title: {section.get('title', 'N/A')}")
            print(f"Section Code: {section.get('section_code', 'N/A')}")
            print(f"Content type: {type(section.get('content', 'N/A'))}")
            print(f"Content length: {len(str(section.get('content', '')))}")
            print(f"Content preview: {str(section.get('content', ''))[:200]}...")
            print(f"Has <table>: {'<table>' in str(section.get('content', ''))}")
            print(f"Has tables array: {len(section.get('tables', []))} tables")
            
            # Check if content_text exists
            if 'content_text' in section:
                print(f"Content text: {section['content_text'][:100]}...")
        
        # Test bilingual document creation
        print(f"\n=== Testing Bilingual Document Creation ===")
        bilingual_data = service.create_bilingual_document(cda_data)
        
        for i, section in enumerate(bilingual_data['sections']):
            print(f"\n--- Bilingual Section {i+1} ---")
            print(f"Title: {section.get('title_original', 'N/A')}")
            print(f"Section Code: {section.get('section_code', 'N/A')}")
            print(f"Content type: {type(section.get('content', 'N/A'))}")
            print(f"Content length: {len(str(section.get('content', '')))}")
            print(f"Content preview: {str(section.get('content', ''))[:200]}...")
            print(f"Has PS table: {bool(section.get('ps_table_html', ''))}")
            
            if section.get('ps_table_html'):
                print(f"PS table preview: {section['ps_table_html'][:100]}...")

    if __name__ == "__main__":
        debug_content_structure()
        
except Exception as e:
    print(f"Django setup error: {e}")
    import traceback
    traceback.print_exc()
