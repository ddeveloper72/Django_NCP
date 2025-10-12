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
            
            # Extract extended patient information for Extended Patient Information tab
            administrative_data = self._extract_administrative_data(
                resources_by_type.get('Patient', []),
                resources_by_type.get('Composition', []),
                fhir_bundle
            )
            
            contact_data = self._extract_contact_data(
                resources_by_type.get('Patient', [])
            )
            
            healthcare_data = self._extract_healthcare_data(
                resources_by_type.get('Practitioner', []),
                resources_by_type.get('Organization', []),
                resources_by_type.get('Composition', [])
            )
            
            # Create clinical arrays for view compatibility
            clinical_arrays = self._create_clinical_arrays(clinical_sections)
            
            # Create enhanced sections structure (compatible with existing views)
            enhanced_sections = {
                'success': True,
                'data_source': 'FHIR Patient Summary Bundle',
                'sections': list(clinical_sections.values()),
                'sections_count': len(clinical_sections),
                'content_type': 'FHIR',
                'patient_identity': patient_identity,
                'patient_information': patient_identity,  # Alias for compatibility
                'patient_data': patient_identity,  # Additional alias for view compatibility
                'section_summary': section_summary,
                
                # Clinical arrays for template compatibility
                'clinical_arrays': clinical_arrays,
                
                # Extended patient information for Extended Patient Information tab
                'administrative_data': administrative_data,
                'contact_data': contact_data,
                'healthcare_data': healthcare_data,
                'patient_extended_data': {
                    'administrative': administrative_data,
                    'contact': contact_data,
                    'healthcare': healthcare_data,
                    'has_extended_data': bool(administrative_data or contact_data or healthcare_data)
                },
                
                'bundle_metadata': {
                    'resource_count': sum(len(resources) for resources in resources_by_type.values()),
                    'bundle_type': fhir_bundle.get('type', 'unknown'),
                    'bundle_id': fhir_bundle.get('id', 'unknown'),
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'supported_resources': list(resources_by_type.keys())
                }
            }
            
            logger.info(f"FHIR Bundle parsed successfully: {len(clinical_sections)} sections, {enhanced_sections['bundle_metadata']['resource_count']} resources")
            logger.info(f"Extended data extracted: admin={bool(administrative_data)}, contact={bool(contact_data)}, healthcare={bool(healthcare_data)}")
            
            return enhanced_sections
            
        except Exception as e:
            logger.error(f"Error parsing FHIR Bundle: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data_source': 'FHIR Patient Summary Bundle',
                'sections': [],
                'sections_count': 0,
                'content_type': 'FHIR_ERROR',
                'administrative_data': {},
                'contact_data': {},
                'healthcare_data': {},
                'patient_extended_data': {}
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
        """Parse FHIR AllergyIntolerance resource with support for negative assertions"""
        # Extract allergen with support for negative assertions
        code = allergy.get('code', {})
        allergen = 'Unknown allergen'
        is_negative_assertion = False
        
        if code.get('coding'):
            coding = code['coding'][0]
            code_value = coding.get('code', '')
            display = coding.get('display', coding.get('code', 'Unknown allergen'))
            
            # Check for negative assertion codes
            if code_value in ['no-allergy-info', 'no-known-allergies', 'no-drug-allergies']:
                is_negative_assertion = True
                allergen = display or 'No allergy information available'
            else:
                allergen = display
        elif code.get('text'):
            allergen = code['text']
        
        # Extract clinical status
        clinical_status = 'Unknown'
        if allergy.get('clinicalStatus', {}).get('coding'):
            clinical_status = allergy['clinicalStatus']['coding'][0].get('display', 'Unknown')
            if is_negative_assertion:
                clinical_status = 'Not applicable'
        
        # Extract verification status
        verification_status = 'Unknown'
        if allergy.get('verificationStatus', {}).get('coding'):
            verification_status = allergy['verificationStatus']['coding'][0].get('display', 'Unknown')
            if is_negative_assertion:
                verification_status = 'Not applicable'
        
        # Extract severity and reactions (only for actual allergies)
        reactions = []
        if not is_negative_assertion:
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
            'onset_date': allergy.get('onsetDateTime', 'Unknown') if not is_negative_assertion else 'Not applicable',
            'resource_type': 'AllergyIntolerance',
            'display_text': f"Allergy: {allergen} ({clinical_status})",
            'is_negative_assertion': is_negative_assertion
        }
    
    def _parse_medication_resource(self, medication: Dict[str, Any]) -> Dict[str, Any]:
        """Parse FHIR MedicationStatement resource with support for negative assertions"""
        # Extract medication name with support for negative assertions
        medication_name = 'Unknown medication'
        is_negative_assertion = False
        
        if medication.get('medicationReference', {}).get('display'):
            medication_name = medication['medicationReference']['display']
        elif medication.get('medicationCodeableConcept', {}).get('text'):
            medication_name = medication['medicationCodeableConcept']['text']
        elif medication.get('medicationCodeableConcept', {}).get('coding'):
            coding = medication['medicationCodeableConcept']['coding'][0]
            code = coding.get('code', '')
            display = coding.get('display', coding.get('code', 'Unknown medication'))
            
            # Check for negative assertion codes
            if code in ['no-medication-info', 'no-drug-therapy', 'no-current-medication']:
                is_negative_assertion = True
                medication_name = display or 'No medication information available'
            else:
                medication_name = display
        
        # Extract dosage information
        dosage_text = 'No dosage information'
        if not is_negative_assertion:
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
        else:
            dosage_text = 'Not applicable - no medication information'
        
        # Extract status and effective period
        status = medication.get('status', 'Unknown')
        if is_negative_assertion:
            status = 'No information available'
            
        effective_period = 'Unknown period'
        if not is_negative_assertion and medication.get('effectivePeriod'):
            period = medication['effectivePeriod']
            start = period.get('start', 'Unknown start')
            end = period.get('end', 'Ongoing')
            effective_period = f"{start} to {end}"
        elif is_negative_assertion:
            effective_period = 'Not applicable'

        return {
            'id': medication.get('id'),
            'medication_name': medication_name,
            'status': status.capitalize(),
            'dosage': dosage_text,
            'effective_period': effective_period,
            'taken': medication.get('taken', 'Unknown'),
            'resource_type': 'MedicationStatement',
            'display_text': f"Medication: {medication_name} ({status})",
            'is_negative_assertion': is_negative_assertion
        }
    
    def _parse_condition_resource(self, condition: Dict[str, Any]) -> Dict[str, Any]:
        """Parse FHIR Condition resource with support for negative assertions"""
        # Extract condition name with support for negative assertions
        code = condition.get('code', {})
        condition_name = 'Unknown condition'
        is_negative_assertion = False
        
        if code.get('coding'):
            coding = code['coding'][0]
            code_value = coding.get('code', '')
            display = coding.get('display', coding.get('code', 'Unknown condition'))
            
            # Check for negative assertion codes
            if code_value in ['no-problem-info', 'no-condition-info', 'no-known-problems']:
                is_negative_assertion = True
                condition_name = display or 'No condition information available'
            else:
                condition_name = display
        elif code.get('text'):
            condition_name = code['text']
        
        # Extract clinical status
        clinical_status = 'Unknown'
        if condition.get('clinicalStatus', {}).get('coding'):
            clinical_status = condition['clinicalStatus']['coding'][0].get('display', 'Unknown')
            if is_negative_assertion:
                clinical_status = 'Not applicable'
        
        # Extract verification status
        verification_status = 'Unknown'
        if condition.get('verificationStatus', {}).get('coding'):
            verification_status = condition['verificationStatus']['coding'][0].get('display', 'Unknown')
            if is_negative_assertion:
                verification_status = 'Not applicable'
        
        # Extract category (only for actual conditions)
        category = 'Unknown'
        if not is_negative_assertion and condition.get('category'):
            cat = condition['category'][0]
            if cat.get('coding'):
                category = cat['coding'][0].get('display', 'Unknown')
            elif cat.get('text'):
                category = cat['text']
        elif is_negative_assertion:
            category = 'Not applicable'
        
        # Extract severity (only for actual conditions)
        severity = 'Unknown'
        if not is_negative_assertion and condition.get('severity'):
            severity = condition.get('severity', {}).get('coding', [{}])[0].get('display', 'Unknown')
        elif is_negative_assertion:
            severity = 'Not applicable'
        
        # Extract onset date (only for actual conditions)
        onset_date = 'Unknown'
        if not is_negative_assertion:
            onset_date = condition.get('onsetDateTime', condition.get('onsetString', 'Unknown'))
        else:
            onset_date = 'Not applicable'

        return {
            'id': condition.get('id'),
            'condition_name': condition_name,
            'clinical_status': clinical_status,
            'verification_status': verification_status,
            'category': category,
            'severity': severity,
            'onset_date': onset_date,
            'resource_type': 'Condition',
            'display_text': f"Condition: {condition_name} ({clinical_status})",
            'is_negative_assertion': is_negative_assertion
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
    
    def _create_clinical_arrays(self, clinical_sections: Dict[str, Any]) -> Dict[str, List]:
        """Create clinical arrays structure for template compatibility"""
        clinical_arrays = {
            'medications': [],
            'allergies': [],
            'conditions': [],
            'problems': [],  # Alias for conditions
            'procedures': [],
            'observations': [],
            'vital_signs': [],  # Subset of observations
            'immunizations': [],
            'diagnostic_reports': [],
            'results': []  # Alias for diagnostic_reports
        }
        
        # Map clinical sections to arrays
        for section_type, section_data in clinical_sections.items():
            if section_type == 'medications' and hasattr(section_data, 'entries'):
                clinical_arrays['medications'] = section_data.entries
            elif section_type == 'allergies' and hasattr(section_data, 'entries'):
                clinical_arrays['allergies'] = section_data.entries
            elif section_type == 'conditions' and hasattr(section_data, 'entries'):
                clinical_arrays['conditions'] = section_data.entries
                clinical_arrays['problems'] = section_data.entries  # Alias
            elif section_type == 'procedures' and hasattr(section_data, 'entries'):
                clinical_arrays['procedures'] = section_data.entries
            elif section_type == 'observations' and hasattr(section_data, 'entries'):
                clinical_arrays['observations'] = section_data.entries
                # Filter for vital signs (basic implementation)
                clinical_arrays['vital_signs'] = [
                    obs for obs in section_data.entries 
                    if any(keyword in str(obs.get('code', {})).lower() 
                          for keyword in ['blood pressure', 'heart rate', 'temperature', 'weight', 'height'])
                ]
            elif section_type == 'immunizations' and hasattr(section_data, 'entries'):
                clinical_arrays['immunizations'] = section_data.entries
            elif section_type == 'diagnostic_reports' and hasattr(section_data, 'entries'):
                clinical_arrays['diagnostic_reports'] = section_data.entries
                clinical_arrays['results'] = section_data.entries  # Alias
        
        return clinical_arrays
    
    def _extract_patient_identity(self, patient_resources: List[Dict]) -> Dict[str, Any]:
        """Extract comprehensive patient identity information for UI display"""
        if not patient_resources:
            return {
                'given_name': 'Unknown',
                'family_name': 'Patient',
                'full_name': 'Unknown Patient',
                'birth_date': 'Unknown',
                'gender': 'Unknown',
                'patient_id': 'Unknown',
                'source_country': 'Unknown',
                'marital_status': 'Unknown',
                'deceased': False,
                'active': True,
                'preferred_language': 'Unknown',
                'patient_identifiers': []
            }
        
        patient = patient_resources[0]  # Use first patient resource
        
        # Extract name components with full FHIR R4 HumanName compliance
        given_name = 'Unknown'
        family_name = 'Patient'
        full_name = 'Unknown Patient'
        prefix = []
        suffix = []
        name_use = 'usual'  # Default use
        name_text = None
        name_period = {}
        
        names = patient.get('name', [])
        if names:
            # Use first name (primary name)
            name = names[0]
            
            # FHIR R4 HumanName standard fields
            name_use = name.get('use', 'usual')  # usual | official | temp | nickname | anonymous | old | maiden
            name_text = name.get('text')  # Text representation of the full name
            family_name = name.get('family', 'Patient')  # Family name (Surname)
            given_names = name.get('given', [])  # Given names array (includes middle names)
            prefix = name.get('prefix', [])  # Parts that come before the name
            suffix = name.get('suffix', [])  # Parts that come after the name  
            name_period = name.get('period', {})  # Time period when name was/is in use
            
            # Process given names
            if given_names:
                given_name = ' '.join(given_names)  # Combine all given names for display
            
            # Create full name from components if text not provided
            if name_text:
                full_name = name_text
            else:
                # Construct full name from components
                name_parts = []
                if prefix:
                    name_parts.extend(prefix)
                if given_names:
                    name_parts.extend(given_names)
                if family_name != 'Patient':
                    name_parts.append(family_name)
                if suffix:
                    name_parts.extend(suffix)
                full_name = ' '.join(name_parts) if name_parts else 'Unknown Patient'
        
        # Extract patient identifiers with full FHIR R4 Identifier compliance
        identifiers = patient.get('identifier', [])
        formatted_identifiers = []
        patient_id = 'Unknown'
        
        for identifier in identifiers:
            # Extract type as CodeableConcept
            identifier_type = identifier.get('type', {})
            type_text = 'Unknown'
            type_coding = []
            
            if identifier_type:
                # Get text representation
                type_text = identifier_type.get('text', 'Unknown')
                
                # If no text, try to get from coding
                if type_text == 'Unknown':
                    codings = identifier_type.get('coding', [])
                    if codings:
                        type_text = codings[0].get('display', codings[0].get('code', 'Unknown'))
                        type_coding = codings
            
            # Extract assigner organization
            assigner = identifier.get('assigner', {})
            assigner_display = 'Unknown'
            if assigner:
                assigner_display = assigner.get('display', assigner.get('reference', 'Unknown'))
            
            # FHIR R4 compliant identifier structure
            formatted_id = {
                # === FHIR R4 Standard Fields ===
                'use': identifier.get('use', 'usual'),  # usual | official | temp | secondary | old
                'type': {  # CodeableConcept
                    'text': type_text,
                    'coding': type_coding
                },
                'system': identifier.get('system', 'Unknown'),  # The namespace URI
                'value': identifier.get('value', 'Unknown'),  # The unique value
                'period': identifier.get('period', {}),  # Time period when valid
                'assigner': {  # Organization reference
                    'display': assigner_display,
                    'reference': assigner.get('reference', None)
                },
                
                # === Legacy Template Compatibility ===
                'type_text': type_text,  # For simple template access
                'assigner_display': assigner_display  # For simple template access
            }
            formatted_identifiers.append(formatted_id)
            
            # Use first identifier as primary patient ID
            if patient_id == 'Unknown':
                patient_id = identifier.get('value', 'Unknown')
        
        # Extract source country from address
        source_country = 'Unknown'
        addresses = patient.get('address', [])
        if addresses:
            address = addresses[0]  # Use first address
            country_code = address.get('country', 'Unknown')
            if country_code and country_code != 'Unknown':
                source_country = country_code  # Will be processed by country_name template filter
        
        # Extract marital status
        marital_status = 'Unknown'
        if patient.get('maritalStatus'):
            marital_status = patient['maritalStatus'].get('text', 
                patient['maritalStatus'].get('coding', [{}])[0].get('display', 'Unknown'))
        
        # Extract preferred language
        preferred_language = 'Unknown'
        communication = patient.get('communication', [])
        if communication:
            for comm in communication:
                if comm.get('preferred', False):
                    language = comm.get('language', {})
                    preferred_language = language.get('text', 
                        language.get('coding', [{}])[0].get('display', 'Unknown'))
                    break
            # If no preferred language found, use first available
            if preferred_language == 'Unknown' and communication:
                language = communication[0].get('language', {})
                preferred_language = language.get('text', 
                    language.get('coding', [{}])[0].get('display', 'Unknown'))
        
        # Extract birth date and format it properly
        birth_date = patient.get('birthDate', 'Unknown')
        if birth_date != 'Unknown' and birth_date:
            try:
                # Ensure consistent date formatting for UI
                from datetime import datetime
                if len(birth_date) == 10:  # YYYY-MM-DD format
                    # Keep the original format for now
                    pass
            except:
                birth_date = 'Unknown'
        
        return {
            # === Legacy/Template Compatibility Fields ===
            'given_name': given_name,
            'family_name': family_name,
            'full_name': full_name,
            'prefix': prefix,
            'suffix': suffix,
            
            # === FHIR R4 HumanName Compliant Fields ===
            'name': {
                'use': name_use,  # usual | official | temp | nickname | anonymous | old | maiden
                'text': name_text or full_name,  # Text representation of the full name
                'family': family_name,  # Family name (often called 'Surname')
                'given': names[0].get('given', []) if names else [],  # Given names array (includes middle names)
                'prefix': prefix,  # Parts that come before the name (array)
                'suffix': suffix,  # Parts that come after the name (array)
                'period': name_period  # Time period when name was/is in use
            },
            
            # === Additional Patient Data ===
            'birth_date': birth_date,
            'gender': patient.get('gender', 'Unknown').capitalize() if patient.get('gender') else 'Unknown',
            'patient_id': patient_id,
            'patient_identifiers': formatted_identifiers,
            'source_country': source_country,
            'marital_status': marital_status,
            'deceased': patient.get('deceasedBoolean', False),
            'deceased_date': patient.get('deceasedDateTime', None),
            'active': patient.get('active', True),
            'preferred_language': preferred_language,
            'multiple_birth': patient.get('multipleBirthBoolean', False),
            'multiple_birth_integer': patient.get('multipleBirthInteger', None)
        }
    
    def _extract_administrative_data(self, patient_resources: List[Dict], 
                                   composition_resources: List[Dict],
                                   fhir_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """Extract comprehensive administrative data for Extended Patient Information tab"""
        administrative_data = {}
        
        if patient_resources:
            patient = patient_resources[0]
            
            # Patient identifiers
            identifiers = patient.get('identifier', [])
            formatted_identifiers = []
            for identifier in identifiers:
                formatted_identifiers.append({
                    'system': identifier.get('system', 'Unknown'),
                    'value': identifier.get('value', 'Unknown'),
                    'type': identifier.get('type', {}).get('text', 'Unknown'),
                    'use': identifier.get('use', 'Unknown'),
                    'assigner': identifier.get('assigner', {}).get('display', 'Unknown')
                })
            
            # Extract communication preferences
            communication_prefs = []
            communications = patient.get('communication', [])
            for comm in communications:
                language = comm.get('language', {})
                language_text = language.get('text', '')
                if not language_text:
                    codings = language.get('coding', [])
                    if codings:
                        language_text = codings[0].get('display', codings[0].get('code', 'Unknown'))
                
                communication_prefs.append({
                    'language': language_text,
                    'preferred': comm.get('preferred', False)
                })
            
            # Extract marital status
            marital_status = 'Unknown'
            if patient.get('maritalStatus'):
                marital_status = patient['maritalStatus'].get('text', 
                    patient['maritalStatus'].get('coding', [{}])[0].get('display', 'Unknown'))
            
            # Patient administrative details
            administrative_data.update({
                'patient_identifiers': formatted_identifiers,
                'marital_status': marital_status,
                'communication': communication_prefs,
                'patient_languages': [cp['language'] for cp in communication_prefs],  # For template compatibility
                'deceased': patient.get('deceasedBoolean', False),
                'deceased_date': patient.get('deceasedDateTime', None),
                'multiple_birth': patient.get('multipleBirthBoolean', False),
                'multiple_birth_integer': patient.get('multipleBirthInteger', None),
                'active': patient.get('active', True),
                'birth_date': patient.get('birthDate', 'Unknown'),
                'gender': patient.get('gender', 'Unknown').capitalize() if patient.get('gender') else 'Unknown'
            })
            
            # Extract links to other patients (for family relationships)
            links = patient.get('link', [])
            formatted_links = []
            for link in links:
                formatted_links.append({
                    'other': link.get('other', {}),
                    'type': link.get('type', 'Unknown')
                })
            administrative_data['patient_links'] = formatted_links
            
            # Extract emergency contacts and guardians from patient.contact
            # and format them for the template's expected structure
            other_contacts = []
            contacts = patient.get('contact', [])
            for contact in contacts:
                # Extract relationship
                relationships = contact.get('relationship', [])
                relationship_text = 'Unknown'
                if relationships:
                    rel = relationships[0]
                    relationship_text = rel.get('text', '')
                    if not relationship_text:
                        codings = rel.get('coding', [])
                        if codings:
                            relationship_text = codings[0].get('display', codings[0].get('code', 'Unknown'))
                
                # Extract name
                name = contact.get('name', {})
                given_name = ' '.join(name.get('given', [])) if name.get('given') else ''
                family_name = name.get('family', '')
                
                # Extract telecom
                phone = ''
                email = ''
                fax = ''
                other_telecoms = []
                contact_telecoms = contact.get('telecom', [])
                for ct in contact_telecoms:
                    value = ct.get('value', '')
                    if value.startswith('tel:'):
                        value = value[4:]
                    elif value.startswith('mailto:'):
                        value = value[7:]
                    elif value.startswith('fax:'):
                        value = value[4:]
                    
                    system = ct.get('system', 'unknown')
                    if system == 'phone':
                        phone = value
                    elif system == 'email':
                        email = value
                    elif system == 'fax':
                        fax = value
                    else:
                        other_telecoms.append({
                            'system': system,
                            'value': value,
                            'use': ct.get('use', 'unknown')
                        })
                
                # Extract address
                address = contact.get('address', {})
                full_address = ''
                if address:
                    addr_parts = []
                    if address.get('line'):
                        addr_parts.extend(address['line'])
                    if address.get('city'):
                        addr_parts.append(address['city'])
                    if address.get('postalCode'):
                        addr_parts.append(address['postalCode'])
                    if address.get('country'):
                        addr_parts.append(address['country'])
                    full_address = ', '.join(addr_parts)
                
                other_contacts.append({
                    'given_name': given_name,
                    'family_name': family_name,
                    'relationship': relationship_text,
                    'contact_type': relationship_text,  # For template compatibility
                    'role': relationship_text,  # For template compatibility
                    'phone': phone,
                    'email': email,
                    'address': full_address,
                    'gender': contact.get('gender', 'Unknown'),
                    'organization': contact.get('organization', {}).get('display', '')
                })
            
            administrative_data['other_contacts'] = other_contacts
            
            # Extract guardian information (look for guardian relationship in contacts)
            guardian = None
            for contact in contacts:
                relationships = contact.get('relationship', [])
                for rel in relationships:
                    rel_text = rel.get('text', '').lower()
                    rel_code = ''
                    codings = rel.get('coding', [])
                    if codings:
                        rel_code = codings[0].get('code', '').lower()
                    
                    # Check if this contact is a guardian
                    if ('guardian' in rel_text or 'parent' in rel_text or 
                        'mother' in rel_text or 'father' in rel_text or
                        'next of kin' in rel_text or 'legal' in rel_text or
                        rel_code in ['guardian', 'parent', 'mother', 'father']):
                        
                        # Extract guardian details
                        name = contact.get('name', {})
                        given_name = ' '.join(name.get('given', [])) if name.get('given') else ''
                        family_name = name.get('family', '')
                        
                        # Extract relationship
                        relationship = rel.get('text', '')
                        if not relationship:
                            if codings:
                                relationship = codings[0].get('display', codings[0].get('code', 'Guardian'))
                        
                        # Extract contact info
                        contact_info = {
                            'addresses': [],
                            'telecoms': []
                        }
                        
                        # Guardian address
                        if contact.get('address'):
                            addr = contact['address']
                            contact_info['addresses'].append({
                                'street_lines': addr.get('line', []),
                                'city': addr.get('city'),
                                'state': addr.get('state'),
                                'postal_code': addr.get('postalCode'),
                                'country': addr.get('country'),
                                'full_address': self._format_address(addr)
                            })
                        
                        # Guardian telecom
                        for ct in contact.get('telecom', []):
                            value = ct.get('value', '')
                            if value.startswith('tel:'):
                                value = value[4:]
                            elif value.startswith('mailto:'):
                                value = value[7:]
                            
                            contact_info['telecoms'].append({
                                'system': ct.get('system', 'Unknown'),
                                'value': value,
                                'use': ct.get('use', 'Unknown'),
                                'display': self._format_telecom_display(ct)
                            })
                        
                        guardian = {
                            'given_name': given_name,
                            'family_name': family_name,
                            'relationship': relationship,
                            'role': relationship,  # For template compatibility
                            'contact_info': contact_info,
                            'gender': contact.get('gender', 'Unknown'),
                            'organization': contact.get('organization', {}).get('display', '')
                        }
                        break
                
                if guardian:
                    break
            
            administrative_data['guardian'] = guardian
        
        # Document metadata from Composition
        if composition_resources:
            composition = composition_resources[0]
            
            # Extract authors with more detail
            authors = []
            for author in composition.get('author', []):
                authors.append({
                    'reference': author.get('reference', ''),
                    'display': author.get('display', 'Unknown'),
                    'type': author.get('type', 'Unknown')
                })
            
            administrative_data.update({
                'document_id': composition.get('id', 'Unknown'),
                'document_title': composition.get('title', 'Patient Summary'),
                'document_status': composition.get('status', 'Unknown'),
                'document_date': composition.get('date', 'Unknown'),
                'document_type': composition.get('type', {}).get('text', 'Patient Summary'),
                'document_type_code': composition.get('type', {}).get('coding', [{}])[0].get('code', 'Unknown'),
                'custodian': composition.get('custodian', {}).get('display', 'Unknown'),
                'author': [author['display'] for author in authors],  # For template compatibility
                'authors': authors,  # Detailed author information
                'confidentiality': composition.get('confidentiality', 'Unknown'),
                'language': composition.get('language', 'Unknown')
            })
        
        # Bundle metadata
        administrative_data.update({
            'bundle_id': fhir_bundle.get('id', 'Unknown'),
            'bundle_type': fhir_bundle.get('type', 'Unknown'),
            'bundle_timestamp': fhir_bundle.get('timestamp', 'Unknown'),
            'bundle_total': fhir_bundle.get('total', 0),
            'bundle_identifier': fhir_bundle.get('identifier', {})
        })
        
        return administrative_data
    
    def _extract_contact_data(self, patient_resources: List[Dict]) -> Dict[str, Any]:
        """Extract comprehensive contact information for Extended Patient Information tab"""
        contact_data = {
            'addresses': [],
            'telecoms': [],
            'contacts': [],  # Emergency contacts, guardians, etc.
            'general_practitioner': [],
            'managing_organization': None
        }
        
        if not patient_resources:
            return contact_data
            
        patient = patient_resources[0]
        
        # Extract addresses with full FHIR R4 Address compliance
        addresses = patient.get('address', [])
        for address in addresses:
            # FHIR R4 Address standard fields
            address_lines = address.get('line', [])
            
            formatted_address = {
                # === FHIR R4 Standard Fields ===
                'use': address.get('use', 'home'),  # home | work | temp | old | billing
                'type': address.get('type', 'physical'),  # postal | physical | both
                'text': self._format_address_text(address),  # Text representation
                'line': address_lines,  # Street name, number, direction & P.O. Box (array)
                'city': address.get('city'),  # Name of city, town etc.
                'district': address.get('district'),  # District name (aka county)
                'state': address.get('state'),  # Sub-unit of country
                'postalCode': address.get('postalCode'),  # Postal code for area
                'country': address.get('country'),  # Country (ISO 3166 code)
                'period': address.get('period', {}),  # Time period when address was/is in use
                
                # === Template Compatibility Fields ===
                'street_lines': address_lines,  # Template expects 'street_lines'
                'street': ', '.join(address_lines) if address_lines else None,  # Combined street
                'postal_code': address.get('postalCode'),  # Snake_case for template
                'full_address': self._format_address(address)  # Complete formatted address
            }
            contact_data['addresses'].append(formatted_address)
        
        # Extract telecom information (phone, email, etc.)
        telecoms = patient.get('telecom', [])
        for telecom in telecoms:
            # Clean up tel: prefix and other system prefixes
            value = telecom.get('value', '')
            if value.startswith('tel:'):
                value = value[4:]  # Remove 'tel:' prefix
            elif value.startswith('mailto:'):
                value = value[7:]  # Remove 'mailto:' prefix
            elif value.startswith('fax:'):
                value = value[4:]  # Remove 'fax:' prefix
            
            formatted_telecom = {
                'system': telecom.get('system', 'Unknown'),
                'value': value,
                'use': telecom.get('use', 'Unknown'),
                'rank': telecom.get('rank', 1),
                'period': telecom.get('period', {}),
                'display': self._format_telecom_display(telecom)
            }
            contact_data['telecoms'].append(formatted_telecom)
        
        # Extract patient contacts (emergency contacts, guardians, next of kin)
        contacts = patient.get('contact', [])
        for contact in contacts:
            formatted_contact = {
                'relationship': [],
                'name': {},
                'telecom': [],
                'address': {},
                'gender': contact.get('gender', 'Unknown'),
                'organization': contact.get('organization', {}),
                'period': contact.get('period', {})
            }
            
            # Extract relationship types
            relationships = contact.get('relationship', [])
            for relationship in relationships:
                rel_text = relationship.get('text', '')
                if not rel_text:
                    # Try to get from coding
                    codings = relationship.get('coding', [])
                    if codings:
                        rel_text = codings[0].get('display', codings[0].get('code', 'Unknown'))
                formatted_contact['relationship'].append(rel_text)
            
            # Extract contact name
            if contact.get('name'):
                name = contact['name']
                formatted_contact['name'] = {
                    'given': ' '.join(name.get('given', [])),
                    'family': name.get('family', ''),
                    'full_name': f"{' '.join(name.get('given', []))} {name.get('family', '')}".strip(),
                    'prefix': name.get('prefix', []),
                    'suffix': name.get('suffix', [])
                }
            
            # Extract contact telecom
            contact_telecoms = contact.get('telecom', [])
            for ct in contact_telecoms:
                value = ct.get('value', '')
                if value.startswith('tel:'):
                    value = value[4:]
                elif value.startswith('mailto:'):
                    value = value[7:]
                
                formatted_contact['telecom'].append({
                    'system': ct.get('system', 'Unknown'),
                    'value': value,
                    'use': ct.get('use', 'Unknown')
                })
            
            # Extract contact address
            if contact.get('address'):
                addr = contact['address']
                formatted_contact['address'] = {
                    'street_lines': addr.get('line', []),
                    'city': addr.get('city'),
                    'state': addr.get('state'),
                    'postal_code': addr.get('postalCode'),
                    'country': addr.get('country'),
                    'full_address': self._format_address(addr)
                }
            
            contact_data['contacts'].append(formatted_contact)
        
        # Extract general practitioner references
        gp_refs = patient.get('generalPractitioner', [])
        for gp_ref in gp_refs:
            contact_data['general_practitioner'].append({
                'reference': gp_ref.get('reference', ''),
                'display': gp_ref.get('display', 'Unknown'),
                'type': gp_ref.get('type', 'Practitioner')
            })
        
        # Extract managing organization
        if patient.get('managingOrganization'):
            org = patient['managingOrganization']
            contact_data['managing_organization'] = {
                'reference': org.get('reference', ''),
                'display': org.get('display', 'Unknown'),
                'type': org.get('type', 'Organization')
            }
        
        return contact_data
        
        # Extract telecom information
        telecoms = patient.get('telecom', [])
        for telecom in telecoms:
            telecom_value = telecom.get('value', '')
            # Clean up tel: prefix if present
            if telecom_value.startswith('tel:'):
                telecom_value = telecom_value[4:]
            
            formatted_telecom = {
                'system': telecom.get('system', 'phone'),
                'value': telecom_value,
                'use': telecom.get('use', 'home'),
                'rank': telecom.get('rank', 0),
                'period': telecom.get('period', {}),
                'display_name': self._format_telecom_display(telecom)
            }
            contact_data['telecoms'].append(formatted_telecom)
        
        return contact_data
    
    def _extract_healthcare_data(self, practitioner_resources: List[Dict],
                               organization_resources: List[Dict],
                               composition_resources: List[Dict]) -> Dict[str, Any]:
        """Extract healthcare provider data for Extended Patient Information tab"""
        healthcare_data = {
            'practitioners': [],
            'organizations': [],
            'healthcare_team': []
        }
        
        # Extract practitioners
        for practitioner in practitioner_resources:
            # Process practitioner addresses (array format)
            practitioner_addresses = []
            addresses = practitioner.get('address', [])
            for address in addresses:
                formatted_address = {
                    'use': address.get('use', 'work'),
                    'type': address.get('type', 'physical'),
                    'street_lines': address.get('line', []),
                    'street': ', '.join(address.get('line', [])) if address.get('line') else None,
                    'city': address.get('city'),
                    'state': address.get('state'),
                    'postal_code': address.get('postalCode'),
                    'postalCode': address.get('postalCode'),
                    'country': address.get('country'),
                    'period': address.get('period', {}),
                    'full_address': self._format_address(address)
                }
                practitioner_addresses.append(formatted_address)
            
            # Process practitioner telecoms
            practitioner_telecoms = []
            telecoms = practitioner.get('telecom', [])
            for telecom in telecoms:
                telecom_value = telecom.get('value', '')
                # Clean up tel: prefix and handle invalid values
                if telecom_value.startswith('tel:'):
                    telecom_value = telecom_value[4:]
                # Skip invalid/empty telecoms
                if telecom_value and telecom_value != '0':
                    formatted_telecom = {
                        'system': telecom.get('system', 'phone'),
                        'value': telecom_value,
                        'use': telecom.get('use', 'work'),
                        'rank': telecom.get('rank', 0),
                        'period': telecom.get('period', {}),
                        'display_name': self._format_telecom_display(telecom)
                    }
                    practitioner_telecoms.append(formatted_telecom)
            
            # Process practitioner identifiers
            practitioner_identifiers = []
            identifiers = practitioner.get('identifier', [])
            for identifier in identifiers:
                formatted_identifier = {
                    'system': identifier.get('system', ''),
                    'value': identifier.get('value', ''),
                    'type': identifier.get('type', {}).get('text', 'Official'),
                    'use': identifier.get('use', 'official')
                }
                practitioner_identifiers.append(formatted_identifier)
            
            formatted_practitioner = {
                'id': practitioner.get('id', 'Unknown'),
                'name': self._format_practitioner_name(practitioner),
                'family_name': self._extract_practitioner_family_name(practitioner),
                'given_names': self._extract_practitioner_given_names(practitioner),
                'qualification': practitioner.get('qualification', []),
                'addresses': practitioner_addresses,
                'telecoms': practitioner_telecoms,
                'identifiers': practitioner_identifiers,
                'gender': practitioner.get('gender', 'Unknown'),
                'active': practitioner.get('active', True)
            }
            healthcare_data['practitioners'].append(formatted_practitioner)
        
        # Extract organizations
        for organization in organization_resources:
            # GDPR Data Protection: Filter out Cyprus organizations to prevent data contamination
            org_name = organization.get('name', '').lower()
            if any(term in org_name for term in ['cyprus', 'ehealthlab', 'university of cyprus']):
                logger.warning(f"GDPR Filter: Excluding Cyprus organization from parsing: {organization.get('name')}")
                continue
            
            # Check address for Cyprus contamination
            address_data = organization.get('address')
            is_cyprus_org = False
            
            if address_data:
                addresses_to_check = [address_data] if isinstance(address_data, dict) else address_data
                for address in addresses_to_check:
                    country = address.get('country', '').lower()
                    city = address.get('city', '').lower()
                    if country == 'cy' or 'cyprus' in country or 'nicosia' in city:
                        is_cyprus_org = True
                        break
            
            if is_cyprus_org:
                logger.warning(f"GDPR Filter: Excluding organization with Cyprus address: {organization.get('name')}")
                continue
            
            # Process organization address (can be single object or array)
            organization_addresses = []
            
            if address_data:
                # Handle both single address object and array of addresses
                addresses_to_process = [address_data] if isinstance(address_data, dict) else address_data
                
                for address in addresses_to_process:
                    formatted_address = {
                        'use': address.get('use', 'work'),
                        'type': address.get('type', 'physical'),
                        'street_lines': address.get('line', []),
                        'street': ', '.join(address.get('line', [])) if address.get('line') else None,
                        'city': address.get('city'),
                        'state': address.get('state'),
                        'postal_code': address.get('postalCode'),
                        'postalCode': address.get('postalCode'),
                        'country': address.get('country'),
                        'period': address.get('period', {}),
                        'full_address': self._format_address(address)
                    }
                    organization_addresses.append(formatted_address)
            
            # Process organization telecoms
            organization_telecoms = []
            telecoms = organization.get('telecom', [])
            for telecom in telecoms:
                telecom_value = telecom.get('value', '')
                # Clean up tel: prefix and handle invalid values
                if telecom_value.startswith('tel:'):
                    telecom_value = telecom_value[4:]
                # Skip invalid/empty telecoms
                if telecom_value and telecom_value != '0':
                    formatted_telecom = {
                        'system': telecom.get('system', 'phone'),
                        'value': telecom_value,
                        'use': telecom.get('use', 'work'),
                        'rank': telecom.get('rank', 0),
                        'period': telecom.get('period', {}),
                        'display_name': self._format_telecom_display(telecom)
                    }
                    organization_telecoms.append(formatted_telecom)
            
            # Process organization identifiers
            organization_identifiers = []
            identifiers = organization.get('identifier', [])
            for identifier in identifiers:
                formatted_identifier = {
                    'system': identifier.get('system', ''),
                    'value': identifier.get('value', ''),
                    'type': identifier.get('type', {}).get('text', 'Official'),
                    'use': identifier.get('use', 'official')
                }
                organization_identifiers.append(formatted_identifier)
            
            formatted_organization = {
                'id': organization.get('id', 'Unknown'),
                'name': organization.get('name', 'Unknown Organization'),
                'type': organization.get('type', []),
                'addresses': organization_addresses,
                'telecoms': organization_telecoms,
                'identifiers': organization_identifiers,
                'active': organization.get('active', True),
                'contact': organization.get('contact', [])
            }
            healthcare_data['organizations'].append(formatted_organization)
        
        # Extract healthcare team from composition
        if composition_resources:
            composition = composition_resources[0]
            authors = composition.get('author', [])
            for author in authors:
                healthcare_data['healthcare_team'].append({
                    'reference': author.get('reference', 'Unknown'),
                    'display': author.get('display', 'Unknown'),
                    'type': author.get('type', 'Author')
                })
        
        return healthcare_data
    
    def _format_address(self, address: Dict[str, Any]) -> str:
        """Format FHIR address into readable string"""
        parts = []
        
        # Add address lines
        if address.get('line'):
            parts.extend(address['line'])
        
        # Add city
        if address.get('city'):
            parts.append(address['city'])
        
        # Add state and postal code
        state_postal = []
        if address.get('state'):
            state_postal.append(address['state'])
        if address.get('postalCode'):
            state_postal.append(address['postalCode'])
        if state_postal:
            parts.append(' '.join(state_postal))
        
        # Add country
        if address.get('country'):
            parts.append(address['country'])
        
        return ', '.join(parts) if parts else 'Unknown Address'
    
    def _format_address_text(self, address: Dict[str, Any]) -> str:
        """
        Format FHIR address into text representation according to FHIR R4 specification.
        
        The 'text' field should be a text representation of the address that can be
        displayed to human users. If provided, this supersedes the structured address parts.
        """
        # If text is already provided in FHIR data, use it
        if address.get('text'):
            return address['text']
        
        # Otherwise, construct from structured parts
        return self._format_address(address)
    
    def _format_telecom_display(self, telecom: Dict[str, Any]) -> str:
        """Format telecom information for display"""
        system = telecom.get('system', 'phone')
        value = telecom.get('value', '')
        use = telecom.get('use', '')
        
        # Clean up tel: prefix if present
        if value.startswith('tel:'):
            value = value[4:]
        
        # Format system name for display
        system_display = {
            'phone': 'Phone',
            'fax': 'Fax',
            'email': 'Email',
            'pager': 'Pager',
            'url': 'Website',
            'sms': 'SMS'
        }.get(system.lower(), system.title())
        
        if use:
            use_display = use.title()
            return f"{system_display} ({use_display}): {value}"
        else:
            return f"{system_display}: {value}"
    
    def _format_practitioner_name(self, practitioner: Dict[str, Any]) -> str:
        """Format practitioner name from FHIR HumanName structure"""
        names = practitioner.get('name', [])
        if not names:
            return 'Unknown Practitioner'
        
        name = names[0]  # Use first name
        parts = []
        
        # Add prefix (Dr., Prof., etc.)
        if name.get('prefix'):
            parts.extend(name['prefix'])
        
        # Add given names
        if name.get('given'):
            parts.extend(name['given'])
        
        # Add family name
        if name.get('family'):
            parts.append(name['family'])
        
        # Add suffix
        if name.get('suffix'):
            parts.extend(name['suffix'])
        
        return ' '.join(parts) if parts else 'Unknown Practitioner'
    
    def _extract_practitioner_family_name(self, practitioner: Dict[str, Any]) -> str:
        """Extract family name from practitioner resource"""
        names = practitioner.get('name', [])
        if names and names[0].get('family'):
            return names[0]['family']
        return 'Unknown'
    
    def _extract_practitioner_given_names(self, practitioner: Dict[str, Any]) -> List[str]:
        """Extract given names from practitioner resource"""
        names = practitioner.get('name', [])
        if names and names[0].get('given'):
            return names[0]['given']
        return []


class FHIRBundleParserError(Exception):
    """Custom exception for FHIR Bundle parsing errors"""
    pass


# Service instance for dependency injection
fhir_bundle_parser = FHIRBundleParser()