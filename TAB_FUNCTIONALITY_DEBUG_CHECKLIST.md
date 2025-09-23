# Tab Functionality Debug Checklist

## Overview
Systematic debugging approach for Django template tab functionality issues where tabs are not properly switching content or showing incorrect nested structures.

## Problem Symptoms
- ✅ **Tab buttons switch visual state correctly** (highlighting works)
- ❌ **Only one tab shows content** while others appear empty
- ❌ **Content appears nested** instead of switching in same viewport
- ❌ **Multiple tab contents visible simultaneously**

## Debug Process Checklist

### Phase 1: Visual Investigation
- [ ] **Check tab button highlighting** - Do buttons change visual state when clicked?
- [ ] **Inspect content visibility** - Do all tabs show content or only some?
- [ ] **Test viewport behavior** - Does content switch in same space or appear nested?
- [ ] **Use browser dev tools** - Right-click → Inspect Element on tab content area

### Phase 2: HTML Structure Analysis
- [ ] **View page source** - Check raw HTML structure in browser
- [ ] **Use VS Code code folding** - Collapse/expand HTML sections to trace structure
- [ ] **Look for nested tab divs** - Tab content should be **siblings**, not nested
- [ ] **Verify proper div hierarchy**:
  ```html
  <div class="extended-tab-content-container">
    <div class="clinical-tab-content active" id="tab1">...</div>
    <div class="clinical-tab-content" id="tab2">...</div>
    <div class="clinical-tab-content" id="tab3">...</div>
  </div>
  ```

### Phase 3: Template Structure Verification
- [ ] **Check main template closing tags** - Look for missing `</div>` in main tab container
- [ ] **Verify included template structure** - Check all `{% include %}` templates for:
  - [ ] Missing opening `<div>` tags
  - [ ] Missing closing `</div>` tags
  - [ ] Unbalanced div structures
- [ ] **Validate container div closure** - Ensure tab content container is properly closed

### Phase 4: CSS Investigation
- [ ] **Check compiled CSS** - Verify `.clinical-tab-content` rules exist:
  ```css
  .clinical-tab-content { display: none; }
  .clinical-tab-content.active { display: block; }
  ```
- [ ] **Test CSS specificity** - More specific selectors may be needed:
  ```css
  .clinical-section .clinical-tab-content.active { display: block; }
  ```
- [ ] **Verify SASS compilation** - Run `sass static/scss:static/css`
- [ ] **Check Django static collection** - Run `python manage.py collectstatic --noinput`

### Phase 5: JavaScript Functionality
- [ ] **Test tab switching logic** - Add console.log to verify:
  - [ ] Tab elements are found in DOM
  - [ ] Active classes are being added/removed
  - [ ] CSS display properties are correct
- [ ] **Check event delegation** - Ensure click events are properly bound
- [ ] **Verify DOM timing** - Use setTimeout for DOM-ready initialization

## Common Root Causes & Solutions

### 1. Missing Closing Divs (Most Common)
**Symptoms**: Nested tab content structure in HTML source
**Check**: 
- Main template container closure
- Included template div balance
**Fix**: Add missing `</div>` tags

### 2. CSS Specificity Issues
**Symptoms**: JavaScript works but content not visible
**Check**: Browser dev tools computed styles
**Fix**: Increase CSS selector specificity or add `!important`

### 3. JavaScript Timing Issues
**Symptoms**: Inconsistent tab behavior
**Check**: Console errors, element not found
**Fix**: Add DOM-ready delays or better event delegation

### 4. Django Static Files Not Updated
**Symptoms**: Changes not reflected in browser
**Check**: File timestamps in `staticfiles/`
**Fix**: Run `collectstatic` after CSS/JS changes

## Debugging Tools & Techniques

### Browser Developer Tools
- **Elements tab**: Inspect HTML structure, check for nesting
- **Console tab**: Look for JavaScript errors and custom logging
- **Computed styles**: Verify CSS rules are being applied

### VS Code Features
- **Code folding**: Collapse HTML sections to trace structure visually
- **HTML validation**: Check for syntax errors and unclosed tags
- **Search & replace**: Find unmatched opening/closing div patterns

### Django Commands
```bash
# Compile SASS
sass static/scss:static/css

# Collect static files
python manage.py collectstatic --noinput

# Check template syntax
python manage.py check
```

## Prevention Best Practices

### Template Organization
- [ ] Always close divs immediately after opening
- [ ] Use meaningful HTML comments for complex structures
- [ ] Test included templates independently
- [ ] Validate HTML structure with tools

### CSS Architecture
- [ ] Use specific selectors for tab content
- [ ] Avoid overly generic class names
- [ ] Test CSS compilation after changes
- [ ] Document tab-specific styling rules

### JavaScript Patterns
- [ ] Use event delegation for dynamic content
- [ ] Add comprehensive error checking
- [ ] Include DOM-ready verification
- [ ] Minimize direct DOM manipulation

## Testing Protocol

### Manual Testing Steps
1. [ ] Test each tab individually
2. [ ] Verify content switches in same viewport
3. [ ] Check mobile responsiveness
4. [ ] Test with different data conditions
5. [ ] Verify browser console is error-free

### Resolution Verification
- [ ] Remove all debug code (console.log, debug divs, etc.)
- [ ] Compile and collect static files
- [ ] Test full functionality
- [ ] Commit working solution
- [ ] Document any project-specific patterns

---

**Key Learning**: Visual inspection of HTML structure combined with systematic template analysis is often more effective than complex debugging tools for template-related issues.