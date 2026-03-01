"""
Model factories for test data generation using factory_boy.
"""

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from apps.notifications.models import Notification, NotificationType
from apps.organizations.models import Organization, OrganizationMember
from apps.projects.models import Board, Column, Project, ProjectMember
from apps.tasks.models import Attachment, Comment, Task
from apps.users.models import User


# ------------------------------------------------------------------ #
# Users
# ------------------------------------------------------------------ #
class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    is_verified = True

    @factory.lazy_attribute
    def password(self):
        return "Testpass123!"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop("password", "Testpass123!")
        obj = super()._create(model_class, *args, **kwargs)
        obj.set_password(password)
        obj.save(update_fields=["password"])
        return obj


class AdminUserFactory(UserFactory):
    is_staff = True
    role = "admin"


# ------------------------------------------------------------------ #
# Organizations
# ------------------------------------------------------------------ #
class OrganizationFactory(DjangoModelFactory):
    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: f"Organization {n}")
    slug = factory.Sequence(lambda n: f"org-{n}")
    is_active = True


class OrganizationMemberFactory(DjangoModelFactory):
    class Meta:
        model = OrganizationMember

    organization = factory.SubFactory(OrganizationFactory)
    user = factory.SubFactory(UserFactory)
    role = "member"


# ------------------------------------------------------------------ #
# Projects
# ------------------------------------------------------------------ #
class ProjectFactory(DjangoModelFactory):
    class Meta:
        model = Project

    name = factory.Sequence(lambda n: f"Project {n}")
    slug = factory.Sequence(lambda n: f"project-{n}")
    prefix = factory.Sequence(lambda n: f"P{n:02d}")
    organization = factory.SubFactory(OrganizationFactory)
    created_by = factory.SubFactory(UserFactory)
    status = "active"


class ProjectMemberFactory(DjangoModelFactory):
    class Meta:
        model = ProjectMember

    project = factory.SubFactory(ProjectFactory)
    user = factory.SubFactory(UserFactory)
    role = "member"


class BoardFactory(DjangoModelFactory):
    class Meta:
        model = Board

    name = factory.Sequence(lambda n: f"Board {n}")
    project = factory.SubFactory(ProjectFactory)
    is_default = True


class ColumnFactory(DjangoModelFactory):
    class Meta:
        model = Column

    name = factory.Sequence(lambda n: f"Column {n}")
    board = factory.SubFactory(BoardFactory)
    position = factory.Sequence(lambda n: n)
    is_done_column = False


# ------------------------------------------------------------------ #
# Tasks
# ------------------------------------------------------------------ #
class TaskFactory(DjangoModelFactory):
    class Meta:
        model = Task

    title = factory.Sequence(lambda n: f"Task {n}")
    description = factory.Faker("paragraph")
    status = "todo"
    priority = "medium"
    column = factory.SubFactory(ColumnFactory)
    reporter = factory.SubFactory(UserFactory)
    position = factory.Sequence(lambda n: n)
    task_number = factory.Sequence(lambda n: n + 1)


class CommentFactory(DjangoModelFactory):
    class Meta:
        model = Comment

    task = factory.SubFactory(TaskFactory)
    author = factory.SubFactory(UserFactory)
    content = factory.Faker("paragraph")


# ------------------------------------------------------------------ #
# Notifications
# ------------------------------------------------------------------ #
class NotificationFactory(DjangoModelFactory):
    class Meta:
        model = Notification

    recipient = factory.SubFactory(UserFactory)
    notification_type = NotificationType.TASK_ASSIGNED
    title = factory.Sequence(lambda n: f"Notification {n}")
    message = factory.Faker("sentence")
