"""
Jinja2 Environment Configuration for EU NCP Server

This module sets up the Jinja2 template environment with custom functions
and filters needed for the EU eHealth portal templates.

IMPORTANT: URL Configuration Fix
==============================

This file contains a critical fix for Django Jinja2 URL reversal.
DO NOT replace the url_helper function with Django's reverse function directly.

Problem: Using "url": reverse directly causes this error:
    ImproperlyConfigured: The included URLconf '<parameter>' does not appear to have any patterns

Solution: Use the url_helper function which properly handles URL arguments.

For complete documentation, see: JINJA2_URL_CONFIGURATION.md
"""

from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from jinja2 import Environment
import os


def url_helper(viewname, *args, **kwargs):
    """
    Helper function for URL reversal in Jinja2 templates.

    CRITICAL: This function fixes a common Django Jinja2 URL configuration issue.

    Problem Solved:
    ===============
    Without this helper, using Django's reverse function directly in Jinja2
    causes ImproperlyConfigured errors when templates call {{ url('app:view', param) }}
    because reverse() interprets the parameter as urlconf instead of args.

    This function properly handles arguments for Django's reverse function
    in Jinja2 templates, converting positional arguments to the args parameter.

    Template Usage Examples:
    ========================
    {{ url('app:view_name') }}                    # No parameters
    {{ url('app:view_name', param1) }}            # Single parameter
    {{ url('app:view_name', param1, param2) }}    # Multiple parameters
    {{ url('app:view_name', id=123) }}            # Keyword arguments

    Args:
        viewname (str): Django URL pattern name (e.g., 'patient_data:patient_details')
        *args: Positional arguments for URL parameters
        **kwargs: Keyword arguments for URL parameters

    Returns:
        str: Reversed URL path

    DO NOT REPLACE THIS WITH: "url": reverse
    """
    if args:
        return reverse(viewname, args=args)
    elif kwargs:
        return reverse(viewname, kwargs=kwargs)
    else:
        return reverse(viewname)


def environment(**options):
    """
    Create and configure Jinja2 environment for Django integration.

    This function is called by Django to create the Jinja2 environment
    and register custom functions and filters.
    """
    env = Environment(**options)

    # Django integration functions
    # CRITICAL: Use url_helper, NOT reverse directly
    # See JINJA2_URL_CONFIGURATION.md for full explanation
    env.globals.update(
        {
            "static": staticfiles_storage.url,
            "url": url_helper,  # DO NOT change to: "url": reverse
        }
    )

    # Custom template functions
    env.globals.update(
        {
            "get_country_flag_class": get_country_flag_class,
            "format_patient_id": format_patient_id,
            "get_member_state_name": get_member_state_name,
        }
    )

    # Custom filters
    env.filters.update(
        {
            "currency": currency_filter,
            "date_format": date_format_filter,
            "basename": lambda x: os.path.basename(x) if x else "",
        }
    )

    return env


def get_country_flag_class(country_code):
    """
    Get CSS class for country flag display.

    Args:
        country_code (str): Two-letter country code (e.g., 'PT', 'IE')

    Returns:
        str: CSS class name for flag display
    """
    if not country_code:
        return "flag-default"

    return f"flag-{country_code.lower()}"


def format_patient_id(patient_id, country_code=None):
    """
    Format patient ID for display with country context.

    Args:
        patient_id (str): Patient identifier
        country_code (str, optional): Two-letter country code

    Returns:
        str: Formatted patient ID
    """
    if not patient_id:
        return ""

    if country_code:
        return f"{country_code.upper()}-{patient_id}"

    return patient_id


def get_member_state_name(country_code):
    """
    Get full member state name from country code.

    Args:
        country_code (str): Two-letter country code

    Returns:
        str: Full country name or country code if not found
    """
    country_names = {
        "PT": "Portugal",
        "IE": "Ireland",
        "DE": "Germany",
        "FR": "France",
        "ES": "Spain",
        "IT": "Italy",
        "NL": "Netherlands",
        "BE": "Belgium",
        "AT": "Austria",
        "CZ": "Czech Republic",
        "PL": "Poland",
        "HU": "Hungary",
        "SK": "Slovakia",
        "SI": "Slovenia",
        "HR": "Croatia",
        "BG": "Bulgaria",
        "RO": "Romania",
        "GR": "Greece",
        "CY": "Cyprus",
        "MT": "Malta",
        "LU": "Luxembourg",
        "FI": "Finland",
        "SE": "Sweden",
        "DK": "Denmark",
        "EE": "Estonia",
        "LV": "Latvia",
        "LT": "Lithuania",
    }

    return country_names.get(
        country_code.upper() if country_code else "", country_code or ""
    )


def currency_filter(value):
    """
    Format numeric value as currency.

    Args:
        value: Numeric value to format

    Returns:
        str: Formatted currency string
    """
    if value is None:
        return ""

    try:
        return f"€{float(value):,.2f}"
    except (ValueError, TypeError):
        return str(value)


def date_format_filter(value, format_string="%Y-%m-%d"):
    """
    Format date value with specified format.

    Args:
        value: Date value to format
        format_string (str): strftime format string

    Returns:
        str: Formatted date string
    """
    if not value:
        return ""

    try:
        if hasattr(value, "strftime"):
            return value.strftime(format_string)
        return str(value)
    except (ValueError, AttributeError):
        return str(value)
