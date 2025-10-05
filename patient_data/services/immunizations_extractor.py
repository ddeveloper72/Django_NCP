import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)

@dataclass
class ImmunizationEntry:
    """Structured data model for Immunization/Vaccination entries"""
    vaccination_name: str
    brand_name: str = ""
    vaccination_date: str = ""
    agent: str = ""
    marketing_authorization_holder: str = ""
    dose_number: str = ""
    batch_lot_number: str = ""
    administering_center: str = ""
    health_professional_name: str = ""
    country_of_vaccination: str = ""
    annotations: str = ""
    status: str = ""
    
    # Clinical codes for CTS integration
    vaccination_code: str = ""
    vaccination_code_system: str = ""
    agent_code: str = ""
    agent_code_system: str = ""

class ImmunizationsExtractor:
    """Extracts Immunizations/Vaccinations data from CDA documents"""
    
    def __init__(self):
        # Define XML namespace mappings for CDA parsing
        self.namespaces = {
            'hl7': 'urn:hl7-org:v3',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
    
    def extract_immunizations(self, cda_content: str) -> List[ImmunizationEntry]:
        """
        Extract Immunizations entries from CDA XML
        
        Args:
            cda_content (str): Raw CDA XML content
            
        Returns:
            List[ImmunizationEntry]: Structured immunization data
        """
        try:
            root = ET.fromstring(cda_content)
            
            # Find the Immunizations section using LOINC code
            sections = root.findall(".//hl7:section", self.namespaces)
            section = None
            for sect in sections:
                code_element = sect.find("hl7:code", self.namespaces)
                if code_element is not None and code_element.get('code') == '11369-6':
                    section = sect
                    break
            
            if section is None:
                logger.info("No Immunizations section found")
                return []
            
            entries = []
            
            # Extract entries from the section
            for entry in section.findall(".//hl7:entry", self.namespaces):
                immunization_entry = self._extract_single_entry(entry)
                if immunization_entry:
                    entries.append(immunization_entry)
            
            logger.info(f"Successfully extracted {len(entries)} Immunization entries")
            return entries
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in Immunizations extraction: {e}")
            return []
    
    def _extract_single_entry(self, entry_element) -> Optional[ImmunizationEntry]:
        """Extract data from a single immunization entry element"""
        try:
            # Find the substanceAdministration element
            substance_admin = entry_element.find(".//hl7:substanceAdministration", self.namespaces)
            if substance_admin is None:
                return None
            
            # Extract basic fields
            vaccination_name = self._get_vaccination_name(substance_admin)
            if not vaccination_name:
                return None
            
            brand_name = self._get_brand_name(substance_admin)
            vaccination_date = self._get_vaccination_date(substance_admin)
            status = self._get_status(substance_admin)
            
            # Extract manufacturer information
            marketing_auth_holder = self._get_manufacturer_name(substance_admin)
            batch_lot_number = self._get_lot_number(substance_admin)
            
            # Extract performer (health professional and center) information
            health_professional_name = self._get_health_professional_name(substance_admin)
            administering_center = self._get_administering_center(substance_admin)
            country_of_vaccination = self._get_country_of_vaccination(substance_admin)
            
            # Extract agent information
            agent, agent_code, agent_code_system = self._get_agent_information(substance_admin)
            
            # Extract dose number
            dose_number = self._get_dose_number(substance_admin)
            
            # Extract vaccination codes
            vaccination_code, vaccination_code_system = self._get_vaccination_codes(substance_admin)
            
            return ImmunizationEntry(
                vaccination_name=vaccination_name,
                brand_name=brand_name,
                vaccination_date=vaccination_date,
                agent=agent,
                marketing_authorization_holder=marketing_auth_holder,
                dose_number=dose_number,
                batch_lot_number=batch_lot_number,
                administering_center=administering_center,
                health_professional_name=health_professional_name,
                country_of_vaccination=country_of_vaccination,
                annotations="",  # Not found in current CDA structure
                status=status,
                vaccination_code=vaccination_code,
                vaccination_code_system=vaccination_code_system,
                agent_code=agent_code,
                agent_code_system=agent_code_system
            )
            
        except Exception as e:
            logger.warning(f"Failed to extract single immunization entry: {e}")
            return None
    
    def _get_vaccination_name(self, substance_admin) -> str:
        """Extract vaccination name from originalText reference"""
        try:
            # Look for the originalText reference in manufacturedMaterial
            original_text = substance_admin.find(
                ".//hl7:manufacturedMaterial/hl7:code/hl7:originalText", 
                self.namespaces
            )
            if original_text is not None:
                reference = original_text.find("hl7:reference", self.namespaces)
                if reference is not None:
                    ref_value = reference.get('value', '')
                    if ref_value.startswith('#'):
                        # This would typically be resolved from the text section
                        # For now, we'll use a fallback approach
                        pass
            
            # Fallback: try to get from the material name or displayName
            material_name = substance_admin.find(
                ".//hl7:manufacturedMaterial/hl7:name", 
                self.namespaces
            )
            if material_name is not None and material_name.text:
                # Extract just the vaccination type from brand name
                brand_text = material_name.text.strip()
                # Try to extract vaccination type from brand name
                if "Hepatitis B" in brand_text:
                    return "Hepatitis B virus vaccine"
                elif "Tetravac" in brand_text:
                    return "Diphtheria + tetanus + pertussis + poliomyelitis vaccine"
                elif "Hiberix" in brand_text:
                    return "Haemophilus influenzae Type b vaccine"
                elif "Cervarix" in brand_text:
                    return "Human papillomavirus vaccine"
                return brand_text
                
            return ""
        except Exception as e:
            logger.warning(f"Error extracting vaccination name: {e}")
            return ""
    
    def _get_brand_name(self, substance_admin) -> str:
        """Extract brand name from manufacturedMaterial"""
        try:
            material_name = substance_admin.find(
                ".//hl7:manufacturedMaterial/hl7:name", 
                self.namespaces
            )
            return material_name.text.strip() if material_name is not None and material_name.text else ""
        except Exception:
            return ""
    
    def _get_vaccination_date(self, substance_admin) -> str:
        """Extract vaccination date from effectiveTime"""
        try:
            effective_time = substance_admin.find("hl7:effectiveTime", self.namespaces)
            if effective_time is not None:
                date_value = effective_time.get('value', '')
                if date_value and date_value != "NA":
                    # Format date from YYYYMMDD to YYYY-MM-DD
                    if len(date_value) >= 8:
                        return f"{date_value[:4]}-{date_value[4:6]}-{date_value[6:8]}"
            return ""
        except Exception:
            return ""
    
    def _get_status(self, substance_admin) -> str:
        """Extract status from statusCode"""
        try:
            status_code = substance_admin.find("hl7:statusCode", self.namespaces)
            if status_code is not None:
                return status_code.get('code', '')
            return ""
        except Exception:
            return ""
    
    def _get_manufacturer_name(self, substance_admin) -> str:
        """Extract manufacturer name"""
        try:
            manufacturer = substance_admin.find(
                ".//hl7:manufacturerOrganization/hl7:name", 
                self.namespaces
            )
            if manufacturer is not None and manufacturer.text:
                return manufacturer.text.strip()
            return ""
        except Exception:
            return ""
    
    def _get_lot_number(self, substance_admin) -> str:
        """Extract lot/batch number"""
        try:
            lot_number = substance_admin.find(
                ".//hl7:manufacturedMaterial/hl7:lotNumberText", 
                self.namespaces
            )
            return lot_number.text.strip() if lot_number is not None and lot_number.text else ""
        except Exception:
            return ""
    
    def _get_health_professional_name(self, substance_admin) -> str:
        """Extract health professional name"""
        try:
            performer = substance_admin.find(".//hl7:performer", self.namespaces)
            if performer is not None:
                family_name = performer.find(
                    ".//hl7:assignedPerson/hl7:name/hl7:family", 
                    self.namespaces
                )
                given_name = performer.find(
                    ".//hl7:assignedPerson/hl7:name/hl7:given", 
                    self.namespaces
                )
                
                if family_name is not None and given_name is not None:
                    family = family_name.text.strip() if family_name.text else ""
                    given = given_name.text.strip() if given_name.text else ""
                    return f"{given} {family}".strip()
            return ""
        except Exception:
            return ""
    
    def _get_administering_center(self, substance_admin) -> str:
        """Extract administering center name"""
        try:
            org_name = substance_admin.find(
                ".//hl7:performer//hl7:representedOrganization/hl7:name", 
                self.namespaces
            )
            return org_name.text.strip() if org_name is not None and org_name.text else ""
        except Exception:
            return ""
    
    def _get_country_of_vaccination(self, substance_admin) -> str:
        """Extract country of vaccination"""
        try:
            country = substance_admin.find(
                ".//hl7:performer//hl7:representedOrganization/hl7:addr/hl7:country", 
                self.namespaces
            )
            return country.text.strip() if country is not None and country.text else ""
        except Exception:
            return ""
    
    def _get_agent_information(self, substance_admin) -> tuple:
        """Extract agent information from participant"""
        try:
            participant = substance_admin.find(".//hl7:participant", self.namespaces)
            if participant is not None:
                code_element = participant.find(".//hl7:code", self.namespaces)
                if code_element is not None:
                    agent_name = code_element.get('displayName', '')
                    agent_code = code_element.get('code', '')
                    agent_code_system = code_element.get('codeSystem', '')
                    return agent_name, agent_code, agent_code_system
            return "", "", ""
        except Exception:
            return "", "", ""
    
    def _get_dose_number(self, substance_admin) -> str:
        """Extract dose number from entryRelationship"""
        try:
            # Find entryRelationship with observation containing dose number code
            entry_relations = substance_admin.findall(".//hl7:entryRelationship", self.namespaces)
            for entry_relation in entry_relations:
                observation = entry_relation.find("hl7:observation", self.namespaces)
                if observation is not None:
                    code_element = observation.find("hl7:code", self.namespaces)
                    if code_element is not None and code_element.get('code') == '30973-2':
                        value_element = observation.find("hl7:value", self.namespaces)
                        if value_element is not None:
                            return str(value_element.get('value', ''))
            return ""
        except Exception:
            return ""
    
    def _get_vaccination_codes(self, substance_admin) -> tuple:
        """Extract vaccination codes from manufacturedMaterial"""
        try:
            code_element = substance_admin.find(
                ".//hl7:manufacturedMaterial/hl7:code", 
                self.namespaces
            )
            if code_element is not None:
                code = code_element.get('code', '')
                code_system = code_element.get('codeSystem', '')
                return code, code_system
            return "", ""
        except Exception:
            return "", ""