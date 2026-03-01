"""Tests for the Projects app."""

import pytest
from rest_framework import status

from apps.projects.models import Board, Column, Project, ProjectMember
from tests.factories import ProjectFactory, UserFactory


@pytest.mark.django_db
class TestProjectCRUD:
    url = "/api/v1/projects/"

    def test_create_project(self, authenticated_client, organization, user):
        response = authenticated_client.post(
            self.url,
            {
                "name": "New Project",
                "organization": str(organization.id),
                "prefix": "NP",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        proj = Project.objects.get(name="New Project")
        assert ProjectMember.objects.filter(
            project=proj, user=user, role="admin"
        ).exists()

    def test_list_projects(self, authenticated_client, project):
        response = authenticated_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1

    def test_update_project(self, authenticated_client, project):
        response = authenticated_client.patch(
            f"{self.url}{project.id}/",
            {"name": "Updated Project"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

    def test_archive_project(self, authenticated_client, project):
        response = authenticated_client.post(f"{self.url}{project.id}/archive/")
        assert response.status_code == status.HTTP_200_OK
        project.refresh_from_db()
        assert project.status == "archived"

    def test_restore_project(self, authenticated_client, project):
        project.status = "archived"
        project.save()
        response = authenticated_client.post(f"{self.url}{project.id}/restore/")
        assert response.status_code == status.HTTP_200_OK
        project.refresh_from_db()
        assert project.status == "active"


@pytest.mark.django_db
class TestDefaultBoardCreation:
    """Signal should auto-create a default board with 5 columns."""

    def test_board_auto_created(self, project):
        boards = Board.objects.filter(project=project)
        assert boards.count() >= 1

    def test_columns_auto_created(self, project):
        board = Board.objects.filter(project=project).first()
        if board:
            columns = Column.objects.filter(board=board)
            assert columns.count() == 5


@pytest.mark.django_db
class TestColumnReorder:
    def test_reorder_columns(self, authenticated_client, board, columns):
        url = f"/api/v1/columns/reorder/"
        new_order = [col.id for col in reversed(columns)]
        response = authenticated_client.post(
            url,
            {"column_ids": [str(cid) for cid in new_order]},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
