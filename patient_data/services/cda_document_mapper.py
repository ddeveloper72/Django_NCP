#!/usr/bin/env python3
"""
CDA Document Mapper - Creates document-specific JSON maps for efficient CDA processing
"""

import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
import logging
import hashlib
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class CDADocumentMapper:
    """
    Creates and manages document-specific JSON maps for CDA processing
    Each CDA gets its own optimized extraction map
    """

    def __init__(self, cache_dir: str = "cda_maps"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def create_document_map(
        self, cda_content: str, patient_id: str = None
    ) -> Dict[str, Any]:
        """
        Create a document-specific JSON map for a CDA

        Args:
            cda_content: Raw CDA XML content
            patient_id: Optional patient identifier for naming

        Returns:
            Dictionary containing the document map
        """
        try:
            # Generate document hash for caching
            doc_hash = hashlib.md5(cda_content.encode()).hexdigest()
            cache_file = self.cache_dir / f"cda_map_{doc_hash}.json"

            # Check if map already exists
            if cache_file.exists():
                logger.info(f"Loading cached document map for {patient_id or doc_hash}")
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)

            logger.info(f"Creating new document map for {patient_id or doc_hash}")

            # Parse the CDA
            root = ET.fromstring(cda_content)
            namespaces = {
                "hl7": "urn:hl7-org:v3",
                "pharm": "urn:hl7-org:pharm",
                "xsi": "http://www.w3.org/2001/XMLSchema-instance",
            }

            # Create the document map
            document_map = {
                "document_id": doc_hash,
                "patient_id": patient_id,
                "created_at": str(datetime.now()),
                "sections": {},
                "extraction_patterns": {},
                "metadata": {},
            }

            # Extract document metadata
            document_map["metadata"] = self._extract_document_metadata(root, namespaces)

            # Find all sections and create extraction patterns
            sections = root.findall(".//hl7:section", namespaces)
            logger.info(f"Found {len(sections)} sections in document")

            for i, section in enumerate(sections):
                section_info = self._analyze_section(section, namespaces, i)
                if section_info:
                    section_code = section_info["code"]
                    document_map["sections"][section_code] = section_info

                    # Create extraction patterns for this section
                    patterns = self._create_extraction_patterns(
                        section, namespaces, section_code
                    )
                    if patterns:
                        document_map["extraction_patterns"][section_code] = patterns

            # Save to cache
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(document_map, f, indent=2, ensure_ascii=False)

            logger.info(
                f"Created document map with {len(document_map['sections'])} sections"
            )
            return document_map

        except Exception as e:
            logger.error(f"Error creating document map: {e}")
            return {}

    def _extract_document_metadata(
        self, root: ET.Element, namespaces: Dict
    ) -> Dict[str, Any]:
        """Extract document-level metadata"""
        metadata = {}

        try:
            # Document ID
            doc_id = root.find(".//hl7:id", namespaces)
            if doc_id is not None:
                metadata["document_id"] = doc_id.get("extension", "")
                metadata["document_root"] = doc_id.get("root", "")

            # Document type
            type_elem = root.find(".//hl7:code", namespaces)
            if type_elem is not None:
                metadata["document_type"] = type_elem.get("displayName", "")
                metadata["document_type_code"] = type_elem.get("code", "")

            # Patient info
            patient_role = root.find(".//hl7:patientRole", namespaces)
            if patient_role is not None:
                patient_id = patient_role.find("hl7:id", namespaces)
                if patient_id is not None:
                    metadata["patient_id"] = patient_id.get("extension", "")
                    metadata["patient_root"] = patient_id.get("root", "")

        except Exception as e:
            logger.error(f"Error extracting document metadata: {e}")

        return metadata

    def _analyze_section(
        self, section: ET.Element, namespaces: Dict, index: int
    ) -> Optional[Dict[str, Any]]:
        """Analyze a section and create its description"""
        try:
            # Get section code
            code_elem = section.find("hl7:code", namespaces)
            section_code = (
                code_elem.get("code", f"section_{index}")
                if code_elem is not None
                else f"section_{index}"
            )

            # Get section title
            title_elem = section.find("hl7:title", namespaces)
            section_title = (
                title_elem.text if title_elem is not None else "Unknown Section"
            )

            # Count entries
            entries = section.findall(".//hl7:entry", namespaces)
            entry_count = len(entries)

            # Analyze entry types
            entry_types = self._analyze_entry_types(entries, namespaces)

            section_info = {
                "code": section_code,
                "title": section_title,
                "entry_count": entry_count,
                "entry_types": entry_types,
                "has_clinical_data": entry_count > 0,
            }

            # Add section-specific analysis
            if section_code in ["48765-2", "10155-0"]:  # Allergies
                section_info["clinical_type"] = "allergies"
                section_info["extraction_complexity"] = (
                    self._analyze_allergy_complexity(entries, namespaces)
                )
            elif section_code == "10160-0":  # Medications
                section_info["clinical_type"] = "medications"
                section_info["extraction_complexity"] = (
                    self._analyze_medication_complexity(entries, namespaces)
                )
            elif section_code == "11450-4":  # Problems
                section_info["clinical_type"] = "problems"
                section_info["extraction_complexity"] = (
                    self._analyze_problem_complexity(entries, namespaces)
                )

            return section_info

        except Exception as e:
            logger.error(f"Error analyzing section: {e}")
            return None

    def _analyze_entry_types(
        self, entries: List[ET.Element], namespaces: Dict
    ) -> Dict[str, int]:
        """Analyze what types of entries exist in a section"""
        entry_types = {}

        for entry in entries:
            # Check for different entry patterns
            if entry.find("hl7:act", namespaces) is not None:
                entry_types["act"] = entry_types.get("act", 0) + 1

                # Check for specific act types
                act_code = entry.find("hl7:act/hl7:code", namespaces)
                if act_code is not None:
                    code = act_code.get("code", "")
                    if code == "CONC":
                        entry_types["allergy_act"] = (
                            entry_types.get("allergy_act", 0) + 1
                        )

            if entry.find(".//hl7:observation", namespaces) is not None:
                entry_types["observation"] = entry_types.get("observation", 0) + 1

            if entry.find(".//hl7:substanceAdministration", namespaces) is not None:
                entry_types["substance_administration"] = (
                    entry_types.get("substance_administration", 0) + 1
                )

            if entry.find(".//hl7:procedure", namespaces) is not None:
                entry_types["procedure"] = entry_types.get("procedure", 0) + 1

        return entry_types

    def _create_extraction_patterns(
        self, section: ET.Element, namespaces: Dict, section_code: str
    ) -> Dict[str, Any]:
        """Create specific extraction patterns for this section"""
        patterns = {"section_code": section_code, "entries": []}

        entries = section.findall(".//hl7:entry", namespaces)

        for i, entry in enumerate(entries):
            entry_pattern = self._create_entry_pattern(entry, namespaces, i)
            if entry_pattern:
                patterns["entries"].append(entry_pattern)

        return patterns

    def _create_entry_pattern(
        self, entry: ET.Element, namespaces: Dict, index: int
    ) -> Dict[str, Any]:
        """Create extraction pattern for a specific entry"""
        pattern = {"entry_index": index, "extraction_paths": {}}

        try:
            # Look for common clinical data patterns

            # Pattern 1: act > entryRelationship > observation > participant (Malta allergies)
            if (
                entry.find(
                    "hl7:act/hl7:entryRelationship/hl7:observation/hl7:participant",
                    namespaces,
                )
                is not None
            ):
                pattern["pattern_type"] = "act_observation_participant"
                pattern["extraction_paths"] = {
                    "substance": "hl7:act/hl7:entryRelationship/hl7:observation/hl7:participant/hl7:participantRole/hl7:playingEntity/hl7:code/@displayName",
                    "substance_code": "hl7:act/hl7:entryRelationship/hl7:observation/hl7:participant/hl7:participantRole/hl7:playingEntity/hl7:code/@code",
                    "type": "hl7:act/hl7:entryRelationship/hl7:observation/hl7:code/@displayName",
                    "date": "hl7:act/hl7:effectiveTime/hl7:low/@value",
                    "status": "hl7:act/hl7:statusCode/@code",
                }

            # Pattern 2: Direct observation with participant
            elif (
                entry.find(".//hl7:observation/hl7:participant", namespaces) is not None
            ):
                pattern["pattern_type"] = "observation_participant"
                pattern["extraction_paths"] = {
                    "substance": ".//hl7:observation/hl7:participant/hl7:participantRole/hl7:playingEntity/hl7:code/@displayName",
                    "substance_code": ".//hl7:observation/hl7:participant/hl7:participantRole/hl7:playingEntity/hl7:code/@code",
                    "type": ".//hl7:observation/hl7:code/@displayName",
                }

            # Pattern 3: Substance administration (medications)
            elif entry.find(".//hl7:substanceAdministration", namespaces) is not None:
                pattern["pattern_type"] = "substance_administration"
                pattern["extraction_paths"] = {
                    "medication": ".//hl7:substanceAdministration/hl7:consumable/hl7:manufacturedProduct/hl7:manufacturedMaterial/hl7:code/@displayName",
                    "medication_code": ".//hl7:substanceAdministration/hl7:consumable/hl7:manufacturedProduct/hl7:manufacturedMaterial/hl7:code/@code",
                    "dosage": ".//hl7:substanceAdministration/hl7:doseQuantity/@value",
                    "unit": ".//hl7:substanceAdministration/hl7:doseQuantity/@unit",
                }

            # Pattern 4: Generic observation
            elif entry.find(".//hl7:observation", namespaces) is not None:
                pattern["pattern_type"] = "observation"
                pattern["extraction_paths"] = {
                    "value": ".//hl7:observation/hl7:value/@displayName",
                    "code": ".//hl7:observation/hl7:code/@code",
                    "display": ".//hl7:observation/hl7:code/@displayName",
                }

            # Test the patterns to make sure they work
            pattern["test_results"] = self._test_extraction_pattern(
                entry, pattern["extraction_paths"], namespaces
            )

        except Exception as e:
            logger.error(f"Error creating entry pattern: {e}")

        return pattern

    def _test_extraction_pattern(
        self, entry: ET.Element, paths: Dict[str, str], namespaces: Dict
    ) -> Dict[str, Any]:
        """Test extraction patterns to see if they find data"""
        results = {}

        for field_name, xpath in paths.items():
            try:
                if "/@" in xpath:  # Attribute extraction
                    elem_path = xpath.split("/@")[0]
                    attr_name = xpath.split("/@")[1]
                    elem = entry.find(elem_path, namespaces)
                    if elem is not None:
                        value = elem.get(attr_name)
                        results[field_name] = {
                            "found": True,
                            "value": value,
                            "sample": value[:50] if value else "",
                        }
                    else:
                        results[field_name] = {"found": False, "value": None}
                else:  # Element text extraction
                    elem = entry.find(xpath, namespaces)
                    if elem is not None:
                        value = elem.text
                        results[field_name] = {
                            "found": True,
                            "value": value,
                            "sample": value[:50] if value else "",
                        }
                    else:
                        results[field_name] = {"found": False, "value": None}
            except Exception as e:
                results[field_name] = {"found": False, "error": str(e)}

        return results

    def extract_using_map(
        self, cda_content: str, document_map: Dict[str, Any]
    ) -> Dict[str, List]:
        """Extract clinical data using the document map"""
        try:
            root = ET.fromstring(cda_content)
            namespaces = {
                "hl7": "urn:hl7-org:v3",
                "pharm": "urn:hl7-org:pharm",
                "xsi": "http://www.w3.org/2001/XMLSchema-instance",
            }

            results = {"allergies": [], "medications": [], "problems": []}

            # Process each section using its specific patterns
            for section_code, patterns in document_map.get(
                "extraction_patterns", {}
            ).items():
                section_results = self._extract_section_using_patterns(
                    root, patterns, namespaces
                )

                # Map to clinical categories
                section_info = document_map["sections"].get(section_code, {})
                clinical_type = section_info.get("clinical_type", "unknown")

                if clinical_type in results:
                    results[clinical_type].extend(section_results)

            logger.info(
                f"Extracted using document map: {sum(len(items) for items in results.values())} total items"
            )
            return results

        except Exception as e:
            logger.error(f"Error extracting using document map: {e}")
            return {"allergies": [], "medications": [], "problems": []}

    def _extract_section_using_patterns(
        self, root: ET.Element, patterns: Dict[str, Any], namespaces: Dict
    ) -> List[Dict]:
        """Extract data from a section using its specific patterns"""
        results = []
        section_code = patterns["section_code"]

        # Find the section
        section = root.find(
            f".//hl7:section[hl7:code/@code='{section_code}']", namespaces
        )
        if section is None:
            return results

        entries = section.findall(".//hl7:entry", namespaces)

        for i, entry in enumerate(entries):
            if i < len(patterns["entries"]):
                entry_pattern = patterns["entries"][i]
                extracted_data = self._extract_entry_using_pattern(
                    entry, entry_pattern, namespaces
                )
                if extracted_data:
                    results.append(extracted_data)

        return results

    def _extract_entry_using_pattern(
        self, entry: ET.Element, pattern: Dict[str, Any], namespaces: Dict
    ) -> Optional[Dict]:
        """Extract data from an entry using its specific pattern"""
        try:
            data = {"data": {}}
            extraction_paths = pattern.get("extraction_paths", {})

            for field_name, xpath in extraction_paths.items():
                value = None

                if "/@" in xpath:  # Attribute extraction
                    elem_path = xpath.split("/@")[0]
                    attr_name = xpath.split("/@")[1]
                    elem = entry.find(elem_path, namespaces)
                    if elem is not None:
                        value = elem.get(attr_name)
                else:  # Element text extraction
                    elem = entry.find(xpath, namespaces)
                    if elem is not None:
                        value = elem.text

                if value:
                    # Map to standard field names
                    if field_name == "substance":
                        data["data"]["agent_display"] = value
                    elif field_name == "substance_code":
                        data["data"]["agent_code"] = value
                    elif field_name == "type":
                        data["data"]["type_display"] = value
                    elif field_name == "medication":
                        data["data"]["medication_display"] = value
                    elif field_name == "medication_code":
                        data["data"]["medication_code"] = value
                    else:
                        data["data"][field_name] = value

            # Only return if we extracted meaningful data
            if any(data["data"].values()):
                return data

        except Exception as e:
            logger.error(f"Error extracting entry using pattern: {e}")

        return None

    def _analyze_allergy_complexity(
        self, entries: List[ET.Element], namespaces: Dict
    ) -> str:
        """Analyze complexity of allergy extraction for this document"""
        if not entries:
            return "no_data"

        # Check first entry to determine pattern complexity
        entry = entries[0]
        if (
            entry.find(
                "hl7:act/hl7:entryRelationship/hl7:observation/hl7:participant",
                namespaces,
            )
            is not None
        ):
            return "complex_act_observation"
        elif entry.find(".//hl7:observation/hl7:participant", namespaces) is not None:
            return "simple_observation"
        else:
            return "unknown"

    def _analyze_medication_complexity(
        self, entries: List[ET.Element], namespaces: Dict
    ) -> str:
        """Analyze complexity of medication extraction for this document"""
        if not entries:
            return "no_data"

        entry = entries[0]
        if entry.find(".//hl7:substanceAdministration", namespaces) is not None:
            return "substance_administration"
        else:
            return "unknown"

    def _analyze_problem_complexity(
        self, entries: List[ET.Element], namespaces: Dict
    ) -> str:
        """Analyze complexity of problem extraction for this document"""
        if not entries:
            return "no_data"

        entry = entries[0]
        if entry.find(".//hl7:observation", namespaces) is not None:
            return "observation_based"
        else:
            return "unknown"


if __name__ == "__main__":
    # Example usage
    import datetime

    mapper = CDADocumentMapper()

    # Test with sample content (you would pass actual CDA content)
    sample_cda = """<?xml version="1.0"?>
    <ClinicalDocument xmlns="urn:hl7-org:v3">
        <component>
            <structuredBody>
                <component>
                    <section>
                        <code code="48765-2"/>
                        <title>Allergies</title>
                        <entry>
                            <act>
                                <code code="CONC"/>
                                <entryRelationship>
                                    <observation>
                                        <participant>
                                            <participantRole>
                                                <playingEntity>
                                                    <code displayName="Penicillin"/>
                                                </playingEntity>
                                            </participantRole>
                                        </participant>
                                    </observation>
                                </entryRelationship>
                            </act>
                        </entry>
                    </section>
                </component>
            </structuredBody>
        </component>
    </ClinicalDocument>"""

    # Create map
    doc_map = mapper.create_document_map(sample_cda, "test_patient")
    print(json.dumps(doc_map, indent=2))
