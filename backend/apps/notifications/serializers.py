"""
Serializers for Notifications.
"""

from rest_framework import serializers

from apps.users.serializers import UserListSerializer

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notification detail."""

    sender = UserListSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "recipient",
            "sender",
            "notification_type",
            "title",
            "message",
            "is_read",
            "read_at",
            "object_id",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "recipient",
            "sender",
            "notification_type",
            "title",
            "message",
            "object_id",
            "created_at",
        ]
