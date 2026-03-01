"""
Serializers for email configuration and management.
"""

from rest_framework import serializers
from .models import EmailConfiguration, EmailRule, ProcessedEmail


class EmailConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for email configuration."""
    
    class Meta:
        model = EmailConfiguration
        fields = [
            'id', 'imap_enabled', 'imap_host', 'imap_port', 'imap_use_ssl',
            'imap_username', 'smtp_enabled', 'smtp_host', 'smtp_port', 
            'smtp_use_tls', 'smtp_username', 'task_email_address',
            'default_project', 'auto_assign_reporter', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """Hide passwords in API responses."""
        data = super().to_representation(instance)
        # Don't expose passwords
        data['imap_password_set'] = bool(instance.imap_password)
        data['smtp_password_set'] = bool(instance.smtp_password)
        return data


class EmailConfigurationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating email configuration with password fields."""
    
    imap_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    smtp_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = EmailConfiguration
        fields = [
            'imap_enabled', 'imap_host', 'imap_port', 'imap_use_ssl',
            'imap_username', 'imap_password', 'smtp_enabled', 'smtp_host', 
            'smtp_port', 'smtp_use_tls', 'smtp_username', 'smtp_password',
            'task_email_address', 'default_project', 'auto_assign_reporter'
        ]
    
    def update(self, instance, validated_data):
        # Handle password updates
        imap_password = validated_data.pop('imap_password', None)
        smtp_password = validated_data.pop('smtp_password', None)
        
        instance = super().update(instance, validated_data)
        
        if imap_password is not None:
            instance.imap_password = imap_password
        if smtp_password is not None:
            instance.smtp_password = smtp_password
        
        instance.save()
        return instance


class EmailRuleSerializer(serializers.ModelSerializer):
    """Serializer for email rules."""
    
    class Meta:
        model = EmailRule
        fields = [
            'id', 'name', 'rule_type', 'rule_value', 'is_active',
            'target_project', 'default_assignee', 'default_priority',
            'default_status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProcessedEmailSerializer(serializers.ModelSerializer):
    """Serializer for processed emails."""
    
    task_key = serializers.CharField(source='task_created.task_key', read_only=True)
    task_title = serializers.CharField(source='task_created.title', read_only=True)
    
    class Meta:
        model = ProcessedEmail
        fields = [
            'id', 'subject', 'sender', 'received_at', 'processed_at',
            'task_key', 'task_title', 'processing_error'
        ]
        read_only_fields = ['id', 'processed_at']
