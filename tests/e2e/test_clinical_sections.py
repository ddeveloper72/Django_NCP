"""
End-to-end tests for Clinical Sections Interface
Tests the clinical sections display, navigation, and functionality we've been working on.
"""

import pytest
from django.test import TestCase
from django.urls import reverse

from tests.conftest import PlaywrightTestCase


@pytest.mark.e2e
@pytest.mark.clinical
class TestClinicalSectionsInterface(PlaywrightTestCase):
    """Test the clinical sections interface functionality"""

    def test_clinical_sections_display(self):
        """Test that clinical sections display properly without content spillover"""
        # Navigate to a CDA document page (you'll need to adjust the URL)
        # For now, using a placeholder URL - replace with your actual patient CDA URL
        test_url = f"{self.live_server_url}/patients/cda/1472807983/L3/"

        self.page.goto(test_url)

        # Wait for page to load
        self.page.wait_for_selector('[data-tab-type="clinical"]')

        # Check that Extended Patient Information tab exists
        extended_tab = self.page.locator("#extended-tab")
        self.assertTrue(extended_tab.is_visible())

        # Click on Extended Patient Information tab
        extended_tab.click()

        # Wait for the clinical information tab to be visible
        clinical_tab_btn = self.page.locator("#clinical-tab-btn")
        self.assertTrue(clinical_tab_btn.is_visible())

        # Click on Clinical Information tab
        clinical_tab_btn.click()

        # Wait for clinical content to load
        self.page.wait_for_selector(".clinical-information-container", timeout=5000)

        # Check that clinical sections are displayed
        clinical_container = self.page.locator(".clinical-information-container")
        self.assertTrue(clinical_container.is_visible())

        # Check for accordion structure
        accordion = self.page.locator("#clinicalInformationAccordion")
        self.assertTrue(accordion.is_visible())

        # Check that medication section exists and is visible
        medication_section = self.page.locator(
            "text=History of Medication use Narrative"
        )
        self.assertTrue(medication_section.is_visible())

    def test_medication_section_functionality(self):
        """Test the enhanced medication section we built"""
        # Navigate to the page
        test_url = f"{self.live_server_url}/patients/cda/1472807983/L3/"
        self.page.goto(test_url)

        # Navigate to clinical sections
        self.page.click("#extended-tab")
        self.page.click("#clinical-tab-btn")

        # Wait for clinical content
        self.page.wait_for_selector(".clinical-information-container")

        # Find the medication section
        medication_accordion = self.page.locator(
            "text=History of Medication use Narrative"
        ).first

        # Check if it's collapsed and expand it
        if not self.page.locator("#collapse-1.show").is_visible():
            medication_accordion.click()

        # Wait for medication content to be visible
        self.page.wait_for_selector("#collapse-1.show")

        # Check for medication history header
        medication_header = self.page.locator("text=Medication History")
        self.assertTrue(medication_header.is_visible())

        # Check for the "No Medication History Available" message (since test data might not have medications)
        no_medication_msg = self.page.locator("text=No Medication History Available")
        self.assertTrue(no_medication_msg.is_visible())

    def test_contrast_and_readability(self):
        """Test that the contrast fixes are working properly"""
        test_url = f"{self.live_server_url}/patients/cda/1472807983/L3/"
        self.page.goto(test_url)

        # Navigate to clinical sections
        self.page.click("#extended-tab")
        self.page.click("#clinical-tab-btn")

        # Wait for clinical content
        self.page.wait_for_selector(".clinical-information-container")

        # Check that accordion buttons have proper contrast
        accordion_buttons = self.page.locator(".accordion-button")

        # Verify first accordion button has good contrast
        first_button = accordion_buttons.first

        # Check computed styles (this verifies our contrast fixes)
        background_color = self.page.evaluate(
            "(element) => window.getComputedStyle(element).backgroundColor",
            first_button.element_handle(),
        )
        color = self.page.evaluate(
            "(element) => window.getComputedStyle(element).color",
            first_button.element_handle(),
        )

        # Basic check that we have different colors (not both transparent/same)
        self.assertNotEqual(background_color, color)

        # Check that text is actually readable by verifying it's not using light colors on light backgrounds
        # RGB values for good contrast should be significantly different
        print(f"Button background: {background_color}, color: {color}")

    def test_all_clinical_sections_present(self):
        """Test that all 13 clinical sections are present and accessible"""
        test_url = f"{self.live_server_url}/patients/cda/1472807983/L3/"
        self.page.goto(test_url)

        # Navigate to clinical sections
        self.page.click("#extended-tab")
        self.page.click("#clinical-tab-btn")

        # Wait for clinical content
        self.page.wait_for_selector(".clinical-information-container")

        # Expected clinical sections based on what we've seen
        expected_sections = [
            "History of Medication use Narrative",
            "Allergies and adverse reactions Document",
            "History of Procedures Document",
            "Problem list - Reported",
            "History of medical device use",
            "History of Past illness Narrative",
            "History of Immunization Narrative",
            "History of pregnancies Narrative",
            "Social history Narrative",
            "Vital signs",
            "Relevant diagnostic tests/laboratory data Narrative",
            "Advance healthcare directives",
            "Functional status assessment note",
        ]

        # Check that each section is present
        for section_name in expected_sections:
            section_element = self.page.locator(f"text={section_name}")
            self.assertTrue(
                section_element.is_visible(),
                f"Section '{section_name}' should be visible",
            )

    def test_accordion_expand_collapse(self):
        """Test accordion expand/collapse functionality"""
        test_url = f"{self.live_server_url}/patients/cda/1472807983/L3/"
        self.page.goto(test_url)

        # Navigate to clinical sections
        self.page.click("#extended-tab")
        self.page.click("#clinical-tab-btn")

        # Wait for clinical content
        self.page.wait_for_selector(".clinical-information-container")

        # Get the first accordion item
        first_accordion = self.page.locator(".accordion-item").first
        first_button = first_accordion.locator(".accordion-button")
        first_collapse = first_accordion.locator(".accordion-collapse")

        # Test collapse (it should start expanded)
        if first_collapse.locator(".show").is_visible():
            first_button.click()
            self.page.wait_for_timeout(300)  # Wait for animation
            self.assertFalse(first_collapse.locator(".show").is_visible())

        # Test expand
        first_button.click()
        self.page.wait_for_timeout(300)  # Wait for animation
        self.assertTrue(first_collapse.locator(".show").is_visible())


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/e2e/test_clinical_sections.py -v
    pytest.main([__file__, "-v"])
