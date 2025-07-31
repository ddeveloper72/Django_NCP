# ISM Implementation - CSV-Accurate Configuration

## Overview
Updated ISM (International Search Mask) implementation to accurately reflect the CSV specifications. Each country now shows only the fields they actually require according to the real eHDSI parameters.

## Corrected Country Configurations

### 🇬🇷 Greece (GR)
- **Fields**: 1 (ID only)
- **Patient ID**: National Person Identifier (11 digits)
- **Validation**: `^\d{11}$`
- **Example**: 12345678901
- **Note**: ✅ CORRECTED - No birth date required (was incorrectly added before)

### 🇮🇹 Italy (IT)
- **Fields**: 1 (Codice Fiscale only)
- **Patient ID**: Codice Fiscale
- **Validation**: `^[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]$`
- **Example**: RSSMRA85M01H501Z
- **Note**: ✅ Birth date encoded in Codice Fiscale

### 🇱🇺 Luxembourg (LU)
- **Fields**: 1 (ID only)
- **Patient ID**: National Person Identifier (13 digits)
- **Validation**: `^\d{13}$`
- **Example**: 1234567890123
- **Note**: ✅ CORRECTED - No additional fields per CSV

### 🇱🇻 Latvia (LV)
- **Fields**: 1 (Personal Code only)
- **Patient ID**: Personal Code (DDMMYY-NNNNN)
- **Validation**: `^\d{6}-\d{5}$`
- **Example**: 123456-12345
- **Note**: ✅ Birth date encoded in personal code

### 🇲🇹 Malta (MT)
- **Fields**: 1 (ID only)
- **Patient ID**: Identity Card Number (7 digits + letter)
- **Validation**: `^\d{7}[A-Z]$`
- **Example**: 1234567M
- **Note**: ✅ CORRECTED - No additional fields per CSV

## Enhanced Validation Features

### Client-Side Validation
- **Real-time validation** as user types
- **Country-specific patterns** with helpful error messages
- **Visual feedback** with green/red borders
- **Clear examples** shown in validation messages

### Input Enhancement
- **Monospace font** for ID fields (easier to read)
- **Pattern attributes** for browser validation
- **Debounced validation** to avoid excessive checking
- **Focus/blur validation** for immediate feedback

### Validation Rules Implementation
```javascript
const validationRules = {
    'GR': {
        pattern: /^\d{11}$/,
        message: 'Greek National ID must be exactly 11 digits',
        example: 'e.g., 12345678901'
    },
    'IT': {
        pattern: /^[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]$/,
        message: 'Italian Codice Fiscale must follow the format...',
        example: 'e.g., RSSMRA85M01H501Z'
    },
    // ... other countries
};
```

## Updated Files

### 1. ISM Management Command
**File**: `ehealth_portal/management/commands/create_cda_isms.py`
- ✅ Removed unnecessary fields (birth_date, family_name, given_name, gender)
- ✅ Set accurate `requires_birth_date: false` for all countries
- ✅ Simplified to only create required fields per CSV specifications

### 2. Patient Search Template
**File**: `templates/jinja2/ehealth_portal/patient_search.html`
- ✅ Added comprehensive client-side validation
- ✅ Real-time pattern checking for patient IDs
- ✅ Country-specific error messages with examples
- ✅ Enhanced UX with visual feedback

### 3. SCSS Styling
**File**: `static/scss/pages/_patient_search.scss`
- ✅ Added validation state styling (`.is-valid`, `.is-invalid`)
- ✅ Enhanced patient ID field with monospace font
- ✅ Custom validation error styling with warning icons
- ✅ Improved visual feedback for form states

## Testing Instructions

1. **Visit Country Forms**:
   - Greece: http://127.0.0.1:8000/portal/country/GR/search/
   - Italy: http://127.0.0.1:8000/portal/country/IT/search/
   - Luxembourg: http://127.0.0.1:8000/portal/country/LU/search/

2. **Test Validation**:
   - Try entering invalid IDs (wrong length, format)
   - Notice real-time validation feedback
   - See country-specific error messages
   - Observe visual styling changes

3. **Test Valid IDs**:
   - GR: Enter 11 digits (e.g., 12345678901)
   - IT: Enter valid Codice Fiscale format
   - Notice green validation styling

## Key Improvements

### ✅ Accuracy
- Forms now match actual CSV specifications
- No unnecessary fields cluttering the interface
- Country-specific validation patterns

### ✅ User Experience
- Real-time validation feedback
- Clear error messages with examples
- Visual indicators for valid/invalid input
- Improved typography for ID fields

### ✅ Technical Quality
- Debounced validation to prevent excessive processing
- Pattern-based client-side validation
- Server-side pattern validation backup
- Clean, maintainable code structure

## Validation Examples

### Valid Patient IDs by Country
- **Greece**: `01234567890` (11 digits)
- **Italy**: `RSSMRA85M01H501Z` (Codice Fiscale format)
- **Luxembourg**: `1234567890123` (13 digits)
- **Latvia**: `123456-12345` (DDMMYY-NNNNN format)
- **Malta**: `1234567M` (7 digits + letter)

### Error Messages
- **Greece**: "Greek National ID must be exactly 11 digits (e.g., 12345678901)"
- **Italy**: "Italian Codice Fiscale must follow the format: 6 letters, 2 digits..." 
- **Latvia**: "Latvian Personal Code must follow format: DDMMYY-NNNNN"

## Next Steps

1. **CSV Integration**: Connect to actual CSV file for dynamic configuration
2. **Additional Countries**: Add more countries as needed
3. **Advanced Validation**: Add checksum validation for applicable ID types
4. **Audit Trail**: Log validation attempts for security monitoring

## Summary
The ISM system now provides accurate, CSV-compliant search forms with enhanced validation and user experience. Each country shows only the fields they actually require, with robust client-side validation to ensure correct data structure input.
