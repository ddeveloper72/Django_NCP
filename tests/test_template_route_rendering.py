"""
Simple template rendering tests for CTS route resolution.
Tests the exact template logic without database dependencies.
"""

import pytest
from django.template import Context, Template
from django.test import SimpleTestCase


class TestTemplateRouteRendering(SimpleTestCase):
    """Test template rendering logic for administration routes."""
    
    def test_template_shows_cts_resolved_text_not_raw_code(self):
        """Test that template prioritizes CTS-resolved text over raw codes."""
        # This is the EXACT template logic from clinical_information_content.html
        template_content = """
        {% if med.data.route_display %}
            <span class="route">{{ med.data.route_display }}</span>
            {% if med.data.route_code %}
                <small>Route Code: {{ med.data.route_code }}</small>
            {% endif %}
        {% elif med.route_display %}
            <span class="route">{{ med.route_display }}</span>
        {% elif med.route %}
            <span class="route">{{ med.route.displayName|default:med.route.code|title }}</span>
            {% if med.route.code %}
                <small>({{ med.route.code }})</small>
            {% endif %}
        {% else %}
            Administration route not specified
        {% endif %}
        """
        
        # Test with CTS-enhanced medication (preferred structure)
        cts_medication = {
            'data': {
                'route_display': 'Oral use',  # CTS-resolved value
                'route_code': '20053000'
            },
            'route': {
                'code': '20053000',
                'displayName': 'Oral use'
            }
        }
        
        template = Template(template_content)
        context = Context({'med': cts_medication})
        rendered = template.render(context).strip()
        
        # Should use the CTS-enhanced data.route_display first
        self.assertIn("Oral use", rendered)
        self.assertIn("Route Code: 20053000", rendered)
        
        # Should NOT show the problematic pattern "20053000 (20053000)"
        self.assertNotIn("20053000 (20053000)", rendered)
        
    def test_template_fallback_with_working_cts(self):
        """Test template fallback when CTS is working in route.displayName."""
        template_content = """
        {% if med.data.route_display %}
            {{ med.data.route_display }}
        {% elif med.route_display %}
            {{ med.route_display }}
        {% elif med.route %}
            {{ med.route.displayName|default:med.route.code|title }}
        {% else %}
            Administration route not specified
        {% endif %}
        """
        
        # Medication with CTS working in route.displayName (like our backend test)
        working_cts_medication = {
            'route': {
                'code': '20053000',
                'displayName': 'Oral use'  # CTS resolved this correctly
            }
        }
        
        template = Template(template_content)
        context = Context({'med': working_cts_medication})
        rendered = template.render(context).strip()
        
        # Should show CTS-resolved text
        self.assertEqual(rendered, "Oral use")
        self.assertNotIn("20053000", rendered)
        
    def test_template_shows_raw_code_when_cts_fails(self):
        """Test template behavior when CTS resolution fails (empty displayName)."""
        template_content = """
        {% if med.data.route_display %}
            {{ med.data.route_display }}
        {% elif med.route_display %}
            {{ med.route_display }}
        {% elif med.route %}
            {{ med.route.displayName|default:med.route.code|title }}
        {% else %}
            Administration route not specified
        {% endif %}
        """
        
        # Medication where CTS failed (empty displayName)
        failed_cts_medication = {
            'route': {
                'code': '20053000',
                'displayName': ''  # CTS resolution failed
            }
        }
        
        template = Template(template_content)
        context = Context({'med': failed_cts_medication})
        rendered = template.render(context).strip()
        
        # Should show formatted code (title case) when CTS fails
        self.assertEqual(rendered, "20053000")
        
    def test_template_problematic_pattern_analysis(self):
        """Analyze the specific problematic pattern '20053000 (20053000)'."""
        # This template mimics the ACTUAL template that creates the problem
        template_content = """
        {% if med.route %}
            {{ med.route.displayName|default:med.route.code|title }}
            {% if med.route.code %}
                <small>({{ med.route.code }})</small>
            {% endif %}
        {% endif %}
        """
        
        # Medication that would create the problematic pattern
        problematic_medication = {
            'route': {
                'code': '20053000',
                'displayName': ''  # Empty, so defaults to code
            }
        }
        
        template = Template(template_content)
        context = Context({'med': problematic_medication})
        rendered = template.render(context).strip()
        
        # This WOULD create the problematic pattern if displayName defaults to code
        # The template shows: "20053000" + "(20053000)" = "20053000 (20053000)"
        expected_pattern = "20053000"  # From displayName|default:code
        self.assertIn(expected_pattern, rendered)
        self.assertIn("(20053000)", rendered)  # From the small tag
        
        # This is exactly the problematic pattern the user sees!
        full_rendered = rendered.replace('\n', ' ').replace('  ', ' ').strip()
        self.assertIn("20053000", full_rendered)
        self.assertIn("(20053000)", full_rendered)

    def test_correct_template_logic_prevents_problem(self):
        """Test that correct CTS integration prevents the problematic pattern."""
        template_content = """
        {% if med.route %}
            {% if med.route.displayName and med.route.displayName != med.route.code %}
                {{ med.route.displayName }}
                <small>Route Code: {{ med.route.code }}</small>
            {% else %}
                {{ med.route.code|title }}
            {% endif %}
        {% endif %}
        """
        
        # Test with working CTS
        working_medication = {
            'route': {
                'code': '20053000',
                'displayName': 'Oral use'  # CTS working
            }
        }
        
        template = Template(template_content)
        context = Context({'med': working_medication})
        rendered = template.render(context).strip()
        
        self.assertIn("Oral use", rendered)
        self.assertIn("Route Code: 20053000", rendered)
        self.assertNotIn("20053000 (20053000)", rendered)
        
        # Test with failed CTS
        failed_medication = {
            'route': {
                'code': '20053000',
                'displayName': ''  # CTS failed
            }
        }
        
        context = Context({'med': failed_medication})
        rendered = template.render(context).strip()
        
        # Should show just the formatted code, not the problematic pattern
        self.assertEqual(rendered, "20053000")
        self.assertNotIn("(20053000)", rendered)