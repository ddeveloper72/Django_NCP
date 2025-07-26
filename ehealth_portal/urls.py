# Frontend URLs for Django Portal UI
from django.urls import path
from . import views

urlpatterns = [
    # Django frontend portal (replicating Java portal UI)
    path('', views.country_selection, name='country_selection'),
    path('country/<str:country_code>/search/', views.patient_search, name='patient_search'),
    path('country/<str:country_code>/patient/<str:patient_id>/', views.patient_data, name='patient_data'),
    path('country/<str:country_code>/patient/<str:patient_id>/document/<str:document_type>/', 
         views.document_viewer, name='document_viewer'),
]
