from django.contrib import admin

from .models import Board, Column, Project, ProjectMember


class ProjectMemberInline(admin.TabularInline):
    model = ProjectMember
    extra = 0


class ColumnInline(admin.TabularInline):
    model = Column
    extra = 0
    ordering = ["position"]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "status", "created_by", "created_at")
    list_filter = ("status", "organization")
    search_fields = ("name", "slug")
    inlines = [ProjectMemberInline]


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "is_default", "created_at")
    inlines = [ColumnInline]


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ("name", "board", "position", "wip_limit", "is_done_column")
    list_filter = ("is_done_column",)
