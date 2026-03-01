"""
Views for Projects, Boards, and Columns.
"""

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Board, Column, Project, ProjectMember, ProjectMemberRole, ProjectStatus
from .permissions import IsProjectAdmin, IsProjectMember
from .serializers import (
    AddProjectMemberSerializer,
    BoardSerializer,
    ColumnReorderSerializer,
    ColumnSerializer,
    ProjectCreateSerializer,
    ProjectMemberSerializer,
    ProjectSerializer,
)

User = get_user_model()


class ProjectViewSet(viewsets.ModelViewSet):
    """
    CRUD for projects. Users see only projects they are members of.
    """

    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        return (
            Project.objects.filter(
                members__user=self.request.user,
                members__is_active=True,
            )
            .select_related("organization", "created_by")
            .annotate(_task_count=Count("tasks"))
            .distinct()
        )

    def get_serializer_class(self):
        if self.action == "create":
            return ProjectCreateSerializer
        return ProjectSerializer

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            return [permissions.IsAuthenticated(), IsProjectAdmin()]
        return super().get_permissions()

    def perform_destroy(self, instance):
        instance.status = ProjectStatus.DELETED
        instance.soft_delete()

    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request, pk=None):
        """Archive a project."""
        project = self.get_object()
        project.status = ProjectStatus.ARCHIVED
        project.save(update_fields=["status"])
        return Response(ProjectSerializer(project).data)

    @action(detail=True, methods=["post"], url_path="restore")
    def restore(self, request, pk=None):
        """Restore an archived project."""
        project = self.get_object()
        project.status = ProjectStatus.ACTIVE
        project.save(update_fields=["status"])
        return Response(ProjectSerializer(project).data)

    # ── Member Management ──

    @action(detail=True, methods=["get"], url_path="members")
    def list_members(self, request, pk=None):
        """List project members."""
        project = self.get_object()
        members = ProjectMember.objects.filter(
            project=project
        ).select_related("user")
        serializer = ProjectMemberSerializer(members, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="members/add")
    def add_member(self, request, pk=None):
        """Add a member to the project."""
        project = self.get_object()
        serializer = AddProjectMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data["user_id"]
        role = serializer.validated_data["role"]

        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return Response(
                {"error": {"code": "user_not_found", "message": "User not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        if ProjectMember.objects.filter(project=project, user=user).exists():
            return Response(
                {"error": {"code": "already_member", "message": "User is already a member."}},
                status=status.HTTP_409_CONFLICT,
            )

        member = ProjectMember.objects.create(
            project=project,
            user=user,
            role=role,
        )
        return Response(
            ProjectMemberSerializer(member).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["delete"], url_path=r"members/(?P<member_id>[^/.]+)")
    def remove_member(self, request, pk=None, member_id=None):
        """Remove a member from the project."""
        project = self.get_object()
        try:
            member = ProjectMember.objects.get(id=member_id, project=project)
        except ProjectMember.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        member.is_active = False
        member.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class BoardViewSet(viewsets.ModelViewSet):
    """
    Board management within a project.
    """

    serializer_class = BoardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Board.objects.filter(
                project__members__user=self.request.user,
                project__members__is_active=True,
            )
            .select_related("project")
            .prefetch_related("columns")
            .distinct()
        )


class ColumnViewSet(viewsets.ModelViewSet):
    """
    Column management within a board.
    Includes reorder endpoint for drag-and-drop.
    """

    serializer_class = ColumnSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Column.objects.filter(
                board__project__members__user=self.request.user,
                board__project__members__is_active=True,
            )
            .select_related("board", "board__project")
            .distinct()
        )

    @action(detail=False, methods=["post"], url_path="reorder")
    def reorder(self, request):
        """Bulk reorder columns by providing ordered column IDs."""
        serializer = ColumnReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        column_ids = serializer.validated_data["column_ids"]

        with transaction.atomic():
            for position, column_id in enumerate(column_ids):
                Column.objects.filter(id=column_id).update(position=position)

        return Response({"message": "Columns reordered successfully."})
