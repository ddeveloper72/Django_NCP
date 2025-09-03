# CDA View Fix - Patient Data Not Found Error

## Problem Analysis

When users clicked the "View CDA Document" button from patient details page, they were getting:

- **HTTP 302 Redirect** to `/patients/`
- **Error Message**: "Patient data not found"
- **Request**: `GET /patients/cda/252003/`

## Root Cause Identified

The `patient_cda_view` was using **incorrect patient lookup logic**:

```python
# OLD CODE (BROKEN)
def patient_cda_view(request, patient_id):
    try:
        patient_data = PatientData.objects.get(id=patient_id)  # ❌ FAILS for temporary patients
        # ... rest of function
    except PatientData.DoesNotExist:
        messages.error(request, "Patient data not found.")
        return redirect("patient_data:patient_data_form")
```

### Why This Failed

1. **Temporary Patients**: When users click "Test NCP Query" for Mario PINO, the system creates a temporary patient with ID `252003`
2. **Session-Only Storage**: This temporary patient exists only in the session (`patient_match_252003`) and is **never saved to the database**
3. **Database-First Lookup**: The CDA view tried to find patient `252003` in the database first, which **always failed**
4. **Immediate Redirect**: The `PatientData.DoesNotExist` exception triggered an immediate redirect with error message

## Solution Implemented

Updated `patient_cda_view` to use the **same logic as `patient_details_view`**:

```python
# NEW CODE (FIXED)
def patient_cda_view(request, patient_id):
    # Check if this is an NCP query result (session data exists but no DB record)
    session_key = f"patient_match_{patient_id}"
    match_data = request.session.get(session_key)

    if match_data and not PatientData.objects.filter(id=patient_id).exists():
        # ✅ This is an NCP query result - create temp patient from session data
        patient_info = match_data["patient_data"]
        
        patient_data = PatientData(
            id=patient_id,
            given_name=patient_info.get("given_name", "Unknown"),
            family_name=patient_info.get("family_name", "Patient"),
            birth_date=patient_info.get("birth_date") or None,
            gender=patient_info.get("gender", ""),
        )
        # Don't save to database - just use for rendering
        
    else:
        # ✅ Standard database lookup for persistent patients
        try:
            patient_data = PatientData.objects.get(id=patient_id)
        except PatientData.DoesNotExist:
            messages.error(request, "Patient data not found.")
            return redirect("patient_data:patient_data_form")
    
    # ✅ Continue with CDA rendering logic...
```

## Fix Benefits

### ✅ **Session-First Logic**

- Checks session data before database lookup
- Handles temporary patients from NCP queries correctly
- Maintains compatibility with persistent database patients

### ✅ **Proper Patient Creation**

- Creates temporary `PatientData` object from session data
- Uses same pattern as `patient_details_view`
- No database saves for temporary patients (maintains NCP principles)

### ✅ **Error Handling**

- Only shows "Patient data not found" for truly missing patients
- Graceful fallback for edge cases
- Preserves existing behavior for database patients

## Expected User Flow (Now Fixed)

1. User clicks "View Test Patients"
2. Clicks "Test NCP Query" for Mario PINO  
3. Search creates temporary patient `252003` with session data
4. User redirected to patient details page
5. User clicks "View CDA Document"
6. **BEFORE**: `GET /patients/cda/252003/` → 302 redirect + "Patient data not found"
7. **AFTER**: `GET /patients/cda/252003/` → 200 OK + CDA display page

## Technical Details

- **Session Key**: `patient_match_{patient_id}` (e.g., `patient_match_252003`)
- **Session Data**: Contains CDA content, patient info, match scores, file paths
- **Temporary Patient**: Created in memory only, never persisted to database
- **Database Fallback**: Still works for patients saved in database

## Testing

Created `test_cda_view_fix.py` to verify:

- Temporary patient handling works correctly
- Session data is properly utilized
- Edge cases (no session data) handled gracefully
- Both temporary and database patients supported

## Files Modified

- `patient_data/views.py` - Fixed `patient_cda_view` function
- Added comprehensive test scripts

This fix ensures the complete NCP query workflow works end-to-end without "Patient data not found" errors.
