from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import os


class Command(BaseCommand):
    help = "Create a test admin user using environment variables"

    def handle(self, *args, **options):
        username = os.getenv("ADMIN_USERNAME", "admin")
        password = os.getenv("ADMIN_PASSWORD")
        email = os.getenv("ADMIN_EMAIL", "admin@localhost")

        if not password:
            self.stdout.write(
                self.style.ERROR(
                    "ADMIN_PASSWORD environment variable not set. Please set it in your .env file."
                )
            )
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'User "{username}" already exists'))
            user = User.objects.get(username=username)
        else:
            user = User.objects.create_superuser(username, email, password)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superuser "{username}"')
            )

        self.stdout.write(f"Admin URL: http://127.0.0.1:8000/admin/")
        self.stdout.write(f"Username: {username}")
        self.stdout.write(f"Email: {email}")
        self.stdout.write(
            self.style.WARNING(
                "Password is set from ADMIN_PASSWORD environment variable"
            )
        )
        self.stdout.write(
            f"MVC Admin: http://127.0.0.1:8000/admin/translation_services/valuesetcatalogue/"
        )
