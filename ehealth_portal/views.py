# Django Frontend Views - Replicating OpenNCP Portal UI
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
import logging

logger = logging.getLogger('ehealth')

def country_selection(request):
    """
    Main country selection page - equivalent to Java portal
    """
    countries = [
        {
            'code': 'BE',
            'name': 'Belgium',
            'flag_image': 'flags/belgium.png',
            'available': True
        },
        {
            'code': 'AT',
            'name': 'Austria', 
            'flag_image': 'flags/austria.png',
            'available': True
        },
        {
            'code': 'HU',
            'name': 'Hungary',
            'flag_image': 'flags/hungary.png', 
            'available': True
        },
        {
            'code': 'EU',
            'name': 'European Commission',
            'flag_image': 'flags/eu.png',
            'available': True
        },
        {
            'code': 'IE',
            'name': 'Ireland',
            'flag_image': 'flags/ireland.png',
            'available': True
        }
    ]
    
    context = {
        'countries': countries,
        'page_title': 'eHealth OpenNCP Portal',
        'step': 'CHOOSE COUNTRY'
    }
    
    return render(request, 'ehealth_portal/country_selection.html', context)

@login_required
def patient_search(request, country_code):
    """
    Patient search page for selected country
    """
    if request.method == 'POST':
        patient_id = request.POST.get('patient_id')
        search_type = request.POST.get('search_type', 'national_id')
        
        # Redirect to patient data view
        return redirect('patient_data', country_code=country_code, patient_id=patient_id)
    
    context = {
        'country_code': country_code,
        'page_title': f'Patient Search - {country_code}',
        'step': 'PATIENT SEARCH'
    }
    
    return render(request, 'ehealth_portal/patient_search.html', context)

@login_required  
def patient_data(request, country_code, patient_id):
    """
    Display patient data and available documents
    """
    # Mock patient data - replace with actual NCP calls
    patient = {
        'id': patient_id,
        'name': 'John Doe',
        'birth_date': '1980-01-01',
        'country': country_code,
        'documents': [
            {
                'type': 'PS',
                'title': 'Patient Summary',
                'date': '2024-12-01',
                'available': True
            },
            {
                'type': 'eP', 
                'title': 'ePrescription',
                'date': '2024-11-15',
                'available': True
            },
            {
                'type': 'LAB',
                'title': 'Laboratory Results', 
                'date': '2024-10-20',
                'available': False
            }
        ]
    }
    
    context = {
        'patient': patient,
        'country_code': country_code,
        'page_title': f'Patient Data - {patient_id}',
        'step': 'PATIENT DATA'
    }
    
    return render(request, 'ehealth_portal/patient_data.html', context)

@login_required
def document_viewer(request, country_code, patient_id, document_type):
    """
    View specific document (CDA or FHIR)
    """
    # Mock document retrieval
    document_data = {
        'type': document_type,
        'patient_id': patient_id,
        'format': 'CDA' if document_type == 'PS' else 'FHIR',
        'content': 'Document content would be displayed here...'
    }
    
    context = {
        'document': document_data,
        'patient_id': patient_id,
        'country_code': country_code,
        'page_title': f'Document Viewer - {document_type}'
    }
    
    return render(request, 'ehealth_portal/document_viewer.html', context)
