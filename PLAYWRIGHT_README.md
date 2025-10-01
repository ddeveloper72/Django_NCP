# Playwright E2E Testing Setup

## 🎭 What's Installed

- **Playwright** for browser automation
- **pytest-playwright** for pytest integration
- **pytest-django** for Django testing
- Browser binaries: Chromium, Firefox, WebKit

## 📁 Test Structure

```
tests/
├── conftest.py              # Playwright configuration and base classes
└── e2e/
    └── test_clinical_sections.py  # Tests for clinical sections interface
```

## 🚀 Running Tests

### Method 1: Using the Test Runner

```bash
python run_tests.py
```

### Method 2: Using pytest directly

```bash
# Run all E2E tests
python -m pytest tests/e2e/ -v -m e2e

# Run specific test
python -m pytest tests/e2e/test_clinical_sections.py::TestClinicalSectionsInterface::test_clinical_sections_display -v
```

### Method 3: Using VS Code

1. Open **Run and Debug** panel (Ctrl+Shift+D)
2. Select "Run Playwright Tests" or "Debug Playwright Test"
3. Click the play button

## 🔧 VS Code Integration

The Playwright extension provides:

- **Test Explorer**: View and run tests from the sidebar
- **Debugging**: Set breakpoints and step through tests
- **Code Generation**: Record interactions to generate test code

### Accessing Test Explorer

1. Look for the test beaker icon in the Activity Bar
2. Or go to **View** → **Testing**

## 📝 Generating New Tests

Use the code generator to record interactions:

```bash
# Start your Django server first
python manage.py runserver

# In another terminal, run codegen
python codegen_helper.py
```

This opens a browser where you can:

1. Navigate to your clinical sections
2. Click through the interface
3. Copy the generated code to your test files

## 🎯 Current Tests

### `test_clinical_sections.py`

- ✅ Clinical sections display without spillover
- ✅ Medication section functionality
- ✅ Contrast and readability verification
- ✅ All 13 clinical sections present
- ✅ Accordion expand/collapse functionality

## 🐛 Debugging Tests

1. **Set `headless=False`** in `conftest.py` to see browser
2. **Add `slow_mo=500`** to slow down interactions
3. **Use VS Code debugger** with breakpoints
4. **Screenshot on failure**: Add to tests if needed

## 📊 Test Configuration

Edit `pytest.ini` to:

- Add new test markers
- Change test discovery patterns
- Modify output settings

## 🔍 What Tests Cover

These tests specifically validate:

- The clinical sections interface we've been building
- No content spillover between tabs
- Proper contrast and readability
- Accordion functionality
- Navigation between tabs
- All 13 clinical sections are present and accessible

Perfect for ensuring our clinical sections display fixes work correctly!
