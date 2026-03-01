"""
Views for Tasks, Comments, and Attachments.
"""

from django.db import transaction
from django.db.models import Count
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.pagination import SmallResultsSetPagination

from .filters import TaskFilter
from .models import ActivityLog, Attachment, Comment, Task, TaskStatus
from .serializers import (
    ActivityLogSerializer,
    AttachmentSerializer,
    AttachmentUploadSerializer,
    BulkTaskMoveSerializer,
    CommentCreateSerializer,
    CommentSerializer,
    TaskCreateSerializer,
    TaskListSerializer,
    TaskMoveSerializer,
    TaskSerializer,
)


class TaskViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for tasks with filtering, search, and ordering.
    Includes endpoints for moving tasks, managing comments, and attachments.
    """

    permission_classes = [permissions.IsAuthenticated]
    filterset_class = TaskFilter
    search_fields = ["title", "description", "task_key"]
    ordering_fields = ["created_at", "updated_at", "due_date", "priority", "position"]
    ordering = ["position", "-created_at"]

    def get_queryset(self):
        return (
            Task.objects.filter(
                project__members__user=self.request.user,
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

    def get_serializer_class(self):
        if self.action == "create":
            return TaskCreateSerializer
        if self.action == "list":
            return TaskListSerializer
        return TaskSerializer

    def perform_destroy(self, instance):
        """Soft delete the task."""
        instance.soft_delete()

    # ── Move / Reorder ──

    @action(detail=True, methods=["post"], url_path="move")
    def move(self, request, pk=None):
        """Move a task to a different column and/or position."""
        task = self.get_object()
        serializer = TaskMoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        column_id = serializer.validated_data["column_id"]
        new_position = serializer.validated_data["position"]

        old_column = task.column
        old_position = task.position

        with transaction.atomic():
            # Update positions in the source column (close gap)
            if old_column:
                Task.objects.filter(
                    column=old_column,
                    position__gt=old_position,
                ).update(position=models.F("position") - 1)

            # Make room in the target column
            Task.objects.filter(
                column_id=column_id,
                position__gte=new_position,
            ).update(position=models.F("position") + 1)

            task.column_id = column_id
            task.position = new_position
            task.save(update_fields=["column_id", "position", "updated_at"])

        return Response(TaskSerializer(task).data)

    @action(detail=False, methods=["post"], url_path="bulk-move")
    def bulk_move(self, request):
        """Bulk move tasks — used for drag-and-drop reordering."""
        serializer = BulkTaskMoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            for item in serializer.validated_data["tasks"]:
                Task.objects.filter(id=item["id"]).update(
                    column_id=item.get("column_id"),
                    position=int(item.get("position", 0)),
                )

        return Response({"message": "Tasks reordered successfully."})

    # ── Comments ──

    @action(detail=True, methods=["get", "post"], url_path="comments")
    def comments(self, request, pk=None):
        task = self.get_object()

        if request.method == "GET":
            comments = (
                Comment.objects.filter(task=task, parent__isnull=True)
                .select_related("author")
                .prefetch_related("replies__author")
            )
            paginator = SmallResultsSetPagination()
            page = paginator.paginate_queryset(comments, request)
            serializer = CommentSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        # POST — create comment
        serializer = CommentCreateSerializer(
            data=request.data,
            context={"request": request, "task_id": task.id},
        )
        serializer.is_valid(raise_exception=True)
        comment = serializer.save()

        # Log activity
        ActivityLog.objects.create(
            task=task,
            user=request.user,
            action="COMMENTED",
            description=f"Added a comment",
        )

        return Response(
            CommentSerializer(comment).data,
            status=status.HTTP_201_CREATED,
        )

    # ── Attachments ──

    @action(detail=True, methods=["get", "post"], url_path="attachments")
    def attachments(self, request, pk=None):
        task = self.get_object()

        if request.method == "GET":
            attachments = task.attachments.select_related("uploaded_by").all()
            serializer = AttachmentSerializer(attachments, many=True)
            return Response(serializer.data)

        # POST — upload attachment
        serializer = AttachmentUploadSerializer(
            data=request.data,
            context={"request": request, "task_id": task.id},
        )
        serializer.is_valid(raise_exception=True)
        attachment = serializer.save()

        # Log activity
        ActivityLog.objects.create(
            task=task,
            user=request.user,
            action="ATTACHMENT_ADDED",
            new_value={"filename": attachment.filename},
            description=f"Attached {attachment.filename}",
        )

        return Response(
            AttachmentSerializer(attachment).data,
            status=status.HTTP_201_CREATED,
        )

    # ── Activity Log ──

    @action(detail=True, methods=["get"], url_path="activity")
    def activity(self, request, pk=None):
        """Get the activity log for a task."""
        task = self.get_object()
        activities = ActivityLog.objects.filter(task=task).select_related("user")
        paginator = SmallResultsSetPagination()
        page = paginator.paginate_queryset(activities, request)
        serializer = ActivityLogSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
