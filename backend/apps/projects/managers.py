"""
Business-logic manager for Projects, Boards, and Columns.
Views delegate to this class; all methods carry enter/exit/error logging
and raise domain exceptions on failure.
"""

import logging

from django.contrib.auth import get_user_model
from django.db import transaction

from apps.common.exceptions import ConflictError, NotFoundError

from .models import Board, Column, Project, ProjectMember, ProjectMemberRole, ProjectStatus

logger = logging.getLogger(__name__)
User = get_user_model()


class ProjectManager:
    """Handles all business logic for the projects app."""

    # ── Project queryset ──────────────────────────────────────────────────────

    def get_user_projects(self, user):
        """Return projects where *user* is an active member."""
        from django.db.models import Count
        logger.debug("ENTER ProjectManager.get_user_projects | user=%s", user.pk)
        try:
            qs = (
                Project.objects.filter(
                    members__user=user,
                    members__is_active=True,
                )
                .select_related("organization", "created_by")
                .annotate(_task_count=Count("tasks"))
                .distinct()
            )
            logger.debug("EXIT ProjectManager.get_user_projects | count=%d", qs.count())
            return qs
        except Exception as exc:
            logger.error("ERROR ProjectManager.get_user_projects: %s", exc, exc_info=True)
            raise

    def soft_delete_project(self, project) -> None:
        """Soft-delete a project by setting status to DELETED."""
        logger.debug("ENTER ProjectManager.soft_delete_project | project=%s", project.pk)
        try:
            project.status = ProjectStatus.DELETED
            project.soft_delete()
            logger.debug("EXIT ProjectManager.soft_delete_project | project=%s deleted", project.pk)
        except Exception as exc:
            logger.error("ERROR ProjectManager.soft_delete_project: %s", exc, exc_info=True)
            raise

    def archive_project(self, project) -> Project:
        """Set project status to ARCHIVED."""
        logger.debug("ENTER ProjectManager.archive_project | project=%s", project.pk)
        try:
            project.status = ProjectStatus.ARCHIVED
            project.save(update_fields=["status"])
            logger.debug("EXIT ProjectManager.archive_project | project=%s archived", project.pk)
            return project
        except Exception as exc:
            logger.error("ERROR ProjectManager.archive_project: %s", exc, exc_info=True)
            raise

    def restore_project(self, project) -> Project:
        """Set project status back to ACTIVE."""
        logger.debug("ENTER ProjectManager.restore_project | project=%s", project.pk)
        try:
            project.status = ProjectStatus.ACTIVE
            project.save(update_fields=["status"])
            logger.debug("EXIT ProjectManager.restore_project | project=%s restored", project.pk)
            return project
        except Exception as exc:
            logger.error("ERROR ProjectManager.restore_project: %s", exc, exc_info=True)
            raise

    # ── Member management ─────────────────────────────────────────────────────

    def list_members(self, project):
        """Return all members of *project* with related user data."""
        logger.debug("ENTER ProjectManager.list_members | project=%s", project.pk)
        try:
            qs = ProjectMember.objects.filter(project=project).select_related("user")
            logger.debug("EXIT ProjectManager.list_members | project=%s count=%d", project.pk, qs.count())
            return qs
        except Exception as exc:
            logger.error("ERROR ProjectManager.list_members: %s", exc, exc_info=True)
            raise

    def add_member(self, project, user_id: str, role: str) -> ProjectMember:
        """
        Add *user_id* to *project* with *role*.
        Raises NotFoundError, ConflictError.
        """
        logger.debug("ENTER ProjectManager.add_member | project=%s user=%s role=%s",
                     project.pk, user_id, role)
        try:
            try:
                user = User.objects.get(id=user_id, is_active=True)
            except User.DoesNotExist:
                raise NotFoundError("User not found.")

            if ProjectMember.objects.filter(project=project, user=user).exists():
                raise ConflictError("User is already a member of this project.")

            member = ProjectMember.objects.create(project=project, user=user, role=role)
            logger.debug("EXIT ProjectManager.add_member | member=%s", member.pk)
            return member
        except (NotFoundError, ConflictError):
            raise
        except Exception as exc:
            logger.error("ERROR ProjectManager.add_member: %s", exc, exc_info=True)
            raise

    def remove_member(self, project, member_id: str) -> None:
        """Deactivate *member_id* from *project*. Raises NotFoundError."""
        logger.debug("ENTER ProjectManager.remove_member | project=%s member=%s", project.pk, member_id)
        try:
            try:
                member = ProjectMember.objects.get(id=member_id, project=project)
            except ProjectMember.DoesNotExist:
                raise NotFoundError("Project member not found.")
            member.is_active = False
            member.save(update_fields=["is_active"])
            logger.debug("EXIT ProjectManager.remove_member | member=%s deactivated", member_id)
        except NotFoundError:
            raise
        except Exception as exc:
            logger.error("ERROR ProjectManager.remove_member: %s", exc, exc_info=True)
            raise

    # ── Board management ──────────────────────────────────────────────────────

    def get_boards_queryset(self, user):
        """Return boards for projects where *user* is an active member."""
        logger.debug("ENTER ProjectManager.get_boards_queryset | user=%s", user.pk)
        try:
            qs = (
                Board.objects.filter(
                    project__members__user=user,
                    project__members__is_active=True,
                )
                .select_related("project")
                .prefetch_related("columns")
                .distinct()
            )
            logger.debug("EXIT ProjectManager.get_boards_queryset | count=%d", qs.count())
            return qs
        except Exception as exc:
            logger.error("ERROR ProjectManager.get_boards_queryset: %s", exc, exc_info=True)
            raise

    # ── Column management ─────────────────────────────────────────────────────

    def get_columns_queryset(self, user):
        """Return columns for boards in projects where *user* is an active member."""
        logger.debug("ENTER ProjectManager.get_columns_queryset | user=%s", user.pk)
        try:
            qs = (
                Column.objects.filter(
                    board__project__members__user=user,
                    board__project__members__is_active=True,
                )
                .select_related("board", "board__project")
                .distinct()
            )
            logger.debug("EXIT ProjectManager.get_columns_queryset | count=%d", qs.count())
            return qs
        except Exception as exc:
            logger.error("ERROR ProjectManager.get_columns_queryset: %s", exc, exc_info=True)
            raise

    def reorder_columns(self, column_ids: list) -> None:
        """Bulk-update column positions from an ordered list of column IDs."""
        logger.debug("ENTER ProjectManager.reorder_columns | ids=%s", column_ids)
        try:
            with transaction.atomic():
                for position, column_id in enumerate(column_ids):
                    Column.objects.filter(id=column_id).update(position=position)
            logger.debug("EXIT ProjectManager.reorder_columns | %d columns reordered", len(column_ids))
        except Exception as exc:
            logger.error("ERROR ProjectManager.reorder_columns: %s", exc, exc_info=True)
            raise


# Module-level singleton
project_manager = ProjectManager()
