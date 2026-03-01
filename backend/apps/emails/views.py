"""
API views for email configuration and management.
"""

from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from apps.common.permissions import IsOrgMemberOrReadOnly
from apps.organizations.models import Organization

from .models import EmailConfiguration, EmailRule, ProcessedEmail
from .serializers import (
    EmailConfigurationSerializer,
    EmailConfigurationUpdateSerializer, 
    EmailRuleSerializer,
    ProcessedEmailSerializer
)
from .tasks import test_email_connection, process_organization_emails


class EmailConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing email configurations."""
    
    serializer_class = EmailConfigurationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgMemberOrReadOnly]
    
    def get_queryset(self):
        org_id = self.request.query_params.get('organization')
        if org_id:
            organization = get_object_or_404(Organization, id=org_id)
            # Check if user has access to this organization
            if not organization.members.filter(id=self.request.user.id).exists():
                return EmailConfiguration.objects.none()
            return EmailConfiguration.objects.filter(organization=organization)
        return EmailConfiguration.objects.none()
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return EmailConfigurationUpdateSerializer
        return EmailConfigurationSerializer
    
    def perform_create(self, serializer):
        org_id = self.request.data.get('organization')
        organization = get_object_or_404(Organization, id=org_id)
        
        # Check if user has access
        if not organization.members.filter(id=self.request.user.id).exists():
            raise permissions.PermissionDenied("You don't have access to this organization")
        
        serializer.save(organization=organization)
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test email connection for this configuration."""
        config = self.get_object()
        
        # Start async task to test connection
        task = test_email_connection.delay(str(config.id))
        
        return Response({
            'message': 'Connection test started',
            'task_id': task.id
        })
    
    @action(detail=True, methods=['post'])
    def process_emails(self, request, pk=None):
        """Manually trigger email processing for this organization."""
        config = self.get_object()
        
        if not config.imap_enabled:
            return Response(
                {'error': 'IMAP is not enabled for this configuration'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Start async task to process emails
        task = process_organization_emails.delay(str(config.organization.id))
        
        return Response({
            'message': 'Email processing started',
            'task_id': task.id
        })


class EmailRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing email rules."""
    
    serializer_class = EmailRuleSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgMemberOrReadOnly]
    
    def get_queryset(self):
        org_id = self.request.query_params.get('organization')
        if org_id:
            organization = get_object_or_404(Organization, id=org_id)
            # Check if user has access to this organization
            if not organization.members.filter(id=self.request.user.id).exists():
                return EmailRule.objects.none()
            return EmailRule.objects.filter(organization=organization)
        return EmailRule.objects.none()
    
    def perform_create(self, serializer):
        org_id = self.request.data.get('organization')
        organization = get_object_or_404(Organization, id=org_id)
        
        # Check if user has access
        if not organization.members.filter(id=self.request.user.id).exists():
            raise permissions.PermissionDenied("You don't have access to this organization")
        
        serializer.save(organization=organization)


class ProcessedEmailViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing processed emails."""
    
    serializer_class = ProcessedEmailSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgMemberOrReadOnly]
    
    def get_queryset(self):
        org_id = self.request.query_params.get('organization')
        if org_id:
            organization = get_object_or_404(Organization, id=org_id)
            # Check if user has access to this organization
            if not organization.members.filter(id=self.request.user.id).exists():
                return ProcessedEmail.objects.none()
            return ProcessedEmail.objects.filter(organization=organization)
        return ProcessedEmail.objects.none()
