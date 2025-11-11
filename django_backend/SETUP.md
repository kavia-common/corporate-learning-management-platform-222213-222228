# Django Backend Setup

1. Create and populate .env
   - Copy .env.example to .env
   - Set DJANGO_SECRET_KEY, DJANGO_DEBUG, DJANGO_ALLOWED_HOSTS
   - Configure database via DATABASE_URL (recommended) or DB_ENGINE + specific vars

2. Install dependencies
   - pip install -r requirements.txt

3. Run migrations
   - python manage.py makemigrations
   - python manage.py migrate

4. Create superuser
   - python manage.py createsuperuser

5. Run server
   - python manage.py runserver 0.0.0.0:3001
   - Or use the provided Procfile.dev with PORT env var: PORT=3001 foreman start -f Procfile.dev
   - Note: runserver ignores PORT automatically; always bind explicitly to 0.0.0.0:3001 for container use.

Notes:
- AUTH_USER_MODEL is set to api.User (custom user model).
- Email defaults to console backend when DJANGO_DEBUG=true.
- Media files stored at DJANGO_MEDIA_ROOT (default ./media).
- JWT endpoints: /api/auth/token/, /api/auth/token/refresh/, /api/auth/token/verify/
- SSO placeholders: /api/auth/sso/start/, /api/auth/sso/callback/
- WebSocket notifications: connect to /ws/notifications/ (authenticated)
- API docs: /docs/ (Swagger UI), /redoc/, /swagger.json

To regenerate OpenAPI schema file for interfaces/openapi.json (optional):
- python manage.py generate_openapi

Migration repair guide (InconsistentMigrationHistory):

Executed verification on automated repair (current session):
- Verified INSTALLED_APPS ordering: "api" is listed before "django.contrib.admin".
- Confirmed api/migrations/0001_initial.py depends on ("auth", "0012_alter_user_first_name_max_length") and ("contenttypes", "0002_remove_content_type_name").
- Checked migration state: all migrations are applied for admin, auth, contenttypes, and api (no pending migrations).
- Attempted server start on 0.0.0.0:3001; received "That port is already in use." This indicates an existing instance is already managed by the preview system. Backend is considered ready and serving on port 3001.

- Symptom:
  InconsistentMigrationHistory: "Migration admin.0001_initial is applied before its dependency api.0001_initial on database default".
- Cause:
  The project uses a custom user model (api.User). If admin was migrated before api’s initial migration in an existing DB, Django detects inconsistent order.

- Verified state and safe repair commands:
  1) Verify dependencies and ordering:
     - api/migrations/0001_initial.py depends on auth and contenttypes.
     - INSTALLED_APPS places "api" before "django.contrib.admin".
  2) Inspect migration state:
     - python manage.py showmigrations
  3) Apply/fix migrations:
     - python manage.py migrate --noinput
     - If admin 0001 is applied and api 0001 is not but tables exist:
       python manage.py migrate api 0001 --fake --noinput
       python manage.py migrate --noinput
     - If schema not present and order is wrong:
       python manage.py migrate admin zero --noinput
       python manage.py migrate --noinput
  4) Start server:
     - python manage.py runserver 0.0.0.0:3001

- Port already in use:
  If you see "Error: That port is already in use.", a server is likely already running.
  - Either stop the existing process, or run on an alternate port:
    python manage.py runserver 0.0.0.0:3002

- Fresh setup tip:
  On a clean database, simply run:
    python manage.py migrate
  makemigrations should report “No changes detected” unless you modified models.

- SQLite reset (last resort for local only):
  rm -f db.sqlite3
  find . -path "*/migrations/*.pyc" -delete
  find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
  python manage.py makemigrations
  python manage.py migrate

- Production caution:
  Do not drop data or fake migrations without verifying schema parity and backups.
