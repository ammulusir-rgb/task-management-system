"""
Views for Tasks, Comments, and Attachments.
Endpoint definitions only — all business logic lives in managers.py.
"""

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.pagination import SmallResultsSetPagination

from .filters import TaskFilter
from .managers import task_manager
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
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = TaskFilter
    search_fields = ["title", "description", "task_key"]
    ordering_fields = ["created_at", "updated_at", "due_date", "priority", "position"]
    ordering = ["position", "-created_at"]

    def get_queryset(self):
        return task_manager.get_task_queryset(self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return TaskCreateSerializer
        if self.action == "list":
            return TaskListSerializer
        return TaskSerializer

    def perform_destroy(self, instance):
        task_manager.soft_delete_task(instance)

    # ── Move / Reorder ──

    @action(detail=True, methods=["post"], url_path="move")
    def move(self, request, pk=None):
        task = self.get_object()
        serializer = TaskMoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = task_manager.move_task(
            task,
            str(serializer.validated_data["column_id"]),
            serializer.validated_data["position"],
        )
        return Response(TaskSerializer(updated).data)

    @action(detail=False, methods=["post"], url_path="bulk-move")
    def bulk_move(self, request):
        serializer = BulkTaskMoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task_manager.bulk_move_tasks(serializer.validated_data["tasks"])
        return Response({"message": "Tasks reordered successfully."})

    # ── Comments ──

    @action(detail=True, methods=["get", "post"], url_path="comments")
    def comments(self, request, pk=None):
        task = self.get_object()
        if request.method == "GET":
            qs = task_manager.list_comments(task)
            paginator = SmallResultsSetPagination()
            page = paginator.paginate_queryset(qs, request)
            return paginator.get_paginated_response(CommentSerializer(page, many=True).data)
        serializer = CommentCreateSerializer(
            data=request.data,
            context={"request": request, "task_id": task.id},
        )
        serializer.is_valid(raise_exception=True)
        comment = task_manager.create_comment(task, serializer, request.user)
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)

    # ── Attachments ──

    @action(detail=True, methods=["get", "post"], url_path="attachments")
    def attachments(self, request, pk=None):
        task = self.get_object()
        if request.method == "GET":
            return Response(AttachmentSerializer(task_manager.list_attachments(task), many=True).data)
        serializer = AttachmentUploadSerializer(
            data=request.data,
            context={"request": request, "task_id": task.id},
        )
        serializer.is_valid(raise_exception=True)
        att = task_manager.create_attachment(task, serializer, request.user)
        return Response(AttachmentSerializer(att).data, status=status.HTTP_201_CREATED)

    # ── Activity Log ──

    @action(detail=True, methods=["get"], url_path="activity")
    def activity(self, request, pk=None):
        task = self.get_object()
        qs = task_manager.get_activity(task)
        paginator = SmallResultsSetPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(ActivityLogSerializer(page, many=True).data)
