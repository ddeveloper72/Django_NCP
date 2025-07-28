from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json
from .certificate_validators import CertificateValidator
from django.core.exceptions import ValidationError


@csrf_exempt
@require_http_methods(["POST"])
def parse_certificate_ajax(request):
    """
    AJAX endpoint to parse certificate file and return information
    without saving to database
    """
    try:
        # Check authentication
        if not request.user.is_authenticated or not request.user.is_staff:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Authentication required. Please ensure you are logged in as staff.",
                },
                status=403,
            )

        # Check if file was uploaded
        if "certificate_file" not in request.FILES:
            return JsonResponse(
                {"success": False, "error": "No certificate file provided"}
            )

        certificate_file = request.FILES["certificate_file"]

        # Read file content
        certificate_file.seek(0)
        file_content = certificate_file.read()
        certificate_file.seek(0)

        if not file_content:
            return JsonResponse(
                {"success": False, "error": "Certificate file is empty"}
            )

        # Validate and parse certificate
        try:
            validator = CertificateValidator(file_content)
            result = validator.validate_for_smp_signing()

            return JsonResponse(
                {
                    "success": True,
                    "info": result["info"],
                    "warnings": result["warnings"],
                    "status": "warning" if result["warnings"] else "valid",
                }
            )

        except ValidationError as e:
            return JsonResponse(
                {"success": False, "error": str(e), "status": "invalid"}
            )

    except Exception as e:
        return JsonResponse(
            {
                "success": False,
                "error": f"Error parsing certificate: {str(e)}",
                "status": "invalid",
            }
        )
