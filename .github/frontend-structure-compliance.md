# Feature Spec: Frontend Structure Compliance Refac  │   ├── _variables.scss (Healthcare colours, breakpoints)

  │   ├── _mixins.scss (Reusable SASS patterns)ring

## 1. Summary

A comprehensive refactoring of Django_NCP templates to achieve 100% compliance with the Original Spec's frontend requirements. This involves extracting all inline CSS and JavaScript from HTML templates and implementing a proper SASS/JS architecture following the **SCSS Architecture Standards**.

## 2. Requirements

### Original Spec Compliance

- **No inline CSS** in HTML templates (remove all `<style>` blocks and `style=""` attributes)
- **No JavaScript** in HTML templates (remove all `<script>` blocks and event handlers)
- **SASS compilation** from `/static/scss/` to `/static/css/`
- **External JS** stored in `/static/js/`
- **Mobile-first** UI design maintained
- **Healthcare colour palette** implementation
- **Maintainability** through reusable CSS classes and JS modules
- **Dynamic, modular, and reusable** SCSS components (see [SCSS Architecture Standards](./scss-architecture-standards.md))

### SCSS Architecture Requirements

- **Context-Aware Components**: All components must adapt to light/dark backgrounds automatically
- **Modular Design**: Single responsibility principle, atomic components, layered architecture
- **Zero Duplication**: DRY principle, centralized patterns, systematic overrides only
- **Variable-Driven**: All design tokens as variables, no magic numbers
- **Mixin-Based Logic**: Complex patterns as reusable mixins
- **Semantic Naming**: BEM methodology for component naming

### Security Requirements

- **No personal names** in code/comments/docs
- **CSRF protection** maintained in forms
- **Session-based** authentication preserved

## 3. System Design

### Current State (Violations)

- 50+ templates with inline CSS (`<style>` blocks, `style=""` attributes)
- 20+ templates with inline JavaScript (`<script>` blocks, event handlers)
- Bootstrap CSS framework (needs replacement with custom SASS)
- Mixed styling approaches causing maintenance issues

### Target State (Spec Compliant)

- **SASS Architecture:**

  ```
  /static/scss/
  ├── main.scss (imports all modules)
  ├── utils/
  │   ├── _variables.scss (HSE colors, breakpoints)
  │   └── _mixins.scss (reusable patterns)
  ├── components/
  │   ├── _buttons.scss
  │   ├── _cards.scss
  │   ├── _forms.scss
  │   └── _modals.scss
  ├── layouts/
  │   ├── _header.scss
  │   ├── _footer.scss
  │   └── _grid.scss
  └── pages/
      ├── _admin.scss
      ├── _patient-data.scss
      └── _smp-client.scss
  ```

- **JavaScript Architecture:**

  ```
  /static/js/
  ├── core/
  │   ├── utils.js (common utilities)
  │   └── api.js (AJAX helpers)
  ├── components/
  │   ├── modal.js
  │   ├── pdf-viewer.js
  │   └── forms.js
  └── pages/
      ├── patient-search.js
      ├── smp-dashboard.js
      └── admin-import.js
  ```

### Healthcare Organisation Color Palette Implementation

```scss
// Healthcare Organisation Official Colours
$hco-blue: #007cba;
$hco-light-blue: #5fc2e7;
$hco-green: #4caf50;
$hco-orange: #ff9800;
$hco-red: #f44336;
$hco-dark-grey: #2c3e50;
$hco-light-grey: #ecf0f1;
$hco-white: #ffffff;
```

## 4. Implementation Tasks - Prioritized Phases

### 🎯 **Phase 1: Foundation & Infrastructure (Highest Priority)**

**Goal:** Set up SASS architecture and healthcare colour system
**Scope:** Minimal template changes, foundational work
**Timeline:** 1-2 sessions

1. Create SASS directory structure in `/static/scss/`
2. Implement healthcare colour palette in `_variables.scss`
3. Create mobile-first mixins and utility classes
4. Set up base typography and layout systems
5. Test SASS compilation pipeline

**Success Criteria:** Clean SASS architecture compiling successfully

---

### 🔥 **Phase 2: Critical Admin Templates (High Priority)**

**Goal:** Fix admin interface compliance violations
**Scope:** 3-4 admin templates with heavy inline styling
**Timeline:** 1-2 sessions

**Templates to fix:**

- `templates/admin/login.html` - Heavy `<style>` block
- `templates/admin/index.html` - Custom dashboard styling
- `smp_client/templates/admin/smp_client/signingcertificate/change_form.html` - Complex form styling

**Approach:**

1. Extract inline styles to `pages/_admin.scss`
2. Implement healthcare branding for admin interface
3. Remove all `<style>` blocks and `style=""` attributes
4. Test admin functionality preservation

**Success Criteria:** Admin pages zero inline CSS, healthcare colours applied

---

### 📋 **Phase 3: Core Patient Data Templates (High Priority)**

**Goal:** Fix main patient workflow violations
**Scope:** 4-5 core patient templates
**Timeline:** 2-3 sessions

**Templates to fix (in order):**

1. `templates/patient_data/patient_search.html` - Search forms and break-glass logic
2. `templates/patient_data/patient_search_results.html` - Results display
3. `templates/patient_data/patient_orcd.html` - PDF viewer (complex)
4. `templates/patient_data/components/extended_patient_info.html` - Component styling

**Approach:**

1. Extract styles to `pages/_patient-data.scss` and `components/` files
2. Extract JavaScript to `pages/patient-search.js` and `components/pdf-viewer.js`
3. Maintain existing functionality while cleaning structure

**Success Criteria:** Core patient workflow clean, mobile-responsive

---

### 🔌 **Phase 4: SMP Client Templates (Medium Priority)**

**Goal:** Clean SMP dashboard and search interfaces
**Scope:** 3-4 SMP client templates
**Timeline:** 2-3 sessions

**Templates to fix:**

- `smp_client/templates/smp_client/dashboard.html` - Dashboard layout
- `smp_client/templates/smp_client/participant_search.html` - Search interface
- `smp_client/templates/smp_client/participant_detail.html` - Detail views

**Success Criteria:** SMP client interface spec-compliant

---

### 🎨 **Phase 5: Enhanced Components (Medium Priority)**

**Goal:** Clean complex component templates
**Scope:** Component templates with heavy styling
**Timeline:** 2-3 sessions

**Templates to fix:**

- `templates/patient_data/enhanced_patient_cda.html` - Complex CDA display
- Component templates in `templates/patient_data/components/`

**Success Criteria:** Reusable components with external styles

---

### 🧹 **Phase 6: Remaining Templates (Lower Priority)**

**Goal:** Clean up remaining violations
**Scope:** Debug templates, smaller violation templates
**Timeline:** 1-2 sessions

**Templates to fix:**

- Debug templates (if keeping them)
- Translation service templates
- Any remaining minor violations

**Success Criteria:** 100% spec compliance across all templates

## 5. Edge Cases & Constraints

### Technical Constraints

- **Django template tags** must not be broken during extraction
- **CSRF tokens** must be preserved in forms
- **Existing URLs** and view logic must remain unchanged
- **PDF.js integration** requires careful JavaScript extraction

### Browser Compatibility

- Modern browsers (ES6+ support required)
- Mobile responsiveness maintained
- Progressive enhancement for older browsers

### Performance Considerations

- SASS compilation must be fast (automated via runOnSave)
- JavaScript modules loaded efficiently
- CSS file size optimized (no unused styles)

## 6. Testing Plan

### Manual Testing

- **Visual regression testing**: Before/after screenshots of all pages
- **Responsive testing**: Mobile, tablet, desktop breakpoints
- **Functionality testing**: All interactive elements work correctly
- **Cross-browser testing**: Chrome, Firefox, Safari, Edge

### Automated Testing

- **CSS linting**: stylelint for SASS code quality
- **JS linting**: ESLint for JavaScript code quality
- **Template validation**: Ensure no inline styles/scripts remain
- **SASS compilation**: Automated testing of build process

### Security Testing

- **CSRF protection**: Verify all forms maintain security
- **Content Security Policy**: Ensure no inline script violations
- **XSS prevention**: Validate proper escaping maintained

## 7. Deployment Notes

### Build Process

- SASS compilation via VS Code runOnSave (already configured)
- CSS minification for production
- JavaScript concatenation and minification
- Cache-busting for static assets

### Rollback Plan

- Git branch for entire refactoring effort
- Feature flags for gradual rollout if needed
- Backup of original templates before modification

## 8. Decision Log

| Date | Decision | Reason |
|------|----------|--------|
| 2025-09-20 | Use healthcare organisation official colour palette | Compliance with healthcare branding standards |
| 2025-09-20 | Phase-based approach | Minimize risk and allow for testing at each stage |
| 2025-09-20 | Keep existing view logic unchanged | Focus on frontend only, maintain backend stability |
| 2025-09-20 | Mobile-first SASS architecture | Original spec requirement for responsive design |

## 9. Success Criteria

- [ ] **Zero inline CSS** in any template file
- [ ] **Zero inline JavaScript** in any template file
- [ ] **100% healthcare colour compliance** across all pages
- [ ] **Mobile-first responsive design** maintained
- [ ] **All existing functionality** preserved
- [ ] **SASS compilation** working automatically
- [ ] **Performance maintained** or improved
- [ ] **Security standards** maintained
