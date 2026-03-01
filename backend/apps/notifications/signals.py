"""
Signal handlers for the Notifications app.
Creates notifications automatically in response to model events.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.tasks.models import Comment, Task

from .models import Notification, NotificationType

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Task)
def notify_task_assignment(sender, instance, created, **kwargs):
    """Send a notification when a task is assigned to someone."""
    if instance.assignee and instance.assignee != instance.reporter:
        if created:
            Notification.objects.create(
                recipient=instance.assignee,
                notification_type=NotificationType.TASK_ASSIGNED,
                title="New task assigned to you",
                message=f'You have been assigned to "{instance.title}" in {instance.column.board.project.name}.',
                content_object=instance,
            )
        else:
            # Check if assignee changed (handled via tracker in views/signals)
            pass


@receiver(post_save, sender=Task)
def notify_task_status_change(sender, instance, created, **kwargs):
    """Notify the reporter when a task is completed."""
    if not created and instance.status == "done" and instance.reporter:
        if instance.reporter != instance.assignee:
            Notification.objects.create(
                recipient=instance.reporter,
                notification_type=NotificationType.STATUS_CHANGED,
                title="Task completed",
                message=f'"{instance.title}" has been marked as done.',
                content_object=instance,
            )


@receiver(post_save, sender=Comment)
def notify_comment_added(sender, instance, created, **kwargs):
    """Notify the task assignee and reporter when a new comment is added."""
    if not created:
        return

    task = instance.task
    commenter = instance.author
    recipients = set()

    # Notify assignee
    if task.assignee and task.assignee != commenter:
        recipients.add(task.assignee)

    # Notify reporter
    if task.reporter and task.reporter != commenter:
        recipients.add(task.reporter)

    # Notify parent comment author (for threaded replies)
    if instance.parent and instance.parent.author != commenter:
        recipients.add(instance.parent.author)

    notifications = [
        Notification(
            recipient=recipient,
            notification_type=NotificationType.COMMENT_ADDED,
            title="New comment on task",
            message=f'{commenter.get_full_name() or commenter.email} commented on "{task.title}".',
            content_object=task,
        )
        for recipient in recipients
    ]

    if notifications:
        Notification.objects.bulk_create(notifications)
        logger.info(
            "Created %d comment notifications for task %s",
            len(notifications),
            task.task_key,
        )
