#!/usr/bin/env python3
"""
Test the complete PS renderer flow with realistic data structures
"""

from bs4 import BeautifulSoup


# Simplified test renderer
class TestPSTableRenderer:
    def __init__(self):
        self.section_renderers = {
            "48765-2": self._render_allergies_table,
        }

    def render_section(self, section):
        """Main render method"""
        if not section or not isinstance(section, dict):
            return section

        # Handle title
        title = section.get("title", "")
        if isinstance(title, dict):
            title_str = title.get("original", title.get("translated", ""))
        else:
            title_str = str(title)

        # Check section code
        section_code = section.get("section_code", "")

        # Try LOINC code first
        if section_code in self.section_renderers:
            renderer = self.section_renderers[section_code]
            return renderer(section)

        # Try title matching for allergies
        title_lower = title_str.lower()
        if "allerg" in title_lower:
            return self._render_allergies_table(section)

        return section

    def _render_allergies_table(self, section):
        """Render allergies table with text parsing fallback"""
        allergies = []

        # Check for existing tables first
        existing_tables = section.get("tables", [])
        if existing_tables:
            print("  Found existing tables, using table data")
            table = existing_tables[0]
            allergies = table.get("rows", [])
        else:
            print("  No tables found, trying text parsing")
            content_html = section.get("content", {}).get("original", "")
            if isinstance(content_html, str):
                # Try HTML parsing first
                soup = BeautifulSoup(content_html, "html.parser")
                rows = soup.find_all("tr")

                if len(rows) > 1:
                    print("    Found HTML table structure")
                    # HTML table parsing logic here
                else:
                    print("    No HTML table, trying concatenated text parsing")
                    allergies = self._parse_concatenated_allergy_text(content_html)

        # Create table data
        table_data = {
            "headers": [
                "Allergy Type",
                "Causative Agent",
                "Manifestation",
                "Severity",
                "Status",
            ],
            "rows": allergies,
        }

        # Create enhanced section
        enhanced = section.copy()
        enhanced["table_data"] = table_data
        enhanced["has_table"] = True
        enhanced["table_html"] = self._generate_table_html(table_data)

        return enhanced

    def _parse_concatenated_allergy_text(self, text):
        """Parse concatenated allergy text"""
        allergies = []

        if not text:
            return allergies

        print(f"    Parsing text: {text[:100]}...")

        # Simple parsing for the known example
        if "Metoprolol" in text and "Réaction cutanée" in text:
            allergies.append(
                [
                    "Allergie médicamenteuse",
                    "Metoprolol",
                    "Réaction cutanée",
                    "Modérée",
                    "Confirmée",
                ]
            )
            print("    Found Metoprolol allergy")

        if "Fruits de mer" in text and "Anaphylaxie" in text:
            allergies.append(
                [
                    "Allergie alimentaire",
                    "Fruits de mer",
                    "Anaphylaxie",
                    "Sévère",
                    "Confirmée",
                ]
            )
            print("    Found seafood allergy")

        print(f"    Extracted {len(allergies)} allergies from text")
        return allergies

    def _generate_table_html(self, table_data):
        """Generate HTML table"""
        if not table_data.get("headers") and not table_data.get("rows"):
            return ""

        html = ["<table>"]

        # Headers
        headers = table_data.get("headers", [])
        if headers:
            html.append("<thead><tr>")
            for header in headers:
                html.append(f"<th>{header}</th>")
            html.append("</tr></thead>")

        # Rows
        rows = table_data.get("rows", [])
        if rows:
            html.append("<tbody>")
            for row in rows:
                html.append("<tr>")
                for cell in row:
                    html.append(f"<td>{cell}</td>")
                html.append("</tr>")
            html.append("</tbody>")

        html.append("</table>")
        return "".join(html)


def test_realistic_scenarios():
    """Test scenarios that match what we see in the browser"""
    renderer = TestPSTableRenderer()

    # Scenario 1: Allergy section with empty tables (what we see in browser)
    empty_allergy_section = {
        "title": {
            "original": "allergy (Allergies et intolérances)",
            "translated": "allergy (Allergies and adverse reactions)",
        },
        "section_code": "Free Text",
        "content": {
            "original": "Type d'allergieAgent causantManifestationSévéritéStatutAllergie médicamenteuseMetoprololRéaction cutanéeModéréeConfirméeAllergie alimentaireFruits de merAnaphylaxieSévèreConfirmée"
        },
        "tables": [],  # Empty - this is likely what's happening in production
    }

    print("=== TESTING EMPTY ALLERGY SECTION (BROWSER SCENARIO) ===")
    result = renderer.render_section(empty_allergy_section)

    print(f"Result has table_data: {'table_data' in result}")
    if "table_data" in result:
        td = result["table_data"]
        print(f"  Headers: {td.get('headers', [])}")
        print(f"  Rows: {td.get('rows', [])}")
        print(f"  Row count: {len(td.get('rows', []))}")

    if "table_html" in result:
        print(f"  Has HTML: Yes (length: {len(result['table_html'])})")
        print(f"  HTML preview: {result['table_html'][:200]}...")

    print()

    # Scenario 2: Test with pre-populated tables (working case)
    populated_allergy_section = {
        "title": {
            "original": "allergy (Allergies et intolérances)",
            "translated": "allergy (Allergies and adverse reactions)",
        },
        "section_code": "Free Text",
        "content": {"original": "Some content"},
        "tables": [
            {
                "headers": [
                    "Type d'Allergie",
                    "Agent Causal",
                    "Manifestation",
                    "Sévérité",
                    "Statut",
                ],
                "rows": [
                    [
                        "Allergie médicamenteuse",
                        "Metoprolol",
                        "Réaction cutanée",
                        "Modérée",
                        "Confirmée",
                    ],
                    [
                        "Allergie alimentaire",
                        "Fruits de mer",
                        "Anaphylaxie",
                        "Sévère",
                        "Confirmée",
                    ],
                ],
            }
        ],
    }

    print("=== TESTING POPULATED ALLERGY SECTION (WORKING CASE) ===")
    result2 = renderer.render_section(populated_allergy_section)

    print(f"Result has table_data: {'table_data' in result2}")
    if "table_data" in result2:
        td = result2["table_data"]
        print(f"  Headers: {td.get('headers', [])}")
        print(f"  Row count: {len(td.get('rows', []))}")

    return result


if __name__ == "__main__":
    test_realistic_scenarios()
