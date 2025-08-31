from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group
from rest_framework import status
from .models import *
from rest_framework.test import APIClient

class UserCRUDTest(APITestCase):
    def setUp(self):
        self.user_list_url = reverse("user-list")
        self.user = User.objects.create_user(username="ctest", password="test", is_staff=True)
        self.profile = Profile.objects.create(user=self.user, gender="m")
        self.group = Group.objects.create(name="coaches")
        self.user.groups.add(self.group)
        self.user.save()
        print("Setup user:", self.user)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_user_with_profile(self):
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "strongpassword123",
            "profile": {
                "gender": "m"
            }
        }
        response = self.client.post(self.user_list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # DB checks
        user = User.objects.get(username="testuser")
        self.assertTrue(user.profile)  # Profile auto-created
        self.assertEqual(user.email, "test@example.com")

    def test_read_user_and_profile(self):
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "strongpassword123",
            "profile": {
                "gender": "m"
            }
        }
        response = self.client.post(self.user_list_url, data, format="json")

        user = User.objects.get(username="testuser")
        detail_url = reverse("user-detail", args=[user.username])
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "testuser")
        self.assertEqual(response.data["profile"]["gender"], "m")

    def test_update_user_and_profile(self):
        data = {
            "username": "testuser",
            "email": "old@example.com",
            "password": "strongpassword123",
            "groups": ["coaches"],
            "profile": {
                "gender": "m"
            }
        }
        response = self.client.post(self.user_list_url, data, format="json")

        user = User.objects.get(username="testuser")

        detail_url = reverse("user-detail", args=[user.username])

        # update user only
        response = self.client.patch(detail_url, {"email": "new@example.com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.email, "new@example.com")

        # update profile directly via profile API
        response = self.client.patch(detail_url, {"profile" : {"gender": "f"}}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.profile.gender, "f")

    def test_delete_user_and_profile(self):
        data = {
            "username": "testuser",
            "email": "old@example.com",
            "password": "strongpassword123",
            "groups": ["coaches"],
            "profile": {
                "gender": "m"
            }
        }
        response = self.client.post(self.user_list_url, data, format="json")

        user = User.objects.get(username="testuser")

        detail_url = reverse("user-detail", args=[user.username])
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(User.objects.filter(username="testuser").exists())
        self.assertFalse(Profile.objects.filter(user=user.id).exists())

class WUDathleteCRUDTest(APITestCase):
    def setUp(self):
        self.user_list_url = reverse("user-list")
        self.wud_list_url = reverse("wake_up_data-list")
        self.user = User.objects.create_user(username="atest", password="test")
        self.profile = Profile.objects.create(user=self.user, gender="m")
        self.group = Group.objects.create(name="athletes")
        self.user.groups.add(self.group)
        self.user.save()
        print("Setup user:", self.user)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_WUD(self):
        data = {
            "date": "2023-10-01",
            "username": self.user.username
        }
        response = self.client.post(self.wud_list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_read_WUD(self):
        data = {
            "date": "2023-10-01",
            "username": self.user.username
        }
        response = self.client.post(self.wud_list_url, data, format="json")
        wake_up_data = response.data
        detail_url = reverse("wake_up_data-detail", args=[wake_up_data["slug"]])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_WUD(self):
        data = {
            "date": "2023-10-01",
            "username": self.user.username
        }

        response = self.client.post(self.wud_list_url, data, format="json")
        wake_up_data = response.data
        detail_url = reverse("wake_up_data-detail", args=[wake_up_data["slug"]])
        response = self.client.patch(detail_url, {"HR": 60}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["HR"], 60)

    def test_delete_WUD(self):
        data = {
            "date": "2023-10-01",
            "username": self.user.username
        }

        response = self.client.post(self.wud_list_url, data, format="json")
        wake_up_data = response.data
        detail_url = reverse("wake_up_data-detail", args=[wake_up_data["slug"]])

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Wake_Up_Data.objects.filter(slug=wake_up_data["slug"]).exists())

class WUDcoachCRUDTest(APITestCase):
    def setUp(self):
        self.user_list_url = reverse("user-list")
        self.wud_list_url = reverse("wake_up_data-list")
        
        self.athlete = User.objects.create_user(username="atest", password="test")
        Profile.objects.create(user=self.athlete, gender="m")
        group = Group.objects.create(name="athletes")
        self.athlete.groups.add(group)
        self.athlete.save()

        self.coach = User.objects.create_user(username="ctest", password="test")
        Profile.objects.create(user=self.coach, gender="m")
        group = Group.objects.create(name="coaches")
        self.coach.groups.add(group)
        self.coach.save()

        print("Setup user:", self.coach)
        self.client = APIClient()
        self.client.force_authenticate(user=self.coach)

    def test_create_WUD(self):
        data = {
            "date": "2023-10-01",
            "username": self.athlete.username
        }
        response = self.client.post(self.wud_list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_read_WUD(self):
        data = {
            "date": "2023-10-01",
            "username": self.athlete.username
        }
        response = self.client.post(self.wud_list_url, data, format="json")
        wake_up_data = response.data
        detail_url = reverse("wake_up_data-detail", args=[wake_up_data["slug"]])
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_WUD(self):
        data = {
            "date": "2023-10-01",
            "username": self.athlete.username
        }

        response = self.client.post(self.wud_list_url, data, format="json")
        wake_up_data = response.data
        detail_url = reverse("wake_up_data-detail", args=[wake_up_data["slug"]])
        response = self.client.patch(detail_url, {"HR": 60}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["HR"], 60)

    def test_delete_WUD(self):
        data = {
            "date": "2023-10-01",
            "username": self.athlete.username
        }

        response = self.client.post(self.wud_list_url, data, format="json")
        wake_up_data = response.data
        detail_url = reverse("wake_up_data-detail", args=[wake_up_data["slug"]])

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Wake_Up_Data.objects.filter(slug=wake_up_data["slug"]).exists())

class PTDathleteCRUDTest(APITestCase):
    def setUp(self):
        self.user_list_url = reverse("user-list")
        self.ptd_list_url = reverse("post_training-list")
        self.user = User.objects.create_user(username="atest", password="test")
        self.profile = Profile.objects.create(user=self.user, gender="m")
        self.group = Group.objects.create(name="athletes")
        self.user.groups.add(self.group)
        self.user.save()
        print("Setup user:", self.user.id)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_PTD(self):
        data = {
            "date": "2023-10-01T14:14:14",
            "username": self.user.username
        }
        response = self.client.post(self.ptd_list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_read_PTD(self):
        data = {
            "date": "2023-10-01T14:14:14",
            "username": self.user.username
        }
        response = self.client.post(self.ptd_list_url, data, format="json")
        post_training_data = response.data

        detail_url = reverse("post_training-detail", args=[post_training_data["slug"]])
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_PTD(self):
        data = {
            "date": "2023-10-01T14:14:14",
            "username": self.user.username
        }

        response = self.client.post(self.ptd_list_url, data, format="json")
        post_training_data = response.data

        detail_url = reverse("post_training-detail", args=[post_training_data["slug"]])
        response = self.client.patch(detail_url, {"perceived_strain_of_activity": 0}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["perceived_strain_of_activity"], "0.00")

    def test_delete_PTD(self):
        data = {
            "date": "2023-10-01T14:14:14",
            "username": self.user.username
        }

        response = self.client.post(self.ptd_list_url, data, format="json")
        post_training_data = response.data
        detail_url = reverse("post_training-detail", args=[post_training_data["slug"]])

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Wake_Up_Data.objects.filter(slug=post_training_data["slug"]).exists())

class PTDcoachCRUDTest(APITestCase):
    def setUp(self):
        self.user_list_url = reverse("user-list")
        self.ptd_list_url = reverse("post_training-list")
        
        self.athlete = User.objects.create_user(username="atest", password="test")
        Profile.objects.create(user=self.athlete, gender="m")
        group = Group.objects.create(name="athletes")
        self.athlete.groups.add(group)
        self.athlete.save()

        self.coach = User.objects.create_user(username="ctest", password="test")
        Profile.objects.create(user=self.coach, gender="m")
        group = Group.objects.create(name="coaches")
        self.coach.groups.add(group)
        self.coach.save()

        print("Setup user:", self.coach)
        self.client = APIClient()
        self.client.force_authenticate(user=self.coach)

    def test_create_PTD(self):
        data = {
            "date": "2023-10-01T14:14:14",
            "username": self.athlete.username
        }
        response = self.client.post(self.ptd_list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_read_PTD(self):
        data = {
            "date": "2023-10-01T14:14:14",
            "username": self.athlete.username
        }
        response = self.client.post(self.ptd_list_url, data, format="json")
        post_training_data = response.data
        detail_url = reverse("post_training-detail", args=[post_training_data["slug"]])
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_PTD(self):
        data = {
            "date": "2023-10-01T14:14:14",
            "username": self.athlete.username
        }

        response = self.client.post(self.ptd_list_url, data, format="json")
        post_training_data = response.data
        detail_url = reverse("post_training-detail", args=[post_training_data["slug"]])
        response = self.client.patch(detail_url, {"perceived_strain_of_activity": 0}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["perceived_strain_of_activity"], "0.00")

    def test_delete_PTD(self):
        data = {
            "date": "2023-10-01T14:14:14",
            "username": self.athlete.username
        }

        response = self.client.post(self.ptd_list_url, data, format="json")
        post_training_data = response.data
        detail_url = reverse("post_training-detail", args=[post_training_data["slug"]])

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Wake_Up_Data.objects.filter(slug=post_training_data["slug"]).exists())

class UserFilterTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ctest", password="test", is_staff=True)
        self.profile = Profile.objects.create(user=self.user, gender="m")
        self.group = Group.objects.create(name="coaches")
        self.user.groups.add(self.group)
        self.user.save()
        print("Setup user:", self.user)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_filter_by_group(self):
        response = self.client.get("/api/user/?groups__name=coaches")
        # self.assertEqual(response.status_code, 200)
        data = response.json()
        print(data)

class WUDFilterTestCase(APITestCase):
    def setUp(self):
        self.user_list_url = reverse("user-list")
        self.wud_list_url = reverse("wake_up_data-list")
        
        self.athlete = User.objects.create_user(username="atest", password="test")
        Profile.objects.create(user=self.athlete, gender="m")
        group = Group.objects.create(name="athletes")
        self.athlete.groups.add(group)
        self.athlete.save()

        self.coach = User.objects.create_user(username="ctest", password="test")
        Profile.objects.create(user=self.coach, gender="m")
        group = Group.objects.create(name="coaches")
        self.coach.groups.add(group)
        self.coach.save()

        print("Setup user:", self.coach)
        self.client = APIClient()
        self.client.force_authenticate(user=self.coach)

        data = {
            "date": "2023-10-01",
            "username": self.athlete.username
        }
        self.client.post(self.wud_list_url, data, format="json")

    def test(self):
        response = self.client.get("/api/wake_up/?user__username=atest")
        # self.assertEqual(response.status_code, 200)
        data = response.json()
        print(data)