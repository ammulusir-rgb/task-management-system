"""
API views for email configuration and management.
Endpoint definitions only — all business logic lives in managers.py.
"""

from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.permissions import IsOrgMemberOrReadOnly

from .managers import email_manager
from .serializers import (
    EmailConfigurationSerializer,
    EmailConfigurationUpdateSerializer,
    EmailRuleSerializer,
    ProcessedEmailSerializer,
)


class EmailConfigurationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOrgMemberOrReadOnly]

    def get_queryset(self):
        return email_manager.get_configurations(self.request.user, self.request.query_params.get("organization"))

    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return EmailConfigurationUpdateSerializer
        return EmailConfigurationSerializer

    def perform_create(self, serializer):
        email_manager.create_configuration(self.request.user, self.request.data.get("organization"), serializer)

    @action(detail=True, methods=["post"])
    def test_connection(self, request, pk=None):
        config = self.get_object()
        task_id = email_manager.test_connection(config)
        return Response({"message": "Connection test started", "task_id": task_id})

    @action(detail=True, methods=["post"])
    def process_emails(self, request, pk=None):
        config = self.get_object()
        task_id = email_manager.process_emails(config)
        return Response({"message": "Email processing started", "task_id": task_id})


class EmailRuleViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOrgMemberOrReadOnly]

    serializer_class = EmailRuleSerializer

    def get_queryset(self):
        return email_manager.get_rules(self.request.user, self.request.query_params.get("organization"))

    def perform_create(self, serializer):
        email_manager.create_rule(self.request.user, self.request.data.get("organization"), serializer)


class ProcessedEmailViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOrgMemberOrReadOnly]

    serializer_class = ProcessedEmailSerializer

    def get_queryset(self):
        return email_manager.get_processed_emails(self.request.user, self.request.query_params.get("organization"))
