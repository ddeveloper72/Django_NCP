# Decision: VS Code Automation and Development Workflow Setup

**Date:** 2025-09-20
**Status:** Accepted
**Deciders:** Duncan (Project Owner)

## Context

The Django_NCP project needed automated development tools to improve workflow efficiency and ensure code quality. The Original Spec requires:

- SASS compilation from `/static/scss/` to `/static/css/`
- Python linting and code quality checks
- No inline CSS/JS in templates (requires external compilation)
- Consistent development environment across team members

The project had existing SASS files but incorrect compilation paths, and no automated linting was in place.

## Decision

Implemented **emeraldwalk.runonsave** VS Code extension configuration with:

1. **SASS Auto-compilation:**
   - Trigger: Save any `.scss` file in `static/scss/`
   - Action: `sass static/scss:static/css`
   - Benefit: Immediate CSS compilation for template development

2. **Python Linting:**
   - Trigger: Save any `.py` file
   - Action: `python -m flake8 ${file} --max-line-length=120 --ignore=E203,W503`
   - Benefit: Immediate code quality feedback

3. **VS Code Tasks:**
   - `Run Unit Tests`: Execute pytest for testing
   - `Compile SASS`: Background watch task for continuous compilation
   - `Compile SASS (One-time)`: Manual compilation command

4. **Configuration Files:**
   - `.vscode/settings.json`: Project-specific Django template protection and runOnSave config
   - `.vscode/tasks.json`: Predefined tasks for common operations
   - Updated `.gitignore`: Track specific VS Code files while excluding personal settings

## Consequences

### Positive

- ✅ **Automated SASS compilation** ensures CSS is always up-to-date
- ✅ **Immediate feedback** on Python code quality via flake8
- ✅ **Consistent environment** for all developers working on the project
- ✅ **Django template protection** prevents auto-formatting of template files
- ✅ **Fixed SASS compilation path** from incorrect `static/sass:static/scss` to correct `static/scss:static/css`
- ✅ **Shared team configuration** via Git tracking of specific VS Code files

### Negative

- ⚠️ **Extension dependency**: Requires developers to install `emeraldwalk.runonsave` extension
- ⚠️ **Potential noise**: Flake8 runs on every Python file save (may be frequent for large files)
- ⚠️ **Platform specific**: Configuration optimized for VS Code users

### Mitigations

- Document required extensions in project README
- Consider adjusting flake8 to run only on explicit request if too frequent
- Provide alternative setup instructions for non-VS Code developers

## Implementation

1. Fixed SASS compilation paths in `.vscode/tasks.json`
2. Added `emeraldwalk.runonsave` configuration to `.vscode/settings.json`
3. Updated `.gitignore` to selectively track VS Code configuration files
4. Removed conflicting `runOnSave.commands` from global VS Code settings
5. Committed changes to main branch (commit `c1d1f4f`)

## Related Documents

- **Original Spec:** Requirements for SASS compilation and code quality
- **Spec Alignment Checklist:** Items 5.5 and 5.6 (VS Code automation setup)
- **TODO Tracker:** Automation section items marked as completed
