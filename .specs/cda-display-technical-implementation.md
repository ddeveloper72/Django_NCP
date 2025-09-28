# CDA Display Technical Implementation Reference

**Document Version:** 1.0
**Last Updated:** September 28, 2025
**Status:** Production Implementation Guide
**Purpose:** Technical reference for implementing the CDA Display wireframes

---

## Implementation Overview

This document provides the technical implementation details for the Enhanced CDA Patient Display interface, directly corresponding to the approved wireframe designs.

**Wireframe Reference:** `cda-display-wireframe-design-guide.md`

---

## Template Structure Implementation

### Primary Template: `enhanced_patient_cda.html`

#### Navigation Tabs Structure

```html
<!-- Primary Level Navigation -->
<ul class="nav nav-tabs nav-tabs-healthcare" id="patientTabs" role="tablist">
    <li class="nav-item" role="presentation">
        <button class="nav-link active" id="overview-tab" data-bs-toggle="tab"
                data-bs-target="#overview-content" type="button" role="tab">
            <i class="fa-solid fa-user me-2"></i>Patient Overview
        </button>
    </li>
    <li class="nav-item" role="presentation">
        <button class="nav-link" id="contact-tab" data-bs-toggle="tab"
                data-bs-target="#contact-content" type="button" role="tab">
            <i class="fa-solid fa-address-book me-2"></i>Extended Patient Information
        </button>
    </li>
</ul>

<!-- Tab Content Container -->
<div class="tab-content" id="patientTabContent">
    <!-- Patient Overview Content -->
    <div class="tab-pane fade show active" id="overview-content" role="tabpanel">
        <!-- Static patient information display -->
    </div>

    <!-- Extended Patient Information Content -->
    <div class="tab-pane fade" id="contact-content" role="tabpanel">
        <!-- Secondary navigation and card layout -->
    </div>
</div>
```

#### Secondary Navigation (Pills) Structure

```html
<!-- Secondary Level Navigation (Pills) -->
<div class="nav nav-pills nav-fill mb-3" role="tablist">
    <button class="nav-link active btn-sm" id="personal-info-tab"
            data-bs-toggle="pill" data-bs-target="#personal-info" type="button" role="tab">
        <i class="fa-solid fa-user me-1"></i>Personal Information
    </button>
    <button class="nav-link btn-sm" id="healthcare-team-tab"
            data-bs-toggle="pill" data-bs-target="#healthcare-team" type="button" role="tab">
        <i class="fa-solid fa-user-md me-1"></i>Healthcare Team
    </button>
    <button class="nav-link btn-sm" id="system-doc-tab"
            data-bs-toggle="pill" data-bs-target="#system-doc" type="button" role="tab">
        <i class="fa-solid fa-cog me-1"></i>System & Documentation
    </button>
</div>

<!-- Pills Content Container -->
<div class="tab-content">
    <div class="tab-pane fade show active" id="personal-info" role="tabpanel">
        <!-- Personal Information Cards -->
    </div>
    <div class="tab-pane fade" id="healthcare-team" role="tabpanel">
        <!-- Healthcare Team Cards -->
    </div>
    <div class="tab-pane fade" id="system-doc" role="tabpanel">
        <!-- System & Documentation Cards -->
    </div>
</div>
```

---

## Card Layout Implementation

### Personal Information Cards (Wireframe 1)

```html
<div class="row g-3">
    <!-- Patient Demographics Card -->
    <div class="col-12 col-md-6 col-lg-4">
        <div class="card border-primary h-100">
            <div class="card-header bg-primary text-white py-2">
                <h6 class="mb-0">
                    <i class="fa-solid fa-user me-2"></i>Patient Demographics
                </h6>
            </div>
            <div class="card-body py-2">
                <p class="mb-1"><strong>{{ patient_identity.given_name }} {{ patient_identity.family_name }}</strong></p>
                <small class="text-muted">
                    <i class="fa-solid fa-calendar me-1"></i>Birth Date: {{ patient_identity.birth_date_formatted }}<br>
                    <i class="fa-solid fa-venus-mars me-1"></i>Gender: {{ patient_identity.administrative_gender|capfirst }}
                </small>
            </div>
        </div>
    </div>

    <!-- Patient Identifiers Card -->
    <div class="col-12 col-md-6 col-lg-4">
        <div class="card border-secondary h-100">
            <div class="card-header bg-secondary text-white py-2">
                <h6 class="mb-0">
                    <i class="fa-solid fa-id-card me-2"></i>Patient Identifiers
                </h6>
            </div>
            <div class="card-body py-2">
                <small class="text-muted">
                    <i class="fa-solid fa-fingerprint me-1"></i>Patient ID:<br>
                    <code class="small">{{ patient_identity.patient_id }}</code>
                </small>
            </div>
        </div>
    </div>

    <!-- Patient Address Card -->
    <div class="col-12 col-md-6 col-lg-4">
        <div class="card border-info h-100">
            <div class="card-header bg-info text-white py-2">
                <h6 class="mb-0">
                    <i class="fa-solid fa-map-marker-alt me-2"></i>Patient Address
                </h6>
            </div>
            <div class="card-body py-2">
                {% if contact_data.patient_contact_info.addresses %}
                {% for address in contact_data.patient_contact_info.addresses %}
                <small class="text-muted">
                    {% if address.street %}{{ address.street }}<br>{% endif %}
                    {% if address.city %}{{ address.city }}{% endif %}
                    {% if address.postalCode %}, {{ address.postalCode }}{% endif %}<br>
                    {{ address.country|country_flag|safe }}{{ address.country|country_name }}
                </small>
                {% endfor %}
                {% endif %}
            </div>
        </div>
    </div>

    <!-- Contact Methods Card (Full Width) -->
    <div class="col-12">
        <div class="card border-success">
            <div class="card-header bg-success text-white py-2">
                <h6 class="mb-0">
                    <i class="fa-solid fa-phone me-2"></i>Contact Methods
                </h6>
            </div>
            <div class="card-body py-2">
                {% if contact_data.patient_contact_info.telecoms %}
                <div class="row">
                    {% for telecom in contact_data.patient_contact_info.telecoms %}
                    <div class="col-md-6">
                        <small class="text-muted">
                            {% if telecom.type == 'phone' %}
                            <i class="fa-solid fa-phone me-1"></i>tel: {{ telecom.display_value }}
                            {% elif telecom.type == 'email' %}
                            <i class="fa-solid fa-envelope me-1"></i>{{ telecom.display_value }}
                            {% endif %}
                        </small>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
            </div>
        </div>
    </div>
</div>
```

### Healthcare Team Card (Wireframe 2)

```html
<div class="card border-success h-100">
    <div class="card-header bg-success text-white py-2">
        <h6 class="mb-0">
            <i class="fa-solid fa-hospital me-2"></i>Healthcare Provider Information
        </h6>
    </div>
    <div class="card-body py-2">
        <div class="row">
            <!-- Healthcare Provider -->
            <div class="col-md-6">
                <h6 class="text-success">
                    <i class="fa-solid fa-user-md me-2"></i>Healthcare Provider
                </h6>
                <p class="mb-1">{{ administrative_data.author_hcp.full_name }}</p>
            </div>

            <!-- Healthcare Organization -->
            <div class="col-md-6">
                <h6 class="text-success">
                    <i class="fa-solid fa-hospital me-2"></i>Healthcare Organization
                </h6>
                <p class="mb-1">{{ administrative_data.custodian_name }}</p>

                <div class="mt-2">
                    <strong>CONTACT INFORMATION</strong><br>
                    <small class="text-muted">
                        {% if administrative_data.author_hcp.organization.telecoms %}
                        {% for telecom in administrative_data.author_hcp.organization.telecoms %}
                        <i class="fa-solid fa-envelope me-1"></i>{{ telecom.display_value }}<br>
                        {% endfor %}
                        {% endif %}
                    </small>
                </div>

                <div class="mt-2">
                    <strong>ORGANIZATION ADDRESS</strong><br>
                    <small class="text-muted">
                        {% if administrative_data.author_hcp.organization.addresses %}
                        {% for address in administrative_data.author_hcp.organization.addresses %}
                        {{ address.street }}<br>
                        {{ address.city }}, {{ address.postalCode }}
                        {% endfor %}
                        {% endif %}
                    </small>
                </div>
            </div>
        </div>

        <!-- Legal Authenticator -->
        <div class="mt-3 pt-3 border-top">
            <h6 class="text-success">
                <i class="fa-solid fa-gavel me-2"></i>Legal Authenticator
            </h6>
            <p class="mb-1"><strong>AUTHENTICATOR</strong></p>
            <p class="mb-0">{{ administrative_data.legal_authenticator.full_name }}</p>
        </div>
    </div>
</div>
```

### System & Documentation Card (Wireframe 3)

```html
<div class="card border-primary h-100">
    <div class="card-header bg-primary text-white py-2">
        <h6 class="mb-0">
            <i class="fa-solid fa-cog me-2"></i>Administrative & System Information
        </h6>
    </div>
    <div class="card-body py-2">
        <div class="row">
            <!-- Document Information -->
            <div class="col-md-6">
                <h6 class="text-primary">
                    <i class="fa-solid fa-file-medical me-2"></i>Document Information
                </h6>
                <p class="mb-1">{{ administrative_data.document_title }} (PS)</p>
                <p class="mb-1 small text-muted">European eHealth Standard</p>

                <div class="mt-2">
                    <strong>DOCUMENT STATUS</strong><br>
                    <span class="badge bg-success me-1">ACTIVE</span>
                    <span class="badge bg-primary me-1">SECURE</span>
                    <span class="badge bg-warning text-dark">NORMAL CONFIDENTIALITY</span>
                </div>

                <div class="mt-2">
                    <small class="text-muted">
                        Creation Date: {{ administrative_data.document_creation_date }}<br>
                        Document ID: {{ administrative_data.document_id }}
                    </small>
                </div>
            </div>

            <!-- Document Custodian -->
            <div class="col-md-6">
                <h6 class="text-primary">
                    <i class="fa-solid fa-shield-alt me-2"></i>Document Custodian
                </h6>
                <p class="mb-1">{{ administrative_data.custodian_name }}</p>

                <div class="mt-2">
                    <strong>CONTACT INFORMATION</strong><br>
                    <small class="text-muted">
                        {% if administrative_data.custodian_organization.telecoms %}
                        {% for telecom in administrative_data.custodian_organization.telecoms %}
                        <i class="fa-solid fa-envelope me-1"></i>{{ telecom.display_value }}<br>
                        {% endfor %}
                        {% endif %}
                    </small>
                </div>

                <div class="mt-2">
                    <strong>ORGANIZATION ADDRESS</strong><br>
                    <small class="text-muted">
                        {% if administrative_data.custodian_organization.addresses %}
                        {% for address in administrative_data.custodian_organization.addresses %}
                        {{ address.street }}<br>
                        {{ address.city }}, {{ address.postalCode }}
                        {% endfor %}
                        {% endif %}
                    </small>
                </div>
            </div>
        </div>
    </div>
</div>
```

---

## CSS Implementation Notes

### Card Styling

```scss
.card {
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);

    .card-header {
        border-radius: 8px 8px 0 0;
        font-weight: 600;

        h6 {
            font-size: 0.9rem;
            margin-bottom: 0;
        }
    }

    .card-body {
        padding: 0.75rem;

        small.text-muted {
            line-height: 1.4;
        }
    }
}

// Equal height cards
.h-100 {
    height: 100% !important;
}

// Responsive card heights
@media (min-width: 992px) {
    .card {
        max-height: 300px;
        overflow-y: auto;
    }
}
```

### Navigation Styling

```scss
.nav-tabs-healthcare {
    border-bottom: 2px solid #dee2e6;

    .nav-link {
        border: none;
        border-bottom: 3px solid transparent;

        &.active {
            border-bottom-color: var(--bs-primary);
            background-color: transparent;
        }
    }
}

.nav-pills {
    .nav-link.btn-sm {
        padding: 0.375rem 0.75rem;
        font-size: 0.8rem;
    }
}
```

---

## Data Binding Requirements

### Django Context Variables

```python
# Required context data for template rendering
context = {
    'patient_identity': {
        'given_name': str,
        'family_name': str,
        'birth_date': str,
        'gender': str,
        'patient_id': str,
        'patient_identifiers': [IdentifierObject],
    },
    'contact_data': {
        'addresses': [AddressObject],
        'telecoms': [TelecomObject],
    },
    'administrative_data': {
        'custodian_name': str,
        'custodian_organization': {
            'name': str,
            'addresses': [AddressObject],
            'telecoms': [TelecomObject],
        },
        'author_hcp': {
            'full_name': str,
            'family_name': str,
            'given_name': str,
            'organization': {
                'name': str,
                'addresses': [AddressObject],
                'telecoms': [TelecomObject],
            },
        },
        'legal_authenticator': {
            'full_name': str,
            'family_name': str,
            'given_name': str,
            'organization': OrganizationObject,
        },
        'document_title': str,
        'document_creation_date': str,
        'document_id': str,
        'document_type': str,
        'guardian': ContactPersonObject,
        'other_contacts': [ContactPersonObject],
    },
}
```

### Service Integration Points

- `ComprehensiveClinicalDataService.get_administrative_data_for_display()`
- `EnhancedCDAXMLParser` for patient identity data
- `CDAAdministrativeExtractor` for healthcare provider information

---

## JavaScript Requirements

### Tab Navigation

```javascript
// Bootstrap 5 tab initialization
document.addEventListener('DOMContentLoaded', function() {
    // Primary tabs
    const primaryTabs = document.querySelectorAll('#patientTabs button[data-bs-toggle="tab"]');
    primaryTabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(event) {
            // Handle primary tab switching
            console.log('Primary tab activated:', event.target.id);
        });
    });

    // Secondary pills
    const secondaryPills = document.querySelectorAll('button[data-bs-toggle="pill"]');
    secondaryPills.forEach(pill => {
        pill.addEventListener('shown.bs.tab', function(event) {
            // Handle secondary navigation
            console.log('Secondary pill activated:', event.target.id);
        });
    });
});
```

---

## Responsive Design Implementation

### Breakpoints

- **Mobile (xs):** Single column layout, stacked cards
- **Tablet (md):** Two-column card layout
- **Desktop (lg):** Three-column card layout for Personal Information
- **Large Desktop (xl):** Maintains three-column with better spacing

### Card Responsiveness

```html
<div class="col-12 col-md-6 col-lg-4">
    <!-- Card content adapts to screen size -->
</div>
```

---

## Testing Checklist

### Functional Testing

- [ ] Primary tab navigation works correctly
- [ ] Secondary pill navigation functions properly
- [ ] Cards display appropriate data
- [ ] Responsive layout functions across devices
- [ ] Icons and fonts load correctly

### Accessibility Testing

- [ ] Keyboard navigation through tabs and pills
- [ ] Screen reader compatibility
- [ ] Color contrast meets WCAG standards
- [ ] ARIA labels are properly implemented

### Data Integration Testing

- [ ] Patient demographic data displays correctly
- [ ] Healthcare provider information populates
- [ ] Contact information renders properly
- [ ] Administrative data shows accurate system info

---

**Implementation Status:** ✅ Production Ready
**Last Tested:** September 28, 2025
**Browser Compatibility:** Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
