"""
Permissions for organization-scoped views.
"""

from rest_framework.permissions import BasePermission

from .models import OrganizationMember, OrganizationRole


class IsOrgMember(BasePermission):
    """Allow access only to organization members."""

    message = "You must be a member of this organization."

    def has_object_permission(self, request, view, obj) -> bool:
        return OrganizationMember.objects.filter(
            organization=obj,
            user=request.user,
            is_active=True,
        ).exists()


class IsOrgAdmin(BasePermission):
    """Allow access only to organization admins/owners."""

    message = "Organization admin access required."

    def has_object_permission(self, request, view, obj) -> bool:
        return OrganizationMember.objects.filter(
            organization=obj,
            user=request.user,
            role__in=[OrganizationRole.OWNER, OrganizationRole.ADMIN],
            is_active=True,
        ).exists()


class IsOrgOwner(BasePermission):
    """Allow access only to organization owners."""

    message = "Organization owner access required."

    def has_object_permission(self, request, view, obj) -> bool:
        return OrganizationMember.objects.filter(
            organization=obj,
            user=request.user,
            role=OrganizationRole.OWNER,
            is_active=True,
        ).exists()
