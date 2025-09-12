"""
Custom template tags for patient data
"""

from django import template

register = template.Library()


@register.filter
def lookup(dictionary, key):
    """Template filter to look up dictionary values"""
    return dictionary.get(key, [])


@register.filter
def dict_key(dictionary, key):
    """Template filter to access dictionary keys"""
    return dictionary.get(key)


@register.filter
def multiply(value, arg):
    """Multiply value by argument"""
    return value * arg


@register.filter
def get_item(dictionary, key):
    """Template filter to get item from dictionary by key - equivalent to dictionary[key]"""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    elif hasattr(dictionary, "__getitem__"):
        try:
            return dictionary[key]
        except (KeyError, IndexError, TypeError):
            return None
    return None


@register.filter
def dict_items(dictionary):
    """Template filter to get dictionary items - equivalent to dictionary.items()"""
    if isinstance(dictionary, dict):
        return dictionary.items()
    elif hasattr(dictionary, "items"):
        return dictionary.items()
    return []


@register.filter
def subtract(value, arg):
    """Template filter to subtract arg from value - equivalent to value - arg"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def safe_get(data, key):
    """Template filter to safely get a value from dictionary or object, handling missing keys gracefully"""
    if isinstance(data, dict):
        if key in data:
            return data[key]
        # Handle different data structures
        if key == "value" and "count" in data:
            return data["count"]
        elif key == "count" and "value" in data:
            return data["value"]
        return None
    elif hasattr(data, key):
        return getattr(data, key, None)
    return None
