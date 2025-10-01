"""
Playwright configuration for Django NCP project
"""

import pytest
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from playwright.sync_api import BrowserType, Playwright


class PlaywrightTestCase(StaticLiveServerTestCase):
    """Base test case for Playwright tests with Django integration"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.playwright = None
        cls.browser = None
        cls.context = None

    @classmethod
    def tearDownClass(cls):
        if cls.context:
            cls.context.close()
        if cls.browser:
            cls.browser.close()
        if cls.playwright:
            cls.playwright.stop()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        if not self.playwright:
            from playwright.sync_api import sync_playwright

            self.__class__.playwright = sync_playwright().start()
            self.__class__.browser = self.playwright.chromium.launch(
                headless=False,  # Set to True for headless mode
                slow_mo=500,  # Slow down by 500ms for debugging
            )
            self.__class__.context = self.browser.new_context(
                viewport={"width": 1920, "height": 1080}
            )

        self.page = self.context.new_page()

    def tearDown(self):
        if hasattr(self, "page"):
            self.page.close()
        super().tearDown()


@pytest.fixture(scope="session")
def playwright_config():
    """Playwright configuration for pytest-playwright"""
    return {
        "browser_name": "chromium",
        "headless": False,
        "slow_mo": 500,
        "viewport": {"width": 1920, "height": 1080},
    }
