# CDA Procedure Architecture Analysis

**Investigation Date**: October 30, 2025  
**Purpose**: Understand CDA procedure structure across EU member states  
**Hypothesis**: Procedures use dual-layer architecture with narrative (local language) + structured codes (for CTS translation)

---

## CDA Standard Architecture for Procedures

### Two-Layer Structure

Every CDA procedure section contains:

1. **Narrative Section** (`<text>`) - Human-readable, local language
2. **Structured Section** (`<entry>`) - Machine-readable, with SNOMED CT codes

---

## Portuguese Patient Example (Diana Ross - 7052820059)

**File**: `test_data/eu_member_states/PT/2-1234-W7.xml`

### Narrative Layer (Lines 1186-1187)
```xml
<text>
    <paragraph ID="pro-1">Implantation of heart assist system, 2014-10-20</paragraph>
    <paragraph ID="pro-2">Cesarean section, 2012-04-14</paragraph>
    <paragraph ID="pro-3">Thyroidectomy, 1997-06-05</paragraph>
    <table>
        <tbody>
            <tr ID="pro-1a">
                <td><content ID="code-22" language="xx-XX">Implantation of heart assist system</content></td>
                <td>2014-10-20</td>
            </tr>
            <!-- ... more procedures ... -->
        </tbody>
    </table>
</text>
```

**Key Observations**:
- `ID="pro-1"` - Links to structured entry
- `ID="code-22"` - Links to code originalText
- Text in English (but could be Portuguese in production)
- Human-readable format for clinical display

### Structured Layer (Lines 1190-1210)
```xml
<entry>
    <procedure classCode="PROC" moodCode="EVN">
        <templateId root="1.3.6.1.4.1.12559.11.10.1.3.1.3.26"/>
        <id root="2.999.3.1"/>
        <code codeSystem="2.16.840.1.113883.6.96" code="64253000">
            <originalText><reference value="#code-22"/></originalText>
        </code>
        <text><reference value="#pro-1"/></text>
        <statusCode code="completed"/>
        <effectiveTime value="20141020"/>
        <targetSiteCode code="76552005" codeSystem="2.16.840.1.113883.6.96" displayName="skin structure of shoulder">
            <qualifier>
                <name code="272741003" displayName="Laterality"/>
                <value code="7771000" displayName="Left"/>
            </qualifier>
        </targetSiteCode>
    </procedure>
</entry>
```

**Key Observations**:
- `code="64253000"` - SNOMED CT code (universal)
- `codeSystem="2.16.840.1.113883.6.96"` - SNOMED CT identifier
- `<originalText><reference value="#code-22"/>` - Links back to narrative
- `<text><reference value="#pro-1"/>` - Links to full description
- **NO displayName in `<code>` element** - Intentional! Should come from CTS

**Complete Procedure Codes**:
1. **Procedure 1**: Code `64253000` (Implantation of heart assist system)
2. **Procedure 2**: Code `11466000` (Cesarean section)
3. **Procedure 3**: Code `13619001` (Thyroidectomy)

---

## Maltese Patient Example (Mario Borg - 9999002M)

**File**: `test_data/eu_member_states/MT/Mario_Borg_9999002M_3.xml`

### Narrative Layer (Lines 340-354)
```xml
<text>
    <table border="1">
        <thead>
            <tr>
                <th>Procedure date</th>
                <th>Description</th>
            </tr>
        </thead>
        <tbody>
            <tr ID="proc.1">
                <td>11-Jan-2018</td>
                <td>Right inguinal hernia repair</td>
            </tr>
        </tbody>
    </table>
</text>
```

**Key Observations**:
- `ID="proc.1"` - Links to structured entry
- Text in English (local language for Malta)
- Simpler structure than Portuguese example

### Structured Layer (Lines 357-377)
```xml
<entry>
    <procedure classCode="PROC" moodCode="EVN">
        <templateId root="1.3.6.1.4.1.19376.1.5.3.1.4.19"/>
        <templateId root="1.3.6.1.4.1.12559.11.10.1.3.1.3.26"/>
        <id extension="proc.1" root="2.16.470.1.100.1.2.1000.990.1.9"/>
        <code code="44558001" codeSystem="2.16.840.1.113883.6.96" codeSystemName="SNOMED CT" codeSystemVersion="2022-07-31" displayName="Repair of inguinal hernia">
            <originalText mediaType="text/xml">
                <reference value="#proc.1"/>
            </originalText>
            <translation code="44558001" codeSystem="2.16.840.1.113883.6.96" codeSystemName="SNOMED CT" displayName="Right inguinal hernia repair"/>
        </code>
        <text>
            <reference value="#proc.1"/>
        </text>
        <statusCode code="completed"/>
        <effectiveTime>
            <low value="20180111000000+0000"/>
        </effectiveTime>
    </procedure>
</entry>
```

**Key Observations**:
- `code="44558001"` - SNOMED CT code
- **HAS displayName in `<code>` element** - "Repair of inguinal hernia"
- `<translation>` element with different displayName - "Right inguinal hernia repair"
- Links back to narrative via `<originalText>` and `<text>`

**Difference from Portuguese**: Malta includes `displayName` attribute in code element

---

## Comparison: Portuguese vs Maltese CDA Structure

| Feature | Portuguese (PT) | Maltese (MT) |
|---------|----------------|--------------|
| **SNOMED CT codes** | ✅ Yes | ✅ Yes |
| **Code system OID** | ✅ 2.16.840.1.113883.6.96 | ✅ 2.16.840.1.113883.6.96 |
| **Narrative text** | ✅ English (test data) | ✅ English |
| **displayName in `<code>`** | ❌ No | ✅ Yes |
| **`<translation>` element** | ❌ No | ✅ Yes |
| **`<targetSiteCode>`** | ✅ Yes (with laterality) | ❌ No |
| **originalText reference** | ✅ Yes | ✅ Yes |

---

## Implications for Django_NCP Architecture

### Current State: Dual Extraction Problem

**Pipeline 1: ProceduresSectionService** (Specialized)
- Extracts from `<text>` narrative section
- Gets: ✅ Procedure names
- Gets: ❌ Procedure codes (missing extraction logic)

**Pipeline 2: EnhancedCDAXMLParser** (Generic)
- Extracts from `<code>` structured section
- Gets: ✅ Procedure codes (as dict: `{code: "64253000", codeSystem: "..."}`)
- Gets: ❌ Procedure names (intentionally - should come from CTS)

**Result**: 6 procedures in `clinical_arrays` (3 from each pipeline)

### Correct Workflow Design

**Option A: CTS Integration (Recommended)**
1. Extract SNOMED code from `<code>` element → `64253000`
2. Send code to CTS agent → Request translation
3. CTS returns: "Implantation of heart assist system" (in clinician's language)
4. Display translated name in UI

**Option B: Fallback to Narrative (Temporary)**
1. Extract SNOMED code from `<code>` element → `64253000`
2. Extract displayName if present → Use as fallback
3. If no displayName, extract from `<text>` reference → Parse narrative
4. Display name with flag indicating source (CTS vs narrative vs fallback)

### Recommended Fix: Single Source of Truth

**Short-term (Tonight's Fix)**:
- Filter out procedures without names in `comprehensive_clinical_data_service.py` (line 629)
- Keep ProceduresSectionService output (has names)
- Discard EnhancedCDAXMLParser output (no names)

**Medium-term (Next Sprint)**:
- Fix ProceduresSectionService to extract BOTH names AND codes
- Add code extraction logic to parse `<code>` element from structured entries
- Remove EnhancedCDAXMLParser procedure extraction (use specialized service only)

**Long-term (Production)**:
- Integrate CTS agent for procedure name translation
- Use SNOMED codes as primary identifier
- Fetch displayNames dynamically based on clinician's language preference
- Cache translations for performance

---

## CTS Integration Requirements

### What is CTS?

**Concept Translation Service (CTS)** - European eHealth service for translating clinical codes:
- Input: SNOMED CT code + target language
- Output: Translated display name
- Example: Code `64253000` + language `pt-PT` → "Implantação de sistema de assistência cardíaca"

### Django_NCP CTS Implementation

**Required Changes**:
1. **Service Layer**: Create `CTSTranslationService`
   - Method: `translate_snomed_code(code: str, language: str) -> str`
   - Caching: Store translations in database for performance
   - Fallback: Use narrative text if CTS unavailable

2. **Procedure Model**: Add fields
   - `snomed_code` (CharField) - Store SNOMED CT code
   - `snomed_display_name` (TextField) - Store CTS translation
   - `narrative_text` (TextField) - Store original narrative
   - `translation_language` (CharField) - Store language code

3. **Template Updates**: Show translation metadata
   - Display: "Implantation of heart assist system"
   - Badge: "Translated from SNOMED 64253000"
   - Tooltip: "Original: [Portuguese text]"

---

## Testing Strategy

### Test Cases Required

**Test 1: Portuguese Procedures (PT)**
- Patient: Diana Ross (7052820059)
- Expected: 3 procedures with SNOMED codes
- Verify: `64253000`, `11466000`, `13619001` extracted correctly

**Test 2: Maltese Procedures (MT)**
- Patient: Mario Borg (9999002M)
- Expected: 1 procedure with displayName
- Verify: `44558001` with "Repair of inguinal hernia"

**Test 3: Missing displayName**
- Test: Procedures without `displayName` attribute
- Expected: Fallback to narrative text extraction
- Verify: No "Unknown Procedure" entries

**Test 4: CTS Integration**
- Test: Translate SNOMED codes via CTS
- Expected: Display names in clinician's language
- Verify: Cache working, fallback to narrative if CTS fails

---

## Conclusion: Hypothesis CONFIRMED ✅

**Your hypothesis was absolutely correct**:

1. **CDA uses dual-layer architecture**:
   - Narrative layer (`<text>`) - Local language, human-readable
   - Structured layer (`<entry>`) - SNOMED codes, machine-readable

2. **SNOMED codes are universal**:
   - Same code system across all EU member states
   - `2.16.840.1.113883.6.96` = SNOMED CT OID

3. **displayName is optional**:
   - Portuguese CDAs: No displayName (rely on CTS)
   - Maltese CDAs: Include displayName (convenience)

4. **CTS is the intended translation mechanism**:
   - Codes should be translated dynamically
   - Enables multi-language support
   - Respects clinician's language preference

**Next Steps**:
1. Apply tonight's fix (filter procedures without names)
2. Fix ProceduresSectionService to extract codes from structured entries
3. Design CTS integration architecture
4. Implement CTS service layer for procedure translation

---

**Related Files**:
- `.github/RESTORE_POINT_2025-10-30.md` - Current debugging session
- `procedures_service.py` - Specialized procedure extraction
- `comprehensive_clinical_data_service.py` - Data merging logic
- `clinical_field_mapper.py` - Field mapping and normalization
- `procedures_section_new.html` - UI template

**References**:
- SNOMED CT: https://www.snomed.org/
- European eHealth CTS: https://ehealthsuisse.art-decor.org/
- CDA R2 Standard: http://www.hl7.org/implement/standards/product_brief.cfm?product_id=7
