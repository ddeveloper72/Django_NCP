"""
Clear Django cache
"""
import os
import sys
import django

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.core.cache import cache

print("Clearing Django cache...")
cache.clear()
print("✅ Cache cleared successfully!")
