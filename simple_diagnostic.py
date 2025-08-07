#!/usr/bin/env python3
"""
Simple diagnostic to check enhanced_sections data structure
"""

import os
import sys
import django

# Setup Django
sys.path.append(r"c:\Users\Duncan\VS_Code_Projects\django_ncp")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.services.enhanced_cda_processor import EnhancedCDAProcessor
from patient_data.enhanced_cda_display import EnhancedCDADisplayView


def diagnose_enhanced_sections():
    print("=== ENHANCED SECTIONS DIAGNOSTIC ===")

    try:
        # Create view instance and get CDA content
        view = EnhancedCDADisplayView()
        patient_id = "debug_test_123"

        print("1. Getting CDA content...")
        cda_content = view._get_patient_cda_content(patient_id)
        print(f"   CDA content length: {len(cda_content)}")

        print("2. Processing with Enhanced CDA Processor...")
        processor = EnhancedCDAProcessor(target_language="lv")
        enhanced_sections = processor.process_clinical_sections(
            cda_content=cda_content, source_language="fr"
        )

        print("3. Enhanced sections result:")
        print(f"   Type: {type(enhanced_sections)}")
        print(
            f"   Keys: {list(enhanced_sections.keys()) if isinstance(enhanced_sections, dict) else 'Not a dict'}"
        )

        if isinstance(enhanced_sections, dict):
            print(f"   Success: {enhanced_sections.get('success')}")
            print(f"   Sections count: {enhanced_sections.get('sections_count')}")

            sections = enhanced_sections.get("sections", [])
            print(f"   Actual sections list length: {len(sections)}")

            for i, section in enumerate(sections):
                print(f"   Section {i+1}:")
                print(f"     Section ID: {section.get('section_id', 'NO ID')}")
                print(f"     Section Code: {section.get('section_code', 'NO CODE')}")
                print(f"     Has table_data: {len(section.get('table_data', []))}")
                print(f"     Has PS table: {section.get('has_ps_table', False)}")

        # Test what template would receive
        print("4. Template context structure:")
        context = {
            "patient_id": patient_id,
            "enhanced_sections": enhanced_sections,
            "document_metadata": {
                "success": enhanced_sections.get("success", False),
                "sections_count": enhanced_sections.get("sections_count", 0),
            },
        }

        print(
            f"   Context enhanced_sections type: {type(context['enhanced_sections'])}"
        )
        print(
            f"   Context enhanced_sections success: {context['enhanced_sections'].get('success') if isinstance(context['enhanced_sections'], dict) else 'Not accessible'}"
        )

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    diagnose_enhanced_sections()
