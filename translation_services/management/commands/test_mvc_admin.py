"""
Quick test command to import MVC data via admin interface
"""

from django.core.management.base import BaseCommand
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.admin.sites import site


class Command(BaseCommand):
    help = "Test MVC import functionality and show admin URLs"

    def handle(self, *args, **options):
        self.stdout.write("MVC Import Test")
        self.stdout.write("=" * 50)

        # Show available admin URLs
        try:
            import_url = reverse(
                "admin:translation_services_valuesetcatalogue_import_mvc"
            )
            sync_url = reverse("admin:translation_services_valuesetcatalogue_sync_cts")

            self.stdout.write(f"✅ Import MVC URL: {import_url}")
            self.stdout.write(f"✅ Sync CTS URL: {sync_url}")

        except Exception as e:
            self.stdout.write(f"❌ URL reverse error: {e}")

        # Check if admin is properly registered
        from translation_services.models import ValueSetCatalogue

        if ValueSetCatalogue in site._registry:
            admin_class = site._registry[ValueSetCatalogue]
            self.stdout.write(f"✅ ValueSetCatalogue admin registered: {admin_class}")

            # Check if custom URLs are available
            if hasattr(admin_class, "get_urls"):
                custom_urls = admin_class.get_urls()
                self.stdout.write(f"✅ Custom URLs count: {len(custom_urls)}")

        else:
            self.stdout.write("❌ ValueSetCatalogue admin not registered")

        # Show current admin URL structure
        self.stdout.write("\nTo access MVC import:")
        self.stdout.write(
            "1. Go to: http://127.0.0.1:8000/admin/translation_services/valuesetcatalogue/"
        )
        self.stdout.write("2. Look for 'Import MVC File' button in top-right corner")
        self.stdout.write(
            "3. Or try direct URL: http://127.0.0.1:8000/admin/translation_services/valuesetcatalogue/import-mvc/"
        )
