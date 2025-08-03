#!/usr/bin/env python
"""
Test the complete CDA translation and table rendering pipeline
"""

import sys
import os

# Add the Django project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_complete_pipeline():
    """Test the complete CDA translation and table rendering pipeline"""
    
    # Sample CDA content that matches the structure from the user's HTML
    sample_cda_html = """
    <html>
        <body>
            <section>
                <h3 id="section-10160-0" data-code="10160-0">History of Medication Use</h3>
                <div class="section-content">
                    <table>
                        <thead>
                            <tr><th>Medication</th><th>Dosage</th><th>Frequency</th></tr>
                        </thead>
                        <tbody>
                            <tr><td>Aspirin</td><td>100mg</td><td>Once daily</td></tr>
                            <tr><td>Metformin</td><td>500mg</td><td>Twice daily</td></tr>
                        </tbody>
                    </table>
                </div>
            </section>
            
            <section>
                <h3 id="section-48765-2" data-code="48765-2">Allergies and Intolerances</h3>
                <div class="section-content">
                    <table>
                        <thead>
                            <tr><th>Allergy Type</th><th>Causative Agent</th><th>Manifestation</th><th>Severity</th></tr>
                        </thead>
                        <tbody>
                            <tr><td>Drug allergy</td><td>Penicillin</td><td>Skin rash</td><td>Moderate</td></tr>
                        </tbody>
                    </table>
                </div>
            </section>
        </body>
    </html>
    """
    
    print("=== Testing Complete CDA Pipeline ===")
    print("Testing CDA parsing, translation, and table rendering...")
    
    # Mock classes to test without full Django setup
    class MockTranslator:
        def translate_term(self, term, source_lang):
            return f"[EN] {term}"
        
        def translate_text_block(self, text, source_lang):
            return f"[EN] {text}"
    
    class MockPSTableRenderer:
        def __init__(self):
            self.section_renderers = {
                "10160-0": self._render_medication_table,
                "48765-2": self._render_allergies_table
            }
        
        def render_section_tables(self, sections):
            """Mock render section tables"""
            rendered_sections = []
            for section in sections:
                section_code = section.get("section_code", "")
                if section_code in self.section_renderers:
                    renderer = self.section_renderers[section_code]
                    rendered = renderer(section)
                    rendered_sections.append(rendered)
                else:
                    rendered_sections.append({"table_html": "", "has_table": False})
            return rendered_sections
        
        def _render_medication_table(self, section):
            """Mock medication table renderer"""
            from bs4 import BeautifulSoup
            
            content = section.get("content", "")
            if content:
                soup = BeautifulSoup(content, "html.parser")
                tables = soup.find_all("table")
                
                if tables:
                    table = tables[0]
                    rows = table.find_all("tr")
                    medications = []
                    
                    if len(rows) > 1:  # Skip header
                        for row in rows[1:]:
                            cells = row.find_all(["td", "th"])
                            if len(cells) >= 1:
                                medication = [
                                    cells[0].get_text().strip() if len(cells) > 0 else "",
                                    "",  # Active ingredient
                                    cells[1].get_text().strip() if len(cells) > 1 else "",
                                    "",  # Route
                                    cells[2].get_text().strip() if len(cells) > 2 else "",
                                    "",  # Start date
                                    "",  # End date
                                    ""   # Notes
                                ]
                                medications.append(medication)
                    
                    table_html = self._generate_table_html({
                        "headers": ["Medication", "Active Ingredient", "Dosage", "Route", "Frequency", "Start Date", "End Date", "Notes"],
                        "rows": medications
                    })
                    
                    return {
                        "table_html": table_html,
                        "has_table": True,
                        "table_data": {
                            "headers": ["Medication", "Active Ingredient", "Dosage", "Route", "Frequency", "Start Date", "End Date", "Notes"],
                            "rows": medications
                        }
                    }
            
            return {"table_html": "", "has_table": False}
        
        def _render_allergies_table(self, section):
            """Mock allergies table renderer"""
            from bs4 import BeautifulSoup
            
            content = section.get("content", "")
            if content:
                soup = BeautifulSoup(content, "html.parser")
                tables = soup.find_all("table")
                
                if tables:
                    table = tables[0]
                    rows = table.find_all("tr")
                    allergies = []
                    
                    if len(rows) > 1:  # Skip header
                        for row in rows[1:]:
                            cells = row.find_all(["td", "th"])
                            if len(cells) >= 1:
                                allergy = [
                                    cells[0].get_text().strip() if len(cells) > 0 else "",
                                    cells[1].get_text().strip() if len(cells) > 1 else "",
                                    cells[2].get_text().strip() if len(cells) > 2 else "",
                                    cells[3].get_text().strip() if len(cells) > 3 else "",
                                    "Active"  # Status
                                ]
                                allergies.append(allergy)
                    
                    table_html = self._generate_table_html({
                        "headers": ["Allergy Type", "Causative Agent", "Manifestation", "Severity", "Status"],
                        "rows": allergies
                    })
                    
                    return {
                        "table_html": table_html,
                        "has_table": True,
                        "table_data": {
                            "headers": ["Allergy Type", "Causative Agent", "Manifestation", "Severity", "Status"],
                            "rows": allergies
                        }
                    }
            
            return {"table_html": "", "has_table": False}
        
        def _generate_table_html(self, table_data):
            """Generate HTML table"""
            html = '<table class="ps-table">\n'
            html += '  <thead>\n    <tr>\n'
            for header in table_data["headers"]:
                html += f'      <th>{header}</th>\n'
            html += '    </tr>\n  </thead>\n'
            html += '  <tbody>\n'
            for row in table_data["rows"]:
                html += '    <tr>\n'
                for cell in row:
                    html += f'      <td>{cell}</td>\n'
                html += '    </tr>\n'
            html += '  </tbody>\n</table>'
            return html
    
    class MockCDATranslationService:
        def __init__(self):
            self.translator = MockTranslator()
            self.table_renderer = MockPSTableRenderer()
        
        def parse_cda_html(self, html_content):
            """Mock CDA HTML parsing"""
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html_content, "html.parser")
            sections = []
            
            section_elements = soup.find_all("section")
            
            for section_element in section_elements:
                section_data = {}
                
                # Extract title and code
                title_h3 = section_element.find("h3")
                if title_h3:
                    section_data["title"] = title_h3.get_text(strip=True)
                    section_data["section_code"] = title_h3.get("data-code", "")
                
                # Extract content
                content_div = section_element.find("div", class_="section-content")
                if content_div:
                    # Preserve HTML structure for table parsing
                    section_data["content"] = str(content_div)
                    section_data["content_text"] = content_div.get_text(strip=True)
                else:
                    section_data["content"] = ""
                    section_data["content_text"] = ""
                
                sections.append(section_data)
            
            return {
                "language": "fr",
                "sections": sections,
                "patient_info": {}
            }
        
        def create_bilingual_document(self, cda_data):
            """Mock bilingual document creation"""
            rendered_sections = self.table_renderer.render_section_tables(cda_data["sections"])
            
            translated_sections = []
            for section, rendered_section in zip(cda_data["sections"], rendered_sections):
                translated_section = {
                    "section_code": section.get("section_code", ""),
                    "title_original": section.get("title", ""),
                    "title_translated": self.translator.translate_term(section.get("title", ""), "fr"),
                    "content_original": section.get("content_text", ""),
                    "content_translated": self.translator.translate_text_block(section.get("content_text", ""), "fr"),
                    "content": section.get("content", ""),  # For PSTableRenderer
                    "ps_table_html": rendered_section.get("table_html", ""),
                    "has_table": rendered_section.get("has_table", False),
                    "table_data": rendered_section.get("table_data", {"headers": [], "rows": []})
                }
                translated_sections.append(translated_section)
            
            return {
                "source_language": "fr",
                "sections": translated_sections
            }
    
    # Test the complete pipeline
    service = MockCDATranslationService()
    
    print("\n1. Parsing CDA HTML...")
    cda_data = service.parse_cda_html(sample_cda_html)
    print(f"   Found {len(cda_data['sections'])} sections")
    for section in cda_data['sections']:
        print(f"   - {section['title']} (Code: {section['section_code']})")
        print(f"     Content length: {len(section['content'])}")
        print(f"     Has table tags: {'<table>' in section['content']}")
    
    print("\n2. Creating bilingual document with table rendering...")
    bilingual_data = service.create_bilingual_document(cda_data)
    
    print("\n3. Results:")
    for section in bilingual_data["sections"]:
        print(f"\n   Section: {section['title_original']}")
        print(f"   Code: {section['section_code']}")
        print(f"   Has PS table: {section['has_table']}")
        if section['has_table']:
            table_data = section['table_data']
            print(f"   Headers: {table_data['headers']}")
            print(f"   Rows: {len(table_data['rows'])}")
            for i, row in enumerate(table_data['rows']):
                print(f"     Row {i+1}: {row}")
            print(f"   PS Table HTML preview: {section['ps_table_html'][:100]}...")
        else:
            print("   No table rendered")
    
    # Check if we successfully extracted table data
    medication_section = next((s for s in bilingual_data["sections"] if s["section_code"] == "10160-0"), None)
    allergy_section = next((s for s in bilingual_data["sections"] if s["section_code"] == "48765-2"), None)
    
    print(f"\n=== Final Results ===")
    if medication_section and medication_section['has_table']:
        print(f"✅ Medications: Found {len(medication_section['table_data']['rows'])} entries")
    else:
        print("❌ Medications: No table data extracted")
    
    if allergy_section and allergy_section['has_table']:
        print(f"✅ Allergies: Found {len(allergy_section['table_data']['rows'])} entries")
    else:
        print("❌ Allergies: No table data extracted")

if __name__ == "__main__":
    test_complete_pipeline()
