"""
PDF Generation Service

Handles generation of PDF documents from patient summaries using ReportLab.
Supports both CDA and FHIR bundle derived data.
"""

import io
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

logger = logging.getLogger(__name__)


class PDFGenerationService:
    """Service for generating PDF documents from patient data."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for PDF generation."""
        # Header styles
        self.styles.add(
            ParagraphStyle(
                "CustomTitle",
                parent=self.styles["Title"],
                fontSize=18,
                spaceAfter=30,
                textColor=colors.HexColor("#2c3e50"),
            )
        )

        self.styles.add(
            ParagraphStyle(
                "SectionHeader",
                parent=self.styles["Heading1"],
                fontSize=14,
                spaceAfter=12,
                spaceBefore=20,
                textColor=colors.HexColor("#34495e"),
                borderWidth=1,
                borderColor=colors.HexColor("#bdc3c7"),
                borderPadding=5,
            )
        )

        self.styles.add(
            ParagraphStyle(
                "SubHeader",
                parent=self.styles["Heading2"],
                fontSize=12,
                spaceAfter=8,
                spaceBefore=12,
                textColor=colors.HexColor("#7f8c8d"),
            )
        )

        # Content styles
        self.styles.add(
            ParagraphStyle(
                "DetailLabel",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.HexColor("#2c3e50"),
                fontName="Helvetica-Bold",
            )
        )

        self.styles.add(
            ParagraphStyle(
                "DetailValue",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.HexColor("#34495e"),
                leftIndent=20,
            )
        )

        self.styles.add(
            ParagraphStyle(
                "TableHeader",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.white,
                fontName="Helvetica-Bold",
                alignment=TA_CENTER,
            )
        )

        self.styles.add(
            ParagraphStyle(
                "TableCell",
                parent=self.styles["Normal"],
                fontSize=8,
                textColor=colors.HexColor("#2c3e50"),
            )
        )

        self.styles.add(
            ParagraphStyle(
                "Metadata",
                parent=self.styles["Normal"],
                fontSize=8,
                textColor=colors.HexColor("#95a5a6"),
                alignment=TA_RIGHT,
            )
        )

    def generate_patient_summary_pdf(self, pdf_data: Dict[str, Any]) -> bytes:
        """
        Generate a comprehensive patient summary PDF.

        Args:
            pdf_data: Structured patient data for PDF generation

        Returns:
            bytes: PDF file content
        """
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )

            # Build PDF content
            story = []

            # Add title page
            story.extend(self._build_title_page(pdf_data))

            # Add table of contents
            story.append(PageBreak())
            story.extend(self._build_table_of_contents(pdf_data))

            # Add patient demographics
            story.append(PageBreak())
            story.extend(
                self._build_patient_demographics(pdf_data.get("patient_info", {}))
            )

            # Add clinical sections
            for section in pdf_data.get("sections", []):
                story.append(PageBreak())
                story.extend(self._build_clinical_section(section))

            # Add metadata footer
            story.extend(self._build_metadata_section(pdf_data))

            # Build PDF
            doc.build(story)

            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()

            return pdf_bytes

        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            raise

    def _build_title_page(self, pdf_data: Dict[str, Any]) -> List:
        """Build the title page of the PDF."""
        story = []

        # Main title
        title = pdf_data.get("title", "Patient Summary")
        story.append(Paragraph(title, self.styles["CustomTitle"]))
        story.append(Spacer(1, 20))

        # Patient info summary
        patient_info = pdf_data.get("patient_info", {})
        if patient_info:
            name = patient_info.get("name", {})
            if isinstance(name, dict):
                patient_name = (
                    f"{' '.join(name.get('given', []))} {name.get('family', '')}"
                )
            else:
                patient_name = str(name)

            story.append(
                Paragraph(f"<b>Patient:</b> {patient_name}", self.styles["Normal"])
            )

            if patient_info.get("birth_date"):
                story.append(
                    Paragraph(
                        f"<b>Date of Birth:</b> {patient_info['birth_date']}",
                        self.styles["Normal"],
                    )
                )

            if patient_info.get("gender"):
                story.append(
                    Paragraph(
                        f"<b>Gender:</b> {patient_info['gender'].title()}",
                        self.styles["Normal"],
                    )
                )

        story.append(Spacer(1, 30))

        # Generation info
        generated_date = pdf_data.get(
            "generated_date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        story.append(
            Paragraph(f"<b>Generated:</b> {generated_date}", self.styles["Normal"])
        )

        # Summary statistics
        sections = pdf_data.get("sections", [])
        if sections:
            story.append(Spacer(1, 20))
            story.append(
                Paragraph("<b>Summary Statistics:</b>", self.styles["SubHeader"])
            )

            stats_data = [["Section", "Items"]]
            for section in sections:
                item_count = self._get_section_item_count(section)
                stats_data.append([section["title"], str(item_count)])

            stats_table = Table(stats_data, colWidths=[3 * inch, 1 * inch])
            stats_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("FONTSIZE", (0, 1), (-1, -1), 9),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )
            story.append(stats_table)

        return story

    def _build_table_of_contents(self, pdf_data: Dict[str, Any]) -> List:
        """Build table of contents."""
        story = []

        story.append(Paragraph("Table of Contents", self.styles["CustomTitle"]))
        story.append(Spacer(1, 20))

        # TOC entries
        toc_data = [["Section", "Page"]]
        toc_data.append(["Patient Demographics", "3"])

        page_num = 4
        for section in pdf_data.get("sections", []):
            toc_data.append([section["title"], str(page_num)])
            page_num += 1

        toc_table = Table(toc_data, colWidths=[4 * inch, 1 * inch])
        toc_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        story.append(toc_table)

        return story

    def _build_patient_demographics(self, patient_info: Dict[str, Any]) -> List:
        """Build patient demographics section."""
        story = []

        story.append(Paragraph("Patient Demographics", self.styles["SectionHeader"]))
        story.append(Spacer(1, 12))

        if not patient_info:
            story.append(
                Paragraph(
                    "No patient demographic information available.",
                    self.styles["Normal"],
                )
            )
            return story

        # Basic information
        demo_data = []

        # Name
        name = patient_info.get("name", {})
        if isinstance(name, dict):
            full_name = f"{' '.join(name.get('given', []))} {name.get('family', '')}"
            demo_data.append(["Full Name", full_name])

            if name.get("prefix"):
                demo_data.append(["Prefix", ", ".join(name["prefix"])])
            if name.get("suffix"):
                demo_data.append(["Suffix", ", ".join(name["suffix"])])

        # Basic demographics
        if patient_info.get("birth_date"):
            demo_data.append(["Date of Birth", patient_info["birth_date"]])

        if patient_info.get("gender"):
            demo_data.append(["Gender", patient_info["gender"].title()])

        if patient_info.get("marital_status"):
            demo_data.append(["Marital Status", str(patient_info["marital_status"])])

        # Identifiers
        identifiers = patient_info.get("identifiers", [])
        if identifiers:
            for i, identifier in enumerate(identifiers):
                id_type = identifier.get("type", f"ID {i+1}")
                demo_data.append(
                    [f"Identifier ({id_type})", identifier.get("value", "N/A")]
                )

        if demo_data:
            demo_table = Table(demo_data, colWidths=[2 * inch, 3 * inch])
            demo_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#ecf0f1")),
                        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#2c3e50")),
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#bdc3c7")),
                    ]
                )
            )
            story.append(demo_table)

        # Address information
        addresses = patient_info.get("address", [])
        if addresses:
            story.append(Spacer(1, 15))
            story.append(Paragraph("Address Information", self.styles["SubHeader"]))

            for i, address in enumerate(addresses):
                if len(addresses) > 1:
                    story.append(
                        Paragraph(f"Address {i+1}:", self.styles["DetailLabel"])
                    )

                addr_lines = []
                if address.get("line"):
                    addr_lines.extend(address["line"])

                if address.get("city"):
                    city_line = address["city"]
                    if address.get("state"):
                        city_line += f", {address['state']}"
                    if address.get("postal_code"):
                        city_line += f" {address['postal_code']}"
                    addr_lines.append(city_line)

                if address.get("country"):
                    addr_lines.append(address["country"])

                if address.get("use"):
                    addr_lines.append(f"({address['use']})")

                story.append(
                    Paragraph("<br/>".join(addr_lines), self.styles["DetailValue"])
                )
                story.append(Spacer(1, 8))

        # Contact information
        telecom = patient_info.get("telecom", [])
        if telecom:
            story.append(Spacer(1, 15))
            story.append(Paragraph("Contact Information", self.styles["SubHeader"]))

            contact_data = []
            for contact in telecom:
                contact_type = contact.get("system", "Contact").title()
                contact_value = contact.get("value", "N/A")
                contact_use = contact.get("use", "")

                display_value = contact_value
                if contact_use:
                    display_value += f" ({contact_use})"

                contact_data.append([contact_type, display_value])

            if contact_data:
                contact_table = Table(contact_data, colWidths=[1.5 * inch, 3.5 * inch])
                contact_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#ecf0f1")),
                            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#2c3e50")),
                            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                            ("FONTSIZE", (0, 0), (-1, -1), 9),
                            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#bdc3c7")),
                        ]
                    )
                )
                story.append(contact_table)

        return story

    def _build_clinical_section(self, section: Dict[str, Any]) -> List:
        """Build a clinical section of the PDF."""
        story = []

        title = section.get("title", "Clinical Section")
        story.append(Paragraph(title, self.styles["SectionHeader"]))
        story.append(Spacer(1, 12))

        section_type = section.get("type", "")
        data = section.get("data", [])

        if not data:
            story.append(
                Paragraph("No data available for this section.", self.styles["Normal"])
            )
            return story

        # Handle different section types
        if section_type == "conditions":
            story.extend(self._build_conditions_section(data))
        elif section_type == "medications":
            story.extend(self._build_medications_section(data))
        elif section_type == "observations":
            story.extend(self._build_observations_section(data))
        elif section_type == "procedures":
            story.extend(self._build_procedures_section(data))
        elif section_type == "allergies":
            story.extend(self._build_allergies_section(data))
        elif section_type == "immunizations":
            story.extend(self._build_immunizations_section(data))
        elif section_type == "encounters":
            story.extend(self._build_encounters_section(data))
        elif section_type == "diagnostic_reports":
            story.extend(self._build_diagnostic_reports_section(data))
        else:
            # Generic section handling
            story.extend(self._build_generic_section(data))

        return story

    def _build_conditions_section(self, conditions: List[Dict[str, Any]]) -> List:
        """Build conditions/problems section."""
        story = []

        if not conditions:
            story.append(Paragraph("No conditions recorded.", self.styles["Normal"]))
            return story

        # Table headers
        headers = ["Condition", "Status", "Severity", "Onset", "Notes"]
        table_data = [headers]

        for condition in conditions:
            code_info = condition.get("code", {})
            condition_name = self._extract_display_name(code_info)

            clinical_status = condition.get("clinical_status", "Unknown")
            severity = (
                self._extract_display_name(condition.get("severity", {}))
                or "Not specified"
            )
            onset = self._format_onset(condition.get("onset", {}))
            notes = "; ".join(condition.get("notes", [])[:2])  # Limit notes

            table_data.append(
                [
                    condition_name,
                    clinical_status.title(),
                    severity,
                    onset,
                    notes[:50] + "..." if len(notes) > 50 else notes,
                ]
            )

        table = Table(
            table_data, colWidths=[2 * inch, 1 * inch, 1 * inch, 1 * inch, 1.5 * inch]
        )
        table.setStyle(self._get_table_style())
        story.append(table)

        return story

    def _build_medications_section(self, medications: List[Dict[str, Any]]) -> List:
        """Build medications section."""
        story = []

        if not medications:
            story.append(Paragraph("No medications recorded.", self.styles["Normal"]))
            return story

        headers = ["Medication", "Status", "Dosage", "Effective Period"]
        table_data = [headers]

        for medication in medications:
            med_info = medication.get("medication", {})
            med_name = self._extract_display_name(med_info)

            status = medication.get("status", "Unknown")
            dosage = self._format_dosage(medication.get("dosage", []))
            effective_period = self._format_period(
                medication.get("effective_period", {})
            )

            table_data.append([med_name, status.title(), dosage, effective_period])

        table = Table(
            table_data, colWidths=[2.5 * inch, 1 * inch, 2 * inch, 1.5 * inch]
        )
        table.setStyle(self._get_table_style())
        story.append(table)

        return story

    def _build_observations_section(self, observations: List[Dict[str, Any]]) -> List:
        """Build observations/vital signs section."""
        story = []

        if not observations:
            story.append(Paragraph("No observations recorded.", self.styles["Normal"]))
            return story

        headers = ["Observation", "Value", "Date", "Status"]
        table_data = [headers]

        for observation in observations:
            code_info = observation.get("code", {})
            obs_name = self._extract_display_name(code_info)

            value = self._format_observation_value(observation.get("value", {}))
            date = observation.get("effective_datetime", "Not specified")
            if date and date != "Not specified":
                date = date.split("T")[0]  # Just the date part

            status = observation.get("status", "Unknown")

            table_data.append([obs_name, value, date, status.title()])

        table = Table(
            table_data, colWidths=[2 * inch, 1.5 * inch, 1.5 * inch, 1 * inch]
        )
        table.setStyle(self._get_table_style())
        story.append(table)

        return story

    def _build_procedures_section(self, procedures: List[Dict[str, Any]]) -> List:
        """Build procedures section."""
        story = []

        if not procedures:
            story.append(Paragraph("No procedures recorded.", self.styles["Normal"]))
            return story

        headers = ["Procedure", "Status", "Date", "Outcome"]
        table_data = [headers]

        for procedure in procedures:
            code_info = procedure.get("code", {})
            proc_name = self._extract_display_name(code_info)

            status = procedure.get("status", "Unknown")
            date = procedure.get("performed_datetime", "Not specified")
            if date and date != "Not specified":
                date = date.split("T")[0]

            outcome = (
                self._extract_display_name(procedure.get("outcome", {}))
                or "Not specified"
            )

            table_data.append([proc_name, status.title(), date, outcome])

        table = Table(
            table_data, colWidths=[2.5 * inch, 1 * inch, 1.5 * inch, 1.5 * inch]
        )
        table.setStyle(self._get_table_style())
        story.append(table)

        return story

    def _build_allergies_section(self, allergies: List[Dict[str, Any]]) -> List:
        """Build allergies section."""
        story = []

        if not allergies:
            story.append(Paragraph("No allergies recorded.", self.styles["Normal"]))
            return story

        headers = ["Allergen", "Type", "Criticality", "Status", "Reactions"]
        table_data = [headers]

        for allergy in allergies:
            code_info = allergy.get("code", {})
            allergen = self._extract_display_name(code_info)

            allergy_type = allergy.get("type", "Unknown")
            criticality = allergy.get("criticality", "Unknown")
            status = allergy.get("clinical_status", "Unknown")

            reactions = []
            for reaction in allergy.get("reactions", []):
                manifestations = reaction.get("manifestation", [])
                for manifest in manifestations:
                    reactions.append(self._extract_display_name(manifest))

            reactions_text = ", ".join(reactions[:3])  # Limit to first 3

            table_data.append(
                [
                    allergen,
                    allergy_type.title(),
                    criticality.title(),
                    status.title(),
                    reactions_text,
                ]
            )

        table = Table(
            table_data, colWidths=[1.5 * inch, 1 * inch, 1 * inch, 1 * inch, 2.5 * inch]
        )
        table.setStyle(self._get_table_style())
        story.append(table)

        return story

    def _build_immunizations_section(self, immunizations: List[Dict[str, Any]]) -> List:
        """Build immunizations section."""
        story = []

        if not immunizations:
            story.append(Paragraph("No immunizations recorded.", self.styles["Normal"]))
            return story

        headers = ["Vaccine", "Date", "Status", "Lot Number"]
        table_data = [headers]

        for immunization in immunizations:
            vaccine_info = immunization.get("vaccine_code", {})
            vaccine_name = self._extract_display_name(vaccine_info)

            date = immunization.get("occurrence_datetime", "Not specified")
            if date and date != "Not specified":
                date = date.split("T")[0]

            status = immunization.get("status", "Unknown")
            lot_number = immunization.get("lot_number", "Not recorded")

            table_data.append([vaccine_name, date, status.title(), lot_number])

        table = Table(
            table_data, colWidths=[2.5 * inch, 1.5 * inch, 1 * inch, 1.5 * inch]
        )
        table.setStyle(self._get_table_style())
        story.append(table)

        return story

    def _build_encounters_section(self, encounters: List[Dict[str, Any]]) -> List:
        """Build encounters section."""
        story = []

        if not encounters:
            story.append(Paragraph("No encounters recorded.", self.styles["Normal"]))
            return story

        headers = ["Type", "Status", "Period", "Class"]
        table_data = [headers]

        for encounter in encounters:
            enc_types = encounter.get("type", [])
            enc_type = (
                ", ".join([self._extract_display_name(t) for t in enc_types])
                if enc_types
                else "Not specified"
            )

            status = encounter.get("status", "Unknown")
            period = self._format_period(encounter.get("period", {}))
            enc_class = encounter.get("class", "Not specified")

            table_data.append([enc_type, status.title(), period, enc_class.title()])

        table = Table(table_data, colWidths=[2 * inch, 1 * inch, 2 * inch, 1.5 * inch])
        table.setStyle(self._get_table_style())
        story.append(table)

        return story

    def _build_diagnostic_reports_section(self, reports: List[Dict[str, Any]]) -> List:
        """Build diagnostic reports section."""
        story = []

        if not reports:
            story.append(
                Paragraph("No diagnostic reports recorded.", self.styles["Normal"])
            )
            return story

        headers = ["Report Type", "Status", "Date", "Conclusion"]
        table_data = [headers]

        for report in reports:
            code_info = report.get("code", {})
            report_type = self._extract_display_name(code_info)

            status = report.get("status", "Unknown")
            date = report.get("effective_datetime", "Not specified")
            if date and date != "Not specified":
                date = date.split("T")[0]

            conclusion = report.get("conclusion", "No conclusion")[:50]
            if len(conclusion) == 50:
                conclusion += "..."

            table_data.append([report_type, status.title(), date, conclusion])

        table = Table(
            table_data, colWidths=[2 * inch, 1 * inch, 1.5 * inch, 2.5 * inch]
        )
        table.setStyle(self._get_table_style())
        story.append(table)

        return story

    def _build_generic_section(self, data: Any) -> List:
        """Build a generic section for unknown data types."""
        story = []

        if isinstance(data, list) and data:
            story.append(
                Paragraph(f"Contains {len(data)} items", self.styles["Normal"])
            )

            # Show first few items as examples
            for i, item in enumerate(data[:3]):
                story.append(
                    Paragraph(
                        f"Item {i+1}: {str(item)[:100]}...", self.styles["DetailValue"]
                    )
                )

        elif isinstance(data, dict):
            story.append(Paragraph("Data structure:", self.styles["Normal"]))
            for key, value in list(data.items())[:5]:  # Show first 5 keys
                story.append(
                    Paragraph(
                        f"<b>{key}:</b> {str(value)[:50]}...",
                        self.styles["DetailValue"],
                    )
                )

        else:
            story.append(Paragraph(str(data), self.styles["Normal"]))

        return story

    def _build_metadata_section(self, pdf_data: Dict[str, Any]) -> List:
        """Build metadata section."""
        story = []

        story.append(Spacer(1, 30))
        story.append(Paragraph("Document Information", self.styles["SubHeader"]))

        generated_date = pdf_data.get(
            "generated_date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        story.append(Paragraph(f"Generated: {generated_date}", self.styles["Metadata"]))
        story.append(
            Paragraph(
                "This document was automatically generated from clinical data.",
                self.styles["Metadata"],
            )
        )

        return story

    # Helper methods
    def _get_table_style(self) -> TableStyle:
        """Get standard table style."""
        return TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )

    def _get_section_item_count(self, section: Dict[str, Any]) -> int:
        """Get the number of items in a section."""
        data = section.get("data", [])
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict):
            return len(data)
        else:
            return 1

    def _extract_display_name(self, code_info: Dict[str, Any]) -> str:
        """Extract display name from code information."""
        if not code_info:
            return "Not specified"

        # Try text first
        if code_info.get("text"):
            return code_info["text"]

        # Try coding display
        coding = code_info.get("coding", [])
        if coding and coding[0].get("display"):
            return coding[0]["display"]

        # Try coding code
        if coding and coding[0].get("code"):
            return coding[0]["code"]

        return "Not specified"

    def _format_onset(self, onset: Dict[str, Any]) -> str:
        """Format onset information."""
        if not onset:
            return "Not specified"

        if onset.get("datetime"):
            return onset["datetime"].split("T")[0]
        elif onset.get("age"):
            return f"Age {onset['age']}"
        elif onset.get("period"):
            return self._format_period(onset["period"])
        elif onset.get("string"):
            return onset["string"]

        return "Not specified"

    def _format_dosage(self, dosages: List[Dict[str, Any]]) -> str:
        """Format dosage information."""
        if not dosages:
            return "Not specified"

        dosage_strs = []
        for dosage in dosages[:2]:  # Limit to first 2
            if dosage.get("text"):
                dosage_strs.append(dosage["text"])
            elif dosage.get("dose_quantity"):
                dosage_strs.append(dosage["dose_quantity"])

        return "; ".join(dosage_strs) if dosage_strs else "Not specified"

    def _format_period(self, period: Dict[str, Any]) -> str:
        """Format period information."""
        if not period:
            return "Not specified"

        start = period.get("start", "").split("T")[0] if period.get("start") else ""
        end = period.get("end", "").split("T")[0] if period.get("end") else ""

        if start and end:
            return f"{start} to {end}"
        elif start:
            return f"From {start}"
        elif end:
            return f"Until {end}"

        return "Not specified"

    def _format_observation_value(self, value: Dict[str, Any]) -> str:
        """Format observation value."""
        if not value:
            return "Not recorded"

        if value.get("quantity"):
            qty = value["quantity"]
            val = qty.get("value", "")
            unit = qty.get("unit", "")
            return f"{val} {unit}".strip()
        elif value.get("codeable_concept"):
            return self._extract_display_name(value["codeable_concept"])
        elif value.get("string"):
            return value["string"]
        elif value.get("boolean") is not None:
            return "Yes" if value["boolean"] else "No"
        elif value.get("integer") is not None:
            return str(value["integer"])

        return "Not recorded"
