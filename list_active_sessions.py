import sys
import os
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.contrib.sessions.models import Session
from django.utils import timezone
import json

print('='*80)
print('ACTIVE SESSIONS WITH PATIENT DATA')
print('='*80)

active_sessions = Session.objects.filter(expire_date__gt=timezone.now())

for session in active_sessions:
    data = session.get_decoded()
    
    if 'patient_match_data' in data:
        match_data = data['patient_match_data']
        
        if isinstance(match_data, dict):
            file_path = match_data.get('file_path', 'Unknown')
            level = match_data.get('level', 'Unknown')
            cda_type = match_data.get('cda_type', 'Unknown')
            
            print(f'\n Session: {session.session_key}')
            print(f'   Level: {level}')
            print(f'   Type: {cda_type}')
            print(f'   File: {file_path}')
            print(f'   URL: http://127.0.0.1:8888/patients/cda/{session.session_key}/{level}/')

print('\n' + '='*80)
