"""Tests for the Organizations app."""

import pytest
from rest_framework import status

from apps.organizations.models import Organization, OrganizationMember
from tests.factories import OrganizationFactory, UserFactory


@pytest.mark.django_db
class TestOrganizationCRUD:
    url = "/api/v1/organizations/"

    def test_create_organization(self, authenticated_client, user):
        response = authenticated_client.post(
            self.url,
            {"name": "New Org"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        org = Organization.objects.get(name="New Org")
        # Creator should be owner
        assert OrganizationMember.objects.filter(
            organization=org, user=user, role="owner"
        ).exists()

    def test_list_organizations(self, authenticated_client, organization):
        response = authenticated_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1

    def test_retrieve_organization(self, authenticated_client, organization):
        response = authenticated_client.get(f"{self.url}{organization.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == organization.name

    def test_update_organization(self, authenticated_client, organization):
        response = authenticated_client.patch(
            f"{self.url}{organization.id}/",
            {"name": "Updated Org"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        organization.refresh_from_db()
        assert organization.name == "Updated Org"


@pytest.mark.django_db
class TestOrganizationMembers:
    def test_add_member(self, authenticated_client, organization):
        new_user = UserFactory()
        url = f"/api/v1/organizations/{organization.id}/add_member/"
        response = authenticated_client.post(
            url,
            {"user_id": str(new_user.id), "role": "member"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert OrganizationMember.objects.filter(
            organization=organization,
            user=new_user,
            role="member",
        ).exists()

    def test_list_members(self, authenticated_client, organization):
        url = f"/api/v1/organizations/{organization.id}/members/"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_cannot_remove_last_owner(self, authenticated_client, organization, user):
        url = f"/api/v1/organizations/{organization.id}/remove_member/"
        response = authenticated_client.post(
            url,
            {"user_id": str(user.id)},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_non_member_cannot_access(self, api_client, organization):
        other = UserFactory()
        api_client.force_authenticate(user=other)
        url = f"/api/v1/organizations/{organization.id}/"
        response = api_client.get(url)
        # Should either 404 or 403 depending on queryset filtering
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ]
