from django.contrib import admin

from .models import ActivityLog, Attachment, Comment, Task


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ("author", "created_at")


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0
    readonly_fields = ("uploaded_by", "file_size", "content_type", "created_at")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("task_key", "title", "status", "priority", "assignee", "project", "due_date")
    list_filter = ("status", "priority", "project")
    search_fields = ("title", "task_key", "description")
    readonly_fields = ("task_number", "task_key")
    inlines = [CommentInline, AttachmentInline]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("task", "author", "created_at")
    list_filter = ("created_at",)


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("task", "user", "action", "field_name", "created_at")
    list_filter = ("action",)
    readonly_fields = ("task", "user", "action", "field_name", "old_value", "new_value", "created_at")
