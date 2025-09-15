# Git Branch Organization Strategy

## Current Situation

- Branch: `django-templates-migration`
- Mixed concerns: Template migration + Session management + Debug/test files
- Need to separate concerns and clean up before committing

## Recommended Branch Structure

### 1. Clean Up Current Branch (django-templates-migration)

Keep only template migration related changes:

- ✅ Core template fixes and improvements
- ✅ SCSS component files
- ❌ Remove: Session management code
- ❌ Remove: Debug/test scripts
- ❌ Remove: Backup files

### 2. Create New Branch (session-management)

Extract session management work:

- ✅ Session token pattern implementation
- ✅ Government ID extraction logic
- ✅ CDA aggregation by patient ID
- ✅ Views.py session-related changes

### 3. Create Temporary Branch (debug-cleanup)

For files that shouldn't be public:

- ❌ test_session_token_pattern.py
- ❌ All backup files (.backup, _backup.html)
- ❌ Debug scripts
- ❌ Any files with real patient data

## Step-by-Step Plan

### Step 1: Stash Current Work

```bash
git add .
git stash push -m "Mixed template and session work - need to separate"
```

### Step 2: Create Session Management Branch

```bash
git checkout -b session-management
git stash pop
```

### Step 3: Clean Session Branch

- Keep only session-related changes in views.py
- Remove template migration changes
- Remove debug/test files
- Commit clean session implementation

### Step 4: Return to Template Branch

```bash
git checkout django-templates-migration
git stash pop  # If needed
```

### Step 5: Clean Template Branch

- Keep only template migration changes
- Remove session management code
- Remove debug/test files
- Commit clean template migration

### Step 6: Create Debug Cleanup Branch (Optional)

```bash
git checkout -b debug-cleanup
```

- Add debug files that need review
- This branch stays private/local

## Files to Handle

### Keep in Template Migration Branch

- staticfiles/scss/components/_tab-system.scss
- templates/patient_data/sections/*.html (clean versions)
- templates/patient_data/enhanced_patient_cda.html improvements

### Move to Session Management Branch

- patient_data/views.py (session-related changes only)
- SESSION_TOKEN_PATTERN_IMPLEMENTATION.md
- Session token extraction logic

### Remove/Don't Commit

- test_session_token_pattern.py
- debug_*.py files
- *.backup files
- *_backup.html files
- *_corrupted.html files
- tab_diagnostic.html

## Benefits

1. ✅ Clean, focused commits
2. ✅ No sensitive/debug data in public repo
3. ✅ Proper separation of concerns
4. ✅ Easy to review and merge
5. ✅ Better git history

## Next Steps

1. Implement the branch separation
2. Review each branch for cleanliness
3. Test both branches independently
4. Merge template migration first
5. Merge session management after review
