"""
Views for User authentication and profile management.
Implements JWT with HttpOnly cookie for refresh token.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.common.throttling import LoginRateThrottle, PasswordResetRateThrottle

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

User = get_user_model()


def _set_refresh_cookie(response, refresh_token: str) -> Response:
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
    return response


def _clear_refresh_cookie(response) -> Response:
    """Clear the refresh token cookie."""
    response.delete_cookie(
        key=settings.SIMPLE_JWT_COOKIE_NAME,
        path=settings.SIMPLE_JWT_COOKIE_PATH,
        samesite=settings.SIMPLE_JWT_COOKIE_SAMESITE,
    )
    return response


class RegisterView(generics.CreateAPIView):
    """
    Register a new user account.
    Returns JWT access token and sets refresh token cookie.
    """

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        refresh["email"] = user.email
        refresh["role"] = user.role
        refresh["full_name"] = user.full_name

        response_data = {
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data,
        }
        response = Response(response_data, status=status.HTTP_201_CREATED)
        _set_refresh_cookie(response, refresh)

        # Send welcome email asynchronously
        send_welcome_email.delay(user.id)

        return response


class CookieTokenObtainPairView(TokenObtainPairView):
    """
    Custom login view that:
    - Returns access token in response body
    - Sets refresh token in HttpOnly cookie
    """

    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [LoginRateThrottle]

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)

        if response.status_code == 200 and "refresh" in response.data:
            refresh_token = response.data.pop("refresh")
            _set_refresh_cookie(response, refresh_token)

        return response


class CookieTokenRefreshView(TokenRefreshView):
    """
    Custom token refresh view that:
    - Reads refresh token from HttpOnly cookie
    - Returns new access token in response body
    - Rotates refresh token cookie
    """

    def post(self, request, *args, **kwargs):
        # Get the refresh token from the cookie
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT_COOKIE_NAME)

        if not refresh_token:
            return Response(
                {"error": {"code": "no_refresh_token", "message": "Refresh token not found."}},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Use the token from the cookie
        serializer = self.get_serializer(data={"refresh": refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        response = Response({"access": serializer.validated_data["access"]})

        # Set the new rotated refresh token
        if "refresh" in serializer.validated_data:
            _set_refresh_cookie(response, serializer.validated_data["refresh"])

        return response


class LogoutView(APIView):
    """
    Logout: blacklist the refresh token and clear the cookie.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT_COOKIE_NAME)

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                pass  # Token already blacklisted or invalid — that's fine

        response = Response(
            {"message": "Successfully logged out."},
            status=status.HTTP_200_OK,
        )
        _clear_refresh_cookie(response)
        return response


class MeView(generics.RetrieveUpdateAPIView):
    """
    GET: Retrieve the authenticated user's profile.
    PATCH/PUT: Update the authenticated user's profile.
    """

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

        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"error": {"code": "invalid_password", "message": "Current password is incorrect."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])

        return Response({"message": "Password changed successfully."})


class PasswordResetRequestView(APIView):
    """Request a password reset email."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email, is_active=True)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            send_password_reset_email.delay(user.id, uid, token)
        except User.DoesNotExist:
            pass  # Don't reveal whether the email exists

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

        return Response(
            {"message": "Password has been reset successfully."},
            status=status.HTTP_200_OK,
        )


class IsAdminOrManager(permissions.BasePermission):
    """Allow only admin or manager users."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_manager


class UserManagementViewSet(ModelViewSet):
    """
    Admin viewset for managing users.
    Only accessible by admin/manager users.
    """

    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        qs = User.objects.all().order_by("-date_joined")
        search = self.request.query_params.get("search")
        role = self.request.query_params.get("role")
        is_active = self.request.query_params.get("is_active")
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )
        if role:
            qs = qs.filter(role=role)
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return AdminUserCreateSerializer
        if self.action in ("partial_update", "update"):
            return AdminUserUpdateSerializer
        return UserSerializer

    def perform_destroy(self, instance):
        """Soft-deactivate instead of hard delete."""
        instance.is_active = False
        instance.save(update_fields=["is_active"])
