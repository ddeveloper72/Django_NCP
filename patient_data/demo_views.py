"""
Views for patient data testing and demonstration
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .patient_loader import patient_loader
from .models import MemberState


@login_required
def patient_demo_view(request):
    """Demo page showing available sample patients"""

    # Get all sample patients
    all_patients = patient_loader.get_all_patients()

    # Get member states with sample data
    member_states_with_data = MemberState.objects.filter(
        sample_data_oid__isnull=False
    ).order_by("country_name")

    context = {
        "all_patients": all_patients,
        "member_states_with_data": member_states_with_data,
    }

    return render(request, "patient_data/patient_demo.html", context)
