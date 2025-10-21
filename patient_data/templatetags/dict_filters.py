from django import template
import ast
import json
import logging

register = template.Library()
logger = logging.getLogger(__name__)

@register.filter
def dict_value(value, key):
    """
    Extract a value from a dictionary or dictionary string representation.
    Usage: {{ item.pharmaceutical_form|dict_value:"display_value" }}
    """
    if not value:
        return ""
    
    # If it's already a dictionary, extract the key
    if isinstance(value, dict):
        return value.get(key, "")
    
    # If it's a string representation of a dictionary, try to parse it
    if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
        try:
            # Try JSON parsing first
            parsed_dict = json.loads(value.replace("'", '"'))
            return parsed_dict.get(key, "")
        except (json.JSONDecodeError, ValueError):
            try:
                # Try AST literal_eval as fallback
                parsed_dict = ast.literal_eval(value)
                return parsed_dict.get(key, "")
            except (ValueError, SyntaxError) as e:
                logger.warning(f"Failed to parse dictionary string: {value[:50]}... Error: {e}")
                return ""
    
    # If it's a string that doesn't look like a dictionary, return as-is
    if isinstance(value, str):
        return value
    
    # For other types, try to get the attribute directly
    try:
        return getattr(value, key, "")
    except (AttributeError, TypeError):
        return ""

@register.filter
def safe_dict_value(value, key):
    """
    Safely extract a value from a dictionary with fallback to common key patterns.
    Tries: display_value, value, translated, coded, then the raw value
    """
    result = dict_value(value, key)
    if result:
        return result
    
    # Try common fallback patterns
    fallback_keys = {
        'display_value': ['value', 'translated', 'coded'],
        'value': ['display_value', 'coded', 'translated'],
        'translated': ['display_value', 'value', 'coded'],
        'coded': ['value', 'display_value', 'translated']
    }
    
    for fallback_key in fallback_keys.get(key, []):
        result = dict_value(value, fallback_key)
        if result:
            return result
    
    # Last resort: return the raw value if it's a simple string
    if isinstance(value, str) and not value.startswith("{"):
        return value
    
    return ""