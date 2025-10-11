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
        """Extract patient identity information for UI display"""
        if not patient_resources:
            return {
                'given_name': 'Unknown',
                'family_name': 'Patient',
                'full_name': 'Unknown Patient',
                'birth_date': 'Unknown',
                'gender': 'Unknown',
                'patient_id': 'Unknown',
                'source_country': 'Unknown'
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
        
        # Extract source country from address
        source_country = 'Unknown'
        addresses = patient.get('address', [])
        if addresses:
            address = addresses[0]  # Use first address
            country_code = address.get('country', 'Unknown')
            if country_code and country_code != 'Unknown':
                source_country = country_code  # Will be processed by country_name template filter
        
        return {
            'given_name': given_name,
            'family_name': family_name,
            'full_name': f"{given_name} {family_name}",
            'birth_date': patient.get('birthDate', 'Unknown'),
            'gender': patient.get('gender', 'Unknown').capitalize(),
            'patient_id': patient.get('id', 'Unknown'),
            'source_country': source_country
        }
    
    def _extract_administrative_data(self, patient_resources: List[Dict], 
                                   composition_resources: List[Dict],
                                   fhir_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """Extract administrative data for Extended Patient Information tab"""
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
                    'use': identifier.get('use', 'Unknown')
                })
            
            # Patient administrative details
            administrative_data.update({
                'patient_identifiers': formatted_identifiers,
                'marital_status': patient.get('maritalStatus', {}).get('text', 'Unknown'),
                'communication': patient.get('communication', []),
                'deceased': patient.get('deceasedBoolean', False),
                'multiple_birth': patient.get('multipleBirthBoolean', False),
                'active': patient.get('active', True)
            })
        
        # Document metadata from Composition
        if composition_resources:
            composition = composition_resources[0]
            administrative_data.update({
                'document_id': composition.get('id', 'Unknown'),
                'document_title': composition.get('title', 'Patient Summary'),
                'document_status': composition.get('status', 'Unknown'),
                'document_date': composition.get('date', 'Unknown'),
                'document_type': composition.get('type', {}).get('text', 'Patient Summary'),
                'custodian': composition.get('custodian', {}).get('display', 'Unknown'),
                'author': [author.get('display', 'Unknown') for author in composition.get('author', [])]
            })
        
        # Bundle metadata
        administrative_data.update({
            'bundle_id': fhir_bundle.get('id', 'Unknown'),
            'bundle_type': fhir_bundle.get('type', 'Unknown'),
            'bundle_timestamp': fhir_bundle.get('timestamp', 'Unknown')
        })
        
        return administrative_data
    
    def _extract_contact_data(self, patient_resources: List[Dict]) -> Dict[str, Any]:
        """Extract contact information for Extended Patient Information tab"""
        contact_data = {
            'addresses': [],
            'telecoms': []
        }
        
        if not patient_resources:
            return contact_data
            
        patient = patient_resources[0]
        
        # Extract addresses
        addresses = patient.get('address', [])
        for address in addresses:
            formatted_address = {
                'use': address.get('use', 'Unknown'),
                'type': address.get('type', 'Unknown'),
                'line': address.get('line', []),
                'city': address.get('city', 'Unknown'),
                'state': address.get('state', 'Unknown'),
                'postal_code': address.get('postalCode', 'Unknown'),
                'country': address.get('country', 'Unknown'),
                'period': address.get('period', {}),
                'full_address': self._format_address(address)
            }
            contact_data['addresses'].append(formatted_address)
        
        # Extract telecom information
        telecoms = patient.get('telecom', [])
        for telecom in telecoms:
            formatted_telecom = {
                'system': telecom.get('system', 'Unknown'),
                'value': telecom.get('value', 'Unknown'),
                'use': telecom.get('use', 'Unknown'),
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
            formatted_practitioner = {
                'id': practitioner.get('id', 'Unknown'),
                'name': self._format_practitioner_name(practitioner),
                'qualification': practitioner.get('qualification', []),
                'telecom': practitioner.get('telecom', []),
                'address': practitioner.get('address', []),
                'gender': practitioner.get('gender', 'Unknown'),
                'active': practitioner.get('active', True)
            }
            healthcare_data['practitioners'].append(formatted_practitioner)
        
        # Extract organizations
        for organization in organization_resources:
            formatted_organization = {
                'id': organization.get('id', 'Unknown'),
                'name': organization.get('name', 'Unknown'),
                'type': organization.get('type', []),
                'telecom': organization.get('telecom', []),
                'address': organization.get('address', []),
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
    
    def _format_telecom_display(self, telecom: Dict[str, Any]) -> str:
        """Format telecom information for display"""
        system = telecom.get('system', 'Unknown')
        value = telecom.get('value', 'Unknown')
        use = telecom.get('use', '')
        
        if use:
            return f"{system.title()} ({use}): {value}"
        else:
            return f"{system.title()}: {value}"
    
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


class FHIRBundleParserError(Exception):
    """Custom exception for FHIR Bundle parsing errors"""
    pass


# Service instance for dependency injection
fhir_bundle_parser = FHIRBundleParser()