# SCSS Component Development Patterns

## Overview

This specification provides concrete patterns and examples for developing SCSS components that follow the Django NCP architecture standards. These patterns ensure consistency, reusability, and maintainability across the entire application.

## Component Development Lifecycle

### 1. Analysis Phase

Before creating any component, answer these questions:

#### Context Analysis

- **Where will this component be used?** (Light backgrounds, dark backgrounds, both?)
- **What variations are needed?** (Sizes, colors, states?)
- **How will it interact with other components?** (Nesting, siblings, containers?)

#### Reusability Assessment

- **Can this be broken into smaller, reusable parts?**
- **Do similar components already exist that can be extended?**
- **What's the minimum viable component that serves multiple use cases?**

### 2. Foundation Pattern

Every component must start with this foundation pattern:

```scss
// Component: .component-name
// Usage: Reusable [component-type] for [use-cases]
// Dependencies: [list of required mixins/variables]
// Examples: [link to usage examples]

.component-name {
  // 1. Foundation mixin (required)
  @include component-base-mixin;

  // 2. Core properties using variables only
  background: var(--component-bg, $default-bg);
  color: var(--component-text, $default-text);
  padding: $component-padding;

  // 3. Context-aware adaptations
  @include context-aware-styling;

  // 4. Child elements (BEM methodology)
  &__element {
    // Element-specific styling
  }

  // 5. Modifier variations
  &--modifier {
    // Modifier-specific styling
  }

  // 6. State variations
  &:hover,
  &:focus,
  &:active,
  &.is-active {
    // State-specific styling
  }

  // 7. Responsive adaptations
  @include mobile-up {
    // Mobile-specific styling
  }
}
```

### 3. Context-Aware Icon Pattern

Icons must always be context-aware. This pattern is mandatory for all icon implementations:

```scss
// ✅ CORRECT: Context-aware icon implementation
.component-with-icon {
  display: flex;
  align-items: center;
  gap: $space-sm;

  .component-icon {
    @include perfect-icon-center; // Mandatory centering
    width: $icon-size-md;
    height: $icon-size-md;

    i {
      @include smart-icon-color(); // Automatic color adaptation
      font-size: 1em;

      // Specific context overrides only when necessary
      .light-background & {
        @include smart-icon-color(#ffffff, #2d3748, #ffffff);
      }

      .dark-background & {
        @include smart-icon-color($hse-primary-teal, #ffffff, #2d3748);
      }
    }
  }
}
```

### 4. Button Component Pattern

All button variations must follow this extensible pattern:

```scss
// Base button foundation
@mixin button-foundation {
  @include button-base; // Shared button properties
  @include focus-ring; // Accessibility support

  // Icon handling
  i {
    @include smart-icon-color();
    margin-right: $space-xs;
    font-size: 1em;

    &:last-child {
      margin-right: 0;
      margin-left: $space-xs;
    }
  }
}

// Button component with variations
.btn {
  @include button-foundation;

  // Primary button (HSE teal)
  &--primary {
    background: linear-gradient(135deg, $hse-primary-teal, $hse-primary-teal-light);
    color: $white;
    border: 2px solid $hse-primary-teal;

    &:hover {
      background: linear-gradient(135deg, $hse-primary-teal-dark, $hse-primary-teal);
      transform: translateY(-2px);
    }

    i {
      @include smart-icon-color($hse-primary-teal, $white, $hse-primary-teal);
    }
  }

  // Outline button (context-aware)
  &--outline {
    background: transparent;
    color: var(--btn-outline-color, $hse-primary-teal);
    border: 2px solid var(--btn-outline-color, $hse-primary-teal);

    &:hover {
      background: var(--btn-outline-color, $hse-primary-teal);
      color: $white;
    }

    i {
      @include smart-icon-color(transparent, var(--btn-outline-color), $white);
    }
  }

  // Size variations
  &--sm {
    padding: $space-xs $space-sm;
    font-size: $font-size-sm;
  }

  &--lg {
    padding: $space-md $space-lg;
    font-size: $font-size-lg;
  }
}
```

### 5. Card Component Pattern

Cards are foundational components that must be highly reusable:

```scss
// Card foundation mixin
@mixin card-foundation {
  background: $white;
  border-radius: $border-radius-lg;
  overflow: hidden;
  transition: all $transition-hse;

  @include responsive-shadow; // Context-aware shadows
}

// Main card component
.card {
  @include card-foundation;

  // Card header
  &__header {
    padding: $space-md $space-lg;
    background: var(--card-header-bg, $hse-primary-teal);
    color: var(--card-header-text, $white);

    .card-title {
      margin: 0;
      font-size: $font-size-lg;
      font-weight: $font-weight-semibold;

      i {
        @include smart-icon-color(var(--card-header-bg));
        margin-right: $space-sm;
      }
    }
  }

  // Card body
  &__body {
    padding: $space-lg;
  }

  // Card footer
  &__footer {
    padding: $space-md $space-lg;
    background: $neutral-lightest;
    border-top: 1px solid $neutral-lighter;

    @include flex-between;
  }

  // Theme variations using CSS custom properties
  &--healthcare {
    --card-header-bg: #{$hse-primary-teal};
    --card-header-text: #{$white};
  }

  &--admin {
    --card-header-bg: #{$hse-secondary-green};
    --card-header-text: #{$white};
  }

  &--warning {
    --card-header-bg: #{$warning-orange};
    --card-header-text: #{$neutral-dark};
  }

  // Interactive card
  &--interactive {
    cursor: pointer;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba($hse-primary-teal, 0.2);
    }
  }
}
```

### 6. Form Component Pattern

Forms require consistent styling with accessibility features:

```scss
// Form foundation
.form {
  &__group {
    margin-bottom: $space-md;

    &--inline {
      @include flex-between;
      align-items: flex-start;
      gap: $space-md;
    }
  }

  &__label {
    display: block;
    margin-bottom: $space-xs;
    font-weight: $font-weight-medium;
    color: $text-dark;

    // Required field indicator
    &--required::after {
      content: " *";
      color: $error-red;
    }
  }

  &__input {
    @include form-input-base;

    // Context-aware styling
    &:focus {
      @include focus-ring($hse-primary-teal);
      border-color: $hse-primary-teal;
    }

    &--error {
      border-color: $error-red;
      background: rgba($error-red, 0.05);
    }

    &--success {
      border-color: $success-green;
      background: rgba($success-green, 0.05);
    }
  }

  &__help {
    font-size: $font-size-sm;
    color: $text-muted;
    margin-top: $space-xs;
  }

  &__error {
    @extend .form__help;
    color: $error-red;

    i {
      margin-right: $space-xs;
      color: inherit;
    }
  }
}
```

### 7. Navigation Component Pattern

Navigation components must be responsive and accessible:

```scss
.navigation {
  @include flex-between;
  padding: $space-md 0;

  &__brand {
    @include flex-center;
    text-decoration: none;
    color: $hse-primary-teal;
    font-weight: $font-weight-bold;
    font-size: $font-size-xl;

    i {
      @include smart-icon-color(transparent, $hse-primary-teal, $hse-primary-teal);
      margin-right: $space-sm;
      font-size: 1.2em;
    }
  }

  &__menu {
    @include flex-center;
    gap: $space-md;
    list-style: none;
    margin: 0;
    padding: 0;

    @include mobile-down {
      display: none;

      &--mobile-open {
        display: flex;
        flex-direction: column;
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: $white;
        border: 1px solid $neutral-lighter;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        z-index: $z-dropdown;
      }
    }
  }

  &__item {
    .nav-link {
      @include nav-link-base;

      &.is-active {
        color: $hse-primary-teal;
        font-weight: $font-weight-semibold;
      }
    }
  }

  &__toggle {
    @include button-base;
    background: transparent;
    border: 1px solid $neutral-light;
    color: $text-dark;

    @include tablet-up {
      display: none;
    }
  }
}
```

### 8. Utility Pattern for Context Overrides

Sometimes specific context overrides are necessary. Use this pattern:

```scss
// High-specificity override pattern
// Use only when component needs specific context behavior
.page-context .page-actions .btn {
  // Context-specific button adaptations
  &.btn-outline-secondary {
    --btn-outline-color: #{$neutral-medium};

    // Icon color override for light backgrounds
    i.page-action-icon {
      @include smart-icon-color(#ffffff, #2d3748, #ffffff);

      // Specific FontAwesome icon overrides
      &.fa-solid,
      &.fa-regular,
      &.fa-brands {
        color: #2d3748 !important; // Only use !important as last resort
      }
    }
  }
}
```

### 9. Responsive Component Pattern

All components must be responsive. Use this pattern:

```scss
.responsive-component {
  // Mobile-first base styles
  padding: $space-sm;
  font-size: $font-size-sm;

  // Tablet and up
  @include tablet-up {
    padding: $space-md;
    font-size: $font-size-base;
  }

  // Desktop and up
  @include desktop-up {
    padding: $space-lg;
    font-size: $font-size-lg;
  }

  // Large desktop and up
  @include large-desktop-up {
    padding: $space-xl;
  }

  // Component-specific responsive behavior
  &__content {
    @include mobile-down {
      flex-direction: column;
      text-align: center;
    }

    @include tablet-up {
      flex-direction: row;
      text-align: left;
    }
  }
}
```

### 10. Animation and Transition Patterns

Consistent animations enhance user experience:

```scss
// Animation utilities
@mixin smooth-hover($transform: translateY(-2px)) {
  transition: all $transition-hse;

  &:hover {
    transform: $transform;
  }
}

@mixin loading-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

// Component with animations
.animated-component {
  @include smooth-hover; // Default hover animation

  &--pulse {
    @include loading-pulse; // Loading state
  }

  &--slide-in {
    animation: slideIn 0.3s ease-out forwards;
  }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

## Best Practices Summary

### Do's ✅

1. **Use mixins** for repeated patterns
2. **Use variables** for all design tokens
3. **Use BEM methodology** for naming
4. **Use context-aware colors** with smart-icon-color mixin
5. **Use CSS custom properties** for component theming
6. **Use mobile-first** responsive design
7. **Use semantic class names** that describe purpose, not appearance
8. **Test across browsers** and devices
9. **Document complex components** with usage examples
10. **Use !important** only as absolute last resort with detailed comment

### Don'ts ❌

1. **Don't use magic numbers** - everything must be a variable
2. **Don't duplicate code** - extract patterns into mixins
3. **Don't hardcode colors** - use HSE theme variables
4. **Don't use overly broad selectors** - be specific to prevent conflicts
5. **Don't ignore accessibility** - include focus states and ARIA support
6. **Don't forget responsive design** - test on all device sizes
7. **Don't use inline styles** - all styling must be in SCSS files
8. **Don't create ad-hoc solutions** - follow established patterns
9. **Don't break the cascade** - understand specificity implications
10. **Don't skip documentation** - complex components need usage examples

This pattern library ensures consistent, maintainable, and scalable SCSS development across the Django NCP application.
