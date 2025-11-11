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
