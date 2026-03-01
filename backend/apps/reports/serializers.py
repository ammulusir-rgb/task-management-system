"""
Serializers for the Reports app.
Mostly read-only shapes for chart / export payloads.
"""

from rest_framework import serializers


class ProjectSummarySerializer(serializers.Serializer):
    total_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    open_tasks = serializers.IntegerField()
    overdue_tasks = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    avg_cycle_time_hours = serializers.FloatField(allow_null=True)


class StatusDistributionSerializer(serializers.Serializer):
    status = serializers.CharField()
    count = serializers.IntegerField()


class PriorityDistributionSerializer(serializers.Serializer):
    priority = serializers.CharField()
    count = serializers.IntegerField()


class AssigneeWorkloadSerializer(serializers.Serializer):
    assignee__id = serializers.UUIDField(allow_null=True)
    assignee__first_name = serializers.CharField(allow_blank=True)
    assignee__last_name = serializers.CharField(allow_blank=True)
    assignee__email = serializers.EmailField(allow_blank=True)
    total = serializers.IntegerField()
    completed = serializers.IntegerField()
    in_progress = serializers.IntegerField()


class TagDistributionSerializer(serializers.Serializer):
    tag = serializers.CharField()
    count = serializers.IntegerField()


class BurndownPointSerializer(serializers.Serializer):
    date = serializers.DateField()
    remaining = serializers.IntegerField()
    completed_cumulative = serializers.IntegerField()
    new_tasks = serializers.IntegerField()


class VelocityPointSerializer(serializers.Serializer):
    week = serializers.DateField()
    completed = serializers.IntegerField()


class MonthlyThroughputSerializer(serializers.Serializer):
    month = serializers.DateField()
    completed = serializers.IntegerField()


class ActivityHeatmapSerializer(serializers.Serializer):
    day = serializers.DateField()
    count = serializers.IntegerField()


class DayOfWeekActivitySerializer(serializers.Serializer):
    weekday = serializers.IntegerField()
    count = serializers.IntegerField()
