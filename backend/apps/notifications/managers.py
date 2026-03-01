"""
Business-logic manager for Notifications.
Views delegate to this class; all methods carry enter/exit/error logging
and raise domain exceptions on failure.
"""

import logging

from django.utils import timezone

from .models import Notification

logger = logging.getLogger(__name__)


class NotificationManager:
    """Handles all business logic for the notifications app."""

    def get_user_notifications(self, user):
        """Return all notifications for *user*, newest first."""
        logger.debug("ENTER NotificationManager.get_user_notifications | user=%s", user.pk)
        try:
            qs = (
                Notification.objects.filter(recipient=user)
                .select_related("sender")
                .order_by("-created_at")
            )
            logger.debug("EXIT NotificationManager.get_user_notifications | user=%s count=%d", user.pk, qs.count())
            return qs
        except Exception as exc:
            logger.error("ERROR NotificationManager.get_user_notifications: %s", exc, exc_info=True)
            raise

    def get_unread_count(self, user) -> int:
        """Return the count of unread notifications for *user*."""
        logger.debug("ENTER NotificationManager.get_unread_count | user=%s", user.pk)
        try:
            count = Notification.objects.filter(recipient=user, is_read=False).count()
            logger.debug("EXIT NotificationManager.get_unread_count | user=%s count=%d", user.pk, count)
            return count
        except Exception as exc:
            logger.error("ERROR NotificationManager.get_unread_count: %s", exc, exc_info=True)
            raise

    def mark_read(self, notification) -> Notification:
        """Mark a single *notification* as read and return it."""
        logger.debug("ENTER NotificationManager.mark_read | notification=%s", notification.pk)
        try:
            notification.mark_as_read()
            logger.debug("EXIT NotificationManager.mark_read | notification=%s", notification.pk)
            return notification
        except Exception as exc:
            logger.error("ERROR NotificationManager.mark_read: %s", exc, exc_info=True)
            raise

    def mark_all_read(self, user) -> int:
        """Mark all unread notifications for *user* as read. Returns updated count."""
        logger.debug("ENTER NotificationManager.mark_all_read | user=%s", user.pk)
        try:
            updated = Notification.objects.filter(
                recipient=user, is_read=False
            ).update(is_read=True, read_at=timezone.now())
            logger.debug("EXIT NotificationManager.mark_all_read | user=%s updated=%d", user.pk, updated)
            return updated
        except Exception as exc:
            logger.error("ERROR NotificationManager.mark_all_read: %s", exc, exc_info=True)
            raise

    def clear_read(self, user) -> int:
        """Delete all read notifications for *user*. Returns deleted count."""
        logger.debug("ENTER NotificationManager.clear_read | user=%s", user.pk)
        try:
            deleted_count, _ = Notification.objects.filter(
                recipient=user, is_read=True
            ).delete()
            logger.debug("EXIT NotificationManager.clear_read | user=%s deleted=%d", user.pk, deleted_count)
            return deleted_count
        except Exception as exc:
            logger.error("ERROR NotificationManager.clear_read: %s", exc, exc_info=True)
            raise


# Module-level singleton
notification_manager = NotificationManager()
