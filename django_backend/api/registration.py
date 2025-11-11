from typing import Any, Dict, Tuple

from django.contrib.auth import get_user_model, password_validation
from django.db import IntegrityError, transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


# PUBLIC_INTERFACE
class RegisterSerializer(serializers.Serializer):
    """Validate and create a new user account.

    Required fields:
      - username: string (unique)
      - email: string (unique, valid email)
      - password: string (must pass Django password validators)

    Optional fields:
      - first_name, last_name
      - role (defaults to "learner" if model supports it)
      - auto_login: boolean (not a model field; if true returns JWT token pair)
    """
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    role = serializers.CharField(required=False, allow_blank=True, max_length=32)
    auto_login = serializers.BooleanField(required=False, default=True)

    def validate_username(self, value: str) -> str:
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(_("Username already in use."))
        return value

    def validate_email(self, value: str) -> str:
        # Normalize email case-insensitively for uniqueness
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(_("Email already in use."))
        return value

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        # Run Django's password validators in context of a user (with provided username/email)
        temp_user = User(username=attrs.get("username"), email=attrs.get("email"))
        try:
            password_validation.validate_password(password=attrs.get("password"), user=temp_user)
        except Exception as exc:
            # Convert any validator exceptions to DRF-friendly error
            raise serializers.ValidationError({"password": [str(x) for x in (exc,)]}) from exc
        return attrs

    @transaction.atomic
    def create(self, validated_data: Dict[str, Any]) -> Tuple[User, bool]:
        auto_login: bool = bool(validated_data.pop("auto_login", True))
        role = validated_data.pop("role", None)
        password = validated_data.pop("password")
        # Only set role if the User model defines it
        user_fields = {k: v for k, v in validated_data.items() if k in {"username", "email", "first_name", "last_name"}}
        try:
            user = User.objects.create_user(**user_fields, password=password)
            # Set role only if model has attribute and role provided
            if role and hasattr(user, "role"):
                setattr(user, "role", role or getattr(user, "role", "learner"))
                user.save(update_fields=["role"])
        except IntegrityError as e:
            # Additional safety net against race conditions
            raise serializers.ValidationError(_("Username or Email already exists.")) from e
        return user, auto_login


# PUBLIC_INTERFACE
@api_view(["POST"])
@permission_classes([AllowAny])
def register(request: Request) -> Response:
    """
    User Registration endpoint.

    Summary:
    - Creates a new user account with username, email, and password.
    - Enforces password validators and uniqueness of username/email.
    - Returns the created user's public profile fields.
    - If auto_login=true (default), also returns JWT tokens (refresh, access).

    Request Body (JSON):
    - username: string (required)
    - email: string (required)
    - password: string (required)
    - first_name: string (optional)
    - last_name: string (optional)
    - role: string (optional; defaults to "learner" if supported by model)
    - auto_login: boolean (optional; default true)

    Response:
    - 201 Created:
      {
        "user": {
          "id": number,
          "username": string,
          "first_name": string,
          "last_name": string,
          "email": string,
          "role": string,
          "job_title": string,
          "department": string,
          "avatar": string
        },
        "tokens": { "refresh": "...", "access": "..." }   // only if auto_login
      }
    - 400 Bad Request: validation errors
    """
    # Log path for diagnostic purposes (helps confirm alias and trailing slash behavior)
    try:
        print(f"[auth.register] POST {request.get_full_path()}")
    except Exception:
        pass

    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user, auto_login = serializer.save()

    # Build public user payload aligned with existing UserSerializer fields.
    user_payload = {
        "id": user.id,
        "username": user.username,
        "first_name": getattr(user, "first_name", ""),
        "last_name": getattr(user, "last_name", ""),
        "email": user.email,
        "role": getattr(user, "role", "learner") if hasattr(user, "role") else "learner",
        "job_title": getattr(user, "job_title", ""),
        "department": getattr(user, "department", ""),
        "avatar": getattr(user, "avatar", ""),
    }

    resp: Dict[str, Any] = {"user": user_payload}
    if auto_login:
        refresh = RefreshToken.for_user(user)
        resp["tokens"] = {"refresh": str(refresh), "access": str(refresh.access_token)}
    return Response(resp, status=status.HTTP_201_CREATED)
