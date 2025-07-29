"""
EADC Administration and User Management
Django admin configuration for EADC user groups and permissions
"""

from django.contrib import admin
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.admin import GroupAdmin
from django.core.management.base import BaseCommand
from django.db import transaction


class EADCGroupAdmin(GroupAdmin):
    """
    Custom admin for EADC-related groups
    """

    list_display = ("name", "get_users_count", "get_permissions_count")

    def get_users_count(self, obj):
        return obj.user_set.count()

    get_users_count.short_description = "Users Count"

    def get_permissions_count(self, obj):
        return obj.permissions.count()

    get_permissions_count.short_description = "Permissions Count"


def create_eadc_groups():
    """
    Create EADC user groups with appropriate permissions
    """
    with transaction.atomic():
        # Create EADC Administrators group
        eadc_admin_group, created = Group.objects.get_or_create(
            name="eadc_administrators"
        )

        if created:
            print("Created EADC Administrators group")

            # Add permissions for full EADC access
            eadc_admin_permissions = [
                "auth.view_user",
                "auth.view_group",
                "patient_data.view_patientdata",
                "patient_data.view_clinicaldocument",
                "patient_data.change_clinicaldocument",
                "patient_data.add_clinicaldocument",
            ]

            for perm_codename in eadc_admin_permissions:
                try:
                    app_label, codename = perm_codename.split(".")
                    permission = Permission.objects.get(
                        content_type__app_label=app_label, codename=codename
                    )
                    eadc_admin_group.permissions.add(permission)
                except Permission.DoesNotExist:
                    print(f"Permission {perm_codename} not found")

        # Create EADC Operators group
        eadc_operator_group, created = Group.objects.get_or_create(
            name="eadc_operators"
        )

        if created:
            print("Created EADC Operators group")

            # Add permissions for read-only EADC access
            eadc_operator_permissions = [
                "patient_data.view_patientdata",
                "patient_data.view_clinicaldocument",
            ]

            for perm_codename in eadc_operator_permissions:
                try:
                    app_label, codename = perm_codename.split(".")
                    permission = Permission.objects.get(
                        content_type__app_label=app_label, codename=codename
                    )
                    eadc_operator_group.permissions.add(permission)
                except Permission.DoesNotExist:
                    print(f"Permission {perm_codename} not found")


# Register the custom admin if groups don't already have custom admin
try:
    admin.site.unregister(Group)
    admin.site.register(Group, EADCGroupAdmin)
except admin.sites.AlreadyRegistered:
    pass
