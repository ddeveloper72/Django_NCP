"""
Unit Tests for Patient Demographics Service

Django NCP Healthcare Portal - Testing unified patient demographic processing
Generated: December 19, 2024
Purpose: Comprehensive test coverage for PatientDemographicsService and models
"""

import pytest
import xml.etree.ElementTree as ET
from datetime import datetime
from unittest.mock import Mock, patch

from patient_data.models.patient_demographics import PatientDemographics, PatientIdentifier
from patient_data.services.patient_demographics_service import PatientDemographicsService


class TestPatientIdentifier:
    """Test PatientIdentifier data model"""
    
    def test_valid_identifier_creation(self):
        """Test creating valid patient identifier"""
        identifier = PatientIdentifier(
            extension="2-1234-W7",
            root="2.16.17.710.804.1000.990.1",
            assigning_authority_name="SNS",
            identifier_type="primary"
        )
        
        assert identifier.extension == "2-1234-W7"
        assert identifier.root == "2.16.17.710.804.1000.990.1"
        assert identifier.assigning_authority_name == "SNS"
        assert identifier.identifier_type == "primary"
    
    def test_empty_extension_raises_error(self):
        """Test that empty extension raises ValueError"""
        with pytest.raises(ValueError, match="Patient identifier extension cannot be empty"):
            PatientIdentifier(extension="")
    
    def test_invalid_identifier_type_normalized(self):
        """Test that invalid identifier type is normalized to primary"""
        identifier = PatientIdentifier(extension="123", identifier_type="invalid")
        assert identifier.identifier_type == "primary"
    
    def test_get_display_value(self):
        """Test display value formatting"""
        identifier = PatientIdentifier(extension="2-1234-W7")
        assert identifier.get_display_value() == "2-1234-W7"
    
    def test_get_full_identifier_with_root(self):
        """Test full identifier with root"""
        identifier = PatientIdentifier(
            extension="2-1234-W7",
            root="2.16.17.710.804.1000.990.1"
        )
        assert identifier.get_full_identifier() == "2.16.17.710.804.1000.990.1^^^2-1234-W7"
    
    def test_get_full_identifier_without_root(self):
        """Test full identifier without root"""
        identifier = PatientIdentifier(extension="2-1234-W7")
        assert identifier.get_full_identifier() == "2-1234-W7"
    
    def test_is_european_health_id_portuguese(self):
        """Test European health ID detection for Portuguese format"""
        identifier = PatientIdentifier(extension="2-1234-W7")
        assert identifier.is_european_health_id() is True
    
    def test_is_european_health_id_generic(self):
        """Test European health ID detection for generic format"""
        identifier = PatientIdentifier(extension="PT123456789")
        assert identifier.is_european_health_id() is True
    
    def test_is_european_health_id_numeric(self):
        """Test European health ID detection for numeric format"""
        identifier = PatientIdentifier(extension="123456789")
        assert identifier.is_european_health_id() is True
    
    def test_is_not_european_health_id(self):
        """Test non-European health ID format"""
        identifier = PatientIdentifier(extension="ABC-123")
        assert identifier.is_european_health_id() is False


class TestPatientDemographics:
    """Test PatientDemographics data model"""
    
    def test_diana_ferreira_demographics(self):
        """Test creating Diana Ferreira demographics"""
        demographics = PatientDemographics(
            given_name="Diana",
            family_name="Ferreira",
            birth_date="19820508",
            gender="F",
            patient_id="1444715089",
            identifiers=[
                PatientIdentifier(
                    extension="2-1234-W7",
                    root="2.16.17.710.804.1000.990.1",
                    assigning_authority_name="SNS"
                )
            ]
        )
        
        assert demographics.given_name == "Diana"
        assert demographics.family_name == "Ferreira"
        assert demographics.birth_date == "19820508"
        assert demographics.gender == "Female"  # Normalized
        assert demographics.patient_id == "1444715089"
        assert len(demographics.identifiers) == 1
    
    def test_gender_normalization_portuguese(self):
        """Test gender normalization for Portuguese"""
        demographics = PatientDemographics(gender="feminino")
        assert demographics.gender == "Female"
        
        demographics = PatientDemographics(gender="masculino")
        assert demographics.gender == "Male"
    
    def test_gender_normalization_standard(self):
        """Test gender normalization for standard values"""
        demographics = PatientDemographics(gender="f")
        assert demographics.gender == "Female"
        
        demographics = PatientDemographics(gender="M")
        assert demographics.gender == "Male"
    
    def test_get_display_name_full(self):
        """Test display name with both names"""
        demographics = PatientDemographics(
            given_name="Diana",
            family_name="Ferreira"
        )
        assert demographics.get_display_name() == "Diana Ferreira"
    
    def test_get_display_name_unknown(self):
        """Test display name with unknown names"""
        demographics = PatientDemographics()
        assert demographics.get_display_name() == "Unknown Patient"
    
    def test_get_display_name_partial(self):
        """Test display name with partial information"""
        demographics = PatientDemographics(
            given_name="Diana",
            family_name="Unknown"
        )
        assert demographics.get_display_name() == "Diana"
    
    def test_get_formatted_birth_date_cda_format(self):
        """Test birth date formatting from CDA format"""
        demographics = PatientDemographics(birth_date="19820508")
        assert demographics.get_formatted_birth_date() == "08/05/1982"
    
    def test_get_formatted_birth_date_iso_format(self):
        """Test birth date formatting from ISO format"""
        demographics = PatientDemographics(birth_date="1982-05-08")
        assert demographics.get_formatted_birth_date() == "08/05/1982"
    
    def test_get_formatted_birth_date_already_formatted(self):
        """Test birth date that's already formatted"""
        demographics = PatientDemographics(birth_date="08/05/1982")
        assert demographics.get_formatted_birth_date() == "08/05/1982"
    
    def test_get_formatted_birth_date_invalid(self):
        """Test invalid birth date returns as-is"""
        demographics = PatientDemographics(birth_date="invalid")
        assert demographics.get_formatted_birth_date() == "invalid"
    
    def test_get_primary_identifier(self):
        """Test getting primary identifier"""
        primary_id = PatientIdentifier(extension="2-1234-W7", identifier_type="primary")
        secondary_id = PatientIdentifier(extension="987654321", identifier_type="secondary")
        
        demographics = PatientDemographics(identifiers=[primary_id, secondary_id])
        assert demographics.get_primary_identifier() == primary_id
    
    def test_get_primary_identifier_first_if_no_primary(self):
        """Test getting first identifier if no primary"""
        id1 = PatientIdentifier(extension="2-1234-W7", identifier_type="secondary")
        id2 = PatientIdentifier(extension="987654321", identifier_type="secondary")
        
        demographics = PatientDemographics(identifiers=[id1, id2])
        assert demographics.get_primary_identifier() == id1
    
    def test_get_primary_identifier_none_if_empty(self):
        """Test getting None if no identifiers"""
        demographics = PatientDemographics()
        assert demographics.get_primary_identifier() is None
    
    def test_get_age_at_date(self):
        """Test age calculation"""
        demographics = PatientDemographics(birth_date="19820508")
        reference_date = datetime(2024, 12, 19)
        age = demographics.get_age_at_date(reference_date)
        assert age == 42
    
    def test_get_age_birthday_not_passed(self):
        """Test age when birthday hasn't passed this year"""
        demographics = PatientDemographics(birth_date="19820508")
        reference_date = datetime(2024, 3, 1)  # Before May 8th
        age = demographics.get_age_at_date(reference_date)
        assert age == 41
    
    def test_get_age_invalid_birth_date(self):
        """Test age with invalid birth date"""
        demographics = PatientDemographics(birth_date="invalid")
        assert demographics.get_age_at_date() is None
    
    def test_to_template_context(self):
        """Test template context creation"""
        demographics = PatientDemographics(
            given_name="Diana",
            family_name="Ferreira",
            birth_date="19820508",
            gender="Female",
            identifiers=[
                PatientIdentifier(extension="2-1234-W7", identifier_type="primary")
            ]
        )
        
        context = demographics.to_template_context()
        
        assert context['display_name'] == "Diana Ferreira"
        assert context['formatted_birth_date'] == "08/05/1982"
        assert context['demographics']['given_name'] == "Diana"
        assert context['demographics']['family_name'] == "Ferreira"
        assert context['primary_identifier']['extension'] == "2-1234-W7"
        assert context['is_female'] is True
        assert context['is_male'] is False
    
    def test_to_legacy_context(self):
        """Test legacy context creation for backward compatibility"""
        demographics = PatientDemographics(
            given_name="Diana",
            family_name="Ferreira",
            birth_date="19820508",
            gender="Female",
            identifiers=[
                PatientIdentifier(extension="2-1234-W7", root="test.root")
            ]
        )
        
        legacy_context = demographics.to_legacy_context()
        
        assert legacy_context['given_name'] == "Diana"
        assert legacy_context['family_name'] == "Ferreira"
        assert legacy_context['birth_date'] == "19820508"
        assert legacy_context['gender'] == "Female"
        assert legacy_context['primary_identifier_extension'] == "2-1234-W7"
        assert legacy_context['primary_identifier_root'] == "test.root"
    
    def test_from_session_data(self):
        """Test creating demographics from session data"""
        session_data = {
            'given_name': 'Diana',
            'family_name': 'Ferreira',
            'birth_date': '19820508',
            'gender': 'F',
            'patient_id': '1444715089',
            'patient_identifiers': [
                {
                    'extension': '2-1234-W7',
                    'root': '2.16.17.710.804.1000.990.1',
                    'assigning_authority_name': 'SNS'
                }
            ],
            'address': {'city': 'Porto', 'country': 'Portugal'},
            'phone': '+351123456789'
        }
        
        demographics = PatientDemographics.from_session_data(session_data)
        
        assert demographics.given_name == "Diana"
        assert demographics.family_name == "Ferreira"
        assert demographics.birth_date == "19820508"
        assert demographics.gender == "Female"
        assert demographics.patient_id == "1444715089"
        assert len(demographics.identifiers) == 1
        assert demographics.identifiers[0].extension == "2-1234-W7"
        assert demographics.address['city'] == 'Porto'
        assert demographics.phone == '+351123456789'


class TestPatientDemographicsService:
    """Test PatientDemographicsService functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = PatientDemographicsService()
        
        # Sample CDA XML for Diana Ferreira
        self.diana_cda_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <ClinicalDocument xmlns="urn:hl7-org:v3">
            <recordTarget>
                <patientRole>
                    <id extension="2-1234-W7" root="2.16.17.710.804.1000.990.1" assigningAuthorityName="SNS"/>
                    <patient>
                        <name>
                            <given>Diana</given>
                            <family>Ferreira</family>
                        </name>
                        <administrativeGenderCode code="F"/>
                        <birthTime value="19820508"/>
                    </patient>
                </patientRole>
            </recordTarget>
        </ClinicalDocument>"""
    
    def test_extract_from_cda_xml_diana_ferreira(self):
        """Test extracting Diana Ferreira from CDA XML"""
        xml_root = ET.fromstring(self.diana_cda_xml)
        
        demographics = self.service.extract_from_cda_xml(xml_root)
        
        assert demographics.given_name == "Diana"
        assert demographics.family_name == "Ferreira"
        assert demographics.birth_date == "19820508"
        assert demographics.gender == "Female"
        assert len(demographics.identifiers) == 1
        assert demographics.identifiers[0].extension == "2-1234-W7"
        assert demographics.identifiers[0].root == "2.16.17.710.804.1000.990.1"
        assert demographics.identifiers[0].assigning_authority_name == "SNS"
    
    def test_extract_from_cda_xml_no_patient_role(self):
        """Test extraction with no patientRole element"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <ClinicalDocument xmlns="urn:hl7-org:v3">
        </ClinicalDocument>"""
        
        xml_root = ET.fromstring(xml_content)
        demographics = self.service.extract_from_cda_xml(xml_root)
        
        assert demographics.given_name == "Unknown"
        assert demographics.family_name == "Unknown"
        assert demographics.birth_date == ""
        assert demographics.gender == "Unknown"
        assert demographics.identifiers == []
    
    def test_extract_from_fhir_bundle(self):
        """Test extracting patient from FHIR bundle"""
        fhir_bundle = {
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "diana-ferreira",
                        "identifier": [
                            {
                                "value": "2-1234-W7",
                                "system": "http://sns.pt",
                                "assigner": {"display": "SNS"}
                            }
                        ],
                        "name": [
                            {
                                "given": ["Diana"],
                                "family": "Ferreira"
                            }
                        ],
                        "gender": "female",
                        "birthDate": "1982-05-08"
                    }
                }
            ]
        }
        
        demographics = self.service.extract_from_fhir_bundle(fhir_bundle)
        
        assert demographics.given_name == "Diana"
        assert demographics.family_name == "Ferreira"
        assert demographics.birth_date == "1982-05-08"
        assert demographics.gender == "Female"
        assert demographics.patient_id == "diana-ferreira"
        assert len(demographics.identifiers) == 1
        assert demographics.identifiers[0].extension == "2-1234-W7"
    
    def test_extract_from_fhir_bundle_no_patient(self):
        """Test extraction with no Patient resource"""
        fhir_bundle = {"entry": []}
        
        demographics = self.service.extract_from_fhir_bundle(fhir_bundle)
        
        assert demographics.given_name == "Unknown"
        assert demographics.family_name == "Unknown"
    
    def test_extract_from_session_data(self):
        """Test extracting from session data"""
        session_data = {
            'given_name': 'Diana',
            'family_name': 'Ferreira',
            'birth_date': '19820508',
            'gender': 'F',
            'patient_identifiers': [
                {'extension': '2-1234-W7', 'root': '2.16.17.710.804.1000.990.1'}
            ]
        }
        
        demographics = self.service.extract_from_session_data(session_data)
        
        assert demographics.given_name == "Diana"
        assert demographics.family_name == "Ferreira"
        assert demographics.birth_date == "19820508"
        assert demographics.gender == "Female"
    
    def test_create_unified_template_context(self):
        """Test creating unified template context"""
        demographics = PatientDemographics(
            given_name="Diana",
            family_name="Ferreira",
            birth_date="19820508",
            gender="Female",
            identifiers=[PatientIdentifier(extension="2-1234-W7")]
        )
        
        context = self.service.create_unified_template_context(demographics)
        
        # Check unified structure
        assert 'patient' in context
        assert context['patient']['display_name'] == "Diana Ferreira"
        assert context['patient']['formatted_birth_date'] == "08/05/1982"
        
        # Check backward compatibility aliases
        assert 'patient_data' in context
        assert 'patient_information' in context
        assert 'patient_identity' in context
        assert context['patient_display_name'] == "Diana Ferreira"
    
    def test_create_template_context_without_legacy(self):
        """Test creating template context without legacy aliases"""
        demographics = PatientDemographics(given_name="Diana", family_name="Ferreira")
        
        context = self.service.create_template_context(demographics, include_legacy=False)
        
        assert 'patient' in context
        assert 'patient_data' not in context
        assert 'patient_information' not in context
        assert 'patient_identity' not in context
    
    def test_normalize_gender_mappings(self):
        """Test gender normalization mappings"""
        assert self.service._normalize_gender("F") == "Female"
        assert self.service._normalize_gender("M") == "Male"
        assert self.service._normalize_gender("feminino") == "Female"
        assert self.service._normalize_gender("masculino") == "Male"
        assert self.service._normalize_gender("unknown") == "Unknown"
        assert self.service._normalize_gender("other") == "Other"
    
    def test_validate_demographics_complete(self):
        """Test validating complete demographics"""
        demographics = PatientDemographics(
            given_name="Diana",
            family_name="Ferreira",
            birth_date="19820508",
            gender="Female",
            identifiers=[PatientIdentifier(extension="2-1234-W7")]
        )
        
        validation = self.service.validate_demographics(demographics)
        
        assert validation['is_valid'] is True
        assert len(validation['errors']) == 0
        assert len(validation['warnings']) == 0
    
    def test_validate_demographics_missing_fields(self):
        """Test validating demographics with missing fields"""
        demographics = PatientDemographics()  # All defaults (Unknown values)
        
        validation = self.service.validate_demographics(demographics)
        
        assert validation['is_valid'] is False
        assert "No patient identifiers found" in validation['errors']
        assert "Given name is unknown" in validation['warnings']
        assert "Family name is unknown" in validation['warnings']
        assert "Birth date is missing" in validation['warnings']
        assert "Gender is unknown" in validation['warnings']
    
    def test_validate_demographics_invalid_identifier(self):
        """Test validating demographics with invalid identifier"""
        demographics = PatientDemographics(
            given_name="Diana",
            family_name="Ferreira",
            identifiers=[PatientIdentifier(extension="")]  # This should raise error in __post_init__
        )
        
        # This should raise an error during PatientIdentifier creation
        with pytest.raises(ValueError):
            PatientIdentifier(extension="")
    
    def test_get_extraction_statistics(self):
        """Test getting extraction statistics"""
        stats = self.service.get_extraction_statistics()
        
        assert isinstance(stats, dict)
        assert 'cda_extractions' in stats
        assert 'fhir_extractions' in stats
        assert 'session_conversions' in stats
        assert 'extraction_errors' in stats


class TestIntegrationWithDianaFerreiraSession:
    """Integration tests using actual Diana Ferreira session data structure"""
    
    def setup_method(self):
        """Set up with Diana Ferreira session data"""
        self.service = PatientDemographicsService()
        
        # Actual session data structure for Diana Ferreira (session 1444715089)
        self.diana_session_data = {
            'given_name': 'Diana',
            'family_name': 'Ferreira',
            'birth_date': '19820508',
            'gender': 'F',
            'patient_id': '1444715089',
            'patient_identifiers': [
                {
                    'extension': '2-1234-W7',
                    'root': '2.16.17.710.804.1000.990.1',
                    'assigning_authority_name': 'SNS'
                }
            ]
        }
    
    def test_diana_ferreira_session_conversion(self):
        """Test converting Diana Ferreira session data"""
        demographics = self.service.extract_from_session_data(self.diana_session_data)
        
        assert demographics.get_display_name() == "Diana Ferreira"
        assert demographics.get_formatted_birth_date() == "08/05/1982"
        assert demographics.gender == "Female"
        assert demographics.patient_id == "1444715089"
        
        primary_id = demographics.get_primary_identifier()
        assert primary_id is not None
        assert primary_id.extension == "2-1234-W7"
        assert primary_id.root == "2.16.17.710.804.1000.990.1"
        assert primary_id.assigning_authority_name == "SNS"
    
    def test_diana_ferreira_template_context(self):
        """Test creating template context for Diana Ferreira"""
        demographics = self.service.extract_from_session_data(self.diana_session_data)
        context = self.service.create_unified_template_context(demographics)
        
        # Test unified structure
        patient = context['patient']
        assert patient['display_name'] == "Diana Ferreira"
        assert patient['formatted_birth_date'] == "08/05/1982"
        assert patient['demographics']['given_name'] == "Diana"
        assert patient['demographics']['family_name'] == "Ferreira"
        assert patient['demographics']['gender'] == "Female"
        assert patient['is_female'] is True
        assert patient['is_male'] is False
        
        # Test backward compatibility
        assert context['patient_data']['given_name'] == "Diana"
        assert context['patient_information']['family_name'] == "Ferreira"
        assert context['patient_identity']['birth_date'] == "19820508"
        assert context['patient_display_name'] == "Diana Ferreira"
    
    def test_diana_ferreira_age_calculation(self):
        """Test age calculation for Diana Ferreira"""
        demographics = self.service.extract_from_session_data(self.diana_session_data)
        
        # Test age calculation at a known date
        reference_date = datetime(2024, 12, 19)
        age = demographics.get_age_at_date(reference_date)
        
        # Diana was born on 1982-05-08, so on 2024-12-19 she should be 42
        assert age == 42
    
    def test_diana_ferreira_validation(self):
        """Test validation of Diana Ferreira demographics"""
        demographics = self.service.extract_from_session_data(self.diana_session_data)
        validation = self.service.validate_demographics(demographics)
        
        assert validation['is_valid'] is True
        assert len(validation['errors']) == 0
        # Should have no warnings since all fields are complete
        assert len(validation['warnings']) == 0


# Additional test fixtures and helpers

@pytest.fixture
def sample_cda_xml():
    """Sample CDA XML for testing"""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <ClinicalDocument xmlns="urn:hl7-org:v3">
        <recordTarget>
            <patientRole>
                <id extension="123456789" root="2.16.840.1.113883.2.9.4.3.2"/>
                <patient>
                    <name>
                        <given>Test</given>
                        <family>Patient</family>
                    </name>
                    <administrativeGenderCode code="M"/>
                    <birthTime value="19900101"/>
                </patient>
            </patientRole>
        </recordTarget>
    </ClinicalDocument>"""


@pytest.fixture
def sample_fhir_bundle():
    """Sample FHIR bundle for testing"""
    return {
        "resourceType": "Bundle",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "test-patient",
                    "identifier": [
                        {
                            "value": "123456789",
                            "system": "http://test.system"
                        }
                    ],
                    "name": [
                        {
                            "given": ["Test"],
                            "family": "Patient"
                        }
                    ],
                    "gender": "male",
                    "birthDate": "1990-01-01"
                }
            }
        ]
    }


# Performance and stress tests

class TestPerformance:
    """Performance tests for patient demographics service"""
    
    def test_large_identifier_list_performance(self):
        """Test performance with large number of identifiers"""
        identifiers = [
            PatientIdentifier(extension=f"ID-{i}", identifier_type="secondary")
            for i in range(100)
        ]
        
        demographics = PatientDemographics(
            given_name="Test",
            family_name="Patient",
            identifiers=identifiers
        )
        
        # Should handle large identifier lists efficiently
        primary_id = demographics.get_primary_identifier()
        assert primary_id.extension == "ID-0"  # First one becomes primary
        
        all_ids = demographics.get_all_identifiers_display()
        assert len(all_ids) == 100
    
    def test_context_creation_performance(self):
        """Test template context creation performance"""
        service = PatientDemographicsService()
        
        demographics = PatientDemographics(
            given_name="Performance",
            family_name="Test",
            birth_date="19900101",
            gender="Male",
            identifiers=[PatientIdentifier(extension="PERF-123")]
        )
        
        # Should create context efficiently
        context = service.create_unified_template_context(demographics)
        
        assert 'patient' in context
        assert 'patient_data' in context
        assert 'patient_information' in context
        assert 'patient_identity' in context