#!/usr/bin/env python3
"""
Patient Date Formatting Utility
Standardizes date display formats across the Django NCP application
"""

import re
from datetime import datetime
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)


class PatientDateFormatter:
    """
    Utility class for formatting patient dates consistently across the application.

    Handles various input formats from CDA documents and converts them to
    user-friendly display formats suitable for healthcare professionals.
    """

    # Common CDA date patterns used by EU member states
    CDA_PATTERNS = [
        # Full datetime with timezone: 20080728130000+0100, 20250318150929+0000
        (r"^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})[+-]\d{4}$", "%Y%m%d%H%M%S"),
        # Date with time: 20080728130000, 20250318150929
        (r"^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})$", "%Y%m%d%H%M%S"),
        # Date with partial time (hour/minute only): 202503181509
        (r"^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})$", "%Y%m%d%H%M"),
        # Date only: 20080728, 20250318
        (r"^(\d{4})(\d{2})(\d{2})$", "%Y%m%d"),
        # ISO datetime with seconds: 2008-07-28T13:00:00, 2025-03-18T15:09:29
        (r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})", "%Y-%m-%dT%H:%M:%S"),
        # ISO datetime without seconds: 2008-07-28T13:00
        (r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})", "%Y-%m-%dT%H:%M"),
        # Date with dashes: 2008-07-28, 2025-03-18
        (r"^(\d{4})-(\d{2})-(\d{2})$", "%Y-%m-%d"),
        # European date format: 28-07-2008, 18-03-2025
        (r"^(\d{1,2})-(\d{1,2})-(\d{4})$", "%d-%m-%Y"),
        # Date with dots (German/Austrian): 28.07.2008, 18.03.2025
        (r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$", "%d.%m.%Y"),
        # Date with slashes (European): 28/07/2008, 18/03/2025
        (r"^(\d{1,2})/(\d{1,2})/(\d{4})$", "%d/%m/%Y"),  # Assuming European format
        # HL7 standard format: 20080728130000.000+0100
        (
            r"^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})\.\d{3}[+-]\d{4}$",
            "%Y%m%d%H%M%S",
        ),
    ]

    def __init__(self, default_format: str = "dd/mm/yyyy", locale: str = "en-GB"):
        """
        Initialize the date formatter.

        Args:
            default_format: Default output format ("dd/mm/yyyy", "mm/dd/yyyy", "yyyy-mm-dd")
            locale: Locale for date interpretation (affects ambiguous formats)
        """
        self.default_format = default_format
        self.locale = locale

    def format_patient_birth_date(self, date_input: Union[str, datetime, None]) -> str:
        """
        Format a patient's birth date for display.

        Args:
            date_input: Raw date from CDA or database

        Returns:
            Formatted date string or "Unknown" if parsing fails
        """
        if not date_input:
            return "Unknown"

        try:
            if isinstance(date_input, datetime):
                return self._format_datetime_to_display(date_input)

            if isinstance(date_input, str):
                # Clean the input
                cleaned_date = date_input.strip()

                # Try to parse the date
                parsed_date = self._parse_cda_date(cleaned_date)
                if parsed_date:
                    return self._format_datetime_to_display(parsed_date)

            logger.warning(f"Could not parse date: {date_input}")
            return "Unknown"

        except Exception as e:
            logger.error(f"Error formatting birth date '{date_input}': {e}")
            return "Unknown"

    def format_document_date(self, date_input: Union[str, datetime, None]) -> str:
        """
        Format a document creation/effective date for display.

        Args:
            date_input: Raw date from CDA document

        Returns:
            Formatted date string with time if available
        """
        if not date_input:
            return "Unknown"

        try:
            if isinstance(date_input, datetime):
                return self._format_datetime_to_display(date_input, include_time=True)

            if isinstance(date_input, str):
                cleaned_date = date_input.strip()
                parsed_date = self._parse_cda_date(cleaned_date)
                if parsed_date:
                    # Include time for document dates if available
                    has_time = len(cleaned_date) > 8  # More than just YYYYMMDD
                    return self._format_datetime_to_display(
                        parsed_date, include_time=has_time
                    )

            return "Unknown"

        except Exception as e:
            logger.error(f"Error formatting document date '{date_input}': {e}")
            return "Unknown"

    def format_clinical_datetime(self, date_input: Union[str, datetime, None]) -> str:
        """
        Format a clinical datetime for Enhanced Extended Header display.
        Provides professional medical-grade formatting similar to Malta standards.

        Args:
            date_input: Raw date from CDA document

        Returns:
            Formatted datetime string in format: "March 18, 2025, 3:09:29PM +0000"
        """
        if not date_input:
            return "Not specified"

        try:
            if isinstance(date_input, datetime):
                return self._format_clinical_datetime_display(date_input)

            if isinstance(date_input, str):
                cleaned_date = date_input.strip()

                # Extract timezone if present
                timezone_match = re.search(r"([+-]\d{4})$", cleaned_date)
                timezone_str = timezone_match.group(1) if timezone_match else ""

                parsed_date = self._parse_cda_date(cleaned_date)
                if parsed_date:
                    formatted = self._format_clinical_datetime_display(parsed_date)
                    if timezone_str:
                        formatted += f" {timezone_str}"
                    return formatted

            return "Not specified"

        except Exception as e:
            logger.error(f"Error formatting clinical datetime '{date_input}': {e}")
            return "Not specified"

    def _parse_cda_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse various CDA and FHIR date formats into a datetime object.

        Args:
            date_str: Date string from CDA document or FHIR resource

        Returns:
            Parsed datetime or None if parsing fails
        """
        if not date_str:
            return None

        # Clean up the input
        date_clean = date_str.strip()

        # FHIR ISO 8601 with 'Z' timezone indicator: 2022-06-15T00:00:00Z
        if 'Z' in date_clean:
            try:
                # Remove 'Z' and parse as UTC
                clean_input = date_clean.replace('Z', '')
                if 'T' in clean_input:
                    parsed = datetime.strptime(clean_input, "%Y-%m-%dT%H:%M:%S")
                else:
                    parsed = datetime.strptime(clean_input, "%Y-%m-%d")
                logger.debug(f"Successfully parsed FHIR ISO date with Z: '{date_str}'")
                return parsed
            except ValueError:
                pass
        
        # FHIR ISO 8601 with timezone offset: 2022-06-15T00:00:00+01:00
        if 'T' in date_clean and ('+' in date_clean[10:] or date_clean.count('-') > 2):
            try:
                # Python 3.7+ supports fromisoformat with timezone
                parsed = datetime.fromisoformat(date_clean.replace('Z', '+00:00'))
                logger.debug(f"Successfully parsed FHIR ISO date with timezone: '{date_str}'")
                return parsed
            except (ValueError, AttributeError):
                # Fallback: strip timezone and parse
                try:
                    clean_input = re.sub(r'[+-]\d{2}:\d{2}$', '', date_clean)
                    if 'T' in clean_input:
                        parsed = datetime.strptime(clean_input, "%Y-%m-%dT%H:%M:%S")
                    else:
                        parsed = datetime.strptime(clean_input, "%Y-%m-%d")
                    logger.debug(f"Successfully parsed FHIR ISO date (timezone stripped): '{date_str}'")
                    return parsed
                except ValueError:
                    pass

        # Remove CDA timezone offset and milliseconds for parsing
        date_clean = re.sub(r"\.\d{3}[+-]\d{4}$", "", date_clean)  # Remove .000+0100
        date_clean = re.sub(r"[+-]\d{4}$", "", date_clean)  # Remove +0100

        # Try each pattern in order of specificity
        for pattern, format_str in self.CDA_PATTERNS:
            if format_str is None:  # Skip patterns without format strings
                continue

            match = re.match(pattern, date_clean)
            if match:
                try:
                    parsed = datetime.strptime(date_clean, format_str)
                    logger.debug(
                        f"Successfully parsed '{date_str}' using pattern '{format_str}'"
                    )
                    return parsed
                except ValueError as e:
                    logger.debug(
                        f"Pattern '{format_str}' matched but parsing failed for '{date_clean}': {e}"
                    )
                    continue

        # Handle special formats that don't fit standard patterns
        special_formats = [
            # HL7 format variations
            (r"^\d{14}$", "%Y%m%d%H%M%S"),  # 20250318150929
            (r"^\d{12}$", "%Y%m%d%H%M"),  # 202503181509
            (r"^\d{8}$", "%Y%m%d"),  # 20250318
        ]

        for pattern, format_str in special_formats:
            if re.match(pattern, date_clean):
                try:
                    parsed = datetime.strptime(date_clean, format_str)
                    logger.debug(
                        f"Successfully parsed '{date_str}' using special format '{format_str}'"
                    )
                    return parsed
                except ValueError:
                    continue

        logger.warning(f"Unable to parse date string: '{date_str}'")
        return None

    def _format_datetime_to_display(
        self, dt: datetime, include_time: bool = False
    ) -> str:
        """
        Format datetime to user-friendly display format.

        Args:
            dt: Datetime object to format
            include_time: Whether to include time component

        Returns:
            Formatted date string
        """
        if self.default_format == "dd/mm/yyyy":
            date_part = dt.strftime("%d/%m/%Y")
        elif self.default_format == "mm/dd/yyyy":
            date_part = dt.strftime("%m/%d/%Y")
        elif self.default_format == "yyyy-mm-dd":
            date_part = dt.strftime("%Y-%m-%d")
        else:
            # Fallback to ISO format
            date_part = dt.strftime("%Y-%m-%d")

        if include_time and (dt.hour != 0 or dt.minute != 0 or dt.second != 0):
            time_part = dt.strftime("%H:%M")
            return f"{date_part} {time_part}"

        return date_part

    def _format_clinical_datetime_display(self, dt: datetime) -> str:
        """
        Format datetime for clinical/medical display following Malta standards.

        Args:
            dt: Datetime object to format

        Returns:
            Formatted string like "March 18, 2025, 3:09:29PM"
        """
        # Format: "March 18, 2025, 3:09:29PM"
        date_part = dt.strftime("%B %d, %Y")  # March 18, 2025

        # Handle time formatting with 12-hour format
        if dt.hour != 0 or dt.minute != 0 or dt.second != 0:
            time_part = dt.strftime("%I:%M:%S%p")  # 3:09:29PM
            # Remove leading zero from hour if present
            time_part = time_part.lstrip("0")
            return f"{date_part}, {time_part}"
        else:
            # Date only
            return date_part

    def get_age_from_birth_date(
        self, birth_date: Union[str, datetime, None]
    ) -> Optional[int]:
        """
        Calculate patient age from birth date.

        Args:
            birth_date: Patient's birth date

        Returns:
            Age in years or None if calculation fails
        """
        if not birth_date:
            return None

        try:
            if isinstance(birth_date, str):
                birth_dt = self._parse_cda_date(birth_date)
            else:
                birth_dt = birth_date

            if birth_dt:
                today = datetime.now()
                age = today.year - birth_dt.year

                # Adjust if birthday hasn't occurred this year
                if today.month < birth_dt.month or (
                    today.month == birth_dt.month and today.day < birth_dt.day
                ):
                    age -= 1

                return max(0, age)  # Ensure non-negative age

        except Exception as e:
            logger.error(f"Error calculating age from '{birth_date}': {e}")

        return None

    def format_with_age(self, birth_date: Union[str, datetime, None]) -> str:
        """
        Format birth date with calculated age.

        Args:
            birth_date: Patient's birth date

        Returns:
            Formatted string like "01/01/1970 (54 years old)"
        """
        formatted_date = self.format_patient_birth_date(birth_date)

        if formatted_date == "Unknown":
            return formatted_date

        age = self.get_age_from_birth_date(birth_date)
        if age is not None:
            return f"{formatted_date} ({age} years old)"

        return formatted_date


# Global formatter instance with European default
default_formatter = PatientDateFormatter(default_format="dd/mm/yyyy", locale="en-GB")


class ClinicalDateFormatter:
    """
    Enhanced clinical date formatter for FHIR and CDA data sources
    Provides consistent formatting across all clinical sections
    
    This class serves as a unified interface for date formatting,
    supporting both the existing PatientDateFormatter methods and
    new FHIR-specific formatting requirements.
    """
    
    # European healthcare standard format (day first, full month name)
    HEALTHCARE_FORMAT = "%d %B %Y"  # "15 June 2022"
    
    # Alternative US format
    US_FORMAT = "%B %d, %Y"  # "June 15, 2022"
    
    @classmethod
    def format_clinical_date(
        cls,
        date_input: Optional[str],
        include_time: bool = False,
        use_us_format: bool = False,
        default_text: str = "Not recorded"
    ) -> str:
        """
        Format date for clinical display with professional healthcare formatting
        
        Supports both FHIR ISO 8601 and CDA compact formats, outputting
        user-friendly dates with full month names.
        
        Args:
            date_input: Date string in FHIR or CDA format
            include_time: Include time component if available
            use_us_format: Use US date format instead of European
            default_text: Text to return if date is missing
            
        Returns:
            Formatted date: "15 June 2022" or "June 15, 2022"
        """
        if not date_input or date_input in ["Not specified", "Unknown", "Not recorded", ""]:
            return default_text
        
        try:
            # Parse using existing PatientDateFormatter
            parsed_date = default_formatter._parse_cda_date(date_input)
            
            if not parsed_date:
                logger.debug(f"Could not parse clinical date: {date_input}")
                return date_input
            
            # Format with full month name
            format_str = cls.US_FORMAT if use_us_format else cls.HEALTHCARE_FORMAT
            formatted = parsed_date.strftime(format_str)
            
            # Remove leading zero from day (01 -> 1, 08 -> 8)
            # This makes dates more natural: "8 September 2021" not "08 September 2021"
            if not use_us_format:
                # European format: "DD Month YYYY" - strip leading zero from day
                parts = formatted.split(' ')
                if len(parts) >= 2 and parts[0].startswith('0'):
                    parts[0] = parts[0].lstrip('0')
                    formatted = ' '.join(parts)
            else:
                # US format: "Month DD, YYYY" - strip leading zero from day
                parts = formatted.split(' ')
                if len(parts) >= 2 and parts[1].startswith('0'):
                    parts[1] = parts[1].lstrip('0')
                    formatted = ' '.join(parts)
            
            # Add time if requested and significant (not midnight)
            if include_time and (parsed_date.hour != 0 or parsed_date.minute != 0):
                time_str = parsed_date.strftime("%H:%M")
                formatted += f" at {time_str}"
            
            return formatted
            
        except Exception as e:
            logger.warning(f"Clinical date formatting error for '{date_input}': {e}")
            return date_input
    
    @classmethod
    def format_pregnancy_date(cls, date_input: Optional[str]) -> str:
        """
        Format date for pregnancy history display
        Always uses full month name without time
        
        Examples:
            "2022-06-15" -> "15 June 2022"
            "20220615" -> "15 June 2022"
        """
        return cls.format_clinical_date(date_input, include_time=False)
    
    @classmethod
    def format_observation_date(cls, date_input: Optional[str]) -> str:
        """
        Format date for observation/vital signs display
        Includes time if significant
        """
        return cls.format_clinical_date(date_input, include_time=True)
    
    @classmethod
    def format_medication_date(cls, date_input: Optional[str]) -> str:
        """Format date for medication statements"""
        return cls.format_clinical_date(date_input, include_time=False)
    
    @classmethod
    def format_procedure_date(cls, date_input: Optional[str]) -> str:
        """Format date for procedure records with time"""
        return cls.format_clinical_date(date_input, include_time=True)
    
    @classmethod
    def to_iso_date(cls, date_input: Optional[str]) -> Optional[str]:
        """
        Convert any date format to ISO (YYYY-MM-DD) for sorting
        
        Returns:
            ISO date string or None
        """
        if not date_input:
            return None
        
        try:
            parsed_date = default_formatter._parse_cda_date(date_input)
            if parsed_date:
                return parsed_date.strftime("%Y-%m-%d")
        except Exception:
            pass
        
        return None
    
    @classmethod
    def format_date_range(
        cls,
        start_date: Optional[str],
        end_date: Optional[str],
        separator: str = " to "
    ) -> str:
        """
        Format a date range for display
        
        Returns:
            "15 June 2022 to 20 June 2022" or appropriate variations
        """
        formatted_start = cls.format_clinical_date(start_date)
        formatted_end = cls.format_clinical_date(end_date)
        
        if formatted_start == "Not recorded" and formatted_end == "Not recorded":
            return "Not recorded"
        elif formatted_start == "Not recorded":
            return f"Until {formatted_end}"
        elif formatted_end == "Not recorded":
            return f"From {formatted_start}"
        else:
            return f"{formatted_start}{separator}{formatted_end}"


# Convenience functions for templates
def format_birth_date(date_input: Union[str, datetime, None]) -> str:
    """Template-friendly birth date formatter."""
    return default_formatter.format_patient_birth_date(date_input)


def format_document_date(date_input: Union[str, datetime, None]) -> str:
    """Template-friendly document date formatter."""
    return default_formatter.format_document_date(date_input)


def format_birth_date_with_age(date_input: Union[str, datetime, None]) -> str:
    """Template-friendly birth date with age formatter."""
    return default_formatter.format_with_age(date_input)


if __name__ == "__main__":
    # Test the formatter with various date formats
    formatter = PatientDateFormatter()

    test_dates = [
        "19700101",  # Mario PINO's birth date
        "20080728130000+0100",  # Document creation with timezone
        "2008-07-28T13:00:00",  # ISO format
        "20230714194500+0200",  # Portuguese CDA date
        "1982-05-08",  # Dash format
        None,  # Missing date
        "",  # Empty date
        "invalid",  # Invalid format
    ]

    print("🗓️  PATIENT DATE FORMATTER TEST")
    print("=" * 50)

    for date_str in test_dates:
        print(f"\nInput: {repr(date_str)}")
        print(f"  Birth Date: {formatter.format_patient_birth_date(date_str)}")
        print(f"  Document Date: {formatter.format_document_date(date_str)}")
        print(f"  With Age: {formatter.format_with_age(date_str)}")
