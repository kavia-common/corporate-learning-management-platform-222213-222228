# Migration Repair Procedure (Automated)

Use these commands if you hit InconsistentMigrationHistory or migration order issues with custom user model:

1) Ensure api is before admin in INSTALLED_APPS (already configured).

2) Safe repair steps:
- python manage.py migrate contenttypes --noinput
- python manage.py migrate auth --noinput
- If admin was applied before api on this DB:
  - python manage.py migrate api 0001 --fake --noinput
  - python manage.py migrate --noinput
- If fake is not appropriate or schema drifted:
  - python manage.py migrate admin zero --noinput
  - python manage.py migrate --noinput

3) If models changed:
- python manage.py makemigrations --noinput
- python manage.py migrate --noinput

4) Start server:
- python manage.py runserver 0.0.0.0:3001

Notes:
- Always verify backups for production. This project uses sqlite by default for dev.
