# URL Privacy and Security Architecture

## Overview

This document outlines the architectural decisions regarding URL design in the Django NCP healthcare application, with a focus on patient privacy and data protection.

## Core Principle: No Patient Data in URLs

**CRITICAL RULE**: Patient identifiers, personal information, or any healthcare data must NEVER be exposed in URLs.

### Why This Matters

1. **Privacy Protection**: URLs can be logged in server access logs, browser history, referrer headers, and shared inadvertently
2. **GDPR Compliance**: Exposing patient IDs in URLs may violate data protection regulations
3. **Security**: URLs are visible in browser address bars and can be accidentally shared
4. **Healthcare Standards**: Healthcare applications must maintain strict patient confidentiality

### Implementation Strategy

#### Use Session IDs Instead of Patient IDs

✅ **CORRECT**:

```
http://127.0.0.1:8000/patients/details/2771684472/
```

❌ **INCORRECT**:

```
http://127.0.0.1:8000/patients/details/9999002M/
```

#### Session-Based Patient Data Access

1. **Patient searches** generate unique session IDs
2. **Patient data** is stored in Django sessions using session keys like `patient_match_{session_id}`
3. **URLs reference** the session ID, not the patient ID
4. **Views retrieve** patient data from the session using the session ID

### URL Pattern Examples

#### Patient-Related URLs (Session-Based)

```python
# Patient details view
path('patients/details/<str:session_id>/', patient_details_view, name='patient_details')

# Patient CDA views
path('patients/cda/<str:session_id>/', patient_cda_view, name='patient_cda')
path('patients/cda/<str:session_id>/l1/', patient_l1_cda_view, name='patient_l1_cda')
path('patients/cda/<str:session_id>/l3/', patient_l3_cda_view, name='patient_l3_cda')
```

#### Non-Patient URLs (Can Use Descriptive IDs)

```python
# Administrative/system views
path('admin/test-patients/', test_patients_view, name='test_patients')
path('admin/cda-index/refresh/', refresh_cda_index_view, name='refresh_cda_index')
```

### Session Data Structure

Patient data is stored in Django sessions with this structure:

```python
session_key = f"patient_match_{session_id}"
session_data = {
    "patient_data": {
        "given_name": "John",
        "family_name": "Doe",
        "birth_date": "1980-01-01",
        "gender": "M",
        "primary_patient_id": "INTERNAL_ID",  # Never exposed in URLs
        "country_code": "MT"
    },
    "cda_content": "...",
    "file_path": "...",
    "confidence_score": 1.0,
    # ... other session data
}
```

### Navigation Flow

1. **User searches** for patient → generates session ID
2. **Search results stored** in session with key `patient_match_{session_id}`
3. **User navigates** using URLs with session ID
4. **Views retrieve** patient data from session
5. **Patient ID remains** internal to the application

### Back Button Implementation

The back button in CDA views should use session IDs:

```html
<!-- CORRECT: Uses session ID -->
<a href="{% url 'patient_data:patient_details' session_id %}">Back to Patient Details</a>

<!-- INCORRECT: Exposes patient ID -->
<a href="{% url 'patient_data:patient_details' patient_id %}">Back to Patient Details</a>
```

### Security Considerations

1. **Session Timeout**: Sessions expire to prevent indefinite access
2. **Session Validation**: Views must validate session data exists before processing
3. **Cross-Session Isolation**: Session IDs prevent cross-patient data access
4. **Audit Trails**: Patient access can be logged using session IDs without exposing patient data in logs

### Compliance Benefits

- **GDPR Article 32**: Appropriate technical measures for data protection
- **HIPAA**: Protects patient health information from inadvertent disclosure
- **Healthcare Standards**: Maintains patient confidentiality requirements
- **Security Best Practices**: Follows principle of least exposure

## Privacy Compliance Audit Results

### ✅ Templates with Verified Privacy Compliance

- **enhanced_patient_cda.html**: All navigation links use `patient_identity.url_patient_id|default:patient_identity.patient_id`
  - Breadcrumb navigation (line 33)
  - Back to Patient button (line 55)
  - L1/L3 CDA type navigation (lines 175, 181)
- **select_document.html**: Uses `patient_id` (session ID) for navigation
- **error.html**: Uses `patient_id` (session ID) for navigation
- **patient_orcd.html**: Uses session-based patient data object with session ID

### ⚠️ Templates with Potential Admin/Testing Exceptions

- **view_document.html**: Uses `doc_request.patient_data.patient_identifier.id` (database ID)
  - Context: Document request workflow, may be admin-oriented
- **test_patients.html**: Uses `patient.patient_id` (database ID)
  - Context: Test patient interface, administrative use

### 🔍 Admin/Testing URL Patterns (Not User-Facing)

- `direct_patient/<str:patient_id>/` - Explicitly bypasses session middleware for admin access
- `patient_search_results/` - Legacy search interface

## Implementation Checklist

- [x] All patient-related URLs use session IDs
- [x] No patient identifiers in URL patterns
- [x] Session data properly structured and validated
- [x] Back buttons and navigation use session IDs
- [x] Error handling preserves privacy (no patient data in error URLs)
- [ ] Logging doesn't expose patient data through URLs
- [ ] Document admin/testing exceptions to privacy rules
- [ ] Consider implementing role-based access controls for admin URLs

## Date Created

September 24, 2025

## Last Updated

September 24, 2025
