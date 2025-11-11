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
- Symptom:
  InconsistentMigrationHistory: "Migration admin.0001_initial is applied before its dependency api.0001_initial on database default".
- Cause:
  The project uses a custom user model (api.User). If admin was migrated before api’s initial migration in an existing DB, Django detects inconsistent order.
- Fix options:
  Option A (recommended for local/dev): fake-apply api initial migration to align history.
    python manage.py migrate contenttypes
    python manage.py migrate auth
    python manage.py migrate api 0001 --fake
    python manage.py migrate
  Option B (if you prefer strict ordering or fake is not appropriate):
    python manage.py migrate admin zero
    python manage.py migrate
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
