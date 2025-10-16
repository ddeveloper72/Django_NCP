"""
Enhanced CDA XML Parser Phase 2 Consolidation Tests

Django NCP Healthcare Portal - Unified Extraction Methods Testing
Generated: December 19, 2024
Purpose: Test the Phase 2 consolidation of 8 systematic methods into 3 unified methods
"""

import pytest
import xml.etree.ElementTree as ET
from unittest.mock import Mock, patch

from patient_data.services.enhanced_cda_xml_parser import EnhancedCDAXMLParser, ClinicalCode
from patient_data.services.patient_demographics_service import PatientDemographicsService


class TestPhase2Consolidation:
    """Test the consolidation of systematic extraction methods"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.parser = EnhancedCDAXMLParser()
        self.demographics_service = PatientDemographicsService()
    
    def test_unified_methods_exist(self):
        """Test that all three unified methods exist"""
        assert hasattr(self.parser, '_extract_code_elements_unified')
        assert hasattr(self.parser, '_extract_contextual_elements_unified')
        assert hasattr(self.parser, '_extract_structural_elements_unified')
    
    def test_old_systematic_methods_removed(self):
        """Test that old systematic methods have been removed"""
        # These methods should no longer exist
        removed_methods = [
            '_extract_coded_elements_systematic',
            '_extract_coded_elements_systematic_enhanced',
            '_extract_text_elements_systematic',
            '_extract_time_elements_systematic',
            '_extract_status_elements_systematic',
            '_extract_value_elements_systematic',
            '_extract_nested_entries_systematic',
            '_extract_medication_codes_systematic'
        ]
        
        for method_name in removed_methods:
            assert not hasattr(self.parser, method_name), f"Method {method_name} should have been removed"
    
    def test_method_count_reduction(self):
        """Test that the total method count has been reduced"""
        all_methods = [method for method in dir(self.parser) if not method.startswith('__') and callable(getattr(self.parser, method))]
        extraction_methods = [method for method in all_methods if '_extract_' in method]
        unified_methods = [method for method in extraction_methods if 'unified' in method]
        
        # Should have exactly 3 unified methods
        assert len(unified_methods) == 3
        
        # Verify specific unified methods
        expected_unified = [
            '_extract_code_elements_unified',
            '_extract_contextual_elements_unified', 
            '_extract_structural_elements_unified'
        ]
        
        for method in expected_unified:
            assert method in unified_methods

    def test_code_elements_unified_functionality(self):
        """Test the unified code elements extraction"""
        # Create a mock XML element with code elements
        xml_content = '''
        <entry xmlns="urn:hl7-org:v3">
            <observation>
                <code code="11348-0" codeSystem="2.16.840.1.113883.6.1" displayName="History of past illness"/>
                <value code="D09" codeSystem="2.16.840.1.113883.6.3" displayName="Carcinoma in situ"/>
                <translation code="TEST" codeSystem="2.16.840.1.113883.6.96" displayName="Test Translation"/>
            </observation>
        </entry>
        '''
        
        entry = ET.fromstring(xml_content)
        codes = []
        
        # Test the unified method
        self.parser._extract_code_elements_unified(entry, codes)
        
        # Should extract codes from code, value, and translation elements
        assert len(codes) >= 2  # At least the main code and value
        
        # Check that LOINC and ICD-10 codes are found
        loinc_found = any(code.system == "2.16.840.1.113883.6.1" for code in codes)
        icd10_found = any(code.system == "2.16.840.1.113883.6.3" for code in codes)
        
        assert loinc_found, "LOINC code should be extracted"
        assert icd10_found, "ICD-10 code should be extracted"

    def test_contextual_elements_unified_functionality(self):
        """Test the unified contextual elements extraction"""
        xml_content = '''
        <entry xmlns="urn:hl7-org:v3">
            <observation>
                <statusCode code="completed"/>
                <effectiveTime value="20231201"/>
                <value unit="mg" value="100" xsi:type="PQ"/>
                <originalText>
                    <reference value="#text1"/>
                </originalText>
            </observation>
        </entry>
        '''
        
        entry = ET.fromstring(xml_content)
        codes = []
        
        # Test the unified method
        self.parser._extract_contextual_elements_unified(entry, codes)
        
        # Should extract status codes and unit codes
        status_codes = [code for code in codes if code.system == "2.16.840.1.113883.5.14"]
        unit_codes = [code for code in codes if code.system == "2.16.840.1.113883.6.8"]
        
        assert len(status_codes) >= 1, "Status code should be extracted"
        assert len(unit_codes) >= 1, "Unit code should be extracted"

    def test_structural_elements_unified_functionality(self):
        """Test the unified structural elements extraction"""
        xml_content = '''
        <entry xmlns="urn:hl7-org:v3">
            <substanceAdministration>
                <entryRelationship>
                    <observation>
                        <code code="TEST" codeSystem="2.16.840.1.113883.6.96" displayName="Test Code"/>
                    </observation>
                </entryRelationship>
                <component>
                    <observation>
                        <code code="COMP" codeSystem="2.16.840.1.113883.6.1" displayName="Component Code"/>
                    </observation>
                </component>
                <manufacturedProduct>
                    <code code="MED" codeSystem="2.16.840.1.113883.6.88" displayName="Medication Code"/>
                </manufacturedProduct>
            </substanceAdministration>
        </entry>
        '''
        
        entry = ET.fromstring(xml_content)
        codes = []
        
        # Test the unified method
        self.parser._extract_structural_elements_unified(entry, codes)
        
        # Should extract codes from nested structures and medication elements
        assert len(codes) >= 2, "Should extract codes from nested structures"
        
        # Check for different types of structural codes
        snomed_codes = [code for code in codes if code.system == "2.16.840.1.113883.6.96"]
        loinc_codes = [code for code in codes if code.system == "2.16.840.1.113883.6.1"]
        
        assert len(snomed_codes) >= 1, "SNOMED code should be extracted from nested structure"
        assert len(loinc_codes) >= 1, "LOINC code should be extracted from component"

    def test_extract_coded_entries_uses_unified_methods(self):
        """Test that _extract_coded_entries uses the new unified methods"""
        # Create a mock section with entries
        xml_content = '''
        <section xmlns="urn:hl7-org:v3">
            <entry>
                <observation>
                    <code code="11348-0" codeSystem="2.16.840.1.113883.6.1" displayName="Test"/>
                    <statusCode code="completed"/>
                </observation>
            </entry>
        </section>
        '''
        
        section = ET.fromstring(xml_content)
        
        # Test that the main extraction method works
        result = self.parser._extract_coded_entries(section)
        
        assert result is not None
        assert hasattr(result, 'codes')
        
        # Should extract at least one code
        assert len(result.codes) >= 1

    def test_integration_with_patient_demographics_service(self):
        """Test that the consolidated parser integrates properly with demographics service"""
        # Test Diana Ferreira data
        session_data = {
            'given_name': 'Diana',
            'family_name': 'Ferreira',
            'birth_date': '19820508',
            'gender': 'F',
            'patient_identifiers': [
                {'extension': '2-1234-W7', 'root': '2.16.17.710.804.1000.990.1', 'assigning_authority_name': 'SNS'}
            ]
        }
        
        # Should work without issues
        demographics = self.demographics_service.extract_from_session_data(session_data)
        context = self.demographics_service.create_unified_template_context(demographics)
        
        assert demographics.get_display_name() == "Diana Ferreira"
        assert demographics.get_formatted_birth_date() == "08/05/1982"
        assert "patient" in context
        assert "patient_data" in context  # Backward compatibility

    def test_european_healthcare_standards_compliance(self):
        """Test that the unified methods maintain European healthcare standards"""
        # Test with Italian healthcare codes
        xml_content = '''
        <entry xmlns="urn:hl7-org:v3">
            <observation>
                <code code="TEST" codeSystem="2.16.840.1.113883.2.9" displayName="Italian Code"/>
                <value code="UCUM" codeSystem="2.16.840.1.113883.6.8" unit="mg" displayName="UCUM Unit"/>
            </observation>
        </entry>
        '''
        
        entry = ET.fromstring(xml_content)
        codes = []
        
        # Test code extraction
        self.parser._extract_code_elements_unified(entry, codes)
        
        # Should handle Italian healthcare codes
        italian_codes = [code for code in codes if "2.16.840.1.113883.2.9" in code.system]
        assert len(italian_codes) >= 1, "Should extract Italian healthcare codes"
        
        # Test contextual extraction for UCUM units
        codes_contextual = []
        self.parser._extract_contextual_elements_unified(entry, codes_contextual)
        
        # Should extract UCUM units
        ucum_codes = [code for code in codes_contextual if "UCUM" in (code.system_name or "")]
        assert len(ucum_codes) >= 1, "Should extract UCUM units for European compliance"

    def test_performance_improvement(self):
        """Test that the consolidated methods perform efficiently"""
        # Create a more complex XML structure
        xml_content = '''
        <section xmlns="urn:hl7-org:v3">
            <entry>
                <observation>
                    <code code="11348-0" codeSystem="2.16.840.1.113883.6.1"/>
                    <statusCode code="completed"/>
                    <effectiveTime value="20231201"/>
                    <value unit="mg" code="TEST" codeSystem="2.16.840.1.113883.6.96"/>
                    <entryRelationship>
                        <observation>
                            <code code="NESTED" codeSystem="2.16.840.1.113883.6.3"/>
                        </observation>
                    </entryRelationship>
                </observation>
            </entry>
        </section>
        '''
        
        section = ET.fromstring(xml_content)
        
        # Time the extraction (simplified performance test)
        import time
        start_time = time.time()
        
        result = self.parser._extract_coded_entries(section)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete quickly (under 1 second for this simple test)
        assert execution_time < 1.0, "Extraction should be performant"
        
        # Should still extract all expected codes
        assert len(result.codes) >= 3, "Should extract multiple codes efficiently"


class TestDianaFerreirIntegration:
    """Test specific Diana Ferreira integration with Phase 2 changes"""
    
    def setup_method(self):
        """Set up Diana Ferreira test data"""
        self.diana_session_data = {
            'given_name': 'Diana',
            'family_name': 'Ferreira',
            'birth_date': '19820508',
            'gender': 'F',
            'patient_identifiers': [
                {'extension': '2-1234-W7', 'root': '2.16.17.710.804.1000.990.1', 'assigning_authority_name': 'SNS'}
            ]
        }
        self.demographics_service = PatientDemographicsService()
    
    def test_diana_ferreira_extraction_unchanged(self):
        """Test that Diana Ferreira extraction works identically to before"""
        demographics = self.demographics_service.extract_from_session_data(self.diana_session_data)
        
        # Core demographic data should be identical
        assert demographics.get_display_name() == "Diana Ferreira"
        assert demographics.get_formatted_birth_date() == "08/05/1982"
        assert demographics.gender == "Female"
        assert demographics.get_primary_identifier().extension == "2-1234-W7"
    
    def test_diana_ferreira_template_context_compatibility(self):
        """Test that Diana Ferreira template context is fully compatible"""
        demographics = self.demographics_service.extract_from_session_data(self.diana_session_data)
        context = self.demographics_service.create_unified_template_context(demographics)
        
        # All expected context keys should be present
        expected_keys = ['patient', 'patient_data', 'patient_information', 'patient_identity', 'patient_display_name']
        for key in expected_keys:
            assert key in context, f"Template context missing key: {key}"
        
        # Legacy patient data should match expected format
        patient_data = context['patient_data']
        assert patient_data['given_name'] == 'Diana'
        assert patient_data['family_name'] == 'Ferreira'
        assert patient_data['birth_date'] == '19820508'
        assert patient_data['gender'] == 'Female'
        
        # Unified patient data should be available
        patient = context['patient']
        assert patient['display_name'] == 'Diana Ferreira'
        assert patient['formatted_birth_date'] == '08/05/1982'
    
    def test_diana_ferreira_ui_rendering_preserved(self):
        """Test that UI rendering data is preserved for Diana Ferreira"""
        demographics = self.demographics_service.extract_from_session_data(self.diana_session_data)
        context = self.demographics_service.create_unified_template_context(demographics)
        
        # Template display name should be available
        assert context['patient_display_name'] == 'Diana Ferreira'
        
        # Patient identity (used in templates) should have correct structure
        patient_identity = context['patient_identity']
        assert 'birth_date' in patient_identity
        assert 'gender' in patient_identity
        assert 'patient_identifiers' in patient_identity
        
        # Identifiers should be in expected format
        identifiers = patient_identity['patient_identifiers']
        assert len(identifiers) == 1
        assert identifiers[0]['extension'] == '2-1234-W7'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])