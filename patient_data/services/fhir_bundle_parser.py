"""
FHIR Bundle Parser Service
Enhanced FHIR R4 Patient Summary Bundle processing for Django NCP

This service parses FHIR Patient Summary Bundles and extracts clinical sections
to feed into existing Django NCP view functions, similar to the CDA parser
but with enhanced FHIR capabilities.

Key Features:
- Direct FHIR R4 resource processing (no CDA conversion)
- Clinical sections extraction for existing UI templates
- Enhanced data structure with FHIR resource references
- Support for EPSOS Patient Summary compliance
- Integration with existing enhanced_patient_cda.html template
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

logger = logging.getLogger("ehealth")


@dataclass
class FHIRClinicalSection:
    """Represents a clinical section extracted from FHIR Bundle"""
    section_type: str
    section_title: str
    entry_count: int
    entries: List[Dict[str, Any]]
    fhir_resource_type: str
    section_code: Optional[str] = None
    display_name: Optional[str] = None
    has_structured_data: bool = True


class FHIRBundleParser:
    """
    Advanced FHIR Bundle Parser for Patient Summary processing
    
    Extracts clinical sections from FHIR R4 Patient Summary Bundle
    to feed into existing Django NCP view functions and templates.
    """
    
    def __init__(self):
        self.supported_resource_types = [
            'Patient', 'Composition', 'AllergyIntolerance', 'MedicationStatement',
            'Condition', 'Procedure', 'Observation', 'Immunization', 
            'DiagnosticReport', 'Practitioner', 'Organization', 'Device'
        ]
        
        # Clinical section mapping for UI consistency
        self.section_mapping = {
            'Patient': {
                'section_type': 'patient_info',
                'display_name': 'Patient Information',
                'icon': 'fa-user'
            },
            'AllergyIntolerance': {
                'section_type': 'allergies',
                'display_name': 'Allergies and Intolerances',
                'icon': 'fa-exclamation-triangle'
            },
            'MedicationStatement': {
                'section_type': 'medications',
                'display_name': 'Current Medications',
                'icon': 'fa-pills'
            },
            'Condition': {
                'section_type': 'conditions',
                'display_name': 'Medical Conditions',
                'icon': 'fa-stethoscope'
            },
            'Procedure': {
                'section_type': 'procedures',
                'display_name': 'Medical Procedures',
                'icon': 'fa-procedures'
            },
            'Observation': {
                'section_type': 'observations',
                'display_name': 'Vital Signs & Observations',
                'icon': 'fa-chart-line'
            },
            'Immunization': {
                'section_type': 'immunizations',
                'display_name': 'Immunizations',
                'icon': 'fa-syringe'
            },
            'DiagnosticReport': {
                'section_type': 'diagnostic_reports',
                'display_name': 'Laboratory Results',
                'icon': 'fa-flask'
            },
            'Device': {
                'section_type': 'medical_devices',
                'display_name': 'Medical Devices',
                'icon': 'fa-microchip'
            }
        }
    
    def parse_patient_summary_bundle(self, fhir_bundle: Union[Dict, str]) -> Dict[str, Any]:
        """
        Parse FHIR Patient Summary Bundle into clinical sections structure
        
        Returns structure compatible with existing enhanced_patient_cda.html template
        
        Args:
            fhir_bundle: FHIR Bundle as dict or JSON string
            
        Returns:
            Clinical sections structure for Django templates
        """
        try:
            # Handle JSON string input
            if isinstance(fhir_bundle, str):
                fhir_bundle = json.loads(fhir_bundle)
            
            # Validate bundle structure
            if not self._validate_fhir_bundle(fhir_bundle):
                raise ValueError("Invalid FHIR Bundle structure")
            
            # Extract resources by type
            resources_by_type = self._group_resources_by_type(fhir_bundle)
            
            # Parse each resource type into clinical sections
            clinical_sections = {}
            section_summary = {}
            
            for resource_type, resources in resources_by_type.items():
                if resource_type in self.section_mapping:
                    section_info = self.section_mapping[resource_type]
                    
                    # Parse resources into structured clinical section
                    clinical_section = self._parse_clinical_section(
                        resource_type, resources, section_info
                    )
                    
                    clinical_sections[section_info['section_type']] = clinical_section
                    
                    # Create section summary for template
                    section_summary[section_info['section_type']] = {
                        'title': section_info['display_name'],
                        'count': clinical_section.entry_count,
                        'has_entries': clinical_section.entry_count > 0,
                        'icon': section_info['icon'],
                        'resource_type': resource_type
                    }
            
            # Extract patient identity for UI
            patient_identity = self._extract_patient_identity(
                resources_by_type.get('Patient', [])
            )
            
            # Create enhanced sections structure (compatible with existing views)
            enhanced_sections = {
                'success': True,
                'data_source': 'FHIR Patient Summary Bundle',
                'sections': list(clinical_sections.values()),
                'sections_count': len(clinical_sections),
                'content_type': 'FHIR',
                'patient_identity': patient_identity,
                'section_summary': section_summary,
                'bundle_metadata': {
                    'resource_count': sum(len(resources) for resources in resources_by_type.values()),
                    'bundle_type': fhir_bundle.get('type', 'unknown'),
                    'bundle_id': fhir_bundle.get('id', 'unknown'),
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'supported_resources': list(resources_by_type.keys())
                }
            }
            
            logger.info(f"FHIR Bundle parsed successfully: {len(clinical_sections)} sections, {enhanced_sections['bundle_metadata']['resource_count']} resources")
            
            return enhanced_sections
            
        except Exception as e:
            logger.error(f"Error parsing FHIR Bundle: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data_source': 'FHIR Patient Summary Bundle',
                'sections': [],
                'sections_count': 0,
                'content_type': 'FHIR_ERROR'
            }
    
    def _validate_fhir_bundle(self, bundle: Dict[str, Any]) -> bool:
        """Validate basic FHIR Bundle structure"""
        return (
            isinstance(bundle, dict) and
            bundle.get('resourceType') == 'Bundle' and
            'entry' in bundle and
            isinstance(bundle['entry'], list)
        )
    
    def _group_resources_by_type(self, fhir_bundle: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Group FHIR resources by resourceType"""
        resources_by_type = {}
        
        for entry in fhir_bundle.get('entry', []):
            # Handle nested arrays (like in your EPSOS data)
            if isinstance(entry, list):
                for sub_entry in entry:
                    self._add_resource_to_group(sub_entry, resources_by_type)
            else:
                self._add_resource_to_group(entry, resources_by_type)
        
        return resources_by_type
    
    def _add_resource_to_group(self, entry: Dict, resources_by_type: Dict[str, List]):
        """Add a single resource to the grouped collection"""
        resource = entry.get('resource', {})
        resource_type = resource.get('resourceType')
        
        if resource_type and resource_type in self.supported_resource_types:
            if resource_type not in resources_by_type:
                resources_by_type[resource_type] = []
            resources_by_type[resource_type].append(resource)
    
    def _parse_clinical_section(self, resource_type: str, resources: List[Dict], section_info: Dict) -> FHIRClinicalSection:
        """Parse specific resource type into clinical section"""
        
        parsed_entries = []
        
        if resource_type == 'Patient':
            parsed_entries = [self._parse_patient_resource(resource) for resource in resources]
        elif resource_type == 'AllergyIntolerance':
            parsed_entries = [self._parse_allergy_resource(resource) for resource in resources]
        elif resource_type == 'MedicationStatement':
            parsed_entries = [self._parse_medication_resource(resource) for resource in resources]
        elif resource_type == 'Condition':
            parsed_entries = [self._parse_condition_resource(resource) for resource in resources]
        elif resource_type == 'Procedure':
            parsed_entries = [self._parse_procedure_resource(resource) for resource in resources]
        elif resource_type == 'Observation':
            parsed_entries = [self._parse_observation_resource(resource) for resource in resources]
        elif resource_type == 'Immunization':
            parsed_entries = [self._parse_immunization_resource(resource) for resource in resources]
        elif resource_type == 'DiagnosticReport':
            parsed_entries = [self._parse_diagnostic_report_resource(resource) for resource in resources]
        elif resource_type == 'Device':
            parsed_entries = [self._parse_device_resource(resource) for resource in resources]
        else:
            # Generic resource parsing
            parsed_entries = [self._parse_generic_resource(resource) for resource in resources]
        
        return FHIRClinicalSection(
            section_type=section_info['section_type'],
            section_title=section_info['display_name'],
            entry_count=len(parsed_entries),
            entries=parsed_entries,
            fhir_resource_type=resource_type,
            display_name=section_info['display_name']
        )
    
    def _parse_patient_resource(self, patient: Dict[str, Any]) -> Dict[str, Any]:
        """Parse FHIR Patient resource"""
        # Extract patient name
        name_parts = []
        names = patient.get('name', [])
        if names:
            name = names[0]
            if name.get('given'):
                name_parts.extend(name['given'])
            if name.get('family'):
                name_parts.append(name['family'])
        
        # Extract address
        address_parts = []
        addresses = patient.get('address', [])
        if addresses:
            address = addresses[0]
            if address.get('line'):
                address_parts.extend(address['line'])
            for field in ['city', 'postalCode', 'country']:
                if address.get(field):
                    address_parts.append(address[field])
        
        # Extract telecom
        phone = None
        email = None
        for telecom in patient.get('telecom', []):
            if telecom.get('system') == 'phone':
                phone = telecom.get('value')
            elif telecom.get('system') == 'email':
                email = telecom.get('value')
        
        return {
            'id': patient.get('id'),
            'name': ' '.join(name_parts) if name_parts else 'Unknown Patient',
            'gender': patient.get('gender', 'Unknown').capitalize(),
            'birth_date': patient.get('birthDate', 'Unknown'),
            'address': ', '.join(address_parts) if address_parts else 'No address provided',
            'phone': phone,
            'email': email,
            'identifiers': patient.get('identifier', []),
            'resource_type': 'Patient',
            'display_text': f"Patient: {' '.join(name_parts) if name_parts else 'Unknown'}"
        }
    
    def _parse_allergy_resource(self, allergy: Dict[str, Any]) -> Dict[str, Any]:
        """Parse FHIR AllergyIntolerance resource"""
        # Extract allergen
        code = allergy.get('code', {})
        allergen = 'Unknown allergen'
        if code.get('coding'):
            coding = code['coding'][0]
            allergen = coding.get('display', coding.get('code', 'Unknown allergen'))
        elif code.get('text'):
            allergen = code['text']
        
        # Extract clinical status
        clinical_status = 'Unknown'
        if allergy.get('clinicalStatus', {}).get('coding'):
            clinical_status = allergy['clinicalStatus']['coding'][0].get('display', 'Unknown')
        
        # Extract verification status
        verification_status = 'Unknown'
        if allergy.get('verificationStatus', {}).get('coding'):
            verification_status = allergy['verificationStatus']['coding'][0].get('display', 'Unknown')
        
        # Extract severity and reactions
        reactions = []
        for reaction in allergy.get('reaction', []):
            severity = reaction.get('severity', 'Unknown')
            manifestation_text = 'Unknown reaction'
            if reaction.get('manifestation'):
                manifestation = reaction['manifestation'][0]
                if manifestation.get('coding'):
                    manifestation_text = manifestation['coding'][0].get('display', 'Unknown reaction')
                elif manifestation.get('text'):
                    manifestation_text = manifestation['text']
            
            reactions.append({
                'severity': severity,
                'manifestation': manifestation_text
            })
        
        return {
            'id': allergy.get('id'),
            'allergen': allergen,
            'clinical_status': clinical_status,
            'verification_status': verification_status,
            'type': allergy.get('type', 'Unknown'),
            'category': allergy.get('category', ['Unknown'])[0] if allergy.get('category') else 'Unknown',
            'reactions': reactions,
            'onset_date': allergy.get('onsetDateTime', 'Unknown'),
            'resource_type': 'AllergyIntolerance',
            'display_text': f"Allergy: {allergen} ({clinical_status})"
        }
    
    def _parse_medication_resource(self, medication: Dict[str, Any]) -> Dict[str, Any]:
        """Parse FHIR MedicationStatement resource"""
        # Extract medication name
        medication_name = 'Unknown medication'
        if medication.get('medicationReference', {}).get('display'):
            medication_name = medication['medicationReference']['display']
        elif medication.get('medicationCodeableConcept', {}).get('text'):
            medication_name = medication['medicationCodeableConcept']['text']
        elif medication.get('medicationCodeableConcept', {}).get('coding'):
            coding = medication['medicationCodeableConcept']['coding'][0]
            medication_name = coding.get('display', coding.get('code', 'Unknown medication'))
        
        # Extract dosage information
        dosage_text = 'No dosage information'
        dosages = medication.get('dosage', [])
        if dosages:
            dosage = dosages[0]
            if dosage.get('text'):
                dosage_text = dosage['text']
            elif dosage.get('doseAndRate'):
                dose_rate = dosage['doseAndRate'][0]
                if dose_rate.get('doseQuantity'):
                    dose_qty = dose_rate['doseQuantity']
                    dosage_text = f"{dose_qty.get('value', '')} {dose_qty.get('unit', '')}"
        
        # Extract status and effective period
        status = medication.get('status', 'Unknown')
        effective_period = 'Unknown period'
        if medication.get('effectivePeriod'):
            period = medication['effectivePeriod']
            start = period.get('start', 'Unknown start')
            end = period.get('end', 'Ongoing')
            effective_period = f"{start} to {end}"
        
        return {
            'id': medication.get('id'),
            'medication_name': medication_name,
            'status': status.capitalize(),
            'dosage': dosage_text,
            'effective_period': effective_period,
            'taken': medication.get('taken', 'Unknown'),
            'resource_type': 'MedicationStatement',
            'display_text': f"Medication: {medication_name} ({status})"
        }
    
    def _parse_condition_resource(self, condition: Dict[str, Any]) -> Dict[str, Any]:
        """Parse FHIR Condition resource"""
        # Extract condition name
        code = condition.get('code', {})
        condition_name = 'Unknown condition'
        if code.get('coding'):
            coding = code['coding'][0]
            condition_name = coding.get('display', coding.get('code', 'Unknown condition'))
        elif code.get('text'):
            condition_name = code['text']
        
        # Extract clinical status
        clinical_status = 'Unknown'
        if condition.get('clinicalStatus', {}).get('coding'):
            clinical_status = condition['clinicalStatus']['coding'][0].get('display', 'Unknown')
        
        # Extract verification status
        verification_status = 'Unknown'
        if condition.get('verificationStatus', {}).get('coding'):
            verification_status = condition['verificationStatus']['coding'][0].get('display', 'Unknown')
        
        # Extract category
        category = 'Unknown'
        if condition.get('category'):
            cat = condition['category'][0]
            if cat.get('coding'):
                category = cat['coding'][0].get('display', 'Unknown')
            elif cat.get('text'):
                category = cat['text']
        
        return {
            'id': condition.get('id'),
            'condition_name': condition_name,
            'clinical_status': clinical_status,
            'verification_status': verification_status,
            'category': category,
            'severity': condition.get('severity', {}).get('coding', [{}])[0].get('display', 'Unknown'),
            'onset_date': condition.get('onsetDateTime', condition.get('onsetString', 'Unknown')),
            'resource_type': 'Condition',
            'display_text': f"Condition: {condition_name} ({clinical_status})"
        }
    
    def _parse_procedure_resource(self, procedure: Dict[str, Any]) -> Dict[str, Any]:
        """Parse FHIR Procedure resource"""
        # Extract procedure name
        code = procedure.get('code', {})
        procedure_name = 'Unknown procedure'
        if code.get('coding'):
            coding = code['coding'][0]
            procedure_name = coding.get('display', coding.get('code', 'Unknown procedure'))
        elif code.get('text'):
            procedure_name = code['text']
        
        # Extract status and performed date
        status = procedure.get('status', 'Unknown')
        performed_date = 'Unknown date'
        if procedure.get('performedDateTime'):
            performed_date = procedure['performedDateTime']
        elif procedure.get('performedPeriod', {}).get('start'):
            performed_date = procedure['performedPeriod']['start']
        
        return {
            'id': procedure.get('id'),
            'procedure_name': procedure_name,
            'status': status.capitalize(),
            'performed_date': performed_date,
            'category': procedure.get('category', {}).get('coding', [{}])[0].get('display', 'Unknown'),
            'resource_type': 'Procedure',
            'display_text': f"Procedure: {procedure_name} ({status})"
        }
    
    def _parse_observation_resource(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """Parse FHIR Observation resource"""
        # Extract observation name
        code = observation.get('code', {})
        observation_name = 'Unknown observation'
        if code.get('coding'):
            coding = code['coding'][0]
            observation_name = coding.get('display', coding.get('code', 'Unknown observation'))
        elif code.get('text'):
            observation_name = code['text']
        
        # Extract value
        value_text = 'No value'
        if observation.get('valueQuantity'):
            value_qty = observation['valueQuantity']
            value_text = f"{value_qty.get('value', '')} {value_qty.get('unit', '')}"
        elif observation.get('valueString'):
            value_text = observation['valueString']
        elif observation.get('valueCodeableConcept', {}).get('text'):
            value_text = observation['valueCodeableConcept']['text']
        
        return {
            'id': observation.get('id'),
            'observation_name': observation_name,
            'value': value_text,
            'status': observation.get('status', 'Unknown'),
            'effective_date': observation.get('effectiveDateTime', 'Unknown date'),
            'category': observation.get('category', [{}])[0].get('coding', [{}])[0].get('display', 'Unknown'),
            'resource_type': 'Observation',
            'display_text': f"Observation: {observation_name} = {value_text}"
        }
    
    def _parse_immunization_resource(self, immunization: Dict[str, Any]) -> Dict[str, Any]:
        """Parse FHIR Immunization resource"""
        # Extract vaccine name
        vaccine_code = immunization.get('vaccineCode', {})
        vaccine_name = 'Unknown vaccine'
        if vaccine_code.get('coding'):
            coding = vaccine_code['coding'][0]
            vaccine_name = coding.get('display', coding.get('code', 'Unknown vaccine'))
        elif vaccine_code.get('text'):
            vaccine_name = vaccine_code['text']
        
        return {
            'id': immunization.get('id'),
            'vaccine_name': vaccine_name,
            'status': immunization.get('status', 'Unknown'),
            'occurrence_date': immunization.get('occurrenceDateTime', 'Unknown date'),
            'lot_number': immunization.get('lotNumber', 'Unknown'),
            'route': immunization.get('route', {}).get('coding', [{}])[0].get('display', 'Unknown'),
            'resource_type': 'Immunization',
            'display_text': f"Vaccination: {vaccine_name}"
        }
    
    def _parse_diagnostic_report_resource(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Parse FHIR DiagnosticReport resource"""
        # Extract report name
        code = report.get('code', {})
        report_name = 'Unknown report'
        if code.get('coding'):
            coding = code['coding'][0]
            report_name = coding.get('display', coding.get('code', 'Unknown report'))
        elif code.get('text'):
            report_name = code['text']
        
        return {
            'id': report.get('id'),
            'report_name': report_name,
            'status': report.get('status', 'Unknown'),
            'effective_date': report.get('effectiveDateTime', 'Unknown date'),
            'category': report.get('category', [{}])[0].get('coding', [{}])[0].get('display', 'Unknown'),
            'conclusion': report.get('conclusion', 'No conclusion available'),
            'resource_type': 'DiagnosticReport',
            'display_text': f"Report: {report_name}"
        }
    
    def _parse_device_resource(self, device: Dict[str, Any]) -> Dict[str, Any]:
        """Parse FHIR Device resource"""
        device_name = device.get('deviceName', [{}])[0].get('name', 'Unknown device')
        if not device_name or device_name == 'Unknown device':
            device_name = device.get('type', {}).get('text', 'Unknown device')
        
        return {
            'id': device.get('id'),
            'device_name': device_name,
            'status': device.get('status', 'Unknown'),
            'manufacturer': device.get('manufacturer', 'Unknown'),
            'model_number': device.get('modelNumber', 'Unknown'),
            'serial_number': device.get('serialNumber', 'Unknown'),
            'resource_type': 'Device',
            'display_text': f"Device: {device_name}"
        }
    
    def _parse_generic_resource(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Parse generic FHIR resource"""
        resource_type = resource.get('resourceType', 'Unknown')
        resource_id = resource.get('id', 'Unknown')
        
        return {
            'id': resource_id,
            'resource_type': resource_type,
            'display_text': f"{resource_type}: {resource_id}",
            'raw_data': resource
        }
    
    def _extract_patient_identity(self, patient_resources: List[Dict]) -> Dict[str, Any]:
        """Extract patient identity information for UI display"""
        if not patient_resources:
            return {
                'given_name': 'Unknown',
                'family_name': 'Patient',
                'full_name': 'Unknown Patient',
                'birth_date': 'Unknown',
                'gender': 'Unknown'
            }
        
        patient = patient_resources[0]  # Use first patient resource
        
        # Extract name components
        given_name = 'Unknown'
        family_name = 'Patient'
        names = patient.get('name', [])
        if names:
            name = names[0]
            if name.get('given'):
                given_name = ' '.join(name['given'])
            if name.get('family'):
                family_name = name['family']
        
        return {
            'given_name': given_name,
            'family_name': family_name,
            'full_name': f"{given_name} {family_name}",
            'birth_date': patient.get('birthDate', 'Unknown'),
            'gender': patient.get('gender', 'Unknown').capitalize(),
            'patient_id': patient.get('id', 'Unknown')
        }


class FHIRBundleParserError(Exception):
    """Custom exception for FHIR Bundle parsing errors"""
    pass


# Service instance for dependency injection
fhir_bundle_parser = FHIRBundleParser()