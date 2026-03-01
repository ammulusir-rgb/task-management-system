"""
Custom middleware for the Task Management SaaS.
"""

import json
import logging
import time
import uuid

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("apps.common.middleware")


class RequestTimingMiddleware(MiddlewareMixin):
    """
    Logs the time taken to process each request.
    Adds X-Request-Time header to the response.
    """

    def process_request(self, request):
        request._start_time = time.monotonic()
        request._request_id = str(uuid.uuid4())[:8]

    def process_response(self, request, response):
        if hasattr(request, "_start_time"):
            duration = time.monotonic() - request._start_time
            duration_ms = round(duration * 1000, 2)
            response["X-Request-Time"] = f"{duration_ms}ms"
            response["X-Request-ID"] = getattr(request, "_request_id", "unknown")

            if duration > 1.0:  # Log slow requests (> 1 second)
                logger.warning(
                    "Slow request: %s %s took %sms [%s]",
                    request.method,
                    request.path,
                    duration_ms,
                    request._request_id,
                )
        return response


class AuditLogMiddleware(MiddlewareMixin):
    """
    Logs all mutating API requests for audit purposes.
    Captures: method, path, user, timestamp, IP address, status code.
    """

    MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    def process_response(self, request, response):
        if request.method not in self.MUTATING_METHODS:
            return response

        if not request.path.startswith("/api/"):
            return response

        user = getattr(request, "user", None)
        user_info = "anonymous"
        if user and user.is_authenticated:
            user_info = f"{user.email} (id={user.id})"

        logger.info(
            "AUDIT: %s %s | User: %s | Status: %s | IP: %s",
            request.method,
            request.path,
            user_info,
            response.status_code,
            self._get_client_ip(request),
        )
        return response

    @staticmethod
    def _get_client_ip(request) -> str:
        """Extract the real client IP, considering proxies."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")
