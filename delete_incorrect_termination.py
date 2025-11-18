"""
Delete the incorrect termination observation (2022-06-08) from Azure FHIR
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from eu_ncp_server.services.fhir_service_factory import get_fhir_service

def main():
    print("\n=== DELETING INCORRECT TERMINATION OBSERVATION ===\n")
    
    fhir_service = get_fhir_service()
    
    # The incorrect observation ID
    observation_id = "e2fb0492-a18d-4616-a9a1-1d9d5ea1fedd"
    
    print(f"Observation to delete: {observation_id}")
    print(f"  Code: 57797005 (Termination of pregnancy)")
    print(f"  Date: 2022-06-08 (INCORRECT)")
    print(f"\nThis observation has the wrong date. The correct termination is on 2010-07-03.")
    
    response = input("\nDo you want to delete this observation? (yes/no): ")
    
    if response.lower() != 'yes':
        print("Operation cancelled.")
        return
    
    try:
        # Delete the observation
        result = fhir_service._make_request(
            method='DELETE',
            endpoint=f"Observation/{observation_id}"
        )
        
        print(f"\n✅ Observation {observation_id} deleted successfully!")
        print("\nNow you should have:")
        print("  - 1 Termination of pregnancy (2010-07-03)")
        print("  - 2 Livebirths (2021-09-08, 2020-02-05)")
        print("\nPlease:")
        print("  1. Clear cache: python clear_cache.py")
        print("  2. Clear sessions: python force_clear_sessions.py")
        print("  3. Restart Django server")
        print("  4. Log in and search for patient again")
        
    except Exception as e:
        print(f"\n❌ Error deleting observation: {e}")

if __name__ == '__main__':
    main()
