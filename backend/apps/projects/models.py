"""
Project, Board, and Column models.
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils.text import slugify

from apps.common.mixins import OrderableMixin, SoftDeleteManager, SoftDeleteMixin, TimestampMixin


class ProjectStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    ARCHIVED = "archived", "Archived"
    DELETED = "deleted", "Deleted"


class ProjectMemberRole(models.TextChoices):
    ADMIN = "admin", "Admin"
    MEMBER = "member", "Member"
    VIEWER = "viewer", "Viewer"


class Project(TimestampMixin, SoftDeleteMixin, models.Model):
    """
    Project within an organization. Contains boards, tasks, and members.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="projects",
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, db_index=True)
    description = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=ProjectStatus.choices,
        default=ProjectStatus.ACTIVE,
        db_index=True,
    )
    prefix = models.CharField(
        max_length=10,
        blank=True,
        default="",
        help_text="Short prefix for task IDs, e.g., 'PRJ'",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_projects",
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("organization", "slug")
        indexes = [
            models.Index(fields=["organization", "status"], name="idx_project_org_status"),
            models.Index(fields=["slug"], name="idx_project_slug"),
            models.Index(
                fields=["organization"],
                name="idx_project_active",
                condition=models.Q(deleted_at__isnull=True),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.organization.name} / {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            counter = 1
            while Project.objects.filter(organization=self.organization, slug=slug).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        if not self.prefix:
            # Generate prefix from first letters of words
            words = self.name.upper().split()
            self.prefix = "".join(w[0] for w in words[:3]) or "TSK"
        super().save(*args, **kwargs)


class ProjectMember(TimestampMixin, models.Model):
    """
    Tracks a user's membership and role within a specific project.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="members",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_memberships",
    )
    role = models.CharField(
        max_length=20,
        choices=ProjectMemberRole.choices,
        default=ProjectMemberRole.MEMBER,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("project", "user")
        indexes = [
            models.Index(fields=["project", "user"], name="idx_projmember_proj_user"),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} — {self.project.name} ({self.role})"


class Board(TimestampMixin, models.Model):
    """
    Kanban board within a project.
    MVP: one board per project (OneToOne feasible, but FK allows future multiple boards).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="boards",
    )
    name = models.CharField(max_length=200, default="Main Board")
    is_default = models.BooleanField(default=True)

    class Meta:
        ordering = ["-is_default", "name"]

    def __str__(self) -> str:
        return f"{self.project.name} / {self.name}"


class Column(TimestampMixin, OrderableMixin, models.Model):
    """
    A column/lane in a Kanban board (e.g., "To Do", "In Progress").
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    board = models.ForeignKey(
        Board,
        on_delete=models.CASCADE,
        related_name="columns",
    )
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default="#6C757D", help_text="Hex color code")
    wip_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Work In Progress limit for this column",
    )
    is_done_column = models.BooleanField(
        default=False,
        help_text="Tasks in this column are considered done",
    )

    class Meta:
        ordering = ["position"]
        indexes = [
            models.Index(fields=["board", "position"], name="idx_column_board_pos"),
        ]

    def __str__(self) -> str:
        return f"{self.board.project.name} / {self.name}"
