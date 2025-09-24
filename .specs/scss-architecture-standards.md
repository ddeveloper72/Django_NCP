# SCSS Architecture Standards - Django NCP

│   ├── _│   └──_irish_healthcare_theme.scss  # Healthcare theme implementation
├── components/                    # Component-specific stylingriables.scss          # Healthcare colours, breakpoints, typography
│   ├── _mixins.scss             # Reusable mixin library Overview

This specification defines the mandat#### Healthcare Organisation Theme Variables

```scss
:root {
  // Healthcare Brand Colours
  --brand-primary: #{$hco-primary-teal};chitecture standards for all SCSS styles and components in the Django NCP application. The architecture must be **dynamic, modular, reusable, and never duplicated or programmed ad-hoc**. This document ensures maintainable, scalable, and professional CSS architecture.

## Core Principles

### 1. Dynamic Architecture

- **Context-Aware Styling**: Components must adapt to their context automatically
- **Smart Color Systems**: Mixins that calculate appropriate colors based on backgrounds
- **Responsive by Default**: All components must work across all device sizes
- **Theme-Aware**: Components must work with healthcare organization color palette variations

### 2. Modular Design

- **Single Responsibility**: Each SCSS file has one clear purpose
- **Atomic Components**: Build complex UI from simple, reusable atoms
- **Layered Architecture**: Clear separation between utilities, components, layouts, and pages
- **Import Hierarchy**: Structured import order for predictable cascade

### 3. Reusability First

- **Mixin-Based Logic**: Complex styling patterns as reusable mixins
- **Variable-Driven**: All magic numbers and colors as variables
- **Component Classes**: Generic classes that work in multiple contexts
- **Extensible Patterns**: Easy to extend without modification

### 4. Zero Duplication

- **DRY Principle**: Never repeat styling rules
- **Centralized Patterns**: Common patterns in mixins and utilities
- **Inheritance Over Repetition**: Use @extend and mixins instead of copying
- **Systematic Overrides**: Specific overrides only where necessary

## Architecture Structure

### Directory Organization

```

/static/scss/
├── main.scss                    # Master import file
├── utils/                       # Foundation utilities
│   ├── _variables.scss          # HSE colors, breakpoints, typography
│   ├──_mixins.scss            # Reusable patterns and functions
│   ├── _tab_mixins.scss        # Tab-specific utilities
│   └── _functions.scss         # SCSS functions for calculations
├── base/                       # Base styles and resets
│   ├──_reset.scss            # CSS reset and normalize
│   ├── _typography.scss       # Font definitions and text styles
│   ├──_accessibility.scss    # WCAG compliance utilities
│   └── _irish_healthcare_theme.scss  # HSE theme implementation
├── components/                 # Reusable UI components
│   ├──_buttons.scss          # Button variants and states
│   ├── _cards.scss            # Card layouts and types
│   ├──_forms.scss            # Form elements and validation
│   ├── _navigation.scss       # Navigation patterns
│   ├──_breadcrumb.scss       # Breadcrumb navigation
│   ├── _modals.scss           # Modal dialogs
│   ├──_tables.scss           # Table styling
│   ├── _icons.scss            # Icon styling and positioning
│   └──_alerts.scss           # Alert and notification components
├── layouts/                    # Page layout patterns
│   ├── _header.scss           # Header layouts
│   ├──_footer.scss           # Footer layouts
│   ├── _sidebar.scss          # Sidebar patterns
│   └──_grid.scss             # Grid system
└── pages/                      # Page-specific styles
    ├── _enhanced_cda.scss     # CDA document display
    ├── _patient_form.scss     # Patient search forms
    └── _admin.scss            # Admin interface styling

```

## Component Development Standards

### 1. Context-Aware Components

**Mandatory Pattern**: All components must be context-aware and automatically adapt to their environment.

#### Smart Color Mixin (Required)

```scss
// ALL icon styling must use context-aware colors
@mixin smart-icon-color(
  $bg-color: null,
  $light-color: var(--healthcare-text-light),
  $dark-color: #2d3748
) {
  @if $bg-color {
    $luminance: calculate-luminance($bg-color);

    @if $luminance > 0.5 {
      color: $dark-color !important; // Light background = dark text
    } @else {
      color: $light-color !important; // Dark background = light text
    }
  } @else {
    color: $light-color !important; // Default for dark healthcare themes
    background: $dark-color;
  }
}
```

#### Context-Aware Button Example

```scss
.btn {
  @include button-base; // Shared button foundation

  // Context-aware variations
  &.btn-outline-secondary {
    @include context-aware-outline($secondary-color);
  }

  // Smart icon colors based on button background
  i {
    @include smart-icon-color(); // Automatic color selection

    // Specific overrides only when necessary
    &.page-action-icon {
      @include smart-icon-color(#ffffff, #2d3748, #ffffff);
    }
  }
}
```

### 2. Modular Mixin System

**Mandatory Pattern**: All complex styling patterns must be mixins, never repeated inline.

#### Button Foundation Mixin

```scss
@mixin button-base {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: $space-sm $space-md;
  border-radius: $border-radius-md;
  font-family: $font-family-primary;
  font-weight: $font-weight-medium;
  text-decoration: none;
  transition: all $transition-hco;
  cursor: pointer;
  border: 2px solid transparent;

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    pointer-events: none;
  }
}
```

#### Layout Mixins

```scss
@mixin container {
  width: 100%;
  max-width: $container-max-width;
  margin: 0 auto;
  padding: 0 $space-md;

  @media (min-width: $breakpoint-lg) {
    padding: 0 $space-lg;
  }
}

@mixin flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

@mixin flex-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
```

### 3. Variable-Driven Design

**Mandatory Pattern**: All design tokens must be variables. No magic numbers in component files.

#### Healthcare Organisation Color System

```scss
// Healthcare Organisation Primary Colors - Based on Healthcare Industry Standards
$hco-primary-teal: #007b7f;
$hco-primary-teal-dark: #005b5f;
$hco-primary-teal-light: #33969a;
$hco-primary-teal-lighter: #80bebf;

// Semantic Color Variables
$primary-color: $hco-primary-teal;
$success-color: $hco-secondary-green;
$warning-color: $warning-orange;
$error-color: $error-red;

// Context Variables
$text-dark: $neutral-dark;
$text-light: $white;
$bg-light: #f7fafc;
$bg-dark: $hco-primary-teal;
```

#### Spacing System

```scss
// Consistent spacing scale
$space-xs: 0.25rem;   // 4px
$space-sm: 0.5rem;    // 8px
$space-md: 1rem;      // 16px
$space-lg: 1.5rem;    // 24px
$space-xl: 2rem;      // 32px
$space-xxl: 3rem;     // 48px
$space-xxxl: 4rem;    // 64px
```

#### Typography Scale

```scss
$font-size-xs: 0.75rem;   // 12px
$font-size-sm: 0.875rem;  // 14px
$font-size-base: 1rem;    // 16px
$font-size-lg: 1.125rem;  // 18px
$font-size-xl: 1.25rem;   // 20px
$font-size-xxl: 1.5rem;   // 24px
$font-size-xxxl: 2rem;    // 32px
```

### 4. Component Specificity Rules

**Mandatory Pattern**: Use specific selectors to prevent style conflicts without overusing !important.

#### Specificity Hierarchy

1. **Utilities**: Highest specificity for overrides
2. **Page-specific**: Medium-high specificity
3. **Components**: Medium specificity
4. **Base**: Lowest specificity

#### Example: Icon Visibility Fix

```scss
// ❌ WRONG: Overly broad selector
.btn i {
  color: white !important;
}

// ✅ CORRECT: Specific, contextual selector
.page-context .page-actions .btn i.page-action-icon {
  @include smart-icon-color(#ffffff, #2d3748, #ffffff);

  // Specific FontAwesome overrides only when necessary
  &.fa-solid,
  &.fa-regular,
  &.fa-brands {
    @include smart-icon-color(#ffffff, #2d3748, #ffffff);
  }
}
```

## Implementation Guidelines

### 1. Creating New Components

#### Step 1: Identify Reusability

- Can this be used in multiple contexts?
- Does it need to adapt to different backgrounds?
- What are the minimum and maximum variations needed?

#### Step 2: Create Atomic Components

```scss
// ✅ CORRECT: Atomic, reusable component
.service-card {
  @include card-base; // Shared card foundation

  &__header {
    @include flex-center;
    background: var(--card-header-bg, $hco-primary-teal);

    .service-icon {
      @include perfect-icon-center; // Reusable centering
      @include smart-icon-color(var(--card-header-bg)); // Context-aware color
    }
  }

  &__content {
    padding: $space-md;
  }

  &__footer {
    @include flex-between;
    padding: $space-sm $space-md;

    .btn {
      @include button-base; // Reusable button foundation
    }
  }
}
```

#### Step 3: Create Variations, Not New Components

```scss
// ✅ CORRECT: Variations of the same component
.service-card {
  // Base implementation above...

  // Healthcare Theme variations
  &--teal {
    --card-header-bg: #{$hco-primary-teal};
  }

  &--green {
    --card-header-bg: #{$hco-secondary-green};
  }

  &--large {
    .service-card__header {
      padding: $space-lg;
    }
  }
}
```

### 2. Extending Existing Components

#### Use @extend for Shared Patterns

```scss
// ✅ CORRECT: Extend shared patterns
%card-shadow {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: box-shadow $transition-hco;

  &:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  }
}

.patient-card {
  @extend %card-shadow;
  // Additional patient-specific styling
}

.admin-card {
  @extend %card-shadow;
  // Additional admin-specific styling
}
```

### 3. Theme Integration

#### HSE Healthcare Theme Variables

```scss
:root {
  // HSE Brand Colors
  --healthcare-primary: #{$hse-primary-teal};
  --healthcare-secondary: #{$hse-secondary-green};
  --healthcare-accent: #{$hse-accent-blue};

  // Context-Aware Text Colors
  --healthcare-text-light: #{$white};
  --healthcare-text-dark: #{$neutral-dark};
  --healthcare-text-muted: #{$neutral-light};

  // Dynamic Background Colors
  --healthcare-bg-light: #{$bg-light};
  --healthcare-bg-dark: #{$hse-primary-teal};
}
```

## Quality Assurance

### Pre-Commit Checklist

Before committing any SCSS changes, verify:

- [ ] **No Magic Numbers**: All measurements are variables
- [ ] **No Color Hardcoding**: All colors are HSE theme variables
- [ ] **Context Awareness**: Components adapt to light/dark backgrounds
- [ ] **Mobile Responsive**: Tested on mobile, tablet, desktop
- [ ] **No Duplication**: No repeated styling patterns
- [ ] **Proper Specificity**: Specific selectors without excessive !important
- [ ] **Mixin Usage**: Complex patterns use mixins, not inline styles
- [ ] **Variable Naming**: Clear, semantic variable names

### Testing Requirements

#### Cross-Browser Testing

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

#### Accessibility Testing

- WCAG 2.1 AA compliance
- Color contrast ratios meet standards
- Focus indicators are visible
- Screen reader compatibility

#### Performance Testing

- CSS bundle size optimization
- Critical CSS inlining for above-the-fold content
- No unused CSS rules

## Migration Strategy

### Existing Code Remediation

#### Phase 1: Audit and Document

1. Identify all inline styles and ad-hoc CSS
2. Document component patterns and variations
3. Create inventory of colors, spacing, and typography used

#### Phase 2: Create Foundation

1. Establish variable system
2. Build mixin library
3. Create base component patterns

#### Phase 3: Systematic Replacement

1. Replace inline styles with component classes
2. Consolidate duplicate patterns into mixins
3. Implement context-aware color system

#### Phase 4: Optimization

1. Remove unused CSS
2. Optimize specificity hierarchy
3. Performance testing and tuning

## Conclusion

This SCSS architecture ensures maintainable, scalable, and professional CSS that adapts to context automatically. By following these standards, the Django NCP application will have a robust, future-proof styling system that eliminates technical debt and supports rapid, consistent development.

### Key Takeaways

1. **Always Context-Aware**: Components must adapt to their environment
2. **Never Repeat**: Use mixins and variables instead of duplicating code
3. **Think Reusable**: Design components that work in multiple contexts
4. **Plan for Scale**: Architecture must support growth and change
5. **Test Everything**: Ensure compatibility across browsers and devices

This specification is living documentation that should evolve with the application while maintaining these core principles.
