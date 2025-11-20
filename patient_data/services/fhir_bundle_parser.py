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
from dataclasses import dataclass, asdict
from patient_data.utils.date_formatter import ClinicalDateFormatter
from translation_services.enhanced_cts_service import EnhancedCTSService

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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class FHIRBundleParser:
    """
    Advanced FHIR Bundle Parser for Patient Summary processing
    
    Extracts clinical sections from FHIR R4 Patient Summary Bundle
    to feed into existing Django NCP view functions and templates.
    """
    
    def __init__(self):
        self.supported_resource_types = [
            'Patient', 'Composition', 'AllergyIntolerance', 'MedicationStatement',
            'Medication',  # Add Medication resources (referenced by MedicationStatement)
            'Condition', 'Procedure', 'Observation', 'Immunization', 
            'DiagnosticReport', 'Practitioner', 'Organization', 'Device', 'RelatedPerson',
            'Consent'  # Advance directives and patient consent
        ]
        
        # Store Medication resources for reference resolution
        self.medication_resources = {}
        
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
            'Condition:Active': {
                'section_type': 'problem_list',
                'display_name': 'Problem List',
                'icon': 'fa-list-ul'
            },
            'Condition:Resolved': {
                'section_type': 'past_illness',
                'display_name': 'History of Past Illness',
                'icon': 'fa-history'
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
            },
            'Consent': {
                'section_type': 'advance_directives',
                'display_name': 'Advance Directives',
                'icon': 'fa-file-contract'
            },
            'RelatedPerson': {
                'section_type': 'emergency_contacts',
                'display_name': 'Emergency Contacts',
                'icon': 'fa-users'
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
            
            # Store Medication resources for reference resolution (Azure FHIR now includes these!)
            if 'Medication' in resources_by_type:
                for med_resource in resources_by_type['Medication']:
                    med_id = med_resource.get('id')
                    if med_id:
                        self.medication_resources[med_id] = med_resource
                logger.info(f"Loaded {len(self.medication_resources)} Medication resources for reference resolution")
            
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
                resources_by_type.get('RelatedPerson', []),
                fhir_bundle
            )
            
            contact_data = self._extract_contact_data(
                resources_by_type.get('Patient', []),
                resources_by_type.get('RelatedPerson', []),
                administrative_data  # Pass administrative_data for other_contacts mapping
            )
            
            # Extract emergency contacts from RelatedPerson resources
            emergency_contacts = self._extract_emergency_contacts(
                resources_by_type.get('RelatedPerson', [])
            )
            
            practitioner_resources = resources_by_type.get('Practitioner', [])
            organization_resources = resources_by_type.get('Organization', [])
            composition_resources = resources_by_type.get('Composition', [])
            logger.info(f"[PARSER DEBUG] Extracting healthcare data: {len(practitioner_resources)} Practitioners, {len(organization_resources)} Organizations, {len(composition_resources)} Compositions")
            
            healthcare_data = self._extract_healthcare_data(
                practitioner_resources,
                organization_resources,
                composition_resources
            )
            
            # Map custodian organization from healthcare_data to administrative_data for template compatibility
            if healthcare_data.get('custodian_organization'):
                administrative_data['custodian_organization'] = healthcare_data['custodian_organization']
                logger.info(f"Mapped custodian organization to administrative_data: {administrative_data['custodian_organization']['name']}")
            
            # Create clinical arrays for view compatibility
            clinical_arrays = self._create_clinical_arrays(clinical_sections)
            
            # Convert FHIRClinicalSection objects to dictionaries for JSON serialization
            serializable_sections = {
                section_type: section.to_dict() if hasattr(section, 'to_dict') else section
                for section_type, section in clinical_sections.items()
            }
            
            # Create enhanced sections structure (compatible with existing views)
            enhanced_sections = {
                'success': True,
                'data_source': 'FHIR Patient Summary Bundle',
                'sections': list(serializable_sections.values()),
                'sections_count': len(serializable_sections),
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
                'emergency_contacts': emergency_contacts,
                'healthcare_data': healthcare_data,
                'patient_extended_data': {
                    'administrative': administrative_data,
                    'contact': contact_data,
                    'emergency_contacts': emergency_contacts,
                    'healthcare': healthcare_data,
                    'has_extended_data': bool(administrative_data or contact_data or emergency_contacts or healthcare_data)
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
            import traceback
            logger.error(f"Error parsing FHIR Bundle: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
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
        """Group FHIR resources by resourceType and deduplicate by version"""
        resources_by_type = {}
        
        for entry in fhir_bundle.get('entry', []):
            # Handle nested arrays (like in your EPSOS data)
            if isinstance(entry, list):
                for sub_entry in entry:
                    self._add_resource_to_group(sub_entry, resources_by_type)
            else:
                self._add_resource_to_group(entry, resources_by_type)
        
        # Deduplicate resources by keeping only the latest version
        resources_by_type = self._deduplicate_resources_by_version(resources_by_type)
        
        # Clinical deduplication for Conditions (same code + onset date)
        resources_by_type = self._deduplicate_conditions_clinically(resources_by_type)
        
        logger.info(f"[PARSER DEBUG] Grouped resources: Practitioner={len(resources_by_type.get('Practitioner', []))}, Organization={len(resources_by_type.get('Organization', []))}, Composition={len(resources_by_type.get('Composition', []))}")
        
        return resources_by_type
    
    def _add_resource_to_group(self, entry: Dict, resources_by_type: Dict[str, List]):
        """Add a single resource to the grouped collection"""
        resource = entry.get('resource', {})
        resource_type = resource.get('resourceType')
        
        if resource_type and resource_type in self.supported_resource_types:
            # Special handling for Condition resources - split by clinical status
            if resource_type == 'Condition':
                clinical_status = 'active'  # default
                if resource.get('clinicalStatus', {}).get('coding'):
                    clinical_status = resource['clinicalStatus']['coding'][0].get('code', 'active')
                
                # Create separate resource types for active vs resolved conditions
                # resolved, inactive, and remission all go to "History of Past Illness"
                if clinical_status in ['resolved', 'inactive', 'remission']:
                    condition_type = 'Condition:Resolved'
                else:
                    condition_type = 'Condition:Active'
                
                if condition_type not in resources_by_type:
                    resources_by_type[condition_type] = []
                resources_by_type[condition_type].append(resource)
                logger.info(f"[PARSER DEBUG] Added {condition_type} resource: {resource.get('id', 'unknown-id')}")
            else:
                if resource_type not in resources_by_type:
                    resources_by_type[resource_type] = []
                resources_by_type[resource_type].append(resource)
                logger.info(f"[PARSER DEBUG] Added {resource_type} resource: {resource.get('id', 'unknown-id')}")
    
    def _deduplicate_resources_by_version(self, resources_by_type: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """
        Deduplicate resources by keeping only the latest version of each resource.
        
        Azure FHIR may return multiple versions of the same resource (e.g., MedicationStatement v2 and v3).
        We need to keep only the latest version to avoid duplicates in the UI.
        
        Args:
            resources_by_type: Dictionary of resource type to list of resources
            
        Returns:
            Dictionary with deduplicated resources (only latest version per ID)
        """
        deduplicated = {}
        
        for resource_type, resources in resources_by_type.items():
            # Group by resource ID
            by_id = {}
            for resource in resources:
                resource_id = resource.get('id')
                if not resource_id:
                    # No ID - keep it (shouldn't happen in Azure FHIR)
                    if resource_type not in deduplicated:
                        deduplicated[resource_type] = []
                    deduplicated[resource_type].append(resource)
                    continue
                
                # Get version from meta.versionId
                version_id = resource.get('meta', {}).get('versionId', '0')
                try:
                    version_num = int(version_id)
                except (ValueError, TypeError):
                    version_num = 0
                
                # Keep resource with highest version
                if resource_id not in by_id or version_num > by_id[resource_id]['version']:
                    by_id[resource_id] = {
                        'resource': resource,
                        'version': version_num
                    }
            
            # Extract deduplicated resources
            if by_id:
                if resource_type not in deduplicated:
                    deduplicated[resource_type] = []
                
                for resource_id, data in by_id.items():
                    deduplicated[resource_type].append(data['resource'])
                    logger.info(f"[DEDUP] Kept {resource_type} {resource_id} version {data['version']}")
        
        return deduplicated
    
    def _deduplicate_conditions_clinically(self, resources_by_type: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """
        Clinical deduplication for Condition resources.
        
        Remove duplicates with same code + onset date, keeping the most complete record.
        Similar to medication deduplication logic.
        
        Args:
            resources_by_type: Dictionary of resource type to list of resources
            
        Returns:
            Dictionary with clinically deduplicated conditions
        """
        deduplicated = {}
        
        for resource_type, resources in resources_by_type.items():
            # Only apply clinical deduplication to Condition resources
            if resource_type not in ['Condition:Active', 'Condition:Resolved']:
                deduplicated[resource_type] = resources
                continue
            
            # Group conditions by code + onset date
            condition_groups = {}
            
            for resource in resources:
                # Extract condition code
                code = None
                if resource.get('code', {}).get('coding'):
                    code = resource['code']['coding'][0].get('code')
                
                # Extract onset date
                onset_date = resource.get('onsetDateTime', '')
                if not onset_date:
                    onset_date = resource.get('onsetPeriod', {}).get('start', '')
                
                # Create key: code + onset_date
                key = f"{code}_{onset_date}"
                
                if key not in condition_groups:
                    condition_groups[key] = []
                condition_groups[key].append(resource)
            
            # For each group, keep the most complete record
            deduplicated[resource_type] = []
            for key, group in condition_groups.items():
                if len(group) == 1:
                    deduplicated[resource_type].append(group[0])
                else:
                    # Keep condition with most complete data
                    # Priority: has severity > has category > has verificationStatus
                    best_condition = max(group, key=lambda c: (
                        bool(c.get('severity', {}).get('coding')),
                        bool(c.get('category')),
                        bool(c.get('verificationStatus', {}).get('coding'))
                    ))
                    deduplicated[resource_type].append(best_condition)
                    logger.info(f"[CONDITION DEDUP] Removed {len(group) - 1} duplicate(s) for key {key}, kept condition {best_condition.get('id')}")
        
        return deduplicated
    
    def _deduplicate_medications_clinically(self, medications: List[Dict]) -> List[Dict]:
        """
        Deduplicate medications by clinical identity (medication name or ATC code).
        
        Azure FHIR may contain multiple MedicationStatement resources representing the same
        clinical medication (e.g., two records for "Levothyroxine" with different IDs).
        This happens when data is migrated or records are updated without proper deduplication.
        
        We group medications by their clinical identifier (ATC code preferred, name as fallback)
        and keep only the medication with the most complete data (highest completeness score).
        
        Args:
            medications: List of parsed medication dictionaries
            
        Returns:
            List of clinically deduplicated medications
        """
        if not medications:
            return medications
        
        # Group medications by clinical identifier
        clinical_groups = {}
        
        for med in medications:
            # Get clinical identifier - prefer ATC code, fallback to medication name
            atc_code = med.get('atc_code', '').strip().upper()
            med_name = med.get('medication_name', '').strip().lower()
            
            # Create unique key: use ATC code if available, otherwise use medication name
            if atc_code and atc_code not in ['UNKNOWN', 'NOT SPECIFIED', '']:
                key = f"ATC:{atc_code}"
            elif med_name and med_name not in ['unknown', 'not specified', '']:
                key = f"NAME:{med_name}"
            else:
                # No valid identifier - keep this medication (shouldn't deduplicate without identity)
                key = f"UNKNOWN:{id(med)}"  # Use Python object ID as unique key
            
            if key not in clinical_groups:
                clinical_groups[key] = []
            clinical_groups[key].append(med)
        
        # For each clinical group, keep the medication with most complete data
        deduplicated = []
        
        for key, group in clinical_groups.items():
            if len(group) == 1:
                # Only one medication for this clinical identifier - keep it
                deduplicated.append(group[0])
                logger.info(f"[CLINICAL DEDUP] Kept unique medication: {key}")
            else:
                # Multiple medications for same clinical entity - score by completeness
                scored_meds = []
                for med in group:
                    score = self._calculate_medication_completeness_score(med)
                    scored_meds.append((score, med))
                
                # Sort by score (descending) and keep the best one
                scored_meds.sort(key=lambda x: x[0], reverse=True)
                best_med = scored_meds[0][1]
                best_score = scored_meds[0][0]
                
                deduplicated.append(best_med)
                logger.info(f"[CLINICAL DEDUP] Grouped {len(group)} medications as {key}, kept best (score: {best_score}/5)")
                
                # Log rejected duplicates
                for score, med in scored_meds[1:]:
                    logger.info(f"[CLINICAL DEDUP] Rejected duplicate with score {score}/5: {med.get('medication_name', 'Unknown')}")
        
        logger.info(f"[CLINICAL DEDUP] Clinical deduplication: {len(medications)} medications -> {len(deduplicated)} unique medications")
        return deduplicated
    
    def _calculate_medication_completeness_score(self, medication: Dict) -> int:
        """
        Calculate completeness score for a medication (0-5, higher = more complete).
        
        Scores medication based on presence of key clinical fields:
        - Pharmaceutical form (tablet, capsule, etc.)
        - Strength (dose per unit)
        - Dosage instructions
        - Route of administration
        - Schedule/timing
        
        Args:
            medication: Parsed medication dictionary
            
        Returns:
            Integer score (0-5) representing data completeness
        """
        score = 0
        
        # Define fields to check and invalid values that don't count as "complete"
        invalid_values = {
            'not specified',
            'not available in source document',
            'unknown',
            'no dosage information',
            'not applicable',
            '',
            'n/a'
        }
        
        # Check pharmaceutical form
        pharma_form = medication.get('pharmaceutical_form', '').strip().lower()
        if pharma_form and pharma_form not in invalid_values:
            score += 1
        
        # Check strength
        strength = medication.get('strength', '').strip().lower()
        if strength and strength not in invalid_values:
            score += 1
        
        # Check dosage
        dosage = medication.get('dosage', '').strip().lower()
        if dosage and dosage not in invalid_values:
            score += 1
        
        # Check route
        route = medication.get('route', '').strip().lower()
        if route and route not in invalid_values:
            score += 1
        
        # Check schedule
        schedule = medication.get('schedule', '').strip().lower()
        if schedule and schedule not in invalid_values:
            score += 1
        
        return score
    
    def _parse_clinical_section(self, resource_type: str, resources: List[Dict], section_info: Dict) -> FHIRClinicalSection:
        """Parse specific resource type into clinical section"""
        
        parsed_entries = []
        
        if resource_type == 'Patient':
            parsed_entries = [self._parse_patient_resource(resource) for resource in resources]
        elif resource_type == 'AllergyIntolerance':
            parsed_entries = [self._parse_allergy_resource(resource) for resource in resources]
        elif resource_type == 'MedicationStatement':
            parsed_entries = [self._parse_medication_resource(resource) for resource in resources]
        elif resource_type in ['Condition:Active', 'Condition:Resolved']:
            # Parse condition resources (now split by clinical status)
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
        elif resource_type == 'Consent':
            parsed_entries = [self._parse_consent_resource(resource) for resource in resources]
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
    
    def _format_allergy_onset_date(self, allergy: Dict[str, Any], is_negative_assertion: bool) -> str:
        """Format allergy onset date using ClinicalDateFormatter
        
        Args:
            allergy: FHIR AllergyIntolerance resource
            is_negative_assertion: Whether this is a negative assertion
            
        Returns:
            Formatted date string
        """
        if is_negative_assertion:
            return 'Not applicable'
        
        # Extract raw onset date from various fields
        raw_onset = (
            allergy.get('onsetDateTime') or 
            allergy.get('onsetString') or 
            (allergy.get('onsetPeriod', {}).get('start') if allergy.get('onsetPeriod') else None) or
            'Unknown'
        )
        
        # Format the date if it's not a placeholder
        if raw_onset and raw_onset not in ('Unknown', 'Not applicable'):
            return ClinicalDateFormatter.format_clinical_date(raw_onset)
        return raw_onset
    
    def _parse_allergy_resource(self, allergy: Dict[str, Any]) -> Dict[str, Any]:
        """Parse FHIR AllergyIntolerance resource with CTS agent code resolution
        
        IMPORTANT: Use CTS agent for allergen name lookup (same as CDA XSLT process)
        - Extract code from FHIR resource (ATC, SNOMED CT, etc.)
        - Resolve via CTS agent to get standardized allergen name
        - Same resolution strategy as medications and conditions
        """
        # Extract allergen with support for negative assertions
        code = allergy.get('code', {})
        allergen = 'Unknown allergen'
        is_negative_assertion = False
        code_value = ''
        code_system = ''
        
        if code.get('coding'):
            coding = code['coding'][0]
            code_value = coding.get('code', '')
            code_system = coding.get('system', '')
            display = coding.get('display', '')
            
            # Check for negative assertion codes
            if code_value in ['no-allergy-info', 'no-known-allergies', 'no-drug-allergies']:
                is_negative_assertion = True
                allergen = display or 'No allergy information available'
            else:
                # PRIORITY 1: Use display name if provided in FHIR
                if display:
                    allergen = display
                    logger.info(f"Using FHIR display for allergy: {allergen}")
                else:
                    # PRIORITY 2: Resolve via CTS agent (ATC, SNOMED, etc.)
                    try:
                        from translation_services.terminology_translator import TerminologyTranslator
                        translator = TerminologyTranslator()
                        
                        # Attempt to resolve the code based on system
                        resolved_name = None
                        
                        # Try system-specific OID if available
                        if 'atc' in code_system.lower():
                            # ATC code - use WHO ATC OID
                            logger.info(f"Attempting ATC resolution for allergy code: {code_value}")
                            resolved_name = translator.resolve_code(code_value, '2.16.840.1.113883.6.73')
                        elif 'snomed' in code_system.lower():
                            # SNOMED CT code - use SNOMED OID
                            logger.info(f"Attempting SNOMED CT resolution for allergy code: {code_value}")
                            resolved_name = translator.resolve_code(code_value, '2.16.840.1.113883.6.96')
                        else:
                            # Try generic resolution
                            logger.info(f"Attempting generic resolution for allergy code: {code_value}")
                            resolved_name = translator.resolve_code(code_value)
                        
                        if resolved_name and resolved_name != code_value:
                            allergen = resolved_name
                            logger.info(f"[ALLERGY] Resolved allergy code {code_value} to: {allergen}")
                        else:
                            # Fallback to code value if resolution failed
                            allergen = code_value
                            logger.warning(f"Could not resolve allergy code: {code_value} from {code_system}")
                    
                    except Exception as e:
                        logger.warning(f"CTS resolution failed for allergy code {code_value}: {e}")
                        allergen = code_value
        elif code.get('text'):
            allergen = code['text']
        
        # Extract clinical status (use code if display not available)
        clinical_status = 'Unknown'
        if allergy.get('clinicalStatus', {}).get('coding'):
            coding = allergy['clinicalStatus']['coding'][0]
            clinical_status = coding.get('display') or coding.get('code', 'Unknown')
            # Capitalize first letter for display
            if clinical_status != 'Unknown':
                clinical_status = clinical_status.capitalize()
            if is_negative_assertion:
                clinical_status = 'Not applicable'
        
        # Extract verification status (use code if display not available)
        verification_status = 'Unknown'
        if allergy.get('verificationStatus', {}).get('coding'):
            coding = allergy['verificationStatus']['coding'][0]
            verification_status = coding.get('display') or coding.get('code', 'Unknown')
            # Capitalize first letter for display
            if verification_status != 'Unknown':
                verification_status = verification_status.capitalize()
            if is_negative_assertion:
                verification_status = 'Not applicable'
        
        # Extract severity and reactions with FHIR R4 data type support (only for actual allergies)
        reactions = []
        if not is_negative_assertion:
            # Import enhanced FHIR processor for complex data types
            from eu_ncp_server.services.fhir_processing import FHIRResourceProcessor
            processor = FHIRResourceProcessor()
            
            for reaction in allergy.get('reaction', []):
                # Extract reaction severity with FHIR R4 CodeableConcept support
                severity = 'Unknown'
                severity_data = {}
                if reaction.get('severity'):
                    severity = reaction['severity']
                    # Note: severity in FHIR R4 is a code (mild | moderate | severe)
                    severity_data = {'code': severity, 'display': severity.capitalize()}
                
                # Extract manifestation with FHIR R4 CodeableConcept support
                manifestation_text = 'Unknown reaction'
                manifestation_data = {}
                if reaction.get('manifestation'):
                    manifestation = reaction['manifestation'][0]
                    manifestation_data = processor._extract_codeable_concept(manifestation)
                    manifestation_text = manifestation_data.get('display_text', 'Unknown reaction')
                
                # Extract onset with FHIR R4 Period support if available
                onset_data = {}
                onset_text = 'Unknown onset'
                if reaction.get('onset'):
                    onset_text = reaction['onset']
                elif reaction.get('onsetPeriod'):
                    onset_data = processor._extract_period_data(reaction['onsetPeriod'])
                    onset_text = onset_data.get('start_display', 'Unknown onset')
                
                # Extract exposure route with FHIR R4 CodeableConcept support
                exposure_route_data = {}
                exposure_route_text = 'Unknown route'
                if reaction.get('exposureRoute'):
                    exposure_route_data = processor._extract_codeable_concept(reaction['exposureRoute'])
                    exposure_route_text = exposure_route_data.get('display_text', 'Unknown route')
                
                reactions.append({
                    'severity': severity,
                    'severity_data': severity_data,
                    'manifestation': manifestation_text,
                    'manifestation_data': manifestation_data,
                    'onset': onset_text,
                    'onset_data': onset_data,
                    'exposure_route': exposure_route_text,
                    'exposure_route_data': exposure_route_data,
                    'substance': reaction.get('substance', {}),  # Additional substance if different from main allergen
                    'description': reaction.get('description', ''),
                    'note': reaction.get('note', '')
                })
        
        # Extract category with FHIR R4 support for multiple categories
        categories = []
        category_display = 'Unknown'
        if allergy.get('category'):
            categories = allergy['category']  # Can be multiple: food, medication, environment, biologic
            category_display = ', '.join(categories) if categories else 'Unknown'
        
        # Extract criticality (low | high | unable-to-assess)
        criticality = allergy.get('criticality', 'Unknown')
        
        # Extract type with enhanced display
        allergy_type = allergy.get('type', 'Unknown')
        type_display = allergy_type.replace('_', ' ').title() if allergy_type != 'Unknown' else 'Unknown'
        
        # Extract FHIR R4 Annotation notes (clinical comments about allergies)
        notes = []
        annotation_text = ''
        if allergy.get('note'):
            # Import the enhanced annotation processor
            from eu_ncp_server.services.fhir_processing import FHIRResourceProcessor
            processor = FHIRResourceProcessor()
            
            # Extract full annotation data with author and timestamp
            notes = processor._extract_annotation_data(allergy['note'])
            
            # Also extract simple text for backward compatibility
            annotation_text = processor._extract_annotation_text(allergy['note'])

        return {
            'id': allergy.get('id'),
            'allergen': allergen,
            'clinical_status': clinical_status,
            'verification_status': verification_status,
            'type': allergy_type,
            'type_display': type_display,
            'category': categories,
            'category_display': category_display,
            'criticality': criticality,
            'reactions': reactions,
            'reaction_count': len(reactions),
            'onset_date': self._format_allergy_onset_date(allergy, is_negative_assertion),
            'notes': notes,  # Full FHIR R4 Annotation data
            'note_text': annotation_text,  # Simple text for display
            'has_notes': bool(notes),
            'has_reactions': bool(reactions),
            'resource_type': 'AllergyIntolerance',
            'display_text': f"Allergy: {allergen} ({clinical_status})",
            'is_negative_assertion': is_negative_assertion,
            'severity_summary': self._get_allergy_severity_summary(reactions) if reactions else 'Not applicable'
        }
    
    def _parse_medication_resource(self, medication: Dict[str, Any]) -> Dict[str, Any]:
        """Parse FHIR MedicationStatement resource with support for negative assertions
        
        IMPORTANT: Use CTS agent for medication name lookup (same as CDA XSLT process)
        - Extract ATC code from FHIR resource
        - Resolve via CTS agent to get standardized medication name
        - Ignore display/text fields from foreign member states (may be in local language)
        - This ensures consistency with CDA clinical sections pipeline
        """
        medication_name = 'Unknown medication'
        atc_code = None
        is_negative_assertion = False
        strength_from_text = None  # Extract early before CTS translation
        referenced_medication = None  # For strength extraction from Medication resource
        
        # PRIORITY 1: Check for medicationReference (Azure FHIR now uses this!)
        if medication.get('medicationReference', {}).get('reference'):
            med_ref = medication['medicationReference']['reference']
            # Extract ID from reference (e.g., "Medication/med-h03aa01" -> "med-h03aa01")
            med_id = med_ref.split('/')[-1] if '/' in med_ref else med_ref
            
            # Get referenced Medication resource from bundle
            if med_id in self.medication_resources:
                referenced_medication = self.medication_resources[med_id]
                logger.info(f"Resolved medicationReference: {med_id}")
                
                # Extract ATC code from referenced Medication
                if referenced_medication.get('code', {}).get('coding'):
                    coding = referenced_medication['code']['coding'][0]
                    if coding.get('system') == 'http://www.whocc.no/atc':
                        atc_code = coding.get('code')
        
        # EARLY EXTRACTION: Get strength from medicationCodeableConcept.text BEFORE CTS translation
        # This preserves strength info like "Amoxicillin 500 mg" before name becomes "Amoxicillin and Clavulanic Acid"
        if medication.get('medicationCodeableConcept', {}).get('text'):
            import re
            med_text = medication['medicationCodeableConcept']['text']
            strength_pattern = r'(\d+(?:\.\d+)?)\s*(mcg|mg|ug|g|ml|iu|units?)'
            strength_match = re.search(strength_pattern, med_text, re.IGNORECASE)
            if strength_match:
                strength_value = strength_match.group(1)
                strength_unit = strength_match.group(2)
                # Normalize mcg to ug (UCUM standard)
                if strength_unit.lower() == 'mcg':
                    strength_unit = 'ug'
                strength_from_text = f"{strength_value} {strength_unit}"
        
        # Priority 2: Extract ATC code from medicationCodeableConcept (fallback if no reference)
        if not atc_code and medication.get('medicationCodeableConcept', {}).get('coding'):
            coding = medication['medicationCodeableConcept']['coding'][0]
            code = coding.get('code', '')
            
            # Check for negative assertion codes
            if code in ['no-medication-info', 'no-drug-therapy', 'no-current-medication']:
                is_negative_assertion = True
                medication_name = coding.get('display', 'No medication information available')
            elif coding.get('system') == 'http://www.whocc.no/atc' and code:
                # ALWAYS use CTS agent lookup for ATC codes (same as CDA process)
                atc_code = code
        
        # Resolve medication name via CTS if we have ATC code
        if atc_code and not is_negative_assertion:
            medication_name = self._get_atc_drug_name(atc_code) or f"ATC Code: {atc_code}"
        
        # Priority 2: Fallback to text fields only if no ATC code available
        # (This maintains compatibility but ATC codes should be preferred)
        if not atc_code and not is_negative_assertion:
            if medication.get('medicationCodeableConcept', {}).get('text'):
                medication_name = medication['medicationCodeableConcept']['text']
            elif medication.get('medicationReference', {}).get('display'):
                medication_name = medication['medicationReference']['display']
        
        # Extract enhanced dosage information with FHIR R4 data types
        dosage_text = 'No dosage information'
        dosage_timing = {}
        dosage_quantity = {}
        dosage_route = {}
        
        if not is_negative_assertion:
            dosages = medication.get('dosage', [])
            if dosages:
                dosage = dosages[0]
                
                # Import enhanced FHIR processor for data type extraction
                from eu_ncp_server.services.fhir_processing import FHIRResourceProcessor
                processor = FHIRResourceProcessor()
                
                # Extract text instruction
                if dosage.get('text'):
                    dosage_text = dosage['text']
                
                # Extract structured dose and rate with FHIR R4 Quantity support
                elif dosage.get('doseAndRate'):
                    dose_rate = dosage['doseAndRate'][0]
                    if dose_rate.get('doseQuantity'):
                        dosage_quantity = processor._extract_quantity_data(dose_rate['doseQuantity'])
                        dosage_text = dosage_quantity.get('display_value', 'Unknown dose')
                    elif dose_rate.get('doseRange'):
                        dose_range = processor._extract_range_data(dose_rate['doseRange'])
                        dosage_text = dose_range.get('display_range', 'Unknown dose range')
                
                # Extract timing information with FHIR R4 Timing support
                if dosage.get('timing'):
                    dosage_timing = processor._extract_timing_data(dosage['timing'])
                    if dosage_timing.get('display_schedule'):
                        timing_text = dosage_timing['display_schedule']
                        if dosage_text != 'No dosage information':
                            dosage_text += f" - {timing_text}"
                        else:
                            dosage_text = timing_text
                
                # Extract route with FHIR R4 CodeableConcept support
                if dosage.get('route'):
                    dosage_route = processor._extract_codeable_concept(dosage['route'])
                    route_text = dosage_route.get('display_text', '')
                    if route_text and dosage_text != 'No dosage information':
                        dosage_text += f" ({route_text})"
        else:
            dosage_text = 'Not applicable - no medication information'
        
        # Extract status and effective period/datetime with FHIR R4 support
        status = medication.get('status', 'Unknown')
        if is_negative_assertion:
            status = 'No information available'
            
        effective_period = 'Unknown period'
        effective_period_data = {}
        start_date = None
        
        # PRIORITY 1: Check for effectivePeriod (date range - "between X and Y")
        if not is_negative_assertion and medication.get('effectivePeriod'):
            # Import enhanced FHIR processor for Period extraction
            from eu_ncp_server.services.fhir_processing import FHIRResourceProcessor
            processor = FHIRResourceProcessor()
            
            effective_period_data = processor._extract_period_data(medication['effectivePeriod'])
            
            # Use enhanced period display or fallback to basic format
            if effective_period_data.get('start_display') or effective_period_data.get('end_display'):
                start = effective_period_data.get('start_display', 'Unknown start')
                end = effective_period_data.get('end_display', 'Ongoing')
                effective_period = f"{start} to {end}"
                
                # Add duration if calculated
                if effective_period_data.get('duration_display'):
                    effective_period += f" ({effective_period_data['duration_display']})"
            else:
                # Fallback to basic display
                period = medication['effectivePeriod']
                start = period.get('start', 'Unknown start')
                end = period.get('end', 'Ongoing')
                effective_period = f"{start} to {end}"
            
            # Extract start_date for template compatibility
            start_date = medication['effectivePeriod'].get('start')
            
        # PRIORITY 2: Check for effectiveDateTime (single date - "since X")
        elif not is_negative_assertion and medication.get('effectiveDateTime'):
            effective_datetime = medication['effectiveDateTime']
            effective_period = f"Since {effective_datetime}"
            start_date = effective_datetime
            logger.info(f"Extracted effectiveDateTime: {effective_datetime}")
            
        elif is_negative_assertion:
            effective_period = 'Not applicable'
        
        # Extract FHIR R4 Annotation notes (prescriber notes, patient instructions, etc.)
        notes = []
        annotation_text = ''
        if medication.get('note'):
            # Import the enhanced annotation processor
            from eu_ncp_server.services.fhir_processing import FHIRResourceProcessor
            processor = FHIRResourceProcessor()
            
            # Extract full annotation data with author and timestamp
            notes = processor._extract_annotation_data(medication['note'])
            
            # Also extract simple text for backward compatibility
            annotation_text = processor._extract_annotation_text(medication['note'])

        # Enhanced Template Compatibility Fields
        # Add fields that medication templates expect for proper display
        
        # Extract medication codes from medicationCodeableConcept
        active_ingredient_code = atc_code or None
        
        if medication.get('medicationCodeableConcept', {}).get('coding'):
            # Direct code in MedicationStatement
            coding = medication['medicationCodeableConcept']['coding'][0]
            if not active_ingredient_code:
                active_ingredient_code = coding.get('code')
        
        # Create active_ingredient as simple string (matches CDA pipeline structure)
        # CDA example: "levothyroxine sodium (100 ug / 1)"
        # FHIR example: "See medication name (ATC: H03AA01)"
        # 
        # FHIR data typically provides ATC codes; brand/generic distinction varies by implementation
        # To avoid redundant display (medication name appearing twice), show ATC reference
        if atc_code:
            # Show ATC code reference instead of duplicating medication name
            active_ingredient = f"See medication name (ATC: {atc_code})"
        else:
            # Fallback when no ATC code available
            active_ingredient = "Not specified"
        
        # Extract template fields from dosage information
        pharmaceutical_form = 'Not specified'
        strength = 'Not specified'
        dose_quantity_value = 'Not specified'
        administration_route = 'Not specified'
        schedule_info = 'Not specified'
        
        import re
        
        # Extract pharmaceutical form from dosage.text (EDQM form codes)
        # Azure FHIR format: "1-2 1 Form code: 10219000 in the morning"
        if dosages:
            dosage = dosages[0]
            dosage_text_raw = dosage.get('text', '')
            
            # Extract EDQM form code from text
            form_code_match = re.search(r'Form code:\s*(\d+)', dosage_text_raw)
            if form_code_match:
                form_code = form_code_match.group(1)
                # Use CTS to resolve EDQM form code
                from translation_services.terminology_translator import TerminologyTranslator
                translator = TerminologyTranslator()
                resolved_form = translator.resolve_code(form_code, '0.4.0.127.0.16.1.1.2.1')  # EDQM OID
                if resolved_form:
                    pharmaceutical_form = resolved_form
            
            # Extract strength from multiple sources (priority order)
            # Pattern 1: BEST - Extract from referenced Medication.ingredient[].strength (Azure FHIR now provides this!)
            if referenced_medication and referenced_medication.get('ingredient'):
                strength_parts = []
                for ingredient in referenced_medication['ingredient']:
                    if ingredient.get('strength'):
                        ratio = ingredient['strength']
                        
                        # Type check: strength should be dict (Ratio), not string
                        if isinstance(ratio, str):
                            logger.warning(f"[FHIR] Medication strength is string instead of Ratio dict: {ratio}")
                            strength_parts.append(ratio)
                            continue
                        
                        num = ratio.get('numerator', {})
                        den = ratio.get('denominator', {})
                        
                        num_value = num.get('value')
                        num_unit = num.get('unit', num.get('code', ''))
                        den_value = den.get('value', 1)
                        den_unit = den.get('unit', den.get('code', ''))
                        
                        # Format strength as "100 ug/1" or "100 ug/1 tablet"
                        if num_value:
                            if den_value == 1 and den_unit in ['1', '']:
                                strength_parts.append(f"{num_value} {num_unit}")
                            else:
                                strength_parts.append(f"{num_value} {num_unit}/{den_value} {den_unit}")
                
                # Join multi-ingredient strengths with " + "
                if strength_parts:
                    strength = " + ".join(strength_parts)
                    logger.info(f"Extracted strength from Medication resource: {strength}")
            
            # Pattern 2: Use early-extracted strength from medicationCodeableConcept.text
            elif strength_from_text:
                strength = strength_from_text
            
            # Pattern 3: "Strength code: 12345" in dosage.text (EDQM code via CTS)
            else:
                strength_code_match = re.search(r'Strength code:\s*(\d+)', dosage_text_raw)
                if strength_code_match:
                    strength_code = strength_code_match.group(1)
                    # Use CTS to resolve EDQM strength code
                    translator = TerminologyTranslator()
                    resolved_strength = translator.resolve_code(strength_code, '0.4.0.127.0.16.1.1.2.2')  # EDQM Strength OID
                    if resolved_strength:
                        strength = resolved_strength
            
            # Extract dose quantity from doseAndRate
            if dosage.get('doseAndRate'):
                dose_rate = dosage['doseAndRate'][0]
                
                # Handle doseRange (e.g., 1-2 units)
                if dose_rate.get('doseRange'):
                    low = dose_rate['doseRange'].get('low', {})
                    high = dose_rate['doseRange'].get('high', {})
                    low_val = low.get('value')
                    high_val = high.get('value')
                    unit = low.get('unit', high.get('unit', ''))
                    ucum_code = low.get('code', high.get('code', ''))
                    
                    # Map UCUM code "1" (dimensionless) to pharmaceutical form
                    if ucum_code == '1' or unit == '1':
                        if pharmaceutical_form and pharmaceutical_form != 'Not specified':
                            # Use pharmaceutical form as unit (e.g., "tablet(s)")
                            unit = pharmaceutical_form.lower() + '(s)' if pharmaceutical_form else 'unit(s)'
                        else:
                            unit = 'unit(s)'
                    
                    if low_val and high_val:
                        dose_quantity_value = f"{low_val}-{high_val} {unit}"
                    elif low_val:
                        dose_quantity_value = f"{low_val} {unit}"
                
                # Handle doseQuantity (e.g., 100 ug)
                elif dose_rate.get('doseQuantity'):
                    dose_qty = dose_rate['doseQuantity']
                    value = dose_qty.get('value')
                    unit = dose_qty.get('unit', '')
                    ucum_code = dose_qty.get('code', '')
                    
                    # Map UCUM code "1" to pharmaceutical form
                    if ucum_code == '1' or unit == '1':
                        if pharmaceutical_form and pharmaceutical_form != 'Not specified':
                            unit = pharmaceutical_form.lower() + '(s)'
                        else:
                            unit = 'unit(s)'
                    
                    if value:
                        dose_quantity_value = f"{value} {unit}"
        
        # Fallback: Extract dose from text patterns if structured data not available
        if dose_quantity_value == 'Not specified':
            dose_pattern = r'(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*(mg|ug|mcg|g|ml|iu|units?)'
            dose_match = re.search(dose_pattern, f"{medication_name} {dosage_text}".lower())
            if dose_match:
                dose_quantity_value = f"{dose_match.group(1)} {dose_match.group(2)}"
        
        # Extract route from dosage information (CTS already resolves EDQM codes)
        if dosage_route.get('display_text'):
            administration_route = dosage_route['display_text']
        # Fallback: Extract route directly from dosage if not already extracted
        elif dosages:
            dosage = dosages[0]
            if dosage.get('route'):
                from eu_ncp_server.services.fhir_processing import FHIRResourceProcessor
                processor = FHIRResourceProcessor()
                route_data = processor._extract_codeable_concept(dosage['route'])
                if route_data.get('display_text'):
                    administration_route = route_data['display_text']
        
        # Extract schedule from timing.repeat.when codes
        if dosages:
            dosage = dosages[0]
            timing = dosage.get('timing', {})
            repeat = timing.get('repeat', {})
            when_codes = repeat.get('when', [])
            
            # Map FHIR timing codes to human-readable schedule
            timing_map = {
                'MORN': 'Morning',
                'ACM': 'Morning',  # FHIR EventTiming: ACM = "morning"
                'ACD': 'Afternoon',  # FHIR EventTiming: ACD = "afternoon"
                'ACV': 'Evening',  # FHIR EventTiming: ACV = "evening"
                'ACN': 'Night',  # FHIR EventTiming: ACN = "night"
                'AFT': 'Afternoon',
                'EVE': 'Evening',
                'NIGHT': 'Night',
                'PHS': 'After sleep',
                'HS': 'Before sleep',
                'WAKE': 'Upon waking',
                'C': 'With meals',
                'CM': 'With breakfast',
                'CD': 'With lunch',
                'CV': 'With dinner',
                'AC': 'Before meals',
                'PC': 'After meals',
                'PCM': 'After breakfast',
                'PCD': 'After lunch',
                'PCV': 'After dinner'
            }
            
            if when_codes:
                schedule_parts = [timing_map.get(code, code) for code in when_codes]
                schedule_info = ', '.join(schedule_parts)
                
                # Add frequency if available
                frequency = repeat.get('frequency')
                period = repeat.get('period')
                period_unit = repeat.get('periodUnit', 'd')
                
                if frequency and period:
                    freq_text = f"{frequency} time(s) per {period} {period_unit}"
                    schedule_info = f"{schedule_info} - {freq_text}"
            
            # Fallback to display_schedule from enhanced processor
            elif dosage_timing.get('display_schedule'):
                schedule_info = dosage_timing['display_schedule']
        
        # Text-based fallback if structured data not available
        if schedule_info == 'Not specified':
            if 'once' in dosage_text.lower():
                schedule_info = 'Once daily'
            elif 'twice' in dosage_text.lower():
                schedule_info = 'Twice daily'
        
        # Create data nested structure for template compatibility
        data_structure = {
            'active_ingredient': active_ingredient,
            'pharmaceutical_form': pharmaceutical_form,
            'strength': strength,
            'dose_quantity': dose_quantity_value,
            'administration_route': administration_route,
            'schedule': schedule_info,
            'period': effective_period if effective_period != 'Not applicable' and effective_period != 'Unknown period' else None
        }

        return {
            'id': medication.get('id'),
            'medication_name': medication_name,
            'name': medication_name,  # Template compatibility
            'display_name': medication_name,  # Template compatibility
            'strength': strength,  # Top-level for template compatibility
            'status': status.capitalize(),
            'dosage': dosage_text,
            'effective_period': effective_period,
            'start_date': start_date,  # Template compatibility - used by medication_section.html
            'taken': medication.get('taken', 'Unknown'),
            'notes': notes,  # Full FHIR R4 Annotation data
            'note_text': annotation_text,  # Simple text for display
            'has_notes': bool(notes),
            'resource_type': 'MedicationStatement',
            
            # ENHANCED TEMPLATE COMPATIBILITY FIELDS (matching CDA structure)
            'active_ingredient': active_ingredient,    # Simple string: "See medication name (ATC: H03AA01)"
            'pharmaceutical_form': pharmaceutical_form,
            'dose_quantity': dose_quantity_value,
            'route': administration_route,
            'schedule': schedule_info,
            'data': data_structure,  # Nested data structure for template fallbacks
            'display_text': f"Medication: {medication_name} ({status})",
            'is_negative_assertion': is_negative_assertion
        }
    
    def _parse_condition_resource(self, condition: Dict[str, Any]) -> Dict[str, Any]:
        """Parse FHIR Condition resource with ICD-10/SNOMED code resolution via CTS agent"""
        # Import enhanced FHIR processor for CodeableConcept with CTS support
        from eu_ncp_server.services.fhir_processing import FHIRResourceProcessor
        processor = FHIRResourceProcessor()
        
        # Extract condition name with support for negative assertions and CTS code resolution
        code = condition.get('code', {})
        condition_name = 'Unknown condition'
        condition_code = None
        code_system = None
        is_negative_assertion = False
        code_data = {}
        
        if code:
            # Use unified CTS-enabled extraction
            code_data = processor._extract_codeable_concept(code)
            condition_code = code_data.get('code', '')
            code_system = code_data.get('system', '')
            condition_name = code_data.get('display_text', 'Unknown condition')
            
            # Check for negative assertion codes
            if condition_code in ['no-problem-info', 'no-condition-info', 'no-known-problems']:
                is_negative_assertion = True
                if not condition_name or condition_name == 'Unknown condition':
                    condition_name = 'No condition information available'
        
        # Extract clinical status
        clinical_status = 'Unknown'
        if condition.get('clinicalStatus', {}).get('coding'):
            coding = condition['clinicalStatus']['coding'][0]
            # PRIORITY 1: Use display if available
            clinical_status = coding.get('display')
            # PRIORITY 2: Use code field and capitalize it
            if not clinical_status:
                code_value = coding.get('code', '')
                if code_value:
                    # Capitalize code: 'active' -> 'Active', 'resolved' -> 'Resolved'
                    clinical_status = code_value.capitalize()
            # Default fallback
            if not clinical_status:
                clinical_status = 'Unknown'
            
            if is_negative_assertion:
                clinical_status = 'Not applicable'
        
        # Extract verification status
        verification_status = 'Unknown'
        if condition.get('verificationStatus', {}).get('coding'):
            coding = condition['verificationStatus']['coding'][0]
            # PRIORITY 1: Use display if available
            verification_status = coding.get('display')
            # PRIORITY 2: Use code field and capitalize it
            if not verification_status:
                code_value = coding.get('code', '')
                if code_value:
                    # Capitalize code: 'confirmed' -> 'Confirmed', 'unconfirmed' -> 'Unconfirmed'
                    verification_status = code_value.capitalize()
            # Default fallback
            if not verification_status:
                verification_status = 'Unknown'
            
            if is_negative_assertion:
                verification_status = 'Not applicable'
        
        # Extract category (problem type) - only for actual conditions
        category = 'Not specified'
        category_code = None
        if not is_negative_assertion and condition.get('category'):
            cat = condition['category'][0]
            if cat.get('coding'):
                category_coding = cat['coding'][0]
                # PRIORITY 1: Use display if available
                category = category_coding.get('display')
                category_code = category_coding.get('code')
                
                # PRIORITY 2: Use code field and format it properly
                if not category and category_code:
                    # Format: 'problem-list-item' -> 'Problem List Item'
                    category = ' '.join(word.capitalize() for word in category_code.replace('-', ' ').split())
                
                # Default fallback
                if not category:
                    category = 'Not specified'
            elif cat.get('text'):
                category = cat['text']
        elif is_negative_assertion:
            category = 'Not applicable'
        
        # Extract severity (only for actual conditions)
        severity = 'Not specified'
        severity_code = None
        if not is_negative_assertion and condition.get('severity'):
            severity_data = condition.get('severity', {})
            if severity_data.get('coding'):
                severity_coding = severity_data['coding'][0]
                # PRIORITY 1: Use display if available
                severity = severity_coding.get('display')
                severity_code = severity_coding.get('code')
                
                # PRIORITY 2: Use text field
                if not severity:
                    severity = severity_data.get('text')
                
                # Default fallback
                if not severity:
                    severity = 'Not specified'
            elif severity_data.get('text'):
                severity = severity_data['text']
        elif is_negative_assertion:
            severity = 'Not applicable'
        
        # Extract onset date (only for actual conditions)
        onset_date = 'Unknown'
        if not is_negative_assertion:
            raw_onset = condition.get('onsetDateTime', condition.get('onsetString', 'Unknown'))
            # Format the onset date using ClinicalDateFormatter
            if raw_onset and raw_onset not in ('Unknown', 'Not applicable'):
                onset_date = ClinicalDateFormatter.format_clinical_date(raw_onset)
            else:
                onset_date = raw_onset
        else:
            onset_date = 'Not applicable'
        
        # Extract FHIR R4 Annotation notes (clinical comments, additional context)
        notes = []
        annotation_text = ''
        if condition.get('note'):
            # Import the enhanced annotation processor
            from eu_ncp_server.services.fhir_processing import FHIRResourceProcessor
            processor = FHIRResourceProcessor()
            
            # Extract full annotation data with author and timestamp
            notes = processor._extract_annotation_data(condition['note'])
            
            # Also extract simple text for backward compatibility
            annotation_text = processor._extract_annotation_text(condition['note'])

        return {
            'id': condition.get('id'),
            'condition_name': condition_name,
            'name': condition_name,  # Template compatibility
            'problem_name': condition_name,  # Template compatibility (alternative name)
            'condition_code': condition_code,  # ICD-10 or other code
            'condition_code_data': code_data,  # Full CodeableConcept with CTS translation
            'code_system': code_system,
            'clinical_status': clinical_status,
            'problem_status': clinical_status,  # Template compatibility - maps to "Problem Status"
            'verification_status': verification_status,
            'health_status': verification_status,  # Template compatibility - maps to "Health Status"
            'category': category,
            'category_code': category_code,
            'problem_type': category,  # Template compatibility - maps to "Problem Type"
            'severity': severity,
            'severity_code': severity_code,
            'onset_date': onset_date,
            'time_period': onset_date,  # Template compatibility - maps to "Time"
            'notes': notes,  # Full FHIR R4 Annotation data
            'note_text': annotation_text,  # Simple text for display
            'has_notes': bool(notes),
            'resource_type': 'Condition',
            'display_text': f"Condition: {condition_name} ({clinical_status})",
            'is_negative_assertion': is_negative_assertion
        }
    
    def _parse_procedure_resource(self, procedure: Dict[str, Any]) -> Dict[str, Any]:
        """Parse FHIR Procedure resource with CTS translation for SNOMED procedure codes"""
        # Import enhanced FHIR processor for CodeableConcept with CTS support
        from eu_ncp_server.services.fhir_processing import FHIRResourceProcessor
        processor = FHIRResourceProcessor()
        
        # Extract procedure name with CTS translation
        code = procedure.get('code', {})
        procedure_name = 'Unknown procedure'
        code_data = {}
        if code:
            code_data = processor._extract_codeable_concept(code)
            procedure_name = code_data.get('display_text', 'Unknown procedure')
        
        # Extract status and performed date
        status = procedure.get('status', 'Unknown')
        performed_date = 'Unknown date'
        raw_date = None
        if procedure.get('performedDateTime'):
            raw_date = procedure['performedDateTime']
        elif procedure.get('performedPeriod', {}).get('start'):
            raw_date = procedure['performedPeriod']['start']
        
        # Format the date using ClinicalDateFormatter
        if raw_date and raw_date != 'Unknown date':
            performed_date = ClinicalDateFormatter.format_procedure_date(raw_date)
        else:
            performed_date = raw_date or 'Unknown date'
        
        # Extract category with CTS translation
        category_text = 'Unknown'
        category_data = {}
        if procedure.get('category'):
            category_data = processor._extract_codeable_concept(procedure['category'])
            category_text = category_data.get('display_text', 'Unknown')
        
        return {
            'id': procedure.get('id'),
            'procedure_name': procedure_name,
            'procedure_code_data': code_data,  # Full CodeableConcept with CTS translation
            'status': status.capitalize(),
            'performed_date': performed_date,
            'category': category_text,
            'category_data': category_data,  # Full category CodeableConcept
            'resource_type': 'Procedure',
            'display_text': f"Procedure: {procedure_name} ({status})"
        }
    
    def _parse_observation_resource(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """Parse FHIR Observation resource with comprehensive FHIR R4 data type support"""
        # Import enhanced FHIR processor for complex data types
        from eu_ncp_server.services.fhir_processing import FHIRResourceProcessor
        processor = FHIRResourceProcessor()
        
        # Extract observation name with FHIR R4 CodeableConcept support
        code = observation.get('code', {})
        observation_name = 'Unknown observation'
        code_data = {}
        if code:
            code_data = processor._extract_codeable_concept(code)
            observation_name = code_data.get('display_text', 'Unknown observation')
        
        # Extract value with comprehensive FHIR R4 data type support
        value_text = 'No value'
        value_data = {}
        value_type = 'none'
        
        # FHIR R4 supports multiple value types for observations
        if observation.get('valueQuantity'):
            value_type = 'quantity'
            value_data = processor._extract_quantity_data(observation['valueQuantity'])
            value_text = value_data.get('display_value', 'Unknown quantity')
        elif observation.get('valueCodeableConcept'):
            value_type = 'concept'
            value_data = processor._extract_codeable_concept(observation['valueCodeableConcept'])
            value_text = value_data.get('display_text', 'Unknown concept')
        elif observation.get('valueString'):
            value_type = 'string'
            value_text = observation['valueString']
            value_data = {'text': value_text}
        elif observation.get('valueBoolean') is not None:
            value_type = 'boolean'
            value_text = 'Yes' if observation['valueBoolean'] else 'No'
            value_data = {'boolean': observation['valueBoolean']}
        elif observation.get('valueInteger') is not None:
            value_type = 'integer'
            value_text = str(observation['valueInteger'])
            value_data = {'integer': observation['valueInteger']}
        elif observation.get('valueRange'):
            value_type = 'range'
            value_data = processor._extract_range_data(observation['valueRange'])
            value_text = value_data.get('display_range', 'Unknown range')
        elif observation.get('valueRatio'):
            value_type = 'ratio'
            value_data = processor._extract_ratio_data(observation['valueRatio'])
            value_text = value_data.get('display_ratio', 'Unknown ratio')
        elif observation.get('valuePeriod'):
            value_type = 'period'
            value_data = processor._extract_period_data(observation['valuePeriod'])
            start = value_data.get('start_display', 'Unknown start')
            end = value_data.get('end_display', 'Unknown end')
            value_text = f"{start} to {end}"
        elif observation.get('valueDateTime'):
            value_type = 'datetime'
            value_text = processor._format_datetime_display(observation['valueDateTime'])
            value_data = {'datetime': observation['valueDateTime'], 'display': value_text}
        elif observation.get('valueTime'):
            value_type = 'time'
            value_text = observation['valueTime']
            value_data = {'time': value_text}
        elif observation.get('valueAttachment'):
            value_type = 'attachment'
            value_data = processor._extract_attachment_data(observation['valueAttachment'])
            value_text = value_data.get('display_title', 'Attachment')
        
        # Extract effective date/time with FHIR R4 support
        effective_date = 'Unknown date'
        effective_data = {}
        if observation.get('effectiveDateTime'):
            effective_date = processor._format_datetime_display(observation['effectiveDateTime'])
            effective_data = {'type': 'datetime', 'value': observation['effectiveDateTime'], 'display': effective_date}
        elif observation.get('effectivePeriod'):
            effective_data = processor._extract_period_data(observation['effectivePeriod'])
            start = effective_data.get('start_display', 'Unknown start')
            end = effective_data.get('end_display', 'Unknown end')
            effective_date = f"{start} to {end}"
            effective_data['type'] = 'period'
        elif observation.get('effectiveInstant'):
            effective_date = processor._format_datetime_display(observation['effectiveInstant'])
            effective_data = {'type': 'instant', 'value': observation['effectiveInstant'], 'display': effective_date}
        
        # Extract category with FHIR R4 CodeableConcept support
        category_text = 'Unknown'
        category_data = {}
        if observation.get('category'):
            categories = observation['category']
            if categories:
                category_data = processor._extract_codeable_concept(categories[0])
                category_text = category_data.get('display_text', 'Unknown')
        
        # Extract reference range with FHIR R4 Range support
        reference_ranges = []
        for ref_range in observation.get('referenceRange', []):
            range_data = {
                'low': processor._extract_quantity_data(ref_range.get('low', {})) if ref_range.get('low') else {},
                'high': processor._extract_quantity_data(ref_range.get('high', {})) if ref_range.get('high') else {},
                'type': processor._extract_codeable_concept(ref_range.get('type', {})) if ref_range.get('type') else {},
                'applies_to': [processor._extract_codeable_concept(concept) for concept in ref_range.get('appliesTo', [])],
                'age': processor._extract_range_data(ref_range.get('age', {})) if ref_range.get('age') else {},
                'text': ref_range.get('text', '')
            }
            
            # Create display text for reference range
            range_display = []
            if range_data['low']:
                range_display.append(f"Low: {range_data['low'].get('display_value', 'Unknown')}")
            if range_data['high']:
                range_display.append(f"High: {range_data['high'].get('display_value', 'Unknown')}")
            range_data['display'] = ', '.join(range_display) if range_display else range_data.get('text', 'Unknown range')
            
            reference_ranges.append(range_data)
        
        # Extract interpretation with FHIR R4 CodeableConcept support
        interpretation_text = ''
        interpretation_data = {}
        if observation.get('interpretation'):
            interpretations = observation['interpretation']
            if interpretations:
                interpretation_data = processor._extract_codeable_concept(interpretations[0])
                interpretation_text = interpretation_data.get('display_text', '')
        
        # Extract status and method
        status = observation.get('status', 'Unknown')
        method_text = ''
        method_data = {}
        if observation.get('method'):
            method_data = processor._extract_codeable_concept(observation['method'])
            method_text = method_data.get('display_text', '')

        # Extract code details for template compatibility
        # code_data structure: {'primary_coding': {'code': ..., 'system': ...}, 'text': ...}
        primary_coding = code_data.get('primary_coding', {})
        observation_code = primary_coding.get('code', '')
        observation_code_system = primary_coding.get('system', '')
        
        # Extract numeric value and unit for template compatibility
        value_numeric = None
        value_unit = None
        if value_type == 'quantity' and value_data:
            value_numeric = value_data.get('value')
            value_unit = value_data.get('unit')
        
        return {
            'id': observation.get('id'),
            'observation_name': observation_name,
            'observation_type': observation_name,  # Template alias
            'code_data': code_data,
            'observation_code': observation_code,  # Template alias
            'observation_code_system': observation_code_system,  # Template alias
            'value': value_text,
            'observation_value': value_text,  # Template alias
            'value_data': value_data,
            'value_type': value_type,
            'value_numeric': value_numeric,  # Template alias
            'value_unit': value_unit,  # Template alias
            'status': status.capitalize(),
            'effective_date': effective_date,
            'observation_time': effective_date,  # Template alias
            'effective_data': effective_data,
            'category': observation.get('category', category_text),  # Preserve raw category for filtering
            'category_text': category_text,  # Display text for UI
            'category_data': category_data,
            'reference_ranges': reference_ranges,
            'has_reference_ranges': bool(reference_ranges),
            'interpretation': interpretation_text,
            'interpretation_data': interpretation_data,
            'method': method_text,
            'method_data': method_data,
            'body_site': processor._extract_codeable_concept(observation.get('bodySite', {})) if observation.get('bodySite') else {},
            'component': observation.get('component', []),  # Multi-component observations
            'has_components': bool(observation.get('component')),
            'resource_type': 'Observation',
            'display_text': f"Observation: {observation_name} = {value_text}",
            'clinical_significance': self._assess_observation_significance(observation, value_data, reference_ranges, interpretation_text)
        }
    
    def _is_pregnancy_related(self, observation: Dict[str, Any]) -> bool:
        """
        Check if observation is pregnancy/obstetric history related
        
        Uses LOINC codes from IPS Pregnancy History section (10162-6)
        """
        pregnancy_loinc_codes = {
            '82810-3',  # Pregnancy status
            '11636-8',  # [# Births] total
            '11637-6',  # [# Births].live
            '11638-4',  # [# Births].still living
            '11639-2',  # [# Births].term
            '11640-0',  # [# Births].preterm
            '11612-9',  # [# Abortions]
            '11613-7',  # [# Abortions].induced
            '11614-5',  # [# Abortions].spontaneous
            '93857-1',  # Date and time of obstetric delivery
            '11996-6',  # Pregnancy status
            '49051-6',  # Gestational age
            '11884-4',  # Gestational age at birth
            '57064-8',  # Estimated date of delivery
            '11778-8',  # Delivery date
            '8339-4',   # Birth weight
            '72149-8',  # Type of delivery
            '73812-0',  # Delivery complications
        }
        
        pregnancy_snomed_codes = {
            '77386006',  # Pregnant
            '281050002', # Livebirth
            '57797005',  # Termination of pregnancy
            '169836001', # Gravida
            '364325004', # Parity
            '161732006', # Gravidity
            '161733001', # Parity - delivered
        }
        
        # Check observation_code field (primary method after _parse_observation_resource)
        observation_code = observation.get('observation_code', '')
        if observation_code and (observation_code in pregnancy_loinc_codes or observation_code in pregnancy_snomed_codes):
            return True
        
        # Also check code_data.code for backwards compatibility
        code_data = observation.get('code_data', {})
        if isinstance(code_data, dict):
            code = code_data.get('code', '')
            if code and (code in pregnancy_loinc_codes or code in pregnancy_snomed_codes):
                return True
        
        # Check category for pregnancy/obstetric (handle both list and string formats)
        category = observation.get('category', [])
        category_text = ''
        if isinstance(category, list):
            # Extract display text from FHIR category structure
            for cat in category:
                if isinstance(cat, dict):
                    codings = cat.get('coding', [])
                    for coding in codings:
                        if isinstance(coding, dict):
                            display = coding.get('display', '')
                            if display:
                                category_text += display.lower() + ' '
        elif isinstance(category, str):
            category_text = category.lower()
        
        if 'pregnancy' in category_text or 'obstetric' in category_text:
            return True
        
        # Check observation name and display text
        observation_name = observation.get('observation_name', '').lower()
        display_text = str(observation.get('code_data', {}).get('text', '')).lower()
        
        pregnancy_keywords = [
            'pregnancy', 'pregnant', 'gravida', 'para', 'gravidity', 'parity',
            'delivery', 'obstetric', 'gestation', 'livebirth', 'stillbirth',
            'abortion', 'miscarriage', 'termination of pregnancy'
        ]
        
        return any(keyword in observation_name or keyword in display_text 
                  for keyword in pregnancy_keywords)
    
    def _transform_pregnancy_observations(self, observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform pregnancy-related observations into template-compatible structure
        
        Template expects:
        - pregnancy_type: 'current' or 'past'
        - data.status.display_value: Pregnancy status
        - data.outcome.display_value: Pregnancy outcome (live birth, etc.)
        - data.observation_date.display_value: Observation date
        - data.delivery_date.display_value: Delivery date
        - data.delivery_date_estimated.display_value: Estimated delivery date
        - data.number_of_births_live.display_value: Number of live births
        - data.number_of_births_stillborn.display_value: Number of stillbirths
        """
        if not observations:
            return []
        
        # Group observations by delivery date to create cohesive pregnancy records
        pregnancy_groups = {}
        current_pregnancy_obs = []
        
        for obs in observations:
            # Extract code from nested code_data structure
            code_data = obs.get('code_data', {})
            if isinstance(code_data.get('coding'), list) and code_data['coding']:
                code = code_data['coding'][0].get('code', '')
            else:
                code = code_data.get('code', '')
            
            observation_name = obs.get('observation_name', '').lower()
            
            # Identify current pregnancy observations (no delivery date yet)
            # CRITICAL: 93857-1 (Date and time of obstetric delivery) is PAST pregnancy, NOT current
            is_current_pregnancy = (
                code == '82810-3' or  # Pregnancy status LOINC code  
                any(keyword in observation_name for keyword in [
                    'gestational age', 'estimated date of delivery', 
                    'estimated delivery', 'edd'
                ])
            ) and code != '93857-1'  # Explicitly exclude delivery date observations
            
            if is_current_pregnancy:
                logger.debug(f"[PREGNANCY] Classified as CURRENT: {observation_name} (code: {code})")
                current_pregnancy_obs.append(obs)
                continue
            else:
                logger.debug(f"[PREGNANCY] Classified as PAST: {observation_name} (code: {code})")
            
            # For past pregnancies, group by delivery date
            # CRITICAL: Use RAW effectiveDateTime from effective_data, NOT formatted effective_date
            delivery_date_raw = None
            
            # Extract raw ISO date from effective_data structure
            effective_data = obs.get('effective_data', {})
            if isinstance(effective_data, dict) and effective_data.get('value'):
                # This is the raw FHIR effectiveDateTime value (e.g., "2021-09-08")
                delivery_date_raw = effective_data['value']
            
            # Always get value_data as it may contain outcome information
            value_data = obs.get('value_data', {})
            
            # If not found in effective_data, check value_data for valueDateTime
            if not delivery_date_raw:
                if isinstance(value_data, dict) and value_data.get('datetime'):
                    delivery_date_raw = value_data['datetime']
            
            # Normalize date format (remove time if present) for grouping key
            if delivery_date_raw and delivery_date_raw != 'Not recorded':
                delivery_date_key = delivery_date_raw.split('T')[0] if 'T' in delivery_date_raw else delivery_date_raw.split(' ')[0]
            else:
                # Log warning and skip this observation if no valid date found
                logger.warning(f"[PREGNANCY] Skipping observation {obs.get('id')} - no valid date found. effective_data: {effective_data}, value_data: {value_data}")
                continue
            
            # CRITICAL FIX: Group by date AND outcome code to handle cases where
            # the same date has both Livebirth and Termination observations
            # Extract outcome code for grouping key
            outcome_code_for_grouping = None
            if code in ['281050002', '57797005']:
                outcome_code_for_grouping = code
            elif code == '93857-1' and isinstance(value_data, dict) and value_data.get('coding'):
                # Extract outcome code from valueCodeableConcept
                outcome_coding = value_data['coding'][0] if isinstance(value_data['coding'], list) else value_data['coding']
                outcome_code_for_grouping = outcome_coding.get('code', '')
            
            # Create composite key: date + outcome_code (if available)
            if outcome_code_for_grouping:
                group_key = f"{delivery_date_key}-{outcome_code_for_grouping}"
            else:
                group_key = delivery_date_key
            
            if group_key not in pregnancy_groups:
                pregnancy_groups[group_key] = []
            pregnancy_groups[group_key].append(obs)
        
        # Build pregnancy records from groups
        pregnancy_records = []
        
        # Process past pregnancies (grouped by delivery date + outcome code)
        for group_key, group_obs in sorted(pregnancy_groups.items(), reverse=True):
            # Extract delivery_date from composite key (format: "YYYY-MM-DD" or "YYYY-MM-DD-SNOMEDCODE")
            if '-281050002' in group_key or '-57797005' in group_key:
                # Composite key: extract date part
                delivery_date_key = group_key.rsplit('-', 1)[0]  # Remove last segment (SNOMED code)
            else:
                # Simple date key
                delivery_date_key = group_key
            
            # Initialize pregnancy record
            pregnancy_record = {
                'pregnancy_type': 'past',
                'observation_id': f"pregnancy-{group_key}",  # Use full group_key for uniqueness
                'resource_type': 'PregnancyGroup',
                'delivery_date': ClinicalDateFormatter.format_pregnancy_date(delivery_date_key),  # Format for display
                'delivery_date_raw': delivery_date_key,  # Keep raw for sorting
                'outcome': None,
                'outcome_code': None,  # Add SNOMED code for outcome
                'gestational_age': None,
                'birth_weight': None,
                'delivery_method': None,
                'complications': 'None reported',
                'observation_date': delivery_date_key,
                'data': {}
            }
            
            # Extract values from grouped observations
            for obs in group_obs:
                code_data = obs.get('code_data', {})
                value_data = obs.get('value_data', {})
                
                if isinstance(code_data.get('coding'), list) and code_data['coding']:
                    code = code_data['coding'][0].get('code', '')
                else:
                    code = code_data.get('code', '')
                
                value_text = obs.get('value', '')
                observation_name = obs.get('observation_name', '')
                
                # Extract outcome (Livebirth, Termination, etc.) from observation name or value
                if code in ['281050002', '57797005']:
                    # For SNOMED outcome codes, use the observation name (e.g., "Livebirth")
                    pregnancy_record['outcome'] = observation_name
                    pregnancy_record['outcome_code'] = code  # Store SNOMED code
                elif code == '93857-1':
                    # For 93857-1 observations, check valueCodeableConcept for outcome
                    if isinstance(value_data, dict) and value_data.get('coding'):
                        # Extract outcome from valueCodeableConcept
                        outcome_coding = value_data['coding'][0] if isinstance(value_data['coding'], list) else value_data['coding']
                        outcome_code = outcome_coding.get('code', '')
                        outcome_display = value_data.get('display_text', value_text)
                        
                        if outcome_code in ['281050002', '57797005'] or outcome_display in ['Livebirth', 'Termination of pregnancy']:
                            pregnancy_record['outcome'] = outcome_display
                            pregnancy_record['outcome_code'] = outcome_code
                elif 'livebirth' in observation_name.lower():
                    pregnancy_record['outcome'] = 'Livebirth'
                    if not pregnancy_record['outcome_code']:
                        pregnancy_record['outcome_code'] = '281050002'
                elif 'termination' in observation_name.lower():
                    pregnancy_record['outcome'] = 'Termination of pregnancy'
                    if not pregnancy_record['outcome_code']:
                        pregnancy_record['outcome_code'] = '57797005'
                elif 'livebirth' in value_text.lower():
                    pregnancy_record['outcome'] = 'Livebirth'
                    if not pregnancy_record['outcome_code']:
                        pregnancy_record['outcome_code'] = '281050002'
                elif 'termination' in value_text.lower():
                    pregnancy_record['outcome'] = 'Termination of pregnancy'
                    if not pregnancy_record['outcome_code']:
                        pregnancy_record['outcome_code'] = '57797005'
                
                # Extract delivery date from valueDateTime (for 93857-1)
                if code == '93857-1':
                    value_data = obs.get('value_data', {})
                    # First try datetime from value_data (FHIR valueDateTime)
                    if isinstance(value_data, dict) and value_data.get('datetime'):
                        pregnancy_record['delivery_date'] = value_data['datetime']
                    # If value_data has CodeableConcept (like "Livebirth"), use effectiveDateTime
                    elif isinstance(value_data, dict) and value_data.get('coding'):
                        # This 93857-1 has valueCodeableConcept not valueDateTime - use effective_date
                        if obs.get('effective_date') and obs.get('effective_date') != 'Not recorded':
                            pregnancy_record['delivery_date'] = obs.get('effective_date')
                    # Otherwise use value_text if it looks like a date
                    elif value_text and value_text not in ['No value', 'Not recorded', 'Livebirth', 'Termination of pregnancy']:
                        pregnancy_record['delivery_date'] = value_text
                
                # Extract birth weight
                if code == '8339-4':
                    pregnancy_record['birth_weight'] = value_text
                
                # Extract gestational age
                if code in ['49051-6', '11884-4']:
                    pregnancy_record['gestational_age'] = value_text
                
                # Extract delivery method
                if code == '72149-8':
                    pregnancy_record['delivery_method'] = value_text
                
                # Extract complications
                if code == '73812-0':
                    pregnancy_record['complications'] = value_text if value_text else 'None reported'
            
            pregnancy_records.append(pregnancy_record)
        
        # Extract FHIR IPS summary counts from all observations
        live_births_count = None
        abortions_count = None
        
        for obs in observations:
            code_data = obs.get('code_data', {})
            if isinstance(code_data.get('coding'), list) and code_data['coding']:
                code = code_data['coding'][0].get('code', '')
            else:
                code = code_data.get('code', '')
            
            value_text = obs.get('value', '')
            
            # Extract live births count (11636-8)
            if code == '11636-8':
                try:
                    live_births_count = int(value_text) if value_text else None
                except (ValueError, TypeError):
                    live_births_count = value_text
            
            # Extract abortions count (11612-9)
            if code == '11612-9':
                try:
                    abortions_count = int(value_text) if value_text else None
                except (ValueError, TypeError):
                    abortions_count = value_text
        
        # Process current pregnancy
        if current_pregnancy_obs:
            pregnancy_record = {
                'pregnancy_type': 'current',
                'observation_id': 'current-pregnancy',
                'resource_type': 'PregnancyGroup',
                'delivery_date': None,
                'expected_delivery_date': None,  # Match template field name
                'outcome': None,
                'gestational_age': None,
                'birth_weight': None,
                'delivery_method': None,
                'complications': None,
                'status': None,
                'observation_date': None,
                'live_births_count': live_births_count,  # FHIR IPS summary count
                'abortions_count': abortions_count,      # FHIR IPS summary count
                'data': {}
            }
            
            for obs in current_pregnancy_obs:
                code_data = obs.get('code_data', {})
                if isinstance(code_data.get('coding'), list) and code_data['coding']:
                    code = code_data['coding'][0].get('code', '')
                else:
                    code = code_data.get('code', '')
                
                value_text = obs.get('value', '')
                effective_date = obs.get('effective_date', '')
                
                # Extract pregnancy status (82810-3)
                if code == '82810-3':
                    pregnancy_record['status'] = value_text
                    pregnancy_record['observation_date'] = ClinicalDateFormatter.format_observation_date(effective_date)
                
                # Extract estimated delivery date (11778-8, 57064-8)
                if code in ['11778-8', '57064-8']:
                    # For valueDateTime observations, extract from value_data
                    value_data = obs.get('value_data', {})
                    if isinstance(value_data, dict) and value_data.get('datetime'):
                        raw_date = value_data['datetime']
                    else:
                        raw_date = value_text
                    # Format using ClinicalDateFormatter for consistency
                    pregnancy_record['expected_delivery_date'] = ClinicalDateFormatter.format_pregnancy_date(raw_date)
                
                # Extract gestational age (49051-6, 11884-4)
                if code in ['49051-6', '11884-4']:
                    pregnancy_record['gestational_age'] = value_text
            
            pregnancy_records.append(pregnancy_record)
        
        logger.info(f"[PREGNANCY TRANSFORM] Transformed {len(observations)} pregnancy observations into {len(pregnancy_records)} pregnancy records ({len(pregnancy_groups)} past, {1 if current_pregnancy_obs else 0} current)")
        return pregnancy_records
    
    def _transform_social_history_observations(self, observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform social history observations into CDA-style nested structure for template compatibility
        
        Uses Enhanced CTS Service to lookup LOINC codes in target language (English) from Master Value
        Catalogue (MVC), ensuring language-independent clinical terminology across EU member states.
        Falls back to FHIR code.text if MVC lookup fails.
        
        European Healthcare Context:
        - Patient FHIR resources may have code.text in source country language (e.g., Portuguese)
        - Healthcare professionals need terminology in their language (e.g., English for Ireland)
        - LOINC codes are universal, MVC provides validated medical translations
        - Future enhancement: Support displaying both source and target language
        
        Template expects nested structure:
        - data.observation_type.display_value: Type (e.g., "Tobacco smoking status", "Alcoholic drinks per day")
        - data.observation_value.display_value: Value (e.g., "0.5 (pack)/d")
        - data.observation_time.display_value: Time/period (e.g., "15/04/2017 to 2022")
        - data.status.display_value: Status (e.g., "Completed", "Final")
        """
        if not observations:
            return []
        
        # Initialize Enhanced CTS service for language-independent MVC lookup
        enhanced_cts = EnhancedCTSService()
        LOINC_OID = "2.16.840.1.113883.6.1"
        
        transformed_observations = []
        
        for obs in observations:
            # Extract observation code and name
            observation_code = obs.get('observation_code', '')
            observation_name = obs.get('observation_name', 'Social history observation')
            
            # Use MVC/CTS for language-independent LOINC lookup
            # Prioritize universal LOINC codes over source country language text
            if observation_code:
                # Query Master Value Catalogue for English translation
                mvc_data = enhanced_cts.get_comprehensive_code_data(
                    code=observation_code,
                    code_system_oid=LOINC_OID,
                    target_language='en',  # Healthcare professional's language
                    include_all_languages=True  # Future: support source language display
                )
                
                if mvc_data and mvc_data.get('display_value'):
                    observation_name = mvc_data['display_value']
                    logger.info(f"[SOCIAL HISTORY MVC] Retrieved '{observation_name}' for LOINC {observation_code} from Master Value Catalogue")
                else:
                    # Fallback to FHIR code.coding[0].display (proper LOINC display)
                    # code.text may be generic or in source language, prefer coding display
                    code_data = obs.get('code_data', {})
                    primary_coding = code_data.get('primary_coding', {})
                    coding_display = primary_coding.get('display', '')
                    
                    if coding_display and coding_display != observation_name:
                        observation_name = coding_display
                        logger.info(f"[SOCIAL HISTORY FALLBACK] Using LOINC coding.display for {observation_code}: '{observation_name}'")
                    else:
                        # Last resort: use code.text (may be in source language)
                        logger.info(f"[SOCIAL HISTORY FALLBACK] Using code.text for LOINC {observation_code}: '{observation_name}'")
            else:
                # No code available, log warning
                logger.warning(f"[SOCIAL HISTORY] No LOINC code for observation: {observation_name}")
            
            # Extract effective period or datetime
            effective_data = obs.get('effective_data', {})
            observation_time = 'Not specified'
            
            if isinstance(effective_data, dict):
                if effective_data.get('type') == 'period':
                    # Handle effectivePeriod (e.g., "2017-04-15" to "2022")
                    start = effective_data.get('start', '')
                    end = effective_data.get('end', '')
                    if start and end:
                        # Format dates using ClinicalDateFormatter
                        start_formatted = ClinicalDateFormatter.format_clinical_date(start)
                        end_formatted = ClinicalDateFormatter.format_clinical_date(end)
                        observation_time = f"{start_formatted} to {end_formatted}"
                    elif start:
                        start_formatted = ClinicalDateFormatter.format_clinical_date(start)
                        observation_time = f"From {start_formatted}"
                elif effective_data.get('type') == 'datetime':
                    # Handle effectiveDateTime
                    datetime_val = effective_data.get('value', '')
                    if datetime_val:
                        observation_time = ClinicalDateFormatter.format_clinical_date(datetime_val)
            
            # Build CDA-style nested structure
            transformed_obs = {
                'id': obs.get('id'),
                'resource_type': 'Observation',
                'observation_type': observation_name,
                'observation_value': obs.get('value', 'Not specified'),
                'observation_time': observation_time,
                'status': obs.get('status', 'Unknown'),
                # Nested data structure for CDA template compatibility
                'data': {
                    'observation_type': {
                        'display_value': observation_name,
                        'code': obs.get('observation_code', ''),
                        'code_system': obs.get('observation_code_system', '')
                    },
                    'observation_value': {
                        'display_value': obs.get('value', 'Not specified'),
                        'numeric': obs.get('value_numeric'),
                        'unit': obs.get('value_unit')
                    },
                    'observation_time': {
                        'display_value': observation_time,
                        'raw_data': effective_data
                    },
                    'status': {
                        'display_value': obs.get('status', 'Unknown')
                    }
                },
                # Preserve original flat structure for backwards compatibility
                'category_text': obs.get('category_text', ''),
                'code_data': obs.get('code_data', {}),
                'value_data': obs.get('value_data', {}),
                'effective_date': obs.get('effective_date', '')
            }
            
            transformed_observations.append(transformed_obs)
        
        logger.info(f"[SOCIAL HISTORY TRANSFORM] Transformed {len(observations)} social history observations into CDA-style structure")
        return transformed_observations
    
    def _is_vital_sign(self, observation: Dict[str, Any]) -> bool:
        """Check if observation is a vital sign using LOINC codes and keywords"""
        # LOINC codes for vital signs (primary method)
        vital_sign_loinc_codes = [
            '85354-9',  # Blood pressure panel
            '8480-6',   # Systolic blood pressure
            '8462-4',   # Diastolic blood pressure
            '8867-4',   # Heart rate
            '8310-5',   # Body temperature
            '9279-1',   # Respiratory rate
            '2710-2',   # Oxygen saturation
            '29463-7',  # Body weight
            '8302-2',   # Body height
            '39156-5',  # Body mass index
        ]
        
        # Check category first (most reliable)
        category = observation.get('category', [])
        
        # Type check: category should be list of dicts, but might be a string
        if isinstance(category, str):
            logger.warning(f"[FHIR] Observation category is string instead of list: {category}")
            # Match string category values (case-insensitive)
            category_lower = category.lower()
            if 'vital' in category_lower or category_lower == 'vital-signs':
                return True
            category = []  # Fallback to empty array for further processing
        
        for cat in category:
            # Type check: each category entry should be dict (CodeableConcept), not string
            if not isinstance(cat, dict):
                logger.warning(f"[FHIR] Observation category entry is not dict: {type(cat)} - {cat}")
                continue
            
            coding = cat.get('coding', [])
            for code in coding:
                if code.get('code') == 'vital-signs':
                    return True
        
        # Check LOINC code
        code_data = observation.get('code', {})
        if code_data.get('coding'):
            for coding in code_data['coding']:
                if coding.get('system') == 'http://loinc.org' and coding.get('code') in vital_sign_loinc_codes:
                    return True
        
        # Fallback to keyword matching
        vital_sign_keywords = [
            'blood pressure', 'systolic', 'diastolic', 'heart rate', 'pulse',
            'temperature', 'respiratory rate', 'oxygen saturation', 'spo2',
            'weight', 'height', 'bmi', 'body mass index'
        ]
        
        observation_text = str(observation.get('code', {})).lower()
        return any(keyword in observation_text for keyword in vital_sign_keywords)
    
    def _is_social_history(self, observation: Dict[str, Any]) -> bool:
        """Check if observation is social history using LOINC codes and category"""
        # Check category first (most reliable)
        category = observation.get('category', [])
        
        # Type check: category should be list of dicts, but might be a string
        if isinstance(category, str):
            # Match string category values (case-insensitive)
            category_lower = category.lower()
            if 'social' in category_lower or category_lower == 'social-history':
                return True
            category = []  # Fallback to empty array for further processing
        
        for cat in category:
            # Type check: each category entry should be dict (CodeableConcept)
            if not isinstance(cat, dict):
                continue
            
            coding = cat.get('coding', [])
            for code in coding:
                if code.get('code') == 'social-history':
                    return True
        
        # LOINC codes for social history
        social_history_loinc_codes = [
            '72166-2',  # Tobacco smoking status
            '74013-4',  # Alcoholic drinks per day
            '11331-6',  # History of occupation
            '63512-8',  # Number of living children
            '93043-8',  # Housing status
            '76689-9',  # Sex assigned at birth
        ]
        
        code_data = observation.get('code', {})
        if code_data.get('coding'):
            for coding in code_data['coding']:
                if coding.get('system') == 'http://loinc.org' and coding.get('code') in social_history_loinc_codes:
                    return True
        
        # Fallback to keyword matching
        social_keywords = [
            'smoking', 'tobacco', 'alcohol', 'occupation', 'employment',
            'housing', 'living', 'marital', 'education', 'social'
        ]
        
        observation_text = str(observation.get('code', {})).lower()
        return any(keyword in observation_text for keyword in social_keywords)
    
    def _is_laboratory_result(self, observation: Dict[str, Any]) -> bool:
        """Check if observation is a laboratory result"""
        # Check category first (most reliable)
        category = observation.get('category', [])
        
        # Type check: category should be list of dicts, but might be a string
        if isinstance(category, str):
            # Match string category values (case-insensitive)
            category_lower = category.lower()
            if 'lab' in category_lower or category_lower == 'laboratory':
                return True
            category = []  # Fallback to empty array for further processing
        
        for cat in category:
            # Type check: each category entry should be dict (CodeableConcept)
            if not isinstance(cat, dict):
                continue
            
            coding = cat.get('coding', [])
            for code in coding:
                if code.get('code') in ['laboratory', 'lab']:
                    return True
        
        # Common lab result LOINC patterns
        lab_keywords = [
            'blood', 'serum', 'plasma', 'urine', 'hemoglobin', 'glucose',
            'cholesterol', 'creatinine', 'panel', 'group', 'test', 'lab'
        ]
        
        observation_text = str(observation.get('code', {})).lower()
        return any(keyword in observation_text for keyword in lab_keywords)
    
    def _is_physical_finding(self, observation: Dict[str, Any]) -> bool:
        """Check if observation is a physical examination finding"""
        # Check category first (most reliable)
        category = observation.get('category', [])
        
        # Type check: category should be list of dicts, but might be a string
        if isinstance(category, str):
            # Match string category values (case-insensitive)
            category_lower = category.lower()
            if 'exam' in category_lower or 'physical' in category_lower:
                return True
            category = []  # Fallback to empty array for further processing
        
        for cat in category:
            # Type check: each category entry should be dict (CodeableConcept)
            if not isinstance(cat, dict):
                continue
            
            coding = cat.get('coding', [])
            for code in coding:
                if code.get('code') in ['exam', 'physical-exam', 'physical-finding']:
                    return True
        
        # LOINC codes for physical examination findings
        physical_exam_loinc_codes = [
            '8716-3',   # Vital signs panel (sometimes used for physical exam)
            '29274-8',  # Physical findings
            '11384-5',  # Physical examination
            '32423-6',  # Physical findings of Abdomen
            '11391-0',  # Physical findings of Chest
            '11413-2',  # Physical findings of Skin
        ]
        
        code_data = observation.get('code', {})
        if code_data.get('coding'):
            for coding in code_data['coding']:
                if coding.get('system') == 'http://loinc.org' and coding.get('code') in physical_exam_loinc_codes:
                    return True
        
        # Fallback to keyword matching
        physical_exam_keywords = [
            'physical exam', 'examination', 'inspection', 'palpation',
            'auscultation', 'percussion', 'abdomen', 'chest', 'skin',
            'appearance', 'finding'
        ]
        
        observation_text = str(observation.get('code', {})).lower()
        return any(keyword in observation_text for keyword in physical_exam_keywords)
    
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
        
        # Extract occurrence - FHIR R4 supports occurrenceDateTime or occurrenceString
        raw_occurrence = (immunization.get('occurrenceDateTime') or 
                         immunization.get('occurrenceString'))
        
        # Format the occurrence date using ClinicalDateFormatter
        if raw_occurrence:
            occurrence_date = ClinicalDateFormatter.format_clinical_date(raw_occurrence)
        else:
            occurrence_date = None
        
        # Extract route - handle missing or complex structures
        route_value = immunization.get('route')
        if route_value:
            route_display = route_value.get('coding', [{}])[0].get('display') if isinstance(route_value, dict) else route_value
        else:
            route_display = None
        
        # Extract lot number - can be None
        lot_number = immunization.get('lotNumber')
        
        return {
            'id': immunization.get('id'),
            'vaccine_name': vaccine_name,
            'status': immunization.get('status', 'Unknown'),
            'date': occurrence_date,  # Use 'date' field name for template compatibility
            'occurrence_date': occurrence_date,  # Keep for backwards compatibility
            'lot_number': lot_number,  # None if not present
            'route': route_display,  # None if not present
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
    
    def _parse_consent_resource(self, consent: Dict[str, Any]) -> Dict[str, Any]:
        """Parse FHIR Consent resource for advance directives"""
        # Extract consent scope and category
        scope = consent.get('scope', {})
        scope_text = scope.get('text') or scope.get('coding', [{}])[0].get('display', 'Unknown')
        
        category = consent.get('category', [])
        category_text = 'Advance Directive'
        if category:
            cat_coding = category[0].get('coding', [{}])
            if cat_coding:
                category_text = cat_coding[0].get('display', category_text)
        
        # Extract decision (permit/deny)
        provision = consent.get('provision', {})
        decision = provision.get('type', 'Unknown')
        
        # Extract effective dates
        effective_start = consent.get('dateTime')
        effective_period = consent.get('period', {})
        effective_time = effective_start or effective_period.get('start', 'Unknown')
        
        # Build directive name
        directive_name = category_text
        if scope_text and scope_text != 'Unknown':
            directive_name = f"{category_text}: {scope_text}"
        
        return {
            'id': consent.get('id'),
            'name': directive_name,
            'code': {
                'code': category[0].get('coding', [{}])[0].get('code', 'Unknown') if category else 'Unknown',
                'display': category_text,
                'system': category[0].get('coding', [{}])[0].get('system', 'Unknown') if category else 'Unknown'
            },
            'status': consent.get('status', 'Unknown'),
            'decision': decision,
            'scope': scope_text,
            'description': provision.get('code', [{}])[0].get('text') if provision.get('code') else None,
            'effective_time': effective_time,
            'resource_type': 'Consent',
            'display_text': f"Advance Directive: {directive_name}"
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
            'problems': [],  # Active conditions (Problem List)
            'past_illness': [],  # Resolved/inactive conditions (History of Past Illness)
            'procedures': [],
            'observations': [],
            'vital_signs': [],  # Subset of observations
            'social_history': [],  # Social history observations
            'physical_findings': [],  # Physical examination observations
            'laboratory_results': [],  # Lab test results
            'pregnancy_history': [],  # Pregnancy/obstetric history
            'immunizations': [],
            'medical_devices': [],  # Implanted/prescribed medical devices
            'advance_directives': [],  # Patient consent and advance care directives
            'diagnostic_reports': [],
            'results': []  # Alias for diagnostic_reports
        }
        
        # Map clinical sections to arrays
        for section_type, section_data in clinical_sections.items():
            if section_type == 'medications' and hasattr(section_data, 'entries'):
                # Apply clinical deduplication to remove duplicate medications (same ATC/name)
                clinical_arrays['medications'] = self._deduplicate_medications_clinically(section_data.entries)
            elif section_type == 'allergies' and hasattr(section_data, 'entries'):
                clinical_arrays['allergies'] = section_data.entries
            elif section_type == 'problem_list' and hasattr(section_data, 'entries'):
                # Active conditions (Problem List)
                clinical_arrays['problems'] = section_data.entries
                clinical_arrays['conditions'] = section_data.entries  # Alias for backward compatibility
            elif section_type == 'past_illness' and hasattr(section_data, 'entries'):
                # Resolved/inactive conditions (History of Past Illness)
                clinical_arrays['past_illness'] = section_data.entries
            elif section_type == 'conditions' and hasattr(section_data, 'entries'):
                # Backward compatibility for old single conditions section
                clinical_arrays['conditions'] = section_data.entries
                clinical_arrays['problems'] = section_data.entries  # Alias
            elif section_type == 'procedures' and hasattr(section_data, 'entries'):
                clinical_arrays['procedures'] = section_data.entries
            elif section_type == 'observations' and hasattr(section_data, 'entries'):
                clinical_arrays['observations'] = section_data.entries
                
                # Debug: Log all observations before filtering
                logger.info(f"[OBS DEBUG] Processing {len(section_data.entries)} observations")
                for obs in section_data.entries:
                    obs_name = obs.get('observation_name', 'Unknown')
                    obs_category = obs.get('category', 'No category')
                    logger.info(f"[OBS] {obs_name} | Category: {obs_category}")
                
                # Filter for vital signs
                clinical_arrays['vital_signs'] = [
                    obs for obs in section_data.entries 
                    if self._is_vital_sign(obs)
                ]
                logger.info(f"[FILTER] Vital signs: {len(clinical_arrays['vital_signs'])} observations")
                
                # Filter for social history and transform to CDA-style structure
                social_history_observations = [
                    obs for obs in section_data.entries 
                    if self._is_social_history(obs)
                ]
                logger.info(f"[FILTER] Social history: {len(social_history_observations)} observations")
                clinical_arrays['social_history'] = self._transform_social_history_observations(social_history_observations)
                
                # Filter for physical findings (physical examination observations)
                clinical_arrays['physical_findings'] = [
                    obs for obs in section_data.entries 
                    if self._is_physical_finding(obs)
                ]
                logger.info(f"[FILTER] Physical findings: {len(clinical_arrays['physical_findings'])} observations")
                
                # Filter for laboratory results
                clinical_arrays['laboratory_results'] = [
                    obs for obs in section_data.entries 
                    if self._is_laboratory_result(obs)
                ]
                logger.info(f"[FILTER] Laboratory results: {len(clinical_arrays['laboratory_results'])} observations")
                
                # Filter for pregnancy history (LOINC 10162-6 section) and transform to template structure
                pregnancy_observations = [
                    obs for obs in section_data.entries 
                    if self._is_pregnancy_related(obs)
                ]
                logger.info(f"[PREGNANCY FILTER] Found {len(pregnancy_observations)} pregnancy-related observations from {len(section_data.entries)} total observations")
                for obs in pregnancy_observations:
                    logger.debug(f"[PREGNANCY OBS] {obs.get('observation_name')} (code: {obs.get('observation_code', 'N/A')}, id: {obs.get('id')})")
                clinical_arrays['pregnancy_history'] = self._transform_pregnancy_observations(pregnancy_observations)
            elif section_type == 'immunizations' and hasattr(section_data, 'entries'):
                clinical_arrays['immunizations'] = section_data.entries
            elif section_type == 'medical_devices' and hasattr(section_data, 'entries'):
                # Medical devices (implanted/prescribed devices)
                clinical_arrays['medical_devices'] = section_data.entries
            elif section_type == 'advance_directives' and hasattr(section_data, 'entries'):
                # Advance directives (Consent resources)
                clinical_arrays['advance_directives'] = section_data.entries
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
                logger.info(f"[PARSER DEBUG] Extracted source_country from Patient.address: {source_country}")
        
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
                                   related_person_resources: List[Dict],
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
            
            # Extract guardian information (look for guardian relationship in contacts and emergency contacts)
            guardian = None
            
            # First check Patient.contact data
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
                        
                        # Extract guardian details from Patient.contact
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
            
            # If no guardian found in Patient.contact, check emergency contacts from RelatedPerson resources
            if not guardian and related_person_resources:
                # Extract emergency contacts for guardian detection
                emergency_contacts = self._extract_emergency_contacts(related_person_resources)
                
                for emergency_contact in emergency_contacts:
                    # Check if this emergency contact could be a guardian
                    relationship = emergency_contact.get('relationship_display', '').lower()
                    
                    if ('guardian' in relationship or 'parent' in relationship or 
                        'mother' in relationship or 'father' in relationship or
                        'next of kin' in relationship or 'legal' in relationship or
                        'emergency' in relationship):
                        
                        # Convert emergency contact to guardian format
                        contact_info = {
                            'addresses': [],
                            'telecoms': []
                        }
                        
                        # Add address if available
                        addresses = emergency_contact.get('address', [])
                        if addresses:
                            addr = addresses[0]  # Take first address
                            contact_info['addresses'].append({
                                'street_lines': addr.get('line', []),
                                'city': addr.get('city', ''),
                                'state': addr.get('state', ''),
                                'postal_code': addr.get('postalCode', ''),
                                'country': addr.get('country', ''),
                                'full_address': addr.get('full_address', '')
                            })
                        
                        # Add telecoms
                        telecoms = emergency_contact.get('telecom', [])
                        for telecom in telecoms:
                            contact_info['telecoms'].append({
                                'system': telecom.get('system', 'Unknown'),
                                'value': telecom.get('value', ''),
                                'use': telecom.get('use', 'Unknown'),
                                'display': f"{telecom.get('system', 'Contact').title()}: {telecom.get('value', '')}"
                            })
                        
                        # Extract name from the name structure
                        name_info = emergency_contact.get('name', {})
                        given_names = name_info.get('given', [])
                        given_name = ' '.join(given_names) if given_names else ''
                        family_name = name_info.get('family', '')
                        
                        guardian = {
                            'given_name': given_name,
                            'family_name': family_name,
                            'relationship': emergency_contact.get('relationship_display', 'Emergency Contact'),
                            'role': emergency_contact.get('relationship_display', 'Emergency Contact'),
                            'contact_info': contact_info,
                            'gender': emergency_contact.get('gender', 'Unknown'),
                            'organization': emergency_contact.get('organization', '')
                        }
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
    
    def _extract_contact_data(self, patient_resources: List[Dict], related_person_resources: List[Dict] = None, administrative_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract comprehensive contact information for Extended Patient Information tab"""
        contact_data = {
            'addresses': [],
            'telecoms': [],
            'contacts': [],  # Emergency contacts, guardians, etc.
            'emergency_contacts': [],  # Specific emergency contacts from RelatedPerson
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
        
        # Extract emergency contacts from RelatedPerson resources
        if related_person_resources:
            emergency_contacts = self._extract_emergency_contacts(related_person_resources)
            contact_data['emergency_contacts'] = emergency_contacts
            
            # Also add to general contacts for template compatibility
            for emergency_contact in emergency_contacts:
                # Convert to format expected by template
                formatted_emergency_contact = {
                    'name': emergency_contact.get('name', {}),
                    'relationship': emergency_contact.get('relationship', []),
                    'telecom': emergency_contact.get('telecom', []),
                    'address': emergency_contact.get('address', []),
                    'type': 'emergency_contact',
                    'source': 'FHIR RelatedPerson'
                }
                contact_data['contacts'].append(formatted_emergency_contact)
        
        # FIX: If no RelatedPerson resources, map Next-of-Kin from other_contacts to emergency_contacts
        # This handles cases like Diana Ferreira where next-of-kin is in Patient.contact, not RelatedPerson
        if not contact_data['emergency_contacts'] and administrative_data.get('other_contacts'):
            logger.info("[FHIR PARSER] No RelatedPerson resources found, mapping Next-of-Kin from other_contacts to emergency_contacts")
            
            for contact in administrative_data['other_contacts']:
                relationship = contact.get('relationship', '').lower()
                
                # Check if this is an emergency contact or next-of-kin
                if any(keyword in relationship for keyword in ['next-of-kin', 'emergency', 'guardian']):
                    # Convert from other_contacts format to emergency_contacts format
                    emergency_contact = {
                        'id': f"emergency-{contact.get('given_name', '')}-{contact.get('family_name', '')}".lower().replace(' ', '-'),
                        'active': True,
                        'name': {
                            'given': [contact.get('given_name', '')],
                            'family': contact.get('family_name', ''),
                            'full_name': f"{contact.get('given_name', '')} {contact.get('family_name', '')}".strip()
                        },
                        'relationship': [{'text': contact.get('relationship', 'Contact')}],
                        'telecom': [
                            {'system': 'phone', 'value': contact.get('phone', ''), 'use': 'home'} if contact.get('phone') else None,
                            {'system': 'email', 'value': contact.get('email', ''), 'use': 'home'} if contact.get('email') else None
                        ],
                        'address': [{'full_address': contact.get('address', '')}] if contact.get('address') else [],
                        'phone': contact.get('phone'),
                        'email': contact.get('email'),
                        'full_name': f"{contact.get('given_name', '')} {contact.get('family_name', '')}".strip(),
                        'relationship_display': contact.get('relationship', 'Contact'),
                        'source': 'FHIR Patient.contact'
                    }
                    
                    # Remove None values from telecom
                    emergency_contact['telecom'] = [t for t in emergency_contact['telecom'] if t]
                    
                    contact_data['emergency_contacts'].append(emergency_contact)
                    logger.info(f"[FHIR PARSER] Mapped Next-of-Kin to emergency_contact: {emergency_contact['full_name']}")
        
        return contact_data
    
    def _extract_emergency_contacts(self, related_person_resources: List[Dict]) -> List[Dict[str, Any]]:
        """Extract emergency contact information from RelatedPerson resources
        
        This method extracts next of kin, emergency contacts, and guardians from FHIR RelatedPerson resources
        to match the contact information available in CDA documents.
        """
        emergency_contacts = []
        
        if not related_person_resources:
            return emergency_contacts
        
        for related_person in related_person_resources:
            # Extract name information
            names = related_person.get('name', [])
            contact_name = {}
            if names:
                name = names[0]
                contact_name = {
                    'given': name.get('given', []),
                    'family': name.get('family', ''),
                    'text': name.get('text', ''),
                    'full_name': name.get('text', '') or f"{' '.join(name.get('given', []))} {name.get('family', '')}".strip()
                }
            
            # Extract relationship information
            relationships = related_person.get('relationship', [])
            relationship_info = []
            for rel in relationships:
                coding = rel.get('coding', [])
                if coding:
                    relationship_info.append({
                        'code': coding[0].get('code', ''),
                        'display': coding[0].get('display', ''),
                        'system': coding[0].get('system', '')
                    })
                relationship_info.append({
                    'text': rel.get('text', 'Contact')
                })
            
            # Extract contact information
            telecoms = related_person.get('telecom', [])
            contact_telecoms = []
            for telecom in telecoms:
                value = telecom.get('value', '')
                # Clean up prefixes
                if value.startswith('tel:'):
                    value = value[4:]
                elif value.startswith('mailto:'):
                    value = value[7:]
                
                contact_telecoms.append({
                    'system': telecom.get('system', 'phone'),
                    'value': value,
                    'use': telecom.get('use', 'home'),
                    'rank': telecom.get('rank', 1)
                })
            
            # Extract address information
            addresses = related_person.get('address', [])
            contact_addresses = []
            for address in addresses:
                contact_addresses.append({
                    'use': address.get('use', 'home'),
                    'type': address.get('type', 'physical'),
                    'line': address.get('line', []),
                    'city': address.get('city', ''),
                    'state': address.get('state', ''),
                    'postalCode': address.get('postalCode', ''),
                    'country': address.get('country', ''),
                    'full_address': self._format_address(address)
                })
            
            # Extract communication languages
            communication = []
            for comm in related_person.get('communication', []):
                lang_obj = comm.get('language', {})
                lang_code = None
                lang_display = None
                
                if 'coding' in lang_obj and isinstance(lang_obj['coding'], list) and len(lang_obj['coding']) > 0:
                    lang_code = lang_obj['coding'][0].get('code')
                    lang_display = lang_obj['coding'][0].get('display')
                if 'text' in lang_obj:
                    lang_display = lang_obj['text']
                
                if lang_code or lang_display:
                    communication.append({
                        'code': lang_code,
                        'display': lang_display or lang_code,
                        'preferred': comm.get('preferred', False)
                    })
            
            # Extract relationship period
            period = related_person.get('period', {})
            
            # Extract gender and birthDate
            gender = related_person.get('gender')
            birth_date = related_person.get('birthDate')
            
            # Build emergency contact entry
            emergency_contact = {
                'id': related_person.get('id', ''),
                'active': related_person.get('active', True),
                'name': contact_name,
                'relationship': relationship_info,
                'telecom': contact_telecoms,
                'address': contact_addresses,
                'communication': communication,
                'period': period,
                'gender': gender,
                'birth_date': birth_date,
                'patient_reference': related_person.get('patient', {}).get('reference', ''),
                'source': 'FHIR RelatedPerson'
            }
            
            # Add convenience fields for template access
            # Extract primary phone number
            primary_phone = None
            primary_email = None
            for telecom in contact_telecoms:
                if telecom.get('system') == 'phone' and not primary_phone:
                    primary_phone = telecom.get('value')
                elif telecom.get('system') == 'email' and not primary_email:
                    primary_email = telecom.get('value')
            
            emergency_contact['phone'] = primary_phone
            emergency_contact['email'] = primary_email
            emergency_contact['full_name'] = contact_name.get('full_name', '')
            
            # Extract primary relationship display
            relationship_display = 'Contact'
            if relationship_info:
                for rel in relationship_info:
                    if rel.get('display'):
                        relationship_display = rel['display']
                        break
                    elif rel.get('text'):
                        relationship_display = rel['text']
                        break
            emergency_contact['relationship_display'] = relationship_display
            
            emergency_contacts.append(emergency_contact)
        
        return emergency_contacts
        
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
        """Extract healthcare provider data for Extended Patient Information tab
        
        This method maps FHIR resources to match both the template structure and CDA compatibility:
        - practitioners: Array for new FHIR template structure
        - organizations: Array for new FHIR template structure  
        - healthcare_team: Composition author references
        - author_hcp: CDA-compatible author mapping (first practitioner)
        - custodian_organization: CDA-compatible organization mapping (first organization)
        """
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
            
            # Extract practitioner name components
            name_data = practitioner.get('name', [])
            prefix = None
            suffix = None
            if name_data and isinstance(name_data, list) and len(name_data) > 0:
                first_name = name_data[0]
                prefix = ', '.join(first_name.get('prefix', [])) if first_name.get('prefix') else None
                suffix = ', '.join(first_name.get('suffix', [])) if first_name.get('suffix') else None
            
            # Extract communication languages
            communication = []
            for comm in practitioner.get('communication', []):
                lang_code = None
                lang_display = None
                
                # Handle both CodeableConcept and simple coding structure
                if 'coding' in comm:
                    if isinstance(comm['coding'], list) and len(comm['coding']) > 0:
                        lang_code = comm['coding'][0].get('code')
                        lang_display = comm['coding'][0].get('display')
                elif 'language' in comm:
                    lang_obj = comm['language']
                    if 'coding' in lang_obj and isinstance(lang_obj['coding'], list) and len(lang_obj['coding']) > 0:
                        lang_code = lang_obj['coding'][0].get('code')
                        lang_display = lang_obj['coding'][0].get('display')
                    if 'text' in lang_obj:
                        lang_display = lang_obj['text']
                
                if 'text' in comm:
                    lang_display = comm['text']
                
                if lang_code or lang_display:
                    communication.append({
                        'code': lang_code,
                        'display': lang_display or lang_code,
                        'preferred': comm.get('preferred', False)
                    })
            
            # Process qualifications with enhanced details
            qualifications = []
            for qual in practitioner.get('qualification', []):
                qual_code = qual.get('code', {})
                
                # Extract qualification text from code.text or coding display
                qual_text = qual_code.get('text')
                if not qual_text and 'coding' in qual_code:
                    codings = qual_code['coding']
                    if isinstance(codings, list) and len(codings) > 0:
                        qual_text = codings[0].get('display')
                
                # Extract issuer organization
                issuer = None
                issuer_ref = qual.get('issuer', {})
                if issuer_ref:
                    issuer = {
                        'reference': issuer_ref.get('reference'),
                        'display': issuer_ref.get('display')
                    }
                
                # Extract qualification period
                period = qual.get('period', {})
                
                qualifications.append({
                    'code': qual_code,
                    'text': qual_text or 'Healthcare Professional',
                    'identifier': qual.get('identifier', []),
                    'issuer': issuer,
                    'period': period
                })
            
            # Extract role and specialty from qualifications for template compatibility
            role = None
            specialty = None
            if qualifications:
                # Use first qualification as primary role
                role = qualifications[0].get('text', 'Healthcare Professional')
                # If multiple qualifications, second one might be specialty
                if len(qualifications) > 1:
                    specialty = qualifications[1].get('text')
            
            # Extract organization name from organization_resources for display
            organization = None
            if organization_resources:
                # Use first organization as practitioner's organization
                organization = organization_resources[0].get('name', 'Healthcare Organization')
            
            formatted_practitioner = {
                'id': practitioner.get('id', 'Unknown'),
                'name': self._format_practitioner_name(practitioner),
                'family_name': self._extract_practitioner_family_name(practitioner),
                'given_names': self._extract_practitioner_given_names(practitioner),
                'prefix': prefix,
                'suffix': suffix,
                'qualification': qualifications or practitioner.get('qualification', []),
                'role': role,  # Primary role for template display
                'specialty': specialty,  # Specialty for template display
                'organization': organization,  # Organization name for template display
                'communication': communication,
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
            
            # Process organization telecoms from both direct and contact sources
            organization_telecoms = []
            
            # Direct telecoms at organization level
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
            
            # Contact structure telecoms (FHIR Organization.contact format)
            contacts = organization.get('contact', [])
            for contact in contacts:
                contact_telecoms = contact.get('telecom', [])
                for telecom in contact_telecoms:
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
                            'display_name': self._format_telecom_display(telecom),
                            'source': 'contact'
                        }
                        organization_telecoms.append(formatted_telecom)
                
                # Also extract contact addresses if they differ from organization address
                contact_address = contact.get('address', {})
                if contact_address and contact_address not in organization_addresses:
                    formatted_contact_address = {
                        'use': contact_address.get('use', 'work'),
                        'type': contact_address.get('type', 'physical'),
                        'street_lines': contact_address.get('line', []),
                        'street': ', '.join(contact_address.get('line', [])) if contact_address.get('line') else None,
                        'city': contact_address.get('city'),
                        'state': contact_address.get('state'),
                        'postal_code': contact_address.get('postalCode'),
                        'postalCode': contact_address.get('postalCode'),
                        'country': contact_address.get('country'),
                        'period': contact_address.get('period', {}),
                        'full_address': self._format_address(contact_address),
                        'source': 'contact'
                    }
                    organization_addresses.append(formatted_contact_address)
            
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
            
            # Extract organization type with display text
            org_types = []
            for org_type in organization.get('type', []):
                type_text = org_type.get('text')
                if not type_text and 'coding' in org_type:
                    codings = org_type['coding']
                    if isinstance(codings, list) and len(codings) > 0:
                        type_text = codings[0].get('display')
                
                org_types.append({
                    'coding': org_type.get('coding', []),
                    'text': type_text or 'Healthcare Organization'
                })
            
            # Extract parent organization (partOf)
            part_of = None
            part_of_ref = organization.get('partOf', {})
            if part_of_ref:
                part_of = {
                    'reference': part_of_ref.get('reference'),
                    'display': part_of_ref.get('display'),
                    'identifier': part_of_ref.get('identifier')
                }
            
            # Extract aliases
            aliases = organization.get('alias', [])
            
            formatted_organization = {
                'id': organization.get('id', 'Unknown'),
                'name': organization.get('name', 'Unknown Organization'),
                'type': org_types or organization.get('type', []),
                'part_of': part_of,
                'alias': aliases,
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
                reference = author.get('reference', 'Unknown')
                display_name = author.get('display', 'Unknown')
                
                # Enhanced reference resolution for both Practitioner/ and urn:uuid: references
                if display_name == 'Unknown':
                    resolved_name = None
                    
                    # Handle Practitioner/ references
                    if reference.startswith('Practitioner/'):
                        practitioner_id = reference.split('/')[-1]
                        # Find the practitioner in our parsed practitioners
                        for practitioner in healthcare_data['practitioners']:
                            if practitioner.get('id') == practitioner_id:
                                resolved_name = practitioner.get('name', 'Healthcare Professional')
                                break
                    
                    # Handle urn:uuid: references
                    elif reference.startswith('urn:uuid:'):
                        uuid_reference = reference
                        # Find the practitioner by UUID reference
                        for practitioner in healthcare_data['practitioners']:
                            practitioner_ids = practitioner.get('identifiers', [])
                            for identifier in practitioner_ids:
                                if identifier.get('value') == uuid_reference:
                                    resolved_name = practitioner.get('name', 'Healthcare Professional')
                                    break
                            if resolved_name:
                                break
                    
                    # If reference couldn't be resolved, provide informative fallback
                    resolved_practitioner = None
                    if resolved_name:
                        display_name = resolved_name
                        # Find the full practitioner data for role/specialty extraction
                        if reference.startswith('Practitioner/'):
                            practitioner_id = reference.split('/')[-1]
                            for practitioner in healthcare_data['practitioners']:
                                if practitioner.get('id') == practitioner_id:
                                    resolved_practitioner = practitioner
                                    break
                    else:
                        # Extract meaningful info from the reference
                        if reference.startswith('urn:uuid:'):
                            uuid_short = reference.split(':')[-1][:8] + "..."
                            display_name = f"Healthcare Provider (ref: {uuid_short})"
                        elif reference.startswith('Practitioner/'):
                            prac_id = reference.split('/')[-1][:10] + "..." if len(reference.split('/')[-1]) > 10 else reference.split('/')[-1]
                            display_name = f"Healthcare Provider (ID: {prac_id})"
                        else:
                            display_name = "Healthcare Provider (reference not resolved)"
                        
                        # Log the broken reference for debugging
                        logger.warning(f"FHIR Bundle: Could not resolve author reference '{reference}' - no matching Practitioner resource found in bundle")
                
                # Extract role and specialty from matched practitioner, or fallback to author type
                role = None
                specialty = None
                organization = None
                
                if resolved_practitioner:
                    # Use enhanced role/specialty from practitioner
                    role = resolved_practitioner.get('role')
                    specialty = resolved_practitioner.get('specialty')
                    organization = resolved_practitioner.get('organization')
                
                # Fallback to author type if no practitioner role found
                if not role:
                    author_type = author.get('type', 'Author')
                    # Filter out placeholder "nnn" values
                    if author_type and author_type != 'nnn':
                        role = author_type
                    else:
                        role = 'Healthcare Professional'
                
                healthcare_data['healthcare_team'].append({
                    'reference': reference,
                    'name': display_name,  # Use 'name' for template compatibility
                    'role': role,
                    'specialty': specialty,
                    'organization': organization,
                    'telecoms': resolved_practitioner.get('telecoms', []) if resolved_practitioner else [],
                    'addresses': resolved_practitioner.get('addresses', []) if resolved_practitioner else []
                })
        
        # GRACEFUL DEGRADATION: Handle missing Practitioner resources
        # Azure FHIR validation may reject Practitioner uploads, so provide informative placeholders
        if not healthcare_data['practitioners']:
            logger.warning("No Practitioner resources found in bundle - this may be due to Azure FHIR validation issues")
            
            # Add placeholder indicating data unavailability
            healthcare_data['practitioner_unavailable'] = True
            healthcare_data['practitioner_unavailable_reason'] = (
                "Healthcare Professional information is currently unavailable. "
                "This may be due to temporary data synchronization issues."
            )
        
        # FALLBACK: If no practitioners found, try to extract from composition authors
        if not healthcare_data['practitioners'] and composition_resources:
            logger.info("Attempting to extract practitioner info from Composition authors as fallback")
            
            for composition in composition_resources:
                authors = composition.get('author', [])
                title = composition.get('title', 'Document')
                date = composition.get('date', 'Unknown date')
                
                for author in authors:
                    # Create a synthetic practitioner from composition author
                    # Use display name if available, otherwise extract from reference or use document title
                    display_name = author.get('display')
                    reference = author.get('reference', '')
                    
                    # Extract practitioner/organization ID from reference
                    practitioner_id = 'composition-author'
                    if reference.startswith('Practitioner/'):
                        practitioner_id = reference.replace('Practitioner/', '')
                        if not display_name:
                            display_name = f"Practitioner ({practitioner_id[:20]})"
                    elif reference.startswith('Organization/'):
                        practitioner_id = reference.replace('Organization/', '')
                        if not display_name:
                            display_name = f"Organization ({practitioner_id[:20]})"
                    elif reference.startswith('urn:uuid:'):
                        practitioner_id = reference.replace('urn:uuid:', '')
                        if not display_name:
                            # Use document title as fallback to differentiate entries
                            display_name = f"{title} Author"
                    
                    synthetic_practitioner = {
                        'id': practitioner_id,
                        'name': display_name,
                        'family_name': display_name.split()[-1] if ' ' in display_name else display_name,
                        'given_names': display_name.split()[:-1] if ' ' in display_name else [],
                        'qualification': [{'code': {'text': f'Author of {title}', 'coding': [{'code': 'DOC_AUTHOR', 'display': f'Author of {title}'}]}}],
                        'addresses': [],
                        'telecoms': [],
                        'identifiers': [{'system': 'composition-reference', 'value': reference, 'type': 'Reference'}],
                        'gender': 'Unknown',
                        'active': True,
                        'source': 'composition-author',
                        'document_title': title,
                        'document_date': date
                    }
                    
                    healthcare_data['practitioners'].append(synthetic_practitioner)
                    logger.info(f"Created synthetic practitioner from composition author: {display_name}")
        
        # ADDITIONAL FALLBACK: If still no practitioners and no filtered organizations, create minimal info
        if not healthcare_data['practitioners'] and not healthcare_data['organizations']:
            logger.info("No healthcare provider information found, creating minimal fallback entry")
            
            fallback_practitioner = {
                'id': 'unknown-provider',
                'name': 'Healthcare Provider',
                'family_name': 'Provider',
                'given_names': ['Healthcare'],
                'qualification': [{'code': {'text': 'Document author/provider information not available in bundle', 'coding': [{'code': 'UNKNOWN', 'display': 'Provider information not available'}]}}],
                'addresses': [],
                'telecoms': [],
                'identifiers': [],
                'gender': 'Unknown',
                'active': True,
                'source': 'fallback',
                'note': 'Provider information not included in the FHIR Patient Summary'
            }
            
            healthcare_data['practitioners'].append(fallback_practitioner)
        
        # CDA COMPATIBILITY MAPPING: Map FHIR resources to CDA-style structure for backwards compatibility
        self._add_cda_compatibility_mapping(healthcare_data, composition_resources)
        
        return healthcare_data
    
    def _add_cda_compatibility_mapping(self, healthcare_data: Dict[str, Any], composition_resources: List[Dict]) -> None:
        """Add CDA-style mappings to healthcare data for backwards compatibility
        
        Maps FHIR practitioner and organization resources to CDA-style fields:
        - author_hcp: Maps to first practitioner with proper CDA structure
        - custodian_organization: Maps to first organization with proper CDA structure
        - legal_authenticator: If specified in composition
        """
        
        # Map first practitioner to author_hcp (CDA-style)
        if healthcare_data['practitioners']:
            first_practitioner = healthcare_data['practitioners'][0]
            
            # Convert FHIR practitioner to CDA-style author_hcp structure
            # Use the enhanced role, specialty, organization fields added in formatted_practitioner
            healthcare_data['author_hcp'] = {
                'id': first_practitioner.get('id'),
                'family_name': first_practitioner.get('family_name', 'Unknown'),
                'given_name': ' '.join(first_practitioner.get('given_names', [])) if first_practitioner.get('given_names') else 'Unknown',
                'full_name': first_practitioner.get('name', 'Unknown Healthcare Provider'),
                'prefix': first_practitioner.get('prefix'),
                'suffix': first_practitioner.get('suffix'),
                'title': self._extract_practitioner_title(first_practitioner),
                'role': first_practitioner.get('role') or self._extract_practitioner_role(first_practitioner),
                'specialty': first_practitioner.get('specialty'),
                'organization': first_practitioner.get('organization'),
                'identifiers': first_practitioner.get('identifiers', []),
                'telecoms': first_practitioner.get('telecoms', []),
                'addresses': first_practitioner.get('addresses', []),
                'qualification': first_practitioner.get('qualification', []),
                'qualifications': first_practitioner.get('qualification', []),  # Backwards compatibility
                'communication': first_practitioner.get('communication', []),
                'active': first_practitioner.get('active', True),
                'source': 'fhir-practitioner',
                'fhir_reference': f"Practitioner/{first_practitioner.get('id')}"
            }
            logger.info(f"Mapped first practitioner to author_hcp: {healthcare_data['author_hcp']['full_name']}")
        
        # Map first organization to custodian_organization (CDA-style)  
        if healthcare_data['organizations']:
            first_organization = healthcare_data['organizations'][0]
            
            # Convert FHIR organization to CDA-style custodian structure
            healthcare_data['custodian_organization'] = {
                'id': first_organization.get('id'),
                'name': first_organization.get('name', 'Unknown Healthcare Organization'),
                'identifiers': first_organization.get('identifiers', []),
                'telecoms': first_organization.get('telecoms', []),
                'addresses': first_organization.get('addresses', []),
                'type': first_organization.get('type', []),
                'contact': first_organization.get('contact', []),
                'active': first_organization.get('active', True),
                'source': 'fhir-organization',
                'fhir_reference': f"Organization/{first_organization.get('id')}"
            }
            logger.info(f"Mapped first organization to custodian_organization: {healthcare_data['custodian_organization']['name']}")
        
        # Check composition for legal authenticator (if different from author)
        if composition_resources:
            composition = composition_resources[0]
            
            # In FHIR, legal authenticator would typically be identified by specific author roles
            # For now, we'll use the author as legal authenticator if no separate one is found
            if healthcare_data.get('author_hcp') and not healthcare_data.get('legal_authenticator'):
                healthcare_data['legal_authenticator'] = {
                    'family_name': healthcare_data['author_hcp']['family_name'],
                    'given_name': healthcare_data['author_hcp']['given_name'],
                    'full_name': healthcare_data['author_hcp']['full_name'],
                    'title': healthcare_data['author_hcp'].get('title'),
                    'role': healthcare_data['author_hcp'].get('role', 'Document Author'),
                    'signature_code': 'S',  # Signed
                    'time': composition.get('date'),
                    'source': 'fhir-composition-author',
                    'fhir_reference': healthcare_data['author_hcp'].get('fhir_reference')
                }
                logger.info(f"Mapped author as legal_authenticator: {healthcare_data['legal_authenticator']['full_name']}")
    
    def _extract_practitioner_title(self, practitioner: Dict[str, Any]) -> str:
        """Extract practitioner title from qualifications or name"""
        qualifications = practitioner.get('qualification', [])
        if qualifications:
            for qual in qualifications:
                code = qual.get('code', {})
                if code.get('text'):
                    return code['text']
                elif code.get('coding') and code['coding']:
                    return code['coding'][0].get('display', 'Healthcare Professional')
        return 'Healthcare Professional'
    
    def _extract_practitioner_role(self, practitioner: Dict[str, Any]) -> str:
        """Extract practitioner role from source or qualifications"""
        source = practitioner.get('source')
        if source == 'composition-author':
            return 'Document Author'
        elif source == 'fallback':
            return 'Healthcare Provider'
        else:
            return 'Healthcare Professional'
    
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
    
    def _get_allergy_severity_summary(self, reactions: List[Dict[str, Any]]) -> str:
        """Generate summary of allergy reaction severities"""
        if not reactions:
            return 'No reactions recorded'
        
        severities = [reaction.get('severity', 'Unknown').lower() for reaction in reactions]
        
        # Count severity levels
        severe_count = severities.count('severe')
        moderate_count = severities.count('moderate')
        mild_count = severities.count('mild')
        unknown_count = severities.count('unknown')
        
        # Build summary
        summary_parts = []
        if severe_count > 0:
            summary_parts.append(f"{severe_count} severe")
        if moderate_count > 0:
            summary_parts.append(f"{moderate_count} moderate")
        if mild_count > 0:
            summary_parts.append(f"{mild_count} mild")
        if unknown_count > 0:
            summary_parts.append(f"{unknown_count} unknown severity")
        
        if summary_parts:
            return f"{len(reactions)} reaction{'s' if len(reactions) != 1 else ''}: {', '.join(summary_parts)}"
        else:
            return f"{len(reactions)} reaction{'s' if len(reactions) != 1 else ''} recorded"
    
    def _assess_observation_significance(self, observation: Dict[str, Any], value_data: Dict[str, Any], 
                                        reference_ranges: List[Dict[str, Any]], interpretation: str) -> str:
        """Assess clinical significance of observation value"""
        # Check interpretation first
        if interpretation:
            interpretation_lower = interpretation.lower()
            if any(term in interpretation_lower for term in ['high', 'elevated', 'increased', 'above']):
                return 'Above normal'
            elif any(term in interpretation_lower for term in ['low', 'decreased', 'below']):
                return 'Below normal'
            elif any(term in interpretation_lower for term in ['normal', 'within', 'reference']):
                return 'Within normal range'
            elif any(term in interpretation_lower for term in ['critical', 'panic', 'alert']):
                return 'Critical value'
            elif any(term in interpretation_lower for term in ['abnormal', 'unusual']):
                return 'Abnormal'
        
        # Try to assess based on reference ranges if available
        if reference_ranges and value_data.get('value') is not None:
            try:
                obs_value = float(value_data['value'])
                for ref_range in reference_ranges:
                    low_data = ref_range.get('low', {})
                    high_data = ref_range.get('high', {})
                    
                    low_value = low_data.get('value')
                    high_value = high_data.get('value')
                    
                    if low_value is not None and obs_value < float(low_value):
                        return 'Below reference range'
                    elif high_value is not None and obs_value > float(high_value):
                        return 'Above reference range'
                    elif low_value is not None and high_value is not None:
                        if float(low_value) <= obs_value <= float(high_value):
                            return 'Within reference range'
            except (ValueError, TypeError):
                pass  # Could not convert to numeric for comparison
        
        # Check observation status for additional context
        status = observation.get('status', '').lower()
        if status in ['cancelled', 'entered-in-error']:
            return 'Invalid result'
        elif status == 'preliminary':
            return 'Preliminary result'
        elif status == 'amended':
            return 'Amended result'
        
        return 'Result recorded'
    
    def _get_atc_drug_name(self, atc_code: str) -> Optional[str]:
        """
        Look up common ATC codes to provide drug names
        
        This is a basic lookup for common medications. In production, this should
        use a comprehensive ATC/drug name database or terminology service.
        
        Args:
            atc_code: ATC classification code (e.g., 'H03AA01')
            
        Returns:
            Drug name or None if not found
        """
        # Common ATC codes used in healthcare
        ATC_LOOKUP = {
            # Thyroid therapy
            'H03AA01': 'Levothyroxine',
            'H03AA02': 'Liothyronine',
            
            # Respiratory system - bronchodilators
            'R03AL02': 'Ipratropium and Salbutamol (combination)',
            'R03AC02': 'Salbutamol',
            'R03AL01': 'Ipratropium and Fenoterol (combination)',
            'R03BB01': 'Ipratropium bromide',
            
            # Antibiotics - Beta-lactams
            'J01CR02': 'Amoxicillin and Clavulanic Acid (Augmentin)',
            'J01CA04': 'Amoxicillin',
            'J01CR05': 'Amoxicillin and Sulbactam',
            
            # Insulin and analogues
            'A10AE06': 'Insulin degludec (Tresiba)',
            'A10AE04': 'Insulin glargine (Lantus)',
            'A10AE05': 'Insulin detemir',
            'A10AB01': 'Insulin (human)',
            'A10AB05': 'Insulin aspart',
            
            # ACE inhibitors and combinations
            'C09BB05': 'Ramipril and Felodipine (combination)',
            'C09AA05': 'Ramipril',
            'C09AA02': 'Enalapril',
            'C09BB07': 'Ramipril and Amlodipine',
            
            # Antihypertensives
            'C08CA01': 'Amlodipine',
            'C07AB02': 'Metoprolol',
            'C08CA02': 'Felodipine',
            
            # Commonly used medications
            'A02BC01': 'Omeprazole',
            'A02BC02': 'Pantoprazole',
            'B01AC06': 'Acetylsalicylic acid (Aspirin)',
            'C10AA01': 'Simvastatin',
            'C10AA05': 'Atorvastatin',
            'A10BA02': 'Metformin',
        }
        
        return ATC_LOOKUP.get(atc_code)


class FHIRBundleParserError(Exception):
    """Custom exception for FHIR Bundle parsing errors"""
    pass


# Service instance for dependency injection
fhir_bundle_parser = FHIRBundleParser()