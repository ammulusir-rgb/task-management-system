"""
Email Configuration and Processing Models.
Handles IMAP settings, email parsing, and task creation from emails.
"""

from django.db import models
from django.contrib.auth import get_user_model
from apps.common.models import BaseModel
from apps.organizations.models import Organization
from apps.projects.models import Project

User = get_user_model()


class EmailConfiguration(BaseModel):
    """Email server configuration for organizations."""
    
    organization = models.OneToOneField(
        Organization, 
        on_delete=models.CASCADE,
        related_name='email_config'
    )
    
    # IMAP Settings
    imap_enabled = models.BooleanField(default=False)
    imap_host = models.CharField(max_length=255, blank=True)
    imap_port = models.PositiveIntegerField(default=993)
    imap_use_ssl = models.BooleanField(default=True)
    imap_username = models.CharField(max_length=255, blank=True)
    imap_password = models.CharField(max_length=255, blank=True)  # Encrypted in production
    
    # SMTP Settings
    smtp_enabled = models.BooleanField(default=False)
    smtp_host = models.CharField(max_length=255, blank=True)
    smtp_port = models.PositiveIntegerField(default=587)
    smtp_use_tls = models.BooleanField(default=True)
    smtp_username = models.CharField(max_length=255, blank=True)
    smtp_password = models.CharField(max_length=255, blank=True)  # Encrypted in production
    
    # Email-to-Task Settings
    task_email_address = models.EmailField(blank=True, help_text="Email address for creating tasks")
    default_project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    auto_assign_reporter = models.BooleanField(default=True, help_text="Auto-assign task to email sender")
    
    class Meta:
        verbose_name = "Email Configuration"
        verbose_name_plural = "Email Configurations"
    
    def __str__(self):
        return f"Email Config for {self.organization.name}"


class ProcessedEmail(BaseModel):
    """Track processed emails to prevent duplicates."""
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    message_id = models.CharField(max_length=255, db_index=True)
    subject = models.CharField(max_length=500)
    sender = models.EmailField()
    received_at = models.DateTimeField()
    processed_at = models.DateTimeField(auto_now_add=True)
    
    # Result
    task_created = models.ForeignKey(
        'tasks.Task',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='source_email'
    )
    processing_error = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('organization', 'message_id')
        verbose_name = "Processed Email"
        verbose_name_plural = "Processed Emails"
        ordering = ['-received_at']
    
    def __str__(self):
        return f"Email: {self.subject} from {self.sender}"


class EmailRule(BaseModel):
    """Rules for processing incoming emails."""
    
    RULE_TYPES = [
        ('subject_contains', 'Subject contains'),
        ('sender_domain', 'Sender domain'),
        ('sender_email', 'Sender email'),
        ('body_contains', 'Body contains'),
    ]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    rule_value = models.CharField(max_length=500)
    is_active = models.BooleanField(default=True)
    
    # Actions
    target_project = models.ForeignKey(Project, on_delete=models.CASCADE)
    default_assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    default_priority = models.CharField(max_length=10, default='medium')
    default_status = models.CharField(max_length=15, default='todo')
    
    class Meta:
        verbose_name = "Email Rule"
        verbose_name_plural = "Email Rules"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.organization.name})"
