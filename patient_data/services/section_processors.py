"""
Section Processors for Enhanced Patient CDA Display
Consistent Python-based processing for all template sections
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from patient_data.utils.date_formatter import PatientDateFormatter

logger = logging.getLogger(__name__)


class PatientSectionProcessor:
    """Process patient-related sections with consistent structure"""

    def __init__(self):
        """Initialize the processor with date formatter"""
        self.date_formatter = PatientDateFormatter()

    def prepare_patient_header_data(
        self,
        patient_identity: Dict[str, Any],
        source_country: str = None,
        cda_type: str = None,
        translation_quality: str = None,
        confidence: int = 0,
        file_name: str = None,
        has_l1_cda: bool = False,
        has_l3_cda: bool = True,
    ) -> Dict[str, Any]:
        """
        Process patient header data for consistent display

        Args:
            patient_identity: Patient identity data from enhanced processing
            source_country: Country code
            cda_type: L1 or L3
            translation_quality: Quality indicator
            confidence: Processing confidence score (0-100)
            file_name: Source CDA file name
            has_l1_cda: Whether L1 CDA is available
            has_l3_cda: Whether L3 CDA is available

        Returns:
            Structured patient header data for template
        """
        try:
            # Process patient name with fallback logic
            display_name = self._get_patient_display_name(patient_identity)

            # Process birth date with formatting
            birth_date_info = self._format_patient_birth_date(patient_identity)

            # Process document metadata
            document_metadata = self._extract_document_metadata(patient_identity)

            # Build structured header data
            header_data = {
                "section_type": "patient_header",
                "section_code": "patient_demographics",
                "display_name": display_name,
                "patient_demographics": {
                    "birth_date": birth_date_info["formatted"],
                    "birth_date_raw": birth_date_info["raw"],
                    "gender": patient_identity.get("gender", "Unknown"),
                    "patient_id": patient_identity.get("patient_id", "Unknown"),
                    "secondary_patient_id": patient_identity.get(
                        "secondary_patient_id"
                    ),
                },
                "document_info": {
                    "source_country": source_country or "Unknown",
                    "cda_type": cda_type or "L3",
                    "translation_quality": translation_quality or "Standard",
                    "confidence": confidence,
                    "file_name": file_name or "unknown.xml",
                    "document_title": document_metadata.get("title", "Patient Summary"),
                    "language_code": document_metadata.get("language_code", "en"),
                },
                "cda_navigation": {
                    "has_l1_cda": has_l1_cda,
                    "has_l3_cda": has_l3_cda,
                    "current_type": cda_type or "L3",
                    "patient_url_id": patient_identity.get(
                        "url_patient_id", patient_identity.get("patient_id")
                    ),
                },
                "styling": {
                    "header_class": "bg-primary",
                    "icon": "fas fa-user-injured",
                    "card_class": "patient-header-section",
                },
            }

            logger.info(f"✅ Patient header data processed for {display_name}")
            return header_data

        except Exception as e:
            logger.error(f"❌ Error processing patient header data: {e}")
            return self._get_fallback_header_data(patient_identity)

    def prepare_enhanced_extended_patient_data(
        self,
        xml_content: str = "",
    ) -> Dict[str, Any]:
        """
        Prepare enhanced extended patient data using the comprehensive EU PS XSL-based extractor

        This method uses the EnhancedCDAAdministrativeExtractor which follows the
        EU Patient Summary XSL templates for comprehensive data extraction.

        Args:
            xml_content: Raw CDA XML content

        Returns:
            Dictionary with enhanced extended patient data for template, including:
            - has_meaningful_data: Boolean indicating if tabs should be generated
            - navigation_tabs: List of tab configurations with counts
            - All data sections: document_info, legal_authenticator, authors, etc.
        """
        try:
            # Use the enhanced extractor based on EU PS XSL templates
            if xml_content:
                try:
                    from enhanced_cda_administrative_extractor import (
                        EnhancedCDAAdministrativeExtractor,
                    )

                    logger.info(
                        "🔄 Using EnhancedCDAAdministrativeExtractor (EU PS XSL-based)"
                    )

                    extractor = EnhancedCDAAdministrativeExtractor()
                    enhanced_data = extractor.extract_administrative_data(xml_content)

                    if enhanced_data and enhanced_data.has_meaningful_data:
                        logger.info(
                            f"✅ Enhanced extraction successful: {enhanced_data.extraction_summary}"
                        )

                        # Process the enhanced data into template-ready format
                        return self._process_enhanced_admin_data(enhanced_data)
                    else:
                        logger.warning("⚠️ Enhanced extraction found no meaningful data")

                except ImportError as e:
                    logger.warning(f"⚠️ Enhanced extractor not available: {e}")
                except Exception as e:
                    logger.error(f"❌ Enhanced extraction failed: {e}")

            # Fallback to empty structure with informative placeholders
            return self._get_fallback_enhanced_extended_data()

        except Exception as e:
            logger.error(f"❌ Error in enhanced extended patient data preparation: {e}")
            return self._get_fallback_enhanced_extended_data()

    def _process_enhanced_admin_data(self, enhanced_data) -> Dict[str, Any]:
        """Process enhanced administrative data into template-ready format"""

        # Process document information
        document_info = self._process_enhanced_document_info(
            enhanced_data.document_info
        )

        # Process legal authenticator
        legal_authenticator = self._process_enhanced_person_info(
            enhanced_data.legal_authenticator
        )

        # Process all authors (HCP and devices)
        authors = [
            self._process_enhanced_person_info(author)
            for author in enhanced_data.authors
        ]

        # Process other contacts
        other_contacts = [
            self._process_enhanced_person_info(contact)
            for contact in enhanced_data.other_contacts
        ]

        # Process patient contact information
        contact_information = self._process_enhanced_contact_info(
            enhanced_data.patient_contact_info
        )

        # Process healthcare team (combination of authors, legal auth, preferred HCP)
        healthcare_team = self._build_enhanced_healthcare_team(enhanced_data)

        # Process custodian
        custodian_organization = self._process_enhanced_organization_info(
            enhanced_data.custodian_organization
        )

        # Build navigation tabs with actual counts
        navigation_tabs = self._build_enhanced_navigation_tabs(
            document_info=document_info,
            legal_authenticator=legal_authenticator,
            other_contacts=other_contacts,
            contact_information=contact_information,
            healthcare_team=healthcare_team,
        )

        return {
            "section_type": "extended_patient",
            "section_code": "enhanced_extended_demographics",
            "has_meaningful_data": True,
            "navigation_tabs": navigation_tabs,
            # Data sections
            "document_information": document_info,
            "legal_authenticator": legal_authenticator,
            "authors": authors,
            "other_contacts": other_contacts,
            "contact_information": contact_information,
            "healthcare_team": healthcare_team,
            "custodian_organization": custodian_organization,
            # Styling
            "styling": {
                "header_class": "bg-info",
                "icon": "fas fa-address-book",
                "card_class": "enhanced-extended-patient-section",
            },
            # Debug info
            "extraction_summary": enhanced_data.extraction_summary,
        }

    def _process_enhanced_document_info(self, doc_info) -> Dict[str, Any]:
        """Process document information for template"""
        document_fields = []

        if doc_info.creation_date:
            document_fields.append(
                {
                    "label": "Creation Date",
                    "value": doc_info.creation_date,
                    "raw_value": doc_info.creation_date,
                    "type": "date",
                }
            )

        if doc_info.last_update_date:
            document_fields.append(
                {
                    "label": "Last Updated",
                    "value": doc_info.last_update_date,
                    "raw_value": doc_info.last_update_date,
                    "type": "date",
                }
            )

        if doc_info.document_id:
            document_fields.append(
                {
                    "label": "Document ID",
                    "value": doc_info.document_id,
                    "type": "identifier",
                }
            )

        if doc_info.custodian_name:
            document_fields.append(
                {
                    "label": "Custodian",
                    "value": doc_info.custodian_name,
                    "type": "organization",
                }
            )

        if doc_info.language_code:
            document_fields.append(
                {
                    "label": "Document Language",
                    "value": doc_info.language_code,
                    "type": "code",
                }
            )

        return {
            "has_document_info": bool(document_fields),
            "document_fields": document_fields,
            "total_fields": len(document_fields),
        }

    def _process_enhanced_person_info(self, person_info) -> Dict[str, Any]:
        """Process person information for template"""
        if not person_info:
            return {}

        return {
            "family_name": person_info.family_name or "",
            "given_name": person_info.given_name or "",
            "title": person_info.title or "",
            "role": person_info.role or "",
            "specialty": person_info.specialty or "",
            "function_code": person_info.function_code or "",
            "organization": self._process_enhanced_organization_info(
                person_info.organization
            ),
            "contact_info": self._process_enhanced_contact_info(
                person_info.contact_info
            ),
        }

    def _process_enhanced_organization_info(self, org_info) -> Dict[str, Any]:
        """Process organization information for template"""
        if not org_info:
            return {
                "name": "",
                "addresses": [],
                "telecoms": [],
                "organization_type": "",
            }

        return {
            "name": org_info.name or "",
            "addresses": org_info.addresses or [],
            "telecoms": org_info.telecoms or [],
            "organization_type": org_info.organization_type or "",
        }

    def _process_enhanced_contact_info(self, contact_info) -> Dict[str, Any]:
        """Process contact information for template"""
        if not contact_info:
            return {
                "addresses": [],
                "telecoms": [],
                "has_addresses": False,
                "has_telecoms": False,
                "total_items": 0,
            }

        addresses = contact_info.addresses or []
        telecoms = contact_info.telecoms or []

        return {
            "addresses": addresses,
            "telecoms": telecoms,
            "has_addresses": bool(addresses),
            "has_telecoms": bool(telecoms),
            "total_items": len(addresses) + len(telecoms),
        }

    def _build_enhanced_healthcare_team(self, enhanced_data) -> Dict[str, Any]:
        """Build healthcare team from various sources"""
        team_members = []

        # Add legal authenticator if present
        if (
            enhanced_data.legal_authenticator
            and enhanced_data.legal_authenticator.family_name
        ):
            team_members.append(
                {
                    "name": f"{enhanced_data.legal_authenticator.given_name} {enhanced_data.legal_authenticator.family_name}".strip(),
                    "role": enhanced_data.legal_authenticator.role,
                    "specialty": enhanced_data.legal_authenticator.specialty,
                    "organization": enhanced_data.legal_authenticator.organization.name,
                    "contact": "",  # Could extract from contact_info if needed
                }
            )

        # Add authors (HCPs, not devices)
        for author in enhanced_data.authors:
            if author.role == "Author (HCP)" and (
                author.family_name or author.given_name
            ):
                team_members.append(
                    {
                        "name": f"{author.given_name} {author.family_name}".strip(),
                        "role": author.role,
                        "specialty": author.specialty,
                        "organization": author.organization.name,
                        "contact": "",
                    }
                )

        return {
            "has_team_info": bool(team_members),
            "team_members": team_members,
            "total_members": len(team_members),
        }

    def _build_enhanced_navigation_tabs(self, **data_sections) -> List[Dict[str, Any]]:
        """Build navigation tabs with actual counts from enhanced data"""
        tabs = []

        # Document Info Tab
        doc_count = data_sections.get("document_info", {}).get("total_fields", 0)
        tabs.append(
            {
                "id": "document",
                "label": "Document Info",
                "icon": "fas fa-file-medical",
                "count": doc_count,
                "active": True,  # First tab is active
            }
        )

        # Legal Authenticator Tab
        legal_auth = data_sections.get("legal_authenticator", {})
        legal_count = (
            1 if (legal_auth.get("family_name") or legal_auth.get("given_name")) else 0
        )
        tabs.append(
            {
                "id": "legal_auth",
                "label": "Legal Authenticator",
                "icon": "fas fa-user-shield",
                "count": legal_count,
                "active": False,
            }
        )

        # Other Contacts Tab
        other_contacts = data_sections.get("other_contacts", [])
        other_count = len(
            [c for c in other_contacts if c.get("family_name") or c.get("given_name")]
        )
        tabs.append(
            {
                "id": "other_contacts",
                "label": "Other Contacts",
                "icon": "fas fa-user-friends",
                "count": other_count,
                "active": False,
            }
        )

        # Contact Details Tab
        contact_info = data_sections.get("contact_information", {})
        contact_count = contact_info.get("total_items", 0)
        tabs.append(
            {
                "id": "contact",
                "label": "Contact Details",
                "icon": "fas fa-address-card",
                "count": contact_count,
                "active": False,
            }
        )

        # Healthcare Team Tab
        healthcare_team = data_sections.get("healthcare_team", {})
        team_count = healthcare_team.get("total_members", 0)
        tabs.append(
            {
                "id": "healthcare",
                "label": "Healthcare Team",
                "icon": "fas fa-user-md",
                "count": team_count,
                "active": False,
            }
        )

        return tabs

    def _get_fallback_enhanced_extended_data(self) -> Dict[str, Any]:
        """Fallback data structure when no meaningful data is found"""
        return {
            "section_type": "extended_patient",
            "section_code": "enhanced_extended_demographics",
            "has_meaningful_data": False,
            "navigation_tabs": [
                {
                    "id": "document",
                    "label": "Document Info",
                    "icon": "fas fa-file-medical",
                    "count": 0,
                    "active": True,
                },
                {
                    "id": "legal_auth",
                    "label": "Legal Authenticator",
                    "icon": "fas fa-user-shield",
                    "count": 0,
                    "active": False,
                },
                {
                    "id": "other_contacts",
                    "label": "Other Contacts",
                    "icon": "fas fa-user-friends",
                    "count": 0,
                    "active": False,
                },
                {
                    "id": "contact",
                    "label": "Contact Details",
                    "icon": "fas fa-address-card",
                    "count": 0,
                    "active": False,
                },
                {
                    "id": "healthcare",
                    "label": "Healthcare Team",
                    "icon": "fas fa-user-md",
                    "count": 0,
                    "active": False,
                },
            ],
            "document_information": {
                "has_document_info": False,
                "document_fields": [],
                "total_fields": 0,
            },
            "legal_authenticator": {},
            "other_contacts": [],
            "contact_information": {
                "has_addresses": False,
                "has_telecoms": False,
                "total_items": 0,
                "addresses": [],
                "telecoms": [],
            },
            "healthcare_team": {
                "has_team_info": False,
                "team_members": [],
                "total_members": 0,
            },
            "styling": {
                "header_class": "bg-info",
                "icon": "fas fa-address-book",
                "card_class": "enhanced-extended-patient-section",
            },
        }

    def prepare_extended_patient_data(
        self,
        administrative_data: Dict[str, Any],
        patient_extended_data: Dict[str, Any],
        has_administrative_data: bool = False,
        xml_content: str = "",
    ) -> Dict[str, Any]:
        """
        Prepare extended patient data for template rendering

        IMPORTANT - Data Availability Context:
        - If administrative_data is empty/None: Template shows "Limited Extended Information"
        - If administrative_data has content: Template generates dynamic tabs with rich content
        - Session ID in URL (e.g., 549316) is temporary identifier, not patient ID
        - Real patient identifiers come from CDA content and are PHI-protected

        Returns:
            Dictionary with extended patient data for template, including:
            - has_meaningful_data: Boolean indicating if tabs should be generated
            - navigation_tabs: List of tab configurations with counts
            - contact_information, healthcare_team, etc.: Processed data sections
        """
        try:
            # Debug logging for investigation
            logger.info(f"DEBUG: prepare_extended_patient_data called")
            logger.info(
                f"DEBUG: xml_content length: {len(xml_content) if xml_content else 0}"
            )
            logger.info(f"DEBUG: has_administrative_data: {has_administrative_data}")
            logger.info(
                f"DEBUG: administrative_data keys: {list(administrative_data.keys()) if administrative_data else 'None'}"
            )

            # First attempt to use the powerful CDAAdministrativeExtractor if XML is available
            enhanced_admin_data = None
            if xml_content:
                try:
                    from enhanced_cda_administrative_extractor import (
                        EnhancedCDAAdministrativeExtractor,
                    )

                    logger.info(
                        "🔄 Using EnhancedCDAAdministrativeExtractor for comprehensive EU PS data extraction"
                    )
                    print(
                        "DEBUG: Enhanced extractor starting with XML content length:",
                        len(xml_content) if xml_content else 0,
                    )
                    admin_extractor = EnhancedCDAAdministrativeExtractor()
                    enhanced_admin_data = admin_extractor.extract_administrative_data(
                        xml_content
                    )

                    if enhanced_admin_data:
                        logger.info("✅ Enhanced administrative extraction successful")
                        print(
                            f"DEBUG: Enhanced extraction found data - Patient contact info: {enhanced_admin_data.patient_contact_info is not None}"
                        )
                        # Convert the enhanced dataclass structure to the format expected by our processor
                        administrative_data = (
                            self._convert_enhanced_data_to_admin_format(
                                enhanced_admin_data
                            )
                        )
                        print(
                            f"DEBUG: Converted admin data - Patient contact addresses: {len(administrative_data.get('patient_contact_info', {}).get('addresses', []))}"
                        )
                        print(
                            f"DEBUG: Converted admin data type: {type(administrative_data)}"
                        )
                        print(
                            f"DEBUG: Converted admin data keys: {list(administrative_data.keys()) if administrative_data else 'None'}"
                        )
                        print(
                            f"DEBUG: patient_contact_info: {administrative_data.get('patient_contact_info', {})}"
                        )
                    else:
                        logger.warning(
                            "⚠️ Enhanced extraction returned no data, falling back to basic data"
                        )
                        print("DEBUG: Enhanced extraction returned None")

                except ImportError as e:
                    logger.warning(
                        f"⚠️ Enhanced extractor not available: {e}, using basic data"
                    )
                    print(f"DEBUG: Import error - {e}")
                except Exception as e:
                    logger.error(
                        f"❌ Enhanced extraction failed: {e}, using basic data"
                    )
                    print(f"DEBUG: Enhanced extraction exception - {e}")
            else:
                print("DEBUG: No XML content provided to enhanced extractor")

            print(
                f"DEBUG: About to call _has_meaningful_extended_data with administrative_data type: {type(administrative_data)}"
            )
            print(
                f"DEBUG: administrative_data keys: {list(administrative_data.keys()) if administrative_data else 'None'}"
            )
            has_meaningful = self._has_meaningful_extended_data(administrative_data)
            print(f"DEBUG: _has_meaningful_extended_data returned: {has_meaningful}")

            # Determine what components to create
            contact_info = self._process_contact_information(administrative_data)
            healthcare_team = self._process_healthcare_team(administrative_data)
            document_info = self._process_document_information(administrative_data)
            additional_components = self._detect_additional_extended_components(
                administrative_data
            )
            navigation_tabs = self._build_extended_navigation_tabs(
                contact_info=contact_info,
                healthcare_team=healthcare_team,
                document_info=document_info,
                additional_components=additional_components,
            )

            extended_data = {
                "section_type": "extended_patient",
                "section_code": "extended_demographics",
                "has_meaningful_data": has_meaningful,
                "contact_information": contact_info,
                "healthcare_team": healthcare_team,
                "document_information": document_info,
                "additional_components": additional_components,
                "navigation_tabs": navigation_tabs,
                "styling": {
                    "header_class": "bg-info",
                    "icon": "fas fa-address-book",
                    "card_class": "extended-patient-section",
                },
            }

            logger.info(
                f"✅ Extended patient data processed - {contact_info.get('total_items', 0)} contact items"
            )
            return extended_data

        except Exception as e:
            logger.error(f"❌ Error processing extended patient data: {e}")
            return self._get_fallback_extended_data()

    def _convert_enhanced_admin_data(self, enhanced_admin_data) -> Dict[str, Any]:
        """
        Convert the rich AdministrativeData dataclass structure to our expected format

        Args:
            enhanced_admin_data: AdministrativeData object from CDAAdministrativeExtractor

        Returns:
            Dictionary in the format expected by our processing methods
        """
        try:
            # Convert the structured data to our expected format
            converted_data = {
                "patient_contact_info": {"addresses": [], "telecoms": []},
                "author_hcp": {
                    "family_name": "",
                    "given_name": "",
                    "title": "",
                    "role": "Author (HCP)",
                    "specialty": "",
                    "organization": {
                        "name": "",
                        "addresses": [],
                        "telecoms": [],
                        "organization_type": "",
                    },
                    "contact_info": {"addresses": [], "telecoms": []},
                },
                "legal_authenticator": {
                    "family_name": "",
                    "given_name": "",
                    "title": "",
                    "role": "Legal Authenticator",
                    "specialty": "",
                    "organization": {
                        "name": "",
                        "addresses": [],
                        "telecoms": [],
                        "organization_type": "",
                    },
                    "contact_info": {"addresses": [], "telecoms": []},
                },
                "custodian_organization": {
                    "name": "",
                    "addresses": [],
                    "telecoms": [],
                    "organization_type": "Custodian",
                },
                "guardian": {
                    "family_name": "",
                    "given_name": "",
                    "title": "",
                    "role": "Guardian",
                    "specialty": "",
                    "organization": {
                        "name": "",
                        "addresses": [],
                        "telecoms": [],
                        "organization_type": "",
                    },
                    "contact_info": {"addresses": [], "telecoms": []},
                },
                "other_contacts": [],
                "preferred_hcp": {
                    "name": "",
                    "addresses": [],
                    "telecoms": [],
                    "organization_type": "Preferred HCP Organization",
                },
                "document_creation_date": "",
                "document_last_update_date": "",
                "document_version_number": "",
                "document_set_id": "",
            }

            # Patient contact info
            if (
                hasattr(enhanced_admin_data, "patient_contact_info")
                and enhanced_admin_data.patient_contact_info
            ):
                pci = enhanced_admin_data.patient_contact_info
                if hasattr(pci, "addresses") and pci.addresses:
                    converted_data["patient_contact_info"]["addresses"] = pci.addresses
                if hasattr(pci, "telecoms") and pci.telecoms:
                    converted_data["patient_contact_info"]["telecoms"] = pci.telecoms

            # Author HCP
            if (
                hasattr(enhanced_admin_data, "author_hcp")
                and enhanced_admin_data.author_hcp
            ):
                author = enhanced_admin_data.author_hcp
                converted_data["author_hcp"]["family_name"] = getattr(
                    author, "family_name", ""
                )
                converted_data["author_hcp"]["given_name"] = getattr(
                    author, "given_name", ""
                )
                converted_data["author_hcp"]["title"] = getattr(author, "title", "")
                converted_data["author_hcp"]["specialty"] = getattr(
                    author, "specialty", ""
                )

                # Author organization
                if hasattr(author, "organization") and author.organization:
                    org = author.organization
                    converted_data["author_hcp"]["organization"]["name"] = getattr(
                        org, "name", ""
                    )
                    converted_data["author_hcp"]["organization"][
                        "organization_type"
                    ] = getattr(org, "organization_type", "")
                    if hasattr(org, "addresses") and org.addresses:
                        converted_data["author_hcp"]["organization"][
                            "addresses"
                        ] = org.addresses
                    if hasattr(org, "telecoms") and org.telecoms:
                        converted_data["author_hcp"]["organization"][
                            "telecoms"
                        ] = org.telecoms

                # Author contact info
                if hasattr(author, "contact_info") and author.contact_info:
                    contact = author.contact_info
                    if hasattr(contact, "addresses") and contact.addresses:
                        converted_data["author_hcp"]["contact_info"][
                            "addresses"
                        ] = contact.addresses
                    if hasattr(contact, "telecoms") and contact.telecoms:
                        converted_data["author_hcp"]["contact_info"][
                            "telecoms"
                        ] = contact.telecoms

            # Legal authenticator
            if (
                hasattr(enhanced_admin_data, "legal_authenticator")
                and enhanced_admin_data.legal_authenticator
            ):
                legal = enhanced_admin_data.legal_authenticator
                converted_data["legal_authenticator"]["family_name"] = getattr(
                    legal, "family_name", ""
                )
                converted_data["legal_authenticator"]["given_name"] = getattr(
                    legal, "given_name", ""
                )
                converted_data["legal_authenticator"]["title"] = getattr(
                    legal, "title", ""
                )
                converted_data["legal_authenticator"]["specialty"] = getattr(
                    legal, "specialty", ""
                )

                # Legal auth organization
                if hasattr(legal, "organization") and legal.organization:
                    org = legal.organization
                    converted_data["legal_authenticator"]["organization"]["name"] = (
                        getattr(org, "name", "")
                    )
                    converted_data["legal_authenticator"]["organization"][
                        "organization_type"
                    ] = getattr(org, "organization_type", "")
                    if hasattr(org, "addresses") and org.addresses:
                        converted_data["legal_authenticator"]["organization"][
                            "addresses"
                        ] = org.addresses
                    if hasattr(org, "telecoms") and org.telecoms:
                        converted_data["legal_authenticator"]["organization"][
                            "telecoms"
                        ] = org.telecoms

                # Legal auth contact info
                if hasattr(legal, "contact_info") and legal.contact_info:
                    contact = legal.contact_info
                    if hasattr(contact, "addresses") and contact.addresses:
                        converted_data["legal_authenticator"]["contact_info"][
                            "addresses"
                        ] = contact.addresses
                    if hasattr(contact, "telecoms") and contact.telecoms:
                        converted_data["legal_authenticator"]["contact_info"][
                            "telecoms"
                        ] = contact.telecoms

            # Custodian organization
            if (
                hasattr(enhanced_admin_data, "custodian_organization")
                and enhanced_admin_data.custodian_organization
            ):
                custodian = enhanced_admin_data.custodian_organization
                converted_data["custodian_organization"]["name"] = getattr(
                    custodian, "name", ""
                )
                converted_data["custodian_organization"]["organization_type"] = getattr(
                    custodian, "organization_type", "Custodian"
                )
                if hasattr(custodian, "addresses") and custodian.addresses:
                    converted_data["custodian_organization"][
                        "addresses"
                    ] = custodian.addresses
                if hasattr(custodian, "telecoms") and custodian.telecoms:
                    converted_data["custodian_organization"][
                        "telecoms"
                    ] = custodian.telecoms

            # Guardian
            if (
                hasattr(enhanced_admin_data, "guardian")
                and enhanced_admin_data.guardian
            ):
                guardian = enhanced_admin_data.guardian
                converted_data["guardian"]["family_name"] = getattr(
                    guardian, "family_name", ""
                )
                converted_data["guardian"]["given_name"] = getattr(
                    guardian, "given_name", ""
                )
                converted_data["guardian"]["title"] = getattr(guardian, "title", "")
                converted_data["guardian"]["specialty"] = getattr(
                    guardian, "specialty", ""
                )

                # Guardian organization
                if hasattr(guardian, "organization") and guardian.organization:
                    org = guardian.organization
                    converted_data["guardian"]["organization"]["name"] = getattr(
                        org, "name", ""
                    )
                    converted_data["guardian"]["organization"]["organization_type"] = (
                        getattr(org, "organization_type", "")
                    )
                    if hasattr(org, "addresses") and org.addresses:
                        converted_data["guardian"]["organization"][
                            "addresses"
                        ] = org.addresses
                    if hasattr(org, "telecoms") and org.telecoms:
                        converted_data["guardian"]["organization"][
                            "telecoms"
                        ] = org.telecoms

                # Guardian contact info
                if hasattr(guardian, "contact_info") and guardian.contact_info:
                    contact = guardian.contact_info
                    if hasattr(contact, "addresses") and contact.addresses:
                        converted_data["guardian"]["contact_info"][
                            "addresses"
                        ] = contact.addresses
                    if hasattr(contact, "telecoms") and contact.telecoms:
                        converted_data["guardian"]["contact_info"][
                            "telecoms"
                        ] = contact.telecoms

            # Other contacts
            if (
                hasattr(enhanced_admin_data, "other_contacts")
                and enhanced_admin_data.other_contacts
            ):
                other_contacts = []
                for contact in enhanced_admin_data.other_contacts:
                    contact_dict = {
                        "family_name": getattr(contact, "family_name", ""),
                        "given_name": getattr(contact, "given_name", ""),
                        "title": getattr(contact, "title", ""),
                        "role": getattr(contact, "role", ""),
                        "specialty": getattr(contact, "specialty", ""),
                        "organization": {
                            "name": "",
                            "addresses": [],
                            "telecoms": [],
                            "organization_type": "",
                        },
                        "contact_info": {"addresses": [], "telecoms": []},
                    }

                    # Contact organization
                    if hasattr(contact, "organization") and contact.organization:
                        org = contact.organization
                        contact_dict["organization"]["name"] = getattr(org, "name", "")
                        contact_dict["organization"]["organization_type"] = getattr(
                            org, "organization_type", ""
                        )
                        if hasattr(org, "addresses") and org.addresses:
                            contact_dict["organization"]["addresses"] = org.addresses
                        if hasattr(org, "telecoms") and org.telecoms:
                            contact_dict["organization"]["telecoms"] = org.telecoms

                    # Contact info
                    if hasattr(contact, "contact_info") and contact.contact_info:
                        contact_info = contact.contact_info
                        if (
                            hasattr(contact_info, "addresses")
                            and contact_info.addresses
                        ):
                            contact_dict["contact_info"][
                                "addresses"
                            ] = contact_info.addresses
                        if hasattr(contact_info, "telecoms") and contact_info.telecoms:
                            contact_dict["contact_info"][
                                "telecoms"
                            ] = contact_info.telecoms

                    other_contacts.append(contact_dict)

                converted_data["other_contacts"] = other_contacts

            # Preferred HCP
            if (
                hasattr(enhanced_admin_data, "preferred_hcp")
                and enhanced_admin_data.preferred_hcp
            ):
                preferred = enhanced_admin_data.preferred_hcp
                converted_data["preferred_hcp"]["name"] = getattr(preferred, "name", "")
                converted_data["preferred_hcp"]["organization_type"] = getattr(
                    preferred, "organization_type", "Preferred HCP Organization"
                )
                if hasattr(preferred, "addresses") and preferred.addresses:
                    converted_data["preferred_hcp"]["addresses"] = preferred.addresses
                if hasattr(preferred, "telecoms") and preferred.telecoms:
                    converted_data["preferred_hcp"]["telecoms"] = preferred.telecoms

            # Document metadata
            converted_data["document_creation_date"] = getattr(
                enhanced_admin_data, "document_creation_date", ""
            )
            converted_data["document_last_update_date"] = getattr(
                enhanced_admin_data, "document_last_update_date", ""
            )
            converted_data["document_version_number"] = getattr(
                enhanced_admin_data, "document_version_number", ""
            )
            converted_data["document_set_id"] = getattr(
                enhanced_admin_data, "document_set_id", ""
            )

            logger.info(
                f"✅ Successfully converted enhanced admin data - found {len(converted_data['other_contacts'])} other contacts"
            )
            return converted_data

        except Exception as e:
            logger.error(f"❌ Error converting enhanced admin data: {e}")
            return {}  # Return empty dict to fall back to basic data

    def _convert_enhanced_data_to_admin_format(self, enhanced_data) -> Dict[str, Any]:
        """
        Convert EnhancedAdministrativeData to the format expected by our processing methods

        Args:
            enhanced_data: EnhancedAdministrativeData object from EnhancedCDAAdministrativeExtractor

        Returns:
            Dictionary in the format expected by our processing methods
        """
        logger = logging.getLogger(__name__)
        logger.info("=== START CONVERSION DEBUG ===")
        logger.info(f"Enhanced data type: {type(enhanced_data)}")
        logger.info(
            f"Enhanced data has patient_contacts: {hasattr(enhanced_data, 'patient_contacts')}"
        )
        if hasattr(enhanced_data, "patient_contacts"):
            logger.info(
                f"Patient contacts length: {len(enhanced_data.patient_contacts) if enhanced_data.patient_contacts else 0}"
            )

        try:
            converted_data = {
                "patient_contact_info": {"addresses": [], "telecoms": []},
                "author_hcp": {
                    "family_name": "",
                    "given_name": "",
                    "title": "",
                    "specialty": "",
                    "organization": {
                        "name": "",
                        "addresses": [],
                        "telecoms": [],
                        "organization_type": "",
                    },
                    "contact_info": {"addresses": [], "telecoms": []},
                },
                "other_contacts": [],
                "preferred_hcp": {
                    "name": "",
                    "addresses": [],
                    "telecoms": [],
                    "organization_type": "Preferred HCP Organization",
                },
                "document_creation_date": (
                    enhanced_data.document_info.creation_date
                    if enhanced_data.document_info
                    else ""
                ),
                "document_last_update_date": (
                    enhanced_data.document_info.last_update_date
                    if enhanced_data.document_info
                    else ""
                ),
                "document_version_number": (
                    enhanced_data.document_info.version_number
                    if enhanced_data.document_info
                    else ""
                ),
                "document_set_id": (
                    enhanced_data.document_info.set_id
                    if enhanced_data.document_info
                    else ""
                ),
            }

            # Process patient contacts
            logger.info("Processing patient contacts...")
            if enhanced_data.patient_contact_info:
                logger.info("Enhanced data has patient_contact_info")
                contact = enhanced_data.patient_contact_info
                logger.info(f"Contact type: {type(contact)}")
                logger.info(f"Contact has addresses: {hasattr(contact, 'addresses')}")
                logger.info(f"Contact has telecoms: {hasattr(contact, 'telecoms')}")
                if hasattr(contact, "addresses"):
                    logger.info(
                        f"Addresses count: {len(contact.addresses) if contact.addresses else 0}"
                    )
                if hasattr(contact, "telecoms"):
                    logger.info(
                        f"Telecoms count: {len(contact.telecoms) if contact.telecoms else 0}"
                    )

                if contact.addresses:
                    logger.info(
                        f"Adding {len(contact.addresses)} addresses to converted data"
                    )
                    converted_data["patient_contact_info"]["addresses"].extend(
                        contact.addresses
                    )
                if contact.telecoms:
                    logger.info(
                        f"Adding {len(contact.telecoms)} telecoms to converted data"
                    )
                    converted_data["patient_contact_info"]["telecoms"].extend(
                        contact.telecoms
                    )
            else:
                logger.warning("Enhanced data has NO patient_contact_info")

            # Process authors (use first author as primary HCP)
            if enhanced_data.authors:
                primary_author = enhanced_data.authors[0]
                converted_data["author_hcp"]["family_name"] = (
                    primary_author.family_name or ""
                )
                converted_data["author_hcp"]["given_name"] = (
                    primary_author.given_name or ""
                )
                converted_data["author_hcp"]["title"] = primary_author.title or ""
                if primary_author.organization:
                    converted_data["author_hcp"]["organization"]["name"] = (
                        primary_author.organization.name or ""
                    )
                    if primary_author.organization.addresses:
                        converted_data["author_hcp"]["organization"][
                            "addresses"
                        ] = primary_author.organization.addresses
                    if primary_author.organization.telecoms:
                        converted_data["author_hcp"]["organization"][
                            "telecoms"
                        ] = primary_author.organization.telecoms

            # Process other contacts
            if enhanced_data.other_contacts:
                for contact in enhanced_data.other_contacts:
                    contact_dict = {
                        "name": "",
                        "role": contact.role or "Contact",
                        "addresses": (
                            contact.contact_info.addresses
                            if contact.contact_info
                            else []
                        ),
                        "telecoms": (
                            contact.contact_info.telecoms
                            if contact.contact_info
                            else []
                        ),
                    }
                    contact_dict["name"] = (
                        f"{contact.given_name or ''} {contact.family_name or ''}".strip()
                    )
                    if contact.organization and contact.organization.name:
                        contact_dict["organization_name"] = contact.organization.name
                    converted_data["other_contacts"].append(contact_dict)

            # Process legal authenticator as preferred HCP
            if (
                enhanced_data.legal_authenticator
                and enhanced_data.legal_authenticator.given_name
            ):
                la = enhanced_data.legal_authenticator
                converted_data["preferred_hcp"][
                    "name"
                ] = f"{la.given_name or ''} {la.family_name or ''}".strip()
                if la.contact_info and la.contact_info.addresses:
                    converted_data["preferred_hcp"][
                        "addresses"
                    ] = la.contact_info.addresses
                if la.contact_info and la.contact_info.telecoms:
                    converted_data["preferred_hcp"][
                        "telecoms"
                    ] = la.contact_info.telecoms

            logger.info(
                f"✅ Successfully converted enhanced data - found {len(converted_data['other_contacts'])} other contacts"
            )
            return converted_data

        except Exception as e:
            logger.error(f"❌ Error converting enhanced data: {e}")
            return {}  # Return empty dict to fall back to basic data

    def prepare_summary_statistics_data(
        self,
        sections_count: int = 0,
        medical_terms_count: int = 0,
        coded_sections_count: int = 0,
        coded_sections_percentage: float = 0.0,
        translation_quality: str = None,
        uses_coded_sections: bool = False,
    ) -> Dict[str, Any]:
        """
        Process summary statistics for consistent display

        Args:
            sections_count: Total number of sections
            medical_terms_count: Total medical terms found
            coded_sections_count: Number of coded sections
            coded_sections_percentage: Percentage of coded sections
            translation_quality: Quality of translation
            uses_coded_sections: Whether document uses coded sections

        Returns:
            Structured summary statistics data for template
        """
        try:
            summary_data = {
                "section_type": "summary_statistics",
                "section_code": "processing_summary",
                "statistics": [
                    {
                        "value": sections_count,
                        "label": "Total Sections",
                        "icon": "fas fa-list",
                        "color": "text-primary",
                        "description": "Clinical sections processed",
                    },
                    {
                        "value": medical_terms_count,
                        "label": "Medical Terms",
                        "icon": "fas fa-stethoscope",
                        "color": "text-success",
                        "description": "Coded medical terminology",
                    },
                    {
                        "value": coded_sections_count,
                        "label": "Coded Sections",
                        "icon": "fas fa-code",
                        "color": "text-info",
                        "description": "Sections with medical codes",
                    },
                    {
                        "value": f"{coded_sections_percentage:.0f}%",
                        "label": "Terminology Coverage",
                        "icon": "fas fa-chart-pie",
                        "color": "text-warning",
                        "description": "Medical coding completeness",
                    },
                ],
                "quality_info": {
                    "translation_quality": translation_quality or "Standard",
                    "uses_coded_sections": uses_coded_sections,
                    "quality_score": coded_sections_percentage,
                },
                "styling": {
                    "header_class": "bg-secondary",
                    "icon": "fas fa-chart-bar",
                    "card_class": "summary-stats-section",
                },
            }

            logger.info(
                f"✅ Summary statistics processed - {sections_count} sections, {medical_terms_count} terms"
            )
            return summary_data

        except Exception as e:
            logger.error(f"❌ Error processing summary statistics: {e}")
            return self._get_fallback_summary_data()

    # Helper methods
    def _get_patient_display_name(self, patient_identity: Dict[str, Any]) -> str:
        """Extract patient display name with fallback logic"""
        if patient_identity.get("full_name"):
            return patient_identity["full_name"]
        elif patient_identity.get("given_name") or patient_identity.get("family_name"):
            given = patient_identity.get("given_name", "")
            family = patient_identity.get("family_name", "")
            return f"{given} {family}".strip()
        else:
            return "Patient"

    def _format_patient_birth_date(
        self, patient_identity: Dict[str, Any]
    ) -> Dict[str, str]:
        """Format birth date using consistent date formatter"""
        if patient_identity.get("birth_date_formatted"):
            return {
                "formatted": patient_identity["birth_date_formatted"],
                "raw": patient_identity.get("birth_date", ""),
            }
        elif patient_identity.get("birth_date"):
            # Use the date formatter for consistent formatting
            raw_date = patient_identity["birth_date"]
            formatted_date = self.date_formatter.format_birth_date(raw_date)
            return {"formatted": formatted_date, "raw": raw_date}
        else:
            return {"formatted": "Unknown", "raw": ""}

    def _extract_document_metadata(
        self, patient_identity: Dict[str, Any]
    ) -> Dict[str, str]:
        """Extract document metadata"""
        doc_metadata = patient_identity.get("document_metadata", {})
        return {
            "title": doc_metadata.get("title", "Patient Summary"),
            "language_code": doc_metadata.get("language_code", "en"),
        }

    def _process_contact_information(
        self, administrative_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process contact information"""
        contact_info = administrative_data.get("patient_contact_info", {})

        addresses = contact_info.get("addresses", [])
        telecoms = contact_info.get("telecoms", [])

        return {
            "addresses": addresses,
            "telecoms": telecoms,
            "total_items": len(addresses) + len(telecoms),
            "has_addresses": len(addresses) > 0,
            "has_telecoms": len(telecoms) > 0,
        }

    def _process_healthcare_team(
        self, administrative_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process healthcare team information"""
        author_hcp = administrative_data.get("author_hcp", {})
        legal_auth = administrative_data.get("legal_authenticator", {})
        preferred_hcp = administrative_data.get("preferred_hcp", {})

        team_members = []
        if author_hcp.get("family_name"):
            team_members.append({"role": "Author", "data": author_hcp})
        if legal_auth.get("family_name"):
            team_members.append({"role": "Legal Authenticator", "data": legal_auth})
        if preferred_hcp.get("name"):
            team_members.append({"role": "Preferred HCP", "data": preferred_hcp})

        return {
            "team_members": team_members,
            "total_members": len(team_members),
            "has_team_info": len(team_members) > 0,
        }

    def _process_document_information(
        self, administrative_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process document information with date formatting"""
        doc_fields = []

        # Extract available document fields
        if administrative_data.get("document_creation_date"):
            raw_date = administrative_data["document_creation_date"]
            formatted_date = self.date_formatter.format_document_date(raw_date)
            doc_fields.append(
                {
                    "label": "Creation Date",
                    "value": formatted_date,
                    "raw_value": raw_date,
                }
            )

        if administrative_data.get("document_last_update_date"):
            raw_date = administrative_data["document_last_update_date"]
            formatted_date = self.date_formatter.format_document_date(raw_date)
            doc_fields.append(
                {
                    "label": "Last Updated",
                    "value": formatted_date,
                    "raw_value": raw_date,
                }
            )

        custodian = administrative_data.get("custodian_organization", {})
        if custodian.get("name"):
            doc_fields.append({"label": "Custodian", "value": custodian["name"]})

        return {
            "document_fields": doc_fields,
            "total_fields": len(doc_fields),
            "has_document_info": len(doc_fields) > 0,
        }

    def _has_meaningful_extended_data(
        self, administrative_data: Dict[str, Any]
    ) -> bool:
        """Check if administrative data contains meaningful information"""
        print(
            f"DEBUG _has_meaningful_extended_data: Input data type: {type(administrative_data)}"
        )
        print(
            f"DEBUG _has_meaningful_extended_data: Input data keys: {list(administrative_data.keys()) if administrative_data else 'None'}"
        )

        if not administrative_data:
            logger.warning(
                "🔍 _has_meaningful_extended_data: No administrative_data provided"
            )
            print("DEBUG _has_meaningful_extended_data: RETURNING FALSE - No data")
            return False

        # Check for meaningful contact info
        contact_info = administrative_data.get("patient_contact_info", {})
        print(f"DEBUG _has_meaningful_extended_data: contact_info = {contact_info}")
        logger.info(f"🔍 _has_meaningful_extended_data: contact_info = {contact_info}")

        if contact_info.get("addresses") or contact_info.get("telecoms"):
            logger.info(
                "🔍 _has_meaningful_extended_data: Found addresses or telecoms - returning True"
            )
            print(
                "DEBUG _has_meaningful_extended_data: RETURNING TRUE - Found addresses or telecoms"
            )
            return True

        # Check for healthcare team info
        author_hcp = administrative_data.get("author_hcp", {}).get("family_name")
        legal_auth = administrative_data.get("legal_authenticator", {}).get(
            "family_name"
        )
        preferred_hcp = administrative_data.get("preferred_hcp", {}).get("name")

        logger.info(
            f"🔍 _has_meaningful_extended_data: author_hcp={author_hcp}, legal_auth={legal_auth}, preferred_hcp={preferred_hcp}"
        )

        if author_hcp or legal_auth or preferred_hcp:
            logger.info(
                "🔍 _has_meaningful_extended_data: Found healthcare team info - returning True"
            )
            return True

        # Check for document info
        doc_date = administrative_data.get("document_creation_date")
        custodian_name = administrative_data.get("custodian_organization", {}).get(
            "name"
        )

        logger.info(
            f"🔍 _has_meaningful_extended_data: doc_date={doc_date}, custodian_name={custodian_name}"
        )

        if doc_date or custodian_name:
            logger.info(
                "🔍 _has_meaningful_extended_data: Found document info - returning True"
            )
            return True

        logger.warning(
            "🔍 _has_meaningful_extended_data: No meaningful data found - returning False"
        )
        return False

    def _format_date_field(
        self, date_value: Any, include_time: bool = True
    ) -> Dict[str, str]:
        """
        Helper method to format any date field consistently

        Args:
            date_value: Raw date value from CDA or administrative data
            include_time: Whether to include time in formatting

        Returns:
            Dict with formatted and raw date values
        """
        if not date_value:
            return {"formatted": "Unknown", "raw": ""}

        try:
            if include_time:
                formatted = self.date_formatter.format_document_date(date_value)
            else:
                formatted = self.date_formatter.format_birth_date(date_value)

            return {"formatted": formatted, "raw": str(date_value)}
        except Exception as e:
            logger.warning(f"Failed to format date '{date_value}': {e}")
            return {"formatted": str(date_value), "raw": str(date_value)}

    def _get_fallback_header_data(
        self, patient_identity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback header data when processing fails"""
        return {
            "section_type": "patient_header",
            "display_name": patient_identity.get("patient_id", "Patient"),
            "patient_demographics": {
                "birth_date": "Unknown",
                "gender": "Unknown",
                "patient_id": patient_identity.get("patient_id", "Unknown"),
            },
            "document_info": {
                "source_country": "Unknown",
                "cda_type": "L3",
            },
            "styling": {
                "header_class": "bg-secondary",
                "icon": "fas fa-user",
                "card_class": "patient-header-section",
            },
        }

    def _get_fallback_extended_data(self) -> Dict[str, Any]:
        """Fallback extended data when processing fails"""
        return {
            "section_type": "extended_patient",
            "has_meaningful_data": False,
            "styling": {
                "header_class": "bg-secondary",
                "icon": "fas fa-address-book",
                "card_class": "extended-patient-section",
            },
        }

    def _get_fallback_summary_data(self) -> Dict[str, Any]:
        """Fallback summary data when processing fails"""
        return {
            "section_type": "summary_statistics",
            "statistics": [
                {"value": 0, "label": "Total Sections", "color": "text-muted"},
                {"value": 0, "label": "Medical Terms", "color": "text-muted"},
                {"value": 0, "label": "Coded Sections", "color": "text-muted"},
                {"value": "0%", "label": "Terminology Coverage", "color": "text-muted"},
            ],
            "styling": {
                "header_class": "bg-secondary",
                "icon": "fas fa-chart-bar",
                "card_class": "summary-stats-section",
            },
        }

    def _detect_additional_extended_components(
        self, administrative_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Detect additional extended patient components based on XSL structure
        Only include components that have meaningful data
        """
        components = {}

        # Legal Authenticator
        if self._has_legal_authenticator_data(administrative_data):
            components["legal_authenticator"] = {
                "has_data": True,
                "data": administrative_data.get("legal_authenticator", {}),
                "component_template": "extended_patient_legal_auth.html",
                "tab_info": {
                    "id": "legal_auth",
                    "label": "Legal Authenticator",
                    "icon": "fas fa-user-check",
                },
            }

        # Guardian
        if self._has_guardian_data(administrative_data):
            components["guardian"] = {
                "has_data": True,
                "data": administrative_data.get("guardian", {}),
                "component_template": "extended_patient_guardian.html",
                "tab_info": {
                    "id": "guardian",
                    "label": "Guardian",
                    "icon": "fas fa-user-shield",
                },
            }

        # Other Contacts
        if self._has_other_contacts_data(administrative_data):
            components["other_contacts"] = {
                "has_data": True,
                "data": administrative_data.get("other_contacts", {}),
                "component_template": "extended_patient_other_contacts.html",
                "tab_info": {
                    "id": "other_contacts",
                    "label": "Other Contacts",
                    "icon": "fas fa-users",
                },
            }

        # Custodian
        if self._has_custodian_data(administrative_data):
            components["custodian"] = {
                "has_data": True,
                "data": administrative_data.get("custodian", {}),
                "component_template": "extended_patient_custodian.html",
                "tab_info": {
                    "id": "custodian",
                    "label": "Custodian",
                    "icon": "fas fa-building",
                },
            }

        return components

    def _build_extended_navigation_tabs(
        self,
        contact_info: Dict[str, Any],
        healthcare_team: Dict[str, Any],
        document_info: Dict[str, Any],
        additional_components: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Build dynamic navigation tabs based on available data"""
        tabs = []
        first_tab = True

        # Start with Document Info (most concise, comes first)
        tabs.append(
            {
                "id": "document",
                "label": "Document Info",
                "icon": "fas fa-file-medical-alt",
                "count": document_info.get("total_fields", 0),
                "active": first_tab,
            }
        )
        first_tab = False

        # Add dynamic tabs for additional components (Legal Auth, Other Contacts, etc)
        for component_name, component_data in additional_components.items():
            if component_data.get("has_data"):
                tab_info = component_data.get("tab_info", {})
                tab_info.update(
                    {"active": first_tab, "count": component_data.get("item_count", 1)}
                )
                tabs.append(tab_info)
                first_tab = False

        # Then detailed contact information
        tabs.append(
            {
                "id": "contact",
                "label": "Contact Details",
                "icon": "fas fa-address-card",
                "count": contact_info.get("total_items", 0),
                "active": first_tab,
            }
        )
        first_tab = False

        # Finally healthcare team (most detailed)
        tabs.append(
            {
                "id": "healthcare",
                "label": "Healthcare Team",
                "icon": "fas fa-user-md",
                "count": healthcare_team.get("total_members", 0),
                "active": first_tab,
            }
        )
        first_tab = False

        return tabs

    # Helper methods for component detection
    def _has_legal_authenticator_data(self, data: Dict[str, Any]) -> bool:
        """Check if legal authenticator data is present"""
        return bool(
            data.get("legal_authenticator")
            and (
                data["legal_authenticator"].get("name")
                or data["legal_authenticator"].get("organization")
            )
        )

    def _has_guardian_data(self, data: Dict[str, Any]) -> bool:
        """Check if guardian data is present"""
        return bool(data.get("guardian") and data["guardian"].get("name"))

    def _has_other_contacts_data(self, data: Dict[str, Any]) -> bool:
        """Check if other contacts data is present"""
        return bool(data.get("other_contacts") and len(data["other_contacts"]) > 0)

    def _has_custodian_data(self, data: Dict[str, Any]) -> bool:
        """Check if custodian data is present"""
        return bool(data.get("custodian") and data["custodian"].get("name"))
