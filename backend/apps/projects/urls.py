"""
URL patterns for projects, boards, and columns.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BoardViewSet, ColumnViewSet, ProjectViewSet

app_name = "projects"

router = DefaultRouter()
router.register(r"", ProjectViewSet, basename="project")

# Nested routes for boards and columns
board_router = DefaultRouter()
board_router.register(r"", BoardViewSet, basename="board")

column_router = DefaultRouter()
column_router.register(r"", ColumnViewSet, basename="column")

urlpatterns = [
    path("", include(router.urls)),
    path("boards/", include(board_router.urls)),
    path("columns/", include(column_router.urls)),
]
