"""
django-filter FilterSets for tasks.
"""

import django_filters
from django.db.models import Q

from .models import Task, TaskPriority, TaskStatus


class TaskFilter(django_filters.FilterSet):
    """
    Comprehensive filter set for task queries.
    Supports filtering by status, priority, assignee, date ranges, tags, and search.
    """

    status = django_filters.MultipleChoiceFilter(choices=TaskStatus.choices)
    priority = django_filters.MultipleChoiceFilter(choices=TaskPriority.choices)
    assignee = django_filters.UUIDFilter(field_name="assignee_id")
    reporter = django_filters.UUIDFilter(field_name="reporter_id")
    column = django_filters.UUIDFilter(field_name="column_id")
    project = django_filters.UUIDFilter(field_name="project_id")

    # Date range filters
    due_date_after = django_filters.DateTimeFilter(field_name="due_date", lookup_expr="gte")
    due_date_before = django_filters.DateTimeFilter(field_name="due_date", lookup_expr="lte")
    created_after = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    # Boolean filters
    is_overdue = django_filters.BooleanFilter(method="filter_overdue")
    has_subtasks = django_filters.BooleanFilter(method="filter_has_subtasks")
    is_unassigned = django_filters.BooleanFilter(method="filter_unassigned")

    # Tag filter
    tags = django_filters.CharFilter(method="filter_tags")

    # Full-text search
    search = django_filters.CharFilter(method="filter_search")

    class Meta:
        model = Task
        fields = [
            "status",
            "priority",
            "assignee",
            "reporter",
            "column",
            "project",
        ]

    def filter_overdue(self, queryset, name, value):
        from django.utils import timezone

        now = timezone.now()
        if value:
            return queryset.filter(
                due_date__lt=now,
            ).exclude(status__in=[TaskStatus.DONE, TaskStatus.CANCELLED])
        return queryset.exclude(due_date__lt=now)

    def filter_has_subtasks(self, queryset, name, value):
        if value:
            return queryset.filter(subtasks__isnull=False).distinct()
        return queryset.filter(subtasks__isnull=True)

    def filter_unassigned(self, queryset, name, value):
        if value:
            return queryset.filter(assignee__isnull=True)
        return queryset.filter(assignee__isnull=False)

    def filter_tags(self, queryset, name, value):
        """Filter tasks containing the specified tag."""
        tags = [t.strip() for t in value.split(",") if t.strip()]
        if tags:
            return queryset.filter(tags__contains=tags)
        return queryset

    def filter_search(self, queryset, name, value):
        """Search in title and description."""
        return queryset.filter(
            Q(title__icontains=value) | Q(description__icontains=value) | Q(task_key__icontains=value)
        )
