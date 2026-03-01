"""
Business-logic manager for Tasks, Comments, Attachments, and Activity Logs.
Views delegate to this class; all methods carry enter/exit/error logging
and raise domain exceptions on failure.
"""

import logging

from django.db import transaction
from django.db.models import Count, F

from apps.common.exceptions import NotFoundError

from .models import ActivityLog, Attachment, Comment, Task

logger = logging.getLogger(__name__)


class TaskManager:
    """Handles all business logic for the tasks app."""

    # ── Task queryset ─────────────────────────────────────────────────────────

    def get_task_queryset(self, user):
        """
        Return all tasks in projects where *user* is an active member,
        with counts and related objects pre-fetched.
        """
        logger.debug("ENTER TaskManager.get_task_queryset | user=%s", user.pk)
        try:
            qs = (
                Task.objects.filter(
                    project__members__user=user,
                    project__members__is_active=True,
                )
                .select_related("assignee", "reporter", "column", "project", "parent")
                .prefetch_related("subtasks")
                .annotate(
                    _comment_count=Count("comments", distinct=True),
                    _attachment_count=Count("attachments", distinct=True),
                )
                .distinct()
            )
            logger.debug("EXIT TaskManager.get_task_queryset | user=%s", user.pk)
            return qs
        except Exception as exc:
            logger.error("ERROR TaskManager.get_task_queryset: %s", exc, exc_info=True)
            raise

    def soft_delete_task(self, task) -> None:
        """Soft-delete *task*."""
        logger.debug("ENTER TaskManager.soft_delete_task | task=%s", task.pk)
        try:
            task.soft_delete()
            logger.debug("EXIT TaskManager.soft_delete_task | task=%s deleted", task.pk)
        except Exception as exc:
            logger.error("ERROR TaskManager.soft_delete_task: %s", exc, exc_info=True)
            raise

    # ── Move / Reorder ────────────────────────────────────────────────────────

    def move_task(self, task, column_id: str, new_position: int) -> Task:
        """
        Move *task* to *column_id* at *new_position*, shifting neighbours accordingly.
        Returns the updated task instance.
        """
        logger.debug("ENTER TaskManager.move_task | task=%s -> col=%s pos=%s",
                     task.pk, column_id, new_position)
        try:
            old_column = task.column
            old_position = task.position

            with transaction.atomic():
                # Close gap in source column
                if old_column:
                    Task.objects.filter(
                        column=old_column,
                        position__gt=old_position,
                    ).update(position=F("position") - 1)

                # Make room in target column
                Task.objects.filter(
                    column_id=column_id,
                    position__gte=new_position,
                ).update(position=F("position") + 1)

                task.column_id = column_id
                task.position = new_position
                task.save(update_fields=["column_id", "position", "updated_at"])

            task.refresh_from_db()
            logger.debug("EXIT TaskManager.move_task | task=%s moved", task.pk)
            return task
        except Exception as exc:
            logger.error("ERROR TaskManager.move_task: %s", exc, exc_info=True)
            raise

    def bulk_move_tasks(self, tasks_data: list) -> None:
        """
        Bulk update column and position for multiple tasks.
        *tasks_data* is a list of dicts: [{id, column_id, position}, ...].
        """
        logger.debug("ENTER TaskManager.bulk_move_tasks | count=%d", len(tasks_data))
        try:
            with transaction.atomic():
                for item in tasks_data:
                    Task.objects.filter(id=item["id"]).update(
                        column_id=item.get("column_id"),
                        position=int(item.get("position", 0)),
                    )
            logger.debug("EXIT TaskManager.bulk_move_tasks | %d tasks updated", len(tasks_data))
        except Exception as exc:
            logger.error("ERROR TaskManager.bulk_move_tasks: %s", exc, exc_info=True)
            raise

    # ── Comments ──────────────────────────────────────────────────────────────

    def list_comments(self, task):
        """Return root-level comments for *task* with replies pre-fetched."""
        logger.debug("ENTER TaskManager.list_comments | task=%s", task.pk)
        try:
            qs = (
                Comment.objects.filter(task=task, parent__isnull=True)
                .select_related("author")
                .prefetch_related("replies__author")
            )
            logger.debug("EXIT TaskManager.list_comments | task=%s count=%d", task.pk, qs.count())
            return qs
        except Exception as exc:
            logger.error("ERROR TaskManager.list_comments: %s", exc, exc_info=True)
            raise

    def create_comment(self, task, serializer, user) -> Comment:
        """Save a new comment and log the COMMENTED activity."""
        logger.debug("ENTER TaskManager.create_comment | task=%s user=%s", task.pk, user.pk)
        try:
            comment = serializer.save()
            ActivityLog.objects.create(
                task=task,
                user=user,
                action="COMMENTED",
                description="Added a comment",
            )
            logger.debug("EXIT TaskManager.create_comment | comment=%s", comment.pk)
            return comment
        except Exception as exc:
            logger.error("ERROR TaskManager.create_comment: %s", exc, exc_info=True)
            raise

    # ── Attachments ───────────────────────────────────────────────────────────

    def list_attachments(self, task):
        """Return all attachments for *task*."""
        logger.debug("ENTER TaskManager.list_attachments | task=%s", task.pk)
        try:
            qs = task.attachments.select_related("uploaded_by").all()
            logger.debug("EXIT TaskManager.list_attachments | task=%s count=%d", task.pk, qs.count())
            return qs
        except Exception as exc:
            logger.error("ERROR TaskManager.list_attachments: %s", exc, exc_info=True)
            raise

    def create_attachment(self, task, serializer, user) -> Attachment:
        """Save a new attachment and log the ATTACHMENT_ADDED activity."""
        logger.debug("ENTER TaskManager.create_attachment | task=%s user=%s", task.pk, user.pk)
        try:
            attachment = serializer.save()
            ActivityLog.objects.create(
                task=task,
                user=user,
                action="ATTACHMENT_ADDED",
                new_value={"filename": attachment.filename},
                description=f"Attached {attachment.filename}",
            )
            logger.debug("EXIT TaskManager.create_attachment | attachment=%s", attachment.pk)
            return attachment
        except Exception as exc:
            logger.error("ERROR TaskManager.create_attachment: %s", exc, exc_info=True)
            raise

    # ── Activity log ──────────────────────────────────────────────────────────

    def get_activity(self, task):
        """Return the full activity log for *task*."""
        logger.debug("ENTER TaskManager.get_activity | task=%s", task.pk)
        try:
            qs = ActivityLog.objects.filter(task=task).select_related("user")
            logger.debug("EXIT TaskManager.get_activity | task=%s count=%d", task.pk, qs.count())
            return qs
        except Exception as exc:
            logger.error("ERROR TaskManager.get_activity: %s", exc, exc_info=True)
            raise


# Module-level singleton
task_manager = TaskManager()
