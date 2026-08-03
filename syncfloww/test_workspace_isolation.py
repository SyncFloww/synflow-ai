from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from workspaces.models import Workspace, WorkspaceMember
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
        
        # User A's workspace — created properly so WorkspaceMember is also created
        self.workspace_a = Workspace.objects.create(name="Workspace A", slug="ws-a", owner=self.user_a)
        WorkspaceMember.objects.create(workspace=self.workspace_a, user=self.user_a, role=WorkspaceMember.Role.OWNER)
        self.brand_a = Brand.objects.create(workspace=self.workspace_a, name="Brand A")
        self.content_a = Content.objects.create(workspace=self.workspace_a, author=self.user_a, title="Content A")
        self.social_a = SocialAccount.objects.create(
            workspace=self.workspace_a,
            platform=Platform.MOCK,
            platform_account_id="A1",
            username="user_a_social"
        )
        
        # User B's workspace
        self.workspace_b = Workspace.objects.create(name="Workspace B", slug="ws-b", owner=self.user_b)
        WorkspaceMember.objects.create(workspace=self.workspace_b, user=self.user_b, role=WorkspaceMember.Role.OWNER)
        
    def test_user_b_cannot_list_workspace_a_brands(self):
        """User B cannot list brands in Workspace A."""
        response = self.client_b.get(f'/api/v1/brands/workspaces/{self.workspace_a.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_b_cannot_access_workspace_a_brand_detail(self):
        """User B cannot access a specific Brand in Workspace A, even with the correct ID."""
        response = self.client_b.get(f'/api/v1/brands/workspaces/{self.workspace_a.id}/{self.brand_a.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_user_b_cannot_list_workspace_a_content(self):
        """User B cannot list content from Workspace A."""
        response = self.client_b.get(f'/api/v1/content/workspaces/{self.workspace_a.id}/contents/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_b_cannot_access_workspace_a_content_detail(self):
        """User B cannot access a specific Content from Workspace A."""
        response = self.client_b.get(f'/api/v1/content/workspaces/{self.workspace_a.id}/contents/{self.content_a.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_user_b_cannot_list_workspace_a_social(self):
        """User B cannot list social accounts from Workspace A."""
        response = self.client_b.get(f'/api/v1/social/workspaces/{self.workspace_a.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_user_b_cannot_view_workspace_a_social_status(self):
        """User B cannot check status of a social account in Workspace A."""
        response = self.client_b.get(f'/api/v1/social/{self.social_a.id}/status/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_a_can_access_own_brand(self):
        """User A can access their own brand."""
        response = self.client_a.get(f'/api/v1/brands/workspaces/{self.workspace_a.id}/{self.brand_a.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_a_can_list_own_content(self):
        """User A can list content in their own workspace."""
        response = self.client_a.get(f'/api/v1/content/workspaces/{self.workspace_a.id}/contents/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
