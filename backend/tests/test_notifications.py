"""Tests for the Notifications app."""

import pytest
from rest_framework import status

from apps.notifications.models import Notification, NotificationType
from tests.factories import NotificationFactory


@pytest.mark.django_db
class TestNotificationEndpoints:
    url = "/api/v1/notifications/"

    def test_list_notifications(self, authenticated_client, user):
        NotificationFactory(recipient=user)
        NotificationFactory(recipient=user)

        response = authenticated_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 2

    def test_unread_count(self, authenticated_client, user):
        NotificationFactory(recipient=user, is_read=False)
        NotificationFactory(recipient=user, is_read=False)
        NotificationFactory(recipient=user, is_read=True)

        response = authenticated_client.get(f"{self.url}unread_count/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["unread_count"] == 2

    def test_mark_read(self, authenticated_client, user):
        notification = NotificationFactory(recipient=user, is_read=False)
        response = authenticated_client.post(
            f"{self.url}{notification.id}/mark_read/"
        )
        assert response.status_code == status.HTTP_200_OK
        notification.refresh_from_db()
        assert notification.is_read is True

    def test_mark_all_read(self, authenticated_client, user):
        NotificationFactory(recipient=user, is_read=False)
        NotificationFactory(recipient=user, is_read=False)

        response = authenticated_client.post(f"{self.url}mark_all_read/")
        assert response.status_code == status.HTTP_200_OK

        unread = Notification.objects.filter(
            recipient=user, is_read=False
        ).count()
        assert unread == 0

    def test_clear_read(self, authenticated_client, user):
        NotificationFactory(recipient=user, is_read=True)
        NotificationFactory(recipient=user, is_read=True)
        NotificationFactory(recipient=user, is_read=False)

        response = authenticated_client.post(f"{self.url}clear_read/")
        assert response.status_code == status.HTTP_200_OK

        total = Notification.objects.filter(recipient=user).count()
        assert total == 1  # only unread remains

    def test_other_user_notifications_not_visible(
        self, authenticated_client, user, other_user
    ):
        NotificationFactory(recipient=other_user)
        response = authenticated_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0
