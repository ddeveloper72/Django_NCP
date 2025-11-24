"""
Add Custodian Organization to Composition
==========================================

Updates a Composition in Azure FHIR to add a custodian organization reference.

This script:
1. Fetches the current Composition
2. Checks if Organization exists (or creates one)
3. Updates Composition.custodian with Organization reference
4. Posts the updated Composition back to Azure FHIR

Usage:
    python add_composition_custodian.py <composition_id> <organization_name>
    
Example:
    python add_composition_custodian.py 78f27b51-7da0-4249-aaf8-ba7d43fdf18f "Hospital Central"
"""

import os
import sys
import json
import subprocess
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class CompositionCustodianUpdater:
    """Update Composition with custodian organization"""
    
    def __init__(self):
        self.base_url = os.getenv('AZURE_FHIR_BASE_URL', '')
        self.tenant_id = os.getenv('AZURE_FHIR_TENANT_ID', '')
        self.client_id = os.getenv('AZURE_FHIR_CLIENT_ID', '')
        self.client_secret = os.getenv('AZURE_FHIR_CLIENT_SECRET', '')
        
        if not self.base_url or not self.tenant_id:
            raise ValueError("Missing Azure FHIR configuration")
        
        self._access_token = None
    
    def _get_access_token(self) -> str:
        """Get Azure AD access token"""
        if self._access_token:
            return self._access_token
        
        if self.client_id and self.client_secret:
            try:
                token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
                data = {
                    'grant_type': 'client_credentials',
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'scope': f'{self.base_url}/.default'
                }
                response = requests.post(token_url, data=data)
                response.raise_for_status()
                self._access_token = response.json()['access_token']
                print("✅ Authenticated via Service Principal")
                return self._access_token
            except Exception as e:
                print(f"⚠️  Service Principal auth failed: {e}")
        
        try:
            result = subprocess.run(
                ['az', 'account', 'get-access-token', '--resource', self.base_url],
                capture_output=True,
                text=True,
                check=True
            )
            token_data = json.loads(result.stdout)
            self._access_token = token_data['accessToken']
            print("✅ Authenticated via Azure CLI")
            return self._access_token
        except Exception as e:
            raise Exception(f"Auth failed: {e}")
    
    def _request(self, method: str, endpoint: str, data: dict = None, params: dict = None) -> dict:
        """Make request to Azure FHIR"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            'Authorization': f'Bearer {self._get_access_token()}',
            'Accept': 'application/fhir+json',
            'Content-Type': 'application/fhir+json'
        }
        
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params, timeout=30)
        elif method == 'PUT':
            response = requests.put(url, json=data, headers=headers, timeout=30)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        if response.status_code in [200, 201]:
            return response.json()
        elif response.status_code == 404:
            return None
        else:
            raise Exception(f"Error {response.status_code}: {response.text[:200]}")
    
    def find_or_create_organization(self, org_name: str) -> str:
        """Find existing organization or create new one"""
        print(f"\n📌 Finding Organization: {org_name}")
        
        # Search for existing organization
        search_results = self._request('GET', 'Organization', params={'name': org_name})
        
        if search_results and search_results.get('entry'):
            org = search_results['entry'][0]['resource']
            org_id = org.get('id')
            print(f"✅ Found existing Organization: {org_id}")
            return org_id
        
        # Create new organization
        print(f"⚠️  Organization not found, creating new one...")
        
        new_org = {
            'resourceType': 'Organization',
            'name': org_name,
            'active': True,
            'type': [
                {
                    'coding': [
                        {
                            'system': 'http://terminology.hl7.org/CodeSystem/organization-type',
                            'code': 'prov',
                            'display': 'Healthcare Provider'
                        }
                    ]
                }
            ]
        }
        
        created_org = self._request('POST', 'Organization', data=new_org)
        org_id = created_org.get('id')
        print(f"✅ Created Organization: {org_id}")
        
        return org_id
    
    def update_composition_custodian(self, composition_id: str, org_name: str):
        """Update composition with custodian organization"""
        print("=" * 80)
        print("ADD CUSTODIAN TO COMPOSITION")
        print(f"Composition ID: {composition_id}")
        print(f"Organization: {org_name}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("=" * 80)
        
        # Step 1: Fetch current composition
        print(f"\n📌 Fetching Composition: {composition_id}")
        composition = self._request('GET', f'Composition/{composition_id}')
        
        if not composition:
            print(f"❌ Composition not found: {composition_id}")
            return
        
        print(f"✅ Found Composition:")
        print(f"   - Version: {composition.get('meta', {}).get('versionId', 'N/A')}")
        print(f"   - Title: {composition.get('title', 'N/A')}")
        print(f"   - Current Custodian: {composition.get('custodian', {}).get('reference', 'None')}")
        
        # Step 2: Find or create organization
        org_id = self.find_or_create_organization(org_name)
        
        # Step 3: Update composition
        print(f"\n📌 Updating Composition with custodian reference")
        
        # Add custodian reference
        composition['custodian'] = {
            'reference': f'Organization/{org_id}',
            'display': org_name
        }
        
        # Update composition in Azure FHIR
        updated_composition = self._request('PUT', f'Composition/{composition_id}', data=composition)
        
        print(f"✅ Composition updated successfully!")
        print(f"   - New Version: {updated_composition.get('meta', {}).get('versionId', 'N/A')}")
        print(f"   - Custodian: Organization/{org_id}")
        
        # Verify
        print(f"\n📌 Verifying update...")
        verify_comp = self._request('GET', f'Composition/{composition_id}')
        
        if verify_comp.get('custodian', {}).get('reference') == f'Organization/{org_id}':
            print("✅ Verification successful - custodian reference confirmed")
        else:
            print("❌ Verification failed - custodian reference not found")
        
        print("\n" + "=" * 80)
        print("COMPLETE")
        print("=" * 80)
        print(f"✅ Composition {composition_id} now has custodian Organization/{org_id}")
        print(f"✅ Django NCP will now retrieve this organization in patient summaries")


def main():
    """Main entry point"""
    if len(sys.argv) < 3:
        print("Usage: python add_composition_custodian.py <composition_id> <organization_name>")
        print("\nExample:")
        print('  python add_composition_custodian.py 78f27b51-7da0-4249-aaf8-ba7d43fdf18f "Hospital Central"')
        sys.exit(1)
    
    composition_id = sys.argv[1]
    org_name = ' '.join(sys.argv[2:])  # Support multi-word names
    
    try:
        updater = CompositionCustodianUpdater()
        updater.update_composition_custodian(composition_id, org_name)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
