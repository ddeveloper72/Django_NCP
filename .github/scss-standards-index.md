# SCSS Standards Index - Django NCP

## Complete SCSS Architecture Documentation

This index provides access to all SCSS architecture standards and guidelines for the Django NCP project. These specifications ensure **dynamic, modular, reusable components that are never duplicated or programmed ad-hoc**.

## Core Documentation

### 1. [SCSS Architecture Standards](./scss-architecture-standards.md)

**Primary specification** defining the fundamental architecture principles:

- **Context-Aware Components**: Automatic adaptation to light/dark backgrounds
- **Modular Design**: Single responsibility, atomic components, layered architecture
- **Zero Duplication**: DRY principle, centralized patterns, systematic overrides
- **Variable-Driven Design**: All design tokens as variables, no magic numbers

### 2. [SCSS Component Patterns](./scss-component-patterns.md)

**Development patterns** with concrete examples and implementation guidelines:

- Component development lifecycle
- Foundation patterns for all component types
- Context-aware icon patterns (mandatory)
- Button, card, form, and navigation component patterns
- Responsive design patterns
- Animation and transition patterns

### 3. [SCSS Quick Reference](./scss-quick-reference.md)

**Developer reference** for day-to-day development:

- Mandatory checklists for SCSS development
- Essential mixins and variables reference
- Common patterns ready for copy/paste
- Troubleshooting guide for common issues
- Performance optimization tips

## Integration with Existing Specifications

### Color Contrast and Accessibility Standards

All SCSS components must comply with [Color Contrast and Accessibility Standards](./color-contrast-accessibility-standards.md):

- WCAG 2.2 AA minimum contrast ratios (4.5:1 normal text, 3:1 large text)
- Badge text color requirements for dark/light backgrounds
- Status indicator multi-modal design (never color alone)
- Focus state contrast requirements (3:1+ minimum)
- Healthcare-specific accessibility considerations

### Frontend Structure Compliance

The SCSS standards integrate with existing [Frontend Structure Compliance](./frontend-structure-compliance.md) requirements:

- No inline CSS in HTML templates
- SASS compilation workflow
- HSE color palette implementation
- Mobile-first responsive design

### Icon Centering Standards

All icon implementations must follow [Icon Centering Standards](./icon-centering-standards.md):

- Perfect cross-hair alignment for badge icons
- Use `@include perfect-icon-center` mixin
- Context-aware color implementation with `@include smart-icon-color()`

## Key Principles Summary

### 1. Dynamic Architecture

- **Smart Color Systems**: `@include smart-icon-color()` adapts to any background
- **Context-Aware Styling**: Components work on light and dark backgrounds
- **Responsive by Default**: Mobile-first approach with breakpoint mixins
- **Theme Integration**: HSE color palette with CSS custom properties

### 2. Modular Design

```scss
// ✅ CORRECT: Modular component structure
.healthcare-card {
  @include card-foundation;           // Shared foundation

  &__header {
    background: var(--card-bg, $hse-primary-teal);

    i {
      @include smart-icon-color(var(--card-bg)); // Context-aware icons
    }
  }

  // Variations, not new components
  &--admin { --card-bg: #{$hse-secondary-green}; }
  &--warning { --card-bg: #{$warning-orange}; }
}
```

### 3. Reusable First

- **Mixin Library**: Complex patterns extracted to reusable mixins
- **Variable System**: Comprehensive design token system
- **Component Classes**: Generic classes working in multiple contexts
- **Extension Patterns**: Easy to extend without modification

### 4. Zero Duplication

- **DRY Principle**: Never repeat styling rules
- **Pattern Extraction**: Common patterns in mixins and utilities
- **Systematic Architecture**: Predictable structure prevents ad-hoc solutions

## Development Workflow

### 1. Before Starting Any Component

1. Review [SCSS Architecture Standards](./scss-architecture-standards.md) core principles
2. Check [SCSS Component Patterns](./scss-component-patterns.md) for similar implementations
3. Use [SCSS Quick Reference](./scss-quick-reference.md) checklist
4. Verify integration with [Frontend Structure Compliance](./frontend-structure-compliance.md)

### 2. Component Development Process

1. **Analysis**: Context assessment, reusability evaluation
2. **Foundation**: Start with base mixins and variables
3. **Implementation**: Follow established patterns
4. **Testing**: Cross-browser, responsive, accessibility
5. **Documentation**: Update patterns if creating new reusable components

### 3. Code Review Process

Use the mandatory checklist from [SCSS Quick Reference](./scss-quick-reference.md):

- [ ] No magic numbers or hardcoded colors
- [ ] Context-aware icon implementations
- [ ] Proper mixin usage and variable-driven design
- [ ] Mobile-responsive with proper breakpoints
- [ ] Accessibility compliance (focus states, contrast)

## Real-World Examples

### Icon Visibility Fix (Recent Implementation)

```scss
// Problem: White icons invisible on light backgrounds
// Solution: Context-aware icon colors with high specificity

.page-context .page-actions .btn i.page-action-icon {
  @include smart-icon-color(#ffffff, #2d3748, #ffffff);

  &.fa-solid,
  &.fa-regular,
  &.fa-brands {
    color: #2d3748 !important; // Specific override for conflicting rules
  }
}
```

### Card Component System

```scss
// Reusable card foundation
@mixin card-foundation {
  background: $white;
  border-radius: $border-radius-lg;
  overflow: hidden;
  transition: all $transition-hse;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

// Context-aware implementations
.patient-card {
  @include card-foundation;
  --card-header-bg: #{$hse-primary-teal};
}

.admin-card {
  @include card-foundation;
  --card-header-bg: #{$hse-secondary-green};
}
```

## Troubleshooting Common Issues

### Issue: Component Conflicts

**Cause**: Overly broad selectors or duplicate implementations
**Solution**: Use specific BEM naming and check for existing patterns

### Issue: Color Contrast Problems

**Cause**: Hardcoded colors not adapting to context
**Solution**: Use `@include smart-icon-color()` and HSE theme variables

### Issue: Non-Responsive Components

**Cause**: Fixed sizing or desktop-first approach
**Solution**: Mobile-first responsive mixins and flexible layouts

### Issue: Performance Problems

**Cause**: Large CSS bundles or inefficient selectors
**Solution**: Component optimization and unused CSS removal

## Maintenance Guidelines

### Monthly Reviews

- Audit for duplicate patterns that can be extracted to mixins
- Review HSE color palette compliance
- Performance analysis and optimization
- Accessibility compliance verification

### New Feature Integration

- All new features must follow these SCSS standards
- Update pattern library when creating reusable components
- Cross-reference with existing specifications
- Document complex implementations

### Legacy Code Migration

- Systematic replacement of inline styles with component classes
- Gradual extraction of duplicate patterns to mixins
- HSE color palette standardization
- Responsive design improvements

## Conclusion

This comprehensive SCSS architecture ensures:

- **Maintainable**: Clear patterns and systematic organization
- **Scalable**: Easy to extend without modification
- **Professional**: HSE healthcare branding compliance
- **Efficient**: No duplication, optimal performance
- **Accessible**: WCAG compliance built into components

By following these standards, the Django NCP application maintains a robust, future-proof styling system that eliminates technical debt and supports rapid, consistent development.

## Quick Links

- [Color Contrast and Accessibility Standards](./color-contrast-accessibility-standards.md) - WCAG 2.2 compliance and healthcare accessibility
- [SCSS Architecture Standards](./scss-architecture-standards.md) - Core principles
- [SCSS Component Patterns](./scss-component-patterns.md) - Implementation guides
- [SCSS Quick Reference](./scss-quick-reference.md) - Developer checklists
- [Testing and Modular Code Standards](./testing-and-modular-code-standards.md) - Backend integration patterns
- [Testing and Modularity Index](./testing-and-modularity-index.md) - Complete development methodology
- [Frontend Structure Compliance](./frontend-structure-compliance.md) - Integration requirements
- [Icon Centering Standards](./icon-centering-standards.md) - Icon implementation rules
