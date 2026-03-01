"""
Permissions for project-scoped views.
"""

from rest_framework.permissions import BasePermission

from .models import ProjectMember, ProjectMemberRole


class IsProjectMember(BasePermission):
    """Allow access only to project members."""

    message = "You must be a member of this project."

    def has_object_permission(self, request, view, obj) -> bool:
        project = obj if hasattr(obj, "members") else getattr(obj, "project", None)
        if project is None:
            return False
        return ProjectMember.objects.filter(
            project=project,
            user=request.user,
            is_active=True,
        ).exists()


class IsProjectAdmin(BasePermission):
    """Allow access only to project admins."""

    message = "Project admin access required."

    def has_object_permission(self, request, view, obj) -> bool:
        project = obj if hasattr(obj, "members") else getattr(obj, "project", None)
        if project is None:
            return False
        return ProjectMember.objects.filter(
            project=project,
            user=request.user,
            role=ProjectMemberRole.ADMIN,
            is_active=True,
        ).exists()
