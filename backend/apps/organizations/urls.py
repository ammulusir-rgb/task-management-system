"""URL patterns for organizations."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import OrganizationViewSet, TeamViewSet

app_name = "organizations"

router = DefaultRouter()
router.register(r"", OrganizationViewSet, basename="organization")

team_router = DefaultRouter()
team_router.register(r"", TeamViewSet, basename="team")

urlpatterns = router.urls + [
    path("teams/", include(team_router.urls)),
]
