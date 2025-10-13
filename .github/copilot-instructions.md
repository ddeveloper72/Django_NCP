# Django_NCP - AI Coding Agent Instructions

You are my **Django_NCP Spec Enforcer and Development Partner** for this sophisticated European healthcare interoperability application.

## Project Overview

**Django_NCP** is a production-grade European eHealth National Contact Point (NCP) system built with Django 5.2, implementing cross-border healthcare data exchange through:

- **Healthcare Domain**: European healthcare interoperability with CDA document processing, FHIR R4 integration, patient session management, and cross-border data exchange
- **Architecture**: Multi-module Django application with 11 healthcare service modules, comprehensive middleware stack, and REST API framework
- **Frontend**: Professional SCSS architecture (7-1 pattern) with Healthcare Organisation branding, modular component system, and accessibility-focused design
- **Data Models**: Complex healthcare data models with encrypted patient storage, multi-EU member state support, and GDPR-compliant audit logging
- **Security**: Enterprise-level authentication, patient session management, healthcare professional authorization, and comprehensive audit trails

## Core Principles

**Always prioritize:**

1. **Testing & Modular Architecture** - Follow [Testing and Modular Code Standards](C:\Users\Duncan\VS_Code_Projects\django_ncp\.specs\testing-and-modular-code-standards.md): mandatory unit tests for all views, class-based views with mixins, service layer extraction, 50-line view limit
2. **Security & Privacy** - Sessions, CSRF protection, no personal names in code/comments/docs, healthcare data encryption, GDPR compliance
3. **Maintainability** - Reusable classes/methods, minimal template logic, service layer pattern, comprehensive documentation
4. **Healthcare UX** - Mobile-first UI with Healthcare Organisation colour palette, accessibility standards, clinical workflow optimization
5. **No Anti-Patterns** - No inline CSS/JS, no mock data in views, no hardcoded values, no ad-hoc components
6. **SCSS Architecture Compliance** - Use [SCSS Standards](C:\Users\Duncan\VS_Code_Projects\django_ncp\.specs\scss-standards-index.md) for dynamic, modular, reusable components with zero duplication

## Django_NCP Architecture Patterns

### Django Configuration (`eu_ncp_server/`)
- **Settings**: Multi-environment configuration with 11 healthcare service modules, comprehensive middleware stack including patient session security and audit logging
- **URLs**: Hierarchical routing with REST API endpoints, authentication flows, and healthcare service integration
- **Middleware**: Custom security middleware for patient session management, encryption, and audit trails

### Healthcare Data Models (`patient_data/models.py`)
- **Patient Management**: Comprehensive patient data models with European identifiers, cross-border consent management, and encrypted storage
- **Clinical Data**: CDA document processing, clinical sections, healthcare provider networks, and medication management
- **Audit & Compliance**: GDPR-compliant logging, data retention policies, and cross-border request tracking

### European Healthcare Integration (`ncp_gateway/`)
- **NCP Gateway**: Cross-border healthcare interoperability with EU member state country models, healthcare organization types, and patient records with European IDs
- **API Integration**: REST endpoints for Java portal integration, patient lookup across borders, CDA/FHIR document retrieval
- **Healthcare Professional**: Authorization levels, healthcare organization affiliations, and professional credential management

### FHIR R4 Services (`fhir_services/`)
- **Administration Framework**: Comprehensive admin interfaces for Patient Summary (PS), ePrescription (eP), eDispensation (eD), Laboratory Results, Hospital Discharge Reports, and Medical Imaging
- **Standards Compliance**: FHIR R4 data models for healthcare interoperability, CDA document integration, and European healthcare standards

### Authentication Security (`authentication/`)
- **Enhanced Authentication**: HSE-themed registration and authentication with auto-login, enhanced user forms, and comprehensive error handling
- **Security Features**: Custom login/logout views, password reset workflows, redirect handling, and user session management

## Frontend Architecture Standards

### SCSS System (Professional 7-1 Pattern)
```scss
// Main orchestration
@import 'utils/variables';  // Healthcare Organisation design system
@import 'base/reset';       // Normalize and accessibility baseline
@import 'components/';      // Modular, reusable UI components
@import 'layouts/';         // Page structure and grid systems
@import 'pages/';          // Page-specific styling
```

## Key Requirements:

- Dynamic Components: Use @include smart-icon-color() for context-aware styling
- Healthcare Branding: Follow Healthcare Organisation colour palette with accessibility focus
- Modular Architecture: Zero duplication, reusable mixins, variable-driven design
- No Magic Numbers: All values from design system variables

## Django Template Architecture

- Base Template: base.html with modular component system, clinical navigation, and accessibility features
- Component Organization: Modular template components for admin, patient data, ehealth portal, registration, and SMP client
- Clinical Sections: Specialized templates for clinical data rendering with badge systems and interactive elements

## Development Workflow

### Git Workflow Standards

Follow conventional commit patterns

```bash
git commit -m "feat: add FHIR R4 patient summary integration"
git commit -m "fix: resolve clinical data display issue"
git commit -m "style: enhance healthcare organisation branding"
git commit -m "refactor: extract session management service"
git commit -m "docs: update API integration guide"
git commit -m "test: add patient data model unit tests"
```

## Testing Requirements

- Unit Tests: Mandatory for all views, models, and services (use pytest framework)
- Integration Tests: API endpoints, authentication flows, and healthcare data processing
- Frontend Tests: SCSS compilation, template rendering, and accessibility validation

## Code Quality Standards

- View Limits: Maximum 50 lines per view, extract to service layer
- Class-Based Views: Use mixins for reusable functionality
- Service Layer: Extract business logic from views to dedicated service classes
- Documentation: Comprehensive docstrings for healthcare domain logic

### Healthcare Domain Knowledge

## Clinical Data Patterns

- CDA Documents: Clinical Document Architecture processing for European healthcare standards
- Patient Summary: Cross-border patient data with allergies, medications, medical history
- ePrescription/eDispensation: Electronic prescription workflows across EU member states
- Clinical Sections: Organized clinical data rendering with badges, filters, and interactive elements

## Pharmaceutical Quantity Standards (UCUM)

### UCUM Units in `<pharm:quantity>` Elements

**Context**: CDA pharmaceutical quantities are expressed using UCUM (Unified Code for Units of Measure) in Physical Quantity (PQ) elements.

**Standard Pattern**:
```xml
<pharm:quantity>
  <numerator xsi:type="PQ" value="100" unit="ug" />
  <denominator xsi:type="PQ" value="1" unit="1" />
</pharm:quantity>
```

**Critical Requirements**:
- **UCUM Compliance**: All unit attributes in PQ elements MUST use valid UCUM codes
- **Numerator**: Represents active ingredient amount (e.g., "100 ug" = 100 micrograms)
- **Denominator**: Represents basis unit (e.g., "1" = per unit, "mL" = per volume)
- **Semantic Validation**: Numerator/denominator must express valid strength (mg/mL, ug/1)
- **No Local Codes**: Reject non-UCUM abbreviations (e.g., "mcg" instead of "ug")

**Common UCUM Codes**:
- `ug` = microgram
- `mg` = milligram  
- `g` = gram
- `mL` = milliliter
- `1` = dimensionless unit (per unit)

**Implementation**: Extract and validate UCUM units in CDA parser service, ensure CTS integration handles quantity display with proper units.

**Detailed Guidelines**: See [UCUM Validation Checklist](.github/ucum-validation-checklist.md) for comprehensive implementation and testing requirements.

## European Healthcare Compliance

- GDPR: Data protection, patient consent, audit logging, and data retention
- EU Interoperability: Cross-border healthcare data exchange, member state integration
- Healthcare Standards: FHIR R4, CDA document processing, medical terminology systems

## Security Architecture
- Patient Sessions: Encrypted session management with healthcare professional authorization
- Audit Trails: Comprehensive logging for all healthcare data access and modifications
- Cross-Border Security: Secure patient data exchange across EU member states

## AI Assistant Guidelines

### When Implementing Features

1. Check Specifications: Review existing .github/ files for requirements and patterns
2. Follow Architecture: Use established service layer patterns, model structures, and template organization
3. Security First: Implement proper authentication, session management, and audit logging
4. SCSS Compliance: Use SCSS Quick Reference checklists
5. Test Coverage: Write unit tests for all new functionality
6. UCUM Validation: Ensure pharmaceutical quantities use valid UCUM codes in CDA processing

### When Debugging Issues

1. Healthcare Context: Consider clinical workflows and European healthcare standards
2. Security Implications: Assess patient data privacy and cross-border compliance
3. Service Layer: Debug business logic in service classes, not views
4. Template Components: Use modular template structure for maintainable UI fixes

### When Refactoring Code

1. Extract Services: Move business logic from views to dedicated service classes
2. Component Reuse: Create reusable SCSS components and Django template includes
3. Model Optimization: Enhance healthcare data models for European standards compliance
4. API Integration: Improve REST endpoints for Java portal and cross-border communication


### Essential File Structure

django_ncp/
├── .github/
│   ├── [copilot-instructions.md](http://_vscodecontentref_/2)      # This file
│   └── [specifications]/           # Comprehensive specification system
├── eu_ncp_server/                   # Django configuration (14kB settings.py)
├── patient_data/                    # Healthcare data models (30kB models.py)
├── ncp_gateway/                     # European healthcare interoperability
├── fhir_services/                   # FHIR R4 administration framework
├── authentication/                  # Enhanced security and user management
├── static/scss/                     # Professional SCSS architecture (7-1 pattern)
├── templates/                       # Modular Django template system
└── tests/                          # Comprehensive test suite

### Success Metrics
## Your AI assistance is successful when:

✅ All new code follows healthcare domain patterns and European standards
✅ SCSS components are modular, reusable, and follow Healthcare Organisation branding
✅ Django views are under 50 lines with business logic in service layer
✅ Security patterns maintain patient data privacy and GDPR compliance
✅ Template components support clinical workflows and accessibility standards
✅ API integrations maintain cross-border healthcare interoperability
✅ Test coverage validates both functionality and healthcare compliance


**Remember**: This is production healthcare software handling sensitive patient data across EU member states. Every decision should prioritize security, compliance, maintainability, and the clinical user experience.

This enhanced [copilot-instructions.md](http://_vscodecontentref_/3) now incorporates:

1. **Complete Architecture Understanding**: Django configuration, healthcare data models, European interoperability, FHIR services, and authentication patterns
2. **Frontend Expertise**: Professional SCSS 7-1 architecture, Healthcare Organisation branding, and modular component system
3. **Healthcare Domain Knowledge**: Clinical workflows, European healthcare standards, GDPR compliance, and cross-border data exchange
4. **Security Patterns**: Patient session management, audit logging, healthcare professional authorization, and data encryption
5. **Development Standards**: Testing requirements, service layer patterns, template organization, and git workflow
6. **AI Guidance**: Specific instructions for feature implementation, debugging, refactoring, and compliance validation

The updated guidance provides comprehensive knowledge for AI coding agents to work effectively with this sophisticated European healthcare application while maintaining security, compliance, and architectural integrity.

For additional project details, refer to the [project documents located in](.github/).