"""
CDA Header Extractor using lxml

Robust extraction of CDA document header information using lxml with XPath support.
Extracts author, custodian, guardian, participant, and other administrative data
from CDA XML documents.

This module addresses the missing CDAAdministrativeExtractor and provides
comprehensive header extraction for Healthcare Team and Extended Patient Information.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

try:
    from lxml import etree
    LXML_AVAILABLE = True
except ImportError:
    # Fallback to ElementTree if lxml not available
    import xml.etree.ElementTree as etree
    LXML_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class ContactInfo:
    """Contact information structure"""
    telecoms: List[Dict[str, str]]
    addresses: List[Dict[str, str]]


@dataclass
class Person:
    """Person information structure"""
    given_name: str
    family_name: str
    full_name: str
    title: str = ""
    role: str = ""


@dataclass
class Organization:
    """Organization information structure"""
    name: str
    contact_info: ContactInfo
    identifiers: List[Dict[str, str]]


@dataclass
class AuthorInfo:
    """Author information structure"""
    person: Person
    organization: Organization
    contact_info: ContactInfo
    timestamp: str = ""


@dataclass
class AdministrativeData:
    """Complete administrative data structure"""
    author_hcp: Optional[AuthorInfo] = None
    custodian_organization: Optional[Organization] = None
    legal_authenticator: Optional[AuthorInfo] = None
    guardians: List[Dict[str, Any]] = None
    participants: List[Dict[str, Any]] = None
    document_creation_date: str = ""
    document_set_id: str = ""
    document_title: str = ""
    document_title: str = ""


class CDAHeaderExtractor:
    """
    CDA header extractor using lxml for robust XML parsing with XPath support
    
    Extracts administrative data from CDA document headers including:
    - Author information (António Pereira) 
    - Custodian organization (Centro Hospitalar de Lisboa Central)
    - Guardian information (Joaquim Baptista)
    - Participant/emergency contacts (Vitória Silva)
    - Document metadata
    """
    
    def __init__(self):
        """Initialize with CDA namespaces"""
        self.namespaces = {
            'cda': 'urn:hl7-org:v3',
            'pharm': 'urn:hl7-org:pharm',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
        
    def extract_administrative_data(self, cda_xml: str) -> AdministrativeData:
        """
        Extract administrative data from CDA XML content
        
        Args:
            cda_xml: CDA XML content as string
            
        Returns:
            AdministrativeData object with extracted header information
        """
        try:
            # Parse XML
            if LXML_AVAILABLE:
                root = etree.fromstring(cda_xml.encode('utf-8'))
            else:
                root = etree.fromstring(cda_xml)
                
            # Extract each component
            author_hcp = self._extract_author(root)
            custodian_org = self._extract_custodian(root) 
            legal_auth = self._extract_legal_authenticator(root)
            guardians = self._extract_guardian(root)
            participants = self._extract_participants(root)
            
            # Extract document metadata
            doc_date = self._extract_document_date(root)
            doc_id = self._extract_document_id(root)
            doc_title = self._extract_document_title(root)
            
            return AdministrativeData(
                author_hcp=author_hcp,
                custodian_organization=custodian_org,
                legal_authenticator=legal_auth,
                guardians=guardians,
                participants=participants,
                document_creation_date=doc_date,
                document_set_id=doc_id,
                document_title=doc_title
            )
            
        except Exception as e:
            logger.error(f"Error extracting CDA administrative data: {e}")
            return AdministrativeData()
    
    def _extract_author(self, root) -> Optional[AuthorInfo]:
        """Extract author information from CDA document"""
        try:
            # XPath to find author element
            if LXML_AVAILABLE:
                authors = root.xpath('//cda:author', namespaces=self.namespaces)
            else:
                authors = root.findall('.//author', self.namespaces)
            
            if not authors:
                return None
                
            author = authors[0]  # Take first author
            
            # Extract person information
            if LXML_AVAILABLE:
                person_elem = author.xpath('.//cda:assignedPerson', namespaces=self.namespaces)
            else:
                person_elem = author.findall('.//assignedPerson', self.namespaces)
                
            if not person_elem:
                return None
                
            person = person_elem[0]
            
            # Extract name
            if LXML_AVAILABLE:
                name_elem = person.xpath('.//cda:name', namespaces=self.namespaces)
            else:
                name_elem = person.findall('.//name', self.namespaces)
                
            given_name = ""
            family_name = ""
            
            if name_elem:
                name = name_elem[0]
                if LXML_AVAILABLE:
                    given_elems = name.xpath('.//cda:given', namespaces=self.namespaces)
                    family_elems = name.xpath('.//cda:family', namespaces=self.namespaces)
                else:
                    given_elems = name.findall('.//given', self.namespaces)
                    family_elems = name.findall('.//family', self.namespaces)
                    
                if given_elems:
                    given_name = given_elems[0].text or ""
                if family_elems:
                    family_name = family_elems[0].text or ""
            
            full_name = f"{given_name} {family_name}".strip()
            
            # Extract contact information  
            contact_info = self._extract_contact_info(author)
            
            # Extract organization
            if LXML_AVAILABLE:
                org_elems = author.xpath('.//cda:representedOrganization', namespaces=self.namespaces)
            else:
                org_elems = author.findall('.//representedOrganization', self.namespaces)
                
            organization = None
            if org_elems:
                org = org_elems[0]
                org_name = ""
                if LXML_AVAILABLE:
                    name_elems = org.xpath('.//cda:name', namespaces=self.namespaces)
                else:
                    name_elems = org.findall('.//name', self.namespaces)
                    
                if name_elems:
                    org_name = name_elems[0].text or ""
                
                # Try to extract contact info from representedOrganization first
                org_contact = self._extract_contact_info(org)
                
                # If no contact info found in representedOrganization, 
                # use contact info from assignedAuthor level (common pattern in CDA)
                # Note: 'author' variable is the <author> element, contact_info already extracted from it
                if not org_contact.telecoms and not org_contact.addresses:
                    # Use the contact_info already extracted at line 190 from the author element
                    org_contact = contact_info
                
                org_identifiers = self._extract_identifiers(org)
                
                organization = Organization(
                    name=org_name,
                    contact_info=org_contact,
                    identifiers=org_identifiers
                )
            
            # Extract timestamp
            timestamp = ""
            if LXML_AVAILABLE:
                time_elems = author.xpath('.//cda:time', namespaces=self.namespaces)
            else:
                time_elems = author.findall('.//time', self.namespaces)
                
            if time_elems:
                timestamp = time_elems[0].get('value', '')
                
            person_info = Person(
                given_name=given_name,
                family_name=family_name,
                full_name=full_name,
                title="",  # Could extract if needed
                role="Author"
            )
            
            return AuthorInfo(
                person=person_info,
                organization=organization,
                contact_info=contact_info,
                timestamp=timestamp
            )
            
        except Exception as e:
            logger.error(f"Error extracting author: {e}")
            return None
    
    def _extract_custodian(self, root) -> Optional[Organization]:
        """Extract custodian organization from CDA document"""
        try:
            # XPath to find custodian element
            if LXML_AVAILABLE:
                custodians = root.xpath('//cda:custodian//cda:representedCustodianOrganization', namespaces=self.namespaces)
            else:
                custodians = root.findall('.//custodian//{urn:hl7-org:v3}representedCustodianOrganization')
            
            if not custodians:
                return None
                
            custodian = custodians[0]
            
            # Extract organization name
            org_name = ""
            if LXML_AVAILABLE:
                name_elems = custodian.xpath('.//cda:name', namespaces=self.namespaces)
            else:
                name_elems = custodian.findall('.//{urn:hl7-org:v3}name')
                
            if name_elems:
                org_name = name_elems[0].text or ""
            
            # Extract contact information
            contact_info = self._extract_contact_info(custodian)
            identifiers = self._extract_identifiers(custodian)
            
            return Organization(
                name=org_name,
                contact_info=contact_info,
                identifiers=identifiers
            )
            
        except Exception as e:
            logger.error(f"Error extracting custodian: {e}")
            return None
    
    def _extract_legal_authenticator(self, root) -> Optional[AuthorInfo]:
        """Extract legal authenticator from CDA document"""
        try:
            # Find legalAuthenticator element
            if LXML_AVAILABLE:
                auth_elems = root.xpath('//cda:legalAuthenticator', namespaces=self.namespaces)
            else:
                auth_elems = root.findall('.//{urn:hl7-org:v3}legalAuthenticator')
            
            if not auth_elems:
                return None
            
            legal_auth = auth_elems[0]  # Take first legal authenticator
            
            # Extract person information from assignedEntity
            if LXML_AVAILABLE:
                person_elem = legal_auth.xpath('.//cda:assignedPerson', namespaces=self.namespaces)
            else:
                person_elem = legal_auth.findall('.//{urn:hl7-org:v3}assignedPerson')
                
            if not person_elem:
                return None
                
            person = person_elem[0]
            
            # Extract name
            if LXML_AVAILABLE:
                name_elem = person.xpath('.//cda:name', namespaces=self.namespaces)
            else:
                name_elem = person.findall('.//{urn:hl7-org:v3}name')
                
            given_name = ""
            family_name = ""
            
            if name_elem:
                name = name_elem[0]
                if LXML_AVAILABLE:
                    given_elems = name.xpath('.//cda:given', namespaces=self.namespaces)
                    family_elems = name.xpath('.//cda:family', namespaces=self.namespaces)
                else:
                    given_elems = name.findall('.//{urn:hl7-org:v3}given')
                    family_elems = name.findall('.//{urn:hl7-org:v3}family')
                    
                if given_elems:
                    given_name = given_elems[0].text or ""
                if family_elems:
                    family_name = family_elems[0].text or ""
            
            full_name = f"{given_name} {family_name}".strip()
            
            # Extract contact information from legalAuthenticator
            contact_info = self._extract_contact_info(legal_auth)
            
            # Extract organization
            if LXML_AVAILABLE:
                org_elems = legal_auth.xpath('.//cda:representedOrganization', namespaces=self.namespaces)
            else:
                org_elems = legal_auth.findall('.//{urn:hl7-org:v3}representedOrganization')
                
            organization = None
            if org_elems:
                org = org_elems[0]
                org_name = ""
                if LXML_AVAILABLE:
                    name_elems = org.xpath('.//cda:name', namespaces=self.namespaces)
                else:
                    name_elems = org.findall('.//{urn:hl7-org:v3}name')
                    
                if name_elems:
                    org_name = name_elems[0].text or ""
                
                # Try to extract contact info from representedOrganization first
                org_contact = self._extract_contact_info(org)
                
                # If no contact info found in representedOrganization, 
                # use contact info from assignedEntity level (common pattern in CDA)
                if not org_contact.telecoms and not org_contact.addresses:
                    org_contact = contact_info
                
                org_identifiers = self._extract_identifiers(org)
                
                organization = Organization(
                    name=org_name,
                    contact_info=org_contact,
                    identifiers=org_identifiers
                )
            
            # Extract timestamp (authentication time)
            timestamp = ""
            if LXML_AVAILABLE:
                time_elems = legal_auth.xpath('.//cda:time', namespaces=self.namespaces)
            else:
                time_elems = legal_auth.findall('.//{urn:hl7-org:v3}time')
                
            if time_elems:
                timestamp = time_elems[0].get('value', '')
                
            person_info = Person(
                given_name=given_name,
                family_name=family_name,
                full_name=full_name,
                title="",
                role="Legal Authenticator"
            )
            
            return AuthorInfo(
                person=person_info,
                organization=organization,
                contact_info=contact_info,
                timestamp=timestamp
            )
            
        except Exception as e:
            logger.error(f"Error extracting legal authenticator: {e}")
            return None
    
    def _extract_guardian(self, root) -> List[Dict[str, Any]]:
        """Extract guardian information from CDA document"""
        try:
            guardians = []
            
            # Method 1: Traditional guardian elements under patient
            if LXML_AVAILABLE:
                guardian_elems = root.xpath('//cda:patient//cda:guardian', namespaces=self.namespaces)
            else:
                guardian_elems = root.findall('.//{urn:hl7-org:v3}patient//{urn:hl7-org:v3}guardian')
            
            for guardian in guardian_elems:
                guardian_info = self._extract_guardian_info(guardian)
                if guardian_info:
                    guardians.append(guardian_info)
            
            # Method 2: Participants with guardian attributes (typeCode="RESP" and classCode="GUAR")
            if LXML_AVAILABLE:
                participant_guardians = root.xpath('//cda:participant[@typeCode="RESP"]//cda:associatedEntity[@classCode="GUAR"]', namespaces=self.namespaces)
                # Process participant-based guardians
                for entity in participant_guardians:
                    guardian_info = self._extract_guardian_info_from_entity(entity)
                    if guardian_info:
                        guardians.append(guardian_info)
            else:
                # For ElementTree, we need to find participants and check attributes
                participant_elems = root.findall('.//{urn:hl7-org:v3}participant')
                for participant in participant_elems:
                    type_code = participant.get('typeCode', '')
                    if type_code == 'RESP':
                        entity_elems = participant.findall('.//{urn:hl7-org:v3}associatedEntity')
                        for entity in entity_elems:
                            if entity.get('classCode', '') == 'GUAR':
                                guardian_info = self._extract_guardian_info_from_entity(entity)
                                if guardian_info:
                                    guardians.append(guardian_info)
                
            return guardians
            
        except Exception as e:
            logger.error(f"Error extracting guardians: {e}")
            return []
    
    def _extract_guardian_info(self, guardian_elem) -> Optional[Dict[str, Any]]:
        """Extract guardian information from traditional guardian element"""
        try:
            # Extract guardian person name
            if LXML_AVAILABLE:
                person_elems = guardian_elem.xpath('.//cda:guardianPerson', namespaces=self.namespaces)
            else:
                person_elems = guardian_elem.findall('.//{urn:hl7-org:v3}guardianPerson')
            
            if not person_elems:
                return None
                
            person = person_elems[0]
            
            # Extract name
            given_name, family_name = self._extract_person_name(person)
            
            # Extract contact information
            contact_info = self._extract_contact_info(guardian_elem)
            
            # Convert ContactInfo dataclass to dict for template compatibility
            from dataclasses import asdict
            contact_info_dict = asdict(contact_info) if contact_info else {'addresses': [], 'telecoms': []}
            
            return {
                'given_name': given_name,
                'family_name': family_name,
                'full_name': f"{given_name} {family_name}".strip(),
                'role': 'Guardian',
                'relationship_code': 'Guardian',
                'contact_info': contact_info_dict
            }
            
        except Exception as e:
            logger.error(f"Error extracting guardian info: {e}")
            return None
    
    def _extract_guardian_info_from_entity(self, entity_elem) -> Optional[Dict[str, Any]]:
        """Extract guardian information from associatedEntity element"""
        try:
            # Extract associated person name
            if LXML_AVAILABLE:
                person_elems = entity_elem.xpath('.//cda:associatedPerson', namespaces=self.namespaces)
            else:
                person_elems = entity_elem.findall('.//{urn:hl7-org:v3}associatedPerson')
            
            if not person_elems:
                return None
                
            person = person_elems[0]
            
            # Extract name
            given_name, family_name = self._extract_person_name(person)
            
            # Extract contact information
            contact_info = self._extract_contact_info(entity_elem)
            
            # Convert ContactInfo dataclass to dict for template compatibility
            from dataclasses import asdict
            contact_info_dict = asdict(contact_info) if contact_info else {'addresses': [], 'telecoms': []}
            
            return {
                'given_name': given_name,
                'family_name': family_name,
                'full_name': f"{given_name} {family_name}".strip(),
                'role': 'Guardian',
                'relationship_code': 'Guardian',
                'contact_info': contact_info_dict
            }
            
        except Exception as e:
            logger.error(f"Error extracting guardian info from entity: {e}")
            return None
    
    def _extract_person_name(self, person_elem) -> tuple:
        """Extract given and family name from person element"""
        try:
            # Extract name
            if LXML_AVAILABLE:
                name_elems = person_elem.xpath('.//cda:name', namespaces=self.namespaces)
            else:
                name_elems = person_elem.findall('.//{urn:hl7-org:v3}name')
                
            given_name = ""
            family_name = ""
            
            if name_elems:
                name = name_elems[0]
                if LXML_AVAILABLE:
                    given_elems = name.xpath('.//cda:given', namespaces=self.namespaces)
                    family_elems = name.xpath('.//cda:family', namespaces=self.namespaces)
                else:
                    given_elems = name.findall('.//{urn:hl7-org:v3}given')
                    family_elems = name.findall('.//{urn:hl7-org:v3}family')
                
                if given_elems:
                    given_name = given_elems[0].text or ""
                if family_elems:
                    family_name = family_elems[0].text or ""
            
            return given_name, family_name
            
        except Exception as e:
            logger.error(f"Error extracting person name: {e}")
            return "", ""
    
    def _extract_participants(self, root) -> List[Dict[str, Any]]:
        """Extract participant information from CDA document (excluding guardians)"""
        try:
            participants = []
            
            # XPath to find participant elements
            if LXML_AVAILABLE:
                participant_elems = root.xpath('//cda:participant', namespaces=self.namespaces)
            else:
                participant_elems = root.findall('.//{urn:hl7-org:v3}participant')
            
            for participant in participant_elems:
                # Check if this participant is actually a guardian
                type_code = participant.get('typeCode', '')
                
                # Look for associated entity class code
                if LXML_AVAILABLE:
                    entity_elems = participant.xpath('.//cda:associatedEntity', namespaces=self.namespaces)
                else:
                    entity_elems = participant.findall('.//{urn:hl7-org:v3}associatedEntity')
                
                class_code = ''
                if entity_elems:
                    class_code = entity_elems[0].get('classCode', '')
                
                # Skip guardians (they will be handled separately)
                if type_code == 'RESP' and class_code == 'GUAR':
                    continue  # This is a guardian, not a regular participant
                
                # Extract regular participant information
                participant_info = self._extract_participant_info(participant)
                if participant_info:
                    participants.append(participant_info)
                    
            return participants
            
        except Exception as e:
            logger.error(f"Error extracting participants: {e}")
            return []
    
    def _extract_participant_info(self, participant) -> Optional[Dict[str, Any]]:
        """Extract individual participant information"""
        try:
            # Extract person name
            if LXML_AVAILABLE:
                person_elems = participant.xpath('.//cda:associatedPerson', namespaces=self.namespaces)
            else:
                person_elems = participant.findall('.//{urn:hl7-org:v3}associatedPerson')
            
            if not person_elems:
                return None
                
            person = person_elems[0]
            
            # Extract name
            if LXML_AVAILABLE:
                name_elems = person.xpath('.//cda:name', namespaces=self.namespaces)
            else:
                name_elems = person.findall('.//{urn:hl7-org:v3}name')
                
            given_name = ""
            family_name = ""
            
            if name_elems:
                name = name_elems[0]
                if LXML_AVAILABLE:
                    given_elems = name.xpath('.//cda:given', namespaces=self.namespaces)
                    family_elems = name.xpath('.//cda:family', namespaces=self.namespaces)
                else:
                    given_elems = name.findall('.//{urn:hl7-org:v3}given')
                    family_elems = name.findall('.//{urn:hl7-org:v3}family')
                    
                if given_elems:
                    given_name = given_elems[0].text or ""
                if family_elems:
                    family_name = family_elems[0].text or ""
            
            # Extract role/relationship
            role = ""
            if LXML_AVAILABLE:
                entity_elems = participant.xpath('.//cda:associatedEntity', namespaces=self.namespaces)
            else:
                entity_elems = participant.findall('.//{urn:hl7-org:v3}associatedEntity')
                
            if entity_elems:
                entity = entity_elems[0]
                if LXML_AVAILABLE:
                    code_elems = entity.xpath('.//cda:code', namespaces=self.namespaces)
                else:
                    code_elems = entity.findall('.//{urn:hl7-org:v3}code')
                    
                if code_elems:
                    role = code_elems[0].get('code', '')
            
            # Extract contact information
            contact_info = self._extract_contact_info(participant)
            
            # Convert ContactInfo dataclass to dict for template compatibility
            from dataclasses import asdict
            contact_info_dict = asdict(contact_info) if contact_info else {'addresses': [], 'telecoms': []}
            
            return {
                'given_name': given_name,
                'family_name': family_name,
                'full_name': f"{given_name} {family_name}".strip(),
                'role': role,
                'relationship_code': role,  # Add for template compatibility
                'contact_info': contact_info_dict
            }
            
        except Exception as e:
            logger.error(f"Error extracting participant info: {e}")
            return None
    
    def _extract_contact_info(self, element) -> ContactInfo:
        """Extract contact information (addresses and telecoms) from element"""
        telecoms = []
        addresses = []
        
        try:
            # Extract telecoms
            if LXML_AVAILABLE:
                telecom_elems = element.xpath('.//cda:telecom', namespaces=self.namespaces)
            else:
                telecom_elems = element.findall('.//{urn:hl7-org:v3}telecom')
            
            for telecom in telecom_elems:
                value = telecom.get('value', '')
                use = telecom.get('use', '')
                if value:
                    telecoms.append({'value': value, 'use': use})
            
            # Extract addresses
            if LXML_AVAILABLE:
                addr_elems = element.xpath('.//cda:addr', namespaces=self.namespaces)
            else:
                addr_elems = element.findall('.//{urn:hl7-org:v3}addr')
            
            for addr in addr_elems:
                address_info = {}
                
                # Extract address components
                if LXML_AVAILABLE:
                    street_elems = addr.xpath('.//cda:streetAddressLine', namespaces=self.namespaces)
                    city_elems = addr.xpath('.//cda:city', namespaces=self.namespaces)
                    postal_elems = addr.xpath('.//cda:postalCode', namespaces=self.namespaces)
                    country_elems = addr.xpath('.//cda:country', namespaces=self.namespaces)
                else:
                    street_elems = addr.findall('.//{urn:hl7-org:v3}streetAddressLine')
                    city_elems = addr.findall('.//{urn:hl7-org:v3}city')
                    postal_elems = addr.findall('.//{urn:hl7-org:v3}postalCode')
                    country_elems = addr.findall('.//{urn:hl7-org:v3}country')
                
                if street_elems:
                    address_info['street'] = street_elems[0].text or ""
                if city_elems:
                    address_info['city'] = city_elems[0].text or ""
                if postal_elems:
                    address_info['postal_code'] = postal_elems[0].text or ""
                if country_elems:
                    address_info['country'] = country_elems[0].text or ""
                    
                if address_info:
                    addresses.append(address_info)
                    
        except Exception as e:
            logger.error(f"Error extracting contact info: {e}")
        
        return ContactInfo(telecoms=telecoms, addresses=addresses)
    
    def _extract_identifiers(self, element) -> List[Dict[str, str]]:
        """Extract identifier information from element"""
        identifiers = []
        
        try:
            if LXML_AVAILABLE:
                id_elems = element.xpath('.//cda:id', namespaces=self.namespaces)
            else:
                id_elems = element.findall('.//{urn:hl7-org:v3}id')
            
            for id_elem in id_elems:
                root = id_elem.get('root', '')
                extension = id_elem.get('extension', '')
                if root or extension:
                    identifiers.append({'root': root, 'extension': extension})
                    
        except Exception as e:
            logger.error(f"Error extracting identifiers: {e}")
            
        return identifiers
    
    def _extract_document_date(self, root) -> str:
        """Extract document creation date"""
        try:
            if LXML_AVAILABLE:
                time_elems = root.xpath('//cda:effectiveTime', namespaces=self.namespaces)
            else:
                time_elems = root.findall('.//{urn:hl7-org:v3}effectiveTime')
            
            if time_elems:
                return time_elems[0].get('value', '')
                
        except Exception as e:
            logger.error(f"Error extracting document date: {e}")
            
        return ""
    
    def _extract_document_id(self, root) -> str:
        """Extract document ID"""
        try:
            if LXML_AVAILABLE:
                id_elems = root.xpath('//cda:id', namespaces=self.namespaces)
            else:
                id_elems = root.findall('.//{urn:hl7-org:v3}id')
            
            if id_elems:
                return id_elems[0].get('extension', '')
                
        except Exception as e:
            logger.error(f"Error extracting document ID: {e}")
            
        return ""
    
    def _extract_document_title(self, root) -> str:
        """Extract document title"""
        try:
            if LXML_AVAILABLE:
                title_elems = root.xpath('//cda:title', namespaces=self.namespaces)
            else:
                title_elems = root.findall('.//{urn:hl7-org:v3}title')
            
            if title_elems and title_elems[0].text:
                return title_elems[0].text
                
        except Exception as e:
            logger.error(f"Error extracting document title: {e}")
            
        return ""