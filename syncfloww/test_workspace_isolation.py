from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from workspaces.models import Workspace
from brands.models import Brand
from content.models import Content
from social_accounts.models import SocialAccount, Platform

User = get_user_model()

class WorkspaceIsolationTestCase(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(email='user_a@example.com', password='password123', first_name='A', last_name='User')
        self.user_b = User.objects.create_user(email='user_b@example.com', password='password123', first_name='B', last_name='User')
        
        self.client_a = APIClient()
        self.client_a.force_authenticate(user=self.user_a)
        
        self.client_b = APIClient()
        self.client_b.force_authenticate(user=self.user_b)
        
        # User A's workspace and data
        self.workspace_a = Workspace.objects.create(name="Workspace A", slug="ws-a", owner=self.user_a)
        self.brand_a = Brand.objects.create(workspace=self.workspace_a, name="Brand A")
        self.content_a = Content.objects.create(workspace=self.workspace_a, author=self.user_a, title="Content A")
        self.social_a = SocialAccount.objects.create(workspace=self.workspace_a, platform=Platform.MOCK, platform_account_id="A1")
        
        # User B's workspace
        self.workspace_b = Workspace.objects.create(name="Workspace B", slug="ws-b", owner=self.user_b)
        
    def test_user_b_cannot_access_workspace_a_brand(self):
        # Even if B guesses the brand ID, B should get a 404/403 when hitting WS A or Brand A
        response = self.client_b.get(f'/api/v1/brands/workspaces/{self.workspace_a.id}/{self.brand_a.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_user_b_cannot_access_workspace_a_content(self):
        response = self.client_b.get(f'/api/v1/content/workspaces/{self.workspace_a.id}/contents/{self.content_a.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_user_b_cannot_access_workspace_a_social(self):
        response = self.client_b.get(f'/api/v1/social/{self.social_a.id}/status/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
