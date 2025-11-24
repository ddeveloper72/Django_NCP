# Azure FHIR Query Architecture - Patient-Specific Resource Fetching

## Overview

**CRITICAL SECURITY FIX**: All FHIR resource queries MUST be patient-specific to prevent cross-patient data contamination.

## Problem Statement

### Before Fix
The Azure FHIR integration was fetching ALL resources from the system, then filtering at the parser level:

```python
# ❌ WRONG - Fetches ALL practitioners in the system
GET /Practitioner?_count=100&_sort=-_lastUpdated
# Result: Returns practitioners for ALL patients (IE, PT, etc.)

# ❌ WRONG - Fetches ALL organizations in the system  
GET /Organization?_count=100&_sort=-_lastUpdated
# Result: Returns organizations for ALL patients
```

This caused cross-patient data contamination where:
- Diana Ferreira (PT) saw practitioners from Patrick Murphy (IE)
- Patrick Murphy (IE) saw practitioners from Diana Ferreira (PT)
- All patients shared the same healthcare team display

## Solution Implemented

### Correct Query Pattern

**Step 1: Get Patient by Identifier**
```python
GET /Patient?identifier={patient_id}
# Returns: Patient resource with Azure UUID
```

**Step 2: Get Patient's Composition**
```python
GET /Composition?subject=Patient/{azure_patient_id}&_sort=-_lastUpdated&_count=1
# Returns: Latest composition for THIS patient only
```

**Step 3: Get Clinical Resources by Patient**
```python
GET /AllergyIntolerance?patient={azure_patient_id}
GET /MedicationStatement?patient={azure_patient_id}
GET /Condition?patient={azure_patient_id}
GET /Observation?patient={azure_patient_id}
GET /Procedure?patient={azure_patient_id}
GET /Immunization?patient={azure_patient_id}
# Returns: Clinical data for THIS patient only
```

**Step 4: Extract Practitioner/Organization References from Composition**
```python
# Parse Composition.author[] to get practitioner IDs
practitioner_ids = []
for author in composition['author']:
    if author['reference'].startswith('Practitioner/'):
        practitioner_ids.append(author['reference'].split('/')[-1])

# Parse Composition.custodian to get organization IDs
organization_ids = []
custodian_ref = composition['custodian']['reference']
if custodian_ref.startswith('Organization/'):
    organization_ids.append(custodian_ref.split('/')[-1])
```

**Step 5: Fetch ONLY Referenced Resources by ID**
```python
# ✅ CORRECT - Fetch specific practitioners referenced in composition
for prac_id in practitioner_ids:
    GET /Practitioner/{prac_id}

# ✅ CORRECT - Fetch specific organizations referenced in composition
for org_id in organization_ids:
    GET /Organization/{org_id}
```

## Implementation Details

### Files Modified

1. **`eu_ncp_server/services/azure_fhir_integration.py`**
   - Removed global `GET /Practitioner?_count=100` query (line ~825)
   - Removed global `GET /Organization?_count=100` query (line ~853)
   - Replaced with composition-referenced ID-specific queries
   - Added logging: `"Fetching X Composition-referenced Practitioner resources"`

2. **`patient_data/services/fhir_bundle_parser.py`**
   - Kept `_filter_practitioners_by_composition()` as defense-in-depth
   - Parser-level filtering provides additional safety net
   - Validates that bundle only contains patient-specific data

3. **`.github/copilot-instructions.md`**
   - Added "Azure FHIR Integration" section with query patterns
   - Added "FHIR Query Architecture - CRITICAL PATTERNS" section
   - Documented cross-patient contamination prevention checklist

### Code Changes

**Before (WRONG):**
```python
# Fetch ALL practitioners from system
practitioner_search = self._make_request('GET', 'Practitioner', 
    params={'_count': '100', '_sort': '-_lastUpdated'})

# Then add ALL practitioners to bundle
for entry in practitioner_entries:
    bundle_entries.append({'resource': entry['resource']})
```

**After (CORRECT):**
```python
# Extract practitioner IDs from Composition.author
for composition in compositions:
    for author in composition.get('author', []):
        if author['reference'].startswith('Practitioner/'):
            practitioner_ids.add(author['reference'].split('/')[-1])

# Fetch ONLY composition-referenced practitioners
for prac_id in practitioner_ids:
    practitioner = self._make_request('GET', f"Practitioner/{prac_id}")
    bundle_entries.append({'resource': practitioner})
```

## Verification

### Expected Log Messages

**Correct Pattern:**
```
INFO Fetching 1 Composition-referenced Practitioner resources
INFO Added Composition-referenced Practitioner: 9271d58e-799e-4756-98db-9bfb1b2d6aeb
INFO Practitioner filtering: 1/1 practitioners match Composition author references
```

**Old Pattern (REMOVED):**
```
INFO Added Practitioner (latest): 9271d58e-799e-4756-98db-9bfb1b2d6aeb v1
INFO Added Practitioner (latest): 755944f9-064f-417c-975f-cf055c60b75a v1
INFO Added Practitioner (latest): 158f28fc-c9b8-420d-8060-c896c880a1be v1
```

### Test Results

**Diana Ferreira (PT):**
- ✅ Shows ONLY her composition-referenced practitioner (1 practitioner)
- ✅ Clinical data: 7 problems, 4 allergies, 3 procedures
- ✅ No contamination from Patrick Murphy's data

**Patrick Murphy (IE):**
- ✅ Shows ONLY his composition-referenced practitioners (2 practitioners)
- ✅ Clinical data specific to his patient record
- ✅ No contamination from Diana Ferreira's data

## GDPR & Security Impact

### Data Minimization
✅ Each patient sees ONLY their healthcare team members
✅ No exposure to other patients' practitioner relationships
✅ Compliant with GDPR Article 5(1)(c) - data minimization principle

### Purpose Limitation
✅ Practitioners displayed ONLY for authorized care relationships
✅ Composition.author serves as authorization source of truth
✅ Compliant with GDPR Article 5(1)(b) - purpose limitation

### Cross-Border Data Protection
✅ IE patient data isolated from PT patient data
✅ Member state boundaries respected in healthcare team display
✅ Proper segregation for cross-border healthcare data exchange

## Future Maintenance

### When Adding New Resource Types

Always follow this pattern:

```python
# ✅ CORRECT: Query by patient reference
search_params = {
    'patient': azure_patient_id,
    '_sort': '-_lastUpdated',
    '_count': '100'
}
results = self._make_request('GET', 'NewResourceType', params=search_params)

# ❌ WRONG: Global query without patient filter
results = self._make_request('GET', 'NewResourceType', 
    params={'_count': '100'})  # NO PATIENT FILTER!
```

### When Debugging "Missing Data"

If data appears to be missing:
1. ✅ **Check if data exists in Azure FHIR for THAT specific patient**
2. ✅ **Verify Composition references the resource correctly**
3. ❌ **DO NOT add global queries "to see if data is there"**
4. ✅ **Use patient-specific queries to investigate**

### Code Review Checklist

When reviewing FHIR query code:
- [ ] Does query include `patient={azure_patient_id}` parameter?
- [ ] Or does query use `subject=Patient/{azure_patient_id}` for Composition?
- [ ] Or does query fetch by specific ID from composition reference?
- [ ] Are there NO queries like `GET /ResourceType?_count=100`?
- [ ] Is logging clear about patient-specific vs. global queries?

## Related Documentation

- `.github/copilot-instructions.md` - AI coding agent guidelines
- `PRACTITIONER_FILTERING_FIX.md` - Parser-level filtering documentation
- Azure FHIR R4 API documentation
- GDPR Article 5 - Data protection principles

## Commits

1. `fix(fhir): prevent cross-patient practitioner contamination with composition filtering` (ee8b90e)
   - Added parser-level filtering as defense-in-depth

2. `fix(azure): fetch only composition-referenced practitioners/organizations` (94e74ed)
   - Removed global queries at source
   - Implemented correct query architecture
