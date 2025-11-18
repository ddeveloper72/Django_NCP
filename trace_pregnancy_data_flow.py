"""
BAP (Break All Points) Analysis - Trace complete pregnancy data flow
from FHIR bundle → Parser → View → Template
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from patient_data.models import PatientSession
from patient_data.services.azure_fhir_integration_service import AzureFHIRIntegrationService
from patient_data.services.fhir_bundle_parser import FHIRBundleParser
import json

print("=" * 80)
print("PREGNANCY DATA FLOW ANALYSIS")
print("=" * 80)

patient_id = "2-1234-W7"

# ============================================================================
# CHECKPOINT 1: Fetch FHIR Bundle from Azure
# ============================================================================
print("\n[CHECKPOINT 1] Fetching FHIR Bundle from Azure...")
azure_service = AzureFHIRIntegrationService()
fhir_bundle = azure_service.fetch_patient_summary_bundle(patient_id)

if not fhir_bundle:
    print("❌ No FHIR bundle returned from Azure")
    exit(1)

# Count pregnancy-related observations in raw bundle
pregnancy_obs_count = 0
for entry in fhir_bundle.get('entry', []):
    resource = entry.get('resource', {})
    if resource.get('resourceType') == 'Observation':
        code = resource.get('code', {})
        codings = code.get('coding', [])
        for coding in codings:
            # Check for pregnancy codes
            loinc_code = coding.get('code', '')
            if loinc_code in ['82810-3', '93857-1', '10162-6']:  # Pregnancy status, delivery date, history
                pregnancy_obs_count += 1
                break

print(f"✅ FHIR bundle fetched: {len(fhir_bundle.get('entry', []))} entries")
print(f"   Pregnancy-related observations in bundle: {pregnancy_obs_count}")

# ============================================================================
# CHECKPOINT 2: Parse Bundle with FHIRBundleParser
# ============================================================================
print("\n[CHECKPOINT 2] Parsing bundle with FHIRBundleParser...")
parser = FHIRBundleParser()
fhir_result = parser.parse_patient_summary_bundle(fhir_bundle)

if not fhir_result or not isinstance(fhir_result, dict):
    print("❌ Parser returned invalid result")
    exit(1)

print(f"✅ Parser result keys: {list(fhir_result.keys())}")

# Check clinical_arrays
if 'clinical_arrays' not in fhir_result:
    print("❌ No 'clinical_arrays' in parser result")
    exit(1)

clinical_arrays = fhir_result['clinical_arrays']
print(f"✅ clinical_arrays keys: {list(clinical_arrays.keys())}")

# Check pregnancy_history in clinical_arrays
if 'pregnancy_history' not in clinical_arrays:
    print("❌ No 'pregnancy_history' in clinical_arrays")
    exit(1)

pregnancy_history = clinical_arrays['pregnancy_history']
print(f"✅ pregnancy_history found: {len(pregnancy_history)} records")

# Display each pregnancy record
for i, preg in enumerate(pregnancy_history, 1):
    print(f"\n   Record {i}:")
    print(f"     pregnancy_type: {preg.get('pregnancy_type')}")
    print(f"     outcome: {preg.get('outcome')}")
    print(f"     outcome_code: {preg.get('outcome_code')}")
    print(f"     outcome_date: {preg.get('outcome_date')}")

# ============================================================================
# CHECKPOINT 3: Check Patient Session Storage
# ============================================================================
print("\n[CHECKPOINT 3] Checking patient session storage...")
sessions = PatientSession.objects.filter(patient_id=patient_id).order_by('-created_at')

if not sessions.exists():
    print("⚠️ No sessions found in database")
else:
    session = sessions.first()
    print(f"✅ Session found: {session.session_id}")
    print(f"   Created: {session.created_at}")
    
    if hasattr(session, 'clinical_data') and session.clinical_data:
        clinical_data = session.clinical_data
        print(f"   clinical_data keys: {list(clinical_data.keys())}")
        
        if 'pregnancy_history' in clinical_data:
            stored_preg = clinical_data['pregnancy_history']
            print(f"   ✅ pregnancy_history in session: {len(stored_preg)} records")
        else:
            print(f"   ❌ pregnancy_history NOT in session clinical_data")
    else:
        print(f"   ❌ No clinical_data in session")

# ============================================================================
# CHECKPOINT 4: Simulate View Context Building
# ============================================================================
print("\n[CHECKPOINT 4] Simulating view context building...")

# This is what views.py line 2741 does:
view_clinical_arrays = fhir_result.get('clinical_arrays', {})
view_pregnancy_history = view_clinical_arrays.get('pregnancy_history', [])

print(f"✅ View would extract {len(view_pregnancy_history)} pregnancy records")

# This is what views.py line 2872 does:
context_pregnancy_history = view_clinical_arrays.get("pregnancy_history", [])
print(f"✅ Context would receive {len(context_pregnancy_history)} pregnancy records")

# ============================================================================
# CHECKPOINT 5: Simulate Template Filter Processing
# ============================================================================
print("\n[CHECKPOINT 5] Simulating template filter processing...")

# Simulate selectattr_pregnancy_type_past filter
past_pregnancies = [
    item for item in context_pregnancy_history
    if isinstance(item, dict) and item.get('pregnancy_type') == 'past'
]
print(f"✅ Past pregnancies (filter result): {len(past_pregnancies)}")

for i, preg in enumerate(past_pregnancies, 1):
    print(f"\n   Past Pregnancy {i}:")
    print(f"     outcome: {preg.get('outcome')}")
    print(f"     outcome_code: {preg.get('outcome_code')}")
    print(f"     outcome_date: {preg.get('outcome_date')}")

# Simulate groupby_outcome filter
outcome_groups = {}
for item in past_pregnancies:
    outcome = item.get('outcome', 'Unknown')
    if outcome not in outcome_groups:
        outcome_groups[outcome] = []
    outcome_groups[outcome].append(item)

print(f"\n✅ Grouped by outcome:")
for outcome, items in outcome_groups.items():
    print(f"   {outcome}: {len(items)} records")
    dates = [item.get('outcome_date') for item in items]
    print(f"     Dates: {dates}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"✅ FHIR Bundle: {pregnancy_obs_count} pregnancy observations")
print(f"✅ Parser Output: {len(pregnancy_history)} pregnancy records")
print(f"✅ View Context: {len(context_pregnancy_history)} pregnancy records")
print(f"✅ Past Pregnancies: {len(past_pregnancies)} records")
print(f"✅ Outcome Groups: {len(outcome_groups)} groups")

# Check for data loss
if pregnancy_obs_count > 0 and len(pregnancy_history) == 0:
    print("\n❌ DATA LOSS: Parser failed to extract pregnancy observations")
elif len(pregnancy_history) > 0 and len(context_pregnancy_history) == 0:
    print("\n❌ DATA LOSS: View failed to pass pregnancy_history to context")
elif len(context_pregnancy_history) > 0 and len(past_pregnancies) == 0:
    print("\n❌ DATA LOSS: Template filter failed to extract past pregnancies")
elif len(past_pregnancies) != len([p for p in pregnancy_history if p.get('pregnancy_type') == 'past']):
    print("\n❌ DATA LOSS: Filter returned wrong number of past pregnancies")
else:
    print("\n✅ NO DATA LOSS: All checkpoints passed successfully")
    
    # But check if UI shows correct data
    termination_count = len(outcome_groups.get('Termination', []))
    livebirth_count = len(outcome_groups.get('Livebirth', []))
    
    print(f"\nExpected UI display:")
    if termination_count > 0:
        print(f"  - Termination: {termination_count} records")
    if livebirth_count > 0:
        print(f"  - Livebirth: {livebirth_count} records")
    
    print(f"\nUser reported UI shows:")
    print(f"  - Livebirth only (dates: 2022-06-08, 2021-09-08 00:00, code: 281050002)")
    print(f"  - Missing: Termination records")
    
    if termination_count > 0:
        print(f"\n❌ UI MISMATCH: Parser has {termination_count} terminations but UI shows 0")
        print(f"   Possible causes:")
        print(f"   1. Stale cached session data")
        print(f"   2. Server not restarted after code changes")
        print(f"   3. Template rendering issue")
