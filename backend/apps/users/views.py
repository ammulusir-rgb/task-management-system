"""
Views for User authentication and profile management.
Endpoint definitions only — all business logic lives in managers.py.
"""

from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.common.throttling import LoginRateThrottle, PasswordResetRateThrottle

from .managers import user_manager
from .serializers import (
    AdminUserCreateSerializer,
    AdminUserUpdateSerializer,
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from .tasks import send_password_reset_email, send_welcome_email


# ── Cookie helpers ────────────────────────────────────────────────────────────

def _set_refresh_cookie(response, refresh_token: str) -> None:
    """Set the refresh token as an HttpOnly cookie."""
    response.set_cookie(
        key=settings.SIMPLE_JWT_COOKIE_NAME,
        value=str(refresh_token),
        httponly=settings.SIMPLE_JWT_COOKIE_HTTPONLY,
        samesite=settings.SIMPLE_JWT_COOKIE_SAMESITE,
        secure=settings.SIMPLE_JWT_COOKIE_SECURE,
        path=settings.SIMPLE_JWT_COOKIE_PATH,
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
    )


def _clear_refresh_cookie(response) -> None:
    """Clear the refresh token cookie."""
    response.delete_cookie(
        key=settings.SIMPLE_JWT_COOKIE_NAME,
        path=settings.SIMPLE_JWT_COOKIE_PATH,
        samesite=settings.SIMPLE_JWT_COOKIE_SAMESITE,
    )


# ── Auth Views ────────────────────────────────────────────────────────────────

class RegisterView(generics.CreateAPIView):
    """Register a new user — issues tokens on success."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        refresh["email"] = user.email
        refresh["role"] = user.role
        refresh["full_name"] = user.full_name

        response = Response(
            {"access": str(refresh.access_token), "user": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )
        _set_refresh_cookie(response, refresh)
        send_welcome_email.delay(user.id)
        return response


class CookieTokenObtainPairView(TokenObtainPairView):
    """Login: return access token in body, set refresh token in HttpOnly cookie."""

    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [LoginRateThrottle]

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if response.status_code == 200 and "refresh" in response.data:
            _set_refresh_cookie(response, response.data.pop("refresh"))
        return response


class CookieTokenRefreshView(TokenRefreshView):
    """Refresh access token using the HttpOnly cookie."""

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT_COOKIE_NAME)
        if not refresh_token:
            return Response(
                {"error": {"code": "no_refresh_token", "message": "Refresh token not found."}},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        serializer = self.get_serializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as exc:
            raise InvalidToken(exc.args[0])
        response = Response({"access": serializer.validated_data["access"]})
        if "refresh" in serializer.validated_data:
            _set_refresh_cookie(response, serializer.validated_data["refresh"])
        return response


class LogoutView(APIView):
    """Logout: blacklist refresh token and clear the cookie."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT_COOKIE_NAME)
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError:
                pass

        response = Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
        _clear_refresh_cookie(response)
        return response


# ── Profile Views ─────────────────────────────────────────────────────────────

class MeView(generics.RetrieveUpdateAPIView):
    """GET / PATCH the authenticated user's profile."""

    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserUpdateSerializer
        return UserSerializer


class ChangePasswordView(APIView):
    """Change the authenticated user's password."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_manager.change_password(
            request.user,
            serializer.validated_data["old_password"],
            serializer.validated_data["new_password"],
        )
        return Response({"message": "Password changed successfully."})


# ── Password Reset Views ──────────────────────────────────────────────────────

class PasswordResetRequestView(APIView):
    """Request a password reset email."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_manager.request_password_reset(
            serializer.validated_data["email"],
            send_password_reset_email,
        )
        return Response(
            {"message": "If the email exists, a password reset link has been sent."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """Confirm a password reset with the token."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)


# ── Admin User Management ─────────────────────────────────────────────────────

class IsAdminOrManager(permissions.BasePermission):
    """Allow only admin or manager users."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_manager


class UserManagementViewSet(ModelViewSet):
    """Admin viewset for managing users (accessible by admin/manager only)."""

    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        return user_manager.get_user_queryset(
            search=self.request.query_params.get("search"),
            role=self.request.query_params.get("role"),
            is_active=self.request.query_params.get("is_active"),
        )

    def get_serializer_class(self):
        if self.action == "create":
            return AdminUserCreateSerializer
        if self.action in ("partial_update", "update"):
            return AdminUserUpdateSerializer
        return UserSerializer

    def perform_destroy(self, instance):
        user_manager.deactivate_user(instance)
