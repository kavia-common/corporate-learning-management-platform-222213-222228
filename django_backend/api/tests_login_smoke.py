import json
from rest_framework.test import APITestCase


# PUBLIC_INTERFACE
class LoginSmokeTests(APITestCase):
    """Backend smoke tests for login success and failure across URL variants."""

    def setUp(self):
        # Create a test user once
        self.username = "smokeuser"
        self.email = "smokeuser@example.com"
        self.password = "S3curePass!123"
        # Hit register endpoint; if exists, ignore duplicate errors on reruns
        r = self.client.post(
            "/api/auth/register/",
            data=json.dumps({"username": self.username, "email": self.email, "password": self.password, "auto_login": False}),
            content_type="application/json",
        )
        if r.status_code not in (201, 400):
            raise AssertionError(f"Registration failed unexpectedly: {getattr(r, 'data', r.content)}")

    def _expect_login_ok(self, url, payload):
        res = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        assert res.status_code == 200, f"Expected 200 at {url}, got {res.status_code} body={getattr(res, 'data', res.content)}"
        body = res.json()
        assert "access" in body and "refresh" in body, f"Missing tokens at {url}"
        return body

    def _expect_login_fail(self, url, payload):
        res = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        assert res.status_code == 401, f"Expected 401 at {url}, got {res.status_code} body={getattr(res, 'data', res.content)}"
        body = res.json()
        assert "detail" in body, f"Expected JSON detail in error at {url}"
        return body

    def test_login_success_username_with_trailing_slash(self):
        self._expect_login_ok("/api/auth/token/", {"username": self.username, "password": self.password})

    def test_login_success_identifier_email_with_trailing_slash(self):
        self._expect_login_ok("/api/auth/token/", {"identifier": self.email, "password": self.password})

    def test_login_success_identifier_email_without_trailing_slash(self):
        self._expect_login_ok("/api/auth/token", {"identifier": self.email, "password": self.password})

    def test_login_success_root_alias_with_and_without_slash(self):
        self._expect_login_ok("/auth/token/", {"username": self.username, "password": self.password})
        self._expect_login_ok("/auth/token", {"identifier": self.email, "password": self.password})

    def test_login_failure_wrong_password(self):
        self._expect_login_fail("/api/auth/token/", {"username": self.username, "password": "wrong"})
        self._expect_login_fail("/auth/token", {"identifier": self.email, "password": "wrong"})

    def test_login_missing_fields_return_field_errors(self):
        res = self.client.post("/api/auth/token/", data=json.dumps({}), content_type="application/json")
        self.assertEqual(res.status_code, 400)
        data = res.json()
        # Expect field-level messages for username/identifier and password
        self.assertIn("username", data)
        self.assertIn("identifier", data)
        self.assertIn("password", data)
