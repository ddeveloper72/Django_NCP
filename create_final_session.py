import sys
import os
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.contrib.sessions.backends.db import SessionStore

print('='*80)
print('CREATING FRESH SESSION FOR DIANA FERREIRA')
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

# Set the data
session['patient_match_data'] = match_data

# Create the session (this generates the session_key)
session.create()

# Now get the session key
session_key = session.session_key

# Add the properly formatted key
session[f'patient_match_{session_key}'] = match_data
session.save()

print(f'\n FRESH SESSION CREATED!')
print(f'   Session Key: {session_key}')
print(f'   Patient: Diana Ferreira (Portugal)')
print(f'   Level: {match_data["level"]}')
print(f'\n NAVIGATE TO THIS URL:')
print(f'\n   http://127.0.0.1:8888/patients/cda/{session_key}/L3/')
print(f'\n With the finalize_context fix, you should now see:')
print(f'    Diana Ferreira patient name')
print(f'    Healthcare Team & Contacts tab')
print(f'    Primary Performer - Medical Doctor section')
print(f'    Dr. António Pereira with full contact details')

print('\n' + '='*80)
