from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from django.contrib.auth import get_user_model
from api.models import Enrollment

User = get_user_model()

class HealthTests(APITestCase):
    def test_health(self):
        url = reverse('Health')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"message": "Server is up!"})


class AuthAndCourseSmokeTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin", password="pass", role="admin", email="a@a.com")
        self.instructor = User.objects.create_user(username="inst", password="pass", role="instructor", email="i@i.com")
        self.learner = User.objects.create_user(username="learner", password="pass", role="learner", email="l@l.com")

    def jwt_for(self, username, password="pass"):
        res = self.client.post(reverse("token_obtain_pair"), {"username": username, "password": password}, format="json")
        self.assertEqual(res.status_code, 200)
        return res.data["access"]

    def test_jwt_and_course_crud(self):
        token = self.jwt_for("inst")
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        # create course
        res = client.post("/api/courses/", {"title": "C1", "slug": "c1"}, format="json")
        self.assertEqual(res.status_code, 201)
        cid = res.data["id"]
        # list
        res = client.get("/api/courses/")
        self.assertEqual(res.status_code, 200)
        # publish
        res = client.post(f"/api/courses/{cid}/publish/")
        self.assertEqual(res.status_code, 200)

    def test_lesson_complete_flow(self):
        inst_token = self.jwt_for("inst")
        inst_client = APIClient()
        inst_client.credentials(HTTP_AUTHORIZATION=f"Bearer {inst_token}")
        # Build content
        c = inst_client.post("/api/courses/", {"title": "C2", "slug": "c2"}, format="json").data
        m = inst_client.post("/api/modules/", {"course": c["id"], "title": "M1", "order": 1}, format="json").data
        l1 = inst_client.post("/api/lessons/", {"module": m["id"], "title": "L1", "order": 1}, format="json").data
        l2 = inst_client.post("/api/lessons/", {"module": m["id"], "title": "L2", "order": 2}, format="json").data

        # enroll learner
        admin_token = self.jwt_for("admin")
        admin_client = APIClient()
        admin_client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_token}")
        admin_client.post("/api/enrollments/", {"user": User.objects.get(username="learner").id, "course": c["id"]}, format="json")

        # learner completes lessons
        learner_token = self.jwt_for("learner")
        learner_client = APIClient()
        learner_client.credentials(HTTP_AUTHORIZATION=f"Bearer {learner_token}")
        r1 = learner_client.post(f"/api/lessons/{l1['id']}/complete/")
        self.assertEqual(r1.status_code, 200)
        r2 = learner_client.post(f"/api/lessons/{l2['id']}/complete/")
        self.assertEqual(r2.status_code, 200)
        # check progress is 100
        enr = Enrollment.objects.get(user__username="learner", course_id=c["id"])
        self.assertEqual(float(enr.progress_percent), 100.0)


class RegistrationAndLoginTests(APITestCase):
    def test_register_with_trailing_slash_and_auto_login(self):
        payload = {
            "username": "newuser1",
            "email": "new1@example.com",
            "password": "S3curePass!123",
            "first_name": "New",
            "last_name": "User",
            "auto_login": True
        }
        # Use named URL for trailing slash
        url = reverse("auth_register")
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, 201, res.data if hasattr(res, "data") else res.content)
        self.assertIn("user", res.data)
        self.assertIn("tokens", res.data)
        self.assertIn("access", res.data["tokens"])
        # Verify we can call a protected endpoint with received token
        token = res.data["tokens"]["access"]
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        protected = client.get("/api/courses/")
        self.assertIn(protected.status_code, (200, 403))  # 200 if allowed to list, 403 otherwise but not 401

    def test_register_without_trailing_slash(self):
        # Explicitly hit /api/auth/register without slash
        payload = {
            "username": "newuser2",
            "email": "new2@example.com",
            "password": "S3curePass!123",
            "auto_login": False
        }
        res = self.client.post("/api/auth/register", payload, format="json")
        self.assertEqual(res.status_code, 201, res.data if hasattr(res, "data") else res.content)
        self.assertIn("user", res.data)
        self.assertNotIn("tokens", res.data)

    def test_login_with_identifier_email_and_username(self):
        # create a user
        create = self.client.post(reverse("auth_register"), {
            "username": "loginuser",
            "email": "login@example.com",
            "password": "S3curePass!123",
            "auto_login": False
        }, format="json")
        self.assertEqual(create.status_code, 201, create.data if hasattr(create, "data") else create.content)

        # login via username
        res1 = self.client.post("/api/auth/login/", {
            "username": "loginuser",
            "password": "S3curePass!123"
        }, format="json")
        self.assertEqual(res1.status_code, 200, res1.data if hasattr(res1, "data") else res1.content)
        self.assertIn("access", res1.data)

        # login via identifier (email)
        res2 = self.client.post("/api/auth/login", {
            "identifier": "login@example.com",
            "password": "S3curePass!123"
        }, format="json")
        self.assertEqual(res2.status_code, 200, res2.data if hasattr(res2, "data") else res2.content)
        self.assertIn("refresh", res2.data)
