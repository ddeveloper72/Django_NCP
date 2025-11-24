"""
Inspect Organization Resource from Azure FHIR
==============================================

Fetches and displays detailed Organization resource information from Azure FHIR
to verify if telecom and address fields are present.

Usage:
    python inspect_organization.py <organization_id>
    
Example:
    python inspect_organization.py 9271d58e-799e-4756-98db-9bfb1b2d6aeb
"""

import os
import sys
import json
import subprocess
import requests
from dotenv import load_dotenv

load_dotenv()


class OrganizationInspector:
    """Inspect Organization resources in Azure FHIR"""
    
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
    
    def _query(self, endpoint: str) -> dict:
        """Make GET request to Azure FHIR"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            'Authorization': f'Bearer {self._get_access_token()}',
            'Accept': 'application/fhir+json'
        }
        
        print(f"\n🔍 Query: GET {url}")
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            print(f"❌ Not found: {url}")
            return None
        else:
            print(f"❌ Error {response.status_code}: {response.text[:200]}")
            return None
    
    def inspect_organization(self, org_id: str):
        """Fetch and inspect organization resource"""
        
        print("=" * 80)
        print(f"AZURE FHIR ORGANIZATION INSPECTION")
        print(f"Organization ID: {org_id}")
        print("=" * 80)
        
        # Fetch organization
        organization = self._query(f'Organization/{org_id}')
        
        if not organization:
            print(f"❌ Organization not found: {org_id}")
            return
        
        print(f"\n✅ Found Organization:")
        print(f"   - ID: {organization.get('id')}")
        print(f"   - Name: {organization.get('name', 'N/A')}")
        print(f"   - Active: {organization.get('active', 'N/A')}")
        
        # Check meta
        meta = organization.get('meta', {})
        print(f"   - Version: {meta.get('versionId', 'N/A')}")
        print(f"   - Last Updated: {meta.get('lastUpdated', 'N/A')}")
        
        # Check identifiers
        identifiers = organization.get('identifier', [])
        print(f"\n🆔 Identifiers ({len(identifiers)}):")
        if identifiers:
            for idx, identifier in enumerate(identifiers, 1):
                print(f"   {idx}. System: {identifier.get('system', 'N/A')}")
                print(f"      Value: {identifier.get('value', 'N/A')}")
                print(f"      Use: {identifier.get('use', 'N/A')}")
        else:
            print("   ⚠️  No identifiers found")
        
        # Check telecom (CRITICAL)
        telecoms = organization.get('telecom', [])
        print(f"\n📞 Telecom ({len(telecoms)}):")
        if telecoms:
            for idx, telecom in enumerate(telecoms, 1):
                print(f"   {idx}. System: {telecom.get('system', 'N/A')}")
                print(f"      Value: {telecom.get('value', 'N/A')}")
                print(f"      Use: {telecom.get('use', 'N/A')}")
        else:
            print("   ❌ NO TELECOM FOUND - This is why contact details aren't showing!")
        
        # Check address (CRITICAL)
        addresses = organization.get('address', [])
        print(f"\n📍 Address ({len(addresses)}):")
        if addresses:
            for idx, address in enumerate(addresses, 1):
                print(f"   {idx}. Use: {address.get('use', 'N/A')}")
                print(f"      Type: {address.get('type', 'N/A')}")
                if address.get('line'):
                    print(f"      Lines: {', '.join(address['line'])}")
                print(f"      City: {address.get('city', 'N/A')}")
                print(f"      State: {address.get('state', 'N/A')}")
                print(f"      Postal Code: {address.get('postalCode', 'N/A')}")
                print(f"      Country: {address.get('country', 'N/A')}")
        else:
            print("   ❌ NO ADDRESS FOUND - This is why address details aren't showing!")
        
        # Check type
        org_types = organization.get('type', [])
        print(f"\n🏥 Organization Type ({len(org_types)}):")
        if org_types:
            for idx, org_type in enumerate(org_types, 1):
                print(f"   {idx}. Text: {org_type.get('text', 'N/A')}")
                codings = org_type.get('coding', [])
                if codings:
                    for coding in codings:
                        print(f"      - System: {coding.get('system', 'N/A')}")
                        print(f"        Code: {coding.get('code', 'N/A')}")
                        print(f"        Display: {coding.get('display', 'N/A')}")
        else:
            print("   ⚠️  No type specified")
        
        # Check contact (administrative contacts)
        contacts = organization.get('contact', [])
        print(f"\n👤 Organization Contact ({len(contacts)}):")
        if contacts:
            for idx, contact in enumerate(contacts, 1):
                print(f"   {idx}. Purpose: {contact.get('purpose', {}).get('text', 'N/A')}")
                
                # Contact name
                name = contact.get('name', {})
                if name:
                    print(f"      Name: {name.get('text', 'N/A')}")
                
                # Contact telecom
                contact_telecoms = contact.get('telecom', [])
                if contact_telecoms:
                    print(f"      Telecom:")
                    for telecom in contact_telecoms:
                        print(f"         - {telecom.get('system', 'N/A')}: {telecom.get('value', 'N/A')}")
                
                # Contact address
                contact_address = contact.get('address', {})
                if contact_address:
                    print(f"      Address:")
                    if contact_address.get('line'):
                        print(f"         Lines: {', '.join(contact_address['line'])}")
                    print(f"         City: {contact_address.get('city', 'N/A')}")
        else:
            print("   ⚠️  No contact information found")
        
        # Check partOf
        part_of = organization.get('partOf', {})
        if part_of:
            print(f"\n🔗 Part Of:")
            print(f"   Reference: {part_of.get('reference', 'N/A')}")
            print(f"   Display: {part_of.get('display', 'N/A')}")
        
        # Summary
        print("\n" + "=" * 80)
        print("DIAGNOSIS")
        print("=" * 80)
        
        has_telecom = len(telecoms) > 0
        has_address = len(addresses) > 0
        has_contact = len(contacts) > 0
        
        if has_telecom and has_address:
            print("✅ Organization has both telecom and address - should display in UI")
        else:
            print("❌ ISSUE FOUND:")
            if not has_telecom:
                print("   - Organization missing 'telecom' field")
                print("   - This is why phone/email/website aren't showing in UI")
            if not has_address:
                print("   - Organization missing 'address' field")
                print("   - This is why organization address isn't showing in UI")
            
            if has_contact:
                print("\n💡 SOLUTION:")
                print("   - Organization has 'contact' array with nested telecom/address")
                print("   - Parser needs to check BOTH organization.telecom AND organization.contact[].telecom")
                print("   - Similarly for addresses")
            else:
                print("\n💡 SOLUTION:")
                print("   - Update Organization resource in Azure FHIR to include:")
                print("     1. organization.telecom[] array")
                print("     2. organization.address[] array")
        
        # Save full JSON
        output_file = f"organization_{org_id}_full.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(organization, f, indent=2)
        print(f"\n💾 Full Organization resource saved to: {output_file}")
        
        print("\n" + "=" * 80)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python inspect_organization.py <organization_id>")
        print("\nExample:")
        print("  python inspect_organization.py 9271d58e-799e-4756-98db-9bfb1b2d6aeb")
        print("\nTo find Organization IDs:")
        print("  python verify_composition_references.py <patient_identifier>")
        sys.exit(1)
    
    org_id = sys.argv[1]
    
    try:
        inspector = OrganizationInspector()
        inspector.inspect_organization(org_id)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
