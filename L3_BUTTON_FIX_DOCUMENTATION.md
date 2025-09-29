# L3 Button Fix Verification

## Problem Analysis

The L3 CDA button was disabled despite L3 CDA documents being available at `http://127.0.0.1:8000/patients/cda/3170408255/L3/`

## Root Cause

In `patient_data/views.py`, the `has_l3_cda` context variable was set using a priority fallback system:

1. Session data from `patient_match_{session_id}`
2. Extended session data from `patient_extended_data_{session_id}`
3. Search result object method `search_result.has_l3_cda()`

When session data expired due to timeout (as evidenced in server logs), the fallback to `search_result.has_l3_cda()` was failing because the search result was either None or incorrectly returning False.

## Solution Implemented

### 1. Added Helper Function

```python
def _check_actual_cda_availability(session_id, cda_type):
    """Check if CDA document is actually available when session data is missing"""
    try:
        from django.contrib.sessions.models import Session

        # Search for session data directly
        session_key = f"patient_match_{session_id}"
        all_sessions = Session.objects.all()

        for db_session in all_sessions:
            try:
                session_data = db_session.get_decoded()
                if session_key in session_data:
                    match_data = session_data[session_key]

                    # Check for the specific CDA type content
                    if cda_type.upper() == "L3":
                        cda_content = match_data.get("l3_cda_content")
                    elif cda_type.upper() == "L1":
                        cda_content = match_data.get("l1_cda_content")
                    else:
                        cda_content = match_data.get("cda_content")

                    # If we found content, the CDA type is available
                    is_available = bool(cda_content and len(cda_content) > 100)

                    logger.info(f"Direct CDA availability check for {session_id}/{cda_type}: {is_available}")
                    return is_available

            except Exception:
                continue  # Skip corrupted sessions

        logger.warning(f"No session data found for direct CDA availability check: {session_id}/{cda_type}")
        return False

    except Exception as e:
        logger.warning(f"Failed to check actual CDA availability for {session_id}/{cda_type}: {e}")
        return False
```

### 2. Enhanced Context Variable Logic

**Before (problematic):**

```python
"has_l3_cda": (
    request.session.get(f"patient_match_{session_id}", {}).get("has_l3")
    if f"patient_match_{session_id}" in request.session
    else (
        request.session.get(f"patient_extended_data_{session_id}", {}).get("has_l3_cda")
        if f"patient_extended_data_{session_id}" in request.session
        else search_result.has_l3_cda()
    )
),
```

**After (robust):**

```python
"has_l3_cda": (
    request.session.get(f"patient_match_{session_id}", {}).get("has_l3")
    if f"patient_match_{session_id}" in request.session
    else (
        request.session.get(f"patient_extended_data_{session_id}", {}).get("has_l3_cda")
        if f"patient_extended_data_{session_id}" in request.session
        else (
            search_result.has_l3_cda() if search_result
            else _check_actual_cda_availability(session_id, "L3")
        )
    )
),
```

### 3. Applied Same Fix to L1 Logic

Applied identical enhancement to `has_l1_cda` for consistency.

## Expected Behavior After Fix

1. **Primary Path**: When session data exists in memory → Use existing logic
2. **Secondary Path**: When extended session data exists → Use extended data
3. **Tertiary Path**: When search_result is available → Use search_result.has_l3_cda()
4. **Fallback Path**: When all else fails → Check Django session database directly for CDA content

## Key Improvements

- **Resilience**: System now handles session timeout gracefully
- **Direct Verification**: Actually checks for CDA content presence rather than relying on potentially stale flags
- **Comprehensive Fallback**: Multiple layers of fallback ensure button state reflects actual data availability
- **Session Recovery**: Can recover CDA availability information even after in-memory session expiry

## Testing Steps

1. Navigate to patient CDA page with expired session
2. Verify L3 button is enabled when L3 CDA content exists
3. Verify button correctly links to functional L3 CDA view
4. Check server logs for proper fallback mechanism activation

## Files Modified

- `patient_data/views.py`: Lines ~2920 (helper function) and ~3800-3810 (context variables)

This fix ensures that the L3 button state accurately reflects actual CDA document availability, even when session data has expired due to timeout.
