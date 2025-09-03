#!/usr/bin/env python3
"""
Country-Specific CDA Mapping Service
Handles member state variations in CDA implementation
"""

import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class CountrySpecificCDAMapper:
    """
    Handles country-specific CDA variations while maintaining base compatibility
    """

    def __init__(self):
        self.country_variations = {
            "MT": {  # Malta
                "allergies_section_codes": ["48765-2", "10155-0"],
                "allergy_xpath_variations": [
                    ".//hl7:act/hl7:entryRelationship/hl7:observation/hl7:participant/hl7:participantRole/hl7:playingEntity/hl7:code/@displayName",
                    ".//hl7:observation/hl7:participant/hl7:participantRole/hl7:playingEntity/hl7:code/@displayName",
                    ".//hl7:observation[hl7:code/@code='609328004']/hl7:participant/hl7:participantRole/hl7:playingEntity/hl7:code/@displayName",
                ],
                "medication_section_codes": ["10160-0", "29549-3"],
                "medication_xpath_variations": [
                    ".//hl7:substanceAdministration/hl7:consumable/hl7:manufacturedProduct/hl7:manufacturedMaterial/hl7:name/@displayName",
                    ".//hl7:supply/hl7:product/hl7:manufacturedProduct/hl7:manufacturedMaterial/hl7:name",
                    ".//hl7:observation/hl7:value/@displayName",
                ],
                "problem_section_codes": ["11450-4", "46240-8"],
                "problem_xpath_variations": [
                    ".//hl7:observation[hl7:code/@code='ASSERTION']/hl7:value/@displayName",
                    ".//hl7:act/hl7:entryRelationship/hl7:observation/hl7:value/@displayName",
                ],
            },
            "PT": {  # Portugal
                "allergies_section_codes": ["48765-2"],
                "allergy_xpath_variations": [
                    ".//hl7:observation/hl7:participant/hl7:participantRole/hl7:playingEntity/hl7:name",
                    ".//hl7:observation/hl7:value/@displayName",
                ],
                "medication_section_codes": ["10160-0"],
                "medication_xpath_variations": [
                    ".//hl7:substanceAdministration/hl7:consumable/hl7:manufacturedProduct/hl7:manufacturedMaterial/hl7:name",
                    ".//hl7:supply/hl7:product/hl7:manufacturedProduct/hl7:manufacturedMaterial/hl7:name/@displayName",
                ],
            },
            "IT": {  # Italy
                "allergies_section_codes": ["48765-2"],
                "allergy_xpath_variations": [
                    ".//hl7:observation/hl7:participant/hl7:participantRole/hl7:playingEntity/hl7:name",
                    ".//hl7:act/hl7:entryRelationship/hl7:observation/hl7:participant/hl7:participantRole/hl7:playingEntity/hl7:name",
                ],
            },
        }

    def extract_clinical_data(
        self, cda_content: str, country_code: str
    ) -> Dict[str, List]:
        """
        Extract clinical data using country-specific patterns
        """
        try:
            root = ET.fromstring(cda_content)
            namespaces = {
                "hl7": "urn:hl7-org:v3",
                "pharm": "urn:hl7-org:pharm",
                "xsi": "http://www.w3.org/2001/XMLSchema-instance",
            }

            country_config = self.country_variations.get(country_code, {})
            logger.info(
                f"Using country config for {country_code}: {bool(country_config)}"
            )

            results = {"allergies": [], "medications": [], "problems": []}

            # Extract allergies with country-specific patterns
            allergies = self._extract_allergies(root, namespaces, country_config)
            if allergies:
                results["allergies"] = allergies
                logger.info(
                    f"Extracted {len(allergies)} allergies using {country_code} patterns"
                )

            # Extract medications
            medications = self._extract_medications(root, namespaces, country_config)
            if medications:
                results["medications"] = medications
                logger.info(
                    f"Extracted {len(medications)} medications using {country_code} patterns"
                )

            # Extract problems
            problems = self._extract_problems(root, namespaces, country_config)
            if problems:
                results["problems"] = problems
                logger.info(
                    f"Extracted {len(problems)} problems using {country_code} patterns"
                )

            logger.info(
                f"Total extraction results for {country_code}: allergies={len(allergies)}, medications={len(medications)}, problems={len(problems)}"
            )
            return results

        except Exception as e:
            logger.error(f"Error extracting clinical data for {country_code}: {e}")
            return {"allergies": [], "medications": [], "problems": []}

    def _extract_allergies(
        self, root: ET.Element, namespaces: Dict, country_config: Dict
    ) -> List[Dict]:
        """Extract allergies using country-specific patterns"""
        allergies = []

        # Get country-specific section codes
        section_codes = country_config.get("allergies_section_codes", ["48765-2"])
        logger.info(f"Looking for allergy sections with codes: {section_codes}")

        for section_code in section_codes:
            # Find sections with this code
            sections = root.findall(
                f".//hl7:section[hl7:code/@code='{section_code}']", namespaces
            )
            logger.info(f"Found {len(sections)} sections with code {section_code}")

            for section in sections:
                # Malta-specific pattern: entry > act > entryRelationship > observation
                entries = section.findall(".//hl7:entry", namespaces)
                logger.info(f"Found {len(entries)} entries in allergy section")

                for entry in entries:
                    # Look for the specific Malta structure: entry > act
                    acts = entry.findall("hl7:act", namespaces)
                    logger.info(f"Found {len(acts)} acts in entry")

                    for act in acts:
                        # Check if this is an allergy act (CONC code)
                        act_code = act.find("hl7:code", namespaces)
                        if act_code is not None and act_code.get("code") == "CONC":
                            logger.info(f"Found allergy act with CONC code")

                            allergy_info = {}

                            # Get effective time from act
                            time_elem = act.find(
                                ".//hl7:effectiveTime/hl7:low", namespaces
                            )
                            if time_elem is not None:
                                allergy_info["date"] = time_elem.get("value", "")
                                logger.info(
                                    f"Found allergy date: {allergy_info['date']}"
                                )

                            # Navigate: act > entryRelationship > observation
                            observations = act.findall(
                                "hl7:entryRelationship/hl7:observation", namespaces
                            )
                            logger.info(
                                f"Found {len(observations)} observations in act"
                            )

                            for obs in observations:
                                # Get allergy type from observation code (should be "609328004" for Allergic disposition)
                                obs_code = obs.find("hl7:code", namespaces)
                                if obs_code is not None:
                                    allergy_info["type"] = obs_code.get(
                                        "displayName", "Allergic disposition"
                                    )
                                    allergy_info["type_code"] = obs_code.get(
                                        "code", "609328004"
                                    )
                                    logger.info(
                                        f"Found allergy type: {allergy_info['type']} ({allergy_info['type_code']})"
                                    )

                                # Get substance from: observation > participant > participantRole > playingEntity > code
                                participants = obs.findall(
                                    "hl7:participant", namespaces
                                )
                                logger.info(f"Found {len(participants)} participants")

                                for participant in participants:
                                    # Check if this is a causative substance participant (typeCode="CSM")
                                    if participant.get("typeCode") == "CSM":
                                        logger.info(
                                            "Found causative substance participant (CSM)"
                                        )

                                        playing_entities = participant.findall(
                                            "hl7:participantRole/hl7:playingEntity",
                                            namespaces,
                                        )
                                        logger.info(
                                            f"Found {len(playing_entities)} playing entities"
                                        )

                                        for entity in playing_entities:
                                            substance_code = entity.find(
                                                "hl7:code", namespaces
                                            )
                                            if substance_code is not None:
                                                allergy_info["substance"] = (
                                                    substance_code.get(
                                                        "displayName",
                                                        "Unknown substance",
                                                    )
                                                )
                                                allergy_info["substance_code"] = (
                                                    substance_code.get("code", "")
                                                )
                                                allergy_info["code_system"] = (
                                                    substance_code.get("codeSystem", "")
                                                )
                                                allergy_info["code_system_name"] = (
                                                    substance_code.get(
                                                        "codeSystemName", ""
                                                    )
                                                )
                                                logger.info(
                                                    f"Found substance: {allergy_info['substance']} (code: {allergy_info['substance_code']}, system: {allergy_info['code_system_name']})"
                                                )

                            # Create allergy entry if we found substance information
                            if allergy_info.get("substance"):
                                logger.info(f"Creating allergy entry: {allergy_info}")
                                # Format for table display - use standard field names expected by the processor
                                formatted_allergy = {
                                    "data": {
                                        "type_display": allergy_info.get(
                                            "type", "Allergy"
                                        ),
                                        "type_code": allergy_info.get(
                                            "type_code", "609328004"
                                        ),
                                        "agent_display": allergy_info.get(
                                            "substance", "Unknown substance"
                                        ),
                                        "agent_code": allergy_info.get(
                                            "substance_code", ""
                                        ),
                                        "manifestation_display": "Not specified",
                                        "severity": "unknown",
                                        "status": "active",
                                        "date": allergy_info.get("date", ""),
                                        "code_system": allergy_info.get(
                                            "code_system", ""
                                        ),
                                        "code_system_name": allergy_info.get(
                                            "code_system_name", ""
                                        ),
                                    }
                                }
                                allergies.append(formatted_allergy)
                                logger.info(
                                    f"Added allergy: {allergy_info['substance']}"
                                )
                            else:
                                logger.warning(
                                    f"No substance found for allergy act, skipping entry"
                                )

        logger.info(f"Total allergies extracted: {len(allergies)}")

        # DEBUG OUTPUT to help with troubleshooting
        print(f"\n🔍 MALTA ALLERGY EXTRACTION DEBUG:")
        print(f"   Total allergies found: {len(allergies)}")
        if allergies:
            for i, allergy in enumerate(allergies[:2]):
                print(
                    f"   Allergy {i+1}: {allergy['data']['agent_display']} ({allergy['data']['type_display']})"
                )
        else:
            print("   ❌ No allergies extracted")

        return allergies

    def _extract_medications(
        self, root: ET.Element, namespaces: Dict, country_config: Dict
    ) -> List[Dict]:
        """Extract medications using country-specific patterns"""
        medications = []

        section_codes = country_config.get("medication_section_codes", ["10160-0"])

        for section_code in section_codes:
            sections = root.findall(
                f".//hl7:section[hl7:code/@code='{section_code}']", namespaces
            )

            for section in sections:
                # Malta-specific: Look for substanceAdministration entries
                substance_admins = section.findall(
                    ".//hl7:substanceAdministration", namespaces
                )
                for sa in substance_admins:
                    med_info = {}

                    # Get medication info from pharm:ingredientSubstance > pharm:code
                    ingredient_substances = sa.findall(
                        ".//pharm:ingredientSubstance", namespaces
                    )
                    for ingredient in ingredient_substances:
                        pharm_codes = ingredient.findall("pharm:code", namespaces)
                        for pharm_code in pharm_codes:
                            # Generic name from main code
                            med_info["generic_name"] = pharm_code.get(
                                "displayName", "Unknown medication"
                            )
                            med_info["code"] = pharm_code.get("code", "")
                            med_info["code_system"] = pharm_code.get("codeSystem", "")

                            # Brand name from pharm:translation
                            translations = pharm_code.findall(
                                "pharm:translation", namespaces
                            )
                            for trans in translations:
                                brand_name = trans.get("displayName", "")
                                if brand_name:
                                    med_info["brand_name"] = brand_name

                    # Get route of administration
                    route_elem = sa.find("hl7:routeCode", namespaces)
                    if route_elem is not None:
                        med_info["route"] = route_elem.get(
                            "displayName", "Unknown route"
                        )

                    # Get effective time - look for different patterns
                    time_elem = sa.find(".//hl7:effectiveTime/hl7:low", namespaces)
                    if time_elem is not None:
                        med_info["start_date"] = time_elem.get("value", "")

                    # Get end time
                    end_time_elem = sa.find(".//hl7:effectiveTime/hl7:high", namespaces)
                    if (
                        end_time_elem is not None
                        and end_time_elem.get("nullFlavor") != "UNK"
                    ):
                        med_info["end_date"] = end_time_elem.get("value", "")

                    if med_info.get("generic_name") or med_info.get("brand_name"):
                        # Format for table display - use standard field names expected by the processor
                        display_name = med_info.get(
                            "brand_name",
                            med_info.get("generic_name", "Unknown medication"),
                        )
                        formatted_med = {
                            "data": {
                                "medication_display": display_name,
                                "medication_code": med_info.get("code", ""),
                                "ingredient_display": med_info.get("generic_name", ""),
                                "ingredient_code": med_info.get("code", ""),
                                "dosage": "Not specified",
                                "posology": med_info.get("route", "Not specified"),
                                "status": "active",
                                "date": med_info.get("start_date", ""),
                                "code_system": med_info.get("code_system", ""),
                            }
                        }
                        medications.append(formatted_med)

    def _extract_medications(
        self, root: ET.Element, namespaces: Dict, country_config: Dict
    ) -> List[Dict]:
        """Extract medications using country-specific patterns"""
        medications = []

        section_codes = country_config.get("medication_section_codes", ["10160-0"])

        for section_code in section_codes:
            sections = root.findall(
                f".//hl7:section[hl7:code/@code='{section_code}']", namespaces
            )

            for section in sections:
                # Malta-specific: Look for substanceAdministration entries
                substance_admins = section.findall(
                    ".//hl7:substanceAdministration", namespaces
                )
                for sa in substance_admins:
                    med_info = {}

                    # Get medication info from pharm:ingredientSubstance > pharm:code
                    ingredient_substances = sa.findall(
                        ".//pharm:ingredientSubstance", namespaces
                    )
                    for ingredient in ingredient_substances:
                        pharm_codes = ingredient.findall("pharm:code", namespaces)
                        for pharm_code in pharm_codes:
                            # Generic name from main code
                            med_info["generic_name"] = pharm_code.get(
                                "displayName", "Unknown medication"
                            )
                            med_info["code"] = pharm_code.get("code", "")
                            med_info["code_system"] = pharm_code.get("codeSystem", "")

                            # Brand name from pharm:translation
                            translations = pharm_code.findall(
                                "pharm:translation", namespaces
                            )
                            for trans in translations:
                                brand_name = trans.get("displayName", "")
                                if brand_name:
                                    med_info["brand_name"] = brand_name

                    # Get route of administration
                    route_elem = sa.find("hl7:routeCode", namespaces)
                    if route_elem is not None:
                        med_info["route"] = route_elem.get(
                            "displayName", "Unknown route"
                        )

                    # Get effective time - look for different patterns
                    time_elem = sa.find(".//hl7:effectiveTime/hl7:low", namespaces)
                    if time_elem is not None:
                        med_info["start_date"] = time_elem.get("value", "")

                    # Get end time
                    end_time_elem = sa.find(".//hl7:effectiveTime/hl7:high", namespaces)
                    if (
                        end_time_elem is not None
                        and end_time_elem.get("nullFlavor") != "UNK"
                    ):
                        med_info["end_date"] = end_time_elem.get("value", "")

                    if med_info.get("generic_name") or med_info.get("brand_name"):
                        # Format for table display - use standard field names expected by the processor
                        display_name = med_info.get(
                            "brand_name",
                            med_info.get("generic_name", "Unknown medication"),
                        )
                        formatted_med = {
                            "data": {
                                "medication_display": display_name,
                                "medication_code": med_info.get("code", ""),
                                "ingredient_display": med_info.get("generic_name", ""),
                                "ingredient_code": med_info.get("code", ""),
                                "dosage": "Not specified",
                                "posology": med_info.get("route", "Not specified"),
                                "status": "active",
                                "date": med_info.get("start_date", ""),
                                "code_system": med_info.get("code_system", ""),
                            }
                        }
                        medications.append(formatted_med)

        return medications

    def _extract_problems(
        self, root: ET.Element, namespaces: Dict, country_config: Dict
    ) -> List[Dict]:
        """Extract problems using country-specific patterns"""
        problems = []

        section_codes = country_config.get("problem_section_codes", ["11450-4"])

        for section_code in section_codes:
            sections = root.findall(
                f".//hl7:section[hl7:code/@code='{section_code}']", namespaces
            )

            for section in sections:
                # Malta-specific: act > entryRelationship > observation > value
                acts = section.findall(".//hl7:act", namespaces)
                for act in acts:
                    problem_info = {}

                    # Get effective time from act
                    time_elem = act.find(".//hl7:effectiveTime/hl7:low", namespaces)
                    if time_elem is not None:
                        problem_info["date"] = time_elem.get("value", "")

                    # Navigate through Malta-specific structure
                    observations = act.findall(
                        ".//hl7:entryRelationship/hl7:observation", namespaces
                    )
                    for obs in observations:
                        # Get problem description from value element
                        value_elem = obs.find("hl7:value", namespaces)
                        if value_elem is not None:
                            problem_info["description"] = value_elem.get(
                                "displayName", "Unknown problem"
                            )
                            problem_info["code"] = value_elem.get("code", "")
                            problem_info["system"] = value_elem.get("codeSystem", "")

                        # Also get problem type from observation code if available
                        obs_code = obs.find("hl7:code", namespaces)
                        if obs_code is not None and not problem_info.get("description"):
                            problem_info["description"] = obs_code.get(
                                "displayName", "Unknown problem"
                            )

                    if problem_info.get("description"):
                        # Format for table display - use standard field names expected by the processor
                        formatted_problem = {
                            "data": {
                                "condition_display": problem_info.get(
                                    "description", "Unknown problem"
                                ),
                                "condition_code": problem_info.get("code", ""),
                                "agent_display": problem_info.get(
                                    "description", "Unknown problem"
                                ),  # Fallback for display compatibility
                                "agent_code": problem_info.get("code", ""),
                                "value": problem_info.get(
                                    "description", "Unknown problem"
                                ),
                                "status": "active",
                                "onset_date": problem_info.get("date", ""),
                                "date": problem_info.get("date", ""),
                                "severity": "unknown",
                                "priority": "Normal",
                                "code_system": problem_info.get("system", ""),
                            }
                        }
                        problems.append(formatted_problem)

        return problems


# Test function
def test_country_specific_extraction():
    """Test the country-specific extraction with sample data"""
    mapper = CountrySpecificCDAMapper()

    # Sample Malta CDA content
    malta_cda = """<?xml version="1.0" encoding="UTF-8"?>
    <ClinicalDocument xmlns="urn:hl7-org:v3">
        <component>
            <structuredBody>
                <component>
                    <section>
                        <code code="48765-2"/>
                        <title>Allergies</title>
                        <entry>
                            <observation>
                                <code code="ASSERTION"/>
                                <value displayName="Penicillin G"/>
                            </observation>
                        </entry>
                    </section>
                </component>
            </structuredBody>
        </component>
    </ClinicalDocument>"""

    results = mapper.extract_clinical_data(malta_cda, "MT")
    print(f"Malta extraction results: {json.dumps(results, indent=2)}")


if __name__ == "__main__":
    test_country_specific_extraction()
