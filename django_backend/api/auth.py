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
      - username + password (SimpleJWT default).
    Returns consistent field-level errors for missing inputs and a normalized 'detail' for auth failures.
    """

    # Explicitly declare username to ensure DRF generates error messages when missing
    username = serializers.CharField(required=False, allow_blank=False)
    identifier = serializers.CharField(required=False, allow_blank=False)
    password = serializers.CharField(write_only=True, trim_whitespace=False, required=True, allow_blank=False)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        identifier = attrs.get("identifier")
        username = attrs.get(self.username_field) or attrs.get("username")
        password = attrs.get("password")

        # Shape basic field errors early
        field_errors = {}
        if not (identifier or username):
            # Return both keys helpful for frontend forms
            field_errors[self.username_field] = [_("Username is required if identifier is not provided.")]
            field_errors["identifier"] = [_("Identifier is required if username is not provided.")]
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
        elif username:
            # Ensure serializer attribute for SimpleJWT base
            attrs[self.username_field] = username

        try:
            # Delegate to base class for password checking and token generation
            return super().validate(attrs)
        except serializers.ValidationError as exc:
            # Normalize error detail to a consistent structure
            detail = getattr(exc, "detail", None) or exc.args
            if isinstance(detail, dict):
                # SimpleJWT may return {"detail": "..."} or {"no_active_account": "..."}; normalize both
                if "no_active_account" in detail:
                    raise serializers.ValidationError({"detail": _("Invalid credentials.")})
                if "detail" in detail:
                    # Keep detail but normalize status at view
                    raise
                # Any other dict -> generic invalid
                raise serializers.ValidationError({"detail": _("Invalid credentials.")})
            raise serializers.ValidationError({"detail": _("Invalid credentials.")})


# PUBLIC_INTERFACE
class UsernameOrEmailTokenObtainPairView(TokenObtainPairView):
    """JWT token obtain endpoint that accepts either username/password or identifier/password (where identifier is username or email)."""

    serializer_class = UsernameOrEmailTokenObtainPairSerializer

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Issue an access/refresh token pair.

        Request body (JSON, content-type application/json):
        - identifier: string (username or email) OR username: string
        - password: string

        Returns:
        - 200 OK with { "refresh": "...", "access": "..." } or 401 with {"detail": "..."} on failure.
        """
        # Lightweight log to help diagnose URL/path and APPEND_SLASH effects
        try:
            path_info = request.get_full_path()
            print(f"[auth.token] POST {path_info}")
        except Exception:
            pass

        # Delegate to SimpleJWT view which uses the serializer above
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
