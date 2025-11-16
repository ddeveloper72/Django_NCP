"""
FHIR Resource Processing Service
Enhanced FHIR R4 Data Types and Resource Processing

This service handles:
- FHIR Bundle parsing and validation
- Patient Summary component extraction
- Complete FHIR R4 data type processing (Quantity, Timing, Range, Ratio, etc.)
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
from translation_services.terminology_translator import TerminologyTranslator

logger = logging.getLogger("ehealth")


class FHIRResourceProcessor:
    """Service for processing FHIR R4 resources and Patient Summaries"""
    
    def __init__(self):
        self.supported_resources = [
            'Patient', 'AllergyIntolerance', 'Medication', 'MedicationStatement',
            'Condition', 'Observation', 'Procedure', 'Immunization'
        ]
        # Initialize CTS translator for code resolution
        self.cts_translator = TerminologyTranslator()
    
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
        """Extract immunization information including enhanced fields"""
        # Extract performer (who administered)
        performers = immunization.get('performer', [])
        performer_name = None
        if performers:
            first_performer = performers[0]
            actor = first_performer.get('actor', {})
            performer_name = actor.get('display', actor.get('reference', None))
        
        # Extract dose number from protocolApplied
        protocols = immunization.get('protocolApplied', [])
        dose_number = None
        if protocols:
            first_protocol = protocols[0]
            dose_number = first_protocol.get('doseNumberPositiveInt', 
                                            first_protocol.get('doseNumberString', None))
        
        return {
            'id': immunization.get('id'),
            'status': immunization.get('status'),
            'vaccine_code': self._extract_coding_display(immunization.get('vaccineCode', {})),
            'occurrence': immunization.get('occurrenceDateTime'),
            'lot_number': immunization.get('lotNumber'),
            'route': self._extract_coding_display(immunization.get('route', {})),
            'dose_quantity': immunization.get('doseQuantity', {}),
            'note': self._extract_annotation_text(immunization.get('note', [])),
            'performer': performer_name,  # NEW: who administered
            'dose_number': dose_number,    # NEW: dose number from protocol
            'site': self._extract_coding_display(immunization.get('site', {}))  # NEW: injection site
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
    
    # ===================================================================
    # FHIR R4 Data Type Processors
    # Comprehensive support for all major FHIR data types
    # ===================================================================
    
    def _extract_quantity_data(self, quantity: Dict[str, Any]) -> Dict[str, Any]:
        """Extract complete FHIR R4 Quantity data structure"""
        if not quantity:
            return {}
        
        return {
            'value': quantity.get('value'),
            'comparator': quantity.get('comparator'),  # <, <=, >=, >
            'unit': quantity.get('unit'),
            'system': quantity.get('system'),  # UCUM system preferred
            'code': quantity.get('code'),
            'display_value': self._format_quantity_display(quantity),
            'is_ucum_compliant': self._is_ucum_quantity(quantity)
        }
    
    def _format_quantity_display(self, quantity: Dict[str, Any]) -> str:
        """Format quantity for human-readable display"""
        if not quantity or not quantity.get('value'):
            return 'Unknown quantity'
        
        value = quantity.get('value')
        unit = quantity.get('unit', quantity.get('code', ''))
        comparator = quantity.get('comparator', '')
        
        # Format display value
        display = f"{comparator}{value}"
        if unit:
            display += f" {unit}"
        
        return display
    
    def _is_ucum_quantity(self, quantity: Dict[str, Any]) -> bool:
        """Check if quantity uses UCUM system"""
        system = quantity.get('system', '')
        return 'unitsofmeasure.org' in system.lower() or 'ucum.org' in system.lower()
    
    def _extract_range_data(self, range_obj: Dict[str, Any]) -> Dict[str, Any]:
        """Extract FHIR R4 Range data structure"""
        if not range_obj:
            return {}
        
        return {
            'low': self._extract_quantity_data(range_obj.get('low', {})),
            'high': self._extract_quantity_data(range_obj.get('high', {})),
            'display_range': self._format_range_display(range_obj),
            'has_bounds': bool(range_obj.get('low') or range_obj.get('high'))
        }
    
    def _format_range_display(self, range_obj: Dict[str, Any]) -> str:
        """Format range for human-readable display"""
        if not range_obj:
            return 'Unknown range'
        
        low = range_obj.get('low')
        high = range_obj.get('high')
        
        if low and high:
            low_display = self._format_quantity_display(low)
            high_display = self._format_quantity_display(high)
            return f"{low_display} - {high_display}"
        elif low:
            return f"≥ {self._format_quantity_display(low)}"
        elif high:
            return f"≤ {self._format_quantity_display(high)}"
        else:
            return 'Unknown range'
    
    def _extract_ratio_data(self, ratio: Dict[str, Any]) -> Dict[str, Any]:
        """Extract FHIR R4 Ratio data structure"""
        if not ratio:
            return {}
        
        return {
            'numerator': self._extract_quantity_data(ratio.get('numerator', {})),
            'denominator': self._extract_quantity_data(ratio.get('denominator', {})),
            'display_ratio': self._format_ratio_display(ratio),
            'has_ratio': bool(ratio.get('numerator') and ratio.get('denominator'))
        }
    
    def _format_ratio_display(self, ratio: Dict[str, Any]) -> str:
        """Format ratio for human-readable display"""
        if not ratio:
            return 'Unknown ratio'
        
        numerator = ratio.get('numerator')
        denominator = ratio.get('denominator')
        
        if numerator and denominator:
            num_display = self._format_quantity_display(numerator)
            den_display = self._format_quantity_display(denominator)
            return f"{num_display} : {den_display}"
        else:
            return 'Incomplete ratio'
    
    def _extract_period_data(self, period: Dict[str, Any]) -> Dict[str, Any]:
        """Extract FHIR R4 Period data structure"""
        if not period:
            return {}
        
        return {
            'start': period.get('start'),
            'end': period.get('end'),
            'start_display': self._format_datetime_display(period.get('start')),
            'end_display': self._format_datetime_display(period.get('end')),
            'is_ongoing': bool(period.get('start') and not period.get('end')),
            'duration_display': self._calculate_period_duration(period)
        }
    
    def _calculate_period_duration(self, period: Dict[str, Any]) -> Optional[str]:
        """Calculate and format period duration"""
        start = period.get('start')
        end = period.get('end')
        
        if not start:
            return None
        
        try:
            from datetime import datetime
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            
            if end:
                end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                duration = end_dt - start_dt
                days = duration.days
                if days > 365:
                    years = days // 365
                    return f"~{years} year{'s' if years != 1 else ''}"
                elif days > 30:
                    months = days // 30
                    return f"~{months} month{'s' if months != 1 else ''}"
                else:
                    return f"{days} day{'s' if days != 1 else ''}"
            else:
                return "Ongoing"
        except (ValueError, AttributeError):
            return None
    
    def _extract_timing_data(self, timing: Dict[str, Any]) -> Dict[str, Any]:
        """Extract FHIR R4 Timing data structure for medication schedules"""
        if not timing:
            return {}
        
        timing_data = {
            'event': timing.get('event', []),  # Specific times
            'code': self._extract_codeable_concept(timing.get('code', {})),
            'display_schedule': self._format_timing_display(timing)
        }
        
        # Process repeat schedule
        repeat = timing.get('repeat', {})
        if repeat:
            timing_data['repeat'] = {
                'bounds': self._extract_timing_bounds(repeat.get('bounds')),
                'count': repeat.get('count'),
                'count_max': repeat.get('countMax'),
                'duration': repeat.get('duration'),
                'duration_unit': repeat.get('durationUnit'),
                'frequency': repeat.get('frequency'),
                'frequency_max': repeat.get('frequencyMax'),
                'period': repeat.get('period'),
                'period_unit': repeat.get('periodUnit'),
                'day_of_week': repeat.get('dayOfWeek', []),
                'time_of_day': repeat.get('timeOfDay', []),
                'when': repeat.get('when', []),
                'offset': repeat.get('offset')
            }
        
        return timing_data
    
    def _extract_timing_bounds(self, bounds: Any) -> Dict[str, Any]:
        """Extract timing bounds (Duration, Range, or Period)"""
        if not bounds:
            return {}
        
        if isinstance(bounds, dict):
            # Determine bounds type and extract accordingly
            if 'start' in bounds or 'end' in bounds:
                return {'type': 'Period', 'data': self._extract_period_data(bounds)}
            elif 'low' in bounds or 'high' in bounds:
                return {'type': 'Range', 'data': self._extract_range_data(bounds)}
            elif 'value' in bounds and 'unit' in bounds:
                return {'type': 'Duration', 'data': self._extract_quantity_data(bounds)}
        
        return {}
    
    def _format_timing_display(self, timing: Dict[str, Any]) -> str:
        """Format timing for human-readable display"""
        # Check for simple code first
        code = timing.get('code', {})
        if code and code.get('text'):
            return code['text']
        
        # Check for specific events
        events = timing.get('event', [])
        if events and not timing.get('repeat'):
            event_times = [self._format_datetime_display(event) for event in events[:3]]
            return f"At specific times: {', '.join(event_times)}"
        
        repeat = timing.get('repeat', {})
        if not repeat:
            if events:
                event_times = [self._format_datetime_display(event) for event in events[:3]]
                return f"At specific times: {', '.join(event_times)}"
            return 'As directed'
        
        # Build schedule description from repeat elements
        frequency = repeat.get('frequency', 1)
        period = repeat.get('period', 1)
        period_unit = repeat.get('periodUnit', 'd')
        
        # Convert period unit to readable format
        unit_map = {'s': 'second', 'min': 'minute', 'h': 'hour', 'd': 'day', 'wk': 'week', 'mo': 'month', 'a': 'year'}
        unit_display = unit_map.get(period_unit, period_unit)
        
        if frequency == 1 and period == 1:
            return f"Once per {unit_display}"
        elif frequency > 1 and period == 1:
            return f"{frequency} times per {unit_display}"
        else:
            return f"{frequency} time{'s' if frequency != 1 else ''} every {period} {unit_display}{'s' if period != 1 else ''}"
    
    def _extract_attachment_data(self, attachment: Dict[str, Any]) -> Dict[str, Any]:
        """Extract FHIR R4 Attachment data structure"""
        if not attachment:
            return {}
        
        return {
            'content_type': attachment.get('contentType'),
            'language': attachment.get('language'),
            'data': attachment.get('data'),  # base64 encoded
            'url': attachment.get('url'),
            'size': attachment.get('size'),
            'hash': attachment.get('hash'),
            'title': attachment.get('title'),
            'creation': attachment.get('creation'),
            'creation_display': self._format_datetime_display(attachment.get('creation')),
            'has_inline_data': bool(attachment.get('data')),
            'has_external_url': bool(attachment.get('url')),
            'display_title': attachment.get('title', 'Attachment'),
            'size_display': self._format_file_size(attachment.get('size'))
        }
    
    def _format_file_size(self, size_bytes: Optional[int]) -> Optional[str]:
        """Format file size for human-readable display"""
        if not size_bytes:
            return None
        
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def _extract_coding_data(self, coding: Dict[str, Any]) -> Dict[str, Any]:
        """Extract FHIR R4 Coding data structure with CTS terminology translation"""
        if not coding:
            return {}
        
        # Get display text, falling back to CTS lookup or code value
        display_text = coding.get('display')
        code = coding.get('code', 'Unknown code')
        code_system = coding.get('system', '')
        
        # If no display text, use CTS translator to resolve the code
        if not display_text and code != 'Unknown code':
            try:
                # Try CTS translation WITHOUT OID first (works best for ICD-10 and other codes)
                resolved_display = self.cts_translator.resolve_code(code)
                if resolved_display and resolved_display != code:
                    display_text = resolved_display
                    logger.debug(f"[CTS] Resolved {code} -> {display_text}")
            except Exception as e:
                logger.warning(f"[CTS] Failed to resolve code {code}: {e}")
        
        # Final fallback to code value
        if not display_text:
            display_text = code
        
        return {
            'system': code_system,
            'version': coding.get('version'),
            'code': code,
            'display': coding.get('display'),
            'user_selected': coding.get('userSelected', False),
            'display_text': display_text
        }
    
    def _extract_codeable_concept(self, concept: Dict[str, Any]) -> Dict[str, Any]:
        """Extract FHIR R4 CodeableConcept data structure"""
        if not concept:
            return {}
        
        codings = []
        for coding in concept.get('coding', []):
            codings.append(self._extract_coding_data(coding))
        
        return {
            'coding': codings,
            'text': concept.get('text'),
            'display_text': concept.get('text') or (codings[0]['display_text'] if codings else 'Unknown concept'),
            'has_multiple_codings': len(codings) > 1,
            'primary_coding': codings[0] if codings else {}
        }
    
    def _convert_code_system_to_oid(self, code_system_url: str) -> str:
        """
        Convert FHIR code system URL to OID format for CTS lookup
        
        Args:
            code_system_url: FHIR code system URL (e.g., "http://standardterms.edqm.eu")
            
        Returns:
            OID or original URL if no mapping found
        """
        # Common FHIR code system URL to OID mappings
        url_to_oid = {
            # EDQM pharmaceutical forms and routes
            'http://standardterms.edqm.eu': '0.4.0.127.0.16.1.1.2.1',
            # ATC medication codes
            'http://www.whocc.no/atc': '2.16.840.1.113883.6.73',
            # SNOMED CT
            'http://snomed.info/sct': '2.16.840.1.113883.6.96',
            # LOINC
            'http://loinc.org': '2.16.840.1.113883.6.1',
            # ICD-10
            'http://hl7.org/fhir/sid/icd-10': '2.16.840.1.113883.6.3',
        }
        
        # If already an OID, return as-is
        if code_system_url and code_system_url[0].isdigit():
            return code_system_url
        
        # Try to find mapping
        for url_pattern, oid in url_to_oid.items():
            if url_pattern in code_system_url:
                return oid
        
        # Return original if no mapping found
        return code_system_url
    
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
        """Format immunizations for template display with enhanced fields"""
        formatted = []
        for imm in immunizations:
            formatted.append({
                'vaccine': imm['vaccine_code'].get('display', 'Unknown vaccine'),
                'status': imm.get('status', 'Unknown'),
                'date': imm.get('occurrence', 'Unknown'),
                'lot_number': imm.get('lot_number', 'Unknown'),
                'route': imm.get('route', {}).get('display', 'Unknown'),
                'performer': imm.get('performer', 'Unknown'),  # NEW: who administered
                'dose_number': imm.get('dose_number', None),    # NEW: dose number
                'site': imm.get('site', {}).get('display', 'Unknown')  # NEW: injection site
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