# Django Session Debugging Guide

## Overview

This guide documents critical information about Django session management in the EU NCP Server project, specifically focusing on clinical data storage and debugging techniques.

## Key Session Concepts

### Session Storage Architecture

- **Django Sessions**: Stored in `django_session` table in SQLite database
- **Session Keys**: Unique identifiers for each session (e.g., `7fn3b46flxfelbi85do2ji67m6uams2r`)
- **Session Data**: **ENCODED/SERIALIZED** - Must use `session.get_decoded()` to access actual data
- **Patient Data Keys**: Stored as `patient_match_{patient_id}` within session data

### ⚠️ Critical: Session Data is Encoded

```python
# WRONG - This won't work
session = Session.objects.get(session_key='some_key')
data = session.session_data  # This is encoded/serialized string

# CORRECT - Always decode session data
session = Session.objects.get(session_key='some_key')
session_data = session.get_decoded()  # This returns actual Python dict
```

## Session Data Structure

### Typical Patient Match Structure

```python
{
    "patient_match_2190038834": {
        "file_path": "/path/to/cda/file.xml",
        "country_code": "MT",
        "confidence_score": 0.95,
        "patient_data": {
            "given_name": "Mario",
            "family_name": "Borg",
            "birth_date": "1970-01-01",
            # ... other patient fields
        },
        "cda_content": "...",           # Raw CDA XML
        "l1_cda_content": "...",        # Level 1 CDA content
        "l3_cda_content": "...",        # Level 3 CDA content
        "l1_cda_path": "/path/to/l1.xml",
        "l3_cda_path": "/path/to/l3.xml",
        "preferred_cda_type": "L3",
        "has_l1": true,
        "has_l3": true,
        "l1_documents": [...],
        "l3_documents": [...],
        "selected_l1_index": 0,
        "selected_l3_index": 0,
        "document_summary": "...",
        "available_document_types": ["L1", "L3"],
        "cda_type": "L3"
    }
}
```

## Common Session Debugging Scenarios

### 1. Finding Patient Data by ID

```python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.contrib.sessions.models import Session

def find_patient_by_id(patient_id):
    """Find patient data across all sessions"""
    session_key = f"patient_match_{patient_id}"

    for session in Session.objects.all():
        try:
            session_data = session.get_decoded()  # CRITICAL: Decode first!
            if session_key in session_data:
                return session, session_data[session_key]
        except Exception:
            continue  # Skip corrupted sessions

    return None, None

# Usage
session, patient_data = find_patient_by_id("2190038834")
if patient_data:
    print(f"Found patient in session: {session.session_key}")
    print(f"CDA content length: {len(patient_data.get('l3_cda_content', ''))}")
```

### 2. Finding All Patients with Specific Name

```python
def find_patients_by_name(given_name, family_name):
    """Find all patients with specific name across sessions"""
    results = []

    for session in Session.objects.all():
        try:
            session_data = session.get_decoded()  # CRITICAL: Decode first!

            # Check all patient_match keys in this session
            for key, match_data in session_data.items():
                if key.startswith('patient_match_'):
                    patient_data = match_data.get('patient_data', {})
                    if (patient_data.get('given_name', '').lower() == given_name.lower() and
                        patient_data.get('family_name', '').lower() == family_name.lower()):
                        results.append({
                            'session_key': session.session_key,
                            'patient_match_key': key,
                            'patient_id': key.replace('patient_match_', ''),
                            'cda_length': len(match_data.get('l3_cda_content', ''))
                        })
        except Exception:
            continue

    return results

# Usage
mario_sessions = find_patients_by_name("Mario", "Borg")
for result in mario_sessions:
    print(f"Mario Borg found: {result}")
```

### 3. Session Data Inspection

```python
def inspect_session(session_key):
    """Detailed inspection of a specific session"""
    try:
        session = Session.objects.get(session_key=session_key)
        session_data = session.get_decoded()  # CRITICAL: Decode first!

        print(f"Session: {session_key}")
        print(f"Expire Date: {session.expire_date}")
        print(f"Total Keys: {len(session_data)}")

        # Find patient match keys
        patient_keys = [k for k in session_data.keys() if k.startswith('patient_match_')]
        print(f"Patient Match Keys: {patient_keys}")

        for key in patient_keys:
            match_data = session_data[key]
            patient_data = match_data.get('patient_data', {})
            print(f"  {key}:")
            print(f"    Patient: {patient_data.get('given_name')} {patient_data.get('family_name')}")
            print(f"    Country: {match_data.get('country_code')}")
            print(f"    CDA Type: {match_data.get('preferred_cda_type')}")
            print(f"    L3 Content: {len(match_data.get('l3_cda_content', ''))} chars")

    except Session.DoesNotExist:
        print(f"Session {session_key} not found")
    except Exception as e:
        print(f"Error inspecting session: {e}")
```

## Clinical Data Debugger Session Lookup Fix

### Problem

The clinical debugger URL uses patient IDs (e.g., `/debug/clinical/2190038834/`) but the view was only looking in the current user's session, not across all database sessions where the patient data is actually stored.

### Solution

Updated `clinical_data_debugger.py` to search across all sessions:

```python
def clinical_data_debugger(request, session_id):
    try:
        # First, try current request session
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key)

        # If not found, search across all database sessions
        if not match_data:
            # Try direct session key lookup
            try:
                db_session = Session.objects.get(session_key=session_id)
                db_session_data = db_session.get_decoded()  # CRITICAL: Decode!
                match_data = db_session_data.get(session_key)
            except Session.DoesNotExist:
                pass

            # Search all sessions for patient_match_{session_id}
            if not match_data:
                for db_session in Session.objects.all():
                    try:
                        db_session_data = db_session.get_decoded()  # CRITICAL: Decode!
                        if session_key in db_session_data:
                            match_data = db_session_data[session_key]
                            break
                    except Exception:
                        continue

        if not match_data:
            return JsonResponse({"error": f"No patient data found for session {session_id}"}, status=404)

        # Continue with clinical data extraction...
```

## Common Debugging Commands

### Quick Session Check

```bash
cd /path/to/django/project
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()
from django.contrib.sessions.models import Session

# Find specific patient
sessions = Session.objects.all()
for s in sessions:
    try:
        data = s.get_decoded()
        if 'patient_match_2190038834' in data:
            print(f'Found in session: {s.session_key}')
            print(f'CDA length: {len(data[\"patient_match_2190038834\"].get(\"l3_cda_content\", \"\"))}')
    except: pass
"
```

### Count All Patients

```bash
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()
from django.contrib.sessions.models import Session

total_patients = 0
for s in Session.objects.all():
    try:
        data = s.get_decoded()
        patient_keys = [k for k in data.keys() if k.startswith('patient_match_')]
        total_patients += len(patient_keys)
    except: pass

print(f'Total patients across all sessions: {total_patients}')
"
```

## Important Notes

1. **Always Decode**: Session data is encoded - always use `session.get_decoded()`
2. **Exception Handling**: Some sessions may be corrupted - wrap in try/catch
3. **Patient ID vs Session Key**: URL patient IDs (like `2190038834`) are NOT Django session keys
4. **Search Pattern**: Patient data is stored as `patient_match_{patient_id}` keys within sessions
5. **Multiple Sessions**: Same patient might appear in multiple sessions
6. **CDA Content Priority**: Check `l3_cda_content` first, then `cda_content`, then `l1_cda_content`

## Related Files

- `patient_data/clinical_data_debugger.py` - Clinical debugger with session lookup fix
- `patient_data/urls.py` - URL routing for debugger
- Database: `django_session` table contains all session data

## Testing the Fix

Use `test_debugger_fix.py` to verify the clinical debugger can find patient data across sessions:

```bash
python test_debugger_fix.py
```

This should output successful session lookup and clinical data extraction for Mario Borg (patient ID 2190038834).
