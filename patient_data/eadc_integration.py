"""
EADC (Epsos Automatic Data Collector) Integration
Handles clinical document transformation, validation, and processing
"""

import xml.etree.ElementTree as ET
import json
import logging
import os
import subprocess
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.utils import timezone
from datetime import datetime
import uuid
import base64

logger = logging.getLogger(__name__)


class EADCProcessor:
    """
    EADC (Epsos Automatic Data Collector) processor for clinical documents
    Handles transformation between national formats and epSOS CDA
    """

    def __init__(self):
        self.eadc_config_path = getattr(
            settings,
            "EADC_CONFIG_PATH",
            "C:\\Users\\Duncan\\VS_Code_Projects\\ehealth-2\\openncp-docker\\openncp-configuration\\EADC_resources",
        )
        self.xslt_path = os.path.join(self.eadc_config_path, "xslt")
        self.schema_path = os.path.join(self.eadc_config_path, "schema")
        self.demo_path = os.path.join(self.eadc_config_path, "demo")

        # Supported document transformations
        self.supported_transformations = {
            "PS": {
                "name": "Patient Summary",
                "national_to_epsos": "ps_national_to_epsos.xsl",
                "epsos_to_national": "ps_epsos_to_national.xsl",
                "template_id": "1.3.6.1.4.1.12559.11.10.1.3.1.1.3",
            },
            "EP": {
                "name": "ePrescription",
                "national_to_epsos": "ep_national_to_epsos.xsl",
                "epsos_to_national": "ep_epsos_to_national.xsl",
                "template_id": "1.3.6.1.4.1.12559.11.10.1.3.1.1.1",
            },
            "ED": {
                "name": "eDispensation",
                "national_to_epsos": "ed_national_to_epsos.xsl",
                "epsos_to_national": "ed_epsos_to_national.xsl",
                "template_id": "1.3.6.1.4.1.12559.11.10.1.3.1.1.2",
            },
        }

    def validate_cda_document(
        self, cda_content: str, document_type: str = "PS"
    ) -> Dict[str, Any]:
        """
        Validate CDA document against epSOS schemas
        """
        try:
            # Parse XML
            root = ET.fromstring(cda_content)

            validation_result = {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "document_type": document_type,
                "template_id": None,
                "epsos_compliant": False,
            }

            # Check for template ID
            template_elements = root.findall(".//templateId", {"cda": "urn:hl7-org:v3"})
            for template in template_elements:
                template_root = template.get("root", "")
                if template_root in [
                    info["template_id"]
                    for info in self.supported_transformations.values()
                ]:
                    validation_result["template_id"] = template_root
                    validation_result["epsos_compliant"] = True
                    break

            # Basic structural validation
            required_elements = [
                (".//cda:ClinicalDocument", "Missing ClinicalDocument root"),
                (".//cda:recordTarget/cda:patientRole", "Missing patient information"),
                (".//cda:author", "Missing document author"),
                (".//cda:custodian", "Missing document custodian"),
            ]

            namespaces = {"cda": "urn:hl7-org:v3"}
            for xpath, error_msg in required_elements:
                if not root.findall(xpath, namespaces):
                    validation_result["errors"].append(error_msg)
                    validation_result["is_valid"] = False

            # Document-specific validation
            if document_type == "PS":
                self._validate_patient_summary(root, validation_result, namespaces)
            elif document_type == "EP":
                self._validate_eprescription(root, validation_result, namespaces)
            elif document_type == "ED":
                self._validate_edispensation(root, validation_result, namespaces)

            return validation_result

        except ET.ParseError as e:
            return {
                "is_valid": False,
                "errors": [f"XML Parse Error: {str(e)}"],
                "warnings": [],
                "document_type": document_type,
                "template_id": None,
                "epsos_compliant": False,
            }
        except Exception as e:
            logger.error(f"Error validating CDA document: {e}")
            return {
                "is_valid": False,
                "errors": [f"Validation Error: {str(e)}"],
                "warnings": [],
                "document_type": document_type,
                "template_id": None,
                "epsos_compliant": False,
            }

    def _validate_patient_summary(self, root, result, namespaces):
        """Validate Patient Summary specific requirements"""
        ps_sections = [
            ("48765-2", "Allergies and adverse reactions"),
            ("10160-0", "History of medication use"),
            ("11450-4", "Problem list"),
        ]

        for code, name in ps_sections:
            sections = root.findall(
                f'.//cda:section[cda:code[@code="{code}"]]', namespaces
            )
            if not sections:
                result["warnings"].append(
                    f"Recommended section missing: {name} ({code})"
                )

    def _validate_eprescription(self, root, result, namespaces):
        """Validate ePrescription specific requirements"""
        # Check for prescription items
        entries = root.findall(".//cda:substanceAdministration", namespaces)
        if not entries:
            result["errors"].append("No prescription items found")
            result["is_valid"] = False

    def _validate_edispensation(self, root, result, namespaces):
        """Validate eDispensation specific requirements"""
        # Check for dispensed items
        entries = root.findall(".//cda:supply", namespaces)
        if not entries:
            result["errors"].append("No dispensed items found")
            result["is_valid"] = False

    def transform_national_to_epsos(
        self, national_document: str, document_type: str, country_code: str
    ) -> Dict[str, Any]:
        """
        Transform national CDA format to epSOS standardized format
        """
        try:
            if document_type not in self.supported_transformations:
                raise ValueError(f"Unsupported document type: {document_type}")

            transformation_info = self.supported_transformations[document_type]

            # For demo purposes, we'll simulate the transformation
            # In production, this would use XSLT processors
            logger.info(
                f"Transforming {country_code} national {document_type} to epSOS format"
            )

            # Parse the national document
            root = ET.fromstring(national_document)

            # Apply transformation logic (simplified for demo)
            epsos_document = self._apply_epsos_transformation(
                root, transformation_info, country_code
            )

            # Validate the result
            validation_result = self.validate_cda_document(
                epsos_document, document_type
            )

            return {
                "success": True,
                "epsos_document": epsos_document,
                "validation": validation_result,
                "transformation_type": f"{country_code}_to_epSOS",
                "document_type": document_type,
                "timestamp": timezone.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error transforming document: {e}")
            return {
                "success": False,
                "error": str(e),
                "transformation_type": f"{country_code}_to_epSOS",
                "document_type": document_type,
                "timestamp": timezone.now().isoformat(),
            }

    def transform_epsos_to_national(
        self, epsos_document: str, document_type: str, target_country: str
    ) -> Dict[str, Any]:
        """
        Transform epSOS standardized format to national CDA format
        """
        try:
            if document_type not in self.supported_transformations:
                raise ValueError(f"Unsupported document type: {document_type}")

            transformation_info = self.supported_transformations[document_type]

            logger.info(
                f"Transforming epSOS {document_type} to {target_country} national format"
            )

            # Parse the epSOS document
            root = ET.fromstring(epsos_document)

            # Apply reverse transformation logic
            national_document = self._apply_national_transformation(
                root, transformation_info, target_country
            )

            return {
                "success": True,
                "national_document": national_document,
                "transformation_type": f"epSOS_to_{target_country}",
                "document_type": document_type,
                "timestamp": timezone.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error transforming document: {e}")
            return {
                "success": False,
                "error": str(e),
                "transformation_type": f"epSOS_to_{target_country}",
                "document_type": document_type,
                "timestamp": timezone.now().isoformat(),
            }

    def _apply_epsos_transformation(self, root, transformation_info, country_code):
        """Apply transformation from national to epSOS format"""
        # Clone the document
        new_root = ET.fromstring(ET.tostring(root))

        # Add epSOS template ID
        template_element = ET.SubElement(new_root, "templateId")
        template_element.set("root", transformation_info["template_id"])

        # Add epSOS specific elements and attributes
        self._add_epsos_metadata(new_root, country_code)

        return ET.tostring(new_root, encoding="unicode")

    def _apply_national_transformation(self, root, transformation_info, target_country):
        """Apply transformation from epSOS to national format"""
        # Clone the document
        new_root = ET.fromstring(ET.tostring(root))

        # Remove epSOS specific elements
        epsos_templates = new_root.findall(
            f'.//templateId[@root="{transformation_info["template_id"]}"]'
        )
        for template in epsos_templates:
            template.getparent().remove(template)

        # Add national specific elements
        self._add_national_metadata(new_root, target_country)

        return ET.tostring(new_root, encoding="unicode")

    def _add_epsos_metadata(self, root, country_code):
        """Add epSOS specific metadata to document"""
        # Add realm code for epSOS
        realm_code = ET.SubElement(root, "realmCode")
        realm_code.set("code", "EU")

        # Add epSOS type ID
        type_id = ET.SubElement(root, "typeId")
        type_id.set("root", "2.16.840.1.113883.1.3")
        type_id.set("extension", "POCD_HD000040")

    def _add_national_metadata(self, root, target_country):
        """Add national specific metadata to document"""
        # Add national realm code
        realm_code = ET.SubElement(root, "realmCode")
        realm_code.set("code", target_country)

    def get_demo_documents(self) -> List[Dict[str, Any]]:
        """Get available demo documents from EADC resources"""
        demo_documents = []

        try:
            demo_file = os.path.join(self.demo_path, "TransactionDemo.xml")
            if os.path.exists(demo_file):
                with open(demo_file, "r", encoding="utf-8") as f:
                    content = f.read()

                demo_documents.append(
                    {
                        "name": "EADC Transaction Demo",
                        "type": "PS",
                        "content": content,
                        "description": "Demo patient summary from EADC resources",
                        "source": "EADC",
                    }
                )
        except Exception as e:
            logger.error(f"Error loading demo documents: {e}")

        return demo_documents

    def create_audit_trail(
        self, transformation_result: Dict[str, Any], request_id: str
    ) -> Dict[str, Any]:
        """Create audit trail entry for EADC transformation"""
        return {
            "audit_id": str(uuid.uuid4()),
            "request_id": request_id,
            "timestamp": timezone.now().isoformat(),
            "transformation_type": transformation_result.get("transformation_type"),
            "document_type": transformation_result.get("document_type"),
            "success": transformation_result.get("success"),
            "error": transformation_result.get("error"),
            "validation_errors": transformation_result.get("validation", {}).get(
                "errors", []
            ),
            "epsos_compliant": transformation_result.get("validation", {}).get(
                "epsos_compliant", False
            ),
        }


class EADCDocumentManager:
    """
    Manager for EADC document lifecycle and storage
    """

    def __init__(self):
        self.processor = EADCProcessor()

    def process_incoming_document(
        self, document_content: str, document_type: str, source_country: str
    ) -> Dict[str, Any]:
        """
        Process incoming document through EADC pipeline
        """
        processing_id = str(uuid.uuid4())

        try:
            # Step 1: Validate incoming document
            validation_result = self.processor.validate_cda_document(
                document_content, document_type
            )

            # Step 2: Transform to epSOS if not already compliant
            if not validation_result.get("epsos_compliant", False):
                transformation_result = self.processor.transform_national_to_epsos(
                    document_content, document_type, source_country
                )

                if transformation_result["success"]:
                    processed_document = transformation_result["epsos_document"]
                    transformation_applied = True
                else:
                    processed_document = document_content
                    transformation_applied = False
            else:
                processed_document = document_content
                transformation_applied = False

            # Step 3: Final validation
            final_validation = self.processor.validate_cda_document(
                processed_document, document_type
            )

            return {
                "processing_id": processing_id,
                "success": True,
                "original_document": document_content,
                "processed_document": processed_document,
                "transformation_applied": transformation_applied,
                "initial_validation": validation_result,
                "final_validation": final_validation,
                "epsos_compliant": final_validation.get("epsos_compliant", False),
                "timestamp": timezone.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error processing document through EADC: {e}")
            return {
                "processing_id": processing_id,
                "success": False,
                "error": str(e),
                "timestamp": timezone.now().isoformat(),
            }

    def prepare_outgoing_document(
        self, epsos_document: str, document_type: str, target_country: str
    ) -> Dict[str, Any]:
        """
        Prepare epSOS document for transmission to target country
        """
        try:
            # Transform to target country format if needed
            transformation_result = self.processor.transform_epsos_to_national(
                epsos_document, document_type, target_country
            )

            if transformation_result["success"]:
                return {
                    "success": True,
                    "national_document": transformation_result["national_document"],
                    "epsos_document": epsos_document,
                    "target_country": target_country,
                    "document_type": document_type,
                    "timestamp": timezone.now().isoformat(),
                }
            else:
                return transformation_result

        except Exception as e:
            logger.error(f"Error preparing outgoing document: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": timezone.now().isoformat(),
            }
