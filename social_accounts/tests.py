from django.urls import reverse
from rest_framework.test import APITestCase
from workspaces.models import Workspace
from accounts.models import User
from .models import SocialAccount, ConnectionStatus, Platform, OAuthToken
from .providers import MockOAuthProvider

class SocialAccountAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@example.com", password="StrongPass123!", first_name="Test", last_name="User")
        self.workspace = Workspace.objects.create(name="Test Workspace", slug="test-workspace", owner=self.user)
        # Assuming simple JWT authentication for this test setup if required, 
        # but since we didn't add it in setUp, let's force authenticate:
        self.client.force_authenticate(user=self.user)

    def test_mock_oauth_provider(self):
        provider = MockOAuthProvider()
        url = provider.get_authorization_url("http://localhost/callback")
        self.assertIn("redirect_uri", url)
        
        token_data = provider.exchange_code_for_token("valid_code", "http://localhost/callback")
        self.assertIn("access_token", token_data)
        
        profile = provider.fetch_user_profile(token_data["access_token"])
        self.assertEqual(profile["username"], "mock_user")

    def test_connect_mock_account(self):
        url = reverse('social-connect', kwargs={'workspace_id': self.workspace.id})
        data = {"code": "valid_code", "platform": "mock"}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, 201)
        self.assertTrue(SocialAccount.objects.filter(workspace=self.workspace, platform="mock").exists())
        
        account = SocialAccount.objects.get(workspace=self.workspace, platform="mock")
        self.assertEqual(account.status, ConnectionStatus.CONNECTED)
        self.assertEqual(account.username, "mock_user")
        self.assertTrue(hasattr(account, 'token'))

    def test_disconnect_account(self):
        account = SocialAccount.objects.create(
            workspace=self.workspace,
            platform=Platform.MOCK,
            platform_account_id="123",
            status=ConnectionStatus.CONNECTED
        )
        url = reverse('social-disconnect', kwargs={'account_id': account.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 200)
        account.refresh_from_db()
        self.assertEqual(account.status, ConnectionStatus.DISCONNECTED)

    def test_account_status(self):
        account = SocialAccount.objects.create(
            workspace=self.workspace,
            platform=Platform.MOCK,
            platform_account_id="123",
            status=ConnectionStatus.CONNECTED
        )
        url = reverse('social-status', kwargs={'account_id': account.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], ConnectionStatus.CONNECTED)
        self.assertFalse(response.data["token_expired"])
