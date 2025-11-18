# Date Format Standardization Plan

## Current State Analysis

### Issue
CDA and FHIR pregnancy history sections display dates in different formats:
- **FHIR Format**: `2022-06-15` or `2022-06-15 00:00` (ISO 8601 format from `_format_datetime_display()`)
- **CDA Format**: Various formats depending on source (likely showing raw XML dates)
- **Goal**: Standardize to user-friendly format: `June 15, 2022` or `15 June 2022`

### Current Date Handling

#### 1. FHIR Date Processing (`eu_ncp_server/services/fhir_processing.py`)
```python
def _format_datetime_display(self, datetime_str: Optional[str]) -> Optional[str]:
    """Format FHIR dateTime for display"""
    if not datetime_str:
        return None
    
    try:
        from datetime import datetime
        # Parse FHIR dateTime format (ISO 8601)
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')  # Returns: "2022-06-15 00:00"
    except (ValueError, AttributeError):
        return datetime_str
```

**Problem**: Returns technical ISO format, not user-friendly clinical format.

#### 2. CDA Date Processing (`patient_data/services.py`)
```python
def _format_date(self, date_str: str) -> str:
    """Format date string for display"""
    if not date_str:
        return "Not provided"

    # Extract date part (YYYYMMDD)
    clean_date = re.sub(r"\D", "", date_str)[:8]

    if len(clean_date) == 8:
        try:
            year = clean_date[:4]
            month = clean_date[4:6]
            day = clean_date[6:8]
            date_obj = datetime.strptime(f"{year}-{month}-{day}", "%Y-%m-%d")
            return date_obj.strftime("%d %B %Y")  # Returns: "15 June 2022"
        except ValueError:
            pass

    return date_str
```

**Status**: Good format, but only used for CDA effectiveTime parsing in limited contexts.

#### 3. Views Date Formatting (`patient_data/views.py`)
```python
def format_clinical_date(date_string):
    """Format date for clinical display with timezone support"""
    # ... comprehensive parsing logic ...
    return date_obj.strftime("%B %d, %Y")  # Returns: "June 15, 2022"
```

**Status**: Best implementation but not consistently used across all clinical sections.

## Recommended Solution

### Strategy
Create a centralized date formatting utility that both parsers use, ensuring consistency across CDA and FHIR sources.

### Implementation Plan

#### 1. Create Unified Date Formatter Utility
**Location**: `patient_data/utils/date_formatter.py` (NEW)

```python
"""
Clinical Date Formatting Utility
Standardizes date display across CDA and FHIR data sources
"""

from datetime import datetime
from typing import Optional
import re


class ClinicalDateFormatter:
    """
    Centralized date formatting for clinical data display
    Supports both CDA and FHIR date formats
    """
    
    # European-style format (preferred for healthcare)
    DEFAULT_FORMAT = "%d %B %Y"  # "15 June 2022"
    
    # Alternative US-style format
    US_FORMAT = "%B %d, %Y"  # "June 15, 2022"
    
    # ISO format for sorting/comparison
    ISO_FORMAT = "%Y-%m-%d"  # "2022-06-15"
    
    @classmethod
    def format_clinical_date(cls, date_input: Optional[str], 
                            include_time: bool = False,
                            use_us_format: bool = False) -> str:
        """
        Format date for clinical display
        
        Args:
            date_input: Date string in various formats
            include_time: Include time component if available
            use_us_format: Use US date format instead of European
            
        Returns:
            Formatted date string or "Not recorded"
        """
        if not date_input or date_input in ["Not specified", "Unknown", "Not recorded"]:
            return "Not recorded"
        
        try:
            # Parse date from various sources
            date_obj, time_str = cls._parse_date(date_input)
            
            if not date_obj:
                return date_input  # Return original if unparseable
            
            # Format date
            format_str = cls.US_FORMAT if use_us_format else cls.DEFAULT_FORMAT
            formatted = date_obj.strftime(format_str)
            
            # Add time if requested and available
            if include_time and time_str:
                formatted += f" at {time_str}"
            
            return formatted
            
        except Exception as e:
            return date_input  # Graceful fallback
    
    @classmethod
    def _parse_date(cls, date_input: str) -> tuple[Optional[datetime], Optional[str]]:
        """
        Parse date from various formats
        
        Returns:
            Tuple of (datetime object, time string or None)
        """
        # 1. FHIR ISO 8601 format: "2022-06-15T00:00:00Z" or "2022-06-15"
        if 'T' in date_input or date_input.count('-') >= 2:
            try:
                # Remove timezone indicator
                clean_input = date_input.replace('Z', '+00:00')
                
                # Try full ISO format with time
                if 'T' in clean_input:
                    dt = datetime.fromisoformat(clean_input)
                    time_str = dt.strftime('%H:%M') if dt.hour or dt.minute else None
                    return dt, time_str
                
                # Try date-only ISO format
                dt = datetime.strptime(date_input, '%Y-%m-%d')
                return dt, None
                
            except (ValueError, AttributeError):
                pass
        
        # 2. CDA format: "YYYYMMDD" or "YYYYMMDDHHMMSS"
        clean_date = re.sub(r"\D", "", date_input)[:8]
        if len(clean_date) == 8:
            try:
                year = clean_date[:4]
                month = clean_date[4:6]
                day = clean_date[6:8]
                dt = datetime.strptime(f"{year}-{month}-{day}", "%Y-%m-%d")
                
                # Check for time component
                if len(clean_date) >= 14:
                    hour = clean_date[8:10]
                    minute = clean_date[10:12]
                    time_str = f"{hour}:{minute}"
                    return dt, time_str
                
                return dt, None
            except ValueError:
                pass
        
        # 3. Common formats: "DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD HH:MM:SS"
        for fmt in ["%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d"]:
            try:
                dt = datetime.strptime(date_input, fmt)
                time_str = dt.strftime('%H:%M') if '%H' in fmt else None
                return dt, time_str
            except ValueError:
                continue
        
        return None, None
    
    @classmethod
    def format_pregnancy_date(cls, date_input: Optional[str]) -> str:
        """
        Format date specifically for pregnancy history display
        Always uses full month name format
        """
        return cls.format_clinical_date(date_input, include_time=False)
    
    @classmethod
    def format_observation_date(cls, date_input: Optional[str]) -> str:
        """
        Format date for observation/vital signs display
        May include time if significant
        """
        return cls.format_clinical_date(date_input, include_time=True)
```

#### 2. Update FHIR Processor
**File**: `eu_ncp_server/services/fhir_processing.py`

```python
from patient_data.utils.date_formatter import ClinicalDateFormatter

def _format_datetime_display(self, datetime_str: Optional[str]) -> Optional[str]:
    """Format FHIR dateTime for clinical display"""
    return ClinicalDateFormatter.format_clinical_date(
        datetime_str, 
        include_time=True
    )
```

#### 3. Update FHIR Bundle Parser Pregnancy Processing
**File**: `patient_data/services/fhir_bundle_parser.py`

Add date formatting when creating pregnancy records:

```python
from patient_data.utils.date_formatter import ClinicalDateFormatter

# In _extract_pregnancy_observations method
pregnancy_record = {
    'pregnancy_type': 'past',
    'observation_id': f"pregnancy-{group_key}",
    'resource_type': 'PregnancyGroup',
    'delivery_date': ClinicalDateFormatter.format_pregnancy_date(delivery_date_key),  # ADD THIS
    'delivery_date_raw': delivery_date_key,  # Keep raw for sorting
    # ... rest of fields
}
```

#### 4. Update Template to Use Formatted Date
**File**: `templates/patient_data/sections/pregnancy_history_section.html`

Template already displays `{{ pregnancy.delivery_date }}` - no changes needed if parser formats correctly.

## Benefits

### 1. Consistency
- ✅ CDA dates: `15 June 2022`
- ✅ FHIR dates: `15 June 2022`
- ✅ All clinical sections use same format

### 2. User Experience
- ✅ Healthcare professionals see familiar date format
- ✅ Month names reduce ambiguity (vs MM/DD vs DD/MM)
- ✅ Professional clinical appearance

### 3. Maintainability
- ✅ Single source of truth for date formatting
- ✅ Easy to change format organization-wide
- ✅ Handles edge cases consistently

### 4. Internationalization Ready
- ✅ Can add locale-specific formatting
- ✅ Supports both European and US formats
- ✅ Extensible for other regional preferences

## Implementation Steps

1. **Create `patient_data/utils/date_formatter.py`** with `ClinicalDateFormatter` class
2. **Update FHIR processor** to use new formatter
3. **Update FHIR bundle parser** pregnancy extraction to format dates
4. **Test with Diana Ferreira** data to verify both CDA and FHIR dates display consistently
5. **Consider extending** to other clinical sections (observations, procedures, etc.)

## Testing Checklist

- [ ] Diana Ferreira pregnancy dates display as "15 June 2022" format
- [ ] CDA pregnancy outcomes show formatted dates
- [ ] FHIR pregnancy outcomes show formatted dates
- [ ] Both formats are identical in UI
- [ ] Dates without time don't show "00:00"
- [ ] Edge cases handled (partial dates, malformed inputs)

## Future Enhancements

1. **Relative Date Display**: "3 months ago" for recent observations
2. **Gestational Age Calculation**: Automatically calculate weeks from EDD
3. **Date Range Formatting**: "15 June 2022 to 20 June 2022"
4. **Timezone Support**: Display user's local timezone for international use
5. **Calendar Integration**: Export to ICS format for appointment tracking

## Rollout Strategy

### Phase 1: Pregnancy History (Current Priority)
- Format pregnancy delivery dates
- Format expected delivery dates
- Ensure consistency across CDA/FHIR

### Phase 2: Other Clinical Sections
- Observation dates
- Procedure dates
- Medication dates
- Immunization dates

### Phase 3: Patient Demographics
- Birth dates
- Document dates
- Consent dates

## Conclusion

By implementing a centralized `ClinicalDateFormatter` utility, we achieve:
- **Consistency**: Same format across all data sources
- **Professionalism**: User-friendly clinical date display
- **Maintainability**: Single point of formatting logic
- **Flexibility**: Easy to adjust for regional preferences

**Next Step**: Create the utility class and integrate into FHIR processing pipeline.
