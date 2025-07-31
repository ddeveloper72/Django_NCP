# Country Flag Styling Fix

## Issue

The country flag on patient data pages was displaying at full size (taking up the whole screen) instead of being properly constrained.

## Root Cause

The patient data template (`patient_data.html`) was missing the `country-flag` CSS class that provides proper sizing constraints.

## Solution

### 1. Template Fix

**File**: `ehealth_portal/templates/ehealth_portal/patient_data.html`

- Added `country-flag` class to the flag image element
- This ensures consistent flag styling across all pages

**Before**:

```html
<img src="{% static 'flags/' %}{{ country_code }}.webp" alt="{{ country.name }} flag" class="me-2">
```

**After**:

```html
<img src="{% static 'flags/' %}{{ country_code }}.webp" alt="{{ country.name }} flag" class="country-flag me-2">
```

### 2. SCSS Enhancement

**File**: `static/scss/pages/_patient_data_view.scss`

- Added specific flag styling for patient data pages
- Sized flags at 48px x 32px (smaller than search pages for headers)
- Added responsive sizing for mobile devices
- Included proper alignment and spacing

**New Styles**:

```scss
.page-header {
  .country-flag {
    width: 48px;
    height: 32px;
    border-radius: 4px;
    vertical-align: middle;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    border: 1px solid rgba(0, 0, 0, 0.1);
    object-fit: cover;
    
    @media (max-width: $breakpoint-sm) {
      width: 40px;
      height: 27px;
    }
  }
}
```

## Flag Sizing Across Pages

- **Country Selection**: 60px x 45px (prominent for selection)
- **Patient Search**: 60px x 40px (prominent in header)
- **Patient Data**: 48px x 32px (smaller for content pages)

## Testing Results

✅ Italy: <http://127.0.0.1:8000/portal/country/IT/patient/10/>
✅ Greece: <http://127.0.0.1:8000/portal/country/GR/patient/10/>
✅ Luxembourg: <http://127.0.0.1:8000/portal/country/LU/patient/10/>

All country flags now display at appropriate sizes with proper styling.

## Files Modified

1. `ehealth_portal/templates/ehealth_portal/patient_data.html` - Added CSS class
2. `static/scss/pages/_patient_data_view.scss` - Added flag styling
3. `static/css/main.css` - Compiled SASS output
