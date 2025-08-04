# PS Display Guidelines - Dynamic Table Rendering System

## Overview

The Patient Summary Display Guidelines require structured presentation of clinical data in standardized table formats. Our Django NCP system now implements dynamic table rendering in Python (backend) rather than pure Jinja2 templates for better:

- **Standardization**: Consistent table structures across all PS sections
- **Flexibility**: Adaptable to varying L3 CDA content structures
- **Maintainability**: Centralized table logic for easier updates
- **PDF Generation**: Simplified HTML for better PDF conversion
- **Compliance**: Adherence to European healthcare display standards

## Architecture

### Components

1. **PSTableRenderer** (`patient_data/services/ps_table_renderer.py`)
   - Processes CDA sections into structured table data
   - Handles section-specific rendering (medications, allergies, etc.)
   - Extracts data from existing HTML tables or free text

2. **Enhanced Views** (`patient_data/views.py`)
   - Integrates table renderer into CDA processing pipeline
   - Passes structured table data to templates

3. **Template Updates** (`templates/jinja2/patient_data/patient_cda.html`)
   - Renders structured tables using Jinja2 loops
   - Falls back to original content when structured data unavailable

4. **PS Table Styling** (`static/scss/pages/_patient_cda.scss`)
   - Professional healthcare-grade table styling
   - Section-specific column sizing
   - Mobile responsiveness and print optimization

## Section-Specific Table Structures

### Medications (LOINC: 10160-0)

```
Headers: Medication | Active Ingredient | Dosage | Route | Frequency | Start Date | End Date | Notes
```

### Allergies (LOINC: 48765-2)

```
Headers: Allergy Type | Causative Agent | Manifestation | Severity | Status
```

### Problems (LOINC: 11450-4)

```
Headers: Problem/Diagnosis | Status | Onset Date | Notes
```

### Procedures (LOINC: 47519-4)

```
Headers: Procedure | Date | Performer | Location | Notes
```

### Results (LOINC: 30954-2)

```
Headers: Test/Result | Value | Reference Range | Date | Status
```

### Immunizations (LOINC: 10157-6)

```
Headers: Vaccine | Date Given | Dose | Route | Provider
```

## Implementation Flow

1. **CDA Section Processing**

   ```python
   # In patient_cda_view
   from .services.ps_table_renderer import PSTableRenderer
   table_renderer = PSTableRenderer()
   enhanced_sections = table_renderer.render_section_tables(sections)
   ```

2. **Section Analysis**
   - Identifies section type by LOINC code
   - Extracts existing table structures using BeautifulSoup
   - Parses free text for structured data when no tables exist

3. **Table Data Creation**

   ```python
   table_data = {
       'headers': ['Column1', 'Column2', ...],
       'rows': [['Cell1', 'Cell2', ...], ...],
       'original_html': '<table>...</table>'  # If exists
   }
   ```

4. **Template Rendering**

   ```jinja2
   {% if section.has_table and section.table_data %}
   <table class="ps-table ps-table-{{ section.section_type }}">
       {% for header in section.table_data.headers %}
       <th class="ps-th">{{ header }}</th>
       {% endfor %}
       <!-- Rows rendered with proper styling -->
   </table>
   {% else %}
   {{ section.content.translated|safe }}
   {% endif %}
   ```

## Benefits of Python-Based Rendering

### 🎯 **Standardization**

- Consistent table structures across all healthcare facilities
- Compliance with PS Display Guidelines requirements
- Uniform column headers and data presentation

### 🔧 **Flexibility**

- Handles varying CDA structures from different countries
- Adapts to both existing table structures and free text
- Extensible for new section types

### 📱 **Responsive Design**

- Mobile-optimized table layouts
- Print-friendly styling for PDF generation
- Accessibility compliance (WCAG AA)

### 🛠️ **Maintainability**

- Centralized table logic in Python services
- Easy to update formatting rules
- Clear separation of concerns

## PDF Generation Compatibility

The simplified HTML structure produced by the table renderer is optimized for:

- **WeasyPrint**: Clean table structures for PDF conversion
- **Puppeteer**: Browser-based PDF generation
- **ReportLab**: Direct table data integration
- **Print Stylesheets**: CSS print media queries for proper formatting

## Future Enhancements

1. **Advanced Data Extraction**
   - Natural Language Processing for better free text parsing
   - Medical entity recognition for coded terminology
   - Automated data validation and standardization

2. **Internationalization**
   - Multi-language table headers
   - Locale-specific date and number formatting
   - Cultural adaptations for different healthcare systems

3. **Enhanced Interactivity**
   - Sortable table columns
   - Advanced filtering and search
   - Data export capabilities (Excel, CSV)

4. **Quality Assurance**
   - Automated table structure validation
   - PS Guidelines compliance checking
   - Data completeness reporting

## Usage Examples

### Adding New Section Types

```python
# In PSTableRenderer class
def _render_custom_section(self, section: Dict) -> Dict:
    \"\"\"Render custom section as standardized table\"\"\"
    table_data = {
        'headers': ['Custom1', 'Custom2', 'Custom3'],
        'rows': self._extract_custom_data(section)
    }
    return self._create_enhanced_section(section, table_data, 'custom')
```

### Template Customization

```jinja2
<!-- Section-specific styling -->
{% if section.section_type == 'medications' %}
<div class="medication-highlight">
    <!-- Enhanced medication display -->
</div>
{% endif %}
```

## Testing and Validation

The system includes comprehensive testing for:

- Section identification accuracy
- Table data extraction correctness
- Template rendering integrity
- Cross-browser compatibility
- PDF generation quality

This implementation provides a robust foundation for professional healthcare document display that meets European Patient Summary standards while maintaining flexibility for diverse clinical data structures.
