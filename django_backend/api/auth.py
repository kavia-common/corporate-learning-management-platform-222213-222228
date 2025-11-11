from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

User = get_user_model()


class UsernameOrEmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer that accepts either:
      - identifier + password (identifier can be username or email), or
      - username + password (backward compatible with SimpleJWT default)
    It resolves the identifier to a username before delegating to the base logic.
    """

    # Accept an "identifier" field in addition to default "username"
    identifier = serializers.CharField(required=False, allow_blank=False)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        identifier = attrs.get("identifier")
        username = attrs.get(self.username_field)

        # If identifier provided, resolve to username via username or email match (case-insensitive for email)
        if identifier and not username:
            try:
                user = User.objects.filter(
                    Q(username=identifier) | Q(email__iexact=identifier)
                ).first()
                if user:
                    # Replace username field in attrs with resolved username for parent validation
                    attrs[self.username_field] = user.username
                else:
                    # Fail early to avoid leaking which field is wrong
                    raise serializers.ValidationError("Invalid credentials.")
            except Exception:
                raise serializers.ValidationError("Invalid credentials.")

        # Delegate to base class for password checking and token generation
        return super().validate(attrs)


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
        response = super().post(request, *args, **kwargs)
        # SimpleJWT returns 200 on success and 401 on failure by default
        if response.status_code not in (status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED):
            # Normalize other error codes to 401 for invalid creds
            response.status_code = status.HTTP_401_UNAUTHORIZED
        return response
