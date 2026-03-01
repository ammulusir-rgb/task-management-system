"""
Task, Comment, ActivityLog, Tag, and Attachment models.
Core domain models for the task management system.
"""

import uuid

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models

from apps.common.mixins import OrderableMixin, SoftDeleteManager, SoftDeleteMixin, TimestampMixin
from apps.common.utils import file_upload_path


class TaskStatus(models.TextChoices):
    BACKLOG = "backlog", "Backlog"
    TODO = "todo", "To Do"
    IN_PROGRESS = "in_progress", "In Progress"
    IN_REVIEW = "in_review", "In Review"
    DONE = "done", "Done"
    CANCELLED = "cancelled", "Cancelled"


class TaskPriority(models.TextChoices):
    CRITICAL = "critical", "Critical"
    HIGH = "high", "High"
    MEDIUM = "medium", "Medium"
    LOW = "low", "Low"


class Task(TimestampMixin, SoftDeleteMixin, OrderableMixin, models.Model):
    """
    Core Task model with full lifecycle support.
    Supports subtasks via self-referential FK, soft delete,
    time tracking, tags, and positional ordering within columns.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    column = models.ForeignKey(
        "projects.Column",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subtasks",
    )

    # Core fields
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, default="")
    task_number = models.PositiveIntegerField(
        editable=False,
        help_text="Auto-incrementing number within the project",
    )
    task_key = models.CharField(
        max_length=20,
        editable=False,
        db_index=True,
        help_text="Project prefix + number, e.g., PRJ-42",
    )

    # Status & Priority
    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.BACKLOG,
        db_index=True,
    )
    priority = models.CharField(
        max_length=20,
        choices=TaskPriority.choices,
        default=TaskPriority.MEDIUM,
        db_index=True,
    )

    # People
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="reported_tasks",
    )

    # Dates
    due_date = models.DateTimeField(null=True, blank=True, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Time tracking
    estimated_hours = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
    )
    logged_hours = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=0,
    )

    # Tags
    tags = ArrayField(
        models.CharField(max_length=50),
        blank=True,
        default=list,
    )

    class Meta:
        ordering = ["position", "-created_at"]
        indexes = [
            models.Index(fields=["project", "status"], name="idx_task_project_status"),
            models.Index(fields=["column", "position"], name="idx_task_column_pos"),
            models.Index(fields=["assignee", "status"], name="idx_task_assignee_status"),
            models.Index(fields=["due_date"], name="idx_task_due_date"),
            models.Index(fields=["priority"], name="idx_task_priority"),
            models.Index(fields=["task_key"], name="idx_task_key"),
            models.Index(
                fields=["project"],
                name="idx_task_active",
                condition=models.Q(deleted_at__isnull=True),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.task_key}: {self.title}"

    def save(self, *args, **kwargs):
        if not self.task_number:
            # Get the next task number for this project
            last_task = (
                Task.all_objects.filter(project=self.project)
                .order_by("-task_number")
                .values_list("task_number", flat=True)
                .first()
            )
            self.task_number = (last_task or 0) + 1
            self.task_key = f"{self.project.prefix}-{self.task_number}"
        super().save(*args, **kwargs)

    @property
    def is_overdue(self) -> bool:
        if self.due_date and self.status not in (TaskStatus.DONE, TaskStatus.CANCELLED):
            from django.utils import timezone
            return self.due_date < timezone.now()
        return False

    @property
    def subtask_count(self) -> int:
        return self.subtasks.count()

    @property
    def completed_subtask_count(self) -> int:
        return self.subtasks.filter(status=TaskStatus.DONE).count()


class Comment(TimestampMixin, models.Model):
    """
    Comments on tasks. Supports threaded replies.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="task_comments",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
    )
    content = models.TextField()

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["task", "created_at"], name="idx_comment_task_date"),
        ]

    def __str__(self) -> str:
        return f"Comment by {self.author.email} on {self.task.task_key}"


class ActivityAction(models.TextChoices):
    CREATED = "created", "Created"
    UPDATED = "updated", "Updated"
    STATUS_CHANGED = "status_changed", "Status Changed"
    PRIORITY_CHANGED = "priority_changed", "Priority Changed"
    ASSIGNED = "assigned", "Assigned"
    UNASSIGNED = "unassigned", "Unassigned"
    COMMENTED = "commented", "Commented"
    ATTACHMENT_ADDED = "attachment_added", "Attachment Added"
    ATTACHMENT_REMOVED = "attachment_removed", "Attachment Removed"
    MOVED = "moved", "Moved"
    DELETED = "deleted", "Deleted"
    RESTORED = "restored", "Restored"


class ActivityLog(models.Model):
    """
    Tracks all changes made to tasks for audit and activity feed.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="activity_logs",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="activity_logs",
    )
    action = models.CharField(
        max_length=30,
        choices=ActivityAction.choices,
    )
    field_name = models.CharField(max_length=50, blank=True, default="")
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["task", "-created_at"], name="idx_activity_task_date"),
        ]

    def __str__(self) -> str:
        return f"{self.action} on {self.task.task_key} by {self.user}"


class Attachment(TimestampMixin, models.Model):
    """
    File attachments on tasks.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file = models.FileField(upload_to=file_upload_path)
    filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    content_type = models.CharField(max_length=100)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_attachments",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.filename} on {self.task.task_key}"
