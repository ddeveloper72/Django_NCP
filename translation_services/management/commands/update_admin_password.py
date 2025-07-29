from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import os


class Command(BaseCommand):
    help = "Update admin user password from environment variable"

    def handle(self, *args, **options):
        username = os.getenv("ADMIN_USERNAME", "admin")
        new_password = os.getenv("ADMIN_PASSWORD")

        if not new_password:
            self.stdout.write(
                self.style.ERROR(
                    "ADMIN_PASSWORD environment variable not set. Please set it in your .env file."
                )
            )
            return

        try:
            user = User.objects.get(username=username)
            user.set_password(new_password)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated password for user "{username}"'
                )
            )
        except User.DoesNotExist:
            # Create new admin user with correct password
            email = os.getenv("ADMIN_EMAIL", "admin@localhost")
            user = User.objects.create_superuser(username, email, new_password)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superuser "{username}"')
            )

        self.stdout.write(f"Admin URL: http://127.0.0.1:8000/admin/")
        self.stdout.write(f"Username: {username}")
        self.stdout.write(
            self.style.WARNING(
                "Password is set from ADMIN_PASSWORD environment variable"
            )
        )
        self.stdout.write(
            f"MVC Admin: http://127.0.0.1:8000/admin/translation_services/valuesetcatalogue/"
        )
