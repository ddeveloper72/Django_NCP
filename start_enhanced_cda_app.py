#!/usr/bin/env python3
"""
Enhanced CDA Processor Django App Startup Script
Quick way to start the application with Enhanced CDA Processing
"""

import os
import sys
import subprocess
import threading
import time
import webbrowser


def main():
    print("🚀 Starting Enhanced CDA Processor Django Application")
    print("=" * 60)

    print("📋 Application Features:")
    print("✅ Enhanced CDA Processing with multi-language support")
    print("✅ Clinical data extraction and rendering")
    print("✅ PS-compliant table generation")
    print("✅ Real-time language switching")
    print("✅ Portuguese Wave 7 eHDSI test data support")

    print(f"\n🌐 Application will be available at:")
    print(f"   Main Portal: http://localhost:8000/portal/")
    print(
        f"   CDA Viewer: http://localhost:8000/portal/country/PT/patient/12345/document/PS/"
    )
    print(
        f"   With German: http://localhost:8000/portal/country/PT/patient/12345/document/PS/?lang=de"
    )

    print(f"\n🔧 Starting Django development server...")

    try:
        # Start Django server
        result = subprocess.run(
            [sys.executable, "manage.py", "runserver", "8000"], check=False
        )

    except KeyboardInterrupt:
        print(f"\n⏹️  Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server startup error: {e}")


if __name__ == "__main__":
    main()
