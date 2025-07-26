# FHIR Services URLs
from django.urls import path
from django.http import HttpResponse

def fhir_home(request):
    return HttpResponse("FHIR Services - Coming Soon")

urlpatterns = [
    path('', fhir_home, name='fhir_home'),
]
