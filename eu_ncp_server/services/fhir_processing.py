"""
FHIR Resource Processing Service
Patient Summary Processing and FHIR R4 Resource Parsing

This service handles:
- FHIR Bundle parsing and validation
- Patient Summary component extraction
- Clinical data conversion to display format
- FHIR resource serialization and deserialization
- Cross-border healthcare data standardization
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from django.conf import settings
from fhir.resources.bundle import Bundle
from fhir.resources.patient import Patient
from fhir.resources.allergyintolerance import AllergyIntolerance
from fhir.resources.medicationstatement import MedicationStatement
from fhir.resources.condition import Condition
from fhir.resources.observation import Observation

logger = logging.getLogger("ehealth")


class FHIRResourceProcessor:
    """Service for processing FHIR R4 resources and Patient Summaries"""
    
    def __init__(self):
        self.supported_resources = [
            'Patient', 'AllergyIntolerance', 'Medication', 'MedicationStatement',
            'Condition', 'Observation', 'Procedure', 'Immunization'
        ]
    
    def parse_patient_summary_bundle(self, fhir_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse FHIR Patient Summary Bundle into structured clinical data
        
        Args:
            fhir_bundle: FHIR Bundle containing Patient Summary
            
        Returns:
            Structured patient summary data for display
        """
        try:
            if not self._validate_bundle(fhir_bundle):
                raise ValueError("Invalid FHIR Bundle structure")
            
            # Initialize patient summary structure
            patient_summary = {
                'patient_info': {},
                'allergies': [],
                'medications': [],
                'conditions': [],
                'observations': [],
                'procedures': [],
                'immunizations': [],
                'metadata': {
                    'bundle_id': fhir_bundle.get('id'),
                    'timestamp': fhir_bundle.get('timestamp'),
                    'processed_at': datetime.now(timezone.utc).isoformat()
                }
            }
            
            # Process each entry in the bundle
            for entry in fhir_bundle.get('entry', []):
                resource = entry.get('resource', {})
                resource_type = resource.get('resourceType')
                
                if resource_type == 'Patient':
                    patient_summary['patient_info'] = self._process_patient_resource(resource)
                elif resource_type == 'AllergyIntolerance':
                    allergy = self._process_allergy_resource(resource)
                    patient_summary['allergies'].append(allergy)
                elif resource_type in ['Medication', 'MedicationStatement']:
                    medication = self._process_medication_resource(resource)
                    patient_summary['medications'].append(medication)
                elif resource_type == 'Condition':
                    condition = self._process_condition_resource(resource)
                    patient_summary['conditions'].append(condition)
                elif resource_type == 'Observation':
                    observation = self._process_observation_resource(resource)
                    patient_summary['observations'].append(observation)
                elif resource_type == 'Procedure':
                    procedure = self._process_procedure_resource(resource)
                    patient_summary['procedures'].append(procedure)
                elif resource_type == 'Immunization':
                    immunization = self._process_immunization_resource(resource)
                    patient_summary['immunizations'].append(immunization)
            
            logger.info(f"Patient Summary processed: bundle_id={fhir_bundle.get('id')}")
            return patient_summary
            
        except Exception as e:
            logger.error(f"Error parsing Patient Summary Bundle: {str(e)}")
            raise FHIRProcessingError(f"Bundle parsing failed: {str(e)}")
    
    def _process_patient_resource(self, patient: Dict[str, Any]) -> Dict[str, Any]:
        """Extract patient demographic information"""
        patient_info = {
            'id': patient.get('id'),
            'name': self._extract_human_name(patient.get('name', [])),
            'birth_date': patient.get('birthDate'),
            'gender': patient.get('gender'),
            'addresses': [],
            'telecoms': [],
            'identifiers': []
        }
        
        # Extract addresses
        for address in patient.get('address', []):
            patient_info['addresses'].append({
                'use': address.get('use', 'home'),
                'line': address.get('line', []),
                'city': address.get('city'),
                'postal_code': address.get('postalCode'),
                'country': address.get('country')
            })
        
        # Extract contact information
        for telecom in patient.get('telecom', []):
            patient_info['telecoms'].append({
                'system': telecom.get('system'),
                'value': telecom.get('value'),
                'use': telecom.get('use')
            })
        
        # Extract identifiers
        for identifier in patient.get('identifier', []):
            patient_info['identifiers'].append({
                'system': identifier.get('system'),
                'value': identifier.get('value'),
                'type': identifier.get('type', {}).get('text', 'Unknown')
            })
        
        return patient_info
    
    def _process_allergy_resource(self, allergy: Dict[str, Any]) -> Dict[str, Any]:
        """Extract allergy/intolerance information"""
        return {
            'id': allergy.get('id'),
            'clinical_status': self._extract_coding_display(allergy.get('clinicalStatus', {})),
            'verification_status': self._extract_coding_display(allergy.get('verificationStatus', {})),
            'category': allergy.get('category', []),
            'criticality': allergy.get('criticality'),
            'code': self._extract_coding_display(allergy.get('code', {})),
            'onset': allergy.get('onsetDateTime', allergy.get('onsetString')),
            'last_occurrence': allergy.get('lastOccurrence'),
            'note': self._extract_annotation_text(allergy.get('note', [])),
            'reactions': self._process_allergy_reactions(allergy.get('reaction', []))
        }
    
    def _process_medication_resource(self, medication: Dict[str, Any]) -> Dict[str, Any]:
        """Extract medication information"""
        med_info = {
            'id': medication.get('id'),
            'status': medication.get('status'),
            'medication': {},
            'dosage': [],
            'effective_period': {},
            'note': self._extract_annotation_text(medication.get('note', []))
        }
        
        # Extract medication coding
        if 'medicationCodeableConcept' in medication:
            med_info['medication'] = self._extract_coding_display(medication['medicationCodeableConcept'])
        elif 'medicationReference' in medication:
            med_info['medication'] = {'reference': medication['medicationReference'].get('reference')}
        
        # Extract dosage instructions
        for dosage in medication.get('dosageInstruction', []):
            med_info['dosage'].append({
                'text': dosage.get('text'),
                'timing': dosage.get('timing', {}).get('repeat', {}).get('frequency'),
                'route': self._extract_coding_display(dosage.get('route', {})),
                'dose_quantity': dosage.get('doseAndRate', [{}])[0].get('doseQuantity', {})
            })
        
        # Extract effective period
        if 'effectivePeriod' in medication:
            med_info['effective_period'] = {
                'start': medication['effectivePeriod'].get('start'),
                'end': medication['effectivePeriod'].get('end')
            }
        
        return med_info
    
    def _process_condition_resource(self, condition: Dict[str, Any]) -> Dict[str, Any]:
        """Extract condition/problem information"""
        return {
            'id': condition.get('id'),
            'clinical_status': self._extract_coding_display(condition.get('clinicalStatus', {})),
            'verification_status': self._extract_coding_display(condition.get('verificationStatus', {})),
            'category': [self._extract_coding_display(cat) for cat in condition.get('category', [])],
            'severity': self._extract_coding_display(condition.get('severity', {})),
            'code': self._extract_coding_display(condition.get('code', {})),
            'onset': condition.get('onsetDateTime', condition.get('onsetString')),
            'recorded_date': condition.get('recordedDate'),
            'note': self._extract_annotation_text(condition.get('note', []))
        }
    
    def _process_observation_resource(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """Extract observation/vital signs information"""
        obs_info = {
            'id': observation.get('id'),
            'status': observation.get('status'),
            'category': [self._extract_coding_display(cat) for cat in observation.get('category', [])],
            'code': self._extract_coding_display(observation.get('code', {})),
            'effective': observation.get('effectiveDateTime', observation.get('effectivePeriod')),
            'value': {},
            'interpretation': [],
            'note': self._extract_annotation_text(observation.get('note', []))
        }
        
        # Extract observation value
        if 'valueQuantity' in observation:
            obs_info['value'] = {
                'type': 'quantity',
                'value': observation['valueQuantity'].get('value'),
                'unit': observation['valueQuantity'].get('unit'),
                'system': observation['valueQuantity'].get('system')
            }
        elif 'valueCodeableConcept' in observation:
            obs_info['value'] = {
                'type': 'concept',
                'coding': self._extract_coding_display(observation['valueCodeableConcept'])
            }
        elif 'valueString' in observation:
            obs_info['value'] = {
                'type': 'string',
                'value': observation['valueString']
            }
        
        # Extract interpretation
        for interp in observation.get('interpretation', []):
            obs_info['interpretation'].append(self._extract_coding_display(interp))
        
        return obs_info
    
    def _process_procedure_resource(self, procedure: Dict[str, Any]) -> Dict[str, Any]:
        """Extract procedure information"""
        return {
            'id': procedure.get('id'),
            'status': procedure.get('status'),
            'category': self._extract_coding_display(procedure.get('category', {})),
            'code': self._extract_coding_display(procedure.get('code', {})),
            'performed': procedure.get('performedDateTime', procedure.get('performedPeriod')),
            'outcome': self._extract_coding_display(procedure.get('outcome', {})),
            'note': self._extract_annotation_text(procedure.get('note', []))
        }
    
    def _process_immunization_resource(self, immunization: Dict[str, Any]) -> Dict[str, Any]:
        """Extract immunization information"""
        return {
            'id': immunization.get('id'),
            'status': immunization.get('status'),
            'vaccine_code': self._extract_coding_display(immunization.get('vaccineCode', {})),
            'occurrence': immunization.get('occurrenceDateTime'),
            'lot_number': immunization.get('lotNumber'),
            'route': self._extract_coding_display(immunization.get('route', {})),
            'dose_quantity': immunization.get('doseQuantity', {}),
            'note': self._extract_annotation_text(immunization.get('note', []))
        }
    
    def _process_allergy_reactions(self, reactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process allergy reaction information"""
        processed_reactions = []
        for reaction in reactions:
            processed_reactions.append({
                'substance': self._extract_coding_display(reaction.get('substance', {})),
                'manifestation': [
                    self._extract_coding_display(manifest) 
                    for manifest in reaction.get('manifestation', [])
                ],
                'severity': reaction.get('severity'),
                'onset': reaction.get('onset'),
                'note': self._extract_annotation_text(reaction.get('note', []))
            })
        return processed_reactions
    
    def _extract_human_name(self, names: List[Dict[str, Any]]) -> str:
        """Extract display name from FHIR HumanName array"""
        if not names:
            return "Unknown"
        
        # Use first name entry
        name = names[0]
        parts = []
        
        if name.get('prefix'):
            parts.extend(name['prefix'])
        if name.get('given'):
            parts.extend(name['given'])
        if name.get('family'):
            parts.append(name['family'])
        
        return ' '.join(parts) if parts else "Unknown"
    
    def _extract_coding_display(self, codeable_concept: Dict[str, Any]) -> Dict[str, Any]:
        """Extract display information from CodeableConcept"""
        if not codeable_concept:
            return {}
        
        # Return text if available
        if codeable_concept.get('text'):
            return {'display': codeable_concept['text']}
        
        # Extract from first coding
        codings = codeable_concept.get('coding', [])
        if codings:
            coding = codings[0]
            return {
                'system': coding.get('system'),
                'code': coding.get('code'),
                'display': coding.get('display', coding.get('code', 'Unknown'))
            }
        
        return {}
    
    def _extract_annotation_text(self, annotations: List[Dict[str, Any]]) -> str:
        """Extract text from FHIR Annotation array (simplified for text display)"""
        if not annotations:
            return ""
        
        texts = []
        for annotation in annotations:
            if annotation.get('text'):
                texts.append(annotation['text'])
        
        return ' '.join(texts)
    
    def _extract_annotation_data(self, annotations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract complete FHIR R4 Annotation data with author and time information"""
        if not annotations:
            return []
        
        annotation_data = []
        for annotation in annotations:
            if not annotation.get('text'):
                continue  # Skip annotations without required text
            
            # Extract author information (either Reference or string)
            author_info = {}
            if annotation.get('authorReference'):
                author_ref = annotation['authorReference']
                author_info = {
                    'type': 'reference',
                    'reference': author_ref.get('reference', ''),
                    'display': author_ref.get('display', 'Unknown Author'),
                    'resource_type': self._extract_reference_type(author_ref.get('reference', ''))
                }
            elif annotation.get('authorString'):
                author_info = {
                    'type': 'string',
                    'display': annotation['authorString'],
                    'reference': None,
                    'resource_type': 'string'
                }
            else:
                author_info = {
                    'type': 'unknown',
                    'display': 'Unknown Author',
                    'reference': None,
                    'resource_type': 'unknown'
                }
            
            # Format annotation with full FHIR R4 compliance
            formatted_annotation = {
                'text': annotation['text'],  # Required field
                'author': author_info,
                'time': annotation.get('time'),  # Optional dateTime
                'timestamp_display': self._format_datetime_display(annotation.get('time')),
                'markdown_text': annotation['text'],  # Annotation text is markdown format
                'has_author': bool(annotation.get('authorReference') or annotation.get('authorString')),
                'has_timestamp': bool(annotation.get('time'))
            }
            
            annotation_data.append(formatted_annotation)
        
        return annotation_data
    
    def _extract_reference_type(self, reference: str) -> str:
        """Extract resource type from FHIR reference string"""
        if not reference:
            return 'unknown'
        
        # FHIR reference format: ResourceType/id
        if '/' in reference:
            return reference.split('/')[0]
        
        return 'unknown'
    
    def _format_datetime_display(self, datetime_str: Optional[str]) -> Optional[str]:
        """Format FHIR dateTime for display"""
        if not datetime_str:
            return None
        
        try:
            from datetime import datetime
            # Parse FHIR dateTime format (ISO 8601)
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M')
        except (ValueError, AttributeError):
            return datetime_str  # Return as-is if parsing fails
    
    def _validate_bundle(self, bundle: Dict[str, Any]) -> bool:
        """Validate FHIR Bundle structure"""
        return (
            bundle.get('resourceType') == 'Bundle' and
            'entry' in bundle and
            isinstance(bundle['entry'], list)
        )
    
    def convert_to_display_format(self, patient_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert processed FHIR data to Django NCP display format
        
        Args:
            patient_summary: Processed FHIR patient summary
            
        Returns:
            Data formatted for Django templates and UI display
        """
        try:
            display_data = {
                'patient': {
                    'name': patient_summary['patient_info'].get('name', 'Unknown'),
                    'birth_date': patient_summary['patient_info'].get('birth_date'),
                    'gender': patient_summary['patient_info'].get('gender', '').title(),
                    'identifiers': patient_summary['patient_info'].get('identifiers', [])
                },
                'clinical_sections': {
                    'allergies': self._format_allergies_for_display(patient_summary['allergies']),
                    'medications': self._format_medications_for_display(patient_summary['medications']),
                    'conditions': self._format_conditions_for_display(patient_summary['conditions']),
                    'observations': self._format_observations_for_display(patient_summary['observations']),
                    'procedures': self._format_procedures_for_display(patient_summary['procedures']),
                    'immunizations': self._format_immunizations_for_display(patient_summary['immunizations'])
                },
                'metadata': patient_summary['metadata']
            }
            
            return display_data
            
        except Exception as e:
            logger.error(f"Error converting to display format: {str(e)}")
            raise FHIRProcessingError(f"Display format conversion failed: {str(e)}")
    
    def _format_allergies_for_display(self, allergies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format allergies for template display"""
        formatted = []
        for allergy in allergies:
            formatted.append({
                'substance': allergy['code'].get('display', 'Unknown allergen'),
                'status': allergy['clinical_status'].get('display', 'Unknown'),
                'criticality': allergy.get('criticality', 'Unknown'),
                'reactions': [r.get('severity', 'Unknown') for r in allergy.get('reactions', [])],
                'category': ', '.join(allergy.get('category', [])),
                'onset': allergy.get('onset', 'Unknown')
            })
        return formatted
    
    def _format_medications_for_display(self, medications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format medications for template display"""
        formatted = []
        for med in medications:
            formatted.append({
                'name': med['medication'].get('display', 'Unknown medication'),
                'status': med.get('status', 'Unknown'),
                'dosage': med['dosage'][0].get('text', 'As directed') if med['dosage'] else 'As directed',
                'start_date': med['effective_period'].get('start', 'Unknown'),
                'end_date': med['effective_period'].get('end', 'Ongoing')
            })
        return formatted
    
    def _format_conditions_for_display(self, conditions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format conditions for template display"""
        formatted = []
        for condition in conditions:
            formatted.append({
                'name': condition['code'].get('display', 'Unknown condition'),
                'status': condition['clinical_status'].get('display', 'Unknown'),
                'severity': condition['severity'].get('display', 'Unknown'),
                'onset': condition.get('onset', 'Unknown'),
                'category': ', '.join([cat.get('display', '') for cat in condition.get('category', [])])
            })
        return formatted
    
    def _format_observations_for_display(self, observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format observations for template display"""
        formatted = []
        for obs in observations:
            value_display = "Unknown"
            if obs['value'].get('type') == 'quantity':
                value_display = f"{obs['value']['value']} {obs['value']['unit']}"
            elif obs['value'].get('type') == 'concept':
                value_display = obs['value']['coding'].get('display', 'Unknown')
            elif obs['value'].get('type') == 'string':
                value_display = obs['value']['value']
            
            formatted.append({
                'name': obs['code'].get('display', 'Unknown observation'),
                'value': value_display,
                'status': obs.get('status', 'Unknown'),
                'date': obs.get('effective', 'Unknown'),
                'interpretation': ', '.join([i.get('display', '') for i in obs.get('interpretation', [])])
            })
        return formatted
    
    def _format_procedures_for_display(self, procedures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format procedures for template display"""
        formatted = []
        for proc in procedures:
            formatted.append({
                'name': proc['code'].get('display', 'Unknown procedure'),
                'status': proc.get('status', 'Unknown'),
                'performed': proc.get('performed', 'Unknown'),
                'category': proc['category'].get('display', 'Unknown')
            })
        return formatted
    
    def _format_immunizations_for_display(self, immunizations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format immunizations for template display"""
        formatted = []
        for imm in immunizations:
            formatted.append({
                'vaccine': imm['vaccine_code'].get('display', 'Unknown vaccine'),
                'status': imm.get('status', 'Unknown'),
                'date': imm.get('occurrence', 'Unknown'),
                'lot_number': imm.get('lot_number', 'Unknown')
            })
        return formatted
    
    def validate_fhir_bundle(self, bundle: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate FHIR Bundle structure and content
        
        Args:
            bundle: FHIR Bundle to validate
            
        Returns:
            Validation result with errors and warnings
        """
        try:
            validation_result = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'information': []
            }
            
            # Basic structure validation
            if not isinstance(bundle, dict):
                validation_result['valid'] = False
                validation_result['errors'].append("Bundle must be a dictionary")
                return validation_result
            
            # Required fields validation
            required_fields = ['resourceType', 'type']
            for field in required_fields:
                if field not in bundle:
                    validation_result['valid'] = False
                    validation_result['errors'].append(f"Missing required field: {field}")
            
            # ResourceType validation
            if bundle.get('resourceType') != 'Bundle':
                validation_result['valid'] = False
                validation_result['errors'].append("ResourceType must be 'Bundle'")
            
            # Bundle type validation
            valid_bundle_types = ['document', 'message', 'transaction', 'transaction-response', 'batch', 'batch-response', 'history', 'searchset', 'collection']
            if bundle.get('type') and bundle.get('type') not in valid_bundle_types:
                validation_result['warnings'].append(f"Bundle type '{bundle.get('type')}' is not standard")
            
            # Entry validation
            entries = bundle.get('entry', [])
            if not isinstance(entries, list):
                validation_result['valid'] = False
                validation_result['errors'].append("Bundle.entry must be an array")
            else:
                for i, entry in enumerate(entries):
                    if not isinstance(entry, dict):
                        validation_result['valid'] = False
                        validation_result['errors'].append(f"Bundle.entry[{i}] must be an object")
                        continue
                    
                    # Check for resource in entry
                    if 'resource' not in entry:
                        validation_result['warnings'].append(f"Bundle.entry[{i}] missing resource")
                    else:
                        resource = entry['resource']
                        if not isinstance(resource, dict):
                            validation_result['valid'] = False
                            validation_result['errors'].append(f"Bundle.entry[{i}].resource must be an object")
                        elif 'resourceType' not in resource:
                            validation_result['valid'] = False
                            validation_result['errors'].append(f"Bundle.entry[{i}].resource missing resourceType")
            
            # Additional checks
            if bundle.get('total') is not None:
                try:
                    total = int(bundle.get('total'))
                    if total < 0:
                        validation_result['warnings'].append("Bundle.total should not be negative")
                except (ValueError, TypeError):
                    validation_result['warnings'].append("Bundle.total should be a number")
            
            logger.info(f"FHIR Bundle validation completed: valid={validation_result['valid']}, errors={len(validation_result['errors'])}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating FHIR Bundle: {str(e)}")
            return {
                'valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': [],
                'information': []
            }


class FHIRProcessingError(Exception):
    """Custom exception for FHIR processing errors"""
    pass


# Service instance for dependency injection
fhir_processor = FHIRResourceProcessor()