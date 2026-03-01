"""
Celery tasks for task-related background operations.
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def send_due_date_reminders():
    """
    Send reminders for tasks due within the next 24 hours.
    Runs daily via Celery Beat at 8 AM UTC.
    """
    from apps.tasks.models import Task, TaskStatus

    tomorrow = timezone.now() + timedelta(days=1)
    today = timezone.now()

    tasks_due_soon = (
        Task.objects.filter(
            due_date__gte=today,
            due_date__lte=tomorrow,
            assignee__isnull=False,
        )
        .exclude(status__in=[TaskStatus.DONE, TaskStatus.CANCELLED])
        .select_related("assignee", "project")
    )

    for task in tasks_due_soon:
        try:
            send_mail(
                subject=f"Reminder: {task.task_key} is due soon",
                message=(
                    f"Hi {task.assignee.first_name},\n\n"
                    f"This is a reminder that task '{task.title}' ({task.task_key}) "
                    f"in project '{task.project.name}' is due on "
                    f"{task.due_date.strftime('%B %d, %Y at %I:%M %p UTC')}.\n\n"
                    f"Best regards,\nTask Manager"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[task.assignee.email],
                fail_silently=True,
            )
        except Exception as exc:
            logger.error("Failed to send due date reminder for %s: %s", task.task_key, exc)

    logger.info("Sent %d due date reminders", tasks_due_soon.count())


@shared_task
def send_overdue_notifications():
    """
    Send notifications for overdue tasks.
    Runs daily via Celery Beat at 9 AM UTC.
    """
    from django.contrib.contenttypes.models import ContentType

    from apps.notifications.models import Notification, NotificationType
    from apps.tasks.models import Task, TaskStatus

    now = timezone.now()
    task_ct = ContentType.objects.get_for_model(Task)

    overdue_tasks = (
        Task.objects.filter(
            due_date__lt=now,
            assignee__isnull=False,
        )
        .exclude(status__in=[TaskStatus.DONE, TaskStatus.CANCELLED])
        .select_related("assignee", "project")
    )

    notifications = []
    for task in overdue_tasks:
        notifications.append(
            Notification(
                recipient=task.assignee,
                notification_type=NotificationType.DUE_DATE_REMINDER,
                title=f"Task Overdue: {task.task_key}",
                message=f"Task '{task.title}' in '{task.project.name}' is overdue.",
                content_type=task_ct,
                object_id=task.id,
            )
        )

    if notifications:
        Notification.objects.bulk_create(notifications, ignore_conflicts=True)
        logger.info("Created %d overdue notifications", len(notifications))


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_task_assignment_email(self, task_id: str, assigner_id: str):
    """Send email notification when a task is assigned."""
    from django.contrib.auth import get_user_model

    from apps.tasks.models import Task

    User = get_user_model()

    try:
        task = Task.objects.select_related("assignee", "project").get(id=task_id)
        assigner = User.objects.get(id=assigner_id)

        if not task.assignee:
            return

        send_mail(
            subject=f"Task Assigned: {task.task_key} - {task.title}",
            message=(
                f"Hi {task.assignee.first_name},\n\n"
                f"{assigner.full_name} has assigned you to task "
                f"'{task.title}' ({task.task_key}) in project '{task.project.name}'.\n\n"
                f"Priority: {task.get_priority_display()}\n"
                f"Due Date: {task.due_date.strftime('%B %d, %Y') if task.due_date else 'Not set'}\n\n"
                f"Best regards,\nTask Manager"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[task.assignee.email],
            fail_silently=False,
        )
        logger.info("Task assignment email sent for %s to %s", task.task_key, task.assignee.email)
    except Exception as exc:
        logger.error("Failed to send task assignment email: %s", exc)
        self.retry(exc=exc)
