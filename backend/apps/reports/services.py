"""
Report service layer — encapsulates complex aggregation queries
for the reporting dashboard. Keeps views slim.
"""

import csv
import io
import logging
from collections import defaultdict
from datetime import timedelta

from django.db.models import (Avg, Case, Count, F, FloatField, Q, Sum, Value, When,)
from django.db.models.functions import (ExtractWeekDay, TruncDate, TruncMonth, TruncWeek,)
from django.utils import timezone

from apps.tasks.models import ActivityLog, Task, TaskStatus

logger = logging.getLogger(__name__)


class ReportService:
    """Generates analytical data for a given project."""

    def __init__(self, project):
        self.project = project
        # Use direct project FK; SoftDeleteManager already excludes deleted tasks
        self._base_qs = Task.objects.filter(project=self.project)

    # ------------------------------------------------------------------ #
    # Summary / KPI
    # ------------------------------------------------------------------ #
    def get_project_summary(self):
        """Top-level KPIs for the project dashboard header."""
        qs = self._base_qs
        now = timezone.now()

        total = qs.count()
        completed = qs.filter(status=TaskStatus.DONE).count()
        overdue = qs.filter(
            due_date__lt=now,
            status__in=[TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW],
        ).count()

        avg_cycle_time = qs.filter(
            started_at__isnull=False,
            completed_at__isnull=False,
        ).aggregate(
            avg_hours=Avg(
                (F("completed_at") - F("started_at")),
                output_field=FloatField(),
            )
        )

        # Convert from microseconds to hours (Django DurationField)
        avg_hours = None
        if avg_cycle_time["avg_hours"]:
            avg_hours = round(avg_cycle_time["avg_hours"] / 3_600_000_000, 1)

        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "open_tasks": total - completed,
            "overdue_tasks": overdue,
            "completion_rate": round(completed / total * 100, 1) if total else 0,
            "avg_cycle_time_hours": avg_hours,
        }

    # ------------------------------------------------------------------ #
    # Task distribution
    # ------------------------------------------------------------------ #
    def get_tasks_by_status(self):
        """Count of tasks grouped by status."""
        return list(
            self._base_qs.values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )

    def get_tasks_by_priority(self):
        """Count of tasks grouped by priority."""
        return list(
            self._base_qs.values("priority")
            .annotate(count=Count("id"))
            .order_by("priority")
        )

    def get_tasks_by_assignee(self):
        """Tasks per assignee — for workload chart."""
        return list(
            self._base_qs.values(
                "assignee__id",
                "assignee__first_name",
                "assignee__last_name",
                "assignee__email",
            )
            .annotate(
                total=Count("id"),
                completed=Count("id", filter=Q(status=TaskStatus.DONE)),
                in_progress=Count(
                    "id", filter=Q(status__in=[TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW])
                ),
            )
            .order_by("-total")
        )

    def get_tasks_by_label(self):
        """
        Frequency count for tags/labels (JSONField storing a list).
        Works on both PostgreSQL and SQLite.
        """
        from django.db import connection

        if connection.vendor == "postgresql":
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT tag, COUNT(*) as count
                    FROM tasks_task, unnest(
                        CASE WHEN tags IS NOT NULL THEN
                            ARRAY(SELECT jsonb_array_elements_text(tags::jsonb))
                        ELSE ARRAY[]::text[] END
                    ) AS tag
                    WHERE tasks_task.deleted_at IS NULL
                      AND tasks_task.project_id = %s
                    GROUP BY tag
                    ORDER BY count DESC
                    LIMIT 20;
                    """,
                    [str(self.project.id)],
                )
                return [
                    {"tag": row[0], "count": row[1]} for row in cursor.fetchall()
                ]
        else:
            # Fallback for SQLite and other backends
            tag_counts = defaultdict(int)
            for tags in self._base_qs.values_list("tags", flat=True):
                if tags:
                    for tag in tags:
                        tag_counts[tag] += 1
            sorted_tags = sorted(tag_counts.items(), key=lambda x: -x[1])[:20]
            return [{"tag": tag, "count": count} for tag, count in sorted_tags]

    # ------------------------------------------------------------------ #
    # Burndown / Burnup
    # ------------------------------------------------------------------ #
    def get_burndown_data(self, days: int = 30):
        """
        Daily burndown: how many tasks remain open over time.
        Returns a list of {date, remaining, completed_cumulative}.
        """
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        # Pre-calculate all completion events within the range
        completions_by_date = dict(
            self._base_qs.filter(
                completed_at__date__gte=start_date,
                completed_at__date__lte=end_date,
            )
            .annotate(day=TruncDate("completed_at"))
            .values("day")
            .annotate(count=Count("id"))
            .values_list("day", "count")
        )

        # Total scope at start
        total_at_start = self._base_qs.filter(
            created_at__date__lte=start_date
        ).count()

        completed_before_start = self._base_qs.filter(
            completed_at__date__lte=start_date
        ).count()

        remaining = total_at_start - completed_before_start
        completed_cumulative = completed_before_start
        result = []

        current = start_date
        while current <= end_date:
            # Tasks created on this day (scope creep)
            new_tasks = self._base_qs.filter(created_at__date=current).count()
            day_completed = completions_by_date.get(current, 0)

            remaining = remaining + new_tasks - day_completed
            completed_cumulative += day_completed

            result.append(
                {
                    "date": current.isoformat(),
                    "remaining": remaining,
                    "completed_cumulative": completed_cumulative,
                    "new_tasks": new_tasks,
                }
            )
            current += timedelta(days=1)

        return result

    # ------------------------------------------------------------------ #
    # Velocity / Throughput
    # ------------------------------------------------------------------ #
    def get_velocity(self, weeks: int = 12):
        """Tasks completed per week — for velocity chart."""
        start = timezone.now() - timedelta(weeks=weeks)
        return list(
            self._base_qs.filter(completed_at__gte=start)
            .annotate(week=TruncWeek("completed_at"))
            .values("week")
            .annotate(completed=Count("id"))
            .order_by("week")
        )

    def get_monthly_throughput(self, months: int = 12):
        """Tasks completed per month."""
        start = timezone.now() - timedelta(days=months * 30)
        return list(
            self._base_qs.filter(completed_at__gte=start)
            .annotate(month=TruncMonth("completed_at"))
            .values("month")
            .annotate(completed=Count("id"))
            .order_by("month")
        )

    # ------------------------------------------------------------------ #
    # Activity / Heatmap
    # ------------------------------------------------------------------ #
    def get_activity_heatmap(self, days: int = 90):
        """Daily activity counts for a heatmap calendar."""
        start = timezone.now() - timedelta(days=days)
        return list(
            ActivityLog.objects.filter(
                task__project=self.project,
                created_at__gte=start,
            )
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )

    def get_activity_by_day_of_week(self):
        """Aggregate activity by day of week (1=Sunday .. 7=Saturday)."""
        return list(
            ActivityLog.objects.filter(
                task__project=self.project,
            )
            .annotate(weekday=ExtractWeekDay("created_at"))
            .values("weekday")
            .annotate(count=Count("id"))
            .order_by("weekday")
        )

    # ------------------------------------------------------------------ #
    # CSV Export
    # ------------------------------------------------------------------ #
    def export_tasks_csv(self):
        """Export all project tasks as a CSV string."""
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "Task Key",
                "Title",
                "Status",
                "Priority",
                "Assignee",
                "Reporter",
                "Due Date",
                "Created",
                "Completed",
                "Column",
                "Tags",
                "Story Points",
            ]
        )

        tasks = (
            self._base_qs.select_related(
                "assignee",
                "reporter",
                "column",
                "column__board",
            )
            .order_by("task_number")
        )

        for task in tasks:
            writer.writerow(
                [
                    task.task_key,
                    task.title,
                    task.get_status_display() if hasattr(task, "get_status_display") else task.status,
                    task.get_priority_display() if hasattr(task, "get_priority_display") else task.priority,
                    task.assignee.email if task.assignee else "",
                    task.reporter.email if task.reporter else "",
                    task.due_date.isoformat() if task.due_date else "",
                    task.created_at.isoformat(),
                    task.completed_at.isoformat() if task.completed_at else "",
                    task.column.name if task.column else "",
                    ", ".join(task.tags) if task.tags else "",
                    task.story_points or "",
                ]
            )

        return buffer.getvalue()
