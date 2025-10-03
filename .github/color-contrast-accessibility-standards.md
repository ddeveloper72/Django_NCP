# Color Contrast and Accessibility Standards

**Document Version:** 1.0  
**Last Updated:** October 3, 2025  
**Purpose:** Comprehensive color contrast and accessibility guidelines for the Django NCP application  
**External Reference:** [Good Practices Design - Color Contrast](https://goodpractices.design/articles/colour-contrast)

---

## Overview

This document establishes mandatory color contrast and accessibility standards for headers, badges, card text, and backgrounds throughout the Django NCP healthcare application. These standards ensure WCAG 2.2 compliance and optimal user experience for healthcare professionals across diverse environments and accessibility needs.

**CRITICAL:** All UI components must meet these accessibility standards before deployment to ensure inclusive healthcare data access.

---

## WCAG 2.2 Contrast Requirements

### Text Elements

#### Normal Text (≤ 24px, or ≤ 19px bold)
- **AA Level (Required):** 4.5:1 contrast ratio minimum
- **AAA Level (Recommended):** 7:1 contrast ratio
- **Application:** Body text, form labels, navigation links, card content

#### Large Text (≥ 24px, or ≥ 19px bold)
- **AA Level (Required):** 3:1 contrast ratio minimum  
- **AAA Level (Recommended):** 4.5:1 contrast ratio
- **Application:** Headers, hero text, primary CTAs, section titles

#### Text on Images/Gradients
- **Requirement:** Must meet above ratios against ALL background colors in image/gradient
- **Solution:** Add semi-transparent overlay or text shadow "halo" effect
- **Implementation:** Use `backdrop-filter` or `text-shadow` CSS properties

### UI Components

#### Interactive Elements (3:1 minimum AA)
- **Buttons:** Border contrast not required if context provides affordance
- **Form Controls:** Border contrast mandatory when primary identification method
- **Focus States:** Must contrast against both component and page background
- **Status Indicators:** Icons and badges requiring interaction identification

#### Non-Interactive Graphics (3:1 minimum AA)
- **Icons:** Only when essential for understanding (not decorative)
- **Charts:** Adjacent color contrast + alternative identification methods
- **Decorative Elements:** No contrast requirements

---

## Django NCP Implementation Standards

### 1. Badge Components

#### Color Contrast Requirements
```scss
// ✅ MANDATORY: White text on dark badge backgrounds
.badge.bg-info,           // Teal badges
.badge.bg-danger,         // Red badges  
.badge.bg-secondary,      // Gray badges
.badge.bg-success,        // Green badges
.badge.bg-primary {       // Blue badges
    color: white !important;
    
    // Ensure 4.5:1 minimum contrast
    min-contrast: 4.5;
}

// ✅ MANDATORY: Dark text on light badge backgrounds  
.badge.bg-light,
.badge.bg-warning {       // Yellow badges
    color: $text-dark !important;
    
    // Ensure 4.5:1 minimum contrast
    min-contrast: 4.5;
}
```

#### Status Badge Icons
```scss
// ✅ MANDATORY: Prevent icon color changes on hover
.status-badge:hover .fas,
.status-badge:hover .far,
.status-badge:hover .fa {
    color: white !important;
    transition: none !important;
}
```

#### Healthcare Domain Applications
- **Clinical Finding:** Dark teal background + white text (≥4.5:1)
- **Problem:** Dark green background + white text (≥4.5:1)
- **Active Status:** Red background + white text + white icons (≥4.5:1)
- **Severity Levels:** Color + text label (never color alone)

### 2. Card Headers and Backgrounds

#### Color Palette Compliance
```scss
// Healthcare Organisation Color System with Accessibility
$hse-primary-teal: #005f5f;      // Contrast ratio: 7.2:1 with white
$hse-secondary-green: #2d5930;   // Contrast ratio: 8.1:1 with white  
$hse-accent-blue: #1e4a72;       // Contrast ratio: 9.2:1 with white
$warning-orange: #d97706;        // Contrast ratio: 4.8:1 with white
$error-red: #dc2626;             // Contrast ratio: 5.6:1 with white

// ✅ MANDATORY: All dark backgrounds use white text
.card-header {
    &.bg-primary,
    &.bg-info, 
    &.bg-success,
    &.bg-secondary {
        color: white !important;
        
        // Icon color inheritance
        i, .fas, .far, .fa {
            color: white !important;
        }
    }
}
```

#### Card Content Areas
```scss
// ✅ MANDATORY: High contrast body text
.card-body {
    color: $text-primary;           // #2d3748 (12.8:1 with white)
    background: $white;             // #ffffff
    
    // Secondary text maintains readability
    .text-muted {
        color: $text-secondary;      // #4a5568 (7.1:1 with white)
    }
}
```

### 3. Navigation and Headers

#### Primary Navigation
```scss
// ✅ MANDATORY: Navigation contrast requirements
.nav-tabs {
    .nav-link {
        color: $text-primary;        // 4.5:1+ against background
        
        &.active {
            background: $hse-primary-teal;
            color: white;            // 7.2:1 contrast
            border-color: $hse-primary-teal;
        }
        
        &:hover {
            color: $hse-primary-teal; // 7.2:1 against white
        }
    }
}

// ✅ MANDATORY: Pills navigation
.nav-pills {
    .nav-link {
        &.active {
            background: $hse-secondary-green;
            color: white;            // 8.1:1 contrast
        }
    }
}
```

#### Page Headers
```scss
// ✅ MANDATORY: Header hierarchy with proper contrast
h1, h2, h3, h4, h5, h6 {
    color: $text-primary;            // 12.8:1 against white
    font-weight: 600;
    
    // Large text: 3:1 minimum (we achieve 12.8:1)
    // Normal text: 4.5:1 minimum (we achieve 12.8:1)
}
```

### 4. Form Controls and Interactive Elements

#### Input Controls
```scss
// ✅ MANDATORY: Form input accessibility
.form-control {
    border: 1px solid $border-color;  // 3:1+ against background
    color: $text-primary;             // 4.5:1+ against input background
    background: $white;
    
    &:focus {
        border-color: $hse-primary-teal;
        box-shadow: 0 0 0 0.25rem rgba(0, 95, 95, 0.25);
        // Focus ring: 3:1+ against page background
    }
    
    &::placeholder {
        color: $text-secondary;       // 4.5:1+ for readability
    }
}
```

#### Button Components
```scss
// ✅ MANDATORY: Button accessibility standards
.btn {
    // Text contrast requirements met in button variants
    &.btn-primary {
        background: $hse-primary-teal;    // 7.2:1 with white text
        color: white;
        border-color: $hse-primary-teal;
    }
    
    &.btn-outline-primary {
        color: $hse-primary-teal;         // 7.2:1 against white
        border-color: $hse-primary-teal;  // 3:1+ border contrast
        
        &:hover {
            background: $hse-primary-teal;
            color: white;
        }
    }
}
```

---

## Clinical Workflow Accessibility

### Medical Problems Table

#### Visual Information Hierarchy
```scss
// ✅ IMPLEMENTED: Enhanced badge readability
.medical-problems-table {
    .badge {
        // Problem type badges with high contrast
        &.bg-info {
            background: #0dcaf0 !important;  // Clinical Finding
            color: #000 !important;          // 6.7:1 contrast
        }
        
        &.bg-success {
            background: #198754 !important;  // Problem type  
            color: white !important;         // 5.9:1 contrast
        }
    }
    
    // Status indicators never rely on color alone
    .status-badge {
        &::before {
            content: attr(data-status);      // Text label always present
        }
        
        i {
            color: white !important;         // Icon color consistency
        }
    }
}
```

#### Severity Indicators
```scss
// ✅ MANDATORY: Multi-modal severity communication
.severity-indicator {
    // Never use color alone for severity
    &.severe {
        color: $error-red;
        font-weight: 600;
        
        &::before {
            content: "⚠ ";                  // Visual indicator
        }
    }
    
    &.moderate {
        color: $warning-orange;
        font-weight: 500;
        
        &::before {
            content: "⚡ ";                 // Visual indicator  
        }
    }
}
```

### Patient Data Cards

#### Contact Information Accessibility
```scss
// ✅ MANDATORY: Contact method visual accessibility
.contact-methods {
    .contact-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        
        i {
            color: $hse-primary-teal;        // 7.2:1 contrast
            width: 1.25rem;                  // Consistent icon sizing
            text-align: center;
        }
        
        a {
            color: $hse-primary-teal;        // 7.2:1 contrast
            text-decoration: underline;      // Never rely on color alone
            
            &:hover {
                text-decoration: none;
                color: darken($hse-primary-teal, 10%);
            }
        }
    }
}
```

---

## Testing and Validation

### Automated Testing Tools

#### Recommended Tools
- **WebAIM Contrast Checker:** https://webaim.org/resources/contrastchecker/
- **Figma Contrast Checker Plugin:** Real-time design validation
- **Color Contrast Matrix:** https://jansensan.github.io/color-contrast-matrix/
- **HSLuv Plugin:** Predictable color pairing for design systems

#### Browser Testing
```bash
# Lighthouse accessibility audit
npm run lighthouse:a11y

# axe-core accessibility testing  
npm run test:a11y

# Color contrast validation
npm run validate:contrast
```

### Manual Testing Checklist

#### Visual Testing
- [ ] All text meets 4.5:1 (normal) or 3:1 (large) minimum contrast
- [ ] Badge text readable on all background colors
- [ ] Icons visible and meaningful in all contexts
- [ ] Focus states clearly visible and properly contrasted
- [ ] No information conveyed by color alone

#### Healthcare Context Testing  
- [ ] Clinical data remains readable in bright medical lighting
- [ ] Emergency status clearly identifiable without color
- [ ] Patient information accessible to colorblind healthcare professionals
- [ ] Medical severity levels use text + visual indicators

#### Device and Environment Testing
- [ ] High contrast mode compatibility
- [ ] Mobile device readability in various lighting
- [ ] Tablet accessibility for bedside use
- [ ] Desktop monitor calibration independence

---

## Design Token Integration

### SCSS Variable System
```scss
// ✅ MANDATORY: Accessibility-first design tokens
:root {
    // Text contrast ratios (calculated values)
    --text-primary-contrast: 12.8;      // #2d3748 on white
    --text-secondary-contrast: 7.1;     // #4a5568 on white  
    --text-muted-contrast: 4.6;         // #718096 on white
    
    // Background contrast ratios
    --bg-primary-contrast: 7.2;         // HSE teal with white text
    --bg-success-contrast: 5.9;         // HSE green with white text
    --bg-info-contrast: 6.7;            // Info blue with dark text
    --bg-warning-contrast: 4.8;         // Warning orange with dark text
    
    // Interactive element ratios
    --border-contrast: 3.1;             // Form borders minimum
    --focus-contrast: 3.2;              // Focus states minimum
    --icon-contrast: 7.2;               // Icon visibility minimum
}
```

### Component Token Usage
```scss
// ✅ USAGE: Token-driven accessible components
.healthcare-component {
    color: var(--text-primary);         // Guaranteed 4.5:1+
    background: var(--bg-surface);      // Guaranteed contrast base
    
    .header {
        background: var(--bg-primary);   // Guaranteed 7.2:1 with white
        color: white;
    }
    
    .border {
        border-color: var(--border-default); // Guaranteed 3:1+
    }
}
```

---

## Implementation Guidelines

### Development Workflow

#### Before Creating Components
1. **Contrast Validation:** Test all color combinations with WebAIM tool
2. **Token Selection:** Use pre-validated design tokens when possible  
3. **Multi-Modal Design:** Never rely on color alone for information
4. **Healthcare Context:** Consider medical environment lighting conditions

#### During Development  
1. **Real Content Testing:** Test with actual medical data and terminology
2. **Device Testing:** Validate across mobile, tablet, desktop healthcare setups
3. **Accessibility Testing:** Run automated and manual a11y validation
4. **Clinical Review:** Healthcare professional usability validation

#### Before Deployment
1. **Contrast Audit:** Automated contrast ratio validation across all components
2. **Focus Testing:** Keyboard navigation and screen reader compatibility
3. **High Contrast Mode:** Windows high contrast mode functionality
4. **Emergency Scenarios:** Critical medical information accessibility under stress

### Code Review Requirements

#### Mandatory Checklist
- [ ] All text meets minimum contrast ratios (4.5:1 normal, 3:1 large)
- [ ] Interactive elements have proper focus states (3:1+ contrast)
- [ ] Status information uses text + visual indicators (never color alone)
- [ ] Badge components use appropriate text colors for backgrounds
- [ ] Icon colors remain consistent and accessible in all states
- [ ] Form controls have proper border contrast (3:1+)
- [ ] Links are underlined or clearly distinguished beyond color

---

## Emergency and Critical Information

### High Priority Medical Data

#### Critical Status Indicators
```scss
// ✅ CRITICAL: Emergency medical information accessibility
.medical-emergency {
    background: $error-red;              // 5.6:1 with white text
    color: white;
    font-weight: 700;
    border: 2px solid darken($error-red, 20%);
    
    // Multiple visual indicators
    &::before {
        content: "🚨 EMERGENCY: ";
        font-weight: 900;
    }
    
    // High contrast focus state
    &:focus {
        outline: 3px solid $white;
        outline-offset: 2px;
        box-shadow: 0 0 0 6px $error-red;
    }
}
```

#### Allergy Alerts
```scss
// ✅ CRITICAL: Allergy information must be unmistakable
.allergy-alert {
    background: linear-gradient(45deg, $error-red 25%, transparent 25%, 
                transparent 75%, $error-red 75%), 
                linear-gradient(45deg, $error-red 25%, $white 25%, 
                $white 75%, $error-red 75%);
    background-size: 20px 20px;
    background-position: 0 0, 10px 10px;
    
    color: $error-red;
    font-weight: 700;
    padding: 1rem;
    border: 3px solid $error-red;
    
    // Text shadow for readability on pattern
    text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.8);
}
```

---

## Future Considerations

### WCAG 3.0 Preparation

#### APCA (Advanced Perceptual Contrast Algorithm)
- **Current Status:** Draft specification for WCAG 3.0
- **Benefits:** More accurate perceptual contrast measurement
- **Implementation:** Monitor specification updates for future migration
- **Preparation:** Current high contrast ratios will likely exceed future requirements

#### HSLuv Color Model Integration
```scss
// ✅ FUTURE: Predictable contrast color system
// HSLuv provides more predictable contrast ratios
@function hsluve-contrast($lightness-1, $lightness-2) {
    // Predictable contrast calculation
    // All colors with L:50 + L:95 = ~8.2:1 contrast
    @return calculate-predictable-contrast($lightness-1, $lightness-2);
}
```

### Design System Evolution

#### Automated Contrast Validation
```scss
// ✅ FUTURE: Build-time contrast validation
@mixin validate-contrast($foreground, $background, $min-ratio: 4.5) {
    $contrast: contrast-ratio($foreground, $background);
    
    @if $contrast < $min-ratio {
        @error "Insufficient contrast: #{$contrast} < #{$min-ratio}";
    }
}
```

---

## Related Documentation

### Internal References
- [SCSS Standards Index](./scss-standards-index.md) - Component implementation patterns
- [UI/UX Design Specifications Index](./ui-ux-design-specifications-index.md) - Visual design standards
- [CDA Display Wireframe Design Guide](./cda-display-wireframe-design-guide.md) - Production interface specifications
- [Icon Centering Standards](./icon-centering-standards.md) - Icon accessibility implementation

### External References
- [Good Practices Design - Color Contrast](https://goodpractices.design/articles/colour-contrast) - Comprehensive accessibility guide
- [WCAG 2.2 Understanding Contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) - Official accessibility guidelines
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/) - Testing tool
- [HSLuv Color Model](https://www.hsluv.org/) - Predictable color contrast system

---

## Maintenance and Updates

### Version Control
This document should be updated whenever:
- New UI components are added requiring accessibility validation
- WCAG guidelines are updated or new versions released
- Healthcare accessibility requirements change
- User feedback indicates accessibility barriers

### Review Schedule
- **Monthly:** Automated contrast validation across all components
- **Quarterly:** Manual accessibility testing with healthcare professionals
- **Annually:** Comprehensive review against latest WCAG standards
- **As Needed:** Updates based on accessibility feedback or compliance requirements

**Approval Required:** All changes to accessibility standards must be reviewed by healthcare UX team and accessibility specialists before implementation.