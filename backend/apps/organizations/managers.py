"""
Business-logic manager for Organizations, Members, and Teams.
Views delegate to this class; all methods carry enter/exit/error logging
and raise domain exceptions on failure.
"""

import logging

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.common.exceptions import BusinessRuleError, ConflictError, NotFoundError

from .models import Organization, OrganizationMember, OrganizationRole, Team, TeamMember

logger = logging.getLogger(__name__)
User = get_user_model()


class OrganizationManager:
    """Handles all business logic for the organizations app."""

    # ── Organization CRUD helpers ──────────────────────────────────────────────

    def get_user_organizations(self, user):
        """Return organizations visible to *user* (active membership only)."""
        logger.debug("ENTER OrganizationManager.get_user_organizations | user=%s", user.pk)
        try:
            qs = (
                Organization.objects.filter(
                    members__user=user,
                    members__is_active=True,
                )
                .select_related("created_by")
                .prefetch_related("members")
                .distinct()
            )
            logger.debug("EXIT OrganizationManager.get_user_organizations | count=%d", qs.count())
            return qs
        except Exception as exc:
            logger.error("ERROR OrganizationManager.get_user_organizations: %s", exc, exc_info=True)
            raise

    def soft_delete_organization(self, org) -> None:
        """Deactivate an organization instead of hard-deleting it."""
        logger.debug("ENTER OrganizationManager.soft_delete_organization | org=%s", org.pk)
        try:
            org.is_active = False
            org.save(update_fields=["is_active"])
            logger.debug("EXIT OrganizationManager.soft_delete_organization | org=%s deactivated", org.pk)
        except Exception as exc:
            logger.error("ERROR OrganizationManager.soft_delete_organization: %s", exc, exc_info=True)
            raise

    # ── Member management ─────────────────────────────────────────────────────

    def list_members(self, org):
        """Return all members of *org* with related user and invited_by."""
        logger.debug("ENTER OrganizationManager.list_members | org=%s", org.pk)
        try:
            qs = (
                OrganizationMember.objects.filter(organization=org)
                .select_related("user", "invited_by")
            )
            logger.debug("EXIT OrganizationManager.list_members | org=%s count=%d", org.pk, qs.count())
            return qs
        except Exception as exc:
            logger.error("ERROR OrganizationManager.list_members: %s", exc, exc_info=True)
            raise

    def add_member(self, org, email: str, role: str, invited_by) -> OrganizationMember:
        """
        Add *email* to *org* with *role*.
        Raises NotFoundError if user does not exist, ConflictError if already a member.
        """
        logger.debug("ENTER OrganizationManager.add_member | org=%s email=%s role=%s", org.pk, email, role)
        try:
            try:
                user = User.objects.get(email=email, is_active=True)
            except User.DoesNotExist:
                raise NotFoundError("No active user found with that email.")

            if OrganizationMember.objects.filter(organization=org, user=user).exists():
                raise ConflictError("User is already a member of this organization.")

            member = OrganizationMember.objects.create(
                organization=org,
                user=user,
                role=role,
                invited_by=invited_by,
                joined_at=timezone.now(),
            )
            logger.debug("EXIT OrganizationManager.add_member | member=%s", member.pk)
            return member
        except (NotFoundError, ConflictError):
            raise
        except Exception as exc:
            logger.error("ERROR OrganizationManager.add_member: %s", exc, exc_info=True)
            raise

    def update_member_role(self, org, member_id: str, new_role: str) -> OrganizationMember:
        """
        Update the role of *member_id* in *org*.
        Raises NotFoundError, BusinessRuleError (last owner protection).
        """
        logger.debug("ENTER OrganizationManager.update_member_role | org=%s member=%s role=%s",
                     org.pk, member_id, new_role)
        try:
            try:
                member = OrganizationMember.objects.get(id=member_id, organization=org)
            except OrganizationMember.DoesNotExist:
                raise NotFoundError("Member not found.")

            if (
                member.role == OrganizationRole.OWNER
                and new_role != OrganizationRole.OWNER
            ):
                owner_count = OrganizationMember.objects.filter(
                    organization=org, role=OrganizationRole.OWNER, is_active=True
                ).count()
                if owner_count <= 1:
                    raise BusinessRuleError("Cannot change the role of the last owner.")

            member.role = new_role
            member.save(update_fields=["role"])
            logger.debug("EXIT OrganizationManager.update_member_role | member=%s new_role=%s", member.pk, new_role)
            return member
        except (NotFoundError, BusinessRuleError):
            raise
        except Exception as exc:
            logger.error("ERROR OrganizationManager.update_member_role: %s", exc, exc_info=True)
            raise

    def remove_member(self, org, member_id: str) -> None:
        """
        Deactivate *member_id* from *org*.
        Raises NotFoundError, BusinessRuleError (last owner protection).
        """
        logger.debug("ENTER OrganizationManager.remove_member | org=%s member=%s", org.pk, member_id)
        try:
            try:
                member = OrganizationMember.objects.get(id=member_id, organization=org)
            except OrganizationMember.DoesNotExist:
                raise NotFoundError("Member not found.")

            if member.role == OrganizationRole.OWNER:
                owner_count = OrganizationMember.objects.filter(
                    organization=org, role=OrganizationRole.OWNER, is_active=True
                ).count()
                if owner_count <= 1:
                    raise BusinessRuleError("Cannot remove the last owner.")

            member.is_active = False
            member.save(update_fields=["is_active"])
            logger.debug("EXIT OrganizationManager.remove_member | member=%s deactivated", member.pk)
        except (NotFoundError, BusinessRuleError):
            raise
        except Exception as exc:
            logger.error("ERROR OrganizationManager.remove_member: %s", exc, exc_info=True)
            raise

    # ── Team management ───────────────────────────────────────────────────────

    def get_teams_queryset(self, user, org_id: str = None):
        """Return teams visible to *user*, optionally filtered by *org_id*."""
        logger.debug("ENTER OrganizationManager.get_teams_queryset | user=%s org_id=%s", user.pk, org_id)
        try:
            qs = (
                Team.objects.filter(
                    organization__members__user=user,
                    organization__members__is_active=True,
                )
                .select_related("organization", "created_by")
                .distinct()
            )
            if org_id:
                qs = qs.filter(organization_id=org_id)
            logger.debug("EXIT OrganizationManager.get_teams_queryset | count=%d", qs.count())
            return qs
        except Exception as exc:
            logger.error("ERROR OrganizationManager.get_teams_queryset: %s", exc, exc_info=True)
            raise

    def list_team_members(self, team):
        """Return all members of *team*."""
        logger.debug("ENTER OrganizationManager.list_team_members | team=%s", team.pk)
        try:
            qs = TeamMember.objects.filter(team=team).select_related("user")
            logger.debug("EXIT OrganizationManager.list_team_members | team=%s count=%d", team.pk, qs.count())
            return qs
        except Exception as exc:
            logger.error("ERROR OrganizationManager.list_team_members: %s", exc, exc_info=True)
            raise

    def add_team_member(self, team, user_id: str, is_lead: bool = False) -> TeamMember:
        """
        Add *user_id* to *team*.
        Raises NotFoundError, ConflictError.
        """
        logger.debug("ENTER OrganizationManager.add_team_member | team=%s user=%s", team.pk, user_id)
        try:
            try:
                user = User.objects.get(id=user_id, is_active=True)
            except User.DoesNotExist:
                raise NotFoundError("User not found.")

            if TeamMember.objects.filter(team=team, user=user).exists():
                raise ConflictError("User is already a team member.")

            member = TeamMember.objects.create(team=team, user=user, is_lead=is_lead)
            logger.debug("EXIT OrganizationManager.add_team_member | member=%s", member.pk)
            return member
        except (NotFoundError, ConflictError):
            raise
        except Exception as exc:
            logger.error("ERROR OrganizationManager.add_team_member: %s", exc, exc_info=True)
            raise

    def remove_team_member(self, team, member_id: str) -> None:
        """Remove (hard-delete) *member_id* from *team*. Raises NotFoundError."""
        logger.debug("ENTER OrganizationManager.remove_team_member | team=%s member=%s", team.pk, member_id)
        try:
            try:
                member = TeamMember.objects.get(id=member_id, team=team)
            except TeamMember.DoesNotExist:
                raise NotFoundError("Team member not found.")
            member.delete()
            logger.debug("EXIT OrganizationManager.remove_team_member | member=%s deleted", member_id)
        except NotFoundError:
            raise
        except Exception as exc:
            logger.error("ERROR OrganizationManager.remove_team_member: %s", exc, exc_info=True)
            raise


# Module-level singleton
organization_manager = OrganizationManager()
