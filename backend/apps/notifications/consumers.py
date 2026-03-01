"""
WebSocket consumers for real-time notifications and board updates.
"""

import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time user notifications.
    Each connected user joins their personal notification group.
    """

    async def connect(self):
        self.user = self.scope.get("user")

        if not self.user or self.user.is_anonymous:
            await self.close(code=4001)
            return

        self.group_name = f"user_{self.user.id}_notifications"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send unread count on connect
        unread_count = await self._get_unread_count()
        await self.send_json({
            "type": "unread_count",
            "count": unread_count,
        })

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        """Handle incoming messages from the client."""
        msg_type = content.get("type")

        if msg_type == "mark_read":
            notification_id = content.get("notification_id")
            if notification_id:
                await self._mark_notification_read(notification_id)
                unread_count = await self._get_unread_count()
                await self.send_json({
                    "type": "unread_count",
                    "count": unread_count,
                })

    # ── Group message handlers ──

    async def notification_new(self, event):
        """Handle new notification broadcast from the group."""
        await self.send_json({
            "type": "new_notification",
            "notification": event["notification"],
        })

    async def notification_count(self, event):
        """Handle unread count update."""
        await self.send_json({
            "type": "unread_count",
            "count": event["count"],
        })

    # ── Database helpers ──

    @database_sync_to_async
    def _get_unread_count(self) -> int:
        from apps.notifications.models import Notification

        return Notification.objects.filter(
            recipient=self.user,
            is_read=False,
        ).count()

    @database_sync_to_async
    def _mark_notification_read(self, notification_id: str):
        from apps.notifications.models import Notification

        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=self.user,
            )
            notification.mark_as_read()
        except Notification.DoesNotExist:
            pass


class BoardConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time board updates.
    Users join a board-specific group to receive live task changes.
    """

    async def connect(self):
        self.user = self.scope.get("user")

        if not self.user or self.user.is_anonymous:
            await self.close(code=4001)
            return

        self.board_id = self.scope["url_route"]["kwargs"]["board_id"]
        self.group_name = f"board_{self.board_id}"

        # Verify membership
        has_access = await self._check_board_access()
        if not has_access:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        logger.info(
            "User %s connected to board %s",
            self.user.email,
            self.board_id,
        )

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        """Handle incoming messages (e.g., cursor position, typing indicator)."""
        msg_type = content.get("type")

        if msg_type == "cursor_position":
            # Broadcast cursor position to other board viewers
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "board.cursor",
                    "user_id": str(self.user.id),
                    "user_name": self.user.full_name,
                    "position": content.get("position", {}),
                },
            )

    # ── Group message handlers ──

    async def board_task_event(self, event):
        """Handle task creation, update, move, or delete events."""
        await self.send_json({
            "type": event["event"],
            "task_id": event.get("task_id"),
            "task_key": event.get("task_key"),
            "column_id": event.get("column_id"),
            "position": event.get("position"),
        })

    async def board_cursor(self, event):
        """Handle cursor position broadcasts (collaborative view)."""
        # Don't send cursor back to the originating user
        if event.get("user_id") != str(self.user.id):
            await self.send_json({
                "type": "cursor_position",
                "user_id": event["user_id"],
                "user_name": event["user_name"],
                "position": event["position"],
            })

    # ── Database helpers ──

    @database_sync_to_async
    def _check_board_access(self) -> bool:
        """Verify that the user has access to this board's project."""
        from apps.projects.models import Board, ProjectMember

        try:
            board = Board.objects.select_related("project").get(id=self.board_id)
            return ProjectMember.objects.filter(
                project=board.project,
                user=self.user,
                is_active=True,
            ).exists()
        except Board.DoesNotExist:
            return False
