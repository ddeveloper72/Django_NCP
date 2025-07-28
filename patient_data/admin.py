"""
Patient Data Admin Interface
Django admin configuration for patient data management
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils import timezone
from .models import (
    MemberState,
    PatientIdentifier,
    PatientData,
    AvailableService,
    PatientServiceRequest
)


@admin.register(MemberState)
class MemberStateAdmin(admin.ModelAdmin):
    list_display = [
        'country_name',
        'country_code',
        'language_code',
        'home_community_id',
        'is_active',
        'created_at'
    ]
    list_filter = ['is_active', 'language_code', 'created_at']
    search_fields = ['country_name', 'country_code', 'home_community_id']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('country_code', 'country_name', 'language_code')
        }),
        ('NCP Configuration', {
            'fields': ('ncp_endpoint', 'home_community_id', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AvailableService)
class AvailableServiceAdmin(admin.ModelAdmin):
    list_display = [
        'service_name',
        'service_type',
        'member_state',
        'is_active'
    ]
    list_filter = ['service_type', 'is_active', 'member_state']
    search_fields = ['service_name', 'service_description']
    
    fieldsets = (
        ('Service Information', {
            'fields': ('service_name', 'service_type', 'service_description')
        }),
        ('Configuration', {
            'fields': ('member_state', 'is_active')
        }),
    )


class AvailableServiceInline(admin.TabularInline):
    model = AvailableService
    extra = 1
    fields = ['service_type', 'service_name', 'is_active']


@admin.register(PatientIdentifier)
class PatientIdentifierAdmin(admin.ModelAdmin):
    list_display = [
        'patient_id',
        'home_member_state',
        'id_root',
        'created_at'
    ]
    list_filter = ['home_member_state', 'created_at']
    search_fields = ['patient_id', 'id_extension', 'id_root']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Patient Identification', {
            'fields': ('patient_id', 'id_extension', 'id_root')
        }),
        ('Source Information', {
            'fields': ('home_member_state',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(PatientData)
class PatientDataAdmin(admin.ModelAdmin):
    list_display = [
        'get_patient_name',
        'patient_identifier',
        'birth_date',
        'gender',
        'get_access_type',
        'accessed_by',
        'access_timestamp'
    ]
    list_filter = [
        'gender',
        'consent_given',
        'break_glass_access',
        'access_timestamp',
        'patient_identifier__home_member_state'
    ]
    search_fields = [
        'given_name',
        'family_name',
        'patient_identifier__patient_id',
        'accessed_by__username'
    ]
    readonly_fields = [
        'access_timestamp',
        'consent_timestamp',
        'break_glass_timestamp'
    ]
    
    fieldsets = (
        ('Patient Information', {
            'fields': (
                'patient_identifier',
                'given_name',
                'family_name',
                'birth_date',
                'gender'
            )
        }),
        ('Contact Information', {
            'fields': ('address_line', 'city', 'postal_code', 'country'),
            'classes': ('collapse',)
        }),
        ('Consent Management', {
            'fields': (
                'consent_given',
                'consent_timestamp',
                'consent_given_by'
            )
        }),
        ('Break Glass Access', {
            'fields': (
                'break_glass_access',
                'break_glass_reason',
                'break_glass_by',
                'break_glass_timestamp'
            ),
            'classes': ('collapse',)
        }),
        ('Access Tracking', {
            'fields': ('accessed_by', 'access_timestamp')
        }),
        ('Raw Data', {
            'fields': ('raw_patient_summary', 'raw_eprescription'),
            'classes': ('collapse',)
        }),
    )
    
    def get_patient_name(self, obj):
        name = f"{obj.given_name} {obj.family_name}".strip()
        return name if name else "Unknown"
    get_patient_name.short_description = "Patient Name"
    
    def get_access_type(self, obj):
        access_type = obj.get_access_type()
        if access_type == "Break Glass":
            return format_html('<span style="color: red; font-weight: bold;">{}</span>', access_type)
        elif access_type == "With Consent":
            return format_html('<span style="color: green;">{}</span>', access_type)
        else:
            return format_html('<span style="color: orange;">{}</span>', access_type)
    get_access_type.short_description = "Access Type"


@admin.register(PatientServiceRequest)
class PatientServiceRequestAdmin(admin.ModelAdmin):
    list_display = [
        'request_id',
        'get_patient_info',
        'requested_service',
        'status',
        'consent_method',
        'requested_by',
        'request_timestamp'
    ]
    list_filter = [
        'status',
        'consent_method',
        'consent_required',
        'consent_obtained',
        'request_timestamp',
        'requested_service__service_type'
    ]
    search_fields = [
        'request_id',
        'patient_identifier__patient_id',
        'requested_by__username',
        'error_message'
    ]
    readonly_fields = [
        'request_id',
        'request_timestamp',
        'response_timestamp'
    ]
    
    fieldsets = (
        ('Request Information', {
            'fields': (
                'request_id',
                'patient_identifier',
                'requested_service',
                'requested_by',
                'request_timestamp'
            )
        }),
        ('Status and Consent', {
            'fields': (
                'status',
                'consent_required',
                'consent_obtained',
                'consent_method'
            )
        }),
        ('Response Data', {
            'fields': (
                'response_data',
                'response_timestamp',
                'error_message'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_patient_info(self, obj):
        return f"{obj.patient_identifier.patient_id} ({obj.patient_identifier.home_member_state.country_code})"
    get_patient_info.short_description = "Patient"
    
    actions = ['mark_as_completed', 'mark_as_failed']
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(
            status='COMPLETED',
            response_timestamp=timezone.now()
        )
        self.message_user(request, f'{updated} requests marked as completed.')
    mark_as_completed.short_description = "Mark selected requests as completed"
    
    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='FAILED')
        self.message_user(request, f'{updated} requests marked as failed.')
    mark_as_failed.short_description = "Mark selected requests as failed"


# Enhance MemberState admin with services inline
MemberStateAdmin.inlines = [AvailableServiceInline]
