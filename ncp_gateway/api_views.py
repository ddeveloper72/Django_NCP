# Django NCP API Views for Java Portal Integration
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
import logging

logger = logging.getLogger('ehealth')
audit_logger = logging.getLogger('audit')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_countries(request):
    """
    API endpoint for Java portal to get available countries for patient lookup
    """
    countries = [
        {
            'code': 'BE',
            'name': 'Belgium',
            'flag_url': '/static/flags/be.png',
            'ncp_endpoint': 'https://be-ncp.ehealth.be',
            'available_services': ['PS', 'eP', 'eD']
        },
        {
            'code': 'AT', 
            'name': 'Austria',
            'flag_url': '/static/flags/at.png',
            'ncp_endpoint': 'https://at-ncp.ehealth.at',
            'available_services': ['PS', 'LAB']
        },
        {
            'code': 'HU',
            'name': 'Hungary', 
            'flag_url': '/static/flags/hu.png',
            'ncp_endpoint': 'https://hu-ncp.ehealth.hu',
            'available_services': ['PS', 'HD']
        },
        {
            'code': 'IE',
            'name': 'Ireland',
            'flag_url': '/static/flags/ie.png', 
            'ncp_endpoint': 'http://localhost:8000',
            'available_services': ['PS', 'eP', 'eD', 'LAB', 'HD', 'MI']
        }
    ]
    
    audit_logger.info(f"Country list requested by user: {request.user.username}")
    return Response({'countries': countries})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def patient_lookup(request):
    """
    API endpoint for cross-border patient lookup from Java portal
    """
    data = request.data
    country_code = data.get('country_code')
    patient_id = data.get('patient_id')
    id_type = data.get('id_type', 'national_id')
    
    # Audit log the patient lookup attempt
    audit_logger.info(
        f"Patient lookup attempted: country={country_code}, "
        f"patient_id={patient_id}, user={request.user.username}"
    )
    
    # Mock patient data - replace with actual NCP lookup
    if patient_id:
        patient_data = {
            'patient_id': patient_id,
            'country_code': country_code,
            'name': 'John Doe',
            'birth_date': '1980-01-01',
            'gender': 'M',
            'available_documents': [
                {
                    'type': 'PS',
                    'title': 'Patient Summary',
                    'date': '2024-12-01',
                    'format': 'CDA',
                    'endpoint': f'/api/fhir/patient/{patient_id}/summary'
                },
                {
                    'type': 'eP',
                    'title': 'ePrescription',
                    'date': '2024-11-15', 
                    'format': 'FHIR',
                    'endpoint': f'/api/fhir/patient/{patient_id}/prescriptions'
                }
            ]
        }
        
        return Response({
            'success': True,
            'patient': patient_data
        })
    else:
        return Response({
            'success': False,
            'error': 'Patient ID required'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_patient_document(request, patient_id, document_type):
    """
    API endpoint to retrieve specific patient document (CDA or FHIR)
    """
    # Audit log document access
    audit_logger.info(
        f"Document access: patient={patient_id}, type={document_type}, "
        f"user={request.user.username}"
    )
    
    # Mock document data - replace with actual document retrieval
    if document_type == 'PS':
        # Return CDA Patient Summary
        document = {
            'format': 'CDA',
            'content_type': 'application/xml',
            'document': '''<?xml version="1.0" encoding="UTF-8"?>
            <ClinicalDocument xmlns="urn:hl7-org:v3">
                <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
                <templateId root="1.3.6.1.4.1.12559.11.10.1.3.1.1.3"/>
                <id extension="{}" root="1.3.6.1.4.1.12559.11.10.1.3.1.1.3"/>
                <title>Patient Summary</title>
                <!-- CDA content here -->
            </ClinicalDocument>'''.format(patient_id)
        }
    elif document_type == 'eP':
        # Return FHIR Bundle
        document = {
            'format': 'FHIR',
            'content_type': 'application/fhir+json',
            'document': {
                'resourceType': 'Bundle',
                'type': 'document',
                'entry': [
                    {
                        'resource': {
                            'resourceType': 'MedicationRequest',
                            'id': f'{patient_id}-prescription-1',
                            'status': 'active',
                            'medicationCodeableConcept': {
                                'text': 'Aspirin 100mg'
                            }
                        }
                    }
                ]
            }
        }
    else:
        return Response({
            'error': 'Document type not supported'
        }, status=status.HTTP_404_NOT_FOUND)
    
    return Response({
        'success': True,
        'document': document
    })
