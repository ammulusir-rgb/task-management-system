"""
Views for Organization management.
"""

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Organization, OrganizationMember, OrganizationRole, Team, TeamMember
from .permissions import IsOrgAdmin, IsOrgMember
from .serializers import (
    AddMemberSerializer,
    AddTeamMemberSerializer,
    OrganizationCreateSerializer,
    OrganizationMemberSerializer,
    OrganizationSerializer,
    TeamCreateSerializer,
    TeamMemberSerializer,
    TeamSerializer,
    UpdateMemberRoleSerializer,
)

User = get_user_model()


class OrganizationViewSet(viewsets.ModelViewSet):
    """
    CRUD for organizations.
    Users see only organizations they belong to.
    """

    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        return (
            Organization.objects.filter(
                members__user=self.request.user,
                members__is_active=True,
            )
            .select_related("created_by")
            .prefetch_related("members")
            .distinct()
        )

    def get_serializer_class(self):
        if self.action == "create":
            return OrganizationCreateSerializer
        return OrganizationSerializer

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            return [permissions.IsAuthenticated(), IsOrgAdmin()]
        return super().get_permissions()

    def perform_destroy(self, instance):
        """Soft-delete: deactivate instead of hard delete."""
        instance.is_active = False
        instance.save(update_fields=["is_active"])

    # ── Member Management ──

    @action(detail=True, methods=["get"], url_path="members")
    def list_members(self, request, pk=None):
        """List all members of an organization."""
        org = self.get_object()
        members = OrganizationMember.objects.filter(
            organization=org
        ).select_related("user", "invited_by")

        serializer = OrganizationMemberSerializer(members, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="members/add")
    def add_member(self, request, pk=None):
        """Add a member to the organization by email."""
        org = self.get_object()
        serializer = AddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        role = serializer.validated_data["role"]

        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            return Response(
                {"error": {"code": "user_not_found", "message": "No active user found with that email."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        if OrganizationMember.objects.filter(organization=org, user=user).exists():
            return Response(
                {"error": {"code": "already_member", "message": "User is already a member."}},
                status=status.HTTP_409_CONFLICT,
            )

        member = OrganizationMember.objects.create(
            organization=org,
            user=user,
            role=role,
            invited_by=request.user,
            joined_at=timezone.now(),
        )

        return Response(
            OrganizationMemberSerializer(member).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["patch"], url_path=r"members/(?P<member_id>[^/.]+)/role")
    def update_member_role(self, request, pk=None, member_id=None):
        """Update a member's role."""
        org = self.get_object()
        serializer = UpdateMemberRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            member = OrganizationMember.objects.get(id=member_id, organization=org)
        except OrganizationMember.DoesNotExist:
            return Response(
                {"error": {"code": "not_found", "message": "Member not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Prevent demoting the last owner
        if (
            member.role == OrganizationRole.OWNER
            and serializer.validated_data["role"] != OrganizationRole.OWNER
        ):
            owner_count = OrganizationMember.objects.filter(
                organization=org, role=OrganizationRole.OWNER, is_active=True
            ).count()
            if owner_count <= 1:
                return Response(
                    {"error": {"code": "last_owner", "message": "Cannot remove the last owner."}},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        member.role = serializer.validated_data["role"]
        member.save(update_fields=["role"])

        return Response(OrganizationMemberSerializer(member).data)

    @action(detail=True, methods=["delete"], url_path=r"members/(?P<member_id>[^/.]+)")
    def remove_member(self, request, pk=None, member_id=None):
        """Remove a member from the organization."""
        org = self.get_object()

        try:
            member = OrganizationMember.objects.get(id=member_id, organization=org)
        except OrganizationMember.DoesNotExist:
            return Response(
                {"error": {"code": "not_found", "message": "Member not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Prevent removing the last owner
        if member.role == OrganizationRole.OWNER:
            owner_count = OrganizationMember.objects.filter(
                organization=org, role=OrganizationRole.OWNER, is_active=True
            ).count()
            if owner_count <= 1:
                return Response(
                    {"error": {"code": "last_owner", "message": "Cannot remove the last owner."}},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        member.is_active = False
        member.save(update_fields=["is_active"])

        return Response(status=status.HTTP_204_NO_CONTENT)


class TeamViewSet(viewsets.ModelViewSet):
    """
    CRUD for teams within an organization.
    Users see only teams in orgs they belong to.
    """

    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Team.objects.filter(
            organization__members__user=self.request.user,
            organization__members__is_active=True,
        ).select_related("organization", "created_by").distinct()
        org_id = self.request.query_params.get("organization")
        if org_id:
            qs = qs.filter(organization_id=org_id)
        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return TeamCreateSerializer
        return TeamSerializer

    @action(detail=True, methods=["get"], url_path="members")
    def list_members(self, request, pk=None):
        """List all members of a team."""
        team = self.get_object()
        members = TeamMember.objects.filter(team=team).select_related("user")
        serializer = TeamMemberSerializer(members, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="members/add")
    def add_member(self, request, pk=None):
        """Add a member to the team."""
        team = self.get_object()
        serializer = AddTeamMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data["user_id"]
        is_lead = serializer.validated_data.get("is_lead", False)

        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return Response(
                {"error": {"code": "user_not_found", "message": "User not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        if TeamMember.objects.filter(team=team, user=user).exists():
            return Response(
                {"error": {"code": "already_member", "message": "User is already a team member."}},
                status=status.HTTP_409_CONFLICT,
            )

        member = TeamMember.objects.create(team=team, user=user, is_lead=is_lead)
        return Response(
            TeamMemberSerializer(member).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["delete"], url_path=r"members/(?P<member_id>[^/.]+)")
    def remove_member(self, request, pk=None, member_id=None):
        """Remove a member from the team."""
        team = self.get_object()
        try:
            member = TeamMember.objects.get(id=member_id, team=team)
        except TeamMember.DoesNotExist:
            return Response(
                {"error": {"code": "not_found", "message": "Member not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
