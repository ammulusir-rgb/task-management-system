"""
Views for the Reports app.
Endpoint definitions only — all business logic lives in managers.py.
"""

from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from .managers import report_manager
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


class ProjectReportViewSet(ViewSet):
    """
    Reports endpoints scoped to a project.
    URL: /api/v1/projects/{project_id}/reports/<action>/
    """

    permission_classes = [IsAuthenticated]

    # ── Summary ──

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request, project_id=None):
        project = report_manager.get_verified_project(request.user, project_id)
        data = report_manager.get_summary(project)
        return Response(ProjectSummarySerializer(data).data)

    # ── Distribution Charts ──

    @action(detail=False, methods=["get"], url_path="tasks-by-status")
    def tasks_by_status(self, request, project_id=None):
        project = report_manager.get_verified_project(request.user, project_id)
        data = report_manager.get_tasks_by_status(project)
        return Response(StatusDistributionSerializer(data, many=True).data)

    @action(detail=False, methods=["get"], url_path="tasks-by-priority")
    def tasks_by_priority(self, request, project_id=None):
        project = report_manager.get_verified_project(request.user, project_id)
        data = report_manager.get_tasks_by_priority(project)
        return Response(PriorityDistributionSerializer(data, many=True).data)

    @action(detail=False, methods=["get"], url_path="tasks-by-assignee")
    def tasks_by_assignee(self, request, project_id=None):
        project = report_manager.get_verified_project(request.user, project_id)
        data = report_manager.get_tasks_by_assignee(project)
        return Response(AssigneeWorkloadSerializer(data, many=True).data)

    @action(detail=False, methods=["get"], url_path="tasks-by-label")
    def tasks_by_label(self, request, project_id=None):
        project = report_manager.get_verified_project(request.user, project_id)
        data = report_manager.get_tasks_by_label(project)
        return Response(TagDistributionSerializer(data, many=True).data)

    # ── Burndown / Burnup ──

    @action(detail=False, methods=["get"], url_path="burndown")
    def burndown(self, request, project_id=None):
        project = report_manager.get_verified_project(request.user, project_id)
        days = min(max(int(request.query_params.get("days", 30)), 7), 365)
        data = report_manager.get_burndown(project, days=days)
        return Response(BurndownPointSerializer(data, many=True).data)

    # ── Velocity & Throughput ──

    @action(detail=False, methods=["get"], url_path="velocity")
    def velocity(self, request, project_id=None):
        project = report_manager.get_verified_project(request.user, project_id)
        weeks = min(max(int(request.query_params.get("weeks", 12)), 4), 52)
        data = report_manager.get_velocity(project, weeks=weeks)
        return Response(VelocityPointSerializer(data, many=True).data)

    @action(detail=False, methods=["get"], url_path="monthly-throughput")
    def monthly_throughput(self, request, project_id=None):
        project = report_manager.get_verified_project(request.user, project_id)
        data = report_manager.get_monthly_throughput(project)
        return Response(MonthlyThroughputSerializer(data, many=True).data)

    # ── Activity ──

    @action(detail=False, methods=["get"], url_path="activity-heatmap")
    def activity_heatmap(self, request, project_id=None):
        project = report_manager.get_verified_project(request.user, project_id)
        days = min(max(int(request.query_params.get("days", 90)), 30), 365)
        data = report_manager.get_activity_heatmap(project, days=days)
        return Response(ActivityHeatmapSerializer(data, many=True).data)

    @action(detail=False, methods=["get"], url_path="activity-by-day")
    def activity_by_day(self, request, project_id=None):
        project = report_manager.get_verified_project(request.user, project_id)
        data = report_manager.get_activity_by_day(project)
        return Response(DayOfWeekActivitySerializer(data, many=True).data)

    # ── CSV Export ──

    @action(detail=False, methods=["get"], url_path="export-csv")
    def export_csv(self, request, project_id=None):
        project = report_manager.get_verified_project(request.user, project_id)
        csv_content = report_manager.export_csv(project)
        response = HttpResponse(csv_content, content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="{project.slug}-tasks.csv"'
        )
        return response
