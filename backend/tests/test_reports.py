"""Tests for the Reports app."""

import pytest
from rest_framework import status

from tests.factories import TaskFactory


@pytest.mark.django_db
class TestReportEndpoints:
    def _url(self, project_id, action):
        return f"/api/v1/projects/{project_id}/reports/{action}/"

    def test_summary(self, authenticated_client, project, columns):
        TaskFactory(column=columns[0], reporter=None, status="todo")
        TaskFactory(column=columns[4], reporter=None, status="done")

        response = authenticated_client.get(
            self._url(project.id, "summary")
        )
        assert response.status_code == status.HTTP_200_OK
        assert "total_tasks" in response.data
        assert "completion_rate" in response.data

    def test_tasks_by_status(self, authenticated_client, project, columns):
        TaskFactory(column=columns[0], status="todo")
        TaskFactory(column=columns[2], status="in_progress")

        response = authenticated_client.get(
            self._url(project.id, "tasks-by-status")
        )
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_tasks_by_priority(self, authenticated_client, project, columns):
        TaskFactory(column=columns[0], priority="high")
        TaskFactory(column=columns[0], priority="low")

        response = authenticated_client.get(
            self._url(project.id, "tasks-by-priority")
        )
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_burndown(self, authenticated_client, project, columns):
        response = authenticated_client.get(
            self._url(project.id, "burndown") + "?days=14"
        )
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        if response.data:
            assert "date" in response.data[0]
            assert "remaining" in response.data[0]

    def test_velocity(self, authenticated_client, project, columns):
        response = authenticated_client.get(
            self._url(project.id, "velocity") + "?weeks=4"
        )
        assert response.status_code == status.HTTP_200_OK

    def test_export_csv(self, authenticated_client, project, columns):
        TaskFactory(column=columns[0])
        response = authenticated_client.get(
            self._url(project.id, "export-csv")
        )
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "text/csv"
        assert "attachment" in response["Content-Disposition"]

    def test_non_member_denied(self, api_client, project, columns):
        from tests.factories import UserFactory

        outsider = UserFactory()
        api_client.force_authenticate(user=outsider)
        response = api_client.get(self._url(project.id, "summary"))
        assert response.status_code == status.HTTP_403_FORBIDDEN
