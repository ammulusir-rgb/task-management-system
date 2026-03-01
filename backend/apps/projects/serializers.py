"""
Serializers for Projects, Boards, and Columns.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.users.serializers import UserListSerializer

from .models import Board, Column, Project, ProjectMember, ProjectMemberRole

User = get_user_model()


class ColumnSerializer(serializers.ModelSerializer):
    """Serializer for board columns."""

    task_count = serializers.SerializerMethodField()

    class Meta:
        model = Column
        fields = [
            "id",
            "board",
            "name",
            "color",
            "position",
            "wip_limit",
            "is_done_column",
            "task_count",
        ]
        read_only_fields = ["id", "board"]

    def get_task_count(self, obj) -> int:
        return getattr(obj, "_task_count", obj.tasks.count())


class ColumnReorderSerializer(serializers.Serializer):
    """Serializer for reordering columns."""

    column_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
    )


class BoardSerializer(serializers.ModelSerializer):
    """Serializer for boards with nested columns."""

    columns = ColumnSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = ["id", "project", "name", "is_default", "columns", "created_at"]
        read_only_fields = ["id", "project", "created_at"]


class ProjectMemberSerializer(serializers.ModelSerializer):
    """Serializer for project members."""

    user = UserListSerializer(read_only=True)

    class Meta:
        model = ProjectMember
        fields = ["id", "project", "user", "role", "is_active", "created_at"]
        read_only_fields = ["id", "project", "created_at"]


class ProjectSerializer(serializers.ModelSerializer):
    """Full serializer for project CRUD."""

    member_count = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "organization",
            "organization_name",
            "name",
            "slug",
            "description",
            "status",
            "prefix",
            "created_by",
            "created_by_name",
            "start_date",
            "end_date",
            "member_count",
            "task_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_by", "created_at", "updated_at"]

    def get_member_count(self, obj) -> int:
        return obj.members.filter(is_active=True).count()

    def get_task_count(self, obj) -> int:
        return getattr(obj, "_task_count", 0)


class ProjectCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a project."""

    class Meta:
        model = Project
        fields = ["organization", "name", "description", "prefix", "start_date", "end_date"]

    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["created_by"] = user
        project = Project.objects.create(**validated_data)

        # Auto-add creator as project admin
        ProjectMember.objects.create(
            project=project,
            user=user,
            role=ProjectMemberRole.ADMIN,
        )
        return project


class AddProjectMemberSerializer(serializers.Serializer):
    """Serializer for adding a member to a project."""

    user_id = serializers.UUIDField()
    role = serializers.ChoiceField(
        choices=ProjectMemberRole.choices,
        default=ProjectMemberRole.MEMBER,
    )
