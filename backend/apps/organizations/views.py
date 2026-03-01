"""
Views for Organization management.
Endpoint definitions only — all business logic lives in managers.py.
"""

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .managers import organization_manager
from .permissions import IsOrgAdmin
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


class OrganizationViewSet(viewsets.ModelViewSet):
    """CRUD for organizations. Users see only organizations they belong to."""

    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return organization_manager.get_user_organizations(self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return OrganizationCreateSerializer
        return OrganizationSerializer

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            return [permissions.IsAuthenticated(), IsOrgAdmin()]
        return super().get_permissions()

    def perform_destroy(self, instance):
        organization_manager.soft_delete_organization(instance)

    # ── Member Management ──────────────────────────────────────────────────────

    @action(detail=True, methods=["get"], url_path="members")
    def list_members(self, request, pk=None):
        """List all members of an organization."""
        org = self.get_object()
        members = organization_manager.list_members(org)
        return Response(OrganizationMemberSerializer(members, many=True).data)

    @action(detail=True, methods=["post"], url_path="members/add")
    def add_member(self, request, pk=None):
        """Add a member to the organization by email."""
        org = self.get_object()
        serializer = AddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = organization_manager.add_member(
            org,
            email=serializer.validated_data["email"],
            role=serializer.validated_data["role"],
            invited_by=request.user,
        )
        return Response(OrganizationMemberSerializer(member).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], url_path=r"members/(?P<member_id>[^/.]+)/role")
    def update_member_role(self, request, pk=None, member_id=None):
        """Update a member's role."""
        org = self.get_object()
        serializer = UpdateMemberRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = organization_manager.update_member_role(
            org, member_id, serializer.validated_data["role"]
        )
        return Response(OrganizationMemberSerializer(member).data)

    @action(detail=True, methods=["delete"], url_path=r"members/(?P<member_id>[^/.]+)")
    def remove_member(self, request, pk=None, member_id=None):
        """Remove a member from the organization."""
        org = self.get_object()
        organization_manager.remove_member(org, member_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TeamViewSet(viewsets.ModelViewSet):
    """CRUD for teams within an organization."""

    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return organization_manager.get_teams_queryset(
            self.request.user,
            org_id=self.request.query_params.get("organization"),
        )

    def get_serializer_class(self):
        if self.action == "create":
            return TeamCreateSerializer
        return TeamSerializer

    @action(detail=True, methods=["get"], url_path="members")
    def list_members(self, request, pk=None):
        """List all members of a team."""
        team = self.get_object()
        members = organization_manager.list_team_members(team)
        return Response(TeamMemberSerializer(members, many=True).data)

    @action(detail=True, methods=["post"], url_path="members/add")
    def add_member(self, request, pk=None):
        """Add a member to the team."""
        team = self.get_object()
        serializer = AddTeamMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = organization_manager.add_team_member(
            team,
            user_id=serializer.validated_data["user_id"],
            is_lead=serializer.validated_data.get("is_lead", False),
        )
        return Response(TeamMemberSerializer(member).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"members/(?P<member_id>[^/.]+)")
    def remove_member(self, request, pk=None, member_id=None):
        """Remove a member from the team."""
        team = self.get_object()
        organization_manager.remove_team_member(team, member_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
