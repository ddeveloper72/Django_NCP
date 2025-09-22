# Spec Alignment Checklist — Django_NCP

This checklist is based on the Retro‑Spec and is used to track progress in aligning the current project state with the target specification.

---

## 1. Frontend Structure

- [ ] **Remove all inline CSS** from templates → move to `/static/sass/` and compile to `/static/css/`
- [ ] **Remove all inline JavaScript** from templates → move to `/static/js/`
- [ ] **Reintegrate original SASS styles** (replace Bootstrap defaults)
- [ ] **Adopt HSE colour palette** in SASS variables
- [ ] **Ensure mobile‑first design** across all pages
- [ ] **Use Font Awesome template strings** from the reference guide, where necessary.  Incorrect classes result in CSS styling issues.
- [ ] **Perfect icon centering compliance** — All FontAwesome icons in badge contexts must pass cross-hair alignment test (see `icon-centering-standards.md`)

---

## 2. Backend & Views

- [ ] **Remove mock data** from Python views → replace with DB queries or API calls
- [ ] **Refactor function‑based views** into class‑based views where reuse is possible
- [ ] **Move complex logic** from templates into Python methods
- [ ] **Ensure reusable view classes and helper methods** are in place

---

## 3. Templates

- [ ] **Simplify templates** — minimal logic, extend from base templates
- [ ] **Remove any Jinja2 remnants** (confirm Django template engine only)
- [ ] **Ensure no personal names** appear in templates

---

## 4. Security

- [ ] **Audit code/comments/docs** for personal names (remove if found)
- [ ] **Verify session‑based authentication** is correctly implemented
- [ ] **Confirm CSRF protection** is active on all forms
- [ ] **Validate all user input** server‑side

---

## 5. Testing & Automation

- [ ] **Add unit tests** for each Python function/class
- [ ] **Add integration tests** for views
- [ ] **Add frontend responsiveness tests**
- [ ] **Add security tests** (CSRF, session handling, input validation)
- [x] **Set up VS Code Run on Save** for auto‑running tests on `.py` save *(Completed 2025-09-20)*
- [x] **Set up SASS auto‑compilation** on `.scss` save *(Completed 2025-09-20)*

---

## 6. Documentation & Process

- [x] **Create `/docs/todo.md`** for ongoing tasks *(Completed 2025-09-20)*
- [x] **Create `/docs/decisions/`** folder for architectural decisions *(Completed 2025-09-20)*
- [ ] **Backfill decision log** with past major choices
- [ ] **Ensure all new features start with a spec file** in `.specs/`
- [ ] **Add PR checklist** to enforce spec compliance

---

## 7. Additional Quality Gates

- [x] **Add linting** (`flake8` via runOnSave) *(Completed 2025-09-20)*
- [ ] **Add code formatting** (`black`, `stylelint`, `eslint`)
- [ ] **Add security scanning** (`bandit`, `pip-audit`)
- [ ] **Implement pre‑commit hooks** for linting/tests
- [ ] **Plan CI/CD pipeline** with automated tests and SASS build

---

### Progress Tracking

- **Date Started:** 2025-09-20
- **Target Completion:** TBD
- **Current Completion:** 5 / 25 items (20%)
- **Last Updated:** 2025-09-20
