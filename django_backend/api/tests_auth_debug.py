import json
from rest_framework.test import APITestCase

# PUBLIC_INTERFACE
class AuthEndpointsDiagnosticsTests(APITestCase):
    """Smoke tests to ensure auth routes resolve and behave as expected."""

    def test_debug_endpoint(self):
        resp = self.client.get("/api/auth/debug/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["resolved_path"], "/api/auth/debug/")
        self.assertTrue(data["has_trailing_slash"])
        self.assertEqual(data["canonical_token_url"], "/api/auth/token/")
        self.assertEqual(data["canonical_register_url"], "/api/auth/register/")

    def test_register_and_login(self):
        payload = {"email": "tester@example.com", "password": "Test123!pass", "username": "tester"}
        r = self.client.post("/api/auth/register/", data=json.dumps(payload), content_type="application/json")
        self.assertIn(r.status_code, [201, 400])  # 400 possible if rerun
        # Ensure id or proper error
        if r.status_code == 201:
            self.assertIn("user", r.json())
        else:
            # normalized error format
            self.assertIn("errors", r.json())

        # Now login via token endpoint using username/password
        login_payload = {"username": "tester", "password": "Test123!pass"}
        t = self.client.post("/api/auth/token/", data=json.dumps(login_payload), content_type="application/json")
        self.assertEqual(t.status_code, 200)  # DRF SimpleJWT returns 200
        self.assertIn("access", t.json())
        self.assertIn("refresh", t.json())

    def test_login_invalid_credentials_returns_json_detail(self):
        # Try with non-existent user
        bad = self.client.post("/api/auth/token/", data=json.dumps({"username": "nouser", "password": "nope"}), content_type="application/json")
        self.assertEqual(bad.status_code, 401)
        data = bad.json()
        self.assertIn("detail", data)
        self.assertTrue("Invalid" in data["detail"] or "No active" in data["detail"])

        # Try via identifier path without trailing slash
        bad2 = self.client.post("/api/auth/token", data=json.dumps({"identifier": "no@no.com", "password": "nope"}), content_type="application/json")
        self.assertEqual(bad2.status_code, 401)
        self.assertIn("detail", bad2.json())

        # Missing fields should return 400 with field-level errors
        missing = self.client.post("/api/auth/token/", data=json.dumps({}), content_type="application/json")
        self.assertEqual(missing.status_code, 400)
        miss_data = missing.json()
        self.assertIn("username", miss_data)
        self.assertIn("identifier", miss_data)
        self.assertIn("password", miss_data)
