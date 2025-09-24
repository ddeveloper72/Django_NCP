# ID Architecture Analysis & Correction Plan

## Current Architecture Understanding (CORRECTED)

### Three-Tier ID System

#### 1. Patient ID (`patient_id`)

- **Source**: CDA XML document
- **Examples**: `9999002M`, `aGVhbHRoY2FyZUlkMTIz`
- **Purpose**: Identifies patient in healthcare system/government records
- **Usage**: Internal processing, CDA parsing, display to healthcare professionals
- **Privacy**: MUST NOT appear in URLs (GDPR/HIPAA violation)

#### 2. Database ID (`database_id`)

- **Source**: Auto-generated primary key when CDA metadata is stored
- **Examples**: `418650`, `221935`
- **Purpose**: Internal database record identification
- **Usage**: Database queries, temporary CDA storage
- **Privacy**: Internal use only, not exposed to users

#### 3. Session ID (`session_id`)

- **Source**: Generated for each patient processing session
- **Examples**: `2771684472`, `2521029704`
- **Purpose**: URL routing, session management, privacy-compliant navigation
- **Usage**: All user-facing URLs, session data keys
- **Privacy**: Safe for URLs - no patient data exposure

## Data Flow Architecture

```
ISM Search Form → Country + Patient ID Input → CDA Retrieval
                                                     ↓
Patient ID (from CDA XML) → Database Storage → Database ID (auto-generated)
                                                     ↓
Session Management → Session ID (generated) → URL Routing
```

## Current Problems Identified

### 1. URL Parameter Naming Confusion

- All URLs use `<str:patient_id>` parameter name
- But the actual values should be session IDs for privacy
- Creates confusion between patient_id (from CDA) vs URL parameter

### 2. View Function Inconsistencies

- 19 view functions accept `patient_id` parameter from URLs
- But they expect this to be session_id values
- Inconsistent handling of the three ID types in context

### 3. Template Context Variable Mixing

- `patient_id` used for both session routing AND CDA patient identification
- `patient_identity.patient_id` sometimes contains session_id, sometimes patient_id
- No clear separation between display data vs URL routing data

### 4. Session Data Key Inconsistencies

- Session keys use `patient_match_{session_id}` pattern
- But views may not consistently use session_id to look up data
- Potential session data mismatches

## Correction Plan

### Phase 1: URL Pattern Correction

- [ ] Rename URL parameter from `patient_id` to `session_id` for clarity
- [ ] Update all 19 view functions to accept `session_id` parameter
- [ ] Ensure all URLs use session_id values, never patient_id values

### Phase 2: Context Variable Standardization

- [ ] Standardize context variables:
  - `session_id`: For URL routing and session management
  - `patient_id`: For CDA patient identification (from XML)
  - `database_id`: For database record identification (if needed)
- [ ] Update all view functions to pass correct context variables

### Phase 3: Template Updates

- [ ] Update all templates to use `session_id` for URL routing
- [ ] Use `patient_id` only for displaying patient information
- [ ] Ensure clear separation between routing data and display data

### Phase 4: Session Management Cleanup

- [ ] Verify session data keys consistently use session_id
- [ ] Ensure view functions correctly look up session data using session_id
- [ ] Test session data integrity across all user flows

### Phase 5: Testing & Validation

- [ ] Create test suite for ID handling
- [ ] Test patient search → CDA retrieval → session creation flow
- [ ] Verify no patient_id values appear in any URLs
- [ ] Test back button navigation and session persistence

## Impact Assessment

### High Impact Changes Required

1. **URLs**: 20+ URL patterns need parameter renaming
2. **Views**: 19 view functions need parameter name changes
3. **Templates**: All patient-related templates need URL pattern updates
4. **Session Logic**: Session data lookup patterns may need correction

### Risk Areas

1. **Breaking Changes**: URL parameter renaming breaks existing bookmarks/links
2. **Data Integrity**: Session data mismatches if lookup keys are wrong
3. **Testing Required**: Complex three-tier ID system needs comprehensive testing

## Next Steps

1. **Start with URL pattern analysis** - map current parameter usage
2. **Identify session_id vs patient_id confusion points** in view functions
3. **Create migration plan** for URL parameter renaming
4. **Implement systematic correction** with comprehensive testing

## Date Created

September 24, 2025

## Status

Analysis Phase - Architecture correction in progress
