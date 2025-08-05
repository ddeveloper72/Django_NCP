#!/usr/bin/env python3
"""
Debug why clinical sections aren't rendering
"""

import os
import sys
import django

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.services.enhanced_cda_processor import EnhancedCDAProcessor


def test_clinical_sections_detection():
    """Test why clinical sections aren't being detected"""

    print("🔍 DEBUGGING CLINICAL SECTIONS DETECTION")
    print("=" * 50)

    # Test with HTML content that should have sections
    test_html = """
    <html>
    <body>
        <h2>Résumé des médicaments</h2>
        <p>Patient prend Amoxicilline 500mg</p>
        <table>
            <tr><th>Médicament</th><th>Dosage</th></tr>
            <tr><td>Amoxicilline</td><td>500mg</td></tr>
        </table>
        
        <h2>Allergies connues</h2>
        <p>Patient allergique à la pénicilline</p>
        
        <h2>Problèmes actifs</h2>
        <p>Hypertension, Diabète</p>
    </body>
    </html>
    """

    print("Testing with HTML content containing medical sections...")

    try:
        processor = EnhancedCDAProcessor(target_language="en")
        result = processor.process_clinical_sections(test_html, "fr")

        print(f"Success: {result.get('success', False)}")
        print(f"Content type: {result.get('content_type', 'unknown')}")
        print(f"Sections count: {result.get('sections_count', 0)}")
        print(f"Medical terms: {result.get('medical_terms_count', 0)}")

        sections = result.get("sections", [])
        if sections:
            print(f"\n✅ Found {len(sections)} clinical sections:")
            for i, section in enumerate(sections):
                print(f"  {i+1}. {section.get('title', {}).get('target', 'Unknown')}")
                print(
                    f"      Original: {section.get('title', {}).get('source', 'Unknown')}"
                )
                print(f"      Has table: {section.get('has_ps_table', False)}")
                print(
                    f"      Medical terms: {section.get('content', {}).get('medical_terms', 0)}"
                )
        else:
            print("❌ No clinical sections found!")

            # Debug: Let's see what the _process_html_cda method finds
            if result.get("content_type") == "html_enhanced":
                print("\nDEBUG INFO:")
                print(f"Error: {result.get('error', 'No error message')}")

        return len(sections) > 0

    except Exception as e:
        print(f"❌ Error testing clinical sections: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_real_patient_content():
    """Test with content that might be similar to what we get from the actual patient view"""

    print("\n🏥 TESTING WITH REALISTIC PATIENT CONTENT")
    print("=" * 50)

    # Simulate what might come from the patient view
    mock_cda_content = """
    <!DOCTYPE html>
    <html>
    <head><title>Patient Summary</title></head>
    <body>
        <div class="patient-header">
            <h1>Patient Summary</h1>
        </div>
        
        <div class="medication-section" data-code="10160-0">
            <h2>Résumé des médicaments</h2>
            <table class="clinical-table">
                <thead>
                    <tr><th>Médicament</th><th>Dosage</th><th>Fréquence</th></tr>
                </thead>
                <tbody>
                    <tr><td>Amoxicilline</td><td>500mg</td><td>3x/jour</td></tr>
                    <tr><td>Paracétamol</td><td>1000mg</td><td>Au besoin</td></tr>
                </tbody>
            </table>
        </div>
        
        <div class="allergy-section" data-code="48765-2">
            <h2>Allergies et réactions indésirables</h2>
            <ul>
                <li>Pénicilline - Éruption cutanée</li>
                <li>Latex - Réaction allergique</li>
            </ul>
        </div>
        
        <div class="problem-section" data-code="11450-4">
            <h2>Liste des problèmes</h2>
            <table class="clinical-table">
                <tr><td>Hypertension artérielle</td><td>Actif</td></tr>
                <tr><td>Diabète type 2</td><td>Actif</td></tr>
            </table>
        </div>
    </body>
    </html>
    """

    try:
        processor = EnhancedCDAProcessor(target_language="en")
        result = processor.process_clinical_sections(mock_cda_content, "fr")

        print(f"Success: {result.get('success', False)}")
        print(f"Content type: {result.get('content_type', 'unknown')}")
        print(f"Sections count: {result.get('sections_count', 0)}")

        sections = result.get("sections", [])
        if sections:
            print(f"\n✅ Found {len(sections)} clinical sections:")
            for i, section in enumerate(sections):
                title_info = section.get("title", {})
                print(f"  {i+1}. {title_info.get('target', 'Unknown')}")
                print(f"      Original: {title_info.get('source', 'Unknown')}")
                print(f"      Section code: {section.get('section_code', 'N/A')}")
                print(f"      Has PS table: {section.get('has_ps_table', False)}")
                print(f"      Is coded: {section.get('is_coded_section', False)}")

            return True
        else:
            print("❌ No clinical sections found in realistic content!")
            return False

    except Exception as e:
        print(f"❌ Error with realistic content: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Testing why clinical sections aren't rendering...")
    print("Let's see what's REALLY happening! 😊")

    test1_success = test_clinical_sections_detection()
    test2_success = test_real_patient_content()

    if test1_success and test2_success:
        print("\n🎉 Tests passed - clinical sections should be working!")
        print("The issue might be in the integration with the views...")
    else:
        print("\n🔧 Found the issue - the enhanced processor needs fixes!")
