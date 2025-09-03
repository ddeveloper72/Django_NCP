# Medical Code System Reference

## Supported Code Systems

This document lists the medical code systems supported by the Django NCP system, including their OIDs (Object Identifiers) and display badges.

### International Standards

| Code System | OID | Badge Color | Description |
|-------------|-----|-------------|-------------|
| **SNOMED CT** | `2.16.840.1.113883.6.96` | 🔵 Blue (Primary) | Systematized Nomenclature of Medicine Clinical Terms |
| **LOINC** | `2.16.840.1.113883.6.1` | 🟢 Green (Success) | Logical Observation Identifiers Names and Codes |
| **RxNorm** | `2.16.840.1.113883.6.88` | 🟠 Orange (Warning) | Normalized drug names |
| **ICD-10-CM** | `2.16.840.1.113883.6.3` | 🔴 Red (Danger) | International Classification of Diseases, 10th Revision, Clinical Modification |
| **ICD-10-PCS** | `2.16.840.1.113883.6.4` | 🔴 Red (Danger) | ICD-10 Procedure Coding System |
| **UCUM** | `2.16.840.1.113883.5.83` | 🔵 Light Blue (Info) | Unified Code for Units of Measure |
| **ATC** | `2.16.840.1.113883.6.73` | ⚫ Dark | Anatomical Therapeutic Chemical Classification |

### Legacy Systems

| Code System | OID | Badge Color | Description |
|-------------|-----|-------------|-------------|
| **ICD-9-CM** | `2.16.840.1.113883.6.103` | ⚪ Gray (Secondary) | ICD-9 Clinical Modification |
| **ICD-9-PCS** | `2.16.840.1.113883.6.104` | ⚪ Gray (Secondary) | ICD-9 Procedure Coding System |

### European/WHO Standards

| Code System | OID | Badge Color | Description |
|-------------|-----|-------------|-------------|
| **ICD-10-WHO** | `2.16.840.1.113883.6.14` | 🔴 Red (Danger) | WHO International Classification of Diseases |
| **ICD-10 FR** | `1.2.250.1.213.1.1.4.1` | 🔴 Red (Danger) | French ICD-10 Classification |
| **EDQM** | `2.16.840.1.113883.3.989.12.2` | 🔵 Light Blue (Info) | European Directorate for the Quality of Medicines |
| **ISO 11238** | `2.16.840.1.113883.6.259` | ⚪ Gray (Secondary) | Substance identification codes |

## Usage in CDA Documents

### Code Structure

```xml
<code code="112746006" 
      codeSystem="2.16.840.1.113883.6.96" 
      displayName="Operative procedure on hand"/>
```

### System Inference

When a CDA document contains only the OID (`codeSystem`), the system automatically infers:

- `2.16.840.1.113883.6.96` → **SNOMED CT** (Blue badge)
- Display: `112746006` <Badge: SNOMED CT>

### Badge Display

The system displays codes in a minimal format:

- **Code Value**: The actual code (e.g., `112746006`)
- **System Badge**: Colored badge indicating the code system
- **No duplicate text**: Avoids showing procedure names twice

## Implementation Details

### Code System Recognition

1. **Primary**: Uses OID from `codeSystem` attribute
2. **Fallback**: Accepts readable system names  
3. **Default**: Unknown systems get gray outline badge

### Badge Colors

- **Blue (Primary)**: SNOMED CT - Most common clinical terminology
- **Green (Success)**: LOINC - Laboratory and observation codes
- **Orange (Warning)**: RxNorm - Drug terminology
- **Red (Danger)**: ICD codes - Diagnosis and procedure classifications
- **Gray (Secondary)**: Legacy and substance codes
- **Light Blue (Info)**: European standards and units

### Multi-Country Support

The system handles CDAs from different countries by:

- Recognizing international OID standards
- Supporting country-specific extensions (e.g., French ICD-10)
- Providing fallback display for unknown systems
- Maintaining consistent badge sizing across all systems

## Example Displays

| Code | System OID | Display |
|------|------------|---------|
| `112746006` | `2.16.840.1.113883.6.96` | `112746006` <Badge: SNOMED CT> |
| `86273004` | `2.16.840.1.113883.6.96` | `86273004` <Badge: SNOMED CT> |
| `33747-0` | `2.16.840.1.113883.6.1` | `33747-0` <Badge: LOINC> |
| `Z51.1` | `2.16.840.1.113883.6.3` | `Z51.1` <Badge: ICD-10-CM> |
