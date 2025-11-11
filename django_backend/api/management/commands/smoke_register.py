from django.core.management.base import BaseCommand
from django.test import Client
from django.utils.crypto import get_random_string


# PUBLIC_INTERFACE
class Command(BaseCommand):
    """Smoke test for registration endpoints to verify routing and method handling.

    This command will POST to both /api/auth/register and /api/auth/register/
    and expects a 201 Created response with a user object in the payload.
    """

    help = "Smoke test the registration endpoint routing."

    def handle(self, *args, **options):
        client = Client(enforce_csrf_checks=False)

        username = f"smoke_{get_random_string(8)}"
        email = f"{username}@example.com"
        payload = {
            "username": username,
            "email": email,
            "password": "S@fePassw0rd!23",
            "auto_login": False,
        }

        endpoints = ["/api/auth/register", "/api/auth/register/"]
        failures = []
        for ep in endpoints:
            res = client.post(ep, data=payload, content_type="application/json")
            if res.status_code != 201 or "user" not in (res.json() if res.content else {}):
                failures.append((ep, res.status_code, res.content.decode() if res.content else ""))

        if failures:
            for ep, code, body in failures:
                self.stderr.write(self.style.ERROR(f"FAIL {ep}: status={code} body={body[:300]}"))
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS("Registration endpoints OK (both variants returned 201)."))
