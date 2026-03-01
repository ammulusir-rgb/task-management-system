"""
Project signals — auto-create default board and columns.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Board, Column, Project

logger = logging.getLogger(__name__)

DEFAULT_COLUMNS = [
    {"name": "Backlog", "color": "#6C757D", "position": 0, "is_done_column": False},
    {"name": "To Do", "color": "#0D6EFD", "position": 1, "is_done_column": False},
    {"name": "In Progress", "color": "#FFC107", "position": 2, "is_done_column": False},
    {"name": "In Review", "color": "#0DCAF0", "position": 3, "is_done_column": False},
    {"name": "Done", "color": "#198754", "position": 4, "is_done_column": True},
]


@receiver(post_save, sender=Project)
def create_default_board(sender, instance, created, **kwargs):
    """
    Auto-create a default Kanban board with standard columns
    when a new project is created.
    """
    if not created:
        return

    board = Board.objects.create(
        project=instance,
        name="Main Board",
        is_default=True,
    )

    columns = [
        Column(board=board, **col_data)
        for col_data in DEFAULT_COLUMNS
    ]
    Column.objects.bulk_create(columns)

    logger.info(
        "Created default board with %d columns for project '%s'",
        len(columns),
        instance.name,
    )
