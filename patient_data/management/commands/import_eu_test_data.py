"""
Management command to import real EU member state test data
Loads XML files from external directory (not in git) for translation testing
"""

import os
import base64
import xml.etree.ElementTree as ET
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils import timezone
from patient_data.models import PatientData, MemberState, PatientIdentifier
from patient_data.clinical_models import ClinicalDocument, ClinicalDocumentRequest


class Command(BaseCommand):
    help = "Import real EU member state test data for translation testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--data-path",
            type=str,
            help="Path to test data directory (overrides environment variable)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview what would be imported without actually importing",
        )
        parser.add_argument(
            "--country",
            type=str,
            help="Import only files from specific country (e.g., DE, FR, IT)",
        )
        parser.add_argument(
            "--patient-id",
            type=str,
            help="Import only specific patient ID",
        )

    def handle(self, *args, **options):
        # Get test data path
        data_path = options.get("data_path") or os.getenv("EU_TEST_DATA_PATH")

        if not data_path:
            self.stdout.write(
                self.style.ERROR(
                    "Test data path not specified. Set EU_TEST_DATA_PATH environment variable "
                    "or use --data-path argument."
                )
            )
            return

        data_path = Path(data_path)
        if not data_path.exists():
            self.stdout.write(
                self.style.ERROR(f"Test data directory not found: {data_path}")
            )
            return

        self.stdout.write(f"Scanning test data directory: {data_path}")

        # Scan for XML files
        xml_files = list(data_path.rglob("*.xml"))

        if not xml_files:
            self.stdout.write(
                self.style.WARNING("No XML files found in test data directory")
            )
            return

        self.stdout.write(f"Found {len(xml_files)} XML files")

        # Filter by country if specified
        if options.get("country"):
            country_filter = options["country"].upper()
            xml_files = [f for f in xml_files if country_filter in str(f).upper()]
            self.stdout.write(
                f"Filtered to {len(xml_files)} files for country: {country_filter}"
            )

        # Process each XML file
        imported_count = 0
        error_count = 0

        for xml_file in xml_files:
            try:
                result = self.process_xml_file(xml_file, options)
                if result:
                    imported_count += 1
                    if not options.get("dry_run"):
                        self.stdout.write(
                            self.style.SUCCESS(f"✓ Imported: {xml_file.name}")
                        )
                    else:
                        self.stdout.write(f"• Would import: {xml_file.name}")

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"✗ Error processing {xml_file.name}: {str(e)}")
                )

        # Summary
        if options.get("dry_run"):
            self.stdout.write(
                self.style.SUCCESS(
                    f"Dry run completed: {imported_count} files would be imported, {error_count} errors"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Import completed: {imported_count} files imported, {error_count} errors"
                )
            )

    def process_xml_file(self, xml_file_path, options):
        """Process a single XML file and extract patient data"""

        # Parse XML with better error handling
        try:
            # Read file content first to check for issues
            with open(xml_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse the XML directly first
            root = ET.fromstring(content)

        except ET.ParseError as e:
            # If parsing fails, it might be due to unescaped characters in attributes
            # This is common in email addresses and URLs
            if "expected ';'" in str(e) or "not well-formed" in str(e):
                try:
                    # Clean content for common issues with email addresses
                    import re

                    # Escape ampersands that are not already part of entities
                    content = re.sub(r"&(?![a-zA-Z0-9#]+;)", "&amp;", content)
                    root = ET.fromstring(content)
                except ET.ParseError as e2:
                    raise Exception(f"XML parsing failed even after cleaning: {e2}")
            else:
                raise Exception(f"Invalid XML: {e}")
        except Exception as e:
            raise Exception(f"Error reading XML file: {e}")

        # Extract patient information
        patient_info = self.extract_patient_info(root, xml_file_path)

        if not patient_info:
            raise Exception("Could not extract patient information from XML")

        # Filter by patient ID if specified
        if options.get("patient_id"):
            if patient_info["patient_id"] != options["patient_id"]:
                return False

        if options.get("dry_run"):
            self.stdout.write(
                f'  Patient: {patient_info["patient_id"]} from {patient_info["country"]}'
            )
            return True

        # Get or create member state
        member_state, created = MemberState.objects.get_or_create(
            country_code=patient_info["country"],
            defaults={
                "country_name": patient_info["country"],
                "language_code": f'{patient_info["country"].lower()}-{patient_info["country"]}',
                "ncp_endpoint": f'http://example.{patient_info["country"].lower()}.eu/ncp',
                "home_community_id": f'2.16.{patient_info["country"]}.1.1.1',
                "is_active": True,
            },
        )

        # Get or create patient identifier
        patient_identifier, created = PatientIdentifier.objects.get_or_create(
            patient_id=patient_info["patient_id"],
            home_member_state=member_state,
            id_root="2.16.840.1.113883.2.9.4.3.2",  # Default OID for test data
            defaults={"id_extension": patient_info["patient_id"]},
        )

        # Create patient data record (each access creates a new record)
        patient_data = PatientData.objects.create(
            patient_identifier=patient_identifier,
            given_name=patient_info.get("first_name", "Test"),
            family_name=patient_info.get("last_name", "Patient"),
            birth_date=patient_info.get("date_of_birth"),
            gender=patient_info.get("gender", "U"),
            country=patient_info["country"],
            accessed_by_id=1,  # Use system user for imports
        )

        # Create clinical document request
        doc_request = ClinicalDocumentRequest.objects.create(
            patient_data=patient_data,
            document_type="PS",  # Patient Summary
            consent_method="EXPLICIT",
            purpose_of_use="TREATMENT",
            requesting_organization="EU Test Data Import",
            status="COMPLETED",
        )

        # Read XML content
        with open(xml_file_path, "r", encoding="utf-8") as f:
            xml_content = f.read()

        # Determine document type from filename
        document_type = "CDA_L1"  # Default
        if "L3" in xml_file_path.name.upper():
            document_type = "CDA_L3"
        elif "FHIR" in xml_file_path.name.upper():
            document_type = "FHIR_BUNDLE"

        # Extract embedded PDFs if present
        pdf_attachments = self.extract_pdf_attachments(root)

        # Create clinical document
        clinical_doc = ClinicalDocument.objects.create(
            request=doc_request,
            document_type=document_type,
            service_type="PS",  # Patient Summary
            document_id=patient_info["patient_id"] + "_" + xml_file_path.stem,
            document_title=f"Test Document for {patient_info['patient_id']}",
            creation_date=timezone.now(),
            author_institution=f"Test Institution {patient_info['country']}",
            raw_document=xml_content,
            document_size=len(xml_content.encode("utf-8")),
            mime_type="application/xml",
        )

        # Save PDF attachments if found
        if pdf_attachments:
            # For now, save the first PDF attachment to pdf_content field
            clinical_doc.pdf_content = base64.b64encode(pdf_attachments[0]).decode(
                "utf-8"
            )
            clinical_doc.save()

        return True

    def extract_patient_info(self, root, xml_file_path):
        """Extract patient information from XML"""

        # Try to determine country from file path or name
        file_path_str = str(xml_file_path).upper()
        country = "UNKNOWN"

        # Common EU country codes
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
        for country_code in eu_countries:
            if country_code in file_path_str:
                country = country_code
                break

        # Try to extract patient ID from XML or filename
        patient_id = self.extract_patient_id(root, xml_file_path)

        if not patient_id:
            # Use filename as fallback
            patient_id = xml_file_path.stem

        # Try to extract basic patient demographics
        patient_info = {
            "patient_id": patient_id,
            "country": country,
            "first_name": self.extract_text_from_xml(root, ".//given") or "Test",
            "last_name": self.extract_text_from_xml(root, ".//family") or "Patient",
            "date_of_birth": self.extract_date_from_xml(root),
            "gender": self.extract_gender_from_xml(root),
        }

        return patient_info

    def extract_patient_id(self, root, xml_file_path):
        """Extract patient ID from XML content"""
        namespaces = {
            "hl7": "urn:hl7-org:v3",
        }

        # Common XPath patterns for patient ID in CDA documents
        id_element_patterns = [
            ".//hl7:recordTarget/hl7:patientRole/hl7:id",
            ".//hl7:patientRole/hl7:id",
            ".//hl7:patient/hl7:id",
            ".//recordTarget//id",
            ".//patientRole/id",
            ".//patient/id",
        ]

        for pattern in id_element_patterns:
            try:
                if "hl7:" in pattern:
                    elements = root.findall(pattern, namespaces)
                else:
                    elements = root.findall(pattern)

                if elements:
                    for elem in elements:
                        # Try extension attribute first
                        patient_id = elem.get("extension")
                        if patient_id and patient_id.strip():
                            return patient_id.strip()
                        # Fallback to root attribute
                        patient_id = elem.get("root")
                        if patient_id and patient_id.strip():
                            return patient_id.strip()
            except Exception as e:
                continue

        # Fallback: use filename
        return xml_file_path.stem

    def extract_text_from_xml(self, root, xpath):
        """Extract text content from XML using xpath with namespace handling"""
        # Define namespaces for HL7 CDA documents
        namespaces = {
            "hl7": "urn:hl7-org:v3",
            "pharm": "urn:hl7-org:pharm",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        }

        # Try with namespace first
        ns_xpath = xpath.replace("//", ".//hl7:").replace("/", "/hl7:")
        try:
            elements = root.findall(ns_xpath, namespaces)
            if elements and elements[0].text:
                return elements[0].text.strip()
        except:
            pass

        # Fallback to original xpath
        try:
            elements = root.findall(xpath)
            if elements and elements[0].text:
                return elements[0].text.strip()
        except:
            pass

        return None

    def extract_date_from_xml(self, root):
        """Extract birth date from XML with namespace handling"""
        namespaces = {
            "hl7": "urn:hl7-org:v3",
        }

        date_element_patterns = [
            ".//hl7:patient/hl7:birthTime",
            ".//hl7:birthTime",
            ".//patient/birthTime",
            ".//birthTime",
        ]

        for pattern in date_element_patterns:
            try:
                if "hl7:" in pattern:
                    elements = root.findall(pattern, namespaces)
                else:
                    elements = root.findall(pattern)

                if elements:
                    date_str = elements[0].get("value", "").strip()
                    # Parse YYYYMMDD format common in HL7
                    if len(date_str) >= 8 and date_str[:8].isdigit():
                        try:
                            return datetime.strptime(date_str[:8], "%Y%m%d").date()
                        except ValueError:
                            continue
            except:
                continue

        return None

    def extract_gender_from_xml(self, root):
        """Extract gender from XML with namespace handling"""
        namespaces = {
            "hl7": "urn:hl7-org:v3",
        }

        gender_element_patterns = [
            ".//hl7:patient/hl7:administrativeGenderCode",
            ".//hl7:administrativeGenderCode",
            ".//patient/administrativeGenderCode",
            ".//administrativeGenderCode",
        ]

        for pattern in gender_element_patterns:
            try:
                if "hl7:" in pattern:
                    elements = root.findall(pattern, namespaces)
                else:
                    elements = root.findall(pattern)

                if elements:
                    gender_code = elements[0].get("code", "").strip().upper()
                    # Map HL7 gender codes to our system
                    gender_mapping = {
                        "M": "M",
                        "F": "F",
                        "U": "U",
                        "MALE": "M",
                        "FEMALE": "F",
                    }
                    return gender_mapping.get(gender_code, "U")
            except:
                continue

        return "U"  # Unknown

    def extract_pdf_attachments(self, root):
        """Extract base64-encoded PDF attachments from XML with namespace handling"""
        namespaces = {
            "hl7": "urn:hl7-org:v3",
        }

        pdf_attachments = []

        # Look for base64 encoded content in CDA documents
        base64_patterns = [
            ".//hl7:observationMedia/hl7:value",
            ".//hl7:text//hl7:content",
            ".//hl7:nonXMLBody/hl7:text",
            ".//observationMedia/value",
            ".//text//content",
            ".//nonXMLBody/text",
        ]

        for pattern in base64_patterns:
            try:
                if "hl7:" in pattern:
                    elements = root.findall(pattern, namespaces)
                else:
                    elements = root.findall(pattern)

                for element in elements:
                    if (
                        element.text and len(element.text.strip()) > 100
                    ):  # Likely base64 content
                        try:
                            # Try to decode as base64
                            decoded_data = base64.b64decode(element.text.strip())

                            # Check if it's a PDF
                            if decoded_data.startswith(b"%PDF"):
                                pdf_attachments.append(decoded_data)
                        except Exception:
                            continue
            except:
                continue

        return pdf_attachments
