# FontAwesome Icon Centering Standards

## Overview

This specification defines the mandatory centering requirements for all FontAwesome icons used within badge backgrounds across the Django NCP application. The requirement is **perfect cross-hair alignment** - all icons must be precisely centered both vertically and horizontally within their container elements.

## Visual Standard

![Cross-hair Alignment Example](crosshair-example.png)
*Icons must align perfectly with imaginary cross-hairs at the exact center of their badge containers*

## Scope

This standard applies to **ALL** FontAwesome icons in the following contexts:

- Service card header icons
- Badge icons in hero sections
- Feature card icons
- Admin card icons
- External service card icons
- Navigation icons with badge backgrounds
- Status indicator icons
- Any icon displayed within a circular or rounded badge background

## Technical Requirements

### 1. Perfect Centering Mandate

- **Vertical Centering**: Icon must be exactly centered on the Y-axis
- **Horizontal Centering**: Icon must be exactly centered on the X-axis
- **Cross-hair Test**: Icon should pass the cross-hair alignment test as demonstrated in design reviews

### 2. Implementation Standards

#### Primary CSS Classes

All badge icons must use the standardized centering system:

```scss
// Perfect icon centering mixin - MANDATORY for all badge icons
@mixin perfect-icon-center {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;

  i {
    // Icon inherits flex child behavior - NO display override needed
    font-size: 1em !important;
    line-height: 1 !important;
    margin: 0 !important;
    text-align: center !important;
    vertical-align: middle !important;
  }
}
```

#### Required HTML Structure

```html
<!-- Service Card Icons -->
<div class="service-icon bg-hse-teal">
  <i class="fa-solid fa-user-md" aria-hidden="true"></i>
</div>

<!-- Badge Icons -->
<div class="hero-badge">
  <span class="badge bg-primary">
    <i class="fa-solid fa-check" aria-hidden="true"></i>
    Badge Text
  </span>
</div>
```

### 3. Affected Components

#### Service Cards

- **Classes**: `.service-card .service-card-header .service-icon`
- **Context**: Primary service offering cards
- **Background**: Circular badges with HSE brand colors
- **Icon Size**: 1.8em for 80px containers

#### External Service Cards

- **Classes**: `.external-service-card .service-card-header .service-icon`
- **Context**: External integration cards (Java OpenNCP, DomiSMP)
- **Background**: HSE teal/green circular badges
- **Icon Size**: 1.8em for consistency

#### Admin Cards

- **Classes**: `.admin-card .service-card-header .service-icon`
- **Context**: Administrative function cards
- **Background**: Warning color badges
- **Icon Size**: 1.8em for consistency

#### Feature Cards

- **Classes**: `.feature-icon`
- **Context**: Feature showcase sections
- **Background**: Gradient circular badges
- **Icon Size**: 2.5em for larger 90px containers

#### Badge Components

- **Classes**: `.hero-badge .badge`, `.badge` (general)
- **Context**: Hero section indicators, status badges
- **Background**: Bootstrap badge backgrounds
- **Icon Size**: 1.2em for inline text alignment

### 4. Browser Testing Requirements

#### Cross-hair Alignment Test

1. **Visual Inspection**: Icons must pass visual cross-hair alignment
2. **DevTools Verification**: Check computed styles for proper flexbox centering
3. **Multi-browser Testing**: Chrome, Firefox, Safari, Edge
4. **Responsive Testing**: All viewport sizes maintain centering

#### Automated Testing

```javascript
// Example test for icon centering verification
describe('Icon Centering Standards', () => {
  it('should center all service card icons perfectly', () => {
    cy.get('.service-icon').each(($icon) => {
      // Verify flexbox centering properties
      cy.wrap($icon).should('have.css', 'display', 'flex');
      cy.wrap($icon).should('have.css', 'align-items', 'center');
      cy.wrap($icon).should('have.css', 'justify-content', 'center');
    });
  });
});
```

### 5. Quality Assurance Checklist

#### Pre-commit Checklist

- [ ] All new icons use `perfect-icon-center` mixin
- [ ] Icon containers have proper flexbox display
- [ ] FontAwesome size overrides are implemented
- [ ] Visual cross-hair alignment verified
- [ ] No conflicting margin/padding styles

#### Code Review Requirements

- [ ] Icon centering implementation reviewed
- [ ] Cross-hair alignment screenshots provided
- [ ] Multiple device testing completed
- [ ] Accessibility standards maintained

### 6. Common Anti-patterns to Avoid

#### ❌ Incorrect Implementations

```scss
// DON'T: Using only vertical-align
.icon {
  vertical-align: middle; // Insufficient for perfect centering
}

// DON'T: Hardcoded margins
.icon i {
  margin-top: 5px; // Fragile and device-dependent
  margin-left: 3px;
}

// DON'T: Text-align only
.icon {
  text-align: center; // Only handles horizontal, not vertical
}
```

#### ✅ Correct Implementation

```scss
// DO: Use the perfect centering mixin
.service-icon {
  @include perfect-icon-center;
  width: 80px;
  height: 80px;
  border-radius: 50%;
}
```

### 7. Performance Considerations

#### CSS Optimization

- Use `!important` sparingly but necessarily for overriding FontAwesome defaults
- Combine selectors to reduce CSS file size
- Leverage CSS Grid/Flexbox for reliable centering

#### Icon Loading

- Ensure FontAwesome CSS loads before custom styles
- Use `aria-hidden="true"` for decorative icons
- Implement fallback styling for icon loading failures

### 8. Accessibility Standards

#### Screen Reader Compliance

- Icons in badges must have appropriate `aria-hidden` attributes
- Text alternatives required for informational icons
- Color contrast ratios maintained for icon backgrounds

#### Keyboard Navigation

- Badge icons should not interfere with keyboard navigation
- Focus states must remain visible around badge containers

### 9. Documentation Requirements

#### Design System Documentation

- Include cross-hair alignment examples in style guide
- Document all approved icon/badge combinations
- Maintain visual regression test screenshots

#### Developer Guidelines

- All new badge icons must reference this specification
- Pull requests must include centering verification screenshots
- Code comments should reference cross-hair alignment requirement

### 10. Future Considerations

#### Icon System Evolution

- Monitor FontAwesome updates for breaking changes
- Consider SVG icon alternatives for better control
- Evaluate CSS Container Queries for responsive icon sizing

#### Design System Expansion

- Extend standards to other graphical elements
- Consider automated cross-hair alignment testing tools
- Develop icon centering linting rules

## Enforcement

This specification is **mandatory** for all current and future development. Any icon implementation that fails the cross-hair alignment test must be corrected before code review approval.

## References

- [HSE Design System Colors](../static/scss/utils/_variables.scss)
- [Perfect Icon Center Mixin](../static/scss/utils/_mixins.scss)
- [FontAwesome Documentation](https://fontawesome.com/docs)
- [CSS Flexbox Specification](https://www.w3.org/TR/css-flexbox-1/)

---

**Last Updated**: September 22, 2025
**Version**: 1.0
**Owner**: Frontend Development Team
**Review Cycle**: Quarterly
