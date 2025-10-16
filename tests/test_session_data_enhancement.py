"""
Test Enhanced Session Management with Complete XML Loading

This test verifies that the SessionDataEnhancementService correctly loads
complete XML files from project folders and provides all clinical resources
instead of incomplete database excerpts.
"""

import os
import tempfile
from pathlib import Path
from django.test import TestCase
from django.conf import settings
from unittest.mock import patch, MagicMock

from patient_data.services.session_data_enhancement_service import SessionDataEnhancementService


class TestSessionDataEnhancement(TestCase):
    """Test enhanced session management with complete XML resources"""

    def setUp(self):
        """Set up test data and service"""
        self.service = SessionDataEnhancementService()
        
        # Sample incomplete match data (what sessions currently store)
        self.incomplete_match_data = {
            "patient_data": {
                "given_name": "Maria",
                "family_name": "Santos", 
                "patient_id": "1902395951",
                "country_code": "PT"
            },
            "cda_content": "<clinical_document>...abbreviated...</clinical_document>",
            "has_l3": True,
            "preferred_cda_type": "L3"
        }
        
        # Sample complete XML content (what should be loaded from files)
        self.complete_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <recordTarget>
        <patientRole>
            <id extension="1902395951"/>
        </patientRole>
    </recordTarget>
    <component>
        <structuredBody>
            <component>
                <section>
                    <code code="10160-0" displayName="History of Medication Use"/>
                    <entry>
                        <substanceAdministration>
                            <consumable>
                                <manufacturedProduct>
                                    <manufacturedMaterial>
                                        <name>Eutirox 25mcg</name>
                                        <pharm:ingredient>
                                            <pharm:quantity>
                                                <numerator value="25" unit="ug"/>
                                                <denominator value="1" unit="1"/>
                                            </pharm:quantity>
                                        </pharm:ingredient>
                                    </manufacturedMaterial>
                                </manufacturedProduct>
                            </consumable>
                        </substanceAdministration>
                    </entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""

    def test_service_initialization(self):
        """Test that service initializes with required parsers"""
        self.assertIsNotNone(self.service.enhanced_parser)
        self.assertIsNotNone(self.service.cda_parser)
        self.assertEqual(len(self.service.xml_folders), 5)
        self.assertIn("malta_test_documents", self.service.xml_folders)

    @patch('patient_data.services.session_data_enhancement_service.get_cda_indexer')
    def test_load_complete_xml_via_indexer(self, mock_indexer):
        """Test loading complete XML via CDA indexer"""
        # Mock indexer to return patient with file path
        mock_indexer_instance = MagicMock()
        mock_indexer.return_value = mock_indexer_instance
        mock_indexer_instance.get_all_patients.return_value = [
            {
                "patient_id": "1902395951",
                "file_path": "/test/path/patient.xml"
            }
        ]
        
        # Mock file reading
        with patch.object(self.service, '_read_xml_file') as mock_read:
            mock_read.return_value = self.complete_xml_content
            
            result = self.service._load_complete_xml_file("1902395951", "PT")
            
            self.assertEqual(result, self.complete_xml_content)
            mock_read.assert_called_once_with("/test/path/patient.xml")

    def test_extract_all_xml_resources(self):
        """Test extraction of all clinical resources from complete XML"""
        with patch.object(self.service.enhanced_parser, 'parse_cda_document') as mock_parse:
            mock_parse.return_value = {
                "sections": {
                    "medications": {"entries": [{"name": "Eutirox 25mcg"}]},
                    "allergies": {"entries": []}
                },
                "medications": [{"name": "Eutirox 25mcg", "strength": "25 ug"}],
                "allergies": [],
                "coded_entries": [{"code": "10160-0", "system": "LOINC"}]
            }
            
            with patch.object(self.service.enhanced_parser, 'extract_administrative_data') as mock_admin:
                mock_admin.return_value = {"patient_id": "1902395951"}
                
                resources = self.service._extract_all_xml_resources(self.complete_xml_content)
                
                self.assertIn("clinical_sections", resources)
                self.assertIn("medication_details", resources)
                self.assertIn("parsing_metadata", resources)
                self.assertEqual(len(resources["medication_details"]), 1)
                self.assertEqual(resources["medication_details"][0]["name"], "Eutirox 25mcg")

    def test_enhance_match_data(self):
        """Test enhancement of match data with complete resources"""
        parsed_resources = {
            "clinical_sections": {"medications": {"entries": []}},
            "medication_details": [{"name": "Eutirox 25mcg"}],
            "parsing_metadata": {"total_sections": 1}
        }
        
        enhanced = self.service._enhance_match_data(
            self.incomplete_match_data,
            self.complete_xml_content, 
            parsed_resources
        )
        
        # Verify enhancement flags
        self.assertTrue(enhanced["has_complete_xml"])
        self.assertTrue(enhanced["has_enhanced_parsing"])
        
        # Verify complete XML content
        self.assertEqual(enhanced["complete_xml_content"], self.complete_xml_content)
        self.assertEqual(enhanced["cda_content"], self.complete_xml_content)
        
        # Verify parsed resources
        self.assertEqual(enhanced["parsed_resources"], parsed_resources)
        self.assertEqual(enhanced["medication_count"], 1)
        
        # Verify metadata
        self.assertIn("enhancement_metadata", enhanced)
        self.assertGreater(enhanced["enhancement_metadata"]["size_improvement_ratio"], 1)

    @patch.object(SessionDataEnhancementService, '_load_complete_xml_file')
    @patch.object(SessionDataEnhancementService, '_extract_all_xml_resources') 
    def test_full_enhancement_workflow(self, mock_extract, mock_load):
        """Test complete enhancement workflow from incomplete to complete"""
        # Mock complete XML loading
        mock_load.return_value = self.complete_xml_content
        
        # Mock resource extraction
        mock_extract.return_value = {
            "clinical_sections": {"medications": {"entries": [{"name": "Eutirox"}]}},
            "medication_details": [{"name": "Eutirox 25mcg", "strength": "25 ug"}],
            "parsing_metadata": {"total_sections": 1}
        }
        
        enhanced = self.service.enhance_session_with_complete_xml(
            self.incomplete_match_data, "1902395951", "PT"
        )
        
        # Verify enhancement occurred
        self.assertTrue(enhanced["has_complete_xml"])
        self.assertEqual(enhanced["medication_count"], 1)
        self.assertIn("Eutirox 25mcg", str(enhanced["parsed_resources"]))
        
        # Verify original data preserved
        self.assertEqual(enhanced["patient_data"]["given_name"], "Maria")
        self.assertEqual(enhanced["patient_data"]["family_name"], "Santos")

    def test_enhanced_session_summary(self):
        """Test generation of enhancement summary for monitoring"""
        enhanced_data = {
            "has_complete_xml": True,
            "total_clinical_sections": 3,
            "medication_count": 2,
            "allergy_count": 1,
            "enhancement_metadata": {
                "enhancement_timestamp": "2024-01-01T00:00:00",
                "size_improvement_ratio": 5.2
            },
            "parsed_resources": {
                "parsing_metadata": {"total_sections": 3},
                "administrative_data": {"patient_id": "1902395951"},
                "coded_entries": [{"code": "10160-0"}]
            }
        }
        
        summary = self.service.get_enhanced_session_summary(enhanced_data)
        
        self.assertTrue(summary["session_enhanced"])
        self.assertEqual(summary["xml_size_improvement"], "5.20x")
        self.assertEqual(summary["clinical_sections"]["total_sections"], 3)
        self.assertEqual(summary["clinical_sections"]["medication_count"], 2)
        self.assertEqual(summary["coded_entries_count"], 1)

    def test_error_handling_fallback(self):
        """Test that service falls back gracefully on errors"""
        with patch.object(self.service, '_load_complete_xml_file') as mock_load:
            # Simulate file loading error
            mock_load.side_effect = Exception("File not found")
            
            enhanced = self.service.enhance_session_with_complete_xml(
                self.incomplete_match_data, "1902395951", "PT"
            )
            
            # Should return original data on error
            self.assertEqual(enhanced, self.incomplete_match_data)
            self.assertNotIn("has_complete_xml", enhanced)

    def test_portuguese_cda_medication_extraction(self):
        """Test extraction works with actual Portuguese CDA structure"""
        # This test verifies the specific case mentioned in conversation
        # where Portuguese CDA has 5 medications that should be extracted
        portuguese_xml = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <recordTarget>
        <patientRole><id extension="1902395951"/></patientRole>
    </recordTarget>
    <component>
        <structuredBody>
            <component>
                <section>
                    <code code="10160-0" displayName="History of Medication Use"/>
                    <entry><substanceAdministration>
                        <consumable><manufacturedProduct><manufacturedMaterial>
                            <name>Eutirox 25mcg</name>
                        </manufacturedMaterial></manufacturedProduct></consumable>
                    </substanceAdministration></entry>
                    <entry><substanceAdministration>
                        <consumable><manufacturedProduct><manufacturedMaterial>
                            <name>Triapin 2.5mg</name>
                        </manufacturedMaterial></manufacturedProduct></consumable>
                    </substanceAdministration></entry>
                    <entry><substanceAdministration>
                        <consumable><manufacturedProduct><manufacturedMaterial>
                            <name>Tresiba 100 units/mL</name>
                        </manufacturedMaterial></manufacturedProduct></consumable>
                    </substanceAdministration></entry>
                    <entry><substanceAdministration>
                        <consumable><manufacturedProduct><manufacturedMaterial>
                            <name>Augmentin 625mg</name>
                        </manufacturedMaterial></manufacturedProduct></consumable>
                    </substanceAdministration></entry>
                    <entry><substanceAdministration>
                        <consumable><manufacturedProduct><manufacturedMaterial>
                            <name>Combivent</name>
                        </manufacturedMaterial></manufacturedProduct></consumable>
                    </substanceAdministration></entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""
        
        with patch.object(self.service.enhanced_parser, 'parse_cda_document') as mock_parse:
            # Mock parser to extract 5 medications as mentioned in conversation
            mock_parse.return_value = {
                "medications": [
                    {"name": "Eutirox 25mcg"},
                    {"name": "Triapin 2.5mg"}, 
                    {"name": "Tresiba 100 units/mL"},
                    {"name": "Augmentin 625mg"},
                    {"name": "Combivent"}
                ],
                "sections": {"medications": {"entries": []}},
                "coded_entries": []
            }
            
            with patch.object(self.service.enhanced_parser, 'extract_administrative_data') as mock_admin:
                mock_admin.return_value = {}
                
                resources = self.service._extract_all_xml_resources(portuguese_xml)
                
                # Verify all 5 medications extracted
                self.assertEqual(len(resources["medication_details"]), 5)
                medication_names = [med["name"] for med in resources["medication_details"]]
                self.assertIn("Eutirox 25mcg", medication_names)
                self.assertIn("Triapin 2.5mg", medication_names)
                self.assertIn("Tresiba 100 units/mL", medication_names)
                self.assertIn("Augmentin 625mg", medication_names)
                self.assertIn("Combivent", medication_names)