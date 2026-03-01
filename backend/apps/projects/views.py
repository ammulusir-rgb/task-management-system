"""
Views for Projects, Boards, and Columns.
Endpoint definitions only — all business logic lives in managers.py.
"""

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .managers import project_manager
from .permissions import IsProjectAdmin
from .serializers import (
    AddProjectMemberSerializer,
    BoardSerializer,
    ColumnReorderSerializer,
    ColumnSerializer,
    ProjectCreateSerializer,
    ProjectMemberSerializer,
    ProjectSerializer,
)


class ProjectViewSet(viewsets.ModelViewSet):
    """CRUD for projects. Users see only projects they are members of."""

    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return project_manager.get_user_projects(self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return ProjectCreateSerializer
        return ProjectSerializer

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            return [permissions.IsAuthenticated(), IsProjectAdmin()]
        return super().get_permissions()

    def perform_destroy(self, instance):
        project_manager.soft_delete_project(instance)

    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request, pk=None):
        """Archive a project."""
        project = self.get_object()
        updated = project_manager.archive_project(project)
        return Response(ProjectSerializer(updated).data)

    @action(detail=True, methods=["post"], url_path="restore")
    def restore(self, request, pk=None):
        """Restore an archived project."""
        project = self.get_object()
        updated = project_manager.restore_project(project)
        return Response(ProjectSerializer(updated).data)

    # ── Member Management ──────────────────────────────────────────────────────

    @action(detail=True, methods=["get"], url_path="members")
    def list_members(self, request, pk=None):
        """List project members."""
        project = self.get_object()
        members = project_manager.list_members(project)
        return Response(ProjectMemberSerializer(members, many=True).data)

    @action(detail=True, methods=["post"], url_path="members/add")
    def add_member(self, request, pk=None):
        """Add a member to the project."""
        project = self.get_object()
        serializer = AddProjectMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = project_manager.add_member(
            project,
            user_id=str(serializer.validated_data["user_id"]),
            role=serializer.validated_data["role"],
        )
        return Response(ProjectMemberSerializer(member).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"members/(?P<member_id>[^/.]+)")
    def remove_member(self, request, pk=None, member_id=None):
        """Remove a member from the project."""
        project = self.get_object()
        project_manager.remove_member(project, member_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class BoardViewSet(viewsets.ModelViewSet):
    """Board management within a project."""

    serializer_class = BoardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return project_manager.get_boards_queryset(self.request.user)


class ColumnViewSet(viewsets.ModelViewSet):
    """Column management within a board. Includes reorder endpoint."""

    serializer_class = ColumnSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return project_manager.get_columns_queryset(self.request.user)

    @action(detail=False, methods=["post"], url_path="reorder")
    def reorder(self, request):
        """Bulk reorder columns by providing ordered column IDs."""
        serializer = ColumnReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project_manager.reorder_columns(serializer.validated_data["column_ids"])
        return Response({"message": "Columns reordered successfully."})
