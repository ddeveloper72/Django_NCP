"""
Patient Data URL Configuration

URL patterns for patient search, data retrieval, and document request functionality.
"""

from django.urls import path
from . import views, demo_views

app_name = "patient_data"

urlpatterns = [
    # Patient search interface
    path("search/", views.patient_search_view, name="patient_search"),
    path(
        "search/results/",
        views.patient_search_results,
        name="patient_search_results",
    ),
    # Patient data display (if function exists)
    # path("patient/<str:patient_id>/", views.patient_data_view, name="patient_data"),
    # Demo and testing (comment out until views exist)
    # path("demo/", demo_views.patient_demo_view, name="patient_demo"),
    # path("demo/sample-data/", demo_views.sample_data_view, name="sample_data"),
]
