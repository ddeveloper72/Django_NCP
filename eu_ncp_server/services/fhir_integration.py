"""
HAPI FHIR Integration Service
HAPI FHIR Server Integration for Django NCP

This service handles:
- HAPI FHIR R4 server connectivity and authentication
- Patient Summary Bundle retrieval and posting
- Healthcare provider and organization lookup
- FHIR resource validation and conversion
- Audit logging for healthcare data access

HAPI FHIR Server Details:
- Base URL: https://hapi.fhir.org/baseR4 (test server)
- FHIR Version: R4 (4.0.1)
- Software: HAPI FHIR Server 8.5.3
- Available Resources: Patient, Bundle, Composition, etc.
"""

import requests
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger("ehealth")
audit_logger = logging.getLogger("audit")


class HAPIFHIRIntegrationService:
    """Service for integrating with HAPI FHIR R4 server"""
    
    def __init__(self):
        # HAPI FHIR server configuration
        self.base_url = getattr(settings, 'HAPI_FHIR_BASE_URL', 'https://hapi.fhir.org/baseR4')
        self.timeout = getattr(settings, 'HAPI_FHIR_TIMEOUT', 30)
        self.cache_timeout = 300  # 5 minutes
        
    def _get_headers(self) -> Dict[str, str]:
        """Get standard headers for HAPI FHIR API requests"""
        headers = {
            'Accept': 'application/fhir+json',
            'Content-Type': 'application/fhir+json',
            'User-Agent': 'Django-NCP/1.0'
        }
        return headers
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make request to HAPI FHIR server"""
        url = f"{self.base_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        headers = self._get_headers()
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=self.timeout)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"HAPI FHIR API request failed: {url} - {str(e)}")
            raise HAPIFHIRIntegrationError(f"HAPI FHIR server request failed: {str(e)}")
    
    def test_connectivity(self) -> Dict[str, Any]:
        """Test connectivity to HAPI FHIR server and return capabilities"""
        try:
            start_time = datetime.now()
            
            # Get FHIR server capabilities/metadata
            capabilities = self._make_request('GET', 'metadata')
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            result = {
                'status': 'connected',
                'server_version': capabilities.get('fhirVersion', 'unknown'),
                'software_name': capabilities.get('software', {}).get('name', 'HAPI FHIR'),
                'software_version': capabilities.get('software', {}).get('version', 'unknown'),
                'supported_resources': [],
                'response_time_ms': round(response_time, 2),
                'base_url': self.base_url,
                'test_timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # Extract supported resource types
            for rest in capabilities.get('rest', []):
                for resource in rest.get('resource', []):
                    result['supported_resources'].append(resource.get('type'))
            
            logger.info(f"HAPI FHIR connectivity test successful: {len(result['supported_resources'])} resources available")
            return result
            
        except Exception as e:
            logger.error(f"HAPI FHIR connectivity test failed: {str(e)}")
            return {
                'status': 'disconnected',
                'error': str(e),
                'base_url': self.base_url,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def get_patient_summary(self, patient_id: str, requesting_user: str) -> Dict[str, Any]:
        """
        Retrieve Patient Summary Bundle from HAPI FHIR server
        
        Args:
            patient_id: Unique patient identifier  
            requesting_user: Username of requesting healthcare professional
            
        Returns:
            FHIR Bundle containing Patient Summary components
        """
        try:
            # Check cache first
            cache_key = f"hapi_fhir_patient_summary_{patient_id}"
            cached_summary = cache.get(cache_key)
            if cached_summary:
                audit_logger.info(f"HAPI FHIR Patient Summary (cached): patient_id={patient_id}, user={requesting_user}")
                return cached_summary
            
            # Try patient-specific $summary operation first
            try:
                endpoint = f"Patient/{patient_id}/$summary"
                summary_bundle = self._make_request('GET', endpoint)
                
                if summary_bundle.get('resourceType') == 'Bundle':
                    # Cache and return the summary
                    cache.set(cache_key, summary_bundle, self.cache_timeout)
                    audit_logger.info(f"HAPI FHIR Patient Summary retrieved via $summary: patient_id={patient_id}, user={requesting_user}")
                    return summary_bundle
                    
            except HAPIFHIRIntegrationError:
                # $summary operation might not be available, fall back to manual assembly
                logger.info(f"$summary operation not available for patient {patient_id}, assembling manually")
            
            # Manual Patient Summary assembly
            summary_bundle = self._assemble_patient_summary(patient_id)
            
            # Cache the result
            cache.set(cache_key, summary_bundle, self.cache_timeout)
            
            # Audit log the access
            audit_logger.info(
                f"HAPI FHIR Patient Summary assembled: patient_id={patient_id}, "
                f"user={requesting_user}, resources={len(summary_bundle.get('entry', []))}"
            )
            
            return summary_bundle
            
        except Exception as e:
            logger.error(f"Failed to retrieve Patient Summary from HAPI FHIR: patient_id={patient_id}, error={str(e)}")
            raise HAPIFHIRIntegrationError(f"Patient Summary retrieval failed: {str(e)}")
    
    def _assemble_patient_summary(self, patient_id: str) -> Dict[str, Any]:
        """
        Manually assemble Patient Summary Bundle by querying individual resources
        """
        try:
            bundle_entries = []
            
            # 1. Get Patient resource
            try:
                patient = self._make_request('GET', f"Patient/{patient_id}")
                bundle_entries.append({'resource': patient})
            except HAPIFHIRIntegrationError:
                logger.warning(f"Patient {patient_id} not found in HAPI FHIR server")
                # Create a basic patient structure for testing
                patient = {
                    'resourceType': 'Patient',
                    'id': patient_id,
                    'name': [{'family': 'Unknown', 'given': ['Patient']}],
                    'birthDate': '1980-01-01',
                    'gender': 'unknown'
                }
                bundle_entries.append({'resource': patient})
            
            # 2. Get Composition resource (critical for healthcare team enrichment)
            # FIX: Only include the LATEST composition to prevent duplication
            try:
                search_params = {'subject': f"Patient/{patient_id}", '_count': '10'}
                composition_results = self._make_request('GET', 'Composition', params=search_params)
                
                if composition_results.get('entry'):
                    # Sort compositions by date (newest first) and take only the latest
                    composition_entries = composition_results['entry']
                    sorted_compositions = sorted(
                        composition_entries,
                        key=lambda e: e.get('resource', {}).get('date', ''),
                        reverse=True
                    )
                    
                    if sorted_compositions:
                        latest_composition = sorted_compositions[0]
                        bundle_entries.append({'resource': latest_composition['resource']})
                        logger.info(
                            f"Added latest Composition (ID: {latest_composition['resource'].get('id')}, "
                            f"Date: {latest_composition['resource'].get('date')}) out of "
                            f"{len(composition_entries)} found to bundle"
                        )
                        
            except HAPIFHIRIntegrationError:
                logger.debug(f"No Composition resources found for patient {patient_id}")
            
            # 3. Get related clinical resources
            clinical_resources = [
                'AllergyIntolerance',
                'MedicationStatement', 
                'Condition',
                'Observation',
                'Procedure',
                'Immunization'
            ]
            
            for resource_type in clinical_resources:
                try:
                    # FIX: Query for latest resources only using FHIR standard search parameters
                    # _sort=-_lastUpdated: Sort by last updated descending (newest first)
                    # _count=50: Reasonable limit (will be deduplicated if needed)
                    search_params = {
                        'patient': patient_id,
                        '_sort': '-_lastUpdated',  # Newest first
                        '_count': '50'
                    }
                    search_results = self._make_request('GET', resource_type, params=search_params)
                    
                    if search_results.get('entry'):
                        entries = search_results['entry']
                        original_count = len(entries)
                        
                        # DEDUPLICATION: Remove duplicate resources based on content
                        # Public FHIR servers may return duplicates even with _sort parameter
                        # Deduplicate by comparing medication names, codes, and dosages
                        deduplicated_entries = self._deduplicate_clinical_resources(entries, resource_type)
                        
                        if len(deduplicated_entries) < original_count:
                            logger.warning(
                                f"Deduplicated {resource_type}: {original_count} -> {len(deduplicated_entries)} "
                                f"(removed {original_count - len(deduplicated_entries)} duplicates from HAPI server)"
                            )
                        
                        for entry in deduplicated_entries:
                            bundle_entries.append({'resource': entry['resource']})
                            
                except HAPIFHIRIntegrationError:
                    logger.debug(f"No {resource_type} resources found for patient {patient_id}")
                    continue
            
            # 4. Create Patient Summary Bundle
            summary_bundle = {
                'resourceType': 'Bundle',
                'id': f'patient-summary-{patient_id}',
                'type': 'document',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'total': len(bundle_entries),
                'entry': bundle_entries,
                'meta': {
                    'source': 'HAPI FHIR Server',
                    'assembled_by': 'Django NCP',
                    'assembly_timestamp': datetime.now(timezone.utc).isoformat()
                }
            }
            
            return summary_bundle
            
        except Exception as e:
            logger.error(f"Error assembling Patient Summary for {patient_id}: {str(e)}")
            raise HAPIFHIRIntegrationError(f"Patient Summary assembly failed: {str(e)}")
    
    def _deduplicate_clinical_resources(self, entries: List[Dict], resource_type: str) -> List[Dict]:
        """
        Deduplicate clinical resources based on content, not just ID
        
        Some FHIR servers (especially public test servers) may return duplicate resources
        with different IDs but identical content. This method deduplicates by comparing
        the actual clinical content (medication name, dosage, dates, etc.)
        
        Args:
            entries: List of FHIR resource entries
            resource_type: Type of resource (MedicationStatement, Condition, etc.)
            
        Returns:
            Deduplicated list of entries
        """
        if not entries or len(entries) <= 1:
            return entries
        
        seen_signatures = set()
        deduplicated = []
        
        for entry in entries:
            resource = entry.get('resource', {})
            
            # Create a content signature based on resource type
            signature = self._create_resource_signature(resource, resource_type)
            
            if signature not in seen_signatures:
                seen_signatures.add(signature)
                deduplicated.append(entry)
        
        return deduplicated
    
    def _create_resource_signature(self, resource: Dict[str, Any], resource_type: str) -> str:
        """
        Create a unique signature for a clinical resource based on its content
        
        This signature is used to identify duplicate resources that have different IDs
        but represent the same clinical information.
        """
        import hashlib
        import json
        
        signature_parts = []
        
        if resource_type == 'MedicationStatement':
            # Signature: ATC code ONLY + status + effective period
            # CRITICAL: Use ATC code for deduplication, ignore display/text fields
            # - Different brand names (Eutirox, Levothyroxine) = same ATC code (H03AA01)
            # - Display text may be in foreign language from member state
            # - Matches CTS agent approach: deduplicate by clinical code, not name
            med_concept = resource.get('medicationCodeableConcept', {})
            med_ref = resource.get('medicationReference', {})
            
            # Get medication identifier - PREFER ATC CODE ONLY
            if med_concept.get('coding'):
                code = med_concept['coding'][0].get('code', '')
                system = med_concept['coding'][0].get('system', '')
                # Use code only (not display) for ATC codes
                if system == 'http://www.whocc.no/atc' and code:
                    signature_parts.append(code)  # ATC code only
                else:
                    # Non-ATC codes: use both code and display
                    display = med_concept['coding'][0].get('display', '')
                    signature_parts.extend([code, display])
            elif med_concept.get('text'):
                signature_parts.append(med_concept['text'])
            elif med_ref.get('display'):
                signature_parts.append(med_ref['display'])
            
            # Add status and dates
            signature_parts.append(resource.get('status', ''))
            effective = resource.get('effectivePeriod', {})
            signature_parts.append(effective.get('start', ''))
            signature_parts.append(effective.get('end', ''))
            
            # Add dosage information
            dosages = resource.get('dosage', [])
            if dosages:
                signature_parts.append(dosages[0].get('text', ''))
        
        elif resource_type == 'AllergyIntolerance':
            # Signature: allergen code + clinical status + verification status
            code = resource.get('code', {})
            if code.get('coding'):
                signature_parts.append(code['coding'][0].get('code', ''))
                signature_parts.append(code['coding'][0].get('display', ''))
            elif code.get('text'):
                signature_parts.append(code['text'])
            
            clinical_status = resource.get('clinicalStatus', {})
            if clinical_status.get('coding'):
                signature_parts.append(clinical_status['coding'][0].get('code', ''))
            
            verification_status = resource.get('verificationStatus', {})
            if verification_status.get('coding'):
                signature_parts.append(verification_status['coding'][0].get('code', ''))
        
        elif resource_type == 'Condition':
            # Signature: condition code + clinical status + onset date
            code = resource.get('code', {})
            if code.get('coding'):
                signature_parts.append(code['coding'][0].get('code', ''))
                signature_parts.append(code['coding'][0].get('display', ''))
            elif code.get('text'):
                signature_parts.append(code['text'])
            
            clinical_status = resource.get('clinicalStatus', {})
            if clinical_status.get('coding'):
                signature_parts.append(clinical_status['coding'][0].get('code', ''))
            
            signature_parts.append(resource.get('onsetDateTime', ''))
        
        elif resource_type == 'Observation':
            # Signature: observation code + value + effective date
            code = resource.get('code', {})
            if code.get('coding'):
                signature_parts.append(code['coding'][0].get('code', ''))
            
            # Add value (can be quantity, string, or codeable concept)
            if 'valueQuantity' in resource:
                val = resource['valueQuantity']
                signature_parts.extend([str(val.get('value', '')), val.get('unit', '')])
            elif 'valueString' in resource:
                signature_parts.append(resource['valueString'])
            elif 'valueCodeableConcept' in resource:
                val_code = resource['valueCodeableConcept']
                if val_code.get('coding'):
                    signature_parts.append(val_code['coding'][0].get('code', ''))
            
            signature_parts.append(resource.get('effectiveDateTime', ''))
        
        elif resource_type == 'Procedure':
            # Signature: procedure code + status + performed date
            code = resource.get('code', {})
            if code.get('coding'):
                signature_parts.append(code['coding'][0].get('code', ''))
                signature_parts.append(code['coding'][0].get('display', ''))
            
            signature_parts.append(resource.get('status', ''))
            signature_parts.append(resource.get('performedDateTime', ''))
        
        elif resource_type == 'Immunization':
            # Signature: vaccine code + status + occurrence date
            vaccine_code = resource.get('vaccineCode', {})
            if vaccine_code.get('coding'):
                signature_parts.append(vaccine_code['coding'][0].get('code', ''))
            
            signature_parts.append(resource.get('status', ''))
            signature_parts.append(resource.get('occurrenceDateTime', ''))
        
        else:
            # Generic signature: resource ID (fallback)
            signature_parts.append(resource.get('id', ''))
        
        # Create hash of signature parts
        signature_string = '|'.join(str(part) for part in signature_parts if part)
        return hashlib.md5(signature_string.encode()).hexdigest()
    
    def post_patient_summary(self, patient_summary_bundle: Dict[str, Any], requesting_user: str) -> Dict[str, Any]:
        """
        Post Patient Summary Bundle to HAPI FHIR server
        
        Args:
            patient_summary_bundle: FHIR Bundle to post
            requesting_user: Username of posting user
            
        Returns:
            Server response with created resource information
        """
        try:
            # Validate bundle structure
            if not self._validate_fhir_bundle(patient_summary_bundle):
                raise ValueError("Invalid FHIR Bundle structure")
            
            # Post bundle to HAPI FHIR server
            response = self._make_request('POST', '', patient_summary_bundle)
            
            # Extract created resource information
            created_resources = []
            if response.get('resourceType') == 'Bundle' and response.get('type') == 'transaction-response':
                for entry in response.get('entry', []):
                    if entry.get('response', {}).get('status', '').startswith('201'):
                        created_resources.append({
                            'resource_type': entry.get('resource', {}).get('resourceType'),
                            'id': entry.get('resource', {}).get('id'),
                            'location': entry.get('response', {}).get('location')
                        })
            
            result = {
                'status': 'success',
                'bundle_id': response.get('id'),
                'created_resources': created_resources,
                'server_response': response,
                'posted_at': datetime.now(timezone.utc).isoformat()
            }
            
            audit_logger.info(
                f"Patient Summary posted to HAPI FHIR: resources={len(created_resources)}, "
                f"user={requesting_user}, bundle_id={response.get('id')}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to post Patient Summary to HAPI FHIR: {str(e)}")
            raise HAPIFHIRIntegrationError(f"Patient Summary posting failed: {str(e)}")
    
    def search_patients(self, search_params: Dict[str, str]) -> Dict[str, Any]:
        """
        Search for patients in HAPI FHIR server
        
        Args:
            search_params: Dictionary containing search criteria
                - name: Patient name
                - birthdate: Birth date
                - identifier: Patient identifier
                - gender: Patient gender
                
        Returns:
            Search results with patient information
        """
        try:
            # Build FHIR search parameters
            fhir_params = {}
            if search_params.get('name'):
                fhir_params['name'] = search_params['name']
            if search_params.get('birthdate'):
                fhir_params['birthdate'] = search_params['birthdate']
            if search_params.get('identifier'):
                fhir_params['identifier'] = search_params['identifier']
            if search_params.get('gender'):
                fhir_params['gender'] = search_params['gender']
            
            # Add pagination
            fhir_params['_count'] = search_params.get('limit', '20')
            fhir_params['_offset'] = search_params.get('offset', '0')
            
            search_results = self._make_request('GET', 'Patient', params=fhir_params)
            
            # Process search results
            patients = []
            for entry in search_results.get('entry', []):
                resource = entry.get('resource', {})
                if resource.get('resourceType') == 'Patient':
                    patient_info = self._extract_patient_info(resource)
                    patients.append(patient_info)
            
            result = {
                'total': search_results.get('total', len(patients)),
                'patients': patients,
                'search_parameters': search_params,
                'search_timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            audit_logger.info(f"Patient search in HAPI FHIR: params={search_params}, results={len(patients)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Patient search in HAPI FHIR failed: {str(e)}")
            raise HAPIFHIRIntegrationError(f"Patient search failed: {str(e)}")
    
    def search_patient_documents(self, patient_id: str) -> Dict[str, Any]:
        """
        Search for patient documents (Compositions) in HAPI FHIR server
        
        Args:
            patient_id: Unique patient identifier
            
        Returns:
            Search results with patient document information
        """
        try:
            # Search for Compositions (patient documents) for this patient
            fhir_params = {
                'subject': f'Patient/{patient_id}',
                '_count': '50'
            }
            
            search_results = self._make_request('GET', 'Composition', params=fhir_params)
            
            # Process composition results
            documents = []
            for entry in search_results.get('entry', []):
                resource = entry.get('resource', {})
                if resource.get('resourceType') == 'Composition':
                    doc_info = self._extract_composition_info(resource)
                    documents.append(doc_info)
            
            result = {
                'total': search_results.get('total', len(documents)),
                'documents': documents,
                'patient_id': patient_id,
                'search_timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            audit_logger.info(f"Patient document search in HAPI FHIR: patient_id={patient_id}, results={len(documents)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Patient document search in HAPI FHIR failed: {str(e)}")
            raise HAPIFHIRIntegrationError(f"Patient document search failed: {str(e)}")
    
    def search_practitioners(self, patient_id: str = None) -> List[Dict[str, Any]]:
        """
        Search for Practitioner resources related to a patient
        
        Args:
            patient_id: Optional patient identifier to find related practitioners
            
        Returns:
            List of Practitioner resources
        """
        try:
            fhir_params = {
                '_count': '50'
            }
            
            # If patient_id provided, search for practitioners involved with this patient
            # Note: HAPI doesn't directly support patient-practitioner search,
            # so we search all and filter client-side if needed
            
            search_results = self._make_request('GET', 'Practitioner', params=fhir_params)
            
            practitioners = []
            for entry in search_results.get('entry', []):
                resource = entry.get('resource', {})
                if resource.get('resourceType') == 'Practitioner':
                    practitioners.append(resource)
            
            logger.info(f"Practitioner search in HAPI FHIR: found {len(practitioners)} practitioners")
            
            return practitioners
            
        except Exception as e:
            logger.warning(f"Practitioner search in HAPI FHIR failed: {str(e)}")
            return []
    
    def search_organizations(self, patient_id: str = None) -> List[Dict[str, Any]]:
        """
        Search for Organization resources related to a patient
        
        Args:
            patient_id: Optional patient identifier to find related organizations
            
        Returns:
            List of Organization resources
        """
        try:
            fhir_params = {
                '_count': '50'
            }
            
            search_results = self._make_request('GET', 'Organization', params=fhir_params)
            
            organizations = []
            for entry in search_results.get('entry', []):
                resource = entry.get('resource', {})
                if resource.get('resourceType') == 'Organization':
                    organizations.append(resource)
            
            logger.info(f"Organization search in HAPI FHIR: found {len(organizations)} organizations")
            
            return organizations
            
        except Exception as e:
            logger.warning(f"Organization search in HAPI FHIR failed: {str(e)}")
            return []
    
    def get_resource_by_id(self, resource_type: str, resource_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific FHIR resource by type and ID
        
        Args:
            resource_type: FHIR resource type (e.g., 'Practitioner', 'Organization')
            resource_id: Resource ID or UUID
            
        Returns:
            Resource dict or None if not found
        """
        try:
            # Handle both regular IDs and UUIDs
            endpoint = f"{resource_type}/{resource_id}"
            resource = self._make_request('GET', endpoint)
            
            if resource.get('resourceType') == resource_type:
                logger.info(f"Retrieved {resource_type} resource: {resource_id}")
                return resource
            else:
                logger.warning(f"Resource type mismatch for {resource_id}")
                return None
                
        except Exception as e:
            logger.warning(f"Failed to retrieve {resource_type}/{resource_id}: {str(e)}")
            return None
    
    def _extract_composition_info(self, composition_resource: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant information from FHIR Composition resource"""
        composition_info = {
            'id': composition_resource.get('id'),
            'title': composition_resource.get('title', 'Patient Document'),
            'status': composition_resource.get('status', 'unknown'),
            'date': composition_resource.get('date'),
            'type': composition_resource.get('type', {}).get('text', 'Patient Summary'),
            'subject_reference': composition_resource.get('subject', {}).get('reference'),
            'author': [],
            'custodian': composition_resource.get('custodian', {}).get('display'),
            'sections': []
        }
        
        # Extract authors
        for author in composition_resource.get('author', []):
            composition_info['author'].append({
                'reference': author.get('reference'),
                'display': author.get('display', 'Unknown Author')
            })
        
        # Extract sections
        for section in composition_resource.get('section', []):
            section_info = {
                'title': section.get('title', 'Unknown Section'),
                'code': section.get('code', {}).get('text', 'Unknown'),
                'entry_count': len(section.get('entry', []))
            }
            composition_info['sections'].append(section_info)
        
        return composition_info
    
    def _validate_fhir_bundle(self, bundle: Dict[str, Any]) -> bool:
        """Validate basic FHIR Bundle structure"""
        required_fields = ['resourceType', 'type']
        return all(field in bundle for field in required_fields) and bundle['resourceType'] == 'Bundle'
    
    def _extract_patient_info(self, patient_resource: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant information from FHIR Patient resource"""
        patient_info = {
            'id': patient_resource.get('id'),
            'name': 'Unknown Patient',
            'birth_date': patient_resource.get('birthDate'),
            'gender': patient_resource.get('gender'),
            'identifiers': [],
            'addresses': [],
            'telecoms': []
        }
        
        # Extract name
        names = patient_resource.get('name', [])
        if names:
            name_parts = []
            if names[0].get('prefix'):
                name_parts.extend(names[0]['prefix'])
            if names[0].get('given'):
                name_parts.extend(names[0]['given'])
            if names[0].get('family'):
                name_parts.append(names[0]['family'])
            patient_info['name'] = ' '.join(name_parts)
        
        # Extract identifiers
        for identifier in patient_resource.get('identifier', []):
            patient_info['identifiers'].append({
                'system': identifier.get('system'),
                'value': identifier.get('value'),
                'type': identifier.get('type', {}).get('text', 'Unknown')
            })
        
        return patient_info


class HAPIFHIRIntegrationError(Exception):
    """Custom exception for HAPI FHIR integration errors"""
    pass


# Service instance for dependency injection
hapi_fhir_service = HAPIFHIRIntegrationService()