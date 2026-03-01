"""Tests for the Tasks app."""

import pytest
from rest_framework import status

from apps.tasks.models import Comment, Task
from tests.factories import CommentFactory, TaskFactory, UserFactory


@pytest.mark.django_db
class TestTaskCRUD:
    url = "/api/v1/tasks/"

    def test_create_task(self, authenticated_client, columns, user):
        response = authenticated_client.post(
            self.url,
            {
                "title": "New Task",
                "column": str(columns[0].id),
                "priority": "high",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Task.objects.filter(title="New Task").exists()

    def test_list_tasks(self, authenticated_client, columns, user):
        TaskFactory(column=columns[0], reporter=user)
        TaskFactory(column=columns[1], reporter=user)
        response = authenticated_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 2

    def test_retrieve_task(self, authenticated_client, columns, user):
        task = TaskFactory(column=columns[0], reporter=user)
        response = authenticated_client.get(f"{self.url}{task.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == task.title

    def test_update_task(self, authenticated_client, columns, user):
        task = TaskFactory(column=columns[0], reporter=user)
        response = authenticated_client.patch(
            f"{self.url}{task.id}/",
            {"title": "Updated Title", "priority": "urgent"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.title == "Updated Title"

    def test_delete_task_soft(self, authenticated_client, columns, user):
        task = TaskFactory(column=columns[0], reporter=user)
        response = authenticated_client.delete(f"{self.url}{task.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        task.refresh_from_db()
        assert task.deleted_at is not None


@pytest.mark.django_db
class TestTaskMove:
    def test_move_task_to_column(self, authenticated_client, columns, user):
        task = TaskFactory(column=columns[0], reporter=user, position=0)
        url = f"/api/v1/tasks/{task.id}/move/"
        response = authenticated_client.post(
            url,
            {"column_id": str(columns[2].id), "position": 0},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.column == columns[2]


@pytest.mark.django_db
class TestTaskFiltering:
    url = "/api/v1/tasks/"

    def test_filter_by_status(self, authenticated_client, columns, user):
        TaskFactory(column=columns[0], reporter=user, status="todo")
        TaskFactory(column=columns[2], reporter=user, status="in_progress")

        response = authenticated_client.get(f"{self.url}?status=todo")
        assert response.status_code == status.HTTP_200_OK
        for task in response.data.get("results", []):
            assert task["status"] == "todo"

    def test_filter_by_priority(self, authenticated_client, columns, user):
        TaskFactory(column=columns[0], reporter=user, priority="urgent")
        TaskFactory(column=columns[0], reporter=user, priority="low")

        response = authenticated_client.get(f"{self.url}?priority=urgent")
        assert response.status_code == status.HTTP_200_OK
        for task in response.data.get("results", []):
            assert task["priority"] == "urgent"

    def test_search(self, authenticated_client, columns, user):
        TaskFactory(column=columns[0], reporter=user, title="Fix login bug")
        TaskFactory(column=columns[0], reporter=user, title="Design dashboard")

        response = authenticated_client.get(f"{self.url}?search=login")
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestTaskComments:
    def test_add_comment(self, authenticated_client, columns, user):
        task = TaskFactory(column=columns[0], reporter=user)
        url = f"/api/v1/tasks/{task.id}/comments/"
        response = authenticated_client.post(
            url,
            {"content": "This is a test comment"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Comment.objects.filter(task=task).exists()

    def test_list_comments(self, authenticated_client, columns, user):
        task = TaskFactory(column=columns[0], reporter=user)
        CommentFactory(task=task, author=user)
        CommentFactory(task=task, author=user)

        url = f"/api/v1/tasks/{task.id}/comments/"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
