"""
Serializers for Organizations.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.users.serializers import UserListSerializer

from .models import Organization, OrganizationMember, OrganizationRole, Team, TeamMember

User = get_user_model()


class OrganizationSerializer(serializers.ModelSerializer):
    """Full serializer for Organization CRUD."""

    member_count = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "logo",
            "website",
            "created_by",
            "created_by_name",
            "is_active",
            "member_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_by", "created_at", "updated_at"]

    def get_member_count(self, obj) -> int:
        return obj.members.filter(is_active=True).count()


class OrganizationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an organization."""

    class Meta:
        model = Organization
        fields = ["name", "description", "logo", "website"]

    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["created_by"] = user
        org = Organization.objects.create(**validated_data)

        # Auto-add creator as Owner
        OrganizationMember.objects.create(
            organization=org,
            user=user,
            role=OrganizationRole.OWNER,
            invited_by=user,
        )
        return org


class OrganizationMemberSerializer(serializers.ModelSerializer):
    """Serializer for organization members."""

    user = UserListSerializer(read_only=True)
    invited_by_name = serializers.CharField(
        source="invited_by.full_name", read_only=True, default=""
    )

    class Meta:
        model = OrganizationMember
        fields = [
            "id",
            "organization",
            "user",
            "role",
            "invited_by",
            "invited_by_name",
            "invited_at",
            "joined_at",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "organization", "invited_by", "invited_at", "created_at"]


class AddMemberSerializer(serializers.Serializer):
    """Serializer for adding a member to an organization."""

    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=OrganizationRole.choices,
        default=OrganizationRole.MEMBER,
    )

    def validate_email(self, value: str) -> str:
        return value.lower().strip()


class UpdateMemberRoleSerializer(serializers.Serializer):
    """Serializer for updating a member's role."""

    role = serializers.ChoiceField(choices=OrganizationRole.choices)


class TeamMemberSerializer(serializers.ModelSerializer):
    """Serializer for team members."""

    user = UserListSerializer(read_only=True)

    class Meta:
        model = TeamMember
        fields = ["id", "team", "user", "is_lead", "created_at"]
        read_only_fields = ["id", "team", "created_at"]


class TeamSerializer(serializers.ModelSerializer):
    """Full serializer for Team CRUD."""

    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = [
            "id",
            "organization",
            "name",
            "description",
            "created_by",
            "member_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def get_member_count(self, obj) -> int:
        return obj.members.count()


class TeamCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a team."""

    class Meta:
        model = Team
        fields = ["organization", "name", "description"]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class AddTeamMemberSerializer(serializers.Serializer):
    """Serializer for adding a member to a team."""

    user_id = serializers.UUIDField()
    is_lead = serializers.BooleanField(default=False)
