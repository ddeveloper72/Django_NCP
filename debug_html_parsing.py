#!/usr/bin/env python3
"""
Debug Enhanced CDA Processing Logic (No Django Required)
"""

# Test if our HTML parsing and field mapping logic is working correctly


def test_html_parsing_logic():
    """Test HTML parsing without Django dependencies"""
    print("Testing Enhanced CDA HTML Processing Logic")
    print("=" * 45)

    # Test HTML content from the view
    test_html = """
    <html>
        <body>
            <section class="allergy-summary" data-code="48765-2">
                <h2>Allergies et réactions indésirables</h2>
                <table class="clinical-table">
                    <thead>
                        <tr>
                            <th>Allergène</th>
                            <th>Réaction</th>
                            <th>Sévérité</th>
                            <th>Statut</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Pénicilline</td>
                            <td>Éruption cutanée</td>
                            <td>Modéré</td>
                            <td>Confirmé</td>
                        </tr>
                    </tbody>
                </table>
            </section>
        </body>
    </html>
    """

    # Test BeautifulSoup parsing
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(test_html, "html.parser")
    print("✅ HTML parsed successfully")

    # Find sections with data-code attributes
    sections = soup.find_all(attrs={"data-code": True})
    print(f"📋 Found {len(sections)} sections with data-code attributes:")

    for section in sections:
        data_code = section.get("data-code")
        title = section.find(["h1", "h2", "h3", "h4"])
        title_text = title.get_text().strip() if title else "No title"

        print(f"   Section Code: {data_code}")
        print(f"   Title: {title_text}")

        # Find tables
        tables = section.find_all("table")
        print(f"   Tables: {len(tables)}")

        if tables:
            table = tables[0]
            # Get headers
            thead = table.find("thead")
            if thead:
                header_row = thead.find("tr")
                headers = [
                    th.get_text().strip() for th in header_row.find_all(["th", "td"])
                ]
                print(f"   Headers: {headers}")

                # Get first data row
                tbody = table.find("tbody")
                if tbody:
                    rows = tbody.find_all("tr")
                    if rows:
                        first_row = rows[0]
                        cells = [
                            td.get_text().strip()
                            for td in first_row.find_all(["td", "th"])
                        ]
                        print(f"   First Row Data: {cells}")

                        # Map cells to headers
                        row_data = {}
                        for i, cell in enumerate(cells):
                            if i < len(headers):
                                row_data[headers[i]] = cell

                        print(f"   Mapped Data: {row_data}")

                        # Test field matching logic
                        print(f"\n🔍 Testing field matching for section {data_code}:")

                        # Mock clinical fields for allergies (48765-2)
                        if data_code == "48765-2":
                            mock_fields = [
                                {
                                    "label": "Allergen Code",
                                    "valueSet": "YES",
                                    "translation": "YES",
                                },
                                {
                                    "label": "Allergen DisplayName",
                                    "valueSet": "YES",
                                    "translation": "YES",
                                },
                                {
                                    "label": "Reaction Code",
                                    "valueSet": "YES",
                                    "translation": "YES",
                                },
                                {
                                    "label": "Reaction DisplayName",
                                    "valueSet": "YES",
                                    "translation": "YES",
                                },
                            ]

                            for field in mock_fields:
                                field_label = field["label"]
                                has_valueset = (
                                    field.get("valueSet", "NO").upper() == "YES"
                                )

                                # Test field matching
                                matched_value = None
                                for header, value in row_data.items():
                                    if test_fuzzy_match(field_label, header):
                                        matched_value = value
                                        print(
                                            f"     {field_label} -> {header}: '{matched_value}' (ValueSet: {has_valueset})"
                                        )
                                        break

                                if not matched_value:
                                    print(f"     {field_label} -> No match found")

    print("\n✅ HTML parsing logic test completed")


def test_fuzzy_match(field_label: str, header: str) -> bool:
    """Test fuzzy field matching logic"""
    field_lower = field_label.lower()
    header_lower = header.lower()

    # Direct match
    if field_lower == header_lower:
        return True

    # Partial matches for common field types
    field_mappings = {
        "allergen": ["allergène", "allergen", "substance", "agent"],
        "reaction": ["réaction", "reaction", "symptôme", "symptom"],
        "medication": ["médicament", "medication", "drug", "medicine"],
        "problem": ["problème", "problem", "condition", "diagnostic"],
        "code": ["code"],
        "displayname": ["nom", "name", "libellé", "display", "description"],
    }

    for field_key, possible_headers in field_mappings.items():
        if field_key in field_lower:
            for possible_header in possible_headers:
                if possible_header in header_lower:
                    return True

    return False


if __name__ == "__main__":
    test_html_parsing_logic()
