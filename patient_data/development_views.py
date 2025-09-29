"""
Development session management views
"""

from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render

from .session_management import DevelopmentSessionManager


def session_manager_view(request):
    """Web interface for session management during development"""
    if not settings.DEBUG:
        return JsonResponse(
            {"error": "Session manager only available in DEBUG mode"}, status=403
        )

    context = {
        "sessions": DevelopmentSessionManager.list_available_sessions(),
        "debug": True,
    }

    if request.method == "POST":
        action = request.POST.get("action")
        patient_id = request.POST.get("patient_id")
        session_key = request.POST.get("session_key")

        try:
            if action == "create" and patient_id:
                new_session_key = (
                    DevelopmentSessionManager.create_test_session_with_patient_data(
                        patient_id
                    )
                )
                messages.success(
                    request,
                    f"Created session {new_session_key} for patient {patient_id}",
                )
                return redirect("patient_data:session_manager")

            elif action == "delete" and session_key:
                from django.contrib.sessions.models import Session

                Session.objects.filter(session_key=session_key).delete()
                messages.success(request, f"Deleted session {session_key}")
                return redirect("patient_data:session_manager")

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect("patient_data:session_manager")

    return render(request, "patient_data/session_manager.html", context)
