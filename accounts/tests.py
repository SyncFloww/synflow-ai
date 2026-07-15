from unittest.mock import Mock, patch

from django.test import override_settings
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


@override_settings(FACEBOOK_APP_ID="facebook-app-id", FACEBOOK_APP_SECRET="facebook-app-secret")
class FacebookLoginTests(APITestCase):
    def _facebook_response(self, data):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = data
        return response

    def test_configuration_returns_the_public_app_id_only(self):
        response = self.client.get("/api/auth/facebook/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"app_id": "facebook-app-id"})

    @patch("accounts.services.http_requests.get")
    def test_login_validates_token_and_returns_jwt_tokens(self, mock_get):
        mock_get.side_effect = [
            self._facebook_response(
                {
                    "data": {
                        "is_valid": True,
                        "app_id": "facebook-app-id",
                        "user_id": "facebook-user-id",
                    }
                }
            ),
            self._facebook_response(
                {
                    "id": "facebook-user-id",
                    "email": "person@example.com",
                    "first_name": "Test",
                    "last_name": "Person",
                }
            ),
        ]

        response = self.client.post(
            "/api/auth/facebook/",
            {"access_token": "facebook-user-token"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["tokens"]["access"])
        self.assertTrue(response.data["tokens"]["refresh"])

        user = User.objects.get(email="person@example.com")
        self.assertTrue(user.is_verified)
        self.assertFalse(user.has_usable_password())
        self.assertTrue(user.referral_code)
        self.assertTrue(Profile.objects.filter(user=user).exists())
        self.assertEqual(mock_get.call_count, 2)

    @patch("accounts.services.http_requests.get")
    def test_login_rejects_token_for_a_different_app(self, mock_get):
        mock_get.return_value = self._facebook_response(
            {
                "data": {
                    "is_valid": True,
                    "app_id": "another-app-id",
                    "user_id": "facebook-user-id",
                }
            }
        )

        response = self.client.post(
            "/api/auth/facebook/",
            {"access_token": "facebook-user-token"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["message"], "Invalid Facebook sign-in token.")
        self.assertFalse(User.objects.filter(email="person@example.com").exists())
        self.assertEqual(mock_get.call_count, 1)

    @override_settings(FACEBOOK_APP_ID="", FACEBOOK_APP_SECRET="")
    def test_login_is_unavailable_when_facebook_is_not_configured(self):
        response = self.client.post(
            "/api/auth/facebook/",
            {"access_token": "facebook-user-token"},
            format="json",
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["message"], "Facebook sign-in is not configured.")
