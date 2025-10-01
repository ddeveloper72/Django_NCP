# SCSS Quick Reference Guide

## Mandatory Checklist for All SCSS Development

### Before Writing Any CSS

- [ ] Check if similar component already exists
- [ ] Identify if pattern can be reused across contexts
- [ ] Plan for light/dark background variations
- [ ] Consider mobile, tablet, desktop breakpoints

### Component Creation Checklist

- [ ] Use BEM methodology for naming (`.block__element--modifier`)
- [ ] Start with foundation mixin if available
- [ ] Use only HSE theme variables for colors
- [ ] Use only spacing variables for measurements
- [ ] Include context-aware icon colors with `@include smart-icon-color()`
- [ ] Add responsive breakpoints using mobile-first approach
- [ ] Include hover/focus/active states
- [ ] Add proper accessibility features (focus rings, etc.)

### Code Review Checklist

- [ ] No magic numbers (hardcoded px/em/rem values)
- [ ] No hardcoded colors (use variables only)
- [ ] No duplicate styling patterns (extract to mixins)
- [ ] Proper specificity hierarchy (not overusing !important)
- [ ] Context-aware icon implementations
- [ ] Mobile-responsive design
- [ ] Accessibility compliance (color contrast, focus states)

## Essential Mixins Reference

### Layout Mixins

```scss
@include container;              // Responsive container
@include flex-center;           // Center content with flexbox
@include flex-between;          // Space-between with flexbox
@include perfect-icon-center;   // Perfect icon centering (mandatory for badges)
```

### Color Mixins

```scss
@include smart-icon-color();                              // Auto light/dark icon color
@include smart-icon-color($bg-color);                     // Icon color based on background
@include smart-icon-color($bg, $light-color, $dark-color); // Custom light/dark colors
```

### Component Foundation Mixins

```scss
@include button-base;           // Base button styling
@include card-foundation;       // Base card styling
@include form-input-base;       // Base form input styling
@include nav-link-base;         // Base navigation link styling
```

### Responsive Mixins

```scss
@include mobile-down { /* styles */ }      // Max-width: 767px
@include tablet-up { /* styles */ }        // Min-width: 768px
@include desktop-up { /* styles */ }       // Min-width: 1024px
@include large-desktop-up { /* styles */ } // Min-width: 1440px
```

### Animation Mixins

```scss
@include smooth-hover();                    // Default hover animation
@include smooth-hover(translateX(4px));     // Custom hover transform
@include loading-pulse;                     // Loading animation
@include focus-ring($color);               // Accessibility focus ring
```

## Essential Variables Reference

### HSE Colors

```scss
// Primary HSE Colors
$hse-primary-teal: #007b7f;
$hse-primary-teal-dark: #005b5f;
$hse-primary-teal-light: #33969a;
$hse-secondary-green: #2d5a27;
$hse-accent-blue: #1e3a5f;

// Semantic Colors
$primary-color: $hse-primary-teal;
$success-color: $hse-secondary-green;
$warning-color: $warning-orange;
$error-color: $error-red;

// Text Colors
$text-dark: #2d3748;
$text-light: #ffffff;
$text-muted: #718096;
```

### Spacing System

```scss
$space-xs: 0.25rem;    // 4px
$space-sm: 0.5rem;     // 8px
$space-md: 1rem;       // 16px
$space-lg: 1.5rem;     // 24px
$space-xl: 2rem;       // 32px
$space-xxl: 3rem;      // 48px
$space-xxxl: 4rem;     // 64px
```

### Typography

```scss
$font-size-xs: 0.75rem;   // 12px
$font-size-sm: 0.875rem;  // 14px
$font-size-base: 1rem;    // 16px
$font-size-lg: 1.125rem;  // 18px
$font-size-xl: 1.25rem;   // 20px

$font-weight-normal: 400;
$font-weight-medium: 500;
$font-weight-semibold: 600;
$font-weight-bold: 700;
```

### Border Radius

```scss
$border-radius-sm: 0.25rem;  // 4px
$border-radius-md: 0.375rem; // 6px
$border-radius-lg: 0.5rem;   // 8px
$border-radius-xl: 0.75rem;  // 12px
```

## Common Patterns Quick Copy

### Context-Aware Button

```scss
.my-button {
  @include button-base;
  background: var(--button-bg, $hse-primary-teal);
  color: var(--button-text, $white);

  i {
    @include smart-icon-color(var(--button-bg));
  }

  &:hover {
    background: var(--button-bg-hover, $hse-primary-teal-dark);
  }
}
```

### Responsive Card

```scss
.my-card {
  @include card-foundation;
  padding: $space-sm;

  @include tablet-up {
    padding: $space-md;
  }

  @include desktop-up {
    padding: $space-lg;
  }

  &__header {
    background: $hse-primary-teal;
    color: $white;
    padding: $space-md;

    i {
      @include smart-icon-color($hse-primary-teal);
    }
  }
}
```

### Form Input with States

```scss
.my-input {
  @include form-input-base;

  &:focus {
    @include focus-ring($hse-primary-teal);
    border-color: $hse-primary-teal;
  }

  &--error {
    border-color: $error-red;
    background: rgba($error-red, 0.05);
  }

  &--success {
    border-color: $success-color;
    background: rgba($success-color, 0.05);
  }
}
```

### Perfect Icon Centering

```scss
.icon-badge {
  @include perfect-icon-center;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: $hse-primary-teal;

  i {
    @include smart-icon-color($hse-primary-teal);
    font-size: 1.2em;
  }
}
```

## Troubleshooting Common Issues

### Issue: White Icons on Light Background

**Solution**: Use context-aware icon colors

```scss
// ❌ Wrong
i {
  color: white;
}

// ✅ Correct
i {
  @include smart-icon-color(); // Automatic adaptation
}
```

### Issue: Repeated Code Across Components

**Solution**: Extract to mixin

```scss
// ❌ Wrong - repeated in multiple components
.card-1 {
  padding: 1rem;
  border-radius: 0.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.card-2 {
  padding: 1rem;
  border-radius: 0.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

// ✅ Correct - shared mixin
@mixin card-base {
  padding: $space-md;
  border-radius: $border-radius-lg;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.card-1 {
  @include card-base;
}
.card-2 {
  @include card-base;
}
```

### Issue: Magic Numbers

**Solution**: Use spacing variables

```scss
// ❌ Wrong
.component {
  padding: 12px 16px;
  margin-bottom: 24px;
}

// ✅ Correct
.component {
  padding: $space-sm $space-md;
  margin-bottom: $space-lg;
}
```

### Issue: Non-Responsive Design

**Solution**: Mobile-first approach

```scss
// ❌ Wrong
.component {
  width: 800px;
}

// ✅ Correct
.component {
  width: 100%; // Mobile first

  @include tablet-up {
    max-width: 600px;
  }

  @include desktop-up {
    max-width: 800px;
  }
}
```

### Issue: Accessibility Problems

**Solution**: Include focus states and proper contrast

```scss
.interactive-element {
  // Always include focus state
  &:focus {
    @include focus-ring($hse-primary-teal);
  }

  // Ensure color contrast
  color: $text-dark; // High contrast
  background: $white;
}
```

## Performance Tips

### Use CSS Custom Properties for Theming

```scss
.themeable-component {
  background: var(--component-bg, $default-bg);
  color: var(--component-text, $default-text);

  // Theme variations
  &--primary {
    --component-bg: #{$hse-primary-teal};
    --component-text: #{$white};
  }
}
```

### Optimize Selectors

```scss
// ❌ Inefficient
div.card .header h2.title {
  font-size: $font-size-lg;
}

// ✅ Efficient
.card__title {
  font-size: $font-size-lg;
}
```

### Use @extend for Shared Styles

```scss
%button-shared {
  padding: $space-sm $space-md;
  border: none;
  border-radius: $border-radius-md;
}

.btn-primary {
  @extend %button-shared;
  background: $hse-primary-teal;
}

.btn-secondary {
  @extend %button-shared;
  background: $hse-secondary-green;
}
```

This quick reference ensures consistent, professional SCSS development following Django NCP standards.
