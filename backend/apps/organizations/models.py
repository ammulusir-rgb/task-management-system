"""
Organization models for multi-tenancy support.
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils.text import slugify

from apps.common.mixins import TimestampMixin


class Organization(TimestampMixin, models.Model):
    """
    Represents a company or team that uses the platform.
    Serves as the top-level tenant for multi-tenancy.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, db_index=True)
    description = models.TextField(blank=True, default="")
    logo = models.ImageField(upload_to="organizations/logos/", blank=True, null=True)
    website = models.URLField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_organizations",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"], name="idx_org_slug"),
            models.Index(fields=["name"], name="idx_org_name"),
            models.Index(fields=["is_active"], name="idx_org_active"),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            counter = 1
            while Organization.objects.filter(slug=slug).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class OrganizationRole(models.TextChoices):
    """Roles within an organization."""

    OWNER = "owner", "Owner"
    ADMIN = "admin", "Admin"
    MEMBER = "member", "Member"


class OrganizationMember(TimestampMixin, models.Model):
    """
    Represents a user's membership in an organization.
    Tracks their role and join date.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="members",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_memberships",
    )
    role = models.CharField(
        max_length=20,
        choices=OrganizationRole.choices,
        default=OrganizationRole.MEMBER,
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="org_invitations_sent",
    )
    invited_at = models.DateTimeField(auto_now_add=True)
    joined_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("organization", "user")
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["organization", "user"],
                name="idx_orgmember_org_user",
            ),
            models.Index(
                fields=["user", "is_active"],
                name="idx_orgmember_user_active",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} — {self.organization.name} ({self.role})"

    @property
    def is_org_admin(self) -> bool:
        return self.role in (OrganizationRole.OWNER, OrganizationRole.ADMIN)


class Team(TimestampMixin, models.Model):
    """
    A team within an organization for grouping members.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="teams",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_teams",
    )

    class Meta:
        ordering = ["name"]
        unique_together = ("organization", "name")

    def __str__(self) -> str:
        return f"{self.organization.name} / {self.name}"


class TeamMember(TimestampMixin, models.Model):
    """
    Membership of a user in a team.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="members",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="team_memberships",
    )
    is_lead = models.BooleanField(default=False)

    class Meta:
        unique_together = ("team", "user")
        ordering = ["-is_lead", "user__first_name"]

    def __str__(self) -> str:
        return f"{self.user.email} — {self.team.name}"
