from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import JsonResponse
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class UsernameOrEmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer that accepts either:
      - identifier + password (identifier can be username or email), or
      - username + password (backward compatible with SimpleJWT default)
    It resolves the identifier to a username before delegating to the base logic.
    """

    identifier = serializers.CharField(required=False, allow_blank=False)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        identifier = attrs.get("identifier")
        username = attrs.get(self.username_field)
        password = attrs.get("password")

        # Shape basic field errors early
        field_errors = {}
        if not (identifier or username):
            field_errors[self.username_field] = [_("Username or identifier is required.")]
        if not password:
            field_errors["password"] = [_("Password is required.")]
        if field_errors:
            raise serializers.ValidationError(field_errors)

        # If identifier provided, resolve to username via username or email match (case-insensitive for email)
        if identifier and not username:
            user = User.objects.filter(
                Q(username=identifier) | Q(email__iexact=identifier)
            ).first()
            if not user:
                # Use consistent message for invalid identifier to avoid leaking existence
                raise serializers.ValidationError({"detail": _("Invalid credentials.")})
            attrs[self.username_field] = user.username

        try:
            # Delegate to base class for password checking and token generation
            return super().validate(attrs)
        except serializers.ValidationError as exc:
            # Normalize error detail to a consistent structure
            detail = exc.detail if hasattr(exc, "detail") else exc.args
            # SimpleJWT may return {"detail": "..."} or {"no_active_account": "..."}; normalize both
            if isinstance(detail, dict):
                if "no_active_account" in detail:
                    raise serializers.ValidationError({"detail": _("Invalid credentials.")})
                raise
            raise serializers.ValidationError({"detail": _("Invalid credentials.")})


# PUBLIC_INTERFACE
class UsernameOrEmailTokenObtainPairView(TokenObtainPairView):
    """JWT token obtain endpoint that accepts either username/password or identifier/password (where identifier is username or email)."""

    serializer_class = UsernameOrEmailTokenObtainPairSerializer

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Issue an access/refresh token pair.

        Request body:
        - identifier: string (username or email) OR username: string
        - password: string

        Returns:
        - 200 OK with { "refresh": "...", "access": "..." } or 401 on failure.
        """
        # Lightweight log to help diagnose URL/path and APPEND_SLASH effects
        try:
            path_info = request.get_full_path()
            print(f"[auth.token] POST {path_info}")
        except Exception:
            pass

        # Ensure we always parse JSON when provided
        response = super().post(request, *args, **kwargs)

        # Normalize non-200 responses from SimpleJWT to keep JSON body with detail
        if response.status_code not in (status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED):
            response.status_code = status.HTTP_401_UNAUTHORIZED
        return response


# PUBLIC_INTERFACE
@api_view(['GET'])
@permission_classes([AllowAny])
def debug_auth_endpoint(request: Request):
    """Auth debug endpoint. Echoes resolved path, method, and trailing slash info."""
    info = {
        'resolved_path': request.path,
        'method': request.method,
        'has_trailing_slash': request.path.endswith('/'),
        'canonical_token_url': '/api/auth/token/',
        'canonical_register_url': '/api/auth/register/',
        'note': 'Use canonical URLs with trailing slash.',
    }
    try:
        print("[auth.debug]", info)
    except Exception:
        pass
    return JsonResponse(info)
