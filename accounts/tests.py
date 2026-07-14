from rest_framework.test import APITestCase

from .models import EmailVerification, Profile, User


class AccountLifecycleTests(APITestCase):
    def test_registration_creates_profile_and_email_verification(self):
        response = self.client.post("/api/auth/register/", {
            "email": "person@example.com",
            "first_name": "Test",
            "last_name": "Person",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email="person@example.com")
        self.assertTrue(Profile.objects.filter(user=user).exists())
        self.assertTrue(EmailVerification.objects.filter(user=user).exists())
