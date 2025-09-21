# Django_NCP — TODO Tracker

This document tracks ongoing tasks and aligns with the **Spec Alignment Checklist** to ensure compliance with our Original Spec.

---

## 🎯 **High Priority - Spec Compliance**

### Frontend Structure - Phase 1: Foundation & Infrastructure (COMPLETE! ✅)

- [x] **Audit templates for inline CSS/JS violations** *(Completed 2025-09-20)*
- [x] **Create comprehensive frontend compliance specification** *(Completed 2025-09-20)*
- [x] **Create SASS directory structure** *(Already exists - excellent organization!)*
- [x] **Implement HSE colour palette** *(Already implemented in _variables.scss)*
- [x] **Create mobile-first mixins** *(Already exists in utils/)*
- [x] **Set up base typography** *(Already exists in base/)*
- [x] **Test SASS compilation pipeline** *(Already working via runOnSave)*

### Frontend Structure - Phase 2: Critical Admin Templates (COMPLETE! ✅)

- [x] **Extract admin login styles** from `templates/admin/login.html` → `pages/_admin.scss` *(Completed 2025-09-20)*
- [x] **Extract admin dashboard styles** from `templates/admin/index.html` → `pages/_admin.scss` *(Completed 2025-09-20)*
- [ ] **Extract SMP certificate form styles** *(Deferred to Phase 4 - complex template)*

### Frontend Structure - Phase 3: Core Patient Data Templates (COMPLETE! ✅)

- [x] **Extract patient search styles** from `templates/patient_data/patient_search.html` → `pages/_patient.scss` *(Completed 2025-09-20)*
- [x] **Extract patient search results styles** from `templates/patient_data/patient_search_results.html` → `pages/_patient.scss` *(Completed 2025-09-20)*
- [x] **Extract ORCD PDF viewer styles** from `templates/patient_data/patient_orcd.html` → `pages/_patient.scss` *(Completed 2025-09-20)*
- [x] **Extract JavaScript** from patient templates → `static/js/patient_data.js` *(Completed 2025-09-20)*
- [x] **Zero inline violations** in core patient workflow templates *(Verified 2025-09-20)*

### Frontend Structure - Phase 4: Remaining Patient Components (NEXT PHASE)

- [ ] **Extract styles from** `templates/patient_data/components/extended_patient_info.html`
- [ ] **Extract scripts from** `templates/patient_data/components/clinical_information_content.html`
- [ ] **Clean test sections** in `templates/patient_data/sections/test_allergies_section.html`
- [ ] **Clean document viewers** in `templates/patient_data/view_document.html` and `view_uploaded_document.html`
- [ ] **Extract CDA bilingual display** styles from `templates/patient_data/cda_bilingual_display.html`

### Frontend Structure - Remaining Phases (FUTURE)

- [ ] **Phase 5:** SMP Client Templates (dashboard, search interfaces)
- [ ] **Phase 6:** Enhanced Components (CDA display, complex components)
- [ ] **Phase 7:** Remaining Templates (debug, translation services)

### Backend & Views

- [ ] **Remove mock data** from Python views → replace with DB queries or API calls
- [ ] **Refactor function‑based views** into class‑based views where reuse is possible
- [ ] **Move complex logic** from templates into Python methods
- [ ] **Ensure reusable view classes and helper methods** are in place

### Templates

- [ ] **Simplify templates** — minimal logic, extend from base templates
- [ ] **Remove any Jinja2 remnants** (confirm Django template engine only)
- [ ] **Ensure no personal names** appear in templates

---

## 🔒 **Security & Compliance**

- [ ] **Audit code/comments/docs** for personal names (remove if found)
- [ ] **Verify session‑based authentication** is correctly implemented
- [ ] **Confirm CSRF protection** is active on all forms
- [ ] **Validate all user input** server‑side

---

## 🧪 **Testing & Automation**

- [x] **Set up VS Code Run on Save** for auto‑running flake8 on `.py` save *(Completed 2025-09-20)*
- [x] **Set up SASS auto‑compilation** on `.scss` save *(Completed 2025-09-20)*
- [ ] **Add unit tests** for each Python function/class
- [ ] **Add integration tests** for views
- [ ] **Add frontend responsiveness tests**
- [ ] **Add security tests** (CSRF, session handling, input validation)

---

## 📚 **Documentation & Process**

- [x] **Create `/docs/todo.md`** for ongoing tasks *(Completed 2025-09-20)*
- [x] **Create `/docs/decisions/`** folder for architectural decisions *(Completed 2025-09-20)*
- [ ] **Backfill decision log** with past major choices
- [ ] **Ensure all new features start with a spec file** in `.specs/`
- [ ] **Add PR checklist** to enforce spec compliance

---

## ⚙️ **Additional Quality Gates**

- [x] **Add linting** (`flake8` via runOnSave) *(Completed 2025-09-20)*
- [ ] **Add code formatting** (`black`, `stylelint`, `eslint`)
- [ ] **Add security scanning** (`bandit`, `pip-audit`)
- [ ] **Implement pre‑commit hooks** for linting/tests
- [ ] **Plan CI/CD pipeline** with automated tests and SASS build

---

## 🔄 **Current Sprint Tasks**

*(Add immediate tasks here as they arise)*

- [x] Set up centralized TODO tracking system *(Completed 2025-09-20)*
- [ ] Create decision log infrastructure
- [ ] Backfill existing architectural decisions

---

## 📈 **Progress Tracking**

- **Date Started:** 2025-09-20
- **Last Updated:** 2025-09-20
- **Current Completion:** 5 / 35+ items (~14%)
- **Target:** Achieve 80%+ spec compliance before next major feature development

---

## 📝 **Notes**

- This TODO list is synchronized with the **Spec Alignment Checklist**
- All completed items should be marked with completion date
- New tasks must align with Original Spec requirements
- Review and update weekly or after major milestones
