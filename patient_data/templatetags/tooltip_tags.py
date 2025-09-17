"""
Tooltip Template Tags
Django template tags for centralized tooltip management
"""

from django import template
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from ..models import Tooltip

register = template.Library()


@register.simple_tag
def tooltip(key, default_content="", placement="bottom"):
    """
    Retrieve tooltip content and generate HTML attributes
    
    Usage in templates:
    {% tooltip "source_country_flag" "Default tooltip text" "top" %}
    
    Args:
        key (str): Unique tooltip identifier
        default_content (str): Fallback content if tooltip not found
        placement (str): Bootstrap tooltip placement (top, bottom, left, right, auto)
    
    Returns:
        str: HTML attributes for data-bs-toggle, data-bs-placement, and title
    """
    tooltip_data = Tooltip.get_tooltip_data(key)
    
    if tooltip_data:
        content = tooltip_data['content']
        placement = tooltip_data.get('placement', placement)
    else:
        content = default_content
    
    if content:
        return format_html(
            'data-bs-toggle="tooltip" data-bs-placement="{}" title="{}"',
            placement,
            content
        )
    return ""


@register.simple_tag
def tooltip_content(key, default=""):
    """
    Get just the tooltip content text
    
    Usage:
    {% tooltip_content "source_country_flag" "Default text" %}
    
    Args:
        key (str): Unique tooltip identifier
        default (str): Fallback content if tooltip not found
    
    Returns:
        str: Tooltip content text
    """
    return Tooltip.get_tooltip(key, default)


@register.simple_tag
def tooltip_data(key):
    """
    Get complete tooltip data as dictionary
    
    Usage:
    {% tooltip_data "source_country_flag" as tooltip_info %}
    {% if tooltip_info %}
        Title: {{ tooltip_info.title }}
        Content: {{ tooltip_info.content }}
        Placement: {{ tooltip_info.placement }}
    {% endif %}
    
    Args:
        key (str): Unique tooltip identifier
    
    Returns:
        dict or None: Complete tooltip data or None if not found
    """
    return Tooltip.get_tooltip_data(key)


@register.inclusion_tag('patient_data/partials/tooltip_span.html')
def tooltip_span(key, text, css_class="", default_content="", placement="bottom"):
    """
    Render a complete span element with tooltip
    
    Usage:
    {% tooltip_span "source_country_flag" "IE" "badge bg-info" "Country information" "top" %}
    
    Args:
        key (str): Unique tooltip identifier
        text (str): Text to display in the span
        css_class (str): CSS classes for the span
        default_content (str): Fallback tooltip content
        placement (str): Bootstrap tooltip placement
    
    Returns:
        dict: Context for the template
    """
    tooltip_data = Tooltip.get_tooltip_data(key)
    
    if tooltip_data:
        content = tooltip_data['content']
        placement = tooltip_data.get('placement', placement)
    else:
        content = default_content
    
    return {
        'text': text,
        'css_class': css_class,
        'tooltip_content': content,
        'placement': placement,
        'has_tooltip': bool(content)
    }


@register.filter
def has_tooltip(key):
    """
    Check if a tooltip exists and is active
    
    Usage:
    {% if "source_country_flag"|has_tooltip %}
        <!-- Tooltip exists -->
    {% endif %}
    
    Args:
        key (str): Unique tooltip identifier
    
    Returns:
        bool: True if tooltip exists and is active
    """
    return Tooltip.get_tooltip_data(key) is not None


@register.simple_tag
def render_tooltip_badge(key, text, badge_type="primary", icon_class="", default_content=""):
    """
    Render a complete badge with tooltip and optional icon
    
    Usage:
    {% render_tooltip_badge "source_country_flag" "IE" "info" "fas fa-flag" "Country info" %}
    
    Args:
        key (str): Unique tooltip identifier
        text (str): Badge text
        badge_type (str): Bootstrap badge type (primary, success, info, etc.)
        icon_class (str): Font Awesome icon classes
        default_content (str): Fallback tooltip content
    
    Returns:
        str: Complete HTML for badge with tooltip
    """
    tooltip_data = Tooltip.get_tooltip_data(key)
    
    if tooltip_data:
        content = tooltip_data['content']
        placement = tooltip_data.get('placement', 'bottom')
    else:
        content = default_content
        placement = 'bottom'
    
    icon_html = f'<i class="{icon_class} me-1"></i>' if icon_class else ''
    
    if content:
        return format_html(
            '<span class="badge bg-{}" data-bs-toggle="tooltip" data-bs-placement="{}" title="{}">{}{}</span>',
            badge_type,
            placement,
            content,
            mark_safe(icon_html),
            text
        )
    else:
        return format_html(
            '<span class="badge bg-{}">{}{}</span>',
            badge_type,
            mark_safe(icon_html),
            text
        )