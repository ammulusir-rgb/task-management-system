"""
Filters for user queries.
"""

import django_filters
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class UserFilter(django_filters.FilterSet):
    """Filter users by role, active status, and search term."""

    role = django_filters.ChoiceFilter(choices=[("ADMIN", "Admin"), ("MANAGER", "Manager"), ("MEMBER", "Member")])
    is_active = django_filters.BooleanFilter()
    search = django_filters.CharFilter(method="filter_search")

    class Meta:
        model = User
        fields = ["role", "is_active"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            models.Q(email__icontains=value)
            | models.Q(first_name__icontains=value)
            | models.Q(last_name__icontains=value)
        )
