"""
Delete the incorrect termination observation from Azure FHIR
Observation ID: e2fb0492-a18d-4616-a9a1-1d9d5ea1fedd
Date: 2022-06-08 (incorrect - should not exist)
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from eu_ncp_server.services.fhir_service_factory import get_fhir_service

def main():
    print("\n=== DELETE INCORRECT TERMINATION OBSERVATION ===\n")
    
    # Initialize service
    fhir_service = get_fhir_service()
    
    # Observation to delete
    observation_id = "e2fb0492-a18d-4616-a9a1-1d9d5ea1fedd"
    
    print(f"Target Observation ID: {observation_id}")
    print(f"  SNOMED Code: 57797005 (Termination of pregnancy)")
    print(f"  Incorrect Date: 2022-06-08T10:49:00Z")
    print(f"\nThis is the observation with the WRONG date.")
    print(f"The CORRECT termination observation is 80b52ff5 (2010-07-03)\n")
    
    # Confirm deletion
    confirm = input("Delete this observation? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("\n❌ Deletion cancelled.")
        return
    
    try:
        # Delete the observation
        print(f"\nDeleting observation {observation_id}...")
        
        response = fhir_service._make_request(
            method='DELETE',
            endpoint=f"Observation/{observation_id}"
        )
        
        print(f"✅ Successfully deleted observation {observation_id}")
        print("\nAfter deletion, you should have:")
        print("  - 1 Current pregnancy (2022-06-15)")
        print("  - 3 Past pregnancies:")
        print("    • Livebirth (2021-09-08)")
        print("    • Livebirth (2020-02-05)")
        print("    • Termination (2010-07-03) ✓")
        print("\nPlease:")
        print("  1. Clear cache: python clear_cache.py")
        print("  2. Clear sessions: python force_clear_sessions.py")
        print("  3. Restart Django server")
        print("  4. Search for patient again")
        
    except Exception as e:
        print(f"\n❌ Error deleting observation: {e}")

if __name__ == '__main__':
    main()
