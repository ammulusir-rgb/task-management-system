"""
Task signals — activity logging and real-time broadcasting.
"""

import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import ActivityAction, ActivityLog, Task, TaskStatus

logger = logging.getLogger(__name__)

# Fields to track changes for
TRACKED_FIELDS = [
    "title",
    "description",
    "status",
    "priority",
    "assignee_id",
    "column_id",
    "due_date",
    "estimated_hours",
]


@receiver(pre_save, sender=Task)
def track_task_changes(sender, instance, **kwargs):
    """
    Compare old vs new field values before saving.
    Store changes on the instance for post_save to process.
    """
    if not instance.pk:
        instance._is_new = True
        return

    instance._is_new = False
    instance._changes = []

    try:
        old = Task.all_objects.get(pk=instance.pk)
    except Task.DoesNotExist:
        instance._is_new = True
        return

    for field in TRACKED_FIELDS:
        old_val = getattr(old, field)
        new_val = getattr(instance, field)
        if old_val != new_val:
            instance._changes.append({
                "field": field,
                "old": str(old_val) if old_val is not None else None,
                "new": str(new_val) if new_val is not None else None,
            })

    # Auto-set started_at when moving to IN_PROGRESS
    if old.status != TaskStatus.IN_PROGRESS and instance.status == TaskStatus.IN_PROGRESS:
        if not instance.started_at:
            instance.started_at = timezone.now()

    # Auto-set completed_at when moving to DONE
    if old.status != TaskStatus.DONE and instance.status == TaskStatus.DONE:
        instance.completed_at = timezone.now()


@receiver(post_save, sender=Task)
def log_task_activity(sender, instance, created, **kwargs):
    """
    Create activity log entries for task changes and broadcast via WebSocket.
    """
    # Avoid recursive signals from activity log creation
    if getattr(instance, "_skip_signals", False):
        return

    user = getattr(instance, "_current_user", None)

    if created:
        ActivityLog.objects.create(
            task=instance,
            user=instance.reporter,
            action=ActivityAction.CREATED,
            description=f"Created task {instance.task_key}",
        )
        _broadcast_task_event(instance, "task_created")
        return

    changes = getattr(instance, "_changes", [])
    for change in changes:
        field = change["field"]
        action = _get_action_for_field(field)

        ActivityLog.objects.create(
            task=instance,
            user=user,
            action=action,
            field_name=field,
            old_value=change["old"],
            new_value=change["new"],
            description=_build_change_description(field, change["old"], change["new"]),
        )

    if changes:
        _broadcast_task_event(instance, "task_updated")


def _get_action_for_field(field: str) -> str:
    """Map a field name to an activity action."""
    mapping = {
        "status": ActivityAction.STATUS_CHANGED,
        "priority": ActivityAction.PRIORITY_CHANGED,
        "assignee_id": ActivityAction.ASSIGNED,
        "column_id": ActivityAction.MOVED,
    }
    return mapping.get(field, ActivityAction.UPDATED)


def _build_change_description(field: str, old_val, new_val) -> str:
    """Build a human-readable description of a field change."""
    field_label = field.replace("_id", "").replace("_", " ").title()
    if old_val and new_val:
        return f"Changed {field_label} from '{old_val}' to '{new_val}'"
    if new_val:
        return f"Set {field_label} to '{new_val}'"
    return f"Cleared {field_label}"


def _broadcast_task_event(task: Task, event_type: str):
    """Broadcast task changes to the board's WebSocket group."""
    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            return

        board = task.column.board if task.column else None
        if board is None:
            return

        group_name = f"board_{board.id}"
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "board.task_event",
                "event": event_type,
                "task_id": str(task.id),
                "task_key": task.task_key,
                "column_id": str(task.column_id) if task.column_id else None,
                "position": task.position,
            },
        )
    except Exception as e:
        logger.warning("Failed to broadcast task event: %s", e)
