import os
import sys
import django

# Setup Django
project_root = os.path.dirname(os.path.abspath('.'))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from patient_data.services import EUPatientSearchService, PatientCredentials

# Create credentials for Diana Ferreira
credentials = PatientCredentials(
    country_code="PT",
    patient_id="2-1234-W7"
)
credentials.given_name = "Diana"
credentials.family_name = "Ferreira"
credentials.birth_date = "1982-05-08"

print("CREATING FRESH DIANA SESSION")
print("=" * 40)

# Perform search to create session data
search_service = EUPatientSearchService()
search_result = search_service.search_patient(credentials)

if search_result:
    print(f"✅ Search successful! Found {len(search_result)} results")
    
    # Use the first result
    first_result = search_result[0] if isinstance(search_result, list) else search_result
    print(f"   ✅ Session created successfully!")
    
    # Test the clinical data extraction
    from patient_data.services.comprehensive_clinical_data_service import ComprehensiveClinicalDataService
    
    service = ComprehensiveClinicalDataService()
    clinical_arrays = service.get_clinical_arrays_for_display(first_result.cda_content)
    
    print(f"\n📊 CLINICAL DATA EXTRACTED:")
    print(f"   Medications: {len(clinical_arrays['medications'])}")
    print(f"   Allergies: {len(clinical_arrays['allergies'])}")
    print(f"   Problems: {len(clinical_arrays['problems'])}")
    
    if clinical_arrays['medications']:
        print(f"\n💊 MEDICATIONS:")
        for i, med in enumerate(clinical_arrays['medications'], 1):
            name = med.get('medication_name') or med.get('name') or med.get('display_name', 'Unknown')
            dose = med.get('data', {}).get('dose_quantity', 'No dose')
            route = med.get('data', {}).get('route_display', 'No route')
            print(f"   {i}. {name} - {dose} ({route})")
    
    print(f"\n🔗 Now you can access Diana at: http://localhost:8000/patients/2-1234-W7/")
    
else:
    print("❌ Search failed - no results found")