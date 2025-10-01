# Feature Spec:  Python based National Contact Point Server

## 1. Summary

A Django-based implementation of an EU eHealth National Contact Point (NCP) server, designed for cross-border healthcare data exchange.

This project implements a complete Django-based EU eHealth infrastructure including:

- NCP Server: National Contact Point for cross-border patient data exchange
- Patient Portal: Web interface for patients and healthcare professionals
- SMP Integration: Service Metadata Publisher communication
- FHIR Services: Support for EU eHealth FHIR profiles
- Leverage the knowledge learned from the Java based eHealth project listed in the Resources section below.

## 2. Requirements

- Study the existing markdown documents
- Study the project folder structure, to know where everything is
- No inline CSS in HTML templates
- No JavaScript in HTML templates (store in `/static/js/`)
- Follow the best practices for inline comments in Django templates. See the resource section below about the Requirements for Django Template Comments
- No mock data in Python views
- Use reusable view classes and methods
- Keep Django templates simple (logic in Python, not templates)
- No longer using Jinja2 templates
- Mobile-first UI design
- Follow HSE colour palette (<www.hse.ie>)
- Maintain security: use sessions, avoid personal names in code/comments/docs
- Keep a running to-do list
- remember our conversations
- remember our solutions to problems we have faced along the way
- [Add any feature-specific requirements here]

## 3. System Design

- **Backend**: Django views, models, serializers
- **Frontend**: SASS stylesheets compiled to CSS, JS in `/static/js/`
- **Templates**: Minimal logic, extend from base templates
- **Security**: Session-based auth, CSRF protection, input validation

## 4. Implementation Tasks

1. Create/Update Django view(s) in `views.py` or class-based views
2. Add/Update templates in `/templates/`
3. Add SASS styles in `/static/sass/` and compile to `/static/css/`
4. Add JS in `/static/js/`
5. Write/Update unit tests in `/tests/`
6. Update documentation if needed
7. Create a git branch, in which to build a new feature, or implement fundamental changes to the project

## 5. Edge Cases & Constraints

- Handle empty datasets gracefully
- Ensure responsive design on small screens
- Avoid exposing sensitive data in templates or logs

## Testing Plan

### Comprehensive Testing Requirements

**🔗 See [Testing and Modular Code Standards](./testing-and-modular-code-standards.md) for complete requirements**

### Mandatory Testing Components

- [ ] **Unit Tests**: Every view, service, and mixin must have comprehensive unit tests
- [ ] **View Function Tests**: Authentication, authorization, context data, error handling
- [ ] **Service Layer Tests**: Business logic testing in isolation
- [ ] **Mixin Tests**: Reusable component functionality
- [ ] **Integration Tests**: Complete user workflows
- [ ] **Security Tests**: CSRF protection, access control, session validation
- [ ] **Performance Tests**: Database query optimization, response time validation

### Modular Architecture Requirements

- [ ] **Class-Based Views**: Use CBVs with mixin architecture
- [ ] **Service Layer**: Extract business logic to dedicated service classes
- [ ] **Reusable Mixins**: Common functionality in reusable mixins
- [ ] **50-Line Rule**: No view functions over 50 lines
- [ ] **DRY Principle**: Zero code duplication - extract to reusable components

### Test File Structure

```
tests/
├── test_[feature_name]_views.py          # View testing
├── test_[feature_name]_services.py       # Service layer testing
├── test_[feature_name]_mixins.py         # Mixin functionality
├── test_[feature_name]_integration.py    # Workflow testing
└── test_[feature_name]_security.py       # Security validation
```

### Pre-Development Checklist

- [ ] Review existing mixins and services for reusability
- [ ] Plan modular architecture with reusable components
- [ ] Design test cases before implementation
- [ ] Ensure SCSS follows [architecture standards](./scss-architecture-standards.md)

### Quality Gates (All Must Pass)

- [ ] 100% test coverage for new code
- [ ] All automated tests pass
- [ ] Performance tests under defined limits
- [ ] Security validation complete
- [ ] Code review approval
- [ ] SCSS compilation successful

## 7. Deployment Notes

- Compile SASS before deployment
- Run `python manage.py test` before merge
- Verify colour compliance with HSE palette

## 8. Resources to utilize

- [Patient Summary CDA Templates](https://code.europa.eu/ehdsi/ehdsi-general-repository/-/tree/main/cda%20documents/W7/PS?ref_type=heads)
- [eHealth Portal](https://code.europa.eu/ehdsi/ehealth-portal)
- [eHealth National Contact Point](https://code.europa.eu/ehdsi/ehealth)
- [Requirements for Django Template Comments](C:\Users\Duncan\VS_Code_Projects\django_ncp\.specs\django_template_comments.md)
-

## 8. Decision Log

- [Date] [Decision] [Reason]
