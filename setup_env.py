#!/usr/bin/env python3
"""
Setup script for Django NCP Server environment configuration
"""

import os
import secrets
import shutil


def generate_secret_key():
    """Generate a secure Django secret key"""
    return "".join(
        secrets.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)")
        for _ in range(50)
    )


def setup_environment():
    """Setup environment configuration"""

    # Check if .env already exists
    if os.path.exists(".env"):
        print("❌ .env file already exists!")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != "y":
            print("Setup cancelled.")
            return

    # Copy .env.example to .env
    if os.path.exists(".env.example"):
        shutil.copy(".env.example", ".env")
        print("✅ Created .env file from template")
    else:
        print("❌ .env.example template not found!")
        return

    # Generate a new secret key
    secret_key = generate_secret_key()

    # Read and update .env file
    with open(".env", "r", encoding="utf-8") as f:
        content = f.read()

    # Replace placeholder secret key
    content = content.replace(
        "your-secret-key-here-change-this-in-production", secret_key
    )

    # Write updated content
    with open(".env", "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Generated new Django SECRET_KEY")
    print("\n🔧 Next steps:")
    print("1. Review and update the .env file with your specific configuration")
    print("2. Update certificate paths to match your system")
    print("3. Configure database settings if using PostgreSQL/MySQL")
    print("4. Set DEBUG=False and update security settings for production")
    print("\n📁 Important files created:")
    print("   .env - Your environment configuration (DO NOT commit to git)")
    print("   .env.example - Template for other developers")
    print("   .gitignore - Prevents sensitive files from being committed")


if __name__ == "__main__":
    setup_environment()
