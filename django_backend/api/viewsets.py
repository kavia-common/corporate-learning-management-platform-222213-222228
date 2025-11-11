from django.db.models import Avg, Count, Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import (
    User, Course, Module, Lesson,
    Enrollment, LessonProgress, Quiz, Question, Choice,
    QuizAttempt, Certificate, LearningPath, LearningPathItem,
    Notification, AuditLog
)
from .serializers import (
    CourseSerializer, ModuleSerializer, LessonSerializer,
    EnrollmentSerializer,
    QuizSerializer, QuestionSerializer, ChoiceSerializer,
    QuizAttemptSerializer, CertificateSerializer,
    LearningPathSerializer,
    NotificationSerializer, ReportCourseProgressSerializer
)
from .permissions import IsInstructorOrAdmin, ReadOnly


def audit(actor: User | None, action: str, entity_type: str, entity_id: str, metadata: dict | None = None):
    AuditLog.objects.create(
        actor=actor, action=action, entity_type=entity_type, entity_id=str(entity_id),
        timestamp=timezone.now(), metadata=metadata or {}
    )


def notify_user(user_id: int, payload: dict):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(f"user_{user_id}", {"type": "notify", "payload": payload})


# PUBLIC_INTERFACE
class CourseViewSet(viewsets.ModelViewSet):
    """Manage courses. Instructors/Admins can create/update; read allowed to authenticated users; publish endpoint."""
    queryset = Course.objects.all().select_related("created_by")
    serializer_class = CourseSerializer
    permission_classes = [IsInstructorOrAdmin | ReadOnly]

    def perform_create(self, serializer):
        obj = serializer.save(created_by=self.request.user)
        audit(self.request.user, "course.create", "course", obj.id, {"title": obj.title})

    @action(detail=True, methods=["post"], permission_classes=[IsInstructorOrAdmin])
    def publish(self, request, pk=None):
        course = self.get_object()
        course.is_published = True
        course.save(update_fields=["is_published"])
        audit(request.user, "course.publish", "course", course.id)
        # notify enrolled users
        for e in course.enrollments.all():
            Notification.objects.create(user=e.user, title="Course published", message=f"{course.title} is now live.")
            notify_user(e.user_id, {"title": "Course published", "message": f"{course.title} is now live."})
        return Response({"status": "published"})


# PUBLIC_INTERFACE
class ModuleViewSet(viewsets.ModelViewSet):
    """Manage modules of courses."""
    queryset = Module.objects.all().select_related("course")
    serializer_class = ModuleSerializer
    permission_classes = [IsInstructorOrAdmin | ReadOnly]


# PUBLIC_INTERFACE
class LessonViewSet(viewsets.ModelViewSet):
    """Manage lessons."""
    queryset = Lesson.objects.all().select_related("module", "module__course")
    serializer_class = LessonSerializer
    permission_classes = [IsInstructorOrAdmin | ReadOnly]

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        lesson = self.get_object()
        lp, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
        lp.is_completed = True
        lp.completed_at = timezone.now()
        lp.save()
        audit(request.user, "lesson.complete", "lesson", lesson.id)
        # update course progress
        course = lesson.module.course
        total_lessons = Lesson.objects.filter(module__course=course).count() or 1
        completed = LessonProgress.objects.filter(user=request.user, lesson__module__course=course, is_completed=True).count()
        progress = round((completed / total_lessons) * 100, 2)
        Enrollment.objects.filter(user=request.user, course=course).update(progress_percent=progress)
        if completed == total_lessons:
            Enrollment.objects.filter(user=request.user, course=course).update(status="completed")
            cert, _ = Certificate.objects.get_or_create(user=request.user, course=course)
            Notification.objects.create(user=request.user, title="Certificate earned", message=f"You completed {course.title}.")
            notify_user(request.user.id, {"title": "Certificate earned", "message": f"You completed {course.title}."})
        return Response({"progress_percent": progress})


# PUBLIC_INTERFACE
class EnrollmentViewSet(viewsets.ModelViewSet):
    """Manage enrollments. Managers/Admins can enroll their team; users can list own."""
    queryset = Enrollment.objects.all().select_related("user", "course")
    serializer_class = EnrollmentSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in ("admin", "manager"):
            return super().get_queryset()
        return super().get_queryset().filter(user=user)

    def perform_create(self, serializer):
        obj = serializer.save()
        audit(self.request.user, "enrollment.create", "enrollment", obj.id, {"user": obj.user_id, "course": obj.course_id})
        Notification.objects.create(user=obj.user, title="Enrolled", message=f"You were enrolled to {obj.course.title}.")
        notify_user(obj.user_id, {"title": "Enrolled", "message": f"You were enrolled to {obj.course.title}."})


# PUBLIC_INTERFACE
class QuizViewSet(viewsets.ModelViewSet):
    """Manage quizzes."""
    queryset = Quiz.objects.all().select_related("course", "lesson")
    serializer_class = QuizSerializer
    permission_classes = [IsInstructorOrAdmin | ReadOnly]


# PUBLIC_INTERFACE
class QuestionViewSet(viewsets.ModelViewSet):
    """Manage questions."""
    queryset = Question.objects.all().select_related("quiz")
    serializer_class = QuestionSerializer
    permission_classes = [IsInstructorOrAdmin | ReadOnly]


# PUBLIC_INTERFACE
class ChoiceViewSet(viewsets.ModelViewSet):
    """Manage choices."""
    queryset = Choice.objects.all().select_related("question")
    serializer_class = ChoiceSerializer
    permission_classes = [IsInstructorOrAdmin | ReadOnly]


# PUBLIC_INTERFACE
class QuizAttemptViewSet(viewsets.ModelViewSet):
    """Create and complete quiz attempts. List only own attempts (non-admin)."""
    queryset = QuizAttempt.objects.all().select_related("quiz", "user")
    serializer_class = QuizAttemptSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return super().get_queryset()
        return super().get_queryset().filter(user=user)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        attempt = self.get_object()
        serializer = self.get_serializer(attempt, data={}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        audit(request.user, "quiz_attempt.complete", "quiz_attempt", attempt.id, {"score": attempt.score, "passed": attempt.passed})
        return Response({"score": attempt.score, "passed": attempt.passed})


# PUBLIC_INTERFACE
class CertificateViewSet(viewsets.ReadOnlyModelViewSet):
    """List certificates. Users see own certificates."""
    queryset = Certificate.objects.all().select_related("user", "course")
    serializer_class = CertificateSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return super().get_queryset()
        return super().get_queryset().filter(user=user)


# PUBLIC_INTERFACE
class LearningPathViewSet(viewsets.ModelViewSet):
    """Manage learning paths and items."""
    queryset = LearningPath.objects.all().select_related("created_by")
    serializer_class = LearningPathSerializer
    permission_classes = [IsInstructorOrAdmin | ReadOnly]

    def perform_create(self, serializer):
        obj = serializer.save(created_by=self.request.user)
        audit(self.request.user, "learning_path.create", "learning_path", obj.id)

    @action(detail=True, methods=["post"], permission_classes=[IsInstructorOrAdmin])
    def add_course(self, request, pk=None):
        path = self.get_object()
        course_id = request.data.get("course")
        order = int(request.data.get("order", 0))
        item, created = LearningPathItem.objects.get_or_create(path=path, course_id=course_id, defaults={"order": order})
        if not created:
            item.order = order
            item.save(update_fields=["order"])
        audit(request.user, "learning_path.add_course", "learning_path", path.id, {"course": course_id})
        return Response({"status": "ok"})


# PUBLIC_INTERFACE
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """List notifications for current user and mark as read."""
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by("-created_at")

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.is_read = True
        notif.save(update_fields=["is_read"])
        return Response({"status": "read"})


# PUBLIC_INTERFACE
class ReportingViewSet(viewsets.ViewSet):
    """Aggregated reporting endpoints for managers/admins."""

    @action(detail=False, methods=["get"])
    def course_progress(self, request):
        # Security: only manager or admin
        if request.user.role not in ("manager", "admin"):
            return Response(status=status.HTTP_403_FORBIDDEN)
        qs = Enrollment.objects.values("course_id").annotate(
            enrolled=Count("id"),
            completed=Count("id", filter=Q(status="completed")),
            avg_progress=Avg("progress_percent"),
        )
        data = [
            {
                "course_id": row["course_id"],
                "enrolled": row["enrolled"],
                "completed": row["completed"],
                "avg_progress": float(row["avg_progress"] or 0.0),
            }
            for row in qs
        ]
        ser = ReportCourseProgressSerializer(data=data, many=True)
        ser.is_valid(raise_exception=True)
        return Response(ser.data)


# PUBLIC_INTERFACE
@api_view(["GET"])
@permission_classes([AllowAny])
def sso_login_start(request):
    """SSO start placeholder endpoint. Redirect URL would be returned."""
    return Response({"message": "SSO initiation placeholder", "redirect_to": "/sso/provider"})


# PUBLIC_INTERFACE
@api_view(["GET"])
@permission_classes([AllowAny])
def sso_callback(request):
    """SSO callback placeholder endpoint. Would exchange code for user."""
    return Response({"message": "SSO callback placeholder"})
