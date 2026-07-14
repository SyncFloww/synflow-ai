from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import User
from .models import Workspace, WorkspaceMember


class WorkspaceAPITests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="StrongPass123!", first_name="Owner", last_name="User")
        self.other = User.objects.create_user(email="other@example.com", password="StrongPass123!", first_name="Other", last_name="User")

    def authenticate(self, user):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")

    def test_owner_can_create_workspace_and_brand(self):
        self.authenticate(self.owner)
        response = self.client.post("/api/v1/workspaces/", {"name": "Acme", "slug": "acme"}, format="json")
        self.assertEqual(response.status_code, 201)
        workspace_id = response.data["id"]
        self.assertEqual(WorkspaceMember.objects.get(workspace_id=workspace_id, user=self.owner).role, WorkspaceMember.Role.OWNER)

        response = self.client.post(f"/api/v1/brands/workspaces/{workspace_id}/", {"name": "Acme Main", "voice": {"tone": "clear"}}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["voice"]["tone"], "clear")

    def test_non_member_cannot_view_workspace(self):
        workspace = Workspace.objects.create(name="Private", slug="private", owner=self.owner)
        WorkspaceMember.objects.create(workspace=workspace, user=self.owner, role=WorkspaceMember.Role.OWNER)
        self.authenticate(self.other)
        self.assertEqual(self.client.get(f"/api/v1/workspaces/{workspace.id}/").status_code, 404)
