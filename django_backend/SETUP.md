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

Notes:
- AUTH_USER_MODEL is set to api.User (custom user model).
- Email defaults to console backend when DJANGO_DEBUG=true.
- Media files stored at DJANGO_MEDIA_ROOT (default ./media).
