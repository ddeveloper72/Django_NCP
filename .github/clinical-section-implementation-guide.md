# Clinical Section Implementation Guide

## Overview

This guide documents the complete process for implementing a new clinical section in the Django_NCP application, using the **History of Past Illness** section as a reference implementation.

## Architecture Components

A clinical section implementation requires 4 main components:

1. **Data Extractor Service** - Extracts structured data from CDA XML
2. **View Integration** - Adds extracted data to Django template context
3. **Template Component** - Renders the section in the UI
4. **Browser Testing** - Validates end-to-end functionality

---

## 1. Data Extractor Service

**Purpose**: Extract structured clinical data from CDA XML documents

### File Location
```
patient_data/services/{section_name}_extractor.py
```

### Implementation Pattern

```python
# patient_data/services/history_of_past_illness_extractor.py

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)

@dataclass
class HistoryIllnessEntry:
    """Structured data model for History of Past Illness entries"""
    problem_name: str
    problem_type: str = ""
    time_period: str = ""
    problem_status: str = ""
    health_status: str = ""
    problem_code: str = ""
    problem_code_system: str = ""
    health_status_code: str = ""

class HistoryOfPastIllnessExtractor:
    """Extracts History of Past Illness data from CDA documents"""
    
    def __init__(self):
        # Define XML namespace mappings for CDA parsing
        self.namespaces = {
            'hl7': 'urn:hl7-org:v3',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
    
    def extract_history_of_past_illness(self, cda_content: str) -> List[HistoryIllnessEntry]:
        """
        Extract History of Past Illness entries from CDA XML
        
        Args:
            cda_content (str): Raw CDA XML content
            
        Returns:
            List[HistoryIllnessEntry]: Structured clinical data
        """
        try:
            root = ET.fromstring(cda_content)
            
            # Find the specific section using LOINC code
            section_xpath = ".//hl7:section[hl7:code[@code='11348-0']]"
            section = root.find(section_xpath, self.namespaces)
            
            if section is None:
                logger.info("No History of Past Illness section found")
                return []
            
            entries = []
            
            # Extract entries from the section
            for entry in section.findall(".//hl7:entry", self.namespaces):
                illness_entry = self._extract_single_entry(entry)
                if illness_entry:
                    entries.append(illness_entry)
            
            logger.info(f"Successfully extracted {len(entries)} History of Past Illness entries")
            return entries
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in History of Past Illness extraction: {e}")
            return []
    
    def _extract_single_entry(self, entry_element) -> Optional[HistoryIllnessEntry]:
        """Extract data from a single entry element"""
        try:
            # Extract problem name
            problem_name = self._find_text_by_id(entry_element, "problem-name")
            if not problem_name:
                return None
            
            # Extract all relevant fields
            return HistoryIllnessEntry(
                problem_name=problem_name,
                problem_type=self._find_text_by_id(entry_element, "problem-type"),
                time_period=self._find_text_by_id(entry_element, "problem-time"),
                problem_status=self._find_text_by_id(entry_element, "problem-status"),
                health_status=self._find_text_by_id(entry_element, "health-status"),
                problem_code=self._extract_code_value(entry_element, "problem-code"),
                problem_code_system=self._extract_code_system(entry_element, "problem-code"),
                health_status_code=self._extract_code_value(entry_element, "health-status-code")
            )
            
        except Exception as e:
            logger.warning(f"Failed to extract single entry: {e}")
            return None
    
    def _find_text_by_id(self, element, target_id: str) -> str:
        """Find text content by ID with namespace support"""
        # Use proper f-string formatting for XPath
        xpath = f".//hl7:*[@ID='{target_id}']"
        target_element = element.find(xpath, self.namespaces)
        return target_element.text.strip() if target_element is not None and target_element.text else ""
```

### Key Implementation Details

1. **Dataclass Structure**: Define a clear data model with all required fields
2. **Namespace Handling**: Proper XML namespace mapping for CDA documents
3. **Error Handling**: Comprehensive try/catch with logging
4. **XPath Queries**: Use specific LOINC codes to find sections
5. **Data Validation**: Check for required fields before creating entries

---

## 2. View Integration

**Purpose**: Integrate the extractor into Django views and add data to template context

### File Location
```
patient_data/views.py
```

### Implementation Steps

#### Step 1: Import the Extractor
```python
# Add to imports section
from .services.history_of_past_illness_extractor import HistoryOfPastIllnessExtractor
```

#### Step 2: Add Specialized Extraction Logic
```python
# Inside patient_cda_view function, after clinical arrays processing
# HISTORY OF PAST ILLNESS SPECIALIZED EXTRACTION
# This runs regardless of comprehensive_data status if we have raw CDA content
try:
    if raw_cda_content:
        logger.info("[HISTORY OF PAST ILLNESS] Starting specialized extraction from raw CDA content")
        history_extractor = HistoryOfPastIllnessExtractor()
        history_entries = history_extractor.extract_history_of_past_illness(raw_cda_content)
        
        if history_entries:
            # Override the history_of_past_illness with structured data
            extended_sections["history_of_past_illness"] = history_entries
            logger.info(f"[HISTORY OF PAST ILLNESS] Successfully extracted {len(history_entries)} structured entries")
        else:
            logger.info("[HISTORY OF PAST ILLNESS] No history entries found in CDA document")
    else:
        logger.warning("[HISTORY OF PAST ILLNESS] No raw CDA content available for extraction")
                        
except Exception as e:
    logger.warning(f"[HISTORY OF PAST ILLNESS] Extraction failed: {e}")
    # Keep existing detection if specialized extraction fails

# UPDATE CONTEXT WITH EXTENDED SECTIONS (including History of Past Illness)
context.update(extended_sections)

total_extended = sum(len(sections) for sections in extended_sections.values())
logger.info(f"[EXTENDED SECTIONS] Added {total_extended} extended clinical sections to context")
```

#### Step 3: Add to Extended Sections Detection
```python
# In detect_extended_clinical_sections function
extended_section_mapping = {
    # ... existing mappings ...
    "11348-0": "history_of_past_illness",  # History of Past Illness (LOINC code)
    # ... other mappings ...
}
```

### Critical Implementation Notes

1. **Context Assignment**: Always call `context.update(extended_sections)` after extraction
2. **Independent Processing**: Make extraction independent of comprehensive_data status
3. **Error Handling**: Graceful degradation if extraction fails
4. **Logging**: Comprehensive logging for debugging and monitoring

---

## 3. Template Component

**Purpose**: Render the clinical section in the user interface

### File Location
```
templates/patient_data/components/clinical_information_content.html
```

### Implementation Pattern

#### Step 1: Add Section Within Extended Clinical Information
```html
<!-- Place after existing clinical sections, before closing extended clinical div -->
<div class="clinical-section-divider">
    <div class="clinical-section-title-group">
        <h5 class="clinical-section-group-title">
            <i class="fa-solid fa-stethoscope me-2"></i>
            Extended Clinical Information
        </h5>
        <p class="group-subtitle text-muted mb-0">
            Additional clinical data available in this patient summary
        </p>
    </div>

    {# History of Past Illness Section #}
    {% if history_of_past_illness and history_of_past_illness|length > 0 %}
    <div class="clinical-section">
        <div class="collapsible-wrapper">
            <input id="toggle-past-illness" class="toggle-input" type="checkbox">
            <label for="toggle-past-illness" class="collapsible-label-title">
                <div class="clinical-section-title-row">
                    <div class="clinical-section-title">
                        <i class="fa-solid fa-history me-2"></i>
                        <span>History of Past Illness</span>
                    </div>
                    <div class="clinical-badge-container">
                        <span class="clinical-badge extended">{{ history_of_past_illness|length }} Found</span>
                    </div>
                </div>
                <i class="fas fa-chevron-down toggle-icon" aria-hidden="true"></i>
            </label>
            <div class="collapsible-content-title">
                <div class="content-inner-title">
                    <p class="mb-3 text-muted">History of Past Illness: {{ history_of_past_illness|length }} closed/inactive conditions</p>
                    
                    <div class="table-responsive">
                        <table class="table table-striped table-hover">
                            <thead class="table-warning">
                                <tr>
                                    <th scope="col" class="fw-bold">Closed/Inactive Problem</th>
                                    <th scope="col" class="fw-bold">Problem Type</th>
                                    <th scope="col" class="fw-bold">Time</th>
                                    <th scope="col" class="fw-bold">Problem Status</th>
                                    <th scope="col" class="fw-bold">Health Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for illness in history_of_past_illness %}
                                <tr>
                                    <td>
                                        <div class="d-flex align-items-start">
                                            <i class="fa-solid fa-file-medical text-warning me-2 mt-1"></i>
                                            <div>
                                                <div class="fw-medium text-dark">{{ illness.problem_name }}</div>
                                                {% if illness.problem_code %}
                                                <small class="text-muted">
                                                    <i class="fa-solid fa-code me-1"></i>
                                                    {{ illness.problem_code }}
                                                    {% if illness.problem_code_system %}
                                                        <span class="badge bg-secondary ms-1">{{ illness.problem_code_system|slice:"-6:" }}</span>
                                                    {% endif %}
                                                </small>
                                                {% endif %}
                                            </div>
                                        </div>
                                    </td>
                                    <td>
                                        <span class="badge bg-info text-dark">{{ illness.problem_type }}</span>
                                    </td>
                                    <td>
                                        <div class="d-flex align-items-center">
                                            <i class="fa-solid fa-calendar text-muted me-2"></i>
                                            <span class="text-muted">{{ illness.time_period }}</span>
                                        </div>
                                    </td>
                                    <td>
                                        <span class="badge bg-success">{{ illness.problem_status }}</span>
                                    </td>
                                    <td>
                                        <div class="d-flex align-items-center">
                                            <i class="fa-solid fa-heartbeat text-danger me-2"></i>
                                            <div>
                                                <div class="fw-medium">{{ illness.health_status }}</div>
                                                {% if illness.health_status_code %}
                                                <small class="text-muted">
                                                    <i class="fa-solid fa-hashtag me-1"></i>
                                                    {{ illness.health_status_code }}
                                                </small>
                                                {% endif %}
                                            </div>
                                        </div>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                    
                    <!-- Clinical Terminology Integration -->
                    <div class="clinical-terminology-summary mt-3">
                        <h6 class="clinical-terminology-title">
                            <i class="fa-solid fa-code-branch me-2"></i>
                            Clinical Terminology Integration
                        </h6>
                        <div class="terminology-codes">
                            <div class="code-group">
                                <strong>Problem Codes:</strong>
                                {% for illness in history_of_past_illness %}
                                    {% if illness.problem_code %}
                                        <span class="code-badge">{{ illness.problem_code }}</span>
                                    {% endif %}
                                {% endfor %}
                            </div>
                            <div class="code-group">
                                <strong>Health Status Codes:</strong>
                                {% for illness in history_of_past_illness %}
                                    {% if illness.health_status_code %}
                                        <span class="code-badge">{{ illness.health_status_code }}</span>
                                    {% endif %}
                                {% endfor %}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    {% endif %}
</div>
```

### Template Design Principles

1. **Conditional Rendering**: Always wrap in `{% if condition %}` blocks
2. **Accordion Pattern**: Use collapsible wrapper with toggle functionality
3. **Badge Indicators**: Show count and status with clinical badges
4. **Table Structure**: Responsive tables with proper healthcare styling
5. **Clinical Icons**: Use Font Awesome icons for visual context
6. **Code Integration**: Display clinical codes for CTS integration

---

## 4. Browser Testing

**Purpose**: Validate end-to-end functionality using Playwright automation

### Testing Process

#### Step 1: Navigate to Patient Data
```javascript
// Navigate to EU NCP Portal
await page.goto('http://localhost:8000');

// Access patient search
await page.getByRole('link', { name: ' Search Patients' }).click();

// View test patients
await page.getByRole('link', { name: ' View Test Patients' }).click();

// Select specific patient (Diana Ferreira)
await page.getByRole('link', { name: ' View Details' }).first().click();
```

#### Step 2: Access CDA Document View
```javascript
// Click CDA Document L3 Browser View
await page.getByRole('link', { name: ' View CDA Document L3' }).click();

// Navigate to Extended Patient Information
await page.getByRole('tab', { name: ' Extended Patient Information' }).click();
```

#### Step 3: Validate Clinical Section
```javascript
// Click Clinical Information tab
await page.getByRole('button', { name: ' Clinical Information' }).click();

// Verify section appears
const historySection = await page.locator('[data-section="history_of_past_illness"]');
await expect(historySection).toBeVisible();

// Validate data
const entryCount = await page.locator('.clinical-badge').textContent();
expect(entryCount).toContain('2 Found');
```

### Validation Checklist

- [ ] Section appears in Clinical Information tab
- [ ] Badge count matches extracted data
- [ ] Accordion functionality works
- [ ] Table structure renders correctly
- [ ] Clinical codes display properly
- [ ] Responsive design works on different screen sizes

---

## 5. Complete Implementation Checklist

### Data Layer ✅
- [ ] Create dataclass for structured data
- [ ] Implement XML parsing with proper namespaces
- [ ] Add error handling and logging
- [ ] Extract clinical codes for CTS integration

### Service Layer ✅
- [ ] Import extractor in views.py
- [ ] Add specialized extraction logic
- [ ] Update context with extracted data
- [ ] Add section mapping for detection

### Presentation Layer ✅
- [ ] Add template section with conditional rendering
- [ ] Implement accordion pattern
- [ ] Create responsive table structure
- [ ] Add clinical terminology summary

### Testing & Validation ✅
- [ ] Unit test the extractor
- [ ] Test template conditional logic
- [ ] Browser test with Playwright
- [ ] Validate UI responsiveness

---

## 6. Common Pitfalls and Solutions

### Issue 1: Context Not Updating
**Problem**: Section doesn't appear in UI
**Solution**: Ensure `context.update(extended_sections)` is called after extraction

### Issue 2: Template Conditions Failing
**Problem**: Template doesn't render even with data
**Solution**: Verify conditional logic: `{% if variable and variable|length > 0 %}`

### Issue 3: XPath Namespace Issues
**Problem**: XML elements not found during parsing
**Solution**: Define proper namespaces and use them consistently in XPath queries

### Issue 4: Missing Clinical Codes
**Problem**: Code fields are empty
**Solution**: Implement specific code extraction methods with proper attribute handling

---

## 7. Next Section Implementation Template

Use this template for implementing the next clinical section:

```python
# 1. Create new extractor
patient_data/services/{next_section}_extractor.py

# 2. Define dataclass
@dataclass
class {NextSection}Entry:
    # Define fields based on CDA structure
    pass

# 3. Implement extractor class
class {NextSection}Extractor:
    def extract_{next_section}(self, cda_content: str) -> List[{NextSection}Entry]:
        # Follow the established pattern
        pass

# 4. Add to views.py
from .services.{next_section}_extractor import {NextSection}Extractor

# 5. Add extraction logic in patient_cda_view

# 6. Add template section in clinical_information_content.html

# 7. Test with Playwright
```

---

## Conclusion

This guide provides a complete blueprint for implementing clinical sections in Django_NCP. The modular approach ensures:

- **Consistency** across different clinical sections
- **Maintainability** through clear separation of concerns
- **Testability** with comprehensive validation
- **Healthcare Standards Compliance** with proper clinical terminology integration

Follow this pattern for each new clinical section to maintain architectural consistency and ensure reliable functionality.