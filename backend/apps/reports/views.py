"""
Views for the Reports app.
All endpoints are read-only and project-scoped.
"""

from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.projects.models import Project, ProjectMember

from .serializers import (
    ActivityHeatmapSerializer,
    AssigneeWorkloadSerializer,
    BurndownPointSerializer,
    DayOfWeekActivitySerializer,
    MonthlyThroughputSerializer,
    PriorityDistributionSerializer,
    ProjectSummarySerializer,
    StatusDistributionSerializer,
    TagDistributionSerializer,
    VelocityPointSerializer,
)
from .services import ReportService


class ProjectReportViewSet(ViewSet):
    """
    Reports endpoints scoped to a project.
    URL: /api/v1/projects/{project_id}/reports/<action>/
    """

    permission_classes = [IsAuthenticated]

    def _get_project(self, request, project_id):
        """Retrieve project and verify membership."""
        try:
            project = Project.objects.get(id=project_id, deleted_at__isnull=True)
        except Project.DoesNotExist:
            return None, Response(
                {"error": {"code": "not_found", "message": "Project not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        is_member = ProjectMember.objects.filter(
            project=project, user=request.user
        ).exists()
        is_org_member = project.organization.members.filter(
            user=request.user
        ).exists()

        if not (is_member or is_org_member or request.user.is_staff):
            return None, Response(
                {"error": {"code": "forbidden", "message": "Not a project member."}},
                status=status.HTTP_403_FORBIDDEN,
            )

        return project, None

    # ------------------------------------------------------------------ #
    # Summary
    # ------------------------------------------------------------------ #
    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request, project_id=None):
        """Project-level KPIs."""
        project, err = self._get_project(request, project_id)
        if err:
            return err

        data = ReportService(project).get_project_summary()
        serializer = ProjectSummarySerializer(data)
        return Response(serializer.data)

    # ------------------------------------------------------------------ #
    # Distribution Charts
    # ------------------------------------------------------------------ #
    @action(detail=False, methods=["get"], url_path="tasks-by-status")
    def tasks_by_status(self, request, project_id=None):
        project, err = self._get_project(request, project_id)
        if err:
            return err

        data = ReportService(project).get_tasks_by_status()
        serializer = StatusDistributionSerializer(data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="tasks-by-priority")
    def tasks_by_priority(self, request, project_id=None):
        project, err = self._get_project(request, project_id)
        if err:
            return err

        data = ReportService(project).get_tasks_by_priority()
        serializer = PriorityDistributionSerializer(data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="tasks-by-assignee")
    def tasks_by_assignee(self, request, project_id=None):
        project, err = self._get_project(request, project_id)
        if err:
            return err

        data = ReportService(project).get_tasks_by_assignee()
        serializer = AssigneeWorkloadSerializer(data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="tasks-by-label")
    def tasks_by_label(self, request, project_id=None):
        project, err = self._get_project(request, project_id)
        if err:
            return err

        data = ReportService(project).get_tasks_by_label()
        serializer = TagDistributionSerializer(data, many=True)
        return Response(serializer.data)

    # ------------------------------------------------------------------ #
    # Burndown / Burnup
    # ------------------------------------------------------------------ #
    @action(detail=False, methods=["get"], url_path="burndown")
    def burndown(self, request, project_id=None):
        project, err = self._get_project(request, project_id)
        if err:
            return err

        days = int(request.query_params.get("days", 30))
        days = min(max(days, 7), 365)

        data = ReportService(project).get_burndown_data(days=days)
        serializer = BurndownPointSerializer(data, many=True)
        return Response(serializer.data)

    # ------------------------------------------------------------------ #
    # Velocity & Throughput
    # ------------------------------------------------------------------ #
    @action(detail=False, methods=["get"], url_path="velocity")
    def velocity(self, request, project_id=None):
        project, err = self._get_project(request, project_id)
        if err:
            return err

        weeks = int(request.query_params.get("weeks", 12))
        weeks = min(max(weeks, 4), 52)

        data = ReportService(project).get_velocity(weeks=weeks)
        serializer = VelocityPointSerializer(data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="monthly-throughput")
    def monthly_throughput(self, request, project_id=None):
        project, err = self._get_project(request, project_id)
        if err:
            return err

        data = ReportService(project).get_monthly_throughput()
        serializer = MonthlyThroughputSerializer(data, many=True)
        return Response(serializer.data)

    # ------------------------------------------------------------------ #
    # Activity
    # ------------------------------------------------------------------ #
    @action(detail=False, methods=["get"], url_path="activity-heatmap")
    def activity_heatmap(self, request, project_id=None):
        project, err = self._get_project(request, project_id)
        if err:
            return err

        days = int(request.query_params.get("days", 90))
        days = min(max(days, 30), 365)

        data = ReportService(project).get_activity_heatmap(days=days)
        serializer = ActivityHeatmapSerializer(data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="activity-by-day")
    def activity_by_day(self, request, project_id=None):
        project, err = self._get_project(request, project_id)
        if err:
            return err

        data = ReportService(project).get_activity_by_day_of_week()
        serializer = DayOfWeekActivitySerializer(data, many=True)
        return Response(serializer.data)

    # ------------------------------------------------------------------ #
    # CSV Export
    # ------------------------------------------------------------------ #
    @action(detail=False, methods=["get"], url_path="export-csv")
    def export_csv(self, request, project_id=None):
        project, err = self._get_project(request, project_id)
        if err:
            return err

        csv_content = ReportService(project).export_tasks_csv()
        response = HttpResponse(csv_content, content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="{project.slug}-tasks.csv"'
        )
        return response
