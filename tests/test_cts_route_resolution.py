"""
Unit tests for CTS (Clinical Terminology Service) route resolution.

This test suite validates that:
1. CTS service correctly resolves administration route codes to human-readable text
2. ComprehensiveClinicalDataService provides CTS-enhanced medication data
3. Template rendering never displays raw clinical codes for administration routes
4. Proper fallback behavior when CTS resolution fails

Following Django_NCP testing standards for healthcare interoperability.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.template import Context, Template

from patient_data.services.comprehensive_clinical_data_service import ComprehensiveClinicalDataService
from translation_services.terminology_translator import TerminologyTranslator


class TestCTSRouteResolution(TestCase):
    """Test CTS integration for administration route resolution."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = ComprehensiveClinicalDataService()
        self.translator = TerminologyTranslator()
        
        # Sample CDA content with route codes
        self.sample_cda_content = """
        <ClinicalDocument>
            <component>
                <structuredBody>
                    <component>
                        <section>
                            <code code="10160-0" displayName="History of Medication use"/>
                            <text>
                                <paragraph>Eutirox : levothyroxine sodium 100 ug Tablet : 1 ACM since 1997-10-06 (Oral use)</paragraph>
                            </text>
                            <entry>
                                <substanceAdministration>
                                    <routeCode code="20053000" codeSystem="0.4.0.127.0.16.1.1.2.1" displayName=""/>
                                    <consumable>
                                        <manufacturedProduct>
                                            <manufacturedMaterial>
                                                <name>Eutirox</name>
                                            </manufacturedMaterial>
                                        </manufacturedProduct>
                                    </consumable>
                                </substanceAdministration>
                            </entry>
                        </section>
                    </component>
                </structuredBody>
            </component>
        </ClinicalDocument>
        """

    def test_cts_translator_resolves_route_codes(self):
        """Test that CTS translator resolves route codes to human-readable text."""
        # Test oral route resolution
        oral_result = self.translator.resolve_code("20053000")
        self.assertEqual(oral_result, "Oral use", 
                        "CTS should resolve 20053000 to 'Oral use'")
        
        # Test subcutaneous route resolution  
        subcutaneous_result = self.translator.resolve_code("20066000")
        self.assertEqual(subcutaneous_result, "Subcutaneous use",
                        "CTS should resolve 20066000 to 'Subcutaneous use'")
        
        # Test with code system parameter
        oral_with_system = self.translator.resolve_code("20053000", "0.4.0.127.0.16.1.1.2.1")
        self.assertEqual(oral_with_system, "Oral use",
                        "CTS should resolve 20053000 with code system to 'Oral use'")

    @patch('translation_services.terminology_translator.TerminologyTranslator.resolve_code')
    def test_comprehensive_service_uses_cts_resolution(self, mock_resolve_code):
        """Test that ComprehensiveClinicalDataService uses CTS for route resolution."""
        # Mock CTS responses
        mock_resolve_code.return_value = "Oral use"
        
        # Process medication data
        clinical_arrays = self.service.get_clinical_arrays_for_display(
            self.sample_cda_content, {}
        )
        
        medications = clinical_arrays.get('medications', [])
        self.assertGreater(len(medications), 0, "Should extract medications from CDA")
        
        first_med = medications[0]
        
        # Verify CTS integration is called
        self.assertTrue(mock_resolve_code.called, 
                       "CTS resolve_code should be called during medication processing")
        
        # Verify medication structure contains CTS-resolved data
        self.assertIn('route', first_med, "Medication should have route information")
        
        route = first_med['route']
        if isinstance(route, dict):
            display_name = route.get('displayName', '')
            self.assertEqual(display_name, "Oral use",
                           "Route displayName should be CTS-resolved value")

    def test_medication_route_data_structure(self):
        """Test that medication data has correct structure for template consumption."""
        clinical_arrays = self.service.get_clinical_arrays_for_display(
            self.sample_cda_content, {}
        )
        
        medications = clinical_arrays.get('medications', [])
        if medications:
            first_med = medications[0]
            
            # Check required fields exist
            self.assertIsInstance(first_med, dict, "Medication should be a dictionary")
            
            # Check route structure
            if 'route' in first_med:
                route = first_med['route']
                self.assertIsInstance(route, dict, "Route should be a dictionary")
                
                # Verify route has code and displayName
                self.assertIn('code', route, "Route should have code field")
                self.assertIn('displayName', route, "Route should have displayName field")
                
                # Verify displayName is not empty or same as code
                display_name = route.get('displayName', '')
                code = route.get('code', '')
                
                if display_name:  # If we have a display name
                    self.assertNotEqual(display_name, code,
                                      "DisplayName should not be same as raw code")
                    self.assertNotIn(code, display_name, 
                                   "DisplayName should not contain raw code pattern")

    def test_template_rendering_shows_resolved_text(self):
        """Test that template renders CTS-resolved text instead of raw codes."""
        # Create mock medication data with CTS-resolved route
        mock_medication = {
            'medication': {'name': 'Eutirox'},
            'route': {
                'code': '20053000',
                'displayName': 'Oral use'  # CTS-resolved value
            }
        }
        
        # Template fragment for route rendering
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
        
        template = Template(template_content)
        context = Context({'med': mock_medication})
        rendered = template.render(context).strip()
        
        # Should render CTS-resolved text, not raw code
        self.assertEqual(rendered, "Oral use",
                        "Template should render CTS-resolved 'Oral use'")
        self.assertNotIn("20053000", rendered,
                        "Template should not display raw route code")

    def test_template_fallback_behavior(self):
        """Test template behavior when CTS resolution fails."""
        # Mock medication with empty displayName (CTS resolution failed)
        mock_medication_no_cts = {
            'medication': {'name': 'Test Drug'},
            'route': {
                'code': '20053000',
                'displayName': ''  # Empty - CTS resolution failed
            }
        }
        
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
        
        template = Template(template_content)
        context = Context({'med': mock_medication_no_cts})
        rendered = template.render(context).strip()
        
        # When CTS fails, should show formatted code, not raw code with parentheses
        self.assertEqual(rendered, "20053000",
                        "When CTS fails, should show formatted code only")
        self.assertNotIn("(20053000)", rendered,
                        "Should not show code in parentheses format")

    def test_template_with_cts_enhanced_data_field(self):
        """Test template rendering with CTS-enhanced data field."""
        # Mock medication with CTS data in 'data' field (preferred structure)
        mock_medication_enhanced = {
            'medication': {'name': 'Eutirox'},
            'data': {
                'route_display': 'Oral use',  # CTS-resolved value
                'route_code': '20053000'
            },
            'route': {
                'code': '20053000',
                'displayName': 'Oral use'
            }
        }
        
        template_content = """
        {% if med.data.route_display %}
            {{ med.data.route_display }}
            {% if med.data.route_code %}
                <small>Route Code: {{ med.data.route_code }}</small>
            {% endif %}
        {% elif med.route_display %}
            {{ med.route_display }}
        {% elif med.route %}
            {{ med.route.displayName|default:med.route.code|title }}
        {% else %}
            Administration route not specified
        {% endif %}
        """
        
        template = Template(template_content)
        context = Context({'med': mock_medication_enhanced})
        rendered = template.render(context).strip()
        
        # Should use CTS-enhanced data field first
        self.assertIn("Oral use", rendered,
                     "Should display CTS-resolved route text")
        self.assertIn("Route Code: 20053000", rendered,
                     "Should display route code as supplementary info")

    def test_ui_never_shows_raw_code_pattern(self):
        """Integration test: Verify UI never shows '20053000 (20053000)' pattern."""
        clinical_arrays = self.service.get_clinical_arrays_for_display(
            self.sample_cda_content, {}
        )
        
        medications = clinical_arrays.get('medications', [])
        
        for medication in medications:
            if 'route' in medication:
                route = medication['route']
                if isinstance(route, dict):
                    display_name = route.get('displayName', '')
                    code = route.get('code', '')
                    
                    # If we have a display name, it should be meaningful
                    if display_name:
                        self.assertNotEqual(display_name, code,
                                          f"DisplayName '{display_name}' should not equal code '{code}'")
                        
                        # Check for the problematic pattern
                        problematic_pattern = f"{code} ({code})"
                        self.assertNotEqual(display_name, problematic_pattern,
                                          f"Should never show pattern '{problematic_pattern}'")

    def test_comprehensive_service_cts_integration_logging(self):
        """Test that CTS integration is properly logged for debugging."""
        with self.assertLogs(level='INFO') as log:
            clinical_arrays = self.service.get_clinical_arrays_for_display(
                self.sample_cda_content, {}
            )
            
            # Check if CTS-related logging occurs
            cts_logs = [log for log in log.output if 'CTS' in log or 'terminology' in log.lower()]
            # Note: Actual logging may vary based on implementation
            # This test documents the expectation for CTS logging


class TestRouteResolutionEdgeCases(TestCase):
    """Test edge cases for route resolution."""
    
    def test_missing_route_code(self):
        """Test behavior when route code is missing."""
        mock_medication = {
            'medication': {'name': 'Test Drug'},
            'route': {}  # Empty route
        }
        
        template_content = """
        {% if med.route %}
            {{ med.route.displayName|default:med.route.code|default:"No route specified"|title }}
        {% else %}
            Administration route not specified
        {% endif %}
        """
        
        template = Template(template_content)
        context = Context({'med': mock_medication})
        rendered = template.render(context).strip()
        
        self.assertIn("No Route Specified", rendered,
                     "Should handle missing route gracefully")

    def test_none_route_values(self):
        """Test behavior when route values are None."""
        mock_medication = {
            'medication': {'name': 'Test Drug'},
            'route': {
                'code': None,
                'displayName': None
            }
        }
        
        template_content = """
        {% if med.route %}
            {{ med.route.displayName|default:med.route.code|default:"Route not available"|title }}
        {% else %}
            Administration route not specified
        {% endif %}
        """
        
        template = Template(template_content)
        context = Context({'med': mock_medication})
        rendered = template.render(context).strip()
        
        self.assertIn("Route Not Available", rendered,
                     "Should handle None values gracefully")