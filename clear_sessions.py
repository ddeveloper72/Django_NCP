"""
Quick Session Clear Script - Safe Option
Clears only Django sessions without affecting other database data
"""
import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.contrib.sessions.models import Session

def clear_sessions():
    """Clear all Django sessions"""
    try:
        session_count = Session.objects.count()
        print(f"Found {session_count} active sessions in database")
        
        if session_count == 0:
            print("✅ No sessions to clear")
            return
        
        # Delete all sessions
        Session.objects.all().delete()
        print(f"✅ Successfully cleared {session_count} sessions")
        print("\nNext steps:")
        print("1. Restart Django server (if running)")
        print("2. Navigate to Diana Ferreira patient view")
        print("3. Fresh data will be parsed with formatted dates")
        
    except Exception as e:
        print(f"❌ Error clearing sessions: {e}")
        print("\nAlternative: Delete db.sqlite3 and run 'python manage.py migrate'")

if __name__ == "__main__":
    print("Django Session Clearer")
    print("=" * 80)
    clear_sessions()
