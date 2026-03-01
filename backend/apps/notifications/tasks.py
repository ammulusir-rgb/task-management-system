"""
Celery tasks for the Notifications app.
Handles async notification delivery (email, push, etc.).
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Notification, NotificationType

logger = logging.getLogger(__name__)

User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification_email(self, notification_id: str):
    """Send an email for a specific notification."""
    try:
        notification = Notification.objects.select_related("recipient").get(
            id=notification_id
        )
    except Notification.DoesNotExist:
        logger.warning("Notification %s not found for email delivery", notification_id)
        return

    recipient = notification.recipient
    if not recipient.is_active:
        return

    try:
        send_mail(
            subject=notification.title,
            message=notification.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient.email],
            html_message=f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2563eb;">{notification.title}</h2>
                <p style="color: #374151; font-size: 16px;">{notification.message}</p>
                <hr style="border: 1px solid #e5e7eb;" />
                <p style="color: #6b7280; font-size: 12px;">
                    You received this email because of your notification settings.
                </p>
            </div>
            """,
        )
        logger.info("Notification email sent to %s", recipient.email)
    except Exception as exc:
        logger.error("Failed to send notification email: %s", exc)
        raise self.retry(exc=exc)


@shared_task
def send_due_date_reminder_notifications():
    """
    Create notifications for tasks due within the next 24 hours.
    Runs via Celery Beat (daily at 8 AM).
    """
    from apps.tasks.models import Task

    tomorrow = timezone.now() + timedelta(days=1)
    today = timezone.now()

    upcoming_tasks = (
        Task.objects.filter(
            due_date__gte=today,
            due_date__lte=tomorrow,
            status__in=["todo", "in_progress", "in_review"],
            assignee__isnull=False,
            deleted_at__isnull=True,
        )
        .select_related("assignee", "column__board__project")
        .distinct()
    )

    notifications = []
    for task in upcoming_tasks:
        notifications.append(
            Notification(
                recipient=task.assignee,
                notification_type=NotificationType.DUE_DATE_REMINDER,
                title="Task due soon",
                message=f'"{task.title}" in {task.column.board.project.name} is due {task.due_date.strftime("%B %d, %Y")}.',
                content_object=task,
            )
        )

    if notifications:
        Notification.objects.bulk_create(notifications)
        logger.info("Created %d due-date reminder notifications", len(notifications))

    return len(notifications)


@shared_task
def send_overdue_task_notifications():
    """
    Create notifications for overdue tasks.
    Runs via Celery Beat (daily at 9 AM).
    """
    from apps.tasks.models import Task

    now = timezone.now()

    overdue_tasks = (
        Task.objects.filter(
            due_date__lt=now,
            status__in=["todo", "in_progress", "in_review"],
            assignee__isnull=False,
            deleted_at__isnull=True,
        )
        .select_related("assignee", "column__board__project")
        .distinct()
    )

    notifications = []
    for task in overdue_tasks:
        # Avoid sending duplicate overdue notifications for the same day
        existing = Notification.objects.filter(
            recipient=task.assignee,
            notification_type=NotificationType.TASK_OVERDUE,
            object_id=str(task.id),
            created_at__date=now.date(),
        ).exists()

        if not existing:
            notifications.append(
                Notification(
                    recipient=task.assignee,
                    notification_type=NotificationType.TASK_OVERDUE,
                    title="Task overdue",
                    message=f'"{task.title}" in {task.column.board.project.name} is overdue.',
                    content_object=task,
                )
            )

    if notifications:
        Notification.objects.bulk_create(notifications)
        logger.info("Created %d overdue task notifications", len(notifications))

    return len(notifications)


@shared_task
def cleanup_old_notifications(days: int = 90):
    """Remove read notifications older than the specified number of days."""
    cutoff = timezone.now() - timedelta(days=days)
    count, _ = Notification.objects.filter(
        is_read=True,
        created_at__lt=cutoff,
    ).delete()

    logger.info("Cleaned up %d old read notifications", count)
    return count
