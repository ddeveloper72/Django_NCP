"""
Unit Tests for Interoperable Healthcare Service
Follows Django NCP Testing and Modular Code Standards
"""

import unittest
from unittest.mock import MagicMock, Mock, patch

from django.contrib.auth.models import User
from django.contrib.sessions.backends.db import SessionStore
from django.http import JsonResponse
from django.test import RequestFactory, TestCase

from patient_data.mixins.healthcare_data_mixin import (
    HealthcareDataMixin,
    HealthcareResponseMixin,
)
from patient_data.views import InteroperableHealthcareView


class HealthcareDataMixinTest(TestCase):
    """Test healthcare data mixin functionality"""

    def setUp(self):
        self.mixin = HealthcareDataMixin()
        self.patient_id = "TEST123"

    @patch("patient_data.mixins.healthcare_data_mixin.InteroperableHealthcareService")
    def test_get_healthcare_service(self, mock_service_class):
        """Test healthcare service instantiation"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        result = self.mixin.get_healthcare_service("en")

        mock_service_class.assert_called_once_with(target_language="en")
        self.assertEqual(result, mock_service)

    @patch("patient_data.mixins.healthcare_data_mixin.InteroperableHealthcareService")
    def test_extract_healthcare_document_success(self, mock_service_class):
        """Test successful document extraction"""
        mock_service = Mock()
        mock_service.extract_complete_healthcare_document.return_value = {
            "document_type": "CDA",
            "patient_id": "TEST123",
        }
        mock_service_class.return_value = mock_service

        result = self.mixin.extract_healthcare_document("TEST123", "cda", "en")

        mock_service.extract_complete_healthcare_document.assert_called_once_with(
            "TEST123", "cda"
        )
        self.assertEqual(result["patient_id"], "TEST123")

    @patch("patient_data.mixins.healthcare_data_mixin.InteroperableHealthcareService")
    def test_extract_healthcare_document_failure(self, mock_service_class):
        """Test document extraction failure"""
        mock_service = Mock()
        mock_service.extract_complete_healthcare_document.return_value = None
        mock_service_class.return_value = mock_service

        result = self.mixin.extract_healthcare_document("TEST123", "cda", "en")

        self.assertIsNone(result)


class HealthcareResponseMixinTest(TestCase):
    """Test healthcare response mixin functionality"""

    def setUp(self):
        self.factory = RequestFactory()
        self.mixin = HealthcareResponseMixin()
        self.document_data = {
            "document_type": "CDA",
            "patient_id": "TEST123",
            "patient_information": {"demographics": {"name": "Test Patient"}},
        }

    def test_render_healthcare_response_html(self):
        """Test HTML response rendering"""
        request = self.factory.get("/healthcare/TEST123/")

        with patch("patient_data.mixins.healthcare_data_mixin.render") as mock_render:
            mock_render.return_value = Mock()

            result = self.mixin.render_healthcare_response(
                request, self.document_data, "TEST123", "cda"
            )

            mock_render.assert_called_once_with(
                request,
                "patient_data/healthcare_document_display.html",
                {
                    "document": self.document_data,
                    "patient_id": "TEST123",
                    "resource_type": "cda",
                },
            )

    def test_render_healthcare_response_json(self):
        """Test JSON response rendering"""
        request = self.factory.get("/healthcare/TEST123/?format=json")

        result = self.mixin.render_healthcare_response(
            request, self.document_data, "TEST123", "cda"
        )

        self.assertIsInstance(result, JsonResponse)

    def test_handle_document_not_found(self):
        """Test document not found error handling"""
        result = self.mixin.handle_document_not_found("TEST123", "cda")

        self.assertIsInstance(result, JsonResponse)
        self.assertEqual(result.status_code, 404)

    def test_handle_service_error(self):
        """Test service error handling"""
        test_error = Exception("Test error")

        result = self.mixin.handle_service_error(test_error)

        self.assertIsInstance(result, JsonResponse)
        self.assertEqual(result.status_code, 500)


class InteroperableHealthcareViewTest(TestCase):
    """Test modular healthcare view"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = InteroperableHealthcareView()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_get_success(self):
        """Test successful GET request"""
        request = self.factory.get("/healthcare/TEST123/")
        request.user = self.user
        request.LANGUAGE_CODE = "en"

        mock_document = {"document_type": "CDA", "patient_id": "TEST123"}

        with patch.object(
            self.view, "extract_healthcare_document"
        ) as mock_extract, patch.object(
            self.view, "render_healthcare_response"
        ) as mock_render:

            mock_extract.return_value = mock_document
            mock_render.return_value = Mock()

            result = self.view.get(request, "TEST123", "cda")

            mock_extract.assert_called_once_with("TEST123", "cda", "en")
            mock_render.assert_called_once_with(
                request, mock_document, "TEST123", "cda"
            )

    def test_get_document_not_found(self):
        """Test GET request when document not found"""
        request = self.factory.get("/healthcare/TEST123/")
        request.user = self.user
        request.LANGUAGE_CODE = "en"

        with patch.object(
            self.view, "extract_healthcare_document"
        ) as mock_extract, patch.object(
            self.view, "handle_document_not_found"
        ) as mock_not_found:

            mock_extract.return_value = None
            mock_not_found.return_value = Mock()

            result = self.view.get(request, "TEST123", "cda")

            mock_not_found.assert_called_once_with("TEST123", "cda")

    def test_get_service_error(self):
        """Test GET request with service error"""
        request = self.factory.get("/healthcare/TEST123/")
        request.user = self.user
        request.LANGUAGE_CODE = "en"

        with patch.object(
            self.view, "extract_healthcare_document"
        ) as mock_extract, patch.object(
            self.view, "handle_service_error"
        ) as mock_error:

            test_error = Exception("Service error")
            mock_extract.side_effect = test_error
            mock_error.return_value = Mock()

            result = self.view.get(request, "TEST123", "cda")

            mock_error.assert_called_once()

    def test_post_not_implemented(self):
        """Test POST request returns not implemented error"""
        request = self.factory.post("/healthcare/TEST123/")
        request.user = self.user

        with patch.object(self.view, "handle_service_error") as mock_error:
            mock_error.return_value = Mock()

            result = self.view.post(request, "TEST123", "cda")

            mock_error.assert_called_once()


class HealthcareViewIntegrationTest(TestCase):
    """Integration tests for healthcare view functionality"""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_view_authentication_required(self):
        """Test that view requires authentication"""
        request = self.factory.get("/healthcare/TEST123/")
        request.user = Mock()
        request.user.is_authenticated = False

        view = InteroperableHealthcareView.as_view()

        # This should redirect to login
        response = view(request, patient_id="TEST123")

        # Check that it's a redirect (302) to login
        self.assertEqual(response.status_code, 302)


if __name__ == "__main__":
    unittest.main()
