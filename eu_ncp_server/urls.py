"""
URL configuration for eu_ncp_server project.

EU eHealth NCP Server - Django implementation
Provides both API endpoints for Java portal integration and Django frontend
"""

from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def home_view(request):
    return HttpResponse("""
    <h1>Django EU eHealth NCP Server</h1>
    <p>Choose your integration approach:</p>
    <ul>
        <li><a href="/portal/">Django Portal UI</a> - Replicated OpenNCP Portal interface</li>
        <li><a href="/admin/">Django Admin</a> - Administrative interface</li>
        <li><a href="/api/countries/">API Endpoints</a> - For Java portal integration</li>
    </ul>
    <p>Java OpenNCP Portal: <a href="http://localhost:8093" target="_blank">localhost:8093</a></p>
    <p>DomiSMP: <a href="http://localhost:8290/smp" target="_blank">localhost:8290/smp</a></p>
    """)

urlpatterns = [
    path("", home_view, name='home'),
    path("admin/", admin.site.urls),
    
    # Option 1: API endpoints for Java portal integration
    path("api/", include('ncp_gateway.urls')),
    
    # Option 2: Django frontend portal (replicating Java portal)
    path("portal/", include('ehealth_portal.urls')),
    
    # FHIR services
    path("fhir/", include('fhir_services.urls')),
    
    # SMP client integration
    path("smp/", include('smp_client.urls')),
]
