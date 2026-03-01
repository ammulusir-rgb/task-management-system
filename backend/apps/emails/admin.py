"""
Django admin configuration for email management.
"""

from django.contrib import admin
from .models import EmailConfiguration, EmailRule, ProcessedEmail


@admin.register(EmailConfiguration)
class EmailConfigurationAdmin(admin.ModelAdmin):
    list_display = ['organization', 'imap_enabled', 'smtp_enabled', 'task_email_address', 'created_at']
    list_filter = ['imap_enabled', 'smtp_enabled', 'created_at']
    search_fields = ['organization__name', 'task_email_address']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Organization', {
            'fields': ['organization']
        }),
        ('IMAP Settings', {
            'fields': ['imap_enabled', 'imap_host', 'imap_port', 'imap_use_ssl', 
                      'imap_username', 'imap_password']
        }),
        ('SMTP Settings', {
            'fields': ['smtp_enabled', 'smtp_host', 'smtp_port', 'smtp_use_tls',
                      'smtp_username', 'smtp_password']
        }),
        ('Email-to-Task Settings', {
            'fields': ['task_email_address', 'default_project', 'auto_assign_reporter']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]


@admin.register(EmailRule)
class EmailRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'rule_type', 'rule_value', 'target_project', 'is_active']
    list_filter = ['rule_type', 'is_active', 'created_at', 'organization']
    search_fields = ['name', 'rule_value', 'organization__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Rule Configuration', {
            'fields': ['organization', 'name', 'rule_type', 'rule_value', 'is_active']
        }),
        ('Actions', {
            'fields': ['target_project', 'default_assignee', 'default_priority', 'default_status']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]


@admin.register(ProcessedEmail)
class ProcessedEmailAdmin(admin.ModelAdmin):
    list_display = ['subject', 'sender', 'organization', 'task_created', 'received_at', 'processed_at']
    list_filter = ['organization', 'processed_at', 'received_at']
    search_fields = ['subject', 'sender', 'message_id']
    readonly_fields = ['received_at', 'processed_at']
    date_hierarchy = 'processed_at'
    
    def has_add_permission(self, request):
        return False  # Don't allow manual creation
    
    def has_change_permission(self, request, obj=None):
        return False  # Don't allow editing
