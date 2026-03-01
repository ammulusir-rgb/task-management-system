"""
Business-logic manager for Reports.
Views delegate to this class; all methods carry enter/exit/error logging
and raise domain exceptions on failure.
"""

import logging

from apps.common.exceptions import ForbiddenError, NotFoundError
from apps.projects.models import Project, ProjectMember

from .services import ReportService

logger = logging.getLogger(__name__)


class ReportManager:
    """Handles access control and delegation to ReportService."""

    def get_verified_project(self, project_id: str, user) -> Project:
        """
        Fetch *project_id* and verify *user* is a member (or staff).
        Raises NotFoundError or ForbiddenError.
        """
        logger.debug("ENTER ReportManager.get_verified_project | project=%s user=%s", project_id, user.pk)
        try:
            try:
                project = Project.objects.get(id=project_id, deleted_at__isnull=True)
            except Project.DoesNotExist:
                raise NotFoundError("Project not found.")

            is_member = ProjectMember.objects.filter(project=project, user=user).exists()
            is_org_member = project.organization.members.filter(user=user).exists()

            if not (is_member or is_org_member or user.is_staff):
                raise ForbiddenError("Not a project member.")

            logger.debug("EXIT ReportManager.get_verified_project | project=%s verified", project_id)
            return project
        except (NotFoundError, ForbiddenError):
            raise
        except Exception as exc:
            logger.error("ERROR ReportManager.get_verified_project: %s", exc, exc_info=True)
            raise

    def get_summary(self, project: Project) -> dict:
        """Return project-level KPI summary."""
        logger.debug("ENTER ReportManager.get_summary | project=%s", project.pk)
        try:
            data = ReportService(project).get_project_summary()
            logger.debug("EXIT ReportManager.get_summary | project=%s", project.pk)
            return data
        except Exception as exc:
            logger.error("ERROR ReportManager.get_summary: %s", exc, exc_info=True)
            raise

    def get_tasks_by_status(self, project: Project) -> list:
        logger.debug("ENTER ReportManager.get_tasks_by_status | project=%s", project.pk)
        try:
            data = ReportService(project).get_tasks_by_status()
            logger.debug("EXIT ReportManager.get_tasks_by_status | project=%s count=%d", project.pk, len(data))
            return data
        except Exception as exc:
            logger.error("ERROR ReportManager.get_tasks_by_status: %s", exc, exc_info=True)
            raise

    def get_tasks_by_priority(self, project: Project) -> list:
        logger.debug("ENTER ReportManager.get_tasks_by_priority | project=%s", project.pk)
        try:
            data = ReportService(project).get_tasks_by_priority()
            logger.debug("EXIT ReportManager.get_tasks_by_priority | project=%s count=%d", project.pk, len(data))
            return data
        except Exception as exc:
            logger.error("ERROR ReportManager.get_tasks_by_priority: %s", exc, exc_info=True)
            raise

    def get_tasks_by_assignee(self, project: Project) -> list:
        logger.debug("ENTER ReportManager.get_tasks_by_assignee | project=%s", project.pk)
        try:
            data = ReportService(project).get_tasks_by_assignee()
            logger.debug("EXIT ReportManager.get_tasks_by_assignee | project=%s count=%d", project.pk, len(data))
            return data
        except Exception as exc:
            logger.error("ERROR ReportManager.get_tasks_by_assignee: %s", exc, exc_info=True)
            raise

    def get_tasks_by_label(self, project: Project) -> list:
        logger.debug("ENTER ReportManager.get_tasks_by_label | project=%s", project.pk)
        try:
            data = ReportService(project).get_tasks_by_label()
            logger.debug("EXIT ReportManager.get_tasks_by_label | project=%s count=%d", project.pk, len(data))
            return data
        except Exception as exc:
            logger.error("ERROR ReportManager.get_tasks_by_label: %s", exc, exc_info=True)
            raise

    def get_burndown(self, project: Project, days: int = 30) -> list:
        logger.debug("ENTER ReportManager.get_burndown | project=%s days=%d", project.pk, days)
        try:
            data = ReportService(project).get_burndown_data(days=days)
            logger.debug("EXIT ReportManager.get_burndown | project=%s points=%d", project.pk, len(data))
            return data
        except Exception as exc:
            logger.error("ERROR ReportManager.get_burndown: %s", exc, exc_info=True)
            raise

    def get_velocity(self, project: Project, weeks: int = 12) -> list:
        logger.debug("ENTER ReportManager.get_velocity | project=%s weeks=%d", project.pk, weeks)
        try:
            data = ReportService(project).get_velocity(weeks=weeks)
            logger.debug("EXIT ReportManager.get_velocity | project=%s points=%d", project.pk, len(data))
            return data
        except Exception as exc:
            logger.error("ERROR ReportManager.get_velocity: %s", exc, exc_info=True)
            raise

    def get_monthly_throughput(self, project: Project) -> list:
        logger.debug("ENTER ReportManager.get_monthly_throughput | project=%s", project.pk)
        try:
            data = ReportService(project).get_monthly_throughput()
            logger.debug("EXIT ReportManager.get_monthly_throughput | project=%s points=%d", project.pk, len(data))
            return data
        except Exception as exc:
            logger.error("ERROR ReportManager.get_monthly_throughput: %s", exc, exc_info=True)
            raise

    def get_activity_heatmap(self, project: Project, days: int = 90) -> list:
        logger.debug("ENTER ReportManager.get_activity_heatmap | project=%s days=%d", project.pk, days)
        try:
            data = ReportService(project).get_activity_heatmap(days=days)
            logger.debug("EXIT ReportManager.get_activity_heatmap | project=%s points=%d", project.pk, len(data))
            return data
        except Exception as exc:
            logger.error("ERROR ReportManager.get_activity_heatmap: %s", exc, exc_info=True)
            raise

    def get_activity_by_day(self, project: Project) -> list:
        logger.debug("ENTER ReportManager.get_activity_by_day | project=%s", project.pk)
        try:
            data = ReportService(project).get_activity_by_day_of_week()
            logger.debug("EXIT ReportManager.get_activity_by_day | project=%s points=%d", project.pk, len(data))
            return data
        except Exception as exc:
            logger.error("ERROR ReportManager.get_activity_by_day: %s", exc, exc_info=True)
            raise

    def export_csv(self, project: Project) -> str:
        """Return CSV string for *project* tasks."""
        logger.debug("ENTER ReportManager.export_csv | project=%s", project.pk)
        try:
            csv_content = ReportService(project).export_tasks_csv()
            logger.debug("EXIT ReportManager.export_csv | project=%s", project.pk)
            return csv_content
        except Exception as exc:
            logger.error("ERROR ReportManager.export_csv: %s", exc, exc_info=True)
            raise


# Module-level singleton
report_manager = ReportManager()
