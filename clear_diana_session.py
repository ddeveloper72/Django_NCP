"""Clear Diana's session to force fresh template rendering"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.sessions.models import Session

# Diana's session
session_key = 'j7wk7qq1xst8x0zrr5yi70wmnzk22grg'

try:
    session = Session.objects.get(session_key=session_key)
    session.delete()
    print(f"✅ Deleted session: {session_key}")
    print(f"💡 You can now create a fresh Diana session with updated templates")
except Session.DoesNotExist:
    print(f"❌ Session {session_key} not found - may already be deleted")
except Exception as e:
    print(f"❌ Error: {e}")
