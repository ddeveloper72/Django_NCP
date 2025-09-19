# Patient Identifier Management in EU NCP Portal

## Overview

The EU NCP Portal uses a multi-layered patient identification system to maintain security while enabling cross-border healthcare data exchange. This document explains the different types of identifiers used and their purposes.

## Identifier Types

### 1. Session-Based Temporary IDs (URL Path)

- **Format**: Numeric (e.g., `549316`, `984385`)
- **Location**: URL path segments (`/patients/cda/{session_id}/L3/`)
- **Purpose**: Temporary identifier for the current user session
- **Lifecycle**: Generated during patient search, expires with session
- **Security**: No correlation to actual patient data

**Example URL Structure:**

```
/patients/cda/549316/L3/
             ^^^^^^
         Session ID (temporary)
```

### 2. CDA Document Patient Identifiers

- **Format**: Large numeric strings (e.g., `539305455995368085`)
- **Location**: Within CDA XML documents
- **Purpose**: Official patient identifier from source healthcare system
- **Lifecycle**: Persistent across all interactions for the same patient
- **Security**: Real patient identifier - handled with strict confidentiality

**CDA XML Example:**

```xml
<patientRole>
    <id extension="539305455995368085" root="2.16.840.1.113883.2.x.x.x"/>
    <!-- Patient identifier from source system -->
</patientRole>
```

### 3. Database Internal IDs

- **Format**: UUIDs or auto-increment integers
- **Location**: Django model primary keys
- **Purpose**: Internal database record management
- **Lifecycle**: Persistent for database records
- **Security**: Internal use only, not exposed to users

## ID Flow and Relationships

```
Patient Search → Session Created → Temporary ID Generated
                       ↓
                 CDA Retrieved → Real Patient ID Extracted
                       ↓
                 Data Processed → Displayed with Session ID in URL
```

## Security Considerations

### Session IDs (URL Path)

✅ **Safe to log/debug**: No patient information
✅ **Safe in URLs**: Temporary and meaningless
✅ **Safe in error messages**: No PHI exposure
✅ **Safe in documentation**: Can be used as examples

### CDA Patient IDs

❌ **Never log in plain text**: Contains PHI
❌ **Never expose in URLs**: Privacy violation
❌ **Encrypt in database**: Use appropriate protection
❌ **Mask in documentation**: Use placeholder values

## Code Implementation

### URL Routing

```python
# urls.py
path('patients/cda/<int:session_id>/<str:cda_type>/', views.patient_cda_detail)
#                    ^^^^^^^^^^
#                 Temporary session ID
```

### Data Processing

```python
# In views.py
def patient_cda_detail(request, session_id, cda_type):
    # session_id is temporary (e.g., 549316)
    patient_data = get_patient_by_session(session_id)

    # Extract real patient ID from CDA
    cda_patient_id = extract_patient_id_from_cda(patient_data.cda_content)
    # cda_patient_id would be the real identifier (e.g., 539305455995368085)
```

### Template Context

```python
# Extended patient data processing
context = {
    'session_id': session_id,  # Temporary (549316)
    'patient_identity': {
        'cda_patient_id': '[PROTECTED]',  # Real ID masked in logs
        'display_name': patient_name,
        # ... other data
    }
}
```

## Database Schema

### Session Management

```python
class PatientSearchSession(models.Model):
    session_id = models.AutoField(primary_key=True)  # Temporary ID
    search_timestamp = models.DateTimeField()
    expires_at = models.DateTimeField()

class PatientData(models.Model):
    session = models.ForeignKey(PatientSearchSession)
    cda_patient_identifier = models.CharField(max_length=255)  # Real ID (encrypted)
    cda_content = models.TextField()  # Full CDA document
```

## Debugging and Logging Guidelines

### Safe to Log

```python
logger.info(f"Processing session {session_id}")  # ✅ Safe
logger.debug(f"URL: /patients/cda/{session_id}/L3/")  # ✅ Safe
print(f"Session {session_id} has extended data: {has_data}")  # ✅ Safe
```

### Must Be Protected

```python
# ❌ NEVER DO THIS:
logger.info(f"Patient ID: {cda_patient_id}")

# ✅ DO THIS INSTEAD:
logger.info(f"Patient ID: {'*' * len(str(cda_patient_id))}")
# or
logger.info(f"Processing patient with ID hash: {hash(cda_patient_id)}")
```

## Testing Examples

### Safe Test Data

- Session IDs: `549316`, `984385`, `123456`
- Mock CDA IDs: `999999999999999999`, `111111111111111111`
- Database IDs: UUIDs or sequential integers

### Real-World Mapping Example

```
User searches for patient → Session 549316 created
CDA retrieved contains    → Patient ID 539305455995368085
User sees URL:           → /patients/cda/549316/L3/
Template displays:       → "Patrick Murphy" (from CDA)
Database stores:         → Session 549316 ↔ Encrypted patient ID
```

## Extended Patient Information Context

When debugging the Extended Patient Information template:

- The tabs and counts (1, 2, 3, 3, 1) are based on CDA content
- The URL session ID (549316) is just the lookup key
- The patient identity comes from the CDA document
- Administrative data depends on what's in the source healthcare system's CDA

## Important Notes

1. **Session IDs are temporary**: They change with each new search
2. **CDA Patient IDs are permanent**: Same for the patient across all sessions
3. **URL path never contains PHI**: Safe for logs, errors, and debugging
4. **Real patient data**: Always treat CDA content as sensitive PHI
5. **Database relationships**: Session ID → Patient Data → CDA Content → Real Patient ID

This architecture ensures patient privacy while enabling efficient session management and cross-border healthcare data exchange.
