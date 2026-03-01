"""
WebSocket URL routing for Django Channels.
"""

from django.urls import re_path

from .consumers import BoardConsumer, NotificationConsumer

websocket_urlpatterns = [
    re_path(r"ws/notifications/$", NotificationConsumer.as_asgi()),
    re_path(r"ws/board/(?P<board_id>[0-9a-f-]+)/$", BoardConsumer.as_asgi()),
]
