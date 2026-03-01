"""
Custom permissions for user-related views.
"""

from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Allow access only to users with ADMIN role."""

    message = "Admin access required."

    def has_permission(self, request, view) -> bool:
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "ADMIN"
        )


class IsManagerOrAbove(BasePermission):
    """Allow access to ADMIN and MANAGER roles."""

    message = "Manager or Admin access required."

    def has_permission(self, request, view) -> bool:
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ("ADMIN", "MANAGER")
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Allow access to the object owner or admins.
    Requires the object to have a user-linking field.
    """

    message = "You do not have permission to perform this action."
    owner_field = "user"

    def has_object_permission(self, request, view, obj) -> bool:
        if request.user.role == "ADMIN":
            return True

        owner = getattr(obj, self.owner_field, None)
        if owner is None:
            # Try common field variations
            for field in ("user", "created_by", "owner", "author"):
                owner = getattr(obj, field, None)
                if owner is not None:
                    break

        if owner is None:
            return False

        return owner == request.user


class IsSelf(BasePermission):
    """Allow users to access only their own user object."""

    def has_object_permission(self, request, view, obj) -> bool:
        return obj == request.user or request.user.role == "ADMIN"
