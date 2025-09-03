
# Template Logic Refactor - Integration Instructions

## Overview
This refactor moves complex data processing from the Jinja2 template back to Python,
following proper MVC separation of concerns.

## Files Created
1. `enhanced_view_processor.py` - Data processing functions for Python view
2. `simplified_patient_cda.html` - Clean template with minimal logic

## Integration Steps

### Step 1: Add processor functions to your view
Copy the functions from `enhanced_view_processor.py` into your `patient_data/views.py` file
or import them as a separate module.

### Step 2: Update your view context preparation
In your `patient_cda_view` function, before rendering the template, add:

```python
# Process sections for template display (move complex logic from template to Python)
if translation_result and translation_result.get('sections'):
    from .services.value_set_service import ValueSetService  # Optional
    value_set_service = ValueSetService()  # Optional for terminology lookup
    
    processed_sections = prepare_enhanced_section_data(
        translation_result.get('sections', []),
        value_set_service=value_set_service
    )
    
    # Add processed data to context
    context['processed_sections'] = processed_sections
else:
    context['processed_sections'] = []
```

### Step 3: Replace template
Replace the bloated `enhanced_patient_cda.html` with `simplified_patient_cda.html`

### Step 4: Test functionality
Verify that:
- Medical terminology still displays correctly
- "Unknown" labels are properly replaced
- Template renders quickly without complex processing
- All value set integration works correctly

## Benefits of This Refactor
- ✅ Proper MVC separation of concerns
- ✅ Complex logic in Python where it belongs
- ✅ Simple, maintainable template
- ✅ Better performance (no template-side processing)
- ✅ Easier testing and debugging
- ✅ Clean repository suitable for GitHub commits

## Architecture
- **Python View**: Handles all data processing, field lookups, value set integration
- **Template**: Only displays pre-processed data with minimal conditionals
- **Result**: Same functionality with proper architectural separation
