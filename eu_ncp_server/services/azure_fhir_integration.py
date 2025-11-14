"""
Azure FHIR Integration Service

Azure Healthcare APIs FHIR service integration for Django NCP

This service handles:
- Azure FHIR R4 server connectivity with Azure AD authentication
- Patient Summary Bundle retrieval and posting
- Healthcare provider and organization lookup
- FHIR resource validation and conversion
- Audit logging for healthcare data access

Azure FHIR Service Details:
- Base URL: https://healtthdata-dev-fhir-service.fhir.azurehealthcareapis.com
- FHIR Version: R4
- Location: West Europe
- Authentication: Azure AD OAuth2
"""

import requests
import json
import logging
import subprocess
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from django.conf import settings
from django.core.cache import cache
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger("ehealth")
audit_logger = logging.getLogger("audit")


class AzureFHIRIntegrationService:
    """Service for integrating with Azure Healthcare APIs FHIR R4 service"""
    
    def __init__(self):
        # Azure FHIR server configuration from environment variables
        self.base_url = os.getenv('AZURE_FHIR_BASE_URL', '')
        self.tenant_id = os.getenv('AZURE_FHIR_TENANT_ID', '')
        self.audience = os.getenv('AZURE_FHIR_BASE_URL', '')
        self.timeout = 30
        self.cache_timeout = 300  # 5 minutes
        self._access_token = None
        self._token_expires_at = None
        
        # Validate configuration
        if not self.base_url or not self.tenant_id:
            raise ValueError(
                "Azure FHIR configuration missing. Please set AZURE_FHIR_BASE_URL "
                "and AZURE_FHIR_TENANT_ID in your .env file."
            )
        
    def _get_access_token(self) -> str:
        """Get Azure AD access token for FHIR API"""
        # Check if we have a cached valid token
        if self._access_token and self._token_expires_at:
            if datetime.now(timezone.utc) < self._token_expires_at:
                return self._access_token
        
        try:
            # Use Azure CLI to get token - check common installation paths
            az_cmd = 'az'
            possible_paths = [
                r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd",
                r"C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin\az.cmd",
                'az'  # Fallback to PATH
            ]
            
            for path in possible_paths:
                if os.path.exists(path) or path == 'az':
                    az_cmd = path
                    break
            
            cmd = [
                az_cmd, 'account', 'get-access-token',
                '--resource', self.audience,
                '--query', 'accessToken',
                '--output', 'tsv'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, shell=True)
            
            if result.returncode == 0:
                self._access_token = result.stdout.strip()
                # Tokens typically valid for 1 hour
                from datetime import timedelta
                self._token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
                
                logger.info(f"Azure AD token acquired for FHIR service")
                return self._access_token
            else:
                error_msg = f"Failed to get Azure token: {result.stderr}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except FileNotFoundError:
            error_msg = "Azure CLI not found. Please install Azure CLI and run 'az login'"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"Error getting Azure token: {e}")
            raise
    
    def _get_headers(self) -> Dict[str, str]:
        """Get standard headers for Azure FHIR API requests including auth token"""
        token = self._get_access_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/fhir+json',
            'Content-Type': 'application/fhir+json',
            'User-Agent': 'Django-NCP/1.0'
        }
        return headers
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make request to Azure FHIR server"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}" if endpoint else self.base_url
        
        try:
            headers = self._get_headers()
            
            logger.info(f"Azure FHIR API {method} {url}")
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, params=params, timeout=self.timeout)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=headers, params=params, timeout=self.timeout)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Log response
            logger.info(f"Azure FHIR API response: {response.status_code}")
            
            if response.status_code in [200, 201]:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Azure FHIR resource not found: {url}")
                return None
            else:
                error_msg = f"Azure FHIR API error: {response.status_code} - {response.text[:200]}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except requests.exceptions.Timeout:
            error_msg = f"Azure FHIR API request timeout: {url}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"Azure FHIR API request failed: {e}")
            raise
    
    def get_patient_summary(self, patient_id: str, requesting_user: str) -> Dict[str, Any]:
        """
        Get patient summary from Azure FHIR server
        
        Args:
            patient_id: FHIR Patient resource ID
            requesting_user: Username of user making request (for audit)
            
        Returns:
            FHIR Bundle containing patient summary
        """
        audit_logger.info(
            f"FHIR patient summary requested by {requesting_user} for patient {patient_id}",
            extra={'user': requesting_user, 'patient_id': patient_id, 'action': 'fhir_patient_summary'}
        )
        
        # Try $summary operation first
        try:
            logger.info(f"Attempting $summary operation for patient {patient_id}")
            bundle = self._make_request('GET', f"Patient/{patient_id}/$summary")
            if bundle:
                logger.info(f"$summary operation successful for patient {patient_id}")
                return bundle
        except Exception as e:
            logger.warning(f"$summary operation not available for patient {patient_id}, assembling manually: {e}")
        
        # Manually assemble patient summary bundle
        return self._assemble_patient_summary(patient_id)
    
    def search_patients(self, search_params: Dict[str, str]) -> Dict[str, Any]:
        """
        Search for patients in Azure FHIR server
        
        Args:
            search_params: Dictionary containing search criteria (identifier, name, birthdate, gender)
            
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
            
            fhir_params['_count'] = search_params.get('limit', '20')
            
            search_results = self._make_request('GET', 'Patient', params=fhir_params)
            
            if not search_results:
                return {'total': 0, 'patients': [], 'search_parameters': search_params}
            
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
            
            audit_logger.info(f"Patient search in Azure FHIR: params={search_params}, results={len(patients)}")
            return result
            
        except Exception as e:
            logger.error(f"Patient search in Azure FHIR failed: {str(e)}")
            raise Exception(f"Patient search failed: {str(e)}")
    
    def search_patient_documents(self, patient_id: str) -> Dict[str, Any]:
        """
        Search for patient documents (Compositions) in Azure FHIR server
        
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
            
            if not search_results:
                return {'total': 0, 'documents': [], 'patient_id': patient_id}
            
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
            
            audit_logger.info(f"Patient document search in Azure FHIR: patient_id={patient_id}, results={len(documents)}")
            return result
            
        except Exception as e:
            logger.error(f"Patient document search in Azure FHIR failed: {str(e)}")
            raise Exception(f"Patient document search failed: {str(e)}")
    
    def _extract_patient_info(self, patient_resource: Dict[str, Any]) -> Dict[str, Any]:
        """Extract patient information from FHIR Patient resource"""
        info = {
            'id': patient_resource.get('id'),
            'identifier': [],
            'name': [],
            'birthDate': patient_resource.get('birthDate'),
            'gender': patient_resource.get('gender'),
            'address': patient_resource.get('address', [])
        }
        
        # Extract identifiers
        for identifier in patient_resource.get('identifier', []):
            info['identifier'].append({
                'system': identifier.get('system'),
                'value': identifier.get('value')
            })
        
        # Extract names
        for name in patient_resource.get('name', []):
            info['name'].append({
                'given': name.get('given', []),
                'family': name.get('family')
            })
        
        return info
    
    def _extract_composition_info(self, composition_resource: Dict[str, Any]) -> Dict[str, Any]:
        """Extract composition information from FHIR Composition resource"""
        return {
            'id': composition_resource.get('id'),
            'status': composition_resource.get('status'),
            'type': composition_resource.get('type', {}).get('coding', [{}])[0].get('display', 'Unknown'),
            'date': composition_resource.get('date'),
            'title': composition_resource.get('title'),
            'author': composition_resource.get('author', [])
        }
    
    def _filter_latest_versions(self, entries: List[Dict], resource_type: str) -> List[Dict]:
        """
        Filter to get only the latest version of each unique resource
        
        Groups resources by their clinical signature and keeps only the version
        with the highest versionId and most recent lastUpdated timestamp.
        
        For MedicationStatement: groups by ATC code
        For AllergyIntolerance: groups by allergen code
        For Condition: groups by condition code
        For others: groups by resource content signature
        """
        if not entries:
            return entries
        
        # Group resources by their clinical identifier
        resource_groups = {}
        
        for entry in entries:
            resource = entry.get('resource', {})
            
            # Create a signature to identify clinically equivalent resources
            signature = self._create_resource_signature(resource, resource_type)
            
            if signature not in resource_groups:
                resource_groups[signature] = []
            
            resource_groups[signature].append(entry)
        
        # For each group, keep only the latest version
        latest_entries = []
        
        for signature, group in resource_groups.items():
            if len(group) == 1:
                # Only one version, keep it
                latest_entries.append(group[0])
            else:
                # Multiple versions - find the latest
                latest = self._get_latest_version(group)
                latest_entries.append(latest)
                
                # Log version filtering
                resource_type_name = group[0].get('resource', {}).get('resourceType', 'Unknown')
                logger.info(f"Filtered {len(group)} versions of {resource_type_name} (signature: {signature[:30]}...) - kept latest version {latest.get('resource', {}).get('meta', {}).get('versionId', 'N/A')}")
        
        return latest_entries
    
    def _create_resource_signature(self, resource: Dict[str, Any], resource_type: str) -> str:
        """
        Create a signature to identify clinically equivalent resources
        
        Uses the same logic as HAPI FHIR deduplication for consistency
        """
        if resource_type == 'MedicationStatement':
            # Use ATC code as signature
            if resource.get('medicationCodeableConcept', {}).get('coding'):
                code = resource['medicationCodeableConcept']['coding'][0].get('code', '')
                system = resource['medicationCodeableConcept']['coding'][0].get('system', '')
                if code:
                    return f"{system}|{code}"
        
        elif resource_type == 'AllergyIntolerance':
            # Use allergen code
            if resource.get('code', {}).get('coding'):
                code = resource['code']['coding'][0].get('code', '')
                system = resource['code']['coding'][0].get('system', '')
                if code:
                    return f"{system}|{code}"
        
        elif resource_type == 'Condition':
            # Use condition code
            if resource.get('code', {}).get('coding'):
                code = resource['code']['coding'][0].get('code', '')
                system = resource['code']['coding'][0].get('system', '')
                if code:
                    return f"{system}|{code}"
        
        elif resource_type == 'Procedure':
            # Use procedure code
            if resource.get('code', {}).get('coding'):
                code = resource['code']['coding'][0].get('code', '')
                system = resource['code']['coding'][0].get('system', '')
                if code:
                    return f"{system}|{code}"
        
        elif resource_type == 'Immunization':
            # Use vaccine code
            if resource.get('vaccineCode', {}).get('coding'):
                code = resource['vaccineCode']['coding'][0].get('code', '')
                system = resource['vaccineCode']['coding'][0].get('system', '')
                if code:
                    return f"{system}|{code}"
        
        elif resource_type == 'Observation':
            # Use observation code
            if resource.get('code', {}).get('coding'):
                code = resource['code']['coding'][0].get('code', '')
                system = resource['code']['coding'][0].get('system', '')
                if code:
                    return f"{system}|{code}"
        
        # Fallback: use resource ID
        return resource.get('id', 'unknown')
    
    def _get_latest_version(self, entries: List[Dict]) -> Dict:
        """
        Get the latest version from a group of resource entries
        
        Prioritizes by:
        1. Highest versionId (numeric comparison)
        2. Most recent lastUpdated timestamp
        3. First in list (fallback)
        """
        if not entries:
            return None
        
        if len(entries) == 1:
            return entries[0]
        
        # Sort by versionId (descending) then lastUpdated (descending)
        def sort_key(entry):
            resource = entry.get('resource', {})
            meta = resource.get('meta', {})
            
            # Get versionId as integer (default to 0)
            version_id = 0
            try:
                version_id = int(meta.get('versionId', '0'))
            except (ValueError, TypeError):
                version_id = 0
            
            # Get lastUpdated timestamp (default to empty string for sorting)
            last_updated = meta.get('lastUpdated', '')
            
            # Return tuple for sorting: higher version and more recent timestamp first
            # Use negative values so higher versions/newer dates sort first
            return (-version_id, -ord(last_updated[0]) if last_updated else 0)
        
        sorted_entries = sorted(entries, key=sort_key)
        
        latest = sorted_entries[0]
        latest_meta = latest.get('resource', {}).get('meta', {})
        
        logger.debug(f"Selected version {latest_meta.get('versionId', 'N/A')} from {len(entries)} versions (lastUpdated: {latest_meta.get('lastUpdated', 'N/A')})")
        
        return latest
    
    def _assemble_patient_summary(self, patient_id: str) -> Dict[str, Any]:
        """Manually assemble patient summary bundle by fetching individual resources"""
        logger.info(f"Assembling patient summary manually for patient {patient_id}")
        
        try:
            bundle_entries = []
            
            # 1. Get Patient resource
            try:
                patient = self._make_request('GET', f"Patient/{patient_id}")
                if patient:
                    bundle_entries.append({'resource': patient})
            except Exception:
                logger.warning(f"Patient {patient_id} not found in Azure FHIR server")
                patient = {
                    'resourceType': 'Patient',
                    'id': patient_id,
                    'name': [{'family': 'Unknown', 'given': ['Patient']}],
                    'birthDate': '1980-01-01',
                    'gender': 'unknown'
                }
                bundle_entries.append({'resource': patient})
            
            # 2. Get Composition resource
            try:
                search_params = {'subject': f"Patient/{patient_id}", '_count': '10'}
                composition_results = self._make_request('GET', 'Composition', params=search_params)
                
                if composition_results and composition_results.get('entry'):
                    # Take only latest composition
                    composition_entries = composition_results['entry']
                    sorted_compositions = sorted(
                        composition_entries,
                        key=lambda e: e.get('resource', {}).get('date', ''),
                        reverse=True
                    )
                    
                    if sorted_compositions:
                        latest_composition = sorted_compositions[0]
                        bundle_entries.append({'resource': latest_composition['resource']})
                        logger.info(f"Added latest Composition to bundle")
                        
            except Exception:
                logger.debug(f"No Composition resources found for patient {patient_id}")
            
            # 3. Get clinical resources
            clinical_resources = [
                'AllergyIntolerance',
                'MedicationStatement', 
                'Condition',
                'Observation',
                'Procedure',
                'Immunization'
            ]
            
            medication_references = set()  # Track Medication references to fetch
            
            for resource_type in clinical_resources:
                try:
                    search_params = {
                        'patient': patient_id,
                        '_sort': '-_lastUpdated',
                        '_count': '100'  # Get more to ensure we capture all versions
                    }
                    search_results = self._make_request('GET', resource_type, params=search_params)
                    
                    if search_results and search_results.get('entry'):
                        entries = search_results['entry']
                        
                        # Filter to get only latest version of each resource
                        entries = self._filter_latest_versions(entries, resource_type)
                        
                        # Deduplicate resources (by clinical signature)
                        from eu_ncp_server.services.fhir_integration import HAPIFHIRIntegrationService
                        hapi_service = HAPIFHIRIntegrationService()
                        deduplicated_entries = hapi_service._deduplicate_clinical_resources(entries, resource_type)
                        
                        for entry in deduplicated_entries:
                            resource = entry['resource']
                            bundle_entries.append({'resource': resource})
                            
                            # Extract Medication references from MedicationStatements
                            if resource_type == 'MedicationStatement' and resource.get('medicationReference'):
                                med_ref = resource['medicationReference'].get('reference', '')
                                if med_ref:
                                    # Extract Medication ID (e.g., "Medication/123" -> "123")
                                    med_id = med_ref.split('/')[-1] if '/' in med_ref else med_ref
                                    medication_references.add(med_id)
                            
                except Exception:
                    logger.debug(f"No {resource_type} resources found for patient {patient_id}")
                    continue
            
            # 4. Fetch referenced Medication resources
            if medication_references:
                logger.info(f"Fetching {len(medication_references)} referenced Medication resources")
                for med_id in medication_references:
                    try:
                        medication = self._make_request('GET', f"Medication/{med_id}")
                        if medication:
                            bundle_entries.append({'resource': medication})
                            logger.debug(f"Added Medication resource: {med_id}")
                    except Exception as e:
                        logger.warning(f"Could not fetch Medication {med_id}: {e}")
                        continue
            
            # 5. Create Patient Summary Bundle
            summary_bundle = {
                'resourceType': 'Bundle',
                'id': f'patient-summary-{patient_id}',
                'type': 'document',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'total': len(bundle_entries),
                'entry': bundle_entries,
                'meta': {
                    'source': 'Azure FHIR Service',
                    'assembled_by': 'Django NCP',
                    'assembly_timestamp': datetime.now(timezone.utc).isoformat()
                }
            }
            
            logger.info(f"Assembled patient summary bundle with {len(bundle_entries)} resources")
            return summary_bundle
            
        except Exception as e:
            logger.error(f"Error assembling Patient Summary for {patient_id}: {str(e)}")
            raise Exception(f"Patient Summary assembly failed: {str(e)}")
