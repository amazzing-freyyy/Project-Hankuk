from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from api.models import Project, UserProfile
from rest_framework_simplejwt.tokens import RefreshToken
from api.models import DynamicTable

class APITestSetup(APITestCase):
    def setUp(self):
        self.project = Project.objects.create(name="TeamAlpha")
        self.admin = User.objects.create_user(username="admin", password="pass1234")
        UserProfile.objects.create(user=self.admin, project=self.project, role="admin")
        self.refresh = RefreshToken.for_user(self.admin)
        self.access_token = str(self.refresh.access_token)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

class UserSignupTests(APITestCase):
    def test_user_signup(self):
        payload = {
            "username": "testuser",
            "password": "securepass",
            "project": "TeamAlpha",
            "role": "athlete"
        }
        response = self.client.post("/api/signup/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

class TokenTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tokenuser", password="12345678")
        UserProfile.objects.create(user=self.user, project=Project.objects.create(name="TeamX"), role="athlete")

    def test_token_obtain(self):
        response = self.client.post("/api/token/", {"username": "tokenuser", "password": "12345678"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_token_refresh(self):
        refresh = RefreshToken.for_user(self.user)
        response = self.client.post("/api/token/refresh/", {"refresh": str(refresh)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

class TableDataTests(APITestSetup):
    def setUp(self):
        self.project = Project.objects.create(name="TeamAlpha")

        # Coach user
        self.coach_user = User.objects.create_user(username='coachuser', password='password')
        UserProfile.objects.create(user=self.coach_user, project=self.project, role="coach")

        # Athlete user
        self.athlete_user = User.objects.create_user(username='athleteuser', password='password')
        UserProfile.objects.create(user=self.athlete_user, project=self.project, role="athlete")

        self.client.force_authenticate(user=self.coach_user)  # Login as coach
        self.response = self.client.post('/api/tables/', {
            "Title": "test_metrics",
            "project":"TeamAlpha",
            "data":{
                "score": {"label": "score", "type": "float"},
                "rating": {"label": "rating", "type": "int"}
            }
        }, format='json')
        self.client.force_authenticate(user=None)

    def test_create_table(self):
        self.assertEqual(self.response.status_code, status.HTTP_200_OK)

    def test_submit_data(self):
        self.client.force_authenticate(user=self.athlete_user)
        # Submit data to the table (assume it exists)
        response = self.client.post('/api/data/', {
            "Title": "test_metrics",
            "data": {
                "score": {"value":85.5},
                "rating": {"value":4}
            }
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.force_authenticate(user=None)

    def test_get_data(self):
        self.client.force_authenticate(user=self.athlete_user)
        # Submit data to the table (assume it exists)
        response = self.client.post('/api/data/', {
            "Title": "test_metrics",
            "data": {
                "score": {"value":85.5},
                "rating": {"value":4}
            }
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.force_authenticate(user=None)

        self.client.force_authenticate(user=self.coach_user)
        # Assuming table "test_metrics" exists and is linked to the project
        response = self.client.get('/api/tables/test_metrics/data/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Optionally check response content
        self.assertIn('data', response.data)
        self.client.force_authenticate(user=None)

    def test_process_data(self):
        self.client.force_authenticate(user=self.athlete_user)
        # Submit data to the table (assume it exists)
        response = self.client.post('/api/data/', {
            "Title": "test_metrics",
            "data": {
                "score": {"value":85.5},
                "rating": {"value":4}
            }
        }, format='json')
        self.client.force_authenticate(user=None)

        self.client.force_authenticate(user=self.coach_user)
        # Example payload for processing data, adjust keys as per your API
        payload = {
            "Title": "test_metrics",
            "data": {
                "squared_score": {
                    "Label": "Score square",
                    "Expression": "score * score",
                    "Type": "float"
                }
            }
        }
        
        response = self.client.post('/api/tables/process/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Optionally check the processed result returned by the API
        self.assertIn('results', response.data)
        self.client.force_authenticate(user=None)

class FormAPITestCase(APITestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Project A")
        self.user_model = get_user_model()
        self.coach = self.user_model.objects.create_user(username="coach", password="pass")
        self.athlete = self.user_model.objects.create_user(username="athlete", password="pass")

        self.coach_profile = UserProfile.objects.create(user=self.coach, role="coach", project=self.project)
        self.athlete_profile = UserProfile.objects.create(user=self.athlete, role="athlete", project=self.project)

        self.table = DynamicTable.objects.create(
            title="Test Table", 
            project=self.project, 
            schema={
                "q1":{"Label":"name", "type": "str"}
            }
        )

        self.form_data = {
            "name": "Test Form",
            "description": "Test Desc",
            "project": self.project.id,
            "table": self.table.id,
            "questions": {
                "q1": {
                    "text": "What is your name?",
                    "type": "str",
                    "input": "text"
                }
            }
        }

    def test_coach_can_create_form(self):
        self.client.force_authenticate(user=self.coach)
        response = self.client.post("/api/forms/", self.form_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_athlete_cannot_create_form(self):
        self.client.force_authenticate(user=self.athlete)
        response = self.client.post("/api/forms/", self.form_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_athlete_can_view_form(self):
        self.client.force_authenticate(user=self.coach)
        create_response = self.client.post("/api/forms/", self.form_data, format='json')
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(user=self.athlete)
        list_response = self.client.get("/api/forms/")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(list_response.data) > 0)

    def test_coach_can_update_form(self):
        self.client.force_authenticate(user=self.coach)
        create_response = self.client.post("/api/forms/", self.form_data, format='json')
        form_id = create_response.data['id']

        update_data = {"name": "Updated Form"}
        update_response = self.client.patch(f"/api/forms/{form_id}/", update_data, format='json')
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data['name'], "Updated Form")

    def test_athlete_cannot_update_form(self):
        self.client.force_authenticate(user=self.coach)
        create_response = self.client.post("/api/forms/", self.form_data, format='json')
        form_id = create_response.data['id']

        self.client.force_authenticate(user=self.athlete)
        update_response = self.client.patch(f"/api/forms/{form_id}/", {"name": "Hack"}, format='json')
        self.assertEqual(update_response.status_code, status.HTTP_403_FORBIDDEN)