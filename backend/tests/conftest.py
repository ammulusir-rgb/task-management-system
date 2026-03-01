"""conftest.py — shared pytest fixtures for the entire test suite."""

import pytest
from rest_framework.test import APIClient

from apps.organizations.models import Organization, OrganizationMember
from apps.projects.models import Board, Column, Project, ProjectMember
from apps.users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="testuser@example.com",
        password="Testpass123!",
        first_name="Test",
        last_name="User",
        is_verified=True,
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email="admin@example.com",
        password="Adminpass123!",
        first_name="Admin",
        last_name="User",
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        email="other@example.com",
        password="Otherpass123!",
        first_name="Other",
        last_name="User",
        is_verified=True,
    )


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def organization(db, user):
    org = Organization.objects.create(
        name="Test Org",
        slug="test-org",
    )
    OrganizationMember.objects.create(
        organization=org,
        user=user,
        role="owner",
    )
    return org


@pytest.fixture
def project(db, organization, user):
    proj = Project.objects.create(
        name="Test Project",
        slug="test-project",
        prefix="TST",
        organization=organization,
        created_by=user,
    )
    ProjectMember.objects.create(
        project=proj,
        user=user,
        role="admin",
    )
    return proj


@pytest.fixture
def board(db, project):
    return Board.objects.create(
        name="Main Board",
        project=project,
        is_default=True,
    )


@pytest.fixture
def columns(db, board):
    cols = []
    for i, name in enumerate(["Backlog", "To Do", "In Progress", "In Review", "Done"]):
        cols.append(
            Column.objects.create(
                name=name,
                board=board,
                position=i,
                is_done_column=(name == "Done"),
            )
        )
    return cols
