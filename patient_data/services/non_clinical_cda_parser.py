"""
Non-Clinical CDA Parser
Extracts administrative data, patient demographics, and document metadata from HL7 CDA documents.
Complements the Enhanced CDA XML Parser which focuses on clinical coded sections.
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any, Union
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class PatientDemographics:
    """Complete patient demographic information"""

    patient_id: Optional[str] = None
    patient_id_root: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    birth_date: Optional[str] = None
    gender_code: Optional[str] = None
    gender_display: Optional[str] = None

    # Address information
    street_address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

    # Contact information
    telecom: List[Dict[str, str]] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        """Get full formatted name"""
        parts = [self.given_name, self.family_name]
        return " ".join(part for part in parts if part)

    @property
    def formatted_address(self) -> str:
        """Get formatted address"""
        parts = [self.street_address, self.city, self.postal_code, self.country]
        return ", ".join(part for part in parts if part)


@dataclass
class HealthcareProvider:
    """Healthcare provider/author information"""

    provider_id: Optional[str] = None
    provider_id_root: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    role: Optional[str] = None
    organization_name: Optional[str] = None
    organization_id: Optional[str] = None
    timestamp: Optional[str] = None

    @property
    def full_name(self) -> str:
        """Get full formatted name"""
        parts = [self.given_name, self.family_name]
        return " ".join(part for part in parts if part)


@dataclass
class DocumentMetadata:
    """Complete document administrative metadata"""

    document_id: Optional[str] = None
    document_id_root: Optional[str] = None
    title: Optional[str] = None
    creation_date: Optional[str] = None
    effective_date: Optional[str] = None

    # Document classification
    document_type_code: Optional[str] = None
    document_type_display: Optional[str] = None
    document_type_system: Optional[str] = None

    # Document status
    confidentiality_code: Optional[str] = None
    confidentiality_display: Optional[str] = None
    language_code: Optional[str] = None

    # Document relationships
    related_documents: List[Dict[str, str]] = field(default_factory=list)

    # Version information
    version_number: Optional[str] = None
    set_id: Optional[str] = None


@dataclass
class CustodianInformation:
    """Document custodian/maintaining organization"""

    organization_id: Optional[str] = None
    organization_id_root: Optional[str] = None
    organization_name: Optional[str] = None
    address: Optional[str] = None
    telecom: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class LegalAuthenticator:
    """Legal authenticator/signer information"""

    authenticator_id: Optional[str] = None
    authenticator_id_root: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    authentication_time: Optional[str] = None
    signature_code: Optional[str] = None
    organization_name: Optional[str] = None

    @property
    def full_name(self) -> str:
        """Get full formatted name"""
        parts = [self.given_name, self.family_name]
        return " ".join(part for part in parts if part)


class NonClinicalCDAParser:
    """
    Parser for non-clinical CDA sections and administrative data
    Extracts patient demographics, document metadata, healthcare providers, etc.
    """

    def __init__(self):
        self.namespace = {"hl7": "urn:hl7-org:v3"}

    def parse_cda_content(self, xml_content: str) -> Dict[str, Any]:
        """
        Parse CDA content and extract all non-clinical administrative data

        Args:
            xml_content: Raw CDA XML content

        Returns:
            Dictionary with complete non-clinical data
        """
        try:
            root = ET.fromstring(xml_content)

            result = {
                "success": True,
                "document_metadata": self._extract_document_metadata(root),
                "patient_demographics": self._extract_patient_demographics(root),
                "healthcare_providers": self._extract_healthcare_providers(root),
                "custodian_information": self._extract_custodian_information(root),
                "legal_authenticator": self._extract_legal_authenticator(root),
                "document_structure": self._extract_document_structure(root),
                "parsing_stats": {
                    "total_sections": len(root.findall(".//{urn:hl7-org:v3}section")),
                    "has_patient_data": self._has_patient_data(root),
                    "has_authors": len(root.findall(".//{urn:hl7-org:v3}author")) > 0,
                    "has_custodian": root.find(".//{urn:hl7-org:v3}custodian")
                    is not None,
                    "has_legal_auth": root.find(".//{urn:hl7-org:v3}legalAuthenticator")
                    is not None,
                },
            }

            logger.info(f"Non-clinical CDA parsing complete: {result['parsing_stats']}")
            return result

        except Exception as e:
            logger.error(f"Non-clinical CDA parsing failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "document_metadata": DocumentMetadata(),
                "patient_demographics": PatientDemographics(),
                "healthcare_providers": [],
                "custodian_information": CustodianInformation(),
                "legal_authenticator": LegalAuthenticator(),
                "document_structure": {},
            }

    def _extract_document_metadata(self, root: ET.Element) -> DocumentMetadata:
        """Extract complete document metadata"""
        metadata = DocumentMetadata()

        # Document ID
        doc_id = root.find(".//{urn:hl7-org:v3}id")
        if doc_id is not None:
            metadata.document_id = doc_id.get("extension")
            metadata.document_id_root = doc_id.get("root")

        # Document title
        title = root.find(".//{urn:hl7-org:v3}title")
        if title is not None and title.text:
            metadata.title = title.text.strip()

        # Creation/effective date
        effective_time = root.find(".//{urn:hl7-org:v3}effectiveTime")
        if effective_time is not None:
            metadata.creation_date = effective_time.get("value")
            metadata.effective_date = effective_time.get("value")

        # Document type
        code = root.find(".//{urn:hl7-org:v3}code")
        if code is not None:
            metadata.document_type_code = code.get("code")
            metadata.document_type_display = code.get("displayName")
            metadata.document_type_system = code.get("codeSystem")

        # Confidentiality
        confidentiality = root.find(".//{urn:hl7-org:v3}confidentialityCode")
        if confidentiality is not None:
            metadata.confidentiality_code = confidentiality.get("code")
            metadata.confidentiality_display = confidentiality.get("displayName")

        # Language
        language = root.find(".//{urn:hl7-org:v3}languageCode")
        if language is not None:
            metadata.language_code = language.get("code")

        # Version information
        version_number = root.find(".//{urn:hl7-org:v3}versionNumber")
        if version_number is not None:
            metadata.version_number = version_number.get("value")

        set_id = root.find(".//{urn:hl7-org:v3}setId")
        if set_id is not None:
            metadata.set_id = set_id.get("extension")

        # Related documents
        related_docs = root.findall(".//{urn:hl7-org:v3}relatedDocument")
        for rel_doc in related_docs:
            rel_info = {"type": rel_doc.get("typeCode")}

            parent_doc = rel_doc.find("{urn:hl7-org:v3}parentDocument")
            if parent_doc is not None:
                parent_id = parent_doc.find("{urn:hl7-org:v3}id")
                if parent_id is not None:
                    rel_info["parent_id"] = parent_id.get("extension")
                    rel_info["parent_root"] = parent_id.get("root")

            metadata.related_documents.append(rel_info)

        return metadata

    def _extract_patient_demographics(self, root: ET.Element) -> PatientDemographics:
        """Extract complete patient demographic information"""
        demographics = PatientDemographics()

        # Find patient role
        patient_role = root.find(
            ".//{urn:hl7-org:v3}recordTarget/{urn:hl7-org:v3}patientRole"
        )
        if patient_role is None:
            return demographics

        # Patient ID
        patient_id = patient_role.find("{urn:hl7-org:v3}id")
        if patient_id is not None:
            demographics.patient_id = patient_id.get("extension")
            demographics.patient_id_root = patient_id.get("root")

        # Patient personal information
        patient = patient_role.find("{urn:hl7-org:v3}patient")
        if patient is not None:
            # Name
            name = patient.find("{urn:hl7-org:v3}name")
            if name is not None:
                given = name.find("{urn:hl7-org:v3}given")
                family = name.find("{urn:hl7-org:v3}family")
                if given is not None:
                    demographics.given_name = given.text
                if family is not None:
                    demographics.family_name = family.text

            # Birth date
            birth_time = patient.find("{urn:hl7-org:v3}birthTime")
            if birth_time is not None:
                demographics.birth_date = birth_time.get("value")

            # Gender
            gender = patient.find("{urn:hl7-org:v3}administrativeGenderCode")
            if gender is not None:
                demographics.gender_code = gender.get("code")
                demographics.gender_display = gender.get("displayName")

        # Address
        addr = patient_role.find("{urn:hl7-org:v3}addr")
        if addr is not None:
            street = addr.find("{urn:hl7-org:v3}streetAddressLine")
            city = addr.find("{urn:hl7-org:v3}city")
            postal = addr.find("{urn:hl7-org:v3}postalCode")
            country = addr.find("{urn:hl7-org:v3}country")

            if street is not None:
                demographics.street_address = street.text
            if city is not None:
                demographics.city = city.text
            if postal is not None:
                demographics.postal_code = postal.text
            if country is not None:
                demographics.country = country.text

        # Telecom
        telecoms = patient_role.findall("{urn:hl7-org:v3}telecom")
        for telecom in telecoms:
            demographics.telecom.append(
                {"use": telecom.get("use", ""), "value": telecom.get("value", "")}
            )

        return demographics

    def _extract_healthcare_providers(
        self, root: ET.Element
    ) -> List[HealthcareProvider]:
        """Extract all healthcare provider/author information"""
        providers = []

        authors = root.findall(".//{urn:hl7-org:v3}author")
        for author in authors:
            provider = HealthcareProvider()

            # Author timestamp
            time_elem = author.find("{urn:hl7-org:v3}time")
            if time_elem is not None:
                provider.timestamp = time_elem.get("value")

            # Assigned author
            assigned_author = author.find("{urn:hl7-org:v3}assignedAuthor")
            if assigned_author is not None:
                # Author ID
                author_id = assigned_author.find("{urn:hl7-org:v3}id")
                if author_id is not None:
                    provider.provider_id = author_id.get("extension")
                    provider.provider_id_root = author_id.get("root")

                # Author person
                assigned_person = assigned_author.find("{urn:hl7-org:v3}assignedPerson")
                if assigned_person is not None:
                    name = assigned_person.find("{urn:hl7-org:v3}name")
                    if name is not None:
                        given = name.find("{urn:hl7-org:v3}given")
                        family = name.find("{urn:hl7-org:v3}family")
                        if given is not None:
                            provider.given_name = given.text
                        if family is not None:
                            provider.family_name = family.text

                # Organization
                org = assigned_author.find("{urn:hl7-org:v3}representedOrganization")
                if org is not None:
                    org_name = org.find("{urn:hl7-org:v3}name")
                    if org_name is not None:
                        provider.organization_name = org_name.text

                    org_id = org.find("{urn:hl7-org:v3}id")
                    if org_id is not None:
                        provider.organization_id = org_id.get("extension")

            providers.append(provider)

        return providers

    def _extract_custodian_information(self, root: ET.Element) -> CustodianInformation:
        """Extract document custodian information"""
        custodian_info = CustodianInformation()

        custodian = root.find(".//{urn:hl7-org:v3}custodian")
        if custodian is not None:
            assigned_custodian = custodian.find("{urn:hl7-org:v3}assignedCustodian")
            if assigned_custodian is not None:
                org = assigned_custodian.find(
                    "{urn:hl7-org:v3}representedCustodianOrganization"
                )
                if org is not None:
                    # Organization ID
                    org_id = org.find("{urn:hl7-org:v3}id")
                    if org_id is not None:
                        custodian_info.organization_id = org_id.get("extension")
                        custodian_info.organization_id_root = org_id.get("root")

                    # Organization name
                    org_name = org.find("{urn:hl7-org:v3}name")
                    if org_name is not None:
                        custodian_info.organization_name = org_name.text

                    # Address
                    addr = org.find("{urn:hl7-org:v3}addr")
                    if addr is not None:
                        address_parts = []
                        for elem in addr:
                            if elem.text:
                                address_parts.append(elem.text)
                        custodian_info.address = ", ".join(address_parts)

                    # Telecom
                    telecoms = org.findall("{urn:hl7-org:v3}telecom")
                    for telecom in telecoms:
                        custodian_info.telecom.append(
                            {
                                "use": telecom.get("use", ""),
                                "value": telecom.get("value", ""),
                            }
                        )

        return custodian_info

    def _extract_legal_authenticator(self, root: ET.Element) -> LegalAuthenticator:
        """Extract legal authenticator information"""
        auth_info = LegalAuthenticator()

        legal_auth = root.find(".//{urn:hl7-org:v3}legalAuthenticator")
        if legal_auth is not None:
            # Authentication time
            time_elem = legal_auth.find("{urn:hl7-org:v3}time")
            if time_elem is not None:
                auth_info.authentication_time = time_elem.get("value")

            # Signature code
            sig_code = legal_auth.find("{urn:hl7-org:v3}signatureCode")
            if sig_code is not None:
                auth_info.signature_code = sig_code.get("code")

            # Assigned entity
            assigned_entity = legal_auth.find("{urn:hl7-org:v3}assignedEntity")
            if assigned_entity is not None:
                # Entity ID
                entity_id = assigned_entity.find("{urn:hl7-org:v3}id")
                if entity_id is not None:
                    auth_info.authenticator_id = entity_id.get("extension")
                    auth_info.authenticator_id_root = entity_id.get("root")

                # Person name
                assigned_person = assigned_entity.find("{urn:hl7-org:v3}assignedPerson")
                if assigned_person is not None:
                    name = assigned_person.find("{urn:hl7-org:v3}name")
                    if name is not None:
                        given = name.find("{urn:hl7-org:v3}given")
                        family = name.find("{urn:hl7-org:v3}family")
                        if given is not None:
                            auth_info.given_name = given.text
                        if family is not None:
                            auth_info.family_name = family.text

                # Organization
                org = assigned_entity.find("{urn:hl7-org:v3}representedOrganization")
                if org is not None:
                    org_name = org.find("{urn:hl7-org:v3}name")
                    if org_name is not None:
                        auth_info.organization_name = org_name.text

        return auth_info

    def _extract_document_structure(self, root: ET.Element) -> Dict[str, Any]:
        """Extract document structure and section organization"""
        structure = {
            "sections": [],
            "section_hierarchy": {},
            "total_sections": 0,
            "section_types": {},
        }

        sections = root.findall(".//{urn:hl7-org:v3}section")
        structure["total_sections"] = len(sections)

        for i, section in enumerate(sections):
            section_info = {
                "index": i,
                "section_id": section.get("ID", f"section_{i}"),
                "has_entries": len(section.findall("{urn:hl7-org:v3}entry")) > 0,
            }

            # Section code
            code_elem = section.find("{urn:hl7-org:v3}code")
            if code_elem is not None:
                section_info["code"] = code_elem.get("code")
                section_info["code_system"] = code_elem.get("codeSystem")
                section_info["display_name"] = code_elem.get("displayName")

            # Section title
            title_elem = section.find("{urn:hl7-org:v3}title")
            if title_elem is not None:
                section_info["title"] = title_elem.text

            # Track section types
            section_type = section_info.get("code", "UNKNOWN")
            if section_type in structure["section_types"]:
                structure["section_types"][section_type] += 1
            else:
                structure["section_types"][section_type] = 1

            structure["sections"].append(section_info)

        return structure

    def _has_patient_data(self, root: ET.Element) -> bool:
        """Check if document has patient data"""
        return (
            root.find(".//{urn:hl7-org:v3}recordTarget/{urn:hl7-org:v3}patientRole")
            is not None
        )
