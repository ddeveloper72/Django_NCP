"""
Test runner for Playwright E2E tests
Run with: python run_tests.py
"""

import os
import subprocess
import sys


def run_django_server():
    """Start Django development server in background"""
    print("Starting Django development server...")
    return subprocess.Popen(
        [sys.executable, "manage.py", "runserver", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def run_playwright_tests():
    """Run Playwright E2E tests"""
    print("Running Playwright E2E tests...")

    # Run the tests
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/e2e/test_clinical_sections.py",
            "-v",
            "--tb=short",
            "-m",
            "e2e",
        ],
        capture_output=False,
    )

    return result.returncode


def main():
    """Main test runner"""
    print("🎭 Django NCP - Playwright E2E Test Runner")
    print("=" * 50)

    # Change to project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Start Django server
    server_process = None
    try:
        server_process = run_django_server()

        # Wait a moment for server to start
        import time

        time.sleep(3)

        # Run tests
        exit_code = run_playwright_tests()

        if exit_code == 0:
            print("\n✅ All tests passed!")
        else:
            print(f"\n❌ Tests failed with exit code {exit_code}")

        return exit_code

    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        return 1
    finally:
        # Clean up server
        if server_process:
            print("\nStopping Django server...")
            server_process.terminate()
            server_process.wait()


if __name__ == "__main__":
    sys.exit(main())
