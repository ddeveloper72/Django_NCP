# Enhanced Patient CDA Template Refactoring Specification

## 1. Summary

Complete refactoring of `templates/patient_data/enhanced_patient_cda.html` to achieve full Django_NCP specification compliance by eliminating inline CSS, simplifying template logic, and enhancing maintainability.

**Current State**: Critical template with 900+ lines of inline CSS violating core spec requirements
**Target State**: Spec-compliant template with externalized assets and simplified logic

## 2. Requirements

### 2.1 Primary Compliance Issues (CRITICAL)

- **No inline CSS in HTML templates** - VIOLATED: 900+ lines of CSS in `<style>` blocks
- **Keep Django templates simple** - VIOLATED: Complex conditional logic and extensive styling
- **Use reusable view classes and methods** - REVIEW NEEDED: Template complexity suggests view logic needed
- **Follow healthcare organisation colour palette** - AUDIT NEEDED: Color compliance verification required

### 2.2 Secondary Issues (HIGH PRIORITY)

- **HTML validation** - Minor breadcrumb structure warning (line 992)
- **Template maintainability** - Large monolithic template needs modularization
- **Mobile-first design** - CSS responsive design needs external organization

### 2.3 Compliant Areas (MAINTAIN)

- **External JavaScript** - ✅ Bootstrap and enhanced_cda.js properly externalized
- **Django template engine** - ✅ No Jinja2 syntax detected
- **Template inheritance** - ✅ Properly extends base.html
- **Security considerations** - ✅ CSRF and Django template tags properly used

## 3. System Design Impact

### 3.1 File Structure Changes

```
Before:
templates/patient_data/enhanced_patient_cda.html (1190 lines, 900+ CSS)

After:
templates/patient_data/enhanced_patient_cda.html (simplified, ~300 lines)
static/scss/pages/_enhanced_cda.scss (new, organized CSS)
static/scss/components/_cda_tabs.scss (new, tab navigation)
static/scss/components/_patient_cards.scss (new, patient info cards)
static/scss/components/_clinical_sections.scss (new, clinical styling)
```

### 3.2 CSS Architecture

```
static/scss/pages/_enhanced_cda.scss
├── @import 'components/cda_tabs'
├── @import 'components/patient_cards'
├── @import 'components/clinical_sections'
├── @import 'components/contact_cards'
├── @import 'components/document_info'
└── @import 'components/navigation_tabs'
```

### 3.3 Template Simplification

- **Move complex conditionals** to view context processors
- **Extract reusable components** into separate template includes
- **Simplify display logic** by preprocessing data in Python views

## 4. Implementation Tasks

### Phase 1: CSS Externalization (IMMEDIATE PRIORITY)

1. **Create SASS file structure**

   ```bash
   touch static/scss/pages/_enhanced_cda.scss
   touch static/scss/components/_cda_tabs.scss
   touch static/scss/components/_patient_cards.scss
   touch static/scss/components/_clinical_sections.scss
   touch static/scss/components/_contact_cards.scss
   touch static/scss/components/_document_info.scss
   touch static/scss/components/_navigation_tabs.scss
   ```

2. **Extract and organize CSS by functional areas**
   - Clinical tab content styles → `_cda_tabs.scss`
   - Patient overview and headers → `_patient_cards.scss`
   - Contact and administrative styling → `_contact_cards.scss`
   - Document information styling → `_document_info.scss`
   - Navigation tab enhancements → `_navigation_tabs.scss`
   - Layout and responsive controls → `_enhanced_cda.scss`

3. **Healthcare Organisation Colour Palette Audit**
   - Audit all colour values against healthcare organisation palette
   - Replace hardcoded colours with SASS variables
   - Document colour usage and compliance

4. **Remove inline CSS from template**
   - Delete `<style>` blocks from template
   - Replace with external CSS references
   - Verify visual consistency after extraction

### Phase 2: Template Logic Simplification (HIGH PRIORITY)

1. **Identify complex template logic**
   - Patient identity handling and display logic
   - Source country badge logic and styling
   - Translation quality assessment display
   - Tab content switching logic

2. **Create view context processors**

   ```python
   # patient_data/context_processors.py
   def enhanced_cda_context(request, patient_data):
       return {
           'patient_display_name': format_patient_name(patient_data),
           'country_badge_class': get_country_badge_class(patient_data.source_country),
           'translation_badge_class': get_translation_badge_class(patient_data.translation_quality),
           'tab_configuration': get_tab_configuration(patient_data),
       }
   ```

3. **Extract reusable template components**

   ```
   templates/patient_data/components/
   ├── patient_header_card.html
   ├── country_source_badge.html
   ├── translation_quality_badge.html
   ├── patient_navigation_tabs.html
   └── clinical_tab_content.html
   ```

### Phase 3: HTML Structure Optimization (MEDIUM PRIORITY)

1. **Fix HTML validation issues**
   - Correct breadcrumb list structure (line 992)
   - Ensure semantic HTML compliance
   - Verify ARIA accessibility attributes

2. **Optimize template structure**
   - Reduce template size to ~300 lines
   - Improve template readability and maintainability
   - Enhance template documentation

### Phase 4: Testing and Validation (ONGOING)

1. **Visual regression testing**
   - Compare before/after screenshots
   - Test responsive breakpoints
   - Verify cross-browser compatibility

2. **Functional testing**
   - Ensure CDA document viewing works (patient ID 4190998075)
   - Test tab navigation functionality
   - Verify patient data display accuracy

3. **Performance testing**
   - Measure CSS load times before/after
   - Optimize SASS compilation
   - Verify static asset caching

## 5. Risk Mitigation

### 5.1 Breaking Changes

- **CSS extraction** could affect visual appearance
- **Template logic changes** might impact functionality
- **Component extraction** could introduce rendering issues

### 5.2 Mitigation Strategies

1. **Incremental approach** - Extract CSS in small, testable chunks
2. **Visual comparison** - Screenshot testing before/after each change
3. **Functional testing** - Verify CDA viewing functionality at each step
4. **Git workflow** - Small, focused commits with easy rollback capability

### 5.3 Rollback Plan

- Each phase committed separately with conventional commit messages
- CSS extraction can be quickly reverted if visual issues arise
- Template logic changes isolated to specific components

## 6. Success Criteria

### 6.1 Specification Compliance

- ✅ **No inline CSS** - All CSS moved to external SASS files
- ✅ **Simple templates** - Template reduced to ~300 lines, logic in Python
- ✅ **Healthcare colour compliance** - All colours verified against healthcare organisation palette
- ✅ **HTML validation** - No validation warnings or errors

### 6.2 Technical Metrics

- **Template size**: Reduced from 1190 to ~300 lines
- **CSS organization**: 900+ lines organized into 6 focused SASS files
- **Load performance**: No regression in page load times
- **Maintainability**: Clear separation of concerns between CSS, template, and logic

### 6.3 Functional Requirements

- **CDA document viewing** works for all patient IDs including 4190998075
- **Visual consistency** maintained across all browsers and devices
- **Tab navigation** functionality preserved
- **Patient data display** accuracy maintained

## 7. Timeline and Dependencies

### Week 1: CSS Externalization

- **Day 1-2**: Create SASS file structure, extract basic layout CSS
- **Day 3-4**: Extract component-specific CSS (tabs, cards, forms)
- **Day 5**: HSE color audit and compliance fixes

### Week 2: Template Simplification

- **Day 1-2**: Create context processors and extract template logic
- **Day 3-4**: Create reusable template components
- **Day 5**: HTML validation fixes and optimization

### Week 3: Testing and Refinement

- **Day 1-2**: Visual regression testing and fixes
- **Day 3-4**: Functional testing and performance optimization
- **Day 5**: Documentation and final validation

### Dependencies

- **SASS compilation** must be working (✅ already operational)
- **Git workflow** established (✅ implemented)
- **Test patient data** available for validation (✅ patient ID 4190998075)

## 8. Post-Implementation

### 8.1 Documentation Updates

- Update template documentation with new structure
- Document SASS component organization
- Create template usage guidelines

### 8.2 Team Knowledge Transfer

- Document refactoring decisions and rationale
- Create guidelines for future template development
- Establish CSS architecture patterns for other templates

### 8.3 Future Enhancements

- Apply same refactoring approach to other large templates
- Establish automated CSS/template compliance checking
- Create reusable component library for patient data templates

---

**Status**: Ready for implementation
**Owner**: Django_NCP Development Team
**Created**: September 21, 2025
**Last Updated**: September 21, 2025
