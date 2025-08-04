# Patient Identifier Rendering Fix

## Problem

Patient identifiers (primary and secondary IDs provided by member states) were not being displayed in the CDA template, showing only the internal database ID instead.

## Root Cause

The `patient_identity` dictionary in the `patient_cda_view` function was missing the actual patient identifiers from the member state data stored in the session.

## Solution Implemented

### 1. Updated Views.py (patient_cda_view function)

**File**: `patient_data/views.py` - Line ~745

- Added `primary_patient_id` and `secondary_patient_id` to the `patient_identity` dictionary
- These values are extracted from `match_data["patient_data"]` which contains the actual member state identifiers

**Before:**

```python
patient_identity = {
    "family_name": patient_data.family_name,
    "given_name": patient_data.given_name,
    "birth_date": ...,
    "gender": ...,
    "patient_id": patient_data.id,  # Only internal DB ID
}
```

**After:**

```python
patient_identity = {
    "family_name": patient_data.family_name,
    "given_name": patient_data.given_name,
    "birth_date": ...,
    "gender": ...,
    "patient_id": patient_data.id,
    "primary_patient_id": match_data["patient_data"].get("primary_patient_id", ""),
    "secondary_patient_id": match_data["patient_data"].get("secondary_patient_id", ""),
}
```

### 2. Updated CDA Template (Patient Identity Banner)

**File**: `templates/jinja2/patient_data/patient_cda.html` - Lines ~37-47

- Replaced single internal ID display with conditional rendering of member state identifiers
- Shows Primary ID and Secondary ID when available
- Falls back to internal ID only if member state IDs are not available

**Before:**

```html
<span class="patient-id">ID: {{ patient_identity.patient_id }}</span>
```

**After:**

```html
{% if patient_identity.primary_patient_id %}
<span class="patient-id-primary">Primary ID: {{ patient_identity.primary_patient_id }}</span>
{% endif %}
{% if patient_identity.secondary_patient_id %}
<span class="patient-id-secondary">Secondary ID: {{ patient_identity.secondary_patient_id }}</span>
{% endif %}
{% if not patient_identity.primary_patient_id and not patient_identity.secondary_patient_id %}
<span class="patient-id">ID: {{ patient_identity.patient_id }}</span>
{% endif %}
```

### 3. Updated Patient Information Section

**File**: `templates/jinja2/patient_data/patient_cda.html` - Lines ~227-240

- Added patient identifier fields to the detailed patient information section
- Shows both Primary and Secondary Patient IDs when available

**Added:**

```html
{% if patient_identity.primary_patient_id %}
<div class="info-item">
    <span class="info-label">Primary Patient ID:</span>
    <span class="info-value">{{ patient_identity.primary_patient_id }}</span>
</div>
{% endif %}
{% if patient_identity.secondary_patient_id %}
<div class="info-item">
    <span class="info-label">Secondary Patient ID:</span>
    <span class="info-value">{{ patient_identity.secondary_patient_id }}</span>
</div>
{% endif %}
```

### 4. Added CSS Styling for Patient IDs

**File**: `static/css/patient_cda_ps_guidelines.css` - Lines ~95-110

- Added distinct styling for primary and secondary patient IDs
- Primary ID: Blue background with darker blue border
- Secondary ID: Light blue background with medium blue border

**Added:**

```css
.patient-identity-banner .patient-identity-left .patient-details .patient-id-primary {
  background: #e8f4f8;
  border: 1px solid #085a9f;
  color: #085a9f;
  font-weight: 600;
}

.patient-identity-banner .patient-identity-left .patient-details .patient-id-secondary {
  background: #f0f8ff;
  border: 1px solid #009fd1;
  color: #006b96;
  font-weight: 600;
}
```

## Expected Results

### Patient Identity Banner Display

- **Primary ID**: Displayed with blue styling (e.g., "Primary ID: DE123456789")
- **Secondary ID**: Displayed with light blue styling (e.g., "Secondary ID: NHS987654321")
- **Fallback**: Internal ID only if member state IDs are missing

### Patient Information Section

- **Primary Patient ID**: Listed in detailed information grid
- **Secondary Patient ID**: Listed in detailed information grid (if available)

## Data Source

Patient identifiers are extracted from CDA documents during the matching process and stored in the session data under:

- `match_data["patient_data"]["primary_patient_id"]`
- `match_data["patient_data"]["secondary_patient_id"]`

These represent the actual patient identifiers from the member state healthcare systems, not the internal database IDs.

## Testing

Created `test_patient_identifiers.py` to verify that:

- ✅ Patient identifiers are properly extracted from session data
- ✅ Template receives the correct identifier values
- ✅ Both primary and secondary IDs are available in the template context

## Files Modified

1. `patient_data/views.py` - Added patient identifiers to patient_identity context
2. `templates/jinja2/patient_data/patient_cda.html` - Updated display logic for patient IDs
3. `static/css/patient_cda_ps_guidelines.css` - Added styling for patient ID displays
4. `test_patient_identifiers.py` - Test script to verify functionality

The patient identifiers from member states should now be properly displayed in both the patient identity banner and the detailed patient information section.
