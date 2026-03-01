"""
Custom throttle classes.
"""

from rest_framework.throttling import AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """Stricter rate limit for login attempts."""

    rate = "5/minute"
    scope = "login"

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            return None  # No throttling for authenticated users
        ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class PasswordResetRateThrottle(AnonRateThrottle):
    """Rate limit for password reset requests."""

    rate = "3/hour"
    scope = "password_reset"
