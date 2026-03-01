"""
Views for Notifications.
Endpoint definitions only — all business logic lives in managers.py.
"""

from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.pagination import SmallResultsSetPagination

from .managers import notification_manager
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SmallResultsSetPagination

    def get_queryset(self):
        return notification_manager.get_user_notifications(self.request.user)

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        return Response({"count": notification_manager.get_unread_count(request.user)})

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        updated = notification_manager.mark_read(notification)
        return Response(NotificationSerializer(updated).data)

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        updated = notification_manager.mark_all_read(request.user)
        return Response({"updated": updated})

    @action(detail=False, methods=["delete"], url_path="clear-read")
    def clear_read(self, request):
        deleted = notification_manager.clear_read(request.user)
        return Response({"deleted": deleted})
