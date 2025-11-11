from django.utils import timezone
from django.db import transaction
from rest_framework import serializers

from .models import (
    User, Role, Permission,
    Course, Module, Lesson,
    Enrollment, LessonProgress,
    Quiz, Question, Choice,
    QuizAttempt, Answer, Certificate,
    LearningPath, LearningPathItem, Notification
)

# PUBLIC_INTERFACE
class PermissionSerializer(serializers.ModelSerializer):
    """Serialize Permission."""

    class Meta:
        model = Permission
        fields = ["id", "code", "name", "description"]


# PUBLIC_INTERFACE
class RoleSerializer(serializers.ModelSerializer):
    """Serialize Role with permissions."""

    permissions = PermissionSerializer(many=True, read_only=True)

    class Meta:
        model = Role
        fields = ["id", "name", "description", "permissions"]


# PUBLIC_INTERFACE
class UserSerializer(serializers.ModelSerializer):
    """Serialize basic User profile data."""

    class Meta:
        model = User
        fields = [
            "id", "username", "first_name", "last_name", "email",
            "role", "job_title", "department", "avatar"
        ]
        read_only_fields = ["id", "username", "email", "role"]


# PUBLIC_INTERFACE
class CourseSerializer(serializers.ModelSerializer):
    """Serialize Course with simple fields."""
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Course
        fields = [
            "id", "title", "slug", "description", "created_by",
            "is_published", "tags", "estimated_hours", "thumbnail_url",
            "created_at", "updated_at"
        ]
        read_only_fields = ["created_by", "created_at", "updated_at"]


# PUBLIC_INTERFACE
class ModuleSerializer(serializers.ModelSerializer):
    """Serialize Module."""
    class Meta:
        model = Module
        fields = ["id", "course", "title", "order", "description"]


# PUBLIC_INTERFACE
class LessonSerializer(serializers.ModelSerializer):
    """Serialize Lesson."""
    class Meta:
        model = Lesson
        fields = [
            "id", "module", "title", "content", "video_url",
            "resources_url", "order", "duration_minutes"
        ]


# PUBLIC_INTERFACE
class EnrollmentSerializer(serializers.ModelSerializer):
    """Serialize Enrollment."""
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())

    class Meta:
        model = Enrollment
        fields = [
            "id", "user", "course", "enrolled_at", "status", "progress_percent"
        ]
        read_only_fields = ["enrolled_at"]

    def validate(self, attrs):
        # prevent duplicate enrollments
        if Enrollment.objects.filter(user=attrs["user"], course=attrs["course"]).exists():
            raise serializers.ValidationError("User already enrolled in course.")
        return attrs


# PUBLIC_INTERFACE
class LessonProgressSerializer(serializers.ModelSerializer):
    """Serialize LessonProgress."""
    class Meta:
        model = LessonProgress
        fields = [
            "id", "user", "lesson", "is_completed", "completed_at",
            "time_spent_seconds", "last_viewed_at"
        ]


# PUBLIC_INTERFACE
class ChoiceSerializer(serializers.ModelSerializer):
    """Serialize Choice."""
    class Meta:
        model = Choice
        fields = ["id", "text", "is_correct", "question"]
        extra_kwargs = {"is_correct": {"write_only": True}}


# PUBLIC_INTERFACE
class QuestionSerializer(serializers.ModelSerializer):
    """Serialize Question with nested choices (read)."""
    choices = ChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "quiz", "prompt", "question_type", "order", "choices"]


# PUBLIC_INTERFACE
class QuizSerializer(serializers.ModelSerializer):
    """Serialize Quiz with nested questions (read-only)."""
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = [
            "id", "title", "course", "lesson",
            "time_limit_minutes", "attempts_allowed", "passing_score",
            "questions"
        ]


# PUBLIC_INTERFACE
class AnswerSerializer(serializers.ModelSerializer):
    """Serialize Answer for attempts."""
    selected_choices = serializers.PrimaryKeyRelatedField(
        queryset=Choice.objects.all(), many=True, required=False
    )

    class Meta:
        model = Answer
        fields = ["id", "attempt", "question", "selected_choices", "text_answer"]


# PUBLIC_INTERFACE
class QuizAttemptSerializer(serializers.ModelSerializer):
    """Serialize QuizAttempt with answers write logic."""
    answers = AnswerSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = QuizAttempt
        fields = [
            "id", "user", "quiz", "started_at", "completed_at",
            "score", "passed", "answers"
        ]
        read_only_fields = ["started_at", "score", "passed", "completed_at"]

    @transaction.atomic
    def create(self, validated_data):
        answers_data = validated_data.pop("answers", [])
        attempt = QuizAttempt.objects.create(**validated_data)
        for ans in answers_data:
            selected_choices = ans.pop("selected_choices", [])
            a = Answer.objects.create(attempt=attempt, **ans)
            if selected_choices:
                a.selected_choices.set(selected_choices)
        return attempt

    def update(self, instance, validated_data):
        # Completing an attempt triggers scoring
        if validated_data:
            # only allow setting completed_at to trigger scoring
            pass
        instance.completed_at = timezone.now()
        instance.save(update_fields=["completed_at"])
        self._score_attempt(instance)
        return instance

    def _score_attempt(self, attempt: QuizAttempt):
        total = 0
        correct = 0
        for q in attempt.quiz.questions.all():
            total += 1
            ans = attempt.answers.filter(question=q).first()
            if not ans:
                continue
            if q.question_type in ("single", "multiple"):
                correct_set = set(q.choices.filter(is_correct=True).values_list("id", flat=True))
                given_set = set(ans.selected_choices.values_list("id", flat=True))
                if correct_set == given_set:
                    correct += 1
            else:
                # text type: non-empty treated as correct placeholder
                if ans.text_answer.strip():
                    correct += 1
        score_pct = int((correct / total) * 100) if total else 0
        attempt.score = score_pct
        attempt.passed = score_pct >= attempt.quiz.passing_score
        attempt.save(update_fields=["score", "passed"])


# PUBLIC_INTERFACE
class CertificateSerializer(serializers.ModelSerializer):
    """Serialize Certificate."""
    class Meta:
        model = Certificate
        fields = ["id", "user", "course", "issued_at", "certificate_url"]


# PUBLIC_INTERFACE
class LearningPathItemSerializer(serializers.ModelSerializer):
    """Serialize LearningPathItem."""
    class Meta:
        model = LearningPathItem
        fields = ["id", "path", "course", "order"]


# PUBLIC_INTERFACE
class LearningPathSerializer(serializers.ModelSerializer):
    """Serialize LearningPath with items read-only."""
    items = LearningPathItemSerializer(many=True, read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = LearningPath
        fields = ["id", "title", "description", "created_by", "created_at", "updated_at", "items"]
        read_only_fields = ["created_by", "created_at", "updated_at"]


# PUBLIC_INTERFACE
class NotificationSerializer(serializers.ModelSerializer):
    """Serialize Notification."""
    class Meta:
        model = Notification
        fields = ["id", "user", "title", "message", "is_read", "created_at"]


# PUBLIC_INTERFACE
class ReportCourseProgressSerializer(serializers.Serializer):
    """Aggregate reporting serializer for course progress."""
    course_id = serializers.IntegerField()
    enrolled = serializers.IntegerField()
    completed = serializers.IntegerField()
    avg_progress = serializers.FloatField()
