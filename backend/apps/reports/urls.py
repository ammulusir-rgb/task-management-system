from django.urls import path

from . import views

app_name = "reports"

# These are nested under /api/v1/projects/<project_id>/reports/
urlpatterns = [
    path("summary/", views.ProjectReportViewSet.as_view({"get": "summary"}), name="summary"),
    path("tasks-by-status/", views.ProjectReportViewSet.as_view({"get": "tasks_by_status"}), name="tasks-by-status"),
    path("tasks-by-priority/", views.ProjectReportViewSet.as_view({"get": "tasks_by_priority"}), name="tasks-by-priority"),
    path("tasks-by-assignee/", views.ProjectReportViewSet.as_view({"get": "tasks_by_assignee"}), name="tasks-by-assignee"),
    path("tasks-by-label/", views.ProjectReportViewSet.as_view({"get": "tasks_by_label"}), name="tasks-by-label"),
    path("burndown/", views.ProjectReportViewSet.as_view({"get": "burndown"}), name="burndown"),
    path("velocity/", views.ProjectReportViewSet.as_view({"get": "velocity"}), name="velocity"),
    path("monthly-throughput/", views.ProjectReportViewSet.as_view({"get": "monthly_throughput"}), name="monthly-throughput"),
    path("activity-heatmap/", views.ProjectReportViewSet.as_view({"get": "activity_heatmap"}), name="activity-heatmap"),
    path("activity-by-day/", views.ProjectReportViewSet.as_view({"get": "activity_by_day"}), name="activity-by-day"),
    path("export-csv/", views.ProjectReportViewSet.as_view({"get": "export_csv"}), name="export-csv"),
]
