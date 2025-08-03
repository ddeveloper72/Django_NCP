#!/usr/bin/env python
"""
Quick test for PSTableRenderer table extraction
"""

import os
import sys
import django

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_ncp.settings")

# Simple test without full Django setup
from patient_data.services.ps_table_renderer import PSTableRenderer


def test_medication_parsing():
    """Test medication table parsing with sample CDA content"""

    # Sample CDA content similar to what we see in the Raw CDA
    sample_section = {
        "title": "History of Medication Use",
        "section_code": "10160-0",
        "content": {
            "original": """
            <table>
                <thead>
                    <tr><th>Medication</th><th>Dosage</th><th>Frequency</th></tr>
                </thead>
                <tbody>
                    <tr><td>Aspirin</td><td>100mg</td><td>Once daily</td></tr>
                </tbody>
            </table>
            """
        },
    }

    print("=== Testing PSTableRenderer Medication Parsing ===")
    print(f"Sample section title: {sample_section.get('title')}")
    print(f"Sample section code: {sample_section.get('section_code')}")
    print(
        f"Sample content preview: {str(sample_section.get('content', {}).get('original', ''))[:100]}..."
    )

    # Test the renderer
    try:
        renderer = PSTableRenderer()

        # Test the specific medication renderer
        result = renderer._render_medication_table(sample_section)

        print(f"\n=== Results ===")
        print(f"Has table: {result.get('has_table', False)}")
        print(f"Table data headers: {result.get('table_data', {}).get('headers', [])}")
        print(f"Table data rows: {result.get('table_data', {}).get('rows', [])}")
        print(
            f"Clinical codes: {result.get('clinical_codes', {}).get('formatted_display', 'None')}"
        )

        if result.get("table_data", {}).get("rows"):
            print(
                f"\n✅ SUCCESS: Extracted {len(result['table_data']['rows'])} medication(s)"
            )
            for i, row in enumerate(result["table_data"]["rows"]):
                print(f"  Medication {i+1}: {row}")
        else:
            print(f"\n❌ FAILED: No medications extracted")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_medication_parsing()
