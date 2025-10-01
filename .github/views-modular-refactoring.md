# Specification: Views.py Modular Refactoring and Mock Data Removal

## 1. Summary

A comprehensive refactoring of `patient_data/views.py` to eliminate mock data violations, enforce Testing & Modular Architecture standards, and bring the codebase into full spec compliance. This includes breaking down monolithic views, extracting business logic to service layers, and implementing comprehensive testing.

## 2. Requirements

### Original Spec Compliance

- **No mock data in views** - All test data must be moved to fixtures/factories
- **50-line view limit** - Large view functions must be broken into smaller components
- **Class-based views preferred** - Use Django CBVs with mixins for complex functionality
- **Service layer extraction** - Business logic separated from presentation logic
- **Comprehensive testing** - Unit tests for all view functions/classes
- **Single Responsibility Principle** - Each function has one clear purpose

### Current Violations Identified

- **20+ mock data references** in views (TEST comments, mock_extended_data, sample data)
- **Monolithic view functions** exceeding 50-line limit significantly
- **Mixed concerns** - business logic embedded directly in views
- **Missing tests** - no corresponding test files for view functionality
- **Hardcoded test data** in production view functions

## 3. System Design

### Current State (Violations)

```
patient_data/views.py (9,691 lines - CRITICAL)
├── Mock data embedded in views (lines 4248-4729)
├── Monolithic functions (enhanced_cda_display: 500+ lines)
├── Business logic mixed with presentation
├── No service layer separation
└── Missing comprehensive tests
```

### Target State (Spec Compliant)

```
patient_data/
├── views/
│   ├── __init__.py
│   ├── base.py (CBV base classes)
│   ├── patient_views.py (patient-related views <50 lines each)
│   ├── cda_views.py (CDA processing views <50 lines each)
│   ├── document_views.py (document handling views <50 lines each)
│   └── mixins.py (reusable view mixins)
├── services/
│   ├── __init__.py
│   ├── patient_service.py (patient business logic)
│   ├── cda_processor.py (CDA processing logic)
│   └── document_service.py (document handling logic)
├── tests/
│   ├── __init__.py
│   ├── test_views/
│   ├── test_services/
│   └── fixtures/
└── factories/ (test data generation)
```

## 4. Implementation Tasks

### Phase 1: Mock Data Elimination (CRITICAL)

1. **Identify all mock data** in views.py
   - Remove lines 4248-4729 (mock_extended_data)
   - Remove line 8549 (TEST: sample allergies)
   - Remove all TEST comments and hardcoded sample data

2. **Move test data to proper location**
   - Create `tests/fixtures/` for static test data
   - Create `tests/factories/` for dynamic test data generation
   - Use Django's fixture system for test data

3. **Replace mock data with real data sources**
   - Database queries for actual patient data
   - Service layer methods for data processing
   - Proper fallbacks for empty data scenarios

### Phase 2: Service Layer Extraction

1. **Create service classes** for business logic
   - `PatientService`: patient data operations
   - `CDAProcessorService`: CDA document processing
   - `DocumentService`: document management operations

2. **Extract business logic** from views
   - Move data processing to services
   - Keep views focused on HTTP request/response
   - Implement dependency injection patterns

### Phase 3: View Modularization

1. **Break down monolithic views**
   - Split `enhanced_cda_display` (500+ lines) into smaller functions
   - Extract common patterns to mixins
   - Implement CBVs for complex functionality

2. **Apply 50-line limit**
   - Refactor any view function over 50 lines
   - Extract helper methods and service calls
   - Use composition over inheritance

### Phase 4: Comprehensive Testing

1. **Create test structure**
   - Unit tests for all view functions
   - Integration tests for complete workflows
   - Mock external dependencies properly

2. **Test coverage requirements**
   - 100% line coverage for new code
   - Security tests (CSRF, authentication)
   - Performance tests for complex operations

## 5. Edge Cases & Constraints

### Technical Constraints

- **Backward compatibility** - existing URLs must continue working
- **Database integrity** - no data corruption during refactoring
- **Session handling** - maintain existing session functionality
- **CSRF protection** - ensure all forms maintain security

### Testing Constraints

- **Test isolation** - each test must be independent
- **Performance** - test suite must run in <30 seconds
- **Data integrity** - use transactions for test database operations

## 6. Testing Plan

### Unit Tests (Required)

- **View function tests**: Test each view in isolation
- **Service layer tests**: Test business logic separately
- **Mixin tests**: Test reusable components
- **Security tests**: CSRF, authentication, authorization

### Integration Tests (Required)

- **Full workflow tests**: Complete user journeys
- **API endpoint tests**: All HTTP methods and responses
- **Template rendering tests**: Ensure correct context data

### Test Data Strategy

- **Factories**: Use factory_boy for dynamic test data
- **Fixtures**: JSON fixtures for static reference data
- **Mocking**: Mock external APIs and services
- **Database**: Use test database with proper cleanup

## 7. Success Criteria

### Code Quality Metrics

- [ ] **Zero mock data** in production view functions
- [ ] **All view functions ≤50 lines** (excluding imports/docstrings)
- [ ] **100% test coverage** for new/modified code
- [ ] **Service layer separation** - no business logic in views
- [ ] **CBV usage** for complex functionality

### Performance Metrics

- [ ] **View response time** <200ms for simple views
- [ ] **Test suite execution** <30 seconds total
- [ ] **Database queries** optimized (no N+1 problems)

### Security Compliance

- [ ] **CSRF protection** on all forms
- [ ] **Authentication** properly enforced
- [ ] **No sensitive data** in templates or logs
- [ ] **Input validation** on all user inputs

## 8. Decision Log

| Date | Decision | Reason |
|------|----------|--------|
| 2025-09-26 | Remove all mock data from views | Spec violation - test data belongs in test files |
| 2025-09-26 | Implement 50-line view limit | Modular architecture requirement |
| 2025-09-26 | Extract service layer | Separation of concerns principle |
| 2025-09-26 | Mandatory comprehensive testing | Quality assurance requirement |

## 9. Implementation Priority

**HIGH PRIORITY (Immediate)**

1. Remove all mock data from views (spec violation)
2. Create test fixtures and factories for removed mock data
3. Implement basic service layer for extracted business logic

**MEDIUM PRIORITY (Next Session)**
4. Break down monolithic view functions
5. Implement CBVs and mixins
6. Create comprehensive test suite

**LOW PRIORITY (Future Sessions)**
7. Performance optimization
8. Advanced testing scenarios
9. Documentation updates
