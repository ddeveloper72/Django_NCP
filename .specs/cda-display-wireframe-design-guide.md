# CDA Display Wireframe Design Guide

**Document Version:** 1.0  
**Last Updated:** September 28, 2025  
**Status:** Production Reference  
**Purpose:** Wireframe specification for Enhanced CDA Patient Display interface

---

## Overview

This document serves as the definitive wireframe and design specification for the Enhanced CDA Patient Display interface. It documents the approved UX/UI structure that should be preserved and enhanced, not modified without careful consideration.

**CRITICAL:** These wireframes represent the approved production design. Any deviations must be carefully evaluated against user experience principles and healthcare display standards.

---

## Interface Structure

### Primary Navigation Layout

#### Top-Level Tabs
- **Patient Overview** (Default active state)
- **Extended Patient Information** (Tabbed sub-navigation)

#### Sub-Navigation Pills (Extended Patient Information)
- Personal Information (Default active)
- Healthcare Team
- System & Documentation
- Clinical Information
- Original Clinical Document

---

## Wireframe 1: Personal Information Tab (Default View)

**File Reference:** Screenshot 1 - Personal Information active tab

### Layout Structure
```
┌─────────────────────────────────────────────────────────────────┐
│ [Patient Overview] [Extended Patient Information]               │
├─────────────────────────────────────────────────────────────────┤
│ [Personal Information] [Healthcare Team] [System & Doc] etc...  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Patient         │  │ Patient         │  │ Patient         │ │
│  │ Demographics    │  │ Identifiers     │  │ Address         │ │
│  │ ─────────────── │  │ ─────────────── │  │ ─────────────── │ │
│  │ Diana Ferreira  │  │ Patient ID:     │  │ 155, Avenida da │ │
│  │ Birth Date:     │  │ 2-1234-W7       │  │ Liberdade       │ │
│  │ 08/05/1982      │  │                 │  │ Lisbon, 1250-141│ │
│  │ Gender: Female  │  │                 │  │ PT              │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Contact Methods                                             │ │
│  │ ─────────────────────────────────────────────────────────── │ │
│  │ 📞 tel: +351211234567                                       │ │
│  │ 📧 mailto:paciente@gmail.com                               │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Design Specifications
- **Card Layout:** 3-column grid for demographic information
- **Card Colors:** 
  - Patient Demographics: Blue header (Primary)
  - Patient Identifiers: Gray header (Secondary)  
  - Patient Address: Blue header (Info)
  - Contact Methods: Blue header (Primary), spans full width
- **Typography:** Clean, medical-grade typography with clear hierarchy
- **Icons:** FontAwesome icons for visual navigation aids
- **Spacing:** Consistent padding and margins following Bootstrap grid

---

## Wireframe 2: Healthcare Team Tab

**File Reference:** Screenshot 2 - Healthcare Team navigation active

### Layout Structure
```
┌─────────────────────────────────────────────────────────────────┐
│ [Personal Information] [Healthcare Team] [System & Doc] etc...  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌───────────────────────────────────────────────────────────────┐ │
│ │ Healthcare Provider Information                               │ │
│ │ ───────────────────────────────────────────────────────────── │ │
│ │                                                               │ │
│ │ 👨‍⚕️ Healthcare Provider        🏥 Healthcare Organization      │ │
│ │ António Pereira                Centro Hospitalar de Lisboa    │ │
│ │                                Central                        │ │
│ │                                                               │ │
│ │                                CONTACT INFORMATION            │ │
│ │                                📧 mailto:hospital@gmail.com   │ │
│ │                                                               │ │
│ │                                ORGANIZATION ADDRESS           │ │
│ │                                Lisbon - PT                    │ │
│ │                                                               │ │
│ │ ⚖️ Legal Authenticator                                        │ │
│ │ AUTHENTICATOR                                                 │ │
│ │ António Pereira                                               │ │
│ └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Design Specifications
- **Card Layout:** Single large card with internal sections
- **Card Color:** Green header (Success/Healthcare theme)
- **Information Hierarchy:** 
  - Healthcare Provider (Left column)
  - Healthcare Organization (Right column)
  - Contact Information (Centered)
  - Legal Authenticator (Bottom section)
- **Visual Elements:** Medical icons for each section type
- **Background:** Light card background with clear section dividers

---

## Wireframe 3: System & Documentation Tab

**File Reference:** Screenshot 3 - System & Documentation active

### Layout Structure
```
┌─────────────────────────────────────────────────────────────────┐
│ [Personal Information] [Healthcare Team] [System & Doc] etc...  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌───────────────────────────────────────────────────────────────┐ │
│ │ Administrative & System Information                           │ │
│ │ ───────────────────────────────────────────────────────────── │ │
│ │                                                               │ │
│ │ 📄 Document Information        🏥 Document Custodian          │ │
│ │                                                               │ │
│ │ Patient Summary (PS)           Centro Hospitalar de Lisboa    │ │
│ │ European eHealth Standard      Central                        │ │
│ │                                                               │ │
│ │ DOCUMENT STATUS                CONTACT INFORMATION            │ │
│ │ [ACTIVE] [SECURE] [NORMAL      📧 mailto:hospital@gmail.com   │ │
│ │ CONFIDENTIALITY]                                              │ │
│ │                                ORGANIZATION ADDRESS           │ │
│ │ Creation Date: Not specified   Lisbon - PT                    │ │
│ │ Document ID: Not specified                                    │ │
│ └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Design Specifications
- **Card Layout:** Single comprehensive card with two-column internal layout
- **Card Color:** Blue header (Primary/System theme)
- **Status Badges:** Color-coded status indicators
  - ACTIVE: Green badge
  - SECURE: Blue badge  
  - NORMAL CONFIDENTIALITY: Yellow badge
- **Information Architecture:**
  - Document Information (Left column)
  - Document Custodian (Right column)
- **Typography:** System-level information with technical hierarchy

---

## Design Principles

### Visual Hierarchy
1. **Primary Navigation:** Bold, clear tab distinction
2. **Secondary Navigation:** Pill-style buttons for sub-sections
3. **Content Cards:** Bordered cards with colored headers
4. **Information Density:** Balanced spacing, not cluttered

### Color Scheme
- **Primary Blue:** Main navigation and primary actions
- **Secondary Gray:** Supporting information and identifiers
- **Success Green:** Healthcare-related information
- **Info Blue:** Address and location information
- **Warning Yellow:** Status and administrative information

### Typography
- **Headers:** Bold, medical-grade sans-serif
- **Body Text:** Clean, readable font with proper contrast
- **Labels:** Semi-bold for field labels
- **Data:** Regular weight for actual patient data

### Accessibility
- **Color Contrast:** WCAG AA compliant
- **Icon Usage:** Icons paired with text labels
- **Navigation:** Keyboard accessible tab navigation
- **Screen Readers:** Proper ARIA labels and structure

---

## Technical Implementation Notes

### Bootstrap Integration
- Utilizes Bootstrap 5 card components
- Responsive grid system (col-12, col-md-6, col-lg-4)
- Nav pills for sub-navigation
- Badge components for status indicators

### Component Structure
```html
<!-- Primary Tab Navigation -->
<ul class="nav nav-tabs">
  <li class="nav-item">Patient Overview</li>
  <li class="nav-item active">Extended Patient Information</li>
</ul>

<!-- Secondary Pill Navigation -->
<ul class="nav nav-pills nav-fill">
  <li class="nav-link active">Personal Information</li>
  <li class="nav-link">Healthcare Team</li>
  <li class="nav-link">System & Documentation</li>
</ul>

<!-- Card Grid Layout -->
<div class="row g-3">
  <div class="col-12 col-md-6 col-lg-4">
    <div class="card border-primary">
      <div class="card-header bg-primary text-white">
        <h6>Section Title</h6>
      </div>
      <div class="card-body">Content</div>
    </div>
  </div>
</div>
```

### Data Binding Requirements
- Patient demographic data from CDA parser
- Healthcare provider information from administrative data
- System status from document metadata
- Contact information from comprehensive service

---

## Maintenance Guidelines

### DO NOT MODIFY
- Overall layout structure (two-level navigation)
- Card-based information architecture
- Color scheme and visual hierarchy
- Responsive breakpoints

### SAFE TO ENHANCE
- Individual card content (within existing structure)
- Additional data fields (following existing patterns)
- Icon improvements (maintaining current icon system)
- Accessibility improvements

### REQUIRES APPROVAL
- Navigation structure changes
- Layout modifications
- Color scheme alterations
- Typography changes

---

## Future Enhancement Areas

### Potential Improvements
1. **Additional Tabs:** Clinical Information, Original Clinical Document
2. **Enhanced Cards:** More detailed patient information cards
3. **Interactive Elements:** Expandable sections within cards
4. **Mobile Optimization:** Enhanced mobile navigation patterns

### Integration Points
- Clinical data service integration
- Enhanced CDA parser data binding
- Administrative data extraction
- Contact information display

---

**Reference Files:**
- `templates/patient_data/enhanced_patient_cda.html`
- `static/scss/_enhanced_cda.scss`
- `patient_data/services/comprehensive_clinical_data_service.py`

**Related Specifications:**
- CSS Architecture Guide
- Component Standards
- Django Template Commenting Standards