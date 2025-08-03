#!/usr/bin/env python
"""
Direct test of PSTableRenderer to debug the table creation issue
"""

import sys
import os

# Add the Django project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


# Simple test of PSTableRenderer without Django setup
def test_medication_rendering():
    """Test medication rendering with sample data structure"""

    # Sample section data that matches what our CDA translation service produces
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
                    <tr><td>Metformin</td><td>500mg</td><td>Twice daily</td></tr>
                </tbody>
            </table>
            """,
            "translated": """
            <table>
                <thead>
                    <tr><th>Medication</th><th>Dosage</th><th>Frequency</th></tr>
                </thead>
                <tbody>
                    <tr><td>Aspirin</td><td>100mg</td><td>Once daily</td></tr>
                    <tr><td>Metformin</td><td>500mg</td><td>Twice daily</td></tr>
                </tbody>
            </table>
            """,
        },
        "tables": [],  # No pre-extracted tables
    }

    print("=== Testing Medication Rendering ===")
    print(f"Section title: {sample_section['title']}")
    print(f"Section code: {sample_section['section_code']}")
    print(f"Content type: {type(sample_section['content'])}")
    print(f"Has original content: {'original' in sample_section['content']}")
    print(f"Content preview: {sample_section['content']['original'][:100]}...")

    # Create a simple mock renderer
    class MockPSTableRenderer:
        def __init__(self):
            pass

        def _render_medication_table(self, section):
            """Mock medication renderer to debug data flow"""
            print(f"\n=== _render_medication_table called ===")
            print(f"Section keys: {list(section.keys())}")

            # Check content structure
            content = section.get("content", {})
            print(f"Content type: {type(content)}")
            print(
                f"Content keys: {list(content.keys()) if isinstance(content, dict) else 'Not a dict'}"
            )

            if isinstance(content, dict):
                original = content.get("original", "")
                print(f"Original content length: {len(original)}")
                print(f"Original preview: {original[:200]}")

                # Try parsing with BeautifulSoup
                from bs4 import BeautifulSoup

                if original:
                    soup = BeautifulSoup(original, "html.parser")
                    tables = soup.find_all("table")
                    print(f"Found {len(tables)} table(s)")

                    if tables:
                        table = tables[0]
                        rows = table.find_all("tr")
                        print(f"Table has {len(rows)} rows")

                        for i, row in enumerate(rows):
                            cells = row.find_all(["td", "th"])
                            cell_texts = [cell.get_text().strip() for cell in cells]
                            print(f"Row {i}: {cell_texts}")

                        # Extract medication data
                        medications = []
                        if len(rows) > 1:  # Skip header
                            for row in rows[1:]:
                                cells = row.find_all(["td", "th"])
                                if len(cells) >= 1:
                                    medication = [
                                        (
                                            cells[0].get_text().strip()
                                            if len(cells) > 0
                                            else ""
                                        ),
                                        "",  # Active ingredient
                                        (
                                            cells[1].get_text().strip()
                                            if len(cells) > 1
                                            else ""
                                        ),
                                        "",  # Route
                                        (
                                            cells[2].get_text().strip()
                                            if len(cells) > 2
                                            else ""
                                        ),
                                        "",  # Start date
                                        "",  # End date
                                        "",  # Notes
                                    ]
                                    medications.append(medication)
                                    print(f"Extracted medication: {medication}")

                        return {
                            "has_table": True,
                            "table_data": {
                                "headers": [
                                    "Medication",
                                    "Active Ingredient",
                                    "Dosage",
                                    "Route",
                                    "Frequency",
                                    "Start Date",
                                    "End Date",
                                    "Notes",
                                ],
                                "rows": medications,
                            },
                            "section_type": "medications",
                        }

            return {
                "has_table": False,
                "table_data": {"headers": [], "rows": []},
                "section_type": "medications",
            }

    # Test the renderer
    renderer = MockPSTableRenderer()
    result = renderer._render_medication_table(sample_section)

    print(f"\n=== Final Result ===")
    print(f"Has table: {result['has_table']}")
    print(f"Table headers: {result['table_data']['headers']}")
    print(f"Table rows: {result['table_data']['rows']}")

    if result["table_data"]["rows"]:
        print(f"\n✅ SUCCESS: Found {len(result['table_data']['rows'])} medications")
        for i, med in enumerate(result["table_data"]["rows"]):
            print(f"  {i+1}. {med[0]} - {med[2]} - {med[4]}")
    else:
        print("\n❌ FAILED: No medications extracted")


if __name__ == "__main__":
    test_medication_rendering()
