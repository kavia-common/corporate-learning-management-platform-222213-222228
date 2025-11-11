from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

# PUBLIC_INTERFACE
@api_view(["GET"])
def health(request):
    """
    Health check endpoint.

    Summary:
    - Returns server readiness status.

    Returns:
      200 OK with {"message": "Server is up!"}
    """
    return Response({"message": "Server is up!"})

# PUBLIC_INTERFACE
@api_view(["GET"])
@permission_classes([AllowAny])
def auth_ping(request):
    """
    Authentication ping endpoint.

    Summary:
    - Lightweight endpoint to verify frontend-backend connectivity and canonical auth URL paths.

    Returns:
      200 OK with {"ok": true, "paths": {...}, "requested_path": "<path>"}
    """
    try:
        full_url = request.build_absolute_uri()
    except Exception:
        full_url = None

    paths = {
        "token": "/api/auth/token/",
        "token_no_slash": "/api/auth/token",
        "register": "/api/auth/register/",
        "register_no_slash": "/api/auth/register",
        "refresh": "/api/auth/token/refresh/",
        "verify": "/api/auth/token/verify/",
        "login": "/api/auth/login/",
        "health": "/api/health/",
    }
    print(f"[auth.ping] GET {request.get_full_path()} -> {full_url}")
    return Response({"ok": True, "paths": paths, "requested_path": request.get_full_path(), "url": full_url})
