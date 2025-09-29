#!/usr/bin/env python3
"""
Integration of CDA Document Mapper with Enhanced CDA Processor
"""

from typing import Dict, List, Any, Optional
import logging
from .cda_document_mapper import CDADocumentMapper

logger = logging.getLogger(__name__)


class DocumentMapperIntegration:
    """
    Integrates document-specific mapping with the enhanced CDA processor
    """

    def __init__(self):
        self.document_mapper = CDADocumentMapper()

    def extract_clinical_data_with_mapping(
        self, cda_content: str, country_code: str, patient_id: str = None
    ) -> Dict[str, List]:
        """
        Extract clinical data using document-specific mapping

        Args:
            cda_content: Raw CDA XML content
            country_code: Country code (for fallback/validation)
            patient_id: Patient identifier

        Returns:
            Dictionary with extracted clinical data
        """
        try:
            logger.debug(
                f"Creating document map for patient {patient_id} from {country_code}"
            )

            # Create document-specific map
            document_map = self.document_mapper.create_document_map(
                cda_content, patient_id
            )

            if not document_map or not document_map.get("extraction_patterns"):
                logger.debug("Document map creation failed, using fallback")
                return self._fallback_extraction(cda_content, country_code)

            # Extract using the document map
            results = self.document_mapper.extract_using_map(cda_content, document_map)

            # Log results (reduced)
            total_items = sum(len(items) for items in results.values())
            if total_items > 0:
                logger.info(
                    f"[SUCCESS] Document mapping extracted {total_items} clinical items"
                )
            else:
                logger.info("[ERROR] Document mapping found no clinical items")

            return results

        except Exception as e:
            logger.error(f"Error in document mapper extraction: {e}")
            return self._fallback_extraction(cda_content, country_code)

    def _fallback_extraction(
        self, cda_content: str, country_code: str
    ) -> Dict[str, List]:
        """Fallback to country-specific extraction if document mapping fails"""
        try:
            from .country_specific_cda_mapper import CountrySpecificCDAMapper

            mapper = CountrySpecificCDAMapper()
            return mapper.extract_clinical_data(cda_content, country_code)
        except Exception as e:
            logger.error(f"Fallback extraction also failed: {e}")
            return {"allergies": [], "medications": [], "problems": []}

    def get_document_analysis(
        self, cda_content: str, patient_id: str = None
    ) -> Dict[str, Any]:
        """
        Get detailed analysis of document structure without full extraction
        """
        try:
            document_map = self.document_mapper.create_document_map(
                cda_content, patient_id
            )

            analysis = {
                "document_id": document_map.get("document_id"),
                "patient_id": patient_id,
                "total_sections": len(document_map.get("sections", {})),
                "clinical_sections": 0,
                "extraction_patterns_count": len(
                    document_map.get("extraction_patterns", {})
                ),
                "sections_summary": {},
            }

            # Analyze sections
            for section_code, section_info in document_map.get("sections", {}).items():
                if section_info.get("has_clinical_data"):
                    analysis["clinical_sections"] += 1

                analysis["sections_summary"][section_code] = {
                    "title": section_info.get("title"),
                    "clinical_type": section_info.get("clinical_type", "unknown"),
                    "entry_count": section_info.get("entry_count", 0),
                    "complexity": section_info.get("extraction_complexity", "unknown"),
                }

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing document: {e}")
            return {"error": str(e)}


# Test function to demonstrate the approach
def test_document_mapping_approach():
    """
    Test the document mapping approach with Malta CDA
    """
    import os
    import sys
    import django

    # Setup Django
    sys.path.append("C:/Users/Duncan/VS_Code_Projects/django_ncp")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
    django.setup()

    from patient_data.models import Patient

    print("🧪 TESTING DOCUMENT MAPPING APPROACH")
    print("=" * 50)

    # Get Malta patient
    malta_patient = Patient.objects.filter(source_country="MT").first()
    if not malta_patient:
        print("[ERROR] No Malta patient found!")
        return

    print(f"[LIST] Testing with patient: {malta_patient.patient_id}")

    # Get CDA content
    cda_content = malta_patient.get_cda_content()
    if not cda_content:
        print("[ERROR] No CDA content!")
        return

    print(f"📄 CDA content: {len(cda_content)} characters")

    # Test document mapping
    integration = DocumentMapperIntegration()

    print("\n[SEARCH] CREATING DOCUMENT MAP...")
    analysis = integration.get_document_analysis(cda_content, malta_patient.patient_id)

    print(f"[CHART] DOCUMENT ANALYSIS:")
    print(f"   Total sections: {analysis.get('total_sections', 0)}")
    print(f"   Clinical sections: {analysis.get('clinical_sections', 0)}")
    print(f"   Extraction patterns: {analysis.get('extraction_patterns_count', 0)}")

    print(f"\n[LIST] SECTIONS SUMMARY:")
    for section_code, info in analysis.get("sections_summary", {}).items():
        print(f"   {section_code}: {info['title']}")
        print(f"      Type: {info['clinical_type']}")
        print(f"      Entries: {info['entry_count']}")
        print(f"      Complexity: {info['complexity']}")

    print("\n[TARGET] EXTRACTING CLINICAL DATA...")
    results = integration.extract_clinical_data_with_mapping(
        cda_content, "MT", malta_patient.patient_id
    )

    print(f"[GRAPH] EXTRACTION RESULTS:")
    total_items = 0
    for section_name, items in results.items():
        item_count = len(items)
        total_items += item_count
        print(f"   {section_name}: {item_count} items")

        if items:
            for i, item in enumerate(items[:2]):  # Show first 2
                data = item.get("data", {})
                agent = data.get(
                    "agent_display", data.get("medication_display", "Unknown")
                )
                print(f"      Item {i+1}: {agent}")

    print(f"\n🏁 TOTAL ITEMS EXTRACTED: {total_items}")

    return total_items > 0


if __name__ == "__main__":
    test_document_mapping_approach()
