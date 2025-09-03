"""
Django management command to setup EADC user groups and permissions
"""

import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission, User
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist


class Command(BaseCommand):
    """
    Management command to setup EADC groups and permissions
    Usage: python manage.py setup_eadc_groups
    """

    help = "Create EADC user groups and assign appropriate permissions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--create-demo-users",
            action="store_true",
            help="Create demo users for testing EADC functionality",
        )

    def handle(self, *args, **options):
        """
        Main command execution
        """
        self.stdout.write(
            self.style.SUCCESS("Setting up EADC user groups and permissions...")
        )

        try:
            with transaction.atomic():
                self.create_eadc_groups()

                if options["create_demo_users"]:
                    self.create_demo_users()

                self.stdout.write(
                    self.style.SUCCESS("EADC setup completed successfully!")
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during EADC setup: {str(e)}"))

    def create_eadc_groups(self):
        """
        Create EADC user groups with appropriate permissions
        """
        # Create EADC Administrators group
        eadc_admin_group, created = Group.objects.get_or_create(
            name="eadc_administrators"
        )

        if created:
            self.stdout.write(self.style.SUCCESS("Created EADC Administrators group"))
        else:
            self.stdout.write(
                self.style.WARNING("EADC Administrators group already exists")
            )

        # Add permissions for full EADC access
        eadc_admin_permissions = [
            ("auth", "view_user"),
            ("auth", "view_group"),
            ("patient_data", "view_patientdata"),
            ("patient_data", "view_clinicaldocument"),
            ("patient_data", "change_clinicaldocument"),
            ("patient_data", "add_clinicaldocument"),
        ]

        admin_perms_added = 0
        for app_label, codename in eadc_admin_permissions:
            try:
                permission = Permission.objects.get(
                    content_type__app_label=app_label, codename=codename
                )
                eadc_admin_group.permissions.add(permission)
                admin_perms_added += 1
            except Permission.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"Permission {app_label}.{codename} not found")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Added {admin_perms_added} permissions to EADC Administrators"
            )
        )

        # Create EADC Operators group
        eadc_operator_group, created = Group.objects.get_or_create(
            name="eadc_operators"
        )

        if created:
            self.stdout.write(self.style.SUCCESS("Created EADC Operators group"))
        else:
            self.stdout.write(self.style.WARNING("EADC Operators group already exists"))

        # Add permissions for read-only EADC access
        eadc_operator_permissions = [
            ("patient_data", "view_patientdata"),
            ("patient_data", "view_clinicaldocument"),
        ]

        operator_perms_added = 0
        for app_label, codename in eadc_operator_permissions:
            try:
                permission = Permission.objects.get(
                    content_type__app_label=app_label, codename=codename
                )
                eadc_operator_group.permissions.add(permission)
                operator_perms_added += 1
            except Permission.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"Permission {app_label}.{codename} not found")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Added {operator_perms_added} permissions to EADC Operators"
            )
        )

    def create_demo_users(self):
        """
        Create demo users for testing EADC functionality
        """
        self.stdout.write("Creating demo EADC users...")

        # Create EADC Administrator demo user
        admin_user, created = User.objects.get_or_create(
            username="eadc_admin",
            defaults={
                "email": "eadc_admin@example.com",
                "first_name": "EADC",
                "last_name": "Administrator",
                "is_staff": True,
                "is_active": True,
            },
        )

        if created:
            eadc_password = os.getenv("EADC_ADMIN_PASSWORD")
            if not eadc_password:
                self.stdout.write(
                    self.style.ERROR(
                        "EADC_ADMIN_PASSWORD environment variable not set. Please set it in your .env file."
                    )
                )
                return

            admin_user.set_password(eadc_password)
            admin_user.save()

            # Add to EADC administrators group
            eadc_admin_group = Group.objects.get(name="eadc_administrators")
            admin_user.groups.add(eadc_admin_group)

            self.stdout.write(
                self.style.SUCCESS("Created EADC Administrator demo user: eadc_admin")
            )
        else:
            self.stdout.write(
                self.style.WARNING("EADC Administrator demo user already exists")
            )

        # Create EADC Operator demo user
        operator_user, created = User.objects.get_or_create(
            username="eadc_operator",
            defaults={
                "email": "eadc_operator@example.com",
                "first_name": "EADC",
                "last_name": "Operator",
                "is_staff": False,
                "is_active": True,
            },
        )

        if created:
            operator_user.set_password("eadc_operator_password")
            operator_user.save()

            # Add to EADC operators group
            eadc_operator_group = Group.objects.get(name="eadc_operators")
            operator_user.groups.add(eadc_operator_group)

            self.stdout.write(
                self.style.SUCCESS("Created EADC Operator demo user: eadc_operator")
            )
        else:
            self.stdout.write(
                self.style.WARNING("EADC Operator demo user already exists")
            )

        self.stdout.write(self.style.SUCCESS("Demo users created successfully!"))
        self.stdout.write(
            self.style.WARNING("Remember to change default passwords in production!")
        )
