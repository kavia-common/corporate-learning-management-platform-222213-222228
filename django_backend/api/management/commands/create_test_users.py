from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Create minimal test users if they do not already exist: admin, inst (instructor), learner. Default password: 'pass'."

    def handle(self, *args, **options):
        created = []

        def ensure_user(username: str, email: str, role: str, is_superuser: bool = False, is_staff: bool = False):
            user = User.objects.filter(username=username).first()
            if not user:
                user = User.objects.create_user(username=username, email=email, role=role, password="pass")
                user.is_staff = is_staff or is_superuser
                user.is_superuser = is_superuser
                user.save()
                created.append(username)
            return user

        ensure_user("admin", "a@a.com", role="admin", is_superuser=True, is_staff=True)
        ensure_user("inst", "i@i.com", role="instructor")
        ensure_user("learner", "l@l.com", role="learner")

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created users: {', '.join(created)} (password: 'pass')"))
        else:
            self.stdout.write(self.style.WARNING("No users created (already exist)."))
