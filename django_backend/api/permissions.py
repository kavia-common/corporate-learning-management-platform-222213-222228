from rest_framework.permissions import BasePermission, SAFE_METHODS

ROLE_ADMIN = "admin"
ROLE_MANAGER = "manager"
ROLE_INSTRUCTOR = "instructor"
ROLE_LEARNER = "learner"


# PUBLIC_INTERFACE
class IsAdmin(BasePermission):
    """Allow only admin role."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == ROLE_ADMIN)


# PUBLIC_INTERFACE
class IsInstructorOrAdmin(BasePermission):
    """Allow instructors or admins."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.role in (ROLE_INSTRUCTOR, ROLE_ADMIN)))


# PUBLIC_INTERFACE
class ReadOnly(BasePermission):
    """Allow read-only methods."""

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


# PUBLIC_INTERFACE
class IsSelfOrAdmin(BasePermission):
    """Allow user to access self or admin."""

    def has_object_permission(self, request, view, obj):
        user = request.user
        return bool(user and user.is_authenticated and (obj == user or user.role == ROLE_ADMIN))
