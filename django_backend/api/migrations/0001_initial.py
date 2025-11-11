from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False, help_text="Designates that this user has all permissions without explicitly assigning them.", verbose_name="superuser status")),
                ("username", models.CharField(error_messages={"unique": "A user with that username already exists."}, help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.", max_length=150, unique=True, verbose_name="username")),
                ("first_name", models.CharField(blank=True, max_length=150, verbose_name="first name")),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="last name")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="email address")),
                ("is_staff", models.BooleanField(default=False, help_text="Designates whether the user can log into this admin site.", verbose_name="staff status")),
                ("is_active", models.BooleanField(default=True, help_text="Designates whether this user should be treated as active.", verbose_name="active")),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now, verbose_name="date joined")),
                ("role", models.CharField(choices=[("admin", "Administrator"), ("manager", "Manager"), ("instructor", "Instructor"), ("learner", "Learner")], db_index=True, default="learner", max_length=32)),
                ("job_title", models.CharField(blank=True, max_length=120)),
                ("department", models.CharField(blank=True, max_length=120)),
                ("avatar", models.URLField(blank=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"abstract": False,},
        ),
        migrations.CreateModel(
            name="Permission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=64, unique=True)),
                ("name", models.CharField(max_length=128)),
                ("description", models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="Role",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=64, unique=True)),
                ("description", models.TextField(blank=True)),
                ("permissions", models.ManyToManyField(blank=True, related_name="roles", to="api.permission")),
            ],
        ),
        migrations.CreateModel(
            name="Course",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("slug", models.SlugField(max_length=255, unique=True)),
                ("description", models.TextField(blank=True)),
                ("is_published", models.BooleanField(db_index=True, default=False)),
                ("tags", models.CharField(blank=True, help_text="Comma-separated tags", max_length=255)),
                ("estimated_hours", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ("thumbnail_url", models.URLField(blank=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="courses_created", to="api.user")),
            ],
        ),
        migrations.CreateModel(
            name="Module",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("order", models.PositiveIntegerField(db_index=True, default=0)),
                ("description", models.TextField(blank=True)),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="modules", to="api.course")),
            ],
            options={"ordering": ["order"], "unique_together": {("course", "order")},},
        ),
        migrations.CreateModel(
            name="Lesson",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("content", models.TextField(blank=True)),
                ("video_url", models.URLField(blank=True)),
                ("resources_url", models.URLField(blank=True)),
                ("order", models.PositiveIntegerField(db_index=True, default=0)),
                ("duration_minutes", models.PositiveIntegerField(default=0)),
                ("module", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lessons", to="api.module")),
            ],
            options={"ordering": ["order"], "unique_together": {("module", "order")},},
        ),
        migrations.CreateModel(
            name="Enrollment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("enrolled_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("status", models.CharField(choices=[("active", "Active"), ("completed", "Completed"), ("dropped", "Dropped"), ("expired", "Expired")], db_index=True, default="active", max_length=16)),
                ("progress_percent", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="enrollments", to="api.course")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="enrollments", to="api.user")),
            ],
            options={"unique_together": {("user", "course")},},
        ),
        migrations.CreateModel(
            name="LessonProgress",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_completed", models.BooleanField(db_index=True, default=False)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("time_spent_seconds", models.PositiveIntegerField(default=0)),
                ("last_viewed_at", models.DateTimeField(blank=True, null=True)),
                ("lesson", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="progress", to="api.lesson")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lesson_progress", to="api.user")),
            ],
            options={"unique_together": {("user", "lesson")},},
        ),
        migrations.CreateModel(
            name="Quiz",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("time_limit_minutes", models.PositiveIntegerField(default=0)),
                ("attempts_allowed", models.PositiveIntegerField(default=1)),
                ("passing_score", models.PositiveIntegerField(default=70)),
                ("course", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="quizzes", to="api.course")),
                ("lesson", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="quizzes", to="api.lesson")),
            ],
        ),
        migrations.CreateModel(
            name="Question",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("prompt", models.TextField()),
                ("question_type", models.CharField(choices=[("single", "Single Choice"), ("multiple", "Multiple Choice"), ("text", "Text")], default="single", max_length=16)),
                ("order", models.PositiveIntegerField(db_index=True, default=0)),
                ("quiz", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="questions", to="api.quiz")),
            ],
            options={"ordering": ["order"],},
        ),
        migrations.CreateModel(
            name="Choice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.CharField(max_length=512)),
                ("is_correct", models.BooleanField(default=False)),
                ("question", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="choices", to="api.question")),
            ],
        ),
        migrations.CreateModel(
            name="QuizAttempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("started_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("score", models.PositiveIntegerField(default=0)),
                ("passed", models.BooleanField(db_index=True, default=False)),
                ("quiz", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attempts", to="api.quiz")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="quiz_attempts", to="api.user")),
            ],
        ),
        migrations.CreateModel(
            name="Answer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text_answer", models.TextField(blank=True)),
                ("attempt", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="answers", to="api.quizattempt")),
                ("question", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="answers", to="api.question")),
            ],
        ),
        migrations.CreateModel(
            name="Certificate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("issued_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("certificate_url", models.URLField(blank=True)),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="certificates", to="api.course")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="certificates", to="api.user")),
            ],
            options={"unique_together": {("user", "course")},},
        ),
        migrations.CreateModel(
            name="LearningPath",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="learning_paths_created", to="api.user")),
            ],
        ),
        migrations.CreateModel(
            name="LearningPathItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order", models.PositiveIntegerField(db_index=True, default=0)),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="in_paths", to="api.course")),
                ("path", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="api.learningpath")),
            ],
            options={"ordering": ["order"], "unique_together": {("path", "course")},},
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("message", models.TextField()),
                ("is_read", models.BooleanField(db_index=True, default=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="api.user")),
            ],
        ),
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(db_index=True, max_length=128)),
                ("entity_type", models.CharField(db_index=True, max_length=64)),
                ("entity_id", models.CharField(db_index=True, max_length=64)),
                ("timestamp", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("actor", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="audit_actions", to="api.user")),
            ],
        ),
        migrations.AddField(
            model_name="role",
            name="users",
            field=models.ManyToManyField(blank=True, related_name="custom_roles", to="api.user"),
        ),
        migrations.AddIndex(model_name="user", index=models.Index(fields=["username"], name="api_user_username_d0dea1_idx")),
        migrations.AddIndex(model_name="user", index=models.Index(fields=["email"], name="api_user_email_2f2a1b_idx")),
        migrations.AddIndex(model_name="user", index=models.Index(fields=["role"], name="api_user_role_c2a5b1_idx")),
        migrations.AddIndex(model_name="course", index=models.Index(fields=["slug"], name="api_course_slug_idx")),
        migrations.AddIndex(model_name="course", index=models.Index(fields=["is_published"], name="api_course_published_idx")),
        migrations.AddIndex(model_name="quizattempt", index=models.Index(fields=["passed"], name="api_attempt_passed_idx")),
        migrations.AddIndex(model_name="notification", index=models.Index(fields=["is_read", "created_at"], name="api_notif_read_created_idx")),
        migrations.AddIndex(model_name="auditlog", index=models.Index(fields=["action"], name="api_audit_action_idx")),
        migrations.AddIndex(model_name="auditlog", index=models.Index(fields=["entity_type", "entity_id"], name="api_audit_entity_idx")),
        migrations.AddIndex(model_name="auditlog", index=models.Index(fields=["timestamp"], name="api_audit_ts_idx")),
        migrations.AlterModelOptions(
            name="module",
            options={"ordering": ["order"]},
        ),
        migrations.AlterModelOptions(
            name="lesson",
            options={"ordering": ["order"]},
        ),
        migrations.AlterModelOptions(
            name="question",
            options={"ordering": ["order"]},
        ),
        migrations.AlterModelOptions(
            name="learningpathitem",
            options={"ordering": ["order"]},
        ),
        migrations.CreateModel(
            name="Answer_selected_choices",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("answer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="api.answer")),
                ("choice", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="api.choice")),
            ],
            options={"db_table": "api_answer_selected_choices",},
        ),
    ]
