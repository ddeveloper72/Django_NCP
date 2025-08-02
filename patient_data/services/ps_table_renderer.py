"""
Patient Summary Table Renderer for PS Display Guidelines Compliance
Dynamically renders CDA L3 sections as standardized healthcare tables
"""

import re
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


class PSTableRenderer:
    """
    Renders CDA L3 sections as structured tables according to PS Display Guidelines
    """

    def __init__(self):
        self.section_renderers = {
            "10160-0": self._render_medication_table,  # History of Medication use
            "48765-2": self._render_allergies_table,  # Allergies and adverse reactions
            "11450-4": self._render_problems_table,  # Problem list
            "47519-4": self._render_procedures_table,  # History of Procedures
            "30954-2": self._render_results_table,  # Relevant diagnostic tests/laboratory data
            "10157-6": self._render_immunizations_table,  # History of immunization
            "18776-5": self._render_treatment_plan_table,  # Plan of care
        }

    def render_section_tables(self, sections: List[Dict]) -> List[Dict]:
        """
        Convert CDA sections to standardized PS Display Guidelines tables
        """
        rendered_sections = []

        for section in sections:
            section_code = section.get("section_code", "")

            # Clean section code (remove system info if present)
            clean_code = section_code.split()[0] if section_code else ""

            if clean_code in self.section_renderers:
                # Use specialized renderer for this section type
                renderer = self.section_renderers[clean_code]
                rendered_section = renderer(section)
            else:
                # Use generic renderer for unspecified sections
                rendered_section = self._render_generic_table(section)

            rendered_sections.append(rendered_section)

        return rendered_sections

    def _render_medication_table(self, section: Dict) -> Dict:
        """Render medication history as standardized table"""
        try:
            # Handle both simple string content and nested content structure
            content_html = section.get("content", "")
            if isinstance(content_html, dict):
                content_html = content_html.get("original", "")

            soup = BeautifulSoup(content_html, "html.parser")

            # Look for existing table structure in the section
            existing_tables = section.get("tables", [])
            if existing_tables:
                return self._enhance_existing_table(
                    section, existing_tables[0], "medications"
                )

            # Create table from text content if no table exists
            return self._create_medication_table_from_text(section)

        except Exception as e:
            logger.error(f"Error rendering medication table: {e}")
            return section

    def _render_allergies_table(self, section: Dict) -> Dict:
        """Render allergies as standardized table"""
        try:
            # Handle both simple string content and nested content structure
            content_html = section.get("content", "")
            if isinstance(content_html, dict):
                content_html = content_html.get("original", "")

            soup = BeautifulSoup(content_html, "html.parser")

            # Look for existing table structure in the section
            existing_tables = section.get("tables", [])
            if existing_tables:
                return self._enhance_existing_table(
                    section, existing_tables[0], "allergies"
                )

            # Create table from text content
            return self._create_allergies_table_from_text(section)

        except Exception as e:
            logger.error(f"Error rendering allergies table: {e}")
            return section

    def _render_problems_table(self, section: Dict) -> Dict:
        """Render problem list as standardized table"""
        try:
            content_html = section.get("content", {}).get("original", "")

            # Extract problem information
            table_data = {
                "headers": ["Problem/Diagnosis", "Status", "Onset Date", "Notes"],
                "rows": [],
            }

            # Parse content for problem data
            problems = self._extract_problems_from_content(content_html)
            for problem in problems:
                table_data["rows"].append(
                    [
                        problem.get("name", "Unknown"),
                        problem.get("status", "Active"),
                        problem.get("onset_date", "Unknown"),
                        problem.get("notes", ""),
                    ]
                )

            return self._create_enhanced_section(section, table_data, "problems")

        except Exception as e:
            logger.error(f"Error rendering problems table: {e}")
            return section

    def _render_procedures_table(self, section: Dict) -> Dict:
        """Render procedures as standardized table"""
        table_data = {
            "headers": ["Procedure", "Date", "Performer", "Location", "Notes"],
            "rows": [],
        }
        return self._create_enhanced_section(section, table_data, "procedures")

    def _render_results_table(self, section: Dict) -> Dict:
        """Render diagnostic results as standardized table"""
        table_data = {
            "headers": ["Test/Result", "Value", "Reference Range", "Date", "Status"],
            "rows": [],
        }
        return self._create_enhanced_section(section, table_data, "results")

    def _render_immunizations_table(self, section: Dict) -> Dict:
        """Render immunizations as standardized table"""
        table_data = {
            "headers": ["Vaccine", "Date Given", "Dose", "Route", "Provider"],
            "rows": [],
        }
        return self._create_enhanced_section(section, table_data, "immunizations")

    def _render_treatment_plan_table(self, section: Dict) -> Dict:
        """Render treatment plan as standardized table"""
        table_data = {
            "headers": ["Treatment/Care Plan", "Priority", "Status", "Target Date"],
            "rows": [],
        }
        return self._create_enhanced_section(section, table_data, "treatment_plan")

    def _render_generic_table(self, section: Dict) -> Dict:
        """Render unknown sections as generic table"""
        try:
            content_html = section.get("content", {}).get("original", "")
            soup = BeautifulSoup(content_html, "html.parser")

            # Look for existing table
            existing_table = soup.find("table")
            if existing_table:
                return self._enhance_existing_table(section, existing_table, "generic")

            # Create simple content display
            table_data = {"headers": ["Information"], "rows": [[content_html]]}

            return self._create_enhanced_section(section, table_data, "generic")

        except Exception as e:
            logger.error(f"Error rendering generic table: {e}")
            return section

    def _enhance_existing_table(
        self, section: Dict, table_data: Dict, section_type: str
    ) -> Dict:
        """Enhance existing table data with PS Guidelines styling"""
        try:
            # Table data already contains headers and rows
            enhanced_table_data = {
                "headers": table_data.get("headers", []),
                "rows": table_data.get("rows", []),
                "section_type": section_type,
            }

            return self._create_enhanced_section(
                section, enhanced_table_data, section_type
            )

        except Exception as e:
            logger.error(f"Error enhancing existing table: {e}")
            return section

    def _create_medication_table_from_text(self, section: Dict) -> Dict:
        """Create medication table from free text"""
        content_html = section.get("content", {}).get("original", "")

        # Look for medication data in the content
        medications = []

        # Try to extract from structured content (Luxembourg example has table structure)
        soup = BeautifulSoup(content_html, "html.parser")
        rows = soup.find_all("tr")

        if len(rows) > 1:  # Has header row
            for row in rows[1:]:  # Skip header
                cells = row.find_all(["td", "th"])
                if len(cells) >= 7:  # Minimum expected columns
                    medication = [
                        (
                            cells[1].get_text().strip() if len(cells) > 1 else ""
                        ),  # Nom commercial
                        (
                            cells[2].get_text().strip() if len(cells) > 2 else ""
                        ),  # Principe actif
                        (
                            cells[2].get_text().strip() if len(cells) > 2 else ""
                        ),  # Dosage (from principle actif)
                        cells[4].get_text().strip() if len(cells) > 4 else "",  # Route
                        (
                            cells[5].get_text().strip() if len(cells) > 5 else ""
                        ),  # Posologie
                        (
                            cells[6].get_text().strip() if len(cells) > 6 else ""
                        ),  # Start date
                        (
                            cells[7].get_text().strip() if len(cells) > 7 else ""
                        ),  # End date
                        cells[8].get_text().strip() if len(cells) > 8 else "",  # Notes
                    ]
                    medications.append(medication)

        table_data = {
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
        }
        return self._create_enhanced_section(section, table_data, "medications")

    def _create_allergies_table_from_text(self, section: Dict) -> Dict:
        """Create allergies table from free text"""
        content_html = section.get("content", {}).get("original", "")

        # Look for allergy data in the content
        allergies = []

        # Try to extract from structured content
        soup = BeautifulSoup(content_html, "html.parser")
        rows = soup.find_all("tr")

        if len(rows) > 1:  # Has header row
            for row in rows[1:]:  # Skip header
                cells = row.find_all(["td", "th"])
                if len(cells) >= 4:  # Minimum expected columns for allergies
                    allergy = [
                        cells[0].get_text().strip() if len(cells) > 0 else "",  # Type
                        cells[1].get_text().strip() if len(cells) > 1 else "",  # Agent
                        (
                            cells[2].get_text().strip() if len(cells) > 2 else ""
                        ),  # Manifestation
                        (
                            cells[3].get_text().strip() if len(cells) > 3 else ""
                        ),  # Severity
                        cells[4].get_text().strip() if len(cells) > 4 else "",  # Status
                    ]
                    allergies.append(allergy)

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
        return self._create_enhanced_section(section, table_data, "allergies")

    def _extract_problems_from_content(self, content_html: str) -> List[Dict]:
        """Extract problem information from HTML content"""
        problems = []
        # Implementation would parse content for problem data
        return problems

    def _create_enhanced_section(
        self, section: Dict, table_data: Dict, section_type: str
    ) -> Dict:
        """Create enhanced section with table data and HTML"""
        enhanced_section = section.copy()

        # Add table data
        enhanced_section["table_data"] = table_data
        enhanced_section["has_table"] = True
        enhanced_section["section_type"] = section_type

        # Generate PS Guidelines compliant HTML
        enhanced_section["table_html"] = self.generate_table_html(
            table_data, section_type
        )

        # Add PS Guidelines compliance markers
        enhanced_section["ps_compliant"] = True
        enhanced_section["table_style"] = f"ps-table-{section_type}"

        return enhanced_section

    def generate_table_html(self, table_data: Dict, section_type: str) -> str:
        """Generate PS Guidelines compliant HTML table"""
        if not table_data.get("headers") and not table_data.get("rows"):
            return ""

        html_parts = []

        # Table start with PS Guidelines classes
        html_parts.append(f'<table class="ps-table ps-table-{section_type}">')

        # Table headers
        if table_data.get("headers"):
            html_parts.append("<thead>")
            html_parts.append("<tr>")
            for header in table_data["headers"]:
                html_parts.append(f'<th class="ps-th">{header}</th>')
            html_parts.append("</tr>")
            html_parts.append("</thead>")

        # Table body
        if table_data.get("rows"):
            html_parts.append("<tbody>")
            for i, row in enumerate(table_data["rows"]):
                row_class = "ps-row-even" if i % 2 == 0 else "ps-row-odd"
                html_parts.append(f'<tr class="ps-tr {row_class}">')
                for cell in row:
                    html_parts.append(f'<td class="ps-td">{cell}</td>')
                html_parts.append("</tr>")
            html_parts.append("</tbody>")

        html_parts.append("</table>")

        return "".join(html_parts)
