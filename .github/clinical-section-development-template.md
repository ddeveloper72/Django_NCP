# Clinical Section Development Prompt Template
## Systematic Approach for Processing Clinical Data Sections

**Version**: 1.0  
**Date**: October 15, 2025  
**Purpose**: Standardized prompt template for documenting and developing clinical section processing

---

## Prompt Template

Use this template when analyzing, documenting, or developing new clinical section processing:

---

### **Clinical Section Analysis Request**

**Section Focus**: [SECTION_NAME] (e.g., Allergies, Medications, Problems)  
**LOINC Code**: [SECTION_CODE] (e.g., 48765-2 for Allergies)  
**Priority**: [HIGH/MEDIUM/LOW]

#### **Phase 1: XML Parsing Documentation**

Walk me through how our data is being parsed from the XML document for the **[SECTION_NAME]** section:

1. **Document the Enhanced CDA XML Parser process**:
   - How the section is discovered using the 8-strategy system
   - XML structure analysis for this specific section type
   - Namespace handling for EU member state compatibility
   - **Critical**: Verify Enhanced CDA XML Parser is extracting clinical codes correctly
   - Test with: `python manage.py shell -c "from enhanced_cda_xml_parser import EnhancedCDAXMLParser; parser.parse_cda_content()"`

2. **Clinical Code Extraction**:
   - Detail the clinical codes found and extracted
   - Document code systems (SNOMED CT, LOINC, ICD, etc.)
   - Show OID mappings for CTS agent integration
   - Include sample clinical codes with their systems
   - **Validation**: Count extracted codes (e.g., "696 clinical codes extracted" confirms parser working)

3. **Date/Time Parsing Implementation**:
   - Document methods for extracting start dates and end dates
   - Show effective time parsing patterns (`<low>`, `<high>` elements)
   - Include date formatting for UI display
   - Handle temporal relationships and ranges
   - **Key Pattern**: Combine narrative text parsing with table data for complete information

4. **XML Content Structure Analysis**:
   - **Primary Data Source**: Check narrative paragraphs first (e.g., `<paragraph>Food allergy to Kiwi fruit, Reaction: Eczema</paragraph>`)
   - **Secondary Data Source**: Extract timing data from table cells (`<td>1990-01-10</td>`)
   - **Namespace Handling**: Use proper XML namespace parsing (`ns = {'hl7': 'urn:hl7-org:v3'}`)
   - **Empty Tables**: Don't rely on table parsing if cells are empty - parse narrative text instead

#### **Phase 2: View Processing Documentation**

Document which view processor method is used and how it processes the information:

1. **CDA Processor Integration**:
   - Which `CDAViewProcessor` methods handle this section
   - How `_enhance_section_with_clinical_codes()` processes the data
   - Template compatibility variable creation
   - **Critical Check**: Verify Enhanced CDA data is being passed correctly to view processor

2. **XML Content Parsing**:
   - How `_parse_xml_content_to_structured_data()` handles this section
   - Specific parsing method (e.g., `_parse_allergy_xml()`)
   - Structured data extraction into `clinical_table` format
   - **Key Pattern**: Method must create proper data structure with `headers` and `rows`

3. **Template Context Building**:
   - How the processed data is passed to the UI context
   - Template variable structure and naming
   - Integration with existing template components
   - **Template Compatibility Requirements**:
     - Headers must use `'label'` property (not `'display'`) for template access pattern `header.label`
     - Rows must have `'data'` wrapper containing objects with `'value'` and `'display_value'` properties
     - Structure: `{'headers': [{'key': 'allergen', 'label': 'Allergen'}], 'rows': [{'data': {'allergen': {'value': 'Kiwi', 'display_value': 'Kiwi Fruit'}}}]}`

4. **Data Structure Validation**:
   - **Test Parsing Method**: Use `processor._parse_[section]_xml(section)` to verify output structure
   - **Verify Headers**: Check headers have correct `'label'` property for template compatibility
   - **Verify Row Data**: Ensure rows contain `'data'` wrapper with proper value objects
   - **Common Pitfall**: Empty table cells - implement narrative text parsing as fallback
   - **Template Compatibility**: Ensure enhanced clinical_arrays are passed to template compatibility layer
   - **Enhanced CDA Integration**: Verify enhanced parsing results reach template through clinical_arrays parameter

#### **Phase 3: UI Integration Documentation**

Document how the information is passed to and displayed in the UI:

1. **Template Rendering**:
   - Which template files handle this section
   - How `clinical_information_content.html` displays the data
   - Table structure and header mappings

2. **CTS Agent Integration**:
   - How clinical codes are formatted for CTS queries
   - Master value catalogue integration for descriptive text
   - Code resolution and display patterns

3. **User Experience**:
   - Clinical workflow optimization
   - Accessibility features and standards
   - Mobile-responsive design considerations

#### **Phase 4: Testing and Validation**

Document the complete testing process:

1. **Enhanced CDA XML Parser Testing**:
   - **Test Command**: `python manage.py shell -c "parser.parse_cda_content(cda_content)"`
   - **Validation**: Confirm clinical codes extracted (e.g., "696 clinical codes extracted")
   - **Section Discovery**: Verify section found with correct LOINC code
   - **Clinical Codes**: Check SNOMED CT, ICD, and other medical terminology extraction

2. **View Processor Method Testing**:
   - **Test Command**: `python manage.py shell -c "processor._parse_[section]_xml(section)"`
   - **Data Structure Validation**: Verify `clinical_table` format with proper headers/rows
   - **Template Compatibility**: Check headers use `'label'` property
   - **Row Data**: Confirm rows have `'data'` wrapper with value objects
   - **Expected Output**: e.g., "4 allergies extracted: Kiwi Fruit, Lactose, Acetylsalicylic Acid, Latex"

3. **Browser Testing**:
   - **Navigation**: Go to Clinical Information tab
   - **Section Header**: Verify shows "✓ X Found" instead of empty/unknown data
   - **Rich Data Display**: Confirm meaningful clinical information instead of "N/A" rows
   - **Template Rendering**: Check proper display of structured clinical data
   - **Success Criteria**: Section displays real clinical data with proper formatting

4. **End-to-End Data Flow Validation**:
   - **Step 1**: Enhanced CDA XML Parser extracts clinical codes ✓
   - **Step 2**: View processor creates template-compatible structure ✓  
   - **Step 3**: Django template renders clinical data properly ✓
   - **Step 4**: Browser displays meaningful clinical information ✓
   - **Failure Pattern Recognition**: If UI shows "Unknown" or "N/A", check template compatibility in Step 2

#### **Phase 5: Methodology Refinement**

Based on the analysis, refine and improve this process guide:

1. **Process Optimization**:
   - Identify bottlenecks or inefficiencies
   - Suggest improvements for code reusability
   - Document best practices discovered
   - **Key Learning**: Always verify Enhanced CDA XML Parser first - if it's working, focus on view processor template compatibility

2. **Pattern Recognition**:
   - Extract reusable patterns for other sections
   - Document common XML structures
   - Create template methods for similar sections
   - **Reusable Patterns Discovered**:
     - Narrative text parsing when table cells are empty
     - Template header structure: `{'key': 'field_name', 'label': 'Display Name'}`
     - Row data wrapper: `{'data': {'field': {'value': 'raw', 'display_value': 'formatted'}}}`
     - XML namespace handling: `ns = {'hl7': 'urn:hl7-org:v3'}`

3. **Documentation Enhancement**:
   - Update the clinical data processing methodology
   - Add section-specific examples
   - Create debugging guidelines
   - **Debugging Flowchart**:
     1. Enhanced CDA working? → If No: Fix parser first
     2. View processor creating data? → If No: Fix template compatibility
     3. Template rendering data? → If No: Check header.label vs header.display
     4. Browser showing data? → If No: Check row.data structure

4. **Common Anti-Patterns to Avoid**:
   - **❌ Don't**: Rely on table parsing if cells are empty
   - **❌ Don't**: Use `'display'` property in headers (templates expect `'label'`)  
   - **❌ Don't**: Create flat row structures (templates expect `row.data.field` pattern)
   - **❌ Don't**: Skip Enhanced CDA validation (always verify parser working first)
   - **❌ Don't**: Forget template compatibility layer - enhanced parsing must reach templates
   - **❌ Don't**: Call template compatibility with original sections when enhanced clinical_arrays exist
   - **✅ Do**: Parse narrative paragraphs for primary data
   - **✅ Do**: Use table data for supplementary information (dates, timing)
   - **✅ Do**: Test each step of data flow independently
   - **✅ Do**: Pass enhanced clinical_arrays to template compatibility when available
   - **✅ Do**: Verify enhanced data overwrites placeholder data in template context

#### **Phase 6: Implementation Guidelines**

Provide concrete implementation steps:

1. **Code Changes Required**:
   - Specific files that need modification
   - New methods to implement
   - Template updates needed

2. **Testing Strategy**:
   - Specific test cases to create
   - Validation criteria
   - Performance benchmarks

3. **Deployment Considerations**:
   - Migration requirements
   - Backward compatibility
   - Production testing approach

---

## Usage Instructions

### For New Clinical Sections

1. Replace `[SECTION_NAME]` with the clinical section you're working on
2. Replace `[SECTION_CODE]` with the appropriate LOINC code
3. Follow each phase systematically
4. Document findings in the clinical data processing methodology
5. Create reusable patterns for future sections

### For Existing Section Analysis

1. Use this template to audit current section processing
2. Identify gaps or improvements needed
3. Document the complete data flow
4. Verify CTS integration completeness
5. Validate UI rendering and accessibility

### For Debugging Issues

1. **Start with Enhanced CDA XML Parser validation**: Verify clinical codes being extracted
2. **Check view processor method**: Ensure parsing method exists and creates proper structure  
3. **Validate template compatibility**: Check headers use `'label'` and rows have `'data'` wrapper
4. **Use Phase 4 testing approaches**: Test each step independently to isolate problems
5. **Apply Phase 5 improvements**: Follow debugging flowchart and avoid common anti-patterns

### **Debugging Decision Tree**

```
UI showing "Unknown" or empty data?
├── YES → Enhanced CDA XML Parser extracting codes?
│   ├── NO → Fix Enhanced CDA XML Parser first
│   └── YES → View processor method implemented?
│       ├── NO → Implement _parse_[section]_xml method
│       └── YES → Method creating clinical_table structure?
│           ├── NO → Fix data structure creation
│           └── YES → Headers using 'label' property?
│               ├── NO → Change 'display' to 'label' 
│               └── YES → Rows have 'data' wrapper?
│                   ├── NO → Add row data wrapper
│                   └── YES → Enhanced parsing reaching template?
│                       ├── NO → Fix template compatibility layer
│                       └── YES → Check XML parsing logic
└── NO → Section working correctly ✓
```

### **Testing Commands Reference**

```bash
# Test Enhanced CDA XML Parser
python manage.py shell -c "
from enhanced_cda_xml_parser import EnhancedCDAXMLParser
parser = EnhancedCDAXMLParser()
result = parser.parse_cda_content(cda_content)
print(f'Clinical codes extracted: {len(result.get(\"clinical_codes\", []))}')
"

# Test view processor method
python manage.py shell -c "
from patient_data.view_processors.cda_processor import CDAViewProcessor
processor = CDAViewProcessor()
result = processor._parse_[section]_xml(section)
print(f'Headers: {len(result[\"clinical_table\"][\"headers\"])}')
print(f'Rows: {len(result[\"clinical_table\"][\"rows\"])}')
"

# Test browser display
# Navigate to Clinical Information tab
# Check section shows "✓ X Found" instead of empty data
```

---

## Example Application

**Section Focus**: Allergies and Adverse Reactions  
**LOINC Code**: 48765-2  
**Priority**: HIGH

This prompt template was used to document the complete allergies section processing, resulting in:

- ✅ **696 clinical codes** extracted from Enhanced CDA XML Parser
- ✅ **SNOMED CT codes** (420134006, 260176001) with proper OID mapping
- ✅ **Structured table data** with headers: Allergen, Type, Date, Status, Severity
- ✅ **Template compatibility** with `clinical_table` structure
- ✅ **CTS integration** with formatted codes for terminology resolution
- ✅ **UI rendering** in beautiful, accessible clinical tables

### **Real-World Case Studies**

#### **Case Study 1: Diana Ferreira Allergies**

**Problem**: Enhanced CDA XML Parser working (696 codes) but UI showing "Allergen (Code: Unknown)"

**Root Cause Analysis**:
1. ✅ Enhanced CDA XML Parser: Working correctly, extracting allergies section 48765-2
2. ❌ View Processor: `_parse_allergy_xml` was empty stub method
3. ❌ Template Compatibility: Headers using `'display'` instead of `'label'`
4. ❌ Data Structure: Missing row `'data'` wrapper for template access

**Solution Implementation**:
1. **Rewrote XML parsing method**: Parse narrative paragraphs instead of empty table cells
   ```python
   # Parse: "Food allergy to Kiwi fruit, Reaction: Eczema"
   paragraphs = section.findall('.//hl7:paragraph', ns)
   ```
2. **Fixed template compatibility**: Changed `'display'` to `'label'` in headers
3. **Added proper data structure**: Created `row['data']` wrapper with value objects
4. **Combined data sources**: Narrative text + table timing data

**Final Result**: 4 allergies displayed with complete clinical data
- Kiwi Fruit (Food allergy) → Eczema [since 1990-01-10]
- Lactose (Food allergy) → Diarrhea [since 1983-05-05]  
- Acetylsalicylic Acid (Medication allergy) → Asthma [from 1994 until 2010]
- Latex (Allergy) → Urticaria [since 1990-01-10]

#### **Case Study 2: Diana Ferreira Medical Problems**

**Problem**: Enhanced CDA XML Parser working (6 real conditions) but UI showing "Medical Problem, Clinical finding, -, -, -" placeholder data

**Root Cause Analysis**:
1. ✅ Enhanced CDA XML Parser: Working correctly, extracting problems with structured entry parsing
2. ✅ View Processor: `_parse_problem_list_xml` correctly parsing 6 real conditions 
3. ❌ Template Compatibility: Enhanced clinical_arrays not reaching template compatibility layer
4. ❌ Data Flow: Original sections passed to template instead of enhanced clinical_arrays

**Solution Implementation**:
1. **Enhanced Template Compatibility**: Modified `_add_template_compatibility_variables` to accept enhanced clinical_arrays parameter
   ```python
   def _add_template_compatibility_variables(self, context, sections, enhanced_clinical_arrays=None):
   ```
2. **Data Flow Priority**: Use enhanced clinical_arrays when available, fall back to context data
3. **Integration Fix**: Pass enhanced clinical_arrays from _enhance_sections_with_updated_parsing method
4. **Template Context**: Enhanced parsing results properly override placeholder data

**Final Result**: 6 real medical problems + 1 remaining placeholder displayed correctly
- Predominantly allergic asthma (Clinical finding, Active)
- Postprocedural hypothyroidism (Clinical finding, Active)  
- Other specified cardiac arrhythmias (Clinical finding, Active)
- Type 2 diabetes mellitus (Clinical finding, Active)
- Severe pre-eclampsia (Problem, Active, Severe)
- Acute tubulo-interstitial nephritis (Problem, Active, Moderate To Severe)

**Key Learning**: Template compatibility layer must receive enhanced parsing results, not original section data.

---

## Integration with Development Workflow

### Git Commit Pattern

When implementing using this methodology:

```bash
git commit -m "feat(clinical): implement [SECTION_NAME] processing using systematic methodology"
git commit -m "docs(clinical): document [SECTION_NAME] data flow and XML parsing"
git commit -m "test(clinical): add comprehensive testing for [SECTION_NAME] section"
```

### Documentation Updates

After each section implementation:

1. Update `clinical-data-processing-methodology.md`
2. Add section-specific examples
3. Document reusable patterns
4. Update testing procedures

### Code Review Checklist

- [ ] **Enhanced CDA XML Parser**: Clinical codes being extracted correctly
- [ ] **XML parsing**: Follows 8-strategy discovery system
- [ ] **Clinical codes**: Properly extracted with OIDs for CTS integration
- [ ] **Date/time parsing**: Handles all temporal patterns from tables and narrative
- [ ] **View processor integration**: Method implemented and creates clinical_table structure
- [ ] **Template compatibility**: Headers use `'label'` property, rows have `'data'` wrapper
- [ ] **Data structure**: Objects have `'value'` and `'display_value'` properties
- [ ] **XML parsing logic**: Handles narrative paragraphs when table cells empty
- [ ] **CTS integration**: Clinical codes formatted for terminology resolution
- [ ] **Testing coverage**: Enhanced CDA → view processor → template → browser tested
- [ ] **Browser validation**: Section displays "✓ X Found" with meaningful clinical data
- [ ] **Documentation**: Updated with section-specific patterns and examples

---

## Success Metrics

The methodology is successful when:

- ✅ Clinical data extracted accurately from CDA XML
- ✅ All clinical codes available for CTS integration
- ✅ Structured data renders in beautiful UI tables
- ✅ Date/time information properly formatted
- ✅ Template compatibility maintained
- ✅ Testing validates complete data flow
- ✅ Documentation enables future development

---

**Note**: This template embodies the systematic approach that successfully resolved the clinical sections rendering issues, transforming raw HTML markup into beautiful, structured clinical data displays with complete CTS integration support.