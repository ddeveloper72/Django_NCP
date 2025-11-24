"""
Find Organization by Name in Azure FHIR
========================================

Searches for organizations by name and displays their IDs.

Usage:
    python find_organization.py <organization_name>
    
Example:
    python find_organization.py "Centro Hospitalar de Lisboa Central"
"""

import os
import sys
import json
import subprocess
import requests
from dotenv import load_dotenv

load_dotenv()


class OrganizationFinder:
    """Find organizations in Azure FHIR"""
    
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
    
    def _query(self, endpoint: str, params: dict = None) -> dict:
        """Make GET request to Azure FHIR"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            'Authorization': f'Bearer {self._get_access_token()}',
            'Accept': 'application/fhir+json'
        }
        
        print(f"\n🔍 Query: GET {url}")
        if params:
            print(f"   Params: {params}")
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error {response.status_code}: {response.text[:200]}")
            return None
    
    def find_organizations(self, org_name: str):
        """Search for organizations by name"""
        
        print("=" * 80)
        print(f"FIND ORGANIZATIONS BY NAME")
        print(f"Search: {org_name}")
        print("=" * 80)
        
        # Search by name
        results = self._query('Organization', {'name': org_name})
        
        if not results or not results.get('entry'):
            print(f"\n❌ No organizations found matching: {org_name}")
            
            # Try partial match
            print(f"\n🔄 Trying partial name search...")
            results = self._query('Organization', {'name:contains': org_name.split()[0]})
            
            if not results or not results.get('entry'):
                print(f"❌ No organizations found with partial match")
                return
        
        entries = results.get('entry', [])
        print(f"\n✅ Found {len(entries)} organization(s):\n")
        
        for idx, entry in enumerate(entries, 1):
            org = entry.get('resource', {})
            org_id = org.get('id')
            org_name_found = org.get('name', 'N/A')
            active = org.get('active', 'N/A')
            
            print(f"{idx}. {org_name_found}")
            print(f"   ID: {org_id}")
            print(f"   Active: {active}")
            
            # Check for telecom
            telecoms = org.get('telecom', [])
            print(f"   Telecom: {len(telecoms)} item(s)")
            if telecoms:
                for telecom in telecoms[:2]:  # Show first 2
                    print(f"      - {telecom.get('system', 'N/A')}: {telecom.get('value', 'N/A')}")
            
            # Check for address
            addresses = org.get('address', [])
            print(f"   Address: {len(addresses)} item(s)")
            if addresses:
                addr = addresses[0]
                city = addr.get('city', 'N/A')
                country = addr.get('country', 'N/A')
                print(f"      - {city}, {country}")
            
            print()
        
        print("=" * 80)
        print("To inspect a specific organization, run:")
        print(f"  python inspect_organization.py <organization_id>")
        print("=" * 80)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python find_organization.py <organization_name>")
        print("\nExample:")
        print('  python find_organization.py "Centro Hospitalar de Lisboa Central"')
        sys.exit(1)
    
    org_name = ' '.join(sys.argv[1:])
    
    try:
        finder = OrganizationFinder()
        finder.find_organizations(org_name)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
