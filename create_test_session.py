import sys
import os
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session

print('='*80)
print('CREATING TEST SESSION FOR DIANA FERREIRA')
print('='*80)

# Create a new session
session = SessionStore()

# Set up match data for Diana
match_data = {
    'file_path': r'test_data\eu_member_states\PT\2-1234-W7.xml',
    'level': 'L3',
    'cda_type': 'patient_summary',
    'has_l1': False,
    'has_l3': True,
    'patient_id': 'PT-2-1234-W7',
    'country_code': 'PT'
}

# Load CDA content
with open(match_data['file_path'], 'r', encoding='utf-8') as f:
    match_data['cda_content'] = f.read()

# Save to session
session['patient_match_data'] = match_data
session.create()

print(f'\n Session created successfully!')
print(f'   Session Key: {session.session_key}')
print(f'   Patient: Diana Ferreira (Portugal)')
print(f'   Level: {match_data["level"]}')
print(f'   CDA Type: {match_data["cda_type"]}')
print(f'\n Access URL:')
print(f'   http://127.0.0.1:8888/patients/cda/{session.session_key}/{match_data["level"]}/')
print(f'\n This session will now use the UPDATED context_builders.py')
print(f'   The "Primary Performer - Medical Doctor" section should display!')

print('\n' + '='*80)
