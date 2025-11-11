from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# PUBLIC_INTERFACE
class User(AbstractUser):
    """Custom user model supporting roles and additional profile fields."""
    USER_ROLE_CHOICES = [
        ("admin", "Administrator"),
        ("manager", "Manager"),
        ("instructor", "Instructor"),
        ("learner", "Learner"),
    ]
    role = models.CharField(max_length=32, choices=USER_ROLE_CHOICES, default="learner", db_index=True)
    job_title = models.CharField(max_length=120, blank=True)
    department = models.CharField(max_length=120, blank=True)
    manager = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="direct_reports")
    avatar = models.URLField(blank=True)
    # auditing
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["username"]),
            models.Index(fields=["email"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self) -> str:
        return f"{self.username} ({self.role})"


class Permission(models.Model):
    """Fine-grained permissions to complement role-based access."""
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.code


class Role(models.Model):
    """Role groups multiple permissions."""
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, blank=True, related_name="roles")
    users = models.ManyToManyField(User, blank=True, related_name="custom_roles")

    def __str__(self):
        return self.name


class Course(models.Model):
    """A course containing modules and lessons."""
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="courses_created")
    is_published = models.BooleanField(default=False, db_index=True)
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated tags")
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    thumbnail_url = models.URLField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_published"]),
        ]

    def __str__(self):
        return self.title


class Module(models.Model):
    """A module belonging to a course."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0, db_index=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["order"]
        unique_together = ("course", "order")


class Lesson(models.Model):
    """An individual lesson within a module."""
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    video_url = models.URLField(blank=True)
    resources_url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0, db_index=True)
    duration_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        unique_together = ("module", "order")


class Enrollment(models.Model):
    """Learner enrollment in a course."""
    STATUS_CHOICES = [
        ("active", "Active"),
        ("completed", "Completed"),
        ("dropped", "Dropped"),
        ("expired", "Expired"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    enrolled_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="active", db_index=True)
    progress_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        unique_together = ("user", "course")
        indexes = [
            models.Index(fields=["status"]),
        ]


class LessonProgress(models.Model):
    """Track progress for a user on each lesson."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lesson_progress")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress")
    is_completed = models.BooleanField(default=False, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent_seconds = models.PositiveIntegerField(default=0)
    last_viewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "lesson")


class Quiz(models.Model):
    """Quiz associated with a lesson or a course."""
    title = models.CharField(max_length=255)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="quizzes", null=True, blank=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="quizzes", null=True, blank=True)
    time_limit_minutes = models.PositiveIntegerField(default=0)
    attempts_allowed = models.PositiveIntegerField(default=1)
    passing_score = models.PositiveIntegerField(default=70)

    def __str__(self):
        return self.title


class Question(models.Model):
    """Quiz questions."""
    QUESTION_TYPE_CHOICES = [
        ("single", "Single Choice"),
        ("multiple", "Multiple Choice"),
        ("text", "Text"),
    ]
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    prompt = models.TextField()
    question_type = models.CharField(max_length=16, choices=QUESTION_TYPE_CHOICES, default="single")
    order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ["order"]


class Choice(models.Model):
    """Choice options for questions."""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=512)
    is_correct = models.BooleanField(default=False)


class QuizAttempt(models.Model):
    """User attempt for a quiz."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quiz_attempts")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveIntegerField(default=0)
    passed = models.BooleanField(default=False, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["passed"]),
        ]


class Answer(models.Model):
    """Answers given within a quiz attempt."""
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    selected_choices = models.ManyToManyField(Choice, blank=True)
    text_answer = models.TextField(blank=True)


class Certificate(models.Model):
    """Certificate awarded after course completion."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="certificates")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="certificates")
    issued_at = models.DateTimeField(default=timezone.now)
    certificate_url = models.URLField(blank=True)

    class Meta:
        unique_together = ("user", "course")


class LearningPath(models.Model):
    """A roadmap grouping multiple courses."""
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="learning_paths_created")
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)


class LearningPathItem(models.Model):
    """An item within a learning path referencing a course with order."""
    path = models.ForeignKey(LearningPath, on_delete=models.CASCADE, related_name="items")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="in_paths")
    order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        unique_together = ("path", "course")
        ordering = ["order"]


class Notification(models.Model):
    """Notification to a user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [models.Index(fields=["is_read", "created_at"])]


class AuditLog(models.Model):
    """Record audit events for compliance."""
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="audit_actions")
    action = models.CharField(max_length=128, db_index=True)
    entity_type = models.CharField(max_length=64, db_index=True)
    entity_id = models.CharField(max_length=64, db_index=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["action"]),
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["timestamp"]),
        ]
