from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView, TokenVerifyView
)
from .views import health
from .viewsets import (
    CourseViewSet, ModuleViewSet, LessonViewSet, EnrollmentViewSet,
    QuizViewSet, QuestionViewSet, ChoiceViewSet, QuizAttemptViewSet,
    CertificateViewSet, LearningPathViewSet, NotificationViewSet,
    ReportingViewSet, sso_login_start, sso_callback
)
from .auth import UsernameOrEmailTokenObtainPairView
from .registration import register  # new

router = DefaultRouter()
router.register(r"courses", CourseViewSet, basename="courses")
router.register(r"modules", ModuleViewSet, basename="modules")
router.register(r"lessons", LessonViewSet, basename="lessons")
router.register(r"enrollments", EnrollmentViewSet, basename="enrollments")
router.register(r"quizzes", QuizViewSet, basename="quizzes")
router.register(r"questions", QuestionViewSet, basename="questions")
router.register(r"choices", ChoiceViewSet, basename="choices")
router.register(r"attempts", QuizAttemptViewSet, basename="attempts")
router.register(r"certificates", CertificateViewSet, basename="certificates")
router.register(r"paths", LearningPathViewSet, basename="learning-paths")
router.register(r"notifications", NotificationViewSet, basename="notifications")
router.register(r"reporting", ReportingViewSet, basename="reporting")

# PUBLIC_INTERFACE
urlpatterns = [
    path("health/", health, name="Health"),
    # Auth - Registration
    path("auth/register/", register, name="auth_register"),
    # Auth - JWT (custom view supports username or email)
    path("auth/token/", UsernameOrEmailTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # SSO placeholders
    path("auth/sso/start/", sso_login_start, name="sso_start"),
    path("auth/sso/callback/", sso_callback, name="sso_callback"),
    # Router
    path("", include(router.urls)),
]
