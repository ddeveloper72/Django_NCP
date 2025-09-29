"""
Healthcare Data Mixins for Modular Architecture
Follows Django NCP Testing and Modular Code Standards
"""

from typing import Any, Dict, Optional

from django.http import JsonResponse
from django.shortcuts import render


class HealthcareDataMixin:
    """
    Mixin providing healthcare data extraction functionality.
    Follows Single Responsibility Principle for data extraction.
    """

    def get_healthcare_service(self, language: str = "en"):
        """Get configured healthcare data service"""
        from ..services.interoperable_healthcare_service import (
            InteroperableHealthcareService,
        )

        return InteroperableHealthcareService(target_language=language)

    def extract_healthcare_document(
        self, patient_id: str, resource_type: str = "cda", language: str = "en"
    ) -> Optional[Dict[str, Any]]:
        """
        Extract healthcare document using service layer.

        Args:
            patient_id: Patient identifier
            resource_type: 'cda' or 'fhir'
            language: Target language

        Returns:
            Structured healthcare document or None
        """
        service = self.get_healthcare_service(language)
        return service.extract_complete_healthcare_document(patient_id, resource_type)


class HealthcareResponseMixin:
    """
    Mixin for handling healthcare document HTTP responses.
    Separates response logic from data extraction.
    """

    def render_healthcare_response(
        self,
        request,
        document_data: Dict[str, Any],
        patient_id: str,
        resource_type: str = "cda",
    ):
        """
        Render healthcare document response in requested format.

        Args:
            request: HTTP request object
            document_data: Structured healthcare document
            patient_id: Patient identifier
            resource_type: Resource type (cda/fhir)

        Returns:
            HttpResponse (HTML or JSON)
        """
        format_type = request.GET.get("format", "html")

        if format_type == "json":
            return JsonResponse(document_data, safe=False)

        return render(
            request,
            "patient_data/healthcare_document_display.html",
            {
                "document": document_data,
                "patient_id": patient_id,
                "resource_type": resource_type,
            },
        )

    def handle_document_not_found(self, patient_id: str, resource_type: str):
        """Handle case when healthcare document is not found"""
        return JsonResponse(
            {
                "error": f"No {resource_type.upper()} document found for patient {patient_id}",
                "patient_id": patient_id,
                "resource_type": resource_type,
            },
            status=404,
        )

    def handle_service_error(self, error: Exception):
        """Handle service layer errors"""
        return JsonResponse(
            {"error": "Healthcare service error", "message": str(error)}, status=500
        )
