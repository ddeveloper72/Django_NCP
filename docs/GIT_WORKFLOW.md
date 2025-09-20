# Git Workflow Guide

## Small, Incremental Commits

This project follows a practice of making small, focused commits with clear messages to maintain a clean git history and enable easy rollbacks.

### Commit Message Format

Use conventional commit format:
- `fix:` for bug fixes
- `feat:` for new features  
- `style:` for formatting/styling changes
- `refactor:` for code restructuring
- `docs:` for documentation changes
- `test:` for adding/updating tests

### Example Workflow

```bash
# Check current status
git status

# Add specific files for a focused change
git add path/to/specific/file.py

# Commit with descriptive message
git commit -m "fix: resolve FontAwesome icon display issues

- Fixed webfont path references in CSS
- Icons now display properly instead of rectangles
- Resolves 404 errors for font files"

# For multiple related changes, make separate commits:
git add templates/home.html
git commit -m "fix: replace invalid FontAwesome icon"

git add static/scss/pages/_home.scss static/css/main.css
git commit -m "style: enforce consistent icon colors"
```

### Benefits

- **Easy debugging**: Pinpoint exactly which change caused an issue
- **Clean rollbacks**: Revert specific changes without affecting other work
- **Clear history**: Understand project evolution through commit messages
- **Better collaboration**: Team members can understand changes quickly

### When to Commit

- After fixing a specific bug
- After implementing a single feature
- After completing a styling adjustment
- Before switching to work on something else
- At logical breakpoints in development

### What NOT to do

- Don't commit large bundles of unrelated changes
- Don't use vague commit messages like "misc fixes"
- Don't commit broken/untested code
- Don't include temporary debug files

## Recent Example

The FontAwesome icon fixes were properly split into focused commits:
1. `fix: resolve FontAwesome webfont 404 errors` - Fixed CSS paths
2. `fix: replace invalid FontAwesome icon for CDA Translation` - Icon replacement
3. `style: enforce white color for FontAwesome icons` - Color consistency
4. `feat: improve FontAwesome icon centering in service cards` - Layout improvements

Each commit addresses one specific aspect of the icon display issues.