# Retro‑Spec: Django_NCP (Current State)

## 1. Summary

A Django‑based implementation of an EU eHealth National Contact Point (NCP) server for cross‑border healthcare data exchange.

The project currently includes:

- Django project structure with core NCP functionality
- Bootstrap CSS integration (migration back to original SASS styles planned)
- HTML templates with some inline CSS/JS
- Python views containing mock data for testing
- Initial patient portal and FHIR service endpoints

---

## 2. Current Requirements Compliance

| Requirement | Status | Notes |
|-------------|--------|-------|
| No inline CSS in HTML templates | ⚠️ | Most templates use external CSS; some inline `<style>` blocks remain |
| No JavaScript in HTML templates | ⚠️ | Most JS moved to external files; some inline `<script>` tags remain |
| No mock data in Python views | ❌ | Some views return hardcoded data |
| Use reusable view classes/methods | ⚠️ | Some CBVs exist, but repeated logic still in FBVs |
| Keep templates simple | ✅ | Templates simplified with enhanced accessibility markup |
| Mobile‑first UI design | ✅ | Navigation enhanced with responsive design and touch targets |
| Follow HSE colour palette | ✅ | HSE colour scheme implemented in navigation and icons |
| Maintain security (sessions, no personal names) | ⚠️ | Sessions enabled; audit for personal names needed |
| Keep running to‑do list | ✅ | Active to-do tracking with manage_todo_list tool |
| Remember solutions to past problems | ✅ | Git workflow documentation and incremental commits implemented |
| No Jinja2 templates | ✅ | Using Django template engine only |
| **Git workflow with incremental commits** | ✅ | **Small, focused commits with conventional messages implemented** |
| **Enhanced navigation accessibility** | ✅ | **WCAG-compliant navigation with proper ARIA labels and focus management** |

---

## 3. System Design (As Implemented)

- **Backend**: Django views (mix of CBVs and FBVs), models, serializers (if DRF used)
- **Frontend**: Bootstrap CSS, some inline styles, JS embedded in templates
- **Templates**: Located in `/templates/`, some contain logic and inline assets
- **Static Assets**: `/static/` contains CSS, JS, images; SASS not yet re‑integrated
- **Security**: Django session middleware enabled, CSRF protection active
- **Testing**: Limited or no automated unit tests; manual testing predominant

---

## 4. Implementation Tasks (Retrofit Plan)

1. ✅ **Git workflow established** → Small incremental commits with conventional messages (see `/docs/GIT_WORKFLOW.md`)
2. ✅ **Navigation enhanced** → HSE-themed, accessible, mobile-responsive navigation implemented
3. ⚠️ Remove remaining inline CSS → move to `/static/sass/` and compile to `/static/css/`
4. ⚠️ Remove remaining inline JS → move to `/static/js/`
5. ❌ Replace mock data with DB queries or API calls
6. ⚠️ Refactor FBVs into CBVs where reuse is possible
7. ⚠️ Simplify remaining templates by moving logic into Python
8. ✅ HSE colour palette adopted in SASS variables and navigation
9. ✅ Create `/docs/` structure for to-do lists and decisions
10. ❌ Add unit tests for each function/class
11. ❌ Set up pre‑commit hooks for linting and security checks

---

## 5. Edge Cases & Constraints

- Some endpoints incomplete or stubbed
- Bootstrap removal may break layouts
- FHIR compliance requires strict schema adherence
- Security audit needed before production

---

## 6. Testing Plan (Current vs Target)

**Current**:

- Manual browser testing
- Occasional `python manage.py test`

**Target**:

- Automated unit tests for all Python functions/classes
- Integration tests for views
- Frontend responsiveness tests
- Security tests (CSRF, session handling, input validation)

---

## 7. Deployment Notes

- SASS compilation not yet in build process
- No CI/CD pipeline configured
- Manual deployment steps documented informally

---

## 8. Resources

- [Patient Summary CDA Templates](https://code.europa.eu/ehdsi/ehdsi-general-repository/-/tree/main/cda%20documents/W7/PS?ref_type=heads)
- [eHealth Portal](https://code.europa.eu/ehdsi/ehealth-portal)
- [eHealth National Contact Point](https://code.europa.eu/ehdsi/ehealth)
- [Font Awesome Style sizing](https://docs.fontawesome.com/web/style/size)
- [Font Awesome Style Cheat Sheets](https://docs.fontawesome.com/web/style/style-cheatsheet)

---

## 9. Decision Log (Backfilled)

| Date | Decision | Reason |
|------|----------|--------|
| YYYY‑MM‑DD | Started with Bootstrap CSS | Faster initial UI prototyping |
| YYYY‑MM‑DD | Used mock data in views | Expedite early development before DB ready |
| YYYY‑MM‑DD | Chose Django template engine over Jinja2 | Native integration, security features |
