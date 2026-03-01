"""
Serializers for Tasks, Comments, Activity Logs, and Attachments.
"""

from django.conf import settings
from django.db import models
from rest_framework import serializers

from apps.common.utils import validate_file_extension, validate_file_size
from apps.users.serializers import UserListSerializer

from .models import ActivityLog, Attachment, Comment, Task, TaskPriority, TaskStatus


class AttachmentSerializer(serializers.ModelSerializer):
    """Serializer for task attachments."""

    uploaded_by = UserListSerializer(read_only=True)
    original_filename = serializers.CharField(source="filename", read_only=True)
    mime_type = serializers.CharField(source="content_type", read_only=True)

    class Meta:
        model = Attachment
        fields = [
            "id",
            "task",
            "file",
            "filename",
            "original_filename",
            "file_size",
            "content_type",
            "mime_type",
            "uploaded_by",
            "created_at",
        ]
        read_only_fields = ["id", "filename", "original_filename", "file_size", "content_type", "mime_type", "uploaded_by", "created_at"]


class AttachmentUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading attachments."""

    class Meta:
        model = Attachment
        fields = ["file"]

    def validate_file(self, value):
        if not validate_file_size(value):
            raise serializers.ValidationError(
                f"File size exceeds the maximum limit of {settings.MAX_UPLOAD_SIZE // (1024*1024)}MB."
            )
        if not validate_file_extension(value.name):
            raise serializers.ValidationError(
                f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_UPLOAD_EXTENSIONS)}"
            )
        return value

    def create(self, validated_data):
        file = validated_data["file"]
        validated_data["filename"] = file.name
        validated_data["file_size"] = file.size
        validated_data["content_type"] = file.content_type or "application/octet-stream"
        validated_data["uploaded_by"] = self.context["request"].user
        validated_data["task_id"] = self.context["task_id"]
        return super().create(validated_data)


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for task comments."""

    author = UserListSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "task",
            "author",
            "parent",
            "content",
            "replies",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "author", "created_at", "updated_at"]

    def get_replies(self, obj):
        """Get only top-level replies (not recursive)."""
        if obj.replies.exists():
            return CommentSerializer(obj.replies.all()[:10], many=True).data
        return []


class CommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating comments."""

    class Meta:
        model = Comment
        fields = ["content", "parent"]

    def create(self, validated_data):
        validated_data["author"] = self.context["request"].user
        validated_data["task_id"] = self.context["task_id"]
        return super().create(validated_data)


class ActivityLogSerializer(serializers.ModelSerializer):
    """Serializer for activity log entries."""

    user = UserListSerializer(read_only=True)

    class Meta:
        model = ActivityLog
        fields = [
            "id",
            "task",
            "user",
            "action",
            "field_name",
            "old_value",
            "new_value",
            "description",
            "created_at",
        ]


class SubtaskSerializer(serializers.ModelSerializer):
    """Lightweight serializer for subtask display."""

    assignee = UserListSerializer(read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "task_key",
            "title",
            "status",
            "priority",
            "assignee",
            "due_date",
        ]


class TaskSerializer(serializers.ModelSerializer):
    """Full serializer for task detail view."""

    assignee = UserListSerializer(read_only=True)
    reporter = UserListSerializer(read_only=True)
    subtasks = SubtaskSerializer(many=True, read_only=True)
    comment_count = serializers.SerializerMethodField()
    attachment_count = serializers.SerializerMethodField()
    is_overdue = serializers.ReadOnlyField()
    subtask_count = serializers.ReadOnlyField()
    completed_subtask_count = serializers.ReadOnlyField()
    column_name = serializers.CharField(source="column.name", read_only=True, default="")
    board = serializers.SerializerMethodField()
    actual_hours = serializers.DecimalField(
        source="logged_hours", max_digits=7, decimal_places=2, read_only=True
    )
    story_points = serializers.IntegerField(read_only=True, default=None)

    class Meta:
        model = Task
        fields = [
            "id",
            "project",
            "column",
            "column_name",
            "board",
            "parent",
            "title",
            "description",
            "task_number",
            "task_key",
            "status",
            "priority",
            "assignee",
            "reporter",
            "due_date",
            "started_at",
            "completed_at",
            "estimated_hours",
            "logged_hours",
            "actual_hours",
            "story_points",
            "tags",
            "position",
            "subtasks",
            "comment_count",
            "attachment_count",
            "is_overdue",
            "subtask_count",
            "completed_subtask_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "task_number",
            "task_key",
            "started_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]

    def get_comment_count(self, obj) -> int:
        return getattr(obj, "_comment_count", obj.comments.count())

    def get_attachment_count(self, obj) -> int:
        return getattr(obj, "_attachment_count", obj.attachments.count())

    def get_board(self, obj) -> str:
        if obj.column and obj.column.board_id:
            return str(obj.column.board_id)
        return ""


class TaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tasks."""

    class Meta:
        model = Task
        fields = [
            "project",
            "column",
            "parent",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "due_date",
            "estimated_hours",
            "tags",
        ]

    def create(self, validated_data):
        validated_data["reporter"] = self.context["request"].user
        # Set position to end of column
        column = validated_data.get("column")
        if column:
            max_pos = Task.objects.filter(column=column).aggregate(
                max_pos=models.Max("position")
            )["max_pos"]
            validated_data["position"] = (max_pos or 0) + 1
        return super().create(validated_data)


class TaskListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for task list/board views."""

    assignee = UserListSerializer(read_only=True)
    subtask_count = serializers.ReadOnlyField()
    completed_subtask_count = serializers.ReadOnlyField()
    comment_count = serializers.SerializerMethodField()
    is_overdue = serializers.ReadOnlyField()

    class Meta:
        model = Task
        fields = [
            "id",
            "task_key",
            "title",
            "status",
            "priority",
            "assignee",
            "due_date",
            "tags",
            "position",
            "column",
            "subtask_count",
            "completed_subtask_count",
            "comment_count",
            "is_overdue",
            "created_at",
        ]

    def get_comment_count(self, obj) -> int:
        return getattr(obj, "_comment_count", 0)


class TaskMoveSerializer(serializers.Serializer):
    """Serializer for moving a task to a different column/position."""

    column_id = serializers.UUIDField()
    position = serializers.IntegerField(min_value=0)


class BulkTaskMoveSerializer(serializers.Serializer):
    """Serializer for bulk moving tasks (drag-and-drop reorder)."""

    tasks = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField()),
        min_length=1,
    )
