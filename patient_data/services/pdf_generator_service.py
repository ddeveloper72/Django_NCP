"""
PDF Generation Service for Clinical Documents
Generates downloadable PDFs from CDA documents and patient summaries
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from io import BytesIO
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class PatientSummaryPDFGenerator:
    """Generate PDF documents from patient summary data"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""

        # Header style
        self.styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=self.styles["Heading1"],
                fontSize=18,
                spaceAfter=30,
                textColor=colors.HexColor("#2c3e50"),
                alignment=TA_CENTER,
            )
        )

        # Section header style
        self.styles.add(
            ParagraphStyle(
                name="SectionHeader",
                parent=self.styles["Heading2"],
                fontSize=14,
                spaceBefore=20,
                spaceAfter=10,
                textColor=colors.HexColor("#34495e"),
                borderWidth=1,
                borderColor=colors.HexColor("#bdc3c7"),
                borderPadding=5,
                backColor=colors.HexColor("#ecf0f1"),
            )
        )

        # Subsection header style
        self.styles.add(
            ParagraphStyle(
                name="SubsectionHeader",
                parent=self.styles["Heading3"],
                fontSize=12,
                spaceBefore=15,
                spaceAfter=5,
                textColor=colors.HexColor("#2980b9"),
            )
        )

        # Entry style
        self.styles.add(
            ParagraphStyle(
                name="EntryStyle",
                parent=self.styles["Normal"],
                fontSize=10,
                spaceBefore=5,
                spaceAfter=5,
                leftIndent=20,
                borderWidth=0.5,
                borderColor=colors.HexColor("#bdc3c7"),
                borderPadding=8,
                backColor=colors.HexColor("#f8f9fa"),
            )
        )

        # Code style
        self.styles.add(
            ParagraphStyle(
                name="CodeStyle",
                parent=self.styles["Normal"],
                fontSize=9,
                fontName="Courier",
                textColor=colors.HexColor("#666666"),
                backColor=colors.HexColor("#f1f1f1"),
            )
        )

        # Footer style
        self.styles.add(
            ParagraphStyle(
                name="Footer",
                parent=self.styles["Normal"],
                fontSize=8,
                alignment=TA_CENTER,
                textColor=colors.HexColor("#666666"),
            )
        )

    def generate_patient_summary_pdf(self, parsed_data: Dict[str, Any]) -> bytes:
        """
        Generate comprehensive patient summary PDF

        Args:
            parsed_data: Parsed CDA document data

        Returns:
            PDF content as bytes
        """
        buffer = BytesIO()

        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=inch,
                leftMargin=inch,
                topMargin=inch,
                bottomMargin=inch,
            )

            # Build document content
            story = []

            # Add header
            story.extend(self._build_header(parsed_data))

            # Add patient information
            story.extend(self._build_patient_info(parsed_data.get("patient_info", {})))

            # Add clinical sections
            story.extend(
                self._build_clinical_sections(parsed_data.get("clinical_sections", []))
            )

            # Add structured summary
            story.extend(
                self._build_structured_summary(parsed_data.get("structured_body", {}))
            )

            # Add footer
            story.extend(self._build_footer())

            # Build PDF
            doc.build(story)

            pdf_content = buffer.getvalue()
            logger.info(f"Generated patient summary PDF: {len(pdf_content)} bytes")

            return pdf_content

        except Exception as e:
            logger.error(f"Error generating patient summary PDF: {e}")
            raise
        finally:
            buffer.close()

    def _build_header(self, parsed_data: Dict[str, Any]) -> List:
        """Build document header"""
        story = []

        # Document title
        doc_info = parsed_data.get("document_info", {})
        title = doc_info.get("title", "Patient Summary")
        story.append(Paragraph(title, self.styles["CustomTitle"]))

        # Document metadata table
        metadata = [
            ["Document ID:", doc_info.get("document_id", "N/A")],
            [
                "Generated:",
                parsed_data.get(
                    "generation_timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ),
            ],
            [
                "Document Type:",
                doc_info.get("display_name", "Clinical Document Assembly"),
            ],
            ["Effective Time:", doc_info.get("formatted_time", "N/A")],
        ]

        if doc_info.get("authors"):
            author_names = []
            for author in doc_info["authors"]:
                if author.get("person") and author["person"].get("given"):
                    given = " ".join(author["person"]["given"])
                    family = author["person"].get("family", "")
                    author_names.append(f"{given} {family}".strip())
            if author_names:
                metadata.append(["Authors:", ", ".join(author_names)])

        if doc_info.get("custodian") and doc_info["custodian"].get("name"):
            metadata.append(["Custodian:", doc_info["custodian"]["name"]])

        # Create metadata table
        metadata_table = Table(metadata, colWidths=[2 * inch, 4 * inch])
        metadata_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#ecf0f1")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#bdc3c7")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        story.append(Spacer(1, 20))
        story.append(metadata_table)
        story.append(Spacer(1, 30))

        return story

    def _build_patient_info(self, patient_info: Dict[str, Any]) -> List:
        """Build patient information section"""
        story = []

        if not patient_info:
            return story

        story.append(Paragraph("Patient Information", self.styles["SectionHeader"]))

        # Patient demographics table
        demographics = []

        # Names
        if patient_info.get("names"):
            for name in patient_info["names"]:
                given_names = " ".join(name.get("given", []))
                family_name = name.get("family", "")
                full_name = f"{given_names} {family_name}".strip()
                if full_name:
                    use = name.get("use", "")
                    name_label = f"Name ({use})" if use else "Name"
                    demographics.append([name_label, full_name])

        # Birth date
        if patient_info.get("formatted_birth_date"):
            demographics.append(["Birth Date:", patient_info["formatted_birth_date"]])

        # Gender
        if patient_info.get("gender_display"):
            demographics.append(["Gender:", patient_info["gender_display"]])

        # Marital status
        if patient_info.get("marital_status") and patient_info["marital_status"].get(
            "display"
        ):
            demographics.append(
                ["Marital Status:", patient_info["marital_status"]["display"]]
            )

        # Patient identifiers
        if patient_info.get("identifiers"):
            for idx, identifier in enumerate(patient_info["identifiers"]):
                id_value = identifier.get("extension", identifier.get("root", ""))
                authority = identifier.get("assigningAuthorityName", "")
                if id_value:
                    id_label = (
                        f"Patient ID {idx + 1}"
                        if len(patient_info["identifiers"]) > 1
                        else "Patient ID"
                    )
                    if authority:
                        id_display = f"{id_value} ({authority})"
                    else:
                        id_display = id_value
                    demographics.append([id_label, id_display])

        # Languages
        if patient_info.get("languages"):
            lang_codes = [
                lang.get("code", "")
                for lang in patient_info["languages"]
                if lang.get("code")
            ]
            if lang_codes:
                demographics.append(["Languages:", ", ".join(lang_codes)])

        if demographics:
            demo_table = Table(demographics, colWidths=[2 * inch, 4 * inch])
            demo_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8f9fa")),
                        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#dee2e6")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )
            story.append(demo_table)
            story.append(Spacer(1, 15))

        # Contact information
        contact_info = []

        # Addresses
        if patient_info.get("addresses"):
            for idx, address in enumerate(patient_info["addresses"]):
                addr_parts = []
                if address.get("streetAddressLine"):
                    addr_parts.extend(address["streetAddressLine"])
                if address.get("city"):
                    addr_parts.append(address["city"])
                if address.get("state"):
                    addr_parts.append(address["state"])
                if address.get("postalCode"):
                    addr_parts.append(address["postalCode"])
                if address.get("country"):
                    addr_parts.append(address["country"])

                if addr_parts:
                    addr_label = (
                        f"Address {idx + 1}"
                        if len(patient_info["addresses"]) > 1
                        else "Address"
                    )
                    use = address.get("use", "")
                    if use:
                        addr_label += f" ({use})"
                    contact_info.append([addr_label, "<br/>".join(addr_parts)])

        # Telecoms
        if patient_info.get("telecoms"):
            for telecom in patient_info["telecoms"]:
                if telecom.get("type") == "phone" and telecom.get("number"):
                    use = telecom.get("use", "")
                    phone_label = f"Phone ({use})" if use else "Phone"
                    contact_info.append([phone_label, telecom["number"]])
                elif telecom.get("type") == "email" and telecom.get("email"):
                    contact_info.append(["Email:", telecom["email"]])

        if contact_info:
            story.append(
                Paragraph("Contact Information", self.styles["SubsectionHeader"])
            )
            contact_table = Table(contact_info, colWidths=[2 * inch, 4 * inch])
            contact_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8f9fa")),
                        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#dee2e6")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )
            story.append(contact_table)
            story.append(Spacer(1, 20))

        # Provider organization
        if patient_info.get("provider_organization"):
            story.append(
                Paragraph("Healthcare Provider", self.styles["SubsectionHeader"])
            )
            org = patient_info["provider_organization"]
            provider_info = []

            if org.get("name"):
                provider_info.append(["Organization:", org["name"]])

            if org.get("id"):
                org_id = org["id"].get("extension", org["id"].get("root", ""))
                if org_id:
                    provider_info.append(["Organization ID:", org_id])

            if org.get("telecoms"):
                for telecom in org["telecoms"]:
                    if telecom.get("type") == "phone" and telecom.get("number"):
                        provider_info.append(["Phone:", telecom["number"]])
                    elif telecom.get("type") == "email" and telecom.get("email"):
                        provider_info.append(["Email:", telecom["email"]])

            if provider_info:
                provider_table = Table(provider_info, colWidths=[2 * inch, 4 * inch])
                provider_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8f9fa")),
                            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, -1), 10),
                            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#dee2e6")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ]
                    )
                )
                story.append(provider_table)
                story.append(Spacer(1, 20))

        return story

    def _build_clinical_sections(self, sections: List) -> List:
        """Build clinical sections"""
        story = []

        if not sections:
            return story

        story.append(Paragraph("Clinical Information", self.styles["SectionHeader"]))

        for section in sections:
            # Section title
            section_title = f"{section.title}"
            if hasattr(section, "code") and section.code:
                section_title += f" ({section.code})"

            story.append(Paragraph(section_title, self.styles["SubsectionHeader"]))

            # Narrative text
            if hasattr(section, "narrative_text") and section.narrative_text:
                story.append(Paragraph(section.narrative_text, self.styles["Normal"]))
                story.append(Spacer(1, 10))

            # Structured entries
            if hasattr(section, "entries") and section.entries:
                for entry in section.entries:
                    entry_content = self._format_entry_for_pdf(entry)
                    if entry_content:
                        story.append(
                            Paragraph(entry_content, self.styles["EntryStyle"])
                        )
                        story.append(Spacer(1, 5))

            story.append(Spacer(1, 15))

        return story

    def _format_entry_for_pdf(self, entry: Dict[str, Any]) -> str:
        """Format entry for PDF display"""
        content_parts = []

        # Entry type
        entry_type = entry.get("type", "Unknown")
        content_parts.append(f"<b>Type:</b> {entry_type.title()}")

        # Code information
        if entry.get("code"):
            code_info = entry["code"]
            display_name = code_info.get("displayName", code_info.get("code", ""))
            code_value = code_info.get("code", "")
            if display_name:
                code_text = f"<b>Code:</b> {display_name}"
                if code_value:
                    code_text += (
                        f" <font name='Courier' color='#666666'>({code_value})</font>"
                    )
                content_parts.append(code_text)

        # Value
        if entry.get("value"):
            value_info = entry["value"]
            if isinstance(value_info, dict):
                if value_info.get("displayName"):
                    content_parts.append(f"<b>Value:</b> {value_info['displayName']}")
                elif value_info.get("value"):
                    value_text = f"<b>Value:</b> {value_info['value']}"
                    if value_info.get("unit"):
                        value_text += f" {value_info['unit']}"
                    content_parts.append(value_text)
            else:
                content_parts.append(f"<b>Value:</b> {value_info}")

        # Effective time
        if entry.get("effective_time"):
            time_info = entry["effective_time"]
            if isinstance(time_info, dict):
                if time_info.get("formatted"):
                    content_parts.append(f"<b>Date:</b> {time_info['formatted']}")
                elif time_info.get("low_formatted") and time_info.get("high_formatted"):
                    content_parts.append(
                        f"<b>Period:</b> {time_info['low_formatted']} to {time_info['high_formatted']}"
                    )
                elif time_info.get("low_formatted"):
                    content_parts.append(
                        f"<b>Start Date:</b> {time_info['low_formatted']}"
                    )
            elif isinstance(time_info, str):
                content_parts.append(f"<b>Date:</b> {time_info}")

        # Status
        if entry.get("status"):
            content_parts.append(f"<b>Status:</b> {entry['status']}")

        # Interpretation
        if entry.get("interpretation"):
            interp = entry["interpretation"]
            display = interp.get("displayName", interp.get("code", ""))
            if display:
                content_parts.append(f"<b>Interpretation:</b> {display}")

        # Medication-specific information
        if entry.get("dose"):
            dose = entry["dose"]
            dose_text = (
                f"<b>Dose:</b> {dose.get('value', '')} {dose.get('unit', '')}".strip()
            )
            content_parts.append(dose_text)

        if entry.get("route"):
            route = entry["route"]
            route_display = route.get("displayName", route.get("code", ""))
            if route_display:
                content_parts.append(f"<b>Route:</b> {route_display}")

        if entry.get("medication"):
            med = entry["medication"]
            if med.get("name"):
                content_parts.append(f"<b>Medication:</b> {med['name']}")
            elif med.get("code") and med["code"].get("displayName"):
                content_parts.append(f"<b>Medication:</b> {med['code']['displayName']}")

        return "<br/>".join(content_parts)

    def _build_structured_summary(self, structured_body: Dict[str, Any]) -> List:
        """Build structured summary section"""
        story = []

        if not structured_body:
            return story

        story.append(PageBreak())
        story.append(
            Paragraph("Structured Clinical Summary", self.styles["SectionHeader"])
        )

        # Define section mappings for better organization
        section_mappings = {
            "allergies": "Allergies and Intolerances",
            "medications": "Current Medications",
            "problems": "Active Problems",
            "procedures": "Medical Procedures",
            "vital_signs": "Vital Signs",
            "laboratory_results": "Laboratory Results",
            "immunizations": "Immunization History",
            "social_history": "Social History",
            "functional_status": "Functional Status",
            "advance_directives": "Advance Directives",
        }

        for key, title in section_mappings.items():
            entries = structured_body.get(key, [])
            if entries:
                story.append(Paragraph(title, self.styles["SubsectionHeader"]))

                for entry in entries:
                    entry_content = self._format_entry_for_pdf(entry)
                    if entry_content:
                        story.append(
                            Paragraph(entry_content, self.styles["EntryStyle"])
                        )
                        story.append(Spacer(1, 5))

                story.append(Spacer(1, 15))

        return story

    def _build_footer(self) -> List:
        """Build document footer"""
        story = []

        story.append(Spacer(1, 30))

        footer_text = f"""
        <br/><br/>
        ─────────────────────────────────────────────────────────────<br/>
        This document was generated by the EU eHealth Network Cross-Border Patient Summary System.<br/>
        Generated on: {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}<br/>
        Document contains clinical information extracted from HL7 CDA Level 3 structured documents.<br/>
        For questions about this summary, please contact the issuing healthcare provider.
        """

        story.append(Paragraph(footer_text, self.styles["Footer"]))

        return story
