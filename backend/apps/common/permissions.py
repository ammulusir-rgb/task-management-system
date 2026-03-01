"""
Common permissions for organization-scoped API views.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS
from apps.organizations.models import OrganizationMember


class IsOrgMemberOrReadOnly(BasePermission):
    """
    Allow read access to anyone, but write access only to organization members.
    
    For object-level permissions, checks if the user is a member of the 
    organization associated with the object.
    """

    message = "You must be a member of this organization to make changes."

    def has_permission(self, request, view):
        """Allow authenticated users basic access."""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Allow read access to anyone, write access to organization members only."""
        # Read permissions for any authenticated user
        if request.method in SAFE_METHODS:
            return True
        
        # Write permissions only for organization members
        if not hasattr(obj, 'organization'):
            # If object doesn't have organization, fallback to admin check
            return request.user.is_staff
        
        return OrganizationMember.objects.filter(
            organization=obj.organization,
            user=request.user,
            is_active=True,
        ).exists()


class IsOrganizationMember(BasePermission):
    """
    Allow access only to organization members.
    """

    message = "You must be a member of this organization."

    def has_object_permission(self, request, view, obj):
        """Check if user is a member of the organization."""
        if not hasattr(obj, 'organization'):
            return False
            
        return OrganizationMember.objects.filter(
            organization=obj.organization,
            user=request.user,
            is_active=True,
        ).exists()