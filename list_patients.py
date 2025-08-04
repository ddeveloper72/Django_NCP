#!/usr/bin/env python
"""List patients in database"""

import os
import sys
import django

# Set up Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from patient_data.models import PatientData

patients = PatientData.objects.all()
print(f'Total patients: {patients.count()}')

for p in patients[:10]:
    print(f'ID: {p.id}, Name: {p.given_name} {p.family_name}')
