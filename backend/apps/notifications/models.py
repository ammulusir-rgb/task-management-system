"""
Notification models.
"""

import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.common.mixins import TimestampMixin


class NotificationType(models.TextChoices):
    TASK_ASSIGNED = "TASK_ASSIGNED", "Task Assigned"
    TASK_UPDATED = "TASK_UPDATED", "Task Updated"
    TASK_COMPLETED = "TASK_COMPLETED", "Task Completed"
    COMMENT_ADDED = "COMMENT_ADDED", "Comment Added"
    MENTION = "MENTION", "Mentioned"
    DUE_DATE_REMINDER = "DUE_DATE_REMINDER", "Due Date Reminder"
    PROJECT_INVITATION = "PROJECT_INVITATION", "Project Invitation"
    SYSTEM = "SYSTEM", "System Notification"


class Notification(TimestampMixin, models.Model):
    """
    Notification model supporting polymorphic content linking via GenericFK.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_notifications",
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        db_index=True,
    )
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True, default="")
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)

    # Generic FK to link to any model (Task, Comment, Project, etc.)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    object_id = models.UUIDField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["recipient", "is_read", "-created_at"],
                name="idx_notif_recipient_read",
            ),
            models.Index(
                fields=["recipient", "-created_at"],
                name="idx_notif_recipient_date",
            ),
        ]

    def __str__(self) -> str:
        return f"[{self.notification_type}] {self.title} → {self.recipient.email}"

    def mark_as_read(self):
        from django.utils import timezone

        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=["is_read", "read_at"])
