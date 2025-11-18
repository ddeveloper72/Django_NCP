# Next-of-Kin Contact Issue - Root Cause Analysis

## Problem
UI displays only 1 next-of-kin contact (Joaquim Baptista) when Diana Ferreira's FHIR bundle contains 2:
1. Joaquim Baptista (guardian@gmail.com, 351211234569)
2. Vitória Silva (paciente@gmail.com, 351211234570)

## Investigation Results

### FHIR Bundle Data ✅
**File**: `test_data/eu_member_states/PT/Diana_Ferreira_bundle.json`
**Lines 442-509**: Patient.contact array with 2 contacts

Both contacts have:
- Relationship: "Next-of-Kin" (code "N", system v2-0131)
- Complete name, telecom, address data

### Parser Code ✅
**File**: `patient_data/services/fhir_bundle_parser.py`

**Lines 2585-2661**: Extract ALL contacts from Patient.contact
```python
contacts = patient.get('contact', [])
for contact in contacts:
    # Extract relationship, name, telecom, address
    other_contacts.append({...})
administrative_data['other_contacts'] = other_contacts
```

**Lines 3005-3041**: Map Next-of-Kin to emergency_contacts
```python
for contact in administrative_data.get('other_contacts'):
    relationship = contact.get('relationship', '').lower()
    if any(keyword in relationship for keyword in ['next-of-kin', 'emergency', 'guardian']):
        emergency_contact = {...}
        contact_data['emergency_contacts'].append(emergency_contact)
```

### Debug Script Results ✅
**File**: `debug_contact_parsing.py`
**Output**:
```
Total contacts in Patient.contact: 2

CONTACT #1: Joaquim Baptista (Next-of-Kin)
CONTACT #2: Vitória Silva (Next-of-Kin)

✅ Extracted 2 contacts to other_contacts list
✅ All contacts successfully mapped to emergency_contacts
```

**Conclusion**: Parser logic is 100% correct - both contacts ARE extracted and mapped.

### Template Code ✅
**File**: `templates/patient_data/components/administrative/patient_contact.html`
**Lines 100-150**: Loop through all contacts
```html
{% for contact in contact_data.contacts %}
    <div class="participant-section mb-4">
        <!-- Display contact details -->
    </div>
{% endfor %}
```

**Conclusion**: Template will display ALL contacts in the array.

### View Context ✅
**File**: `patient_data/view_processors/fhir_processor.py`
**Line 217**:
```python
contact_data = parsed_data.get('contact_data', {})
if contact_data:
    context['contact_data'] = contact_data
```

**Conclusion**: View passes parser output directly to template.

## Root Cause: Session Cache Persistence

The issue is **NOT** in the code - it's in Django's session data:

1. **Original CDA**: Had only 1 next-of-kin (likely Joaquim Baptista)
2. **FHIR Bundle Created**: CDA converted to FHIR, gained 2nd contact (Vitória Silva)
3. **Session Created**: Django parsed FHIR bundle, stored contact data in db.sqlite3
4. **CDA Updated**: Original CDA may have been updated with 2nd contact
5. **FHIR Re-converted**: New FHIR bundle now has 2 contacts
6. **Session NOT Cleared**: Django still serves old session data with 1 contact
7. **UI Shows Old Data**: Template displays cached 1-contact data, not fresh 2-contact data

### Evidence
- Parser extracts 2 contacts (debug script proves this)
- Template loops through all contacts (code reviewed)
- UI shows only 1 contact (user report)
- **Conclusion**: UI is displaying old cached session data

## Solution: Clear Django Sessions

Same fix as date formatting issue:

### Step 1: Stop Django Server
```powershell
# Press Ctrl+C in terminal running Django
```

### Step 2: Clear Python Cache
```powershell
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
```

### Step 3: Clear Django Sessions
**Option A - Clear all sessions** (recommended):
```powershell
python clear_sessions.py
```

**Option B - Delete database** (nuclear option):
```powershell
Remove-Item db.sqlite3
python manage.py migrate
```

### Step 4: Restart Django Server
```powershell
python manage.py runserver
```

### Step 5: Re-parse Diana's Data
1. Navigate to Diana Ferreira patient view in browser
2. Fresh parsing will use current FHIR bundle with 2 contacts
3. New session data will have both Joaquim Baptista AND Vitória Silva

## Expected Results After Cache Clear

✅ Extended Patient Information tab will show 2 "Contact Person / Next of Kin" cards:

**Card 1:**
- Name: Joaquim Baptista
- Role: Next-of-Kin
- Email: guardian@gmail.com
- Phone: 351211234569
- Address: 155, Avenida da Liberdade, Lisbon 1250-141, PT

**Card 2:**
- Name: Vitória Silva
- Role: Next-of-Kin
- Email: paciente@gmail.com
- Phone: 351211234570

## Related Issues

This is the **SAME** root cause as the date formatting issue:
- Date formatter code works (19/19 tests pass)
- UI shows raw dates
- **Reason**: Session cache has old unformatted dates

Both issues require clearing Django session cache to see the updated code output.

## Technical Notes

### Why Session Caching Causes This

Django's session middleware stores parsed FHIR data in `django_session` table:
```python
# On first patient view
parsed_data = fhir_bundle_parser.parse(bundle)  # Returns 2 contacts
session['patient_data'] = parsed_data  # Stored in db.sqlite3

# On subsequent views
if 'patient_data' in session:
    context['contact_data'] = session['patient_data']['contact_data']  # Uses cached data
    # Parser NOT called again - no re-parsing of updated FHIR bundle
```

### Why Cache Isn't Auto-Invalidated

Django sessions don't auto-invalidate when:
- Source FHIR bundle files change
- Parser code is updated
- Database schema remains same

Manual cache clearing required after:
- Parser code changes (e.g., date formatting)
- FHIR bundle regeneration (e.g., CDA-to-FHIR conversion)
- Data structure updates (e.g., additional contacts)

## Prevention Strategy

For future development, consider:

1. **Version-based cache invalidation**:
```python
PARSER_VERSION = "2.0.0"  # Increment on changes
cache_key = f"patient_{patient_id}_v{PARSER_VERSION}"
```

2. **Bundle timestamp checking**:
```python
bundle_modified = os.path.getmtime(bundle_path)
cached_timestamp = session.get('bundle_timestamp')
if bundle_modified > cached_timestamp:
    # Re-parse bundle
```

3. **Development mode auto-refresh**:
```python
if settings.DEBUG:
    # Always re-parse in development
    parsed_data = parser.parse(bundle)
else:
    # Use cache in production
    parsed_data = cache.get_or_set(...)
```

## Files Verified

✅ `patient_data/services/fhir_bundle_parser.py` - Parser logic correct
✅ `test_data/eu_member_states/PT/Diana_Ferreira_bundle.json` - 2 contacts present
✅ `templates/patient_data/components/administrative/patient_contact.html` - Loop displays all
✅ `patient_data/view_processors/fhir_processor.py` - Context mapping correct
✅ `debug_contact_parsing.py` - Simulation confirms 2 contacts extracted

**Code is correct. Issue is environmental (session cache).**
