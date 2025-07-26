# SMP Client URLs  
from django.urls import path
from django.http import HttpResponse

def smp_home(request):
    return HttpResponse("SMP Client Integration - Coming Soon")

urlpatterns = [
    path('', smp_home, name='smp_home'),
]
