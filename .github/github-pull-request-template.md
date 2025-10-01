# Pull Request Checklist — Django_NCP Spec Compliance

Please review and tick all items that apply before requesting a merge.

---

## 1. Spec Compliance

- [ ] Feature/update has an associated `.spec` file in `/docs/specs/`
- [ ] All changes align with the **Original Spec** requirements
- [ ] No inline CSS in templates
- [ ] No inline JavaScript in templates
- [ ] No mock data in Python views
- [ ] Templates are minimal in logic (complexity moved to Python)
- [ ] Mobile-first design maintained
- [ ] HSE colour palette applied (SASS variables)

---

## 2. Code Quality

- [ ] Code follows project style guides (`flake8`, `black`, `stylelint`, `eslint`)
- [ ] No personal names in code, comments, or documentation
- [ ] Security best practices followed (sessions, CSRF, input validation)
- [ ] All new Python functions/classes have unit tests
- [ ] All new views have integration tests
- [ ] Frontend changes tested for responsiveness

---

## 3. Documentation

- [ ] `/docs/decisions/` updated if architectural/design decisions were made
- [ ] `/docs/todo.md` updated if new tasks were identified
- [ ] Decision log in relevant `.spec` updated

---

## 4. Automation & CI

- [ ] SASS compiles without errors
- [ ] All tests pass locally (`pytest` or `python manage.py test`)
- [ ] CI pipeline passes (if configured)

---

## 5. Reviewer Notes

_Optional: Add any context, screenshots, or notes for reviewers here._

---

**By submitting this PR, you confirm that all applicable boxes are ticked and the changes meet the Spec Alignment Checklist requirements.**
