#!/usr/bin/env python
"""
Django Startup Script with Patient Session Cleanup

This script can be used to start the Django server with automatic patient session cleanup.
It runs the startup cleanup command before starting the server.

Usage:
    python startup_with_cleanup.py [--port PORT] [--host HOST] [--cleanup-options]

Examples:
    python startup_with_cleanup.py
    python startup_with_cleanup.py --port 8080
    python startup_with_cleanup.py --all-sessions --force
"""

import os
import sys
import subprocess
import argparse
import logging

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")

import django

django.setup()

from django.core.management import execute_from_command_line
from django.conf import settings

logger = logging.getLogger(__name__)


def run_startup_cleanup(cleanup_options=None):
    """Run the startup patient session cleanup command"""
    print("🔧 Running startup patient session cleanup...")

    cleanup_cmd = ["python", "manage.py", "startup_cleanup_patient_sessions"]

    # Add cleanup options if provided
    if cleanup_options:
        cleanup_cmd.extend(cleanup_options)
    else:
        # Default cleanup options
        cleanup_cmd.extend(["--older-than-hours", "24", "--force"])

    try:
        result = subprocess.run(cleanup_cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Startup cleanup completed successfully")
            if result.stdout:
                print(result.stdout)
        else:
            print("⚠️  Startup cleanup completed with warnings")
            if result.stderr:
                print(f"Warnings: {result.stderr}")
            if result.stdout:
                print(result.stdout)

    except Exception as e:
        print(f"❌ Startup cleanup failed: {e}")
        print("Continuing with server startup...")


def start_development_server(host="127.0.0.1", port=8000):
    """Start the Django development server"""
    print(f"🚀 Starting Django development server on {host}:{port}")
    print("🔒 Patient session security is active")
    print("📋 Available cleanup endpoints:")
    print("   - /api/clear-patient-session/ (manual cleanup)")
    print("   - /api/emergency-session-cleanup/ (emergency cleanup)")
    print("⌨️  Keyboard shortcuts in patient pages:")
    print("   - Ctrl+Shift+C: Clear patient data")
    print("   - Ctrl+Shift+E: Emergency cleanup")
    print("-" * 60)

    # Start the server
    execute_from_command_line(["manage.py", "runserver", f"{host}:{port}"])


def main():
    parser = argparse.ArgumentParser(
        description="Start Django server with patient session cleanup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Cleanup Options:
  --all-sessions      Clean patient data from ALL sessions (including authenticated)
  --older-than-hours  Only clean sessions older than specified hours (default: 24)
  --dry-run          Show what would be cleaned without making changes
  --force            Skip confirmation prompts

Examples:
  python startup_with_cleanup.py
  python startup_with_cleanup.py --port 8080 --host 0.0.0.0
  python startup_with_cleanup.py --all-sessions --force
  python startup_with_cleanup.py --dry-run --older-than-hours 12
        """,
    )

    # Server options
    parser.add_argument(
        "--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Server port (default: 8000)"
    )
    parser.add_argument(
        "--skip-cleanup", action="store_true", help="Skip startup cleanup"
    )

    # Cleanup options
    parser.add_argument(
        "--all-sessions",
        action="store_true",
        help="Clean patient data from ALL sessions",
    )
    parser.add_argument(
        "--older-than-hours",
        type=int,
        default=24,
        help="Only clean sessions older than specified hours",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be cleaned without making changes",
    )
    parser.add_argument(
        "--force", action="store_true", help="Skip confirmation prompts"
    )

    args = parser.parse_args()

    # Prepare cleanup options
    cleanup_options = []
    if args.all_sessions:
        cleanup_options.append("--all-sessions")
    if args.older_than_hours != 24:
        cleanup_options.extend(["--older-than-hours", str(args.older_than_hours)])
    if args.dry_run:
        cleanup_options.append("--dry-run")
    if args.force:
        cleanup_options.append("--force")

    # Run startup cleanup unless skipped
    if not args.skip_cleanup:
        run_startup_cleanup(cleanup_options)
    else:
        print("⏭️  Skipping startup cleanup")

    # Start the development server
    start_development_server(args.host, args.port)


if __name__ == "__main__":
    main()
