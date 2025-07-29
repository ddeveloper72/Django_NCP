"""
Clinical Document Processing Services
Services for retrieving, processing, and rendering clinical documents
"""

import xml.etree.ElementTree as ET
import json
import base64
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from django.conf import settings
from django.utils import timezone
import requests
import uuid

logger = logging.getLogger(__name__)


class CDAProcessor:
    """Process CDA documents (Level 1 and Level 3)"""

    def __init__(self):
        self.namespaces = {
            "cda": "urn:hl7-org:v3",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        }

    def parse_cda_document(self, cda_content: str) -> Dict[str, Any]:
        """Parse CDA document and extract metadata and content"""
        try:
            root = ET.fromstring(cda_content)

            # Extract document metadata
            metadata = {
                "document_id": self._get_text(root, ".//cda:id/@extension"),
                "title": self._get_text(root, ".//cda:title"),
                "creation_time": self._get_text(root, ".//cda:effectiveTime/@value"),
                "author": self._extract_author_info(root),
                "patient": self._extract_patient_info(root),
                "sections": self._extract_sections(root),
                "document_type": "CDA_L3" if self._is_level3(root) else "CDA_L1",
            }

            return metadata

        except ET.ParseError as e:
            logger.error(f"Error parsing CDA document: {e}")
            raise ValueError(f"Invalid CDA XML: {e}")
        except Exception as e:
            logger.error(f"Error processing CDA document: {e}")
            raise

    def _get_text(self, root, xpath, default=""):
        """Get text content from XPath"""
        try:
            elements = root.findall(xpath, self.namespaces)
            return elements[0].text if elements and elements[0].text else default
        except:
            return default

    def _extract_author_info(self, root) -> Dict[str, str]:
        """Extract author information"""
        try:
            author_element = root.find(".//cda:author", self.namespaces)
            if author_element is not None:
                return {
                    "name": self._get_text(author_element, ".//cda:name"),
                    "institution": self._get_text(
                        author_element, ".//cda:representedOrganization/cda:name"
                    ),
                }
        except:
            pass
        return {"name": "Unknown", "institution": "Unknown"}

    def _extract_patient_info(self, root) -> Dict[str, str]:
        """Extract patient information"""
        try:
            patient_element = root.find(".//cda:patient", self.namespaces)
            if patient_element is not None:
                return {
                    "name": self._get_text(patient_element, ".//cda:name"),
                    "birth_time": self._get_text(
                        patient_element, ".//cda:birthTime/@value"
                    ),
                    "gender": self._get_text(
                        patient_element, ".//cda:administrativeGenderCode/@code"
                    ),
                }
        except:
            pass
        return {}

    def _extract_sections(self, root) -> list:
        """Extract document sections"""
        sections = []
        try:
            section_elements = root.findall(".//cda:section", self.namespaces)
            for section in section_elements:
                section_data = {
                    "title": self._get_text(section, ".//cda:title"),
                    "code": self._get_text(section, ".//cda:code/@code"),
                    "text": self._get_section_text(section),
                }
                sections.append(section_data)
        except Exception as e:
            logger.warning(f"Error extracting sections: {e}")
        return sections

    def _get_section_text(self, section) -> str:
        """Get formatted text content from section"""
        try:
            text_element = section.find(".//cda:text", self.namespaces)
            if text_element is not None:
                return ET.tostring(
                    text_element, encoding="unicode", method="text"
                ).strip()
        except:
            pass
        return ""

    def _is_level3(self, root) -> bool:
        """Check if document is CDA Level 3 (structured)"""
        try:
            # Level 3 documents have structured entries
            entries = root.findall(".//cda:entry", self.namespaces)
            return len(entries) > 0
        except:
            return False

    def render_as_html(self, cda_content: str, include_styles: bool = True) -> str:
        """Render CDA document as HTML"""
        try:
            metadata = self.parse_cda_document(cda_content)

            html_parts = []

            if include_styles:
                html_parts.append(
                    """
                <style>
                .cda-document { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .cda-header { border-bottom: 2px solid #2c3e50; padding-bottom: 20px; margin-bottom: 30px; }
                .cda-title { font-size: 24px; font-weight: bold; color: #2c3e50; margin-bottom: 10px; }
                .cda-metadata { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
                .cda-section { margin-bottom: 30px; border-left: 4px solid #3498db; padding-left: 15px; }
                .cda-section-title { font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px; }
                .cda-section-content { line-height: 1.6; }
                .cda-patient-info { background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
                </style>
                """
                )

            html_parts.append('<div class="cda-document">')

            # Document header
            html_parts.append('<div class="cda-header">')
            html_parts.append(
                f'<div class="cda-title">{metadata.get("title", "Clinical Document")}</div>'
            )

            html_parts.append('<div class="cda-metadata">')
            html_parts.append(
                f'<div><strong>Document ID:</strong> {metadata.get("document_id", "N/A")}</div>'
            )
            html_parts.append(
                f'<div><strong>Created:</strong> {self._format_hl7_date(metadata.get("creation_time", ""))}</div>'
            )
            html_parts.append(
                f'<div><strong>Author:</strong> {metadata.get("author", {}).get("name", "N/A")}</div>'
            )
            html_parts.append(
                f'<div><strong>Institution:</strong> {metadata.get("author", {}).get("institution", "N/A")}</div>'
            )
            html_parts.append("</div>")
            html_parts.append("</div>")

            # Patient information
            patient = metadata.get("patient", {})
            if patient:
                html_parts.append('<div class="cda-patient-info">')
                html_parts.append("<h3>Patient Information</h3>")
                html_parts.append(
                    f'<p><strong>Name:</strong> {patient.get("name", "N/A")}</p>'
                )
                html_parts.append(
                    f'<p><strong>Birth Date:</strong> {self._format_hl7_date(patient.get("birth_time", ""))}</p>'
                )
                html_parts.append(
                    f'<p><strong>Gender:</strong> {patient.get("gender", "N/A")}</p>'
                )
                html_parts.append("</div>")

            # Document sections
            for section in metadata.get("sections", []):
                if section["title"] or section["text"]:
                    html_parts.append('<div class="cda-section">')
                    if section["title"]:
                        html_parts.append(
                            f'<div class="cda-section-title">{section["title"]}</div>'
                        )
                    if section["text"]:
                        html_parts.append(
                            f'<div class="cda-section-content">{section["text"]}</div>'
                        )
                    html_parts.append("</div>")

            html_parts.append("</div>")

            return "\n".join(html_parts)

        except Exception as e:
            logger.error(f"Error rendering CDA as HTML: {e}")
            return f"<div class='error'>Error rendering document: {e}</div>"

    def _format_hl7_date(self, hl7_date: str) -> str:
        """Format HL7 date string to human readable format"""
        if not hl7_date:
            return "N/A"
        try:
            # HL7 dates are typically in format YYYYMMDDHHMMSS
            if len(hl7_date) >= 8:
                year = hl7_date[:4]
                month = hl7_date[4:6]
                day = hl7_date[6:8]
                return f"{day}/{month}/{year}"
        except:
            pass
        return hl7_date


class FHIRProcessor:
    """Process FHIR bundles and resources"""

    def parse_fhir_bundle(self, fhir_content: str) -> Dict[str, Any]:
        """Parse FHIR bundle and extract metadata and content"""
        try:
            bundle = json.loads(fhir_content)

            if bundle.get("resourceType") != "Bundle":
                raise ValueError("Not a valid FHIR Bundle")

            metadata = {
                "bundle_id": bundle.get("id", ""),
                "type": bundle.get("type", ""),
                "timestamp": bundle.get("timestamp", ""),
                "total": bundle.get("total", 0),
                "entries": self._extract_entries(bundle),
                "patient": self._find_patient_resource(bundle),
                "composition": self._find_composition_resource(bundle),
                "document_type": "FHIR_BUNDLE",
            }

            return metadata

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing FHIR JSON: {e}")
            raise ValueError(f"Invalid FHIR JSON: {e}")
        except Exception as e:
            logger.error(f"Error processing FHIR bundle: {e}")
            raise

    def _extract_entries(self, bundle: Dict) -> list:
        """Extract entries from FHIR bundle"""
        entries = []
        for entry in bundle.get("entry", []):
            if "resource" in entry:
                resource = entry["resource"]
                entries.append(
                    {
                        "resourceType": resource.get("resourceType"),
                        "id": resource.get("id"),
                        "fullUrl": entry.get("fullUrl"),
                    }
                )
        return entries

    def _find_patient_resource(self, bundle: Dict) -> Optional[Dict]:
        """Find Patient resource in bundle"""
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            if resource.get("resourceType") == "Patient":
                return resource
        return None

    def _find_composition_resource(self, bundle: Dict) -> Optional[Dict]:
        """Find Composition resource in bundle"""
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            if resource.get("resourceType") == "Composition":
                return resource
        return None

    def render_as_html(self, fhir_content: str, include_styles: bool = True) -> str:
        """Render FHIR bundle as HTML"""
        try:
            metadata = self.parse_fhir_bundle(fhir_content)

            html_parts = []

            if include_styles:
                html_parts.append(
                    """
                <style>
                .fhir-document { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .fhir-header { border-bottom: 2px solid #27ae60; padding-bottom: 20px; margin-bottom: 30px; }
                .fhir-title { font-size: 24px; font-weight: bold; color: #27ae60; margin-bottom: 10px; }
                .fhir-metadata { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
                .fhir-section { margin-bottom: 30px; border-left: 4px solid #f39c12; padding-left: 15px; }
                .fhir-resource { background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 15px; }
                .fhir-resource-title { font-weight: bold; color: #2c3e50; margin-bottom: 10px; }
                </style>
                """
                )

            html_parts.append('<div class="fhir-document">')

            # Document header
            html_parts.append('<div class="fhir-header">')
            html_parts.append('<div class="fhir-title">FHIR Patient Summary</div>')

            html_parts.append('<div class="fhir-metadata">')
            html_parts.append(
                f'<div><strong>Bundle ID:</strong> {metadata.get("bundle_id", "N/A")}</div>'
            )
            html_parts.append(
                f'<div><strong>Type:</strong> {metadata.get("type", "N/A")}</div>'
            )
            html_parts.append(
                f'<div><strong>Timestamp:</strong> {metadata.get("timestamp", "N/A")}</div>'
            )
            html_parts.append(
                f'<div><strong>Resources:</strong> {metadata.get("total", 0)}</div>'
            )
            html_parts.append("</div>")
            html_parts.append("</div>")

            # Patient information
            patient = metadata.get("patient")
            if patient:
                html_parts.append('<div class="fhir-resource">')
                html_parts.append(
                    '<div class="fhir-resource-title">Patient Information</div>'
                )

                # Extract patient name
                names = patient.get("name", [])
                if names:
                    name_parts = []
                    name = names[0]
                    if "given" in name:
                        name_parts.extend(name["given"])
                    if "family" in name:
                        name_parts.append(name["family"])
                    html_parts.append(
                        f'<p><strong>Name:</strong> {" ".join(name_parts)}</p>'
                    )

                # Other patient details
                if "birthDate" in patient:
                    html_parts.append(
                        f'<p><strong>Birth Date:</strong> {patient["birthDate"]}</p>'
                    )
                if "gender" in patient:
                    html_parts.append(
                        f'<p><strong>Gender:</strong> {patient["gender"]}</p>'
                    )

                html_parts.append("</div>")

            # Composition
            composition = metadata.get("composition")
            if composition:
                html_parts.append('<div class="fhir-resource">')
                html_parts.append(
                    '<div class="fhir-resource-title">Document Composition</div>'
                )
                html_parts.append(
                    f'<p><strong>Title:</strong> {composition.get("title", "N/A")}</p>'
                )
                html_parts.append(
                    f'<p><strong>Date:</strong> {composition.get("date", "N/A")}</p>'
                )
                html_parts.append(
                    f'<p><strong>Status:</strong> {composition.get("status", "N/A")}</p>'
                )
                html_parts.append("</div>")

            # Resource summary
            html_parts.append('<div class="fhir-section">')
            html_parts.append("<h3>Bundle Resources</h3>")
            for entry in metadata.get("entries", []):
                html_parts.append(f'<div class="fhir-resource">')
                html_parts.append(
                    f'<strong>{entry["resourceType"]}</strong> (ID: {entry.get("id", "N/A")})'
                )
                html_parts.append("</div>")
            html_parts.append("</div>")

            html_parts.append("</div>")

            return "\n".join(html_parts)

        except Exception as e:
            logger.error(f"Error rendering FHIR as HTML: {e}")
            return f"<div class='error'>Error rendering document: {e}</div>"


class NCPDocumentRetriever:
    """Service to retrieve documents from member state NCPs"""

    def __init__(self):
        self.cda_processor = CDAProcessor()
        self.fhir_processor = FHIRProcessor()

    def retrieve_patient_summary(
        self, patient_id: str, member_state_oid: str, consent_method: str
    ) -> Dict[str, Any]:
        """Simulate retrieving patient summary from member state NCP"""
        # In a real implementation, this would make actual NCP calls
        # For now, we'll simulate with sample data

        logger.info(
            f"Retrieving patient summary for {patient_id} from {member_state_oid}"
        )

        # Simulate different document types based on OID
        if member_state_oid == "1.3.6.1.4.1.48336":  # Portugal
            return self._simulate_cda_response(patient_id, member_state_oid)
        elif member_state_oid == "2.16.17.710.813.1000.990.1":  # Ireland
            return self._simulate_fhir_response(patient_id, member_state_oid)
        else:
            return self._simulate_cda_response(patient_id, member_state_oid)

    def _simulate_cda_response(self, patient_id: str, oid: str) -> Dict[str, Any]:
        """Simulate CDA patient summary response"""
        sample_cda = self._generate_sample_cda(patient_id)

        return {
            "success": True,
            "document_type": "CDA_L3",
            "content": sample_cda,
            "mime_type": "application/xml",
            "document_id": f"PS_{patient_id}_{uuid.uuid4().hex[:8]}",
            "title": "Patient Summary (CDA)",
            "creation_date": timezone.now(),
            "has_embedded_pdf": True,  # Simulate embedded PDF
        }

    def _simulate_fhir_response(self, patient_id: str, oid: str) -> Dict[str, Any]:
        """Simulate FHIR bundle response"""
        sample_fhir = self._generate_sample_fhir(patient_id)

        return {
            "success": True,
            "document_type": "FHIR_BUNDLE",
            "content": sample_fhir,
            "mime_type": "application/fhir+json",
            "document_id": f"PS_{patient_id}_{uuid.uuid4().hex[:8]}",
            "title": "Patient Summary (FHIR)",
            "creation_date": timezone.now(),
            "has_embedded_pdf": False,
        }

    def _generate_sample_cda(self, patient_id: str) -> str:
        """Generate sample CDA document"""
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <id extension="{patient_id}" root="2.16.17.710.813.1000.990.1"/>
    <title>Patient Summary</title>
    <effectiveTime value="{datetime.now().strftime('%Y%m%d%H%M%S')}"/>
    <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
    
    <recordTarget>
        <patientRole>
            <id extension="{patient_id}" root="2.16.17.710.813.1000.990.1"/>
            <patient>
                <name>
                    <given>Robert</given>
                    <family>Schuman</family>
                </name>
                <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
                <birthTime value="18860629"/>
            </patient>
        </patientRole>
    </recordTarget>
    
    <author>
        <time value="{datetime.now().strftime('%Y%m%d%H%M%S')}"/>
        <assignedAuthor>
            <name>
                <given>Dr. Maria</given>
                <family>Santos</family>
            </name>
            <representedOrganization>
                <name>Hospital Central de Lisboa</name>
            </representedOrganization>
        </assignedAuthor>
    </author>
    
    <component>
        <structuredBody>
            <component>
                <section>
                    <code code="48765-2" codeSystem="2.16.840.1.113883.6.1" displayName="Allergies"/>
                    <title>Allergies and Intolerances</title>
                    <text>
                        <paragraph>No known allergies.</paragraph>
                    </text>
                </section>
            </component>
            <component>
                <section>
                    <code code="10160-0" codeSystem="2.16.840.1.113883.6.1" displayName="Medications"/>
                    <title>Current Medications</title>
                    <text>
                        <table>
                            <thead>
                                <tr><th>Medication</th><th>Dosage</th><th>Frequency</th></tr>
                            </thead>
                            <tbody>
                                <tr><td>Lisinopril</td><td>10mg</td><td>Once daily</td></tr>
                                <tr><td>Metformin</td><td>500mg</td><td>Twice daily</td></tr>
                            </tbody>
                        </table>
                    </text>
                </section>
            </component>
            <component>
                <section>
                    <code code="11450-4" codeSystem="2.16.840.1.113883.6.1" displayName="Problem List"/>
                    <title>Medical Problems</title>
                    <text>
                        <list>
                            <item>Hypertension - controlled</item>
                            <item>Type 2 Diabetes Mellitus - well controlled</item>
                        </list>
                    </text>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""

    def _generate_sample_fhir(self, patient_id: str) -> str:
        """Generate sample FHIR bundle"""
        bundle = {
            "resourceType": "Bundle",
            "id": f"bundle-{patient_id}",
            "type": "document",
            "timestamp": datetime.now().isoformat(),
            "entry": [
                {
                    "fullUrl": f"urn:uuid:patient-{patient_id}",
                    "resource": {
                        "resourceType": "Patient",
                        "id": patient_id,
                        "name": [{"given": ["Robert"], "family": "Schuman"}],
                        "gender": "male",
                        "birthDate": "1886-06-29",
                    },
                },
                {
                    "fullUrl": f"urn:uuid:composition-{patient_id}",
                    "resource": {
                        "resourceType": "Composition",
                        "id": f"composition-{patient_id}",
                        "status": "final",
                        "type": {
                            "coding": [
                                {
                                    "system": "http://loinc.org",
                                    "code": "60591-5",
                                    "display": "Patient Summary",
                                }
                            ]
                        },
                        "subject": {"reference": f"urn:uuid:patient-{patient_id}"},
                        "date": datetime.now().isoformat(),
                        "title": "Patient Summary",
                    },
                },
            ],
        }

        return json.dumps(bundle, indent=2)
