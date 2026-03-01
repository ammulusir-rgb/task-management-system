"""
JWT Authentication Middleware for Django Channels WebSocket connections.
Extracts JWT from query string parameter and authenticates the user.
"""

import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

logger = logging.getLogger(__name__)

User = get_user_model()


@database_sync_to_async
def get_user_from_token(token_str: str):
    """Validate a JWT access token and return the corresponding user."""
    try:
        token = AccessToken(token_str)
        user_id = token.get("user_id")
        if user_id:
            return User.objects.get(id=user_id, is_active=True)
    except (InvalidToken, TokenError) as e:
        logger.debug("Invalid WebSocket token: %s", e)
    except User.DoesNotExist:
        logger.debug("User from WebSocket token not found")
    except Exception as e:
        logger.warning("WebSocket auth error: %s", e)

    return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom middleware for Django Channels that authenticates
    WebSocket connections using JWT passed as a query parameter.

    Usage in ASGI routing:
        JWTAuthMiddleware(URLRouter(websocket_urlpatterns))

    Client-side connection:
        new WebSocket('ws://host/ws/path/?token=<access_token>')
    """

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)

        token_list = query_params.get("token", [])
        token_str = token_list[0] if token_list else None

        if token_str:
            scope["user"] = await get_user_from_token(token_str)
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)
