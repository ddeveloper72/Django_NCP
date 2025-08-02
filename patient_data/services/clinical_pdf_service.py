"""
Service for handling PDF extraction and rendering from clinical documents
Manages base64-encoded PDFs embedded in XML clinical documents
"""

import base64
import os
import tempfile
from typing import List, Dict, Optional, Tuple
from django.conf import settings
from django.core.files.base import ContentFile
from django.http import HttpResponse, Http404
from django.utils import timezone
import xml.etree.ElementTree as ET


class ClinicalDocumentPDFService:
    """Service for extracting and serving PDFs from clinical documents"""

    def __init__(self):
        self.pdf_storage_path = getattr(
            settings, "PDF_STORAGE_PATH", "pdfs/clinical_documents/"
        )

    def extract_pdfs_from_xml(self, xml_content: str) -> List[Dict]:
        """
        Extract all PDF attachments from XML content

        Returns:
            List of dictionaries with PDF info: {'data': bytes, 'filename': str, 'size': int}
        """
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML content: {e}")

        pdf_attachments = []

        # HL7 CDA namespace
        ns = {'hl7': 'urn:hl7-org:v3'}

        # Define common patterns for base64 content in clinical documents
        # Both with and without namespaces for compatibility
        base64_patterns = [
            # CDA observationMedia (with namespace)
            './/hl7:observationMedia/hl7:value[@mediaType="application/pdf"]',
            ".//hl7:observationMedia/hl7:value",
            # CDA nonXMLBody (with namespace) - L1 CDA ORCD
            './/hl7:nonXMLBody/hl7:text[@mediaType="application/pdf"]',
            ".//hl7:nonXMLBody/hl7:text",
            # Generic content patterns (with namespace)
            './/hl7:content[@mediaType="application/pdf"]',
            './/hl7:attachment[@mediaType="application/pdf"]',
            # Fallback patterns without namespace
            './/observationMedia/value[@mediaType="application/pdf"]',
            ".//observationMedia/value",
            './/nonXMLBody/text[@mediaType="application/pdf"]',
            ".//nonXMLBody/text",
            './/content[@mediaType="application/pdf"]',
            './/attachment[@mediaType="application/pdf"]',
            # Text content that might contain base64
            ".//text//content",
        ]

        attachment_index = 0

        for pattern in base64_patterns:
            try:
                if pattern.startswith('.//hl7:'):
                    elements = root.findall(pattern, ns)
                else:
                    elements = root.findall(pattern)
            except Exception as e:
                continue  # Skip invalid patterns

            for element in elements:
                pdf_data = self._extract_pdf_from_element(element)
                if pdf_data:
                    pdf_info = {
                        "data": pdf_data,
                        "filename": f"clinical_document_attachment_{attachment_index}.pdf",
                        "size": len(pdf_data),
                        "index": attachment_index,
                        "media_type": element.get("mediaType", "application/pdf"),
                    }
                    pdf_attachments.append(pdf_info)
                    attachment_index += 1

        return pdf_attachments

    def _extract_pdf_from_element(self, element) -> Optional[bytes]:
        """Extract PDF data from an XML element"""

        if element.text is None:
            return None

        # Clean the base64 content
        base64_content = element.text.strip()

        # Skip if content is too short to be a PDF
        if len(base64_content) < 100:
            return None

        try:
            # Attempt to decode base64
            decoded_data = base64.b64decode(base64_content)

            # Verify it's a PDF by checking header
            if decoded_data.startswith(b"%PDF"):
                return decoded_data

        except Exception:
            # If base64 decode fails, skip this element
            pass

        return None

    def save_pdf_to_storage(
        self, pdf_data: bytes, filename: str, document_id: str
    ) -> str:
        """
        Save PDF data to storage and return the file path

        Args:
            pdf_data: Binary PDF data
            filename: Desired filename
            document_id: Clinical document ID for organization

        Returns:
            String path to saved file
        """
        # Create directory structure
        storage_dir = os.path.join(
            settings.MEDIA_ROOT, self.pdf_storage_path, str(document_id)
        )
        os.makedirs(storage_dir, exist_ok=True)

        # Generate unique filename
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(storage_dir, safe_filename)

        # Write PDF data
        with open(file_path, "wb") as f:
            f.write(pdf_data)

        # Return relative path for database storage
        return os.path.join(self.pdf_storage_path, str(document_id), safe_filename)

    def get_pdf_response(
        self, pdf_data: bytes, filename: str, disposition: str = "inline"
    ) -> HttpResponse:
        """
        Create HTTP response for PDF data

        Args:
            pdf_data: Binary PDF data
            filename: Filename for download
            disposition: 'inline' for preview, 'attachment' for download
        """
        response = HttpResponse(pdf_data, content_type="application/pdf")
        response["Content-Disposition"] = f'{disposition}; filename="{filename}"'
        response["Content-Length"] = len(pdf_data)

        return response

    def create_pdf_preview_url(self, document_id: str, attachment_index: int) -> str:
        """Generate URL for PDF preview"""
        return f"/patient-data/documents/{document_id}/pdf/{attachment_index}/preview/"

    def create_pdf_download_url(self, document_id: str, attachment_index: int) -> str:
        """Generate URL for PDF download"""
        return f"/patient-data/documents/{document_id}/pdf/{attachment_index}/download/"


class TranslatedDocumentRenderer:
    """Service for rendering clinical documents with terminology translation"""

    def __init__(self):
        self.pdf_service = ClinicalDocumentPDFService()

    def render_translated_document(
        self, clinical_document, target_language: str = "en"
    ) -> Dict:
        """
        Render a clinical document with terminology translation

        Args:
            clinical_document: ClinicalDocument instance
            target_language: Target language code for translation

        Returns:
            Dictionary with rendered content and PDF attachments
        """
        from translation_services.terminology_translator import TerminologyTranslator

        # Initialize translator
        translator = TerminologyTranslator()

        # Extract original XML content
        xml_content = clinical_document.xml_content

        # Apply terminology translation
        translated_content = translator.translate_clinical_document(
            xml_content, target_language=target_language
        )

        # Extract PDF attachments
        pdf_attachments = self.pdf_service.extract_pdfs_from_xml(xml_content)

        # Process attachments for web display
        processed_attachments = []
        for i, attachment in enumerate(pdf_attachments):
            processed_attachment = {
                "index": i,
                "filename": attachment["filename"],
                "size": attachment["size"],
                "size_mb": round(attachment["size"] / (1024 * 1024), 2),
                "preview_url": self.pdf_service.create_pdf_preview_url(
                    clinical_document.id, i
                ),
                "download_url": self.pdf_service.create_pdf_download_url(
                    clinical_document.id, i
                ),
            }
            processed_attachments.append(processed_attachment)

        return {
            "original_content": xml_content,
            "translated_content": translated_content,
            "pdf_attachments": processed_attachments,
            "translation_stats": translated_content.get("translation_stats", {}),
            "target_language": target_language,
            "source_country": clinical_document.source_country,
            "document_type": clinical_document.document_type,
            "received_at": clinical_document.received_at,
        }

    def get_available_translations(self, clinical_document) -> List[str]:
        """Get list of available translation languages for a document"""

        # For now, return common EU languages
        # In the future, this could be determined by available MVC translations
        return [
            "en",  # English
            "de",  # German
            "fr",  # French
            "it",  # Italian
            "es",  # Spanish
            "nl",  # Dutch
            "pt",  # Portuguese
        ]


class TestDataManager:
    """Manager for EU member state test data"""

    def __init__(self):
        self.test_data_path = os.getenv("EU_TEST_DATA_PATH")
        self.enabled = os.getenv("ENABLE_TEST_DATA_IMPORT", "False").lower() == "true"

    def is_test_data_available(self) -> bool:
        """Check if test data directory is available"""
        if not self.enabled or not self.test_data_path:
            return False
        return os.path.exists(self.test_data_path)

    def get_available_countries(self) -> List[str]:
        """Get list of countries with test data available"""
        if not self.is_test_data_available():
            return []

        # Scan for country patterns in filenames
        countries = set()
        test_path = os.path.join(self.test_data_path)

        if os.path.exists(test_path):
            for filename in os.listdir(test_path):
                # Look for country codes in filenames
                filename_upper = filename.upper()
                eu_countries = [
                    "DE",
                    "FR",
                    "IT",
                    "ES",
                    "NL",
                    "BE",
                    "AT",
                    "PL",
                    "CZ",
                    "HU",
                    "PT",
                    "SE",
                    "DK",
                    "FI",
                    "GR",
                ]
                for country in eu_countries:
                    if country in filename_upper:
                        countries.add(country)

        return sorted(list(countries))

    def get_test_data_summary(self) -> Dict:
        """Get summary of available test data"""
        if not self.is_test_data_available():
            return {
                "available": False,
                "message": "Test data not configured or not available",
            }

        countries = self.get_available_countries()

        return {
            "available": True,
            "path": self.test_data_path,
            "countries": countries,
            "total_countries": len(countries),
            "message": f"Test data available for {len(countries)} countries",
        }
