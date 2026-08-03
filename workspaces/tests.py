from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from workspaces.models import Workspace, WorkspaceMember, Invitation, WorkspaceSetting

class WorkspaceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(username='owner', email='owner@example.com', password='password123')
        self.admin_user = User.objects.create_user(username='admin_user', email='admin@example.com', password='password123')
        self.member_user = User.objects.create_user(username='member_user', email='member@example.com', password='password123')
        self.stranger = User.objects.create_user(username='stranger', email='stranger@example.com', password='password123')

        self.client.force_authenticate(user=self.owner)
        response = self.client.post('/api/workspaces/', {
            'name': 'Owner Workspace',
            'description': 'Main workspace'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.workspace_id = response.data['id']
        self.workspace = Workspace.objects.get(id=self.workspace_id)

    def test_workspace_creation_creates_owner_member_and_setting(self):
        self.assertTrue(WorkspaceMember.objects.filter(workspace=self.workspace, user=self.owner, role='OWNER', status='ACTIVE').exists())
        self.assertTrue(WorkspaceSetting.objects.filter(workspace=self.workspace).exists())

    def test_workspace_isolation_and_permissions(self):
        # Stranger cannot see workspace
        self.client.force_authenticate(user=self.stranger)
        response = self.client.get('/api/workspaces/')
        self.assertEqual(len(response.data), 0)

        response = self.client.get(f'/api/workspaces/{self.workspace_id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_and_manage_members(self):
        # Owner adds member
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(f'/api/workspaces/{self.workspace_id}/members/', {
            'user_id': self.member_user.id,
            'role': 'MEMBER'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Member can now list workspaces and see it
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get('/api/workspaces/')
        self.assertEqual(len(response.data), 1)

        # Member CANNOT add another member
        response = self.client.post(f'/api/workspaces/{self.workspace_id}/members/', {
            'user_id': self.stranger.id,
            'role': 'MEMBER'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_admin_member_role_hierarchy(self):
        # Owner adds admin
        self.client.force_authenticate(user=self.owner)
        resp = self.client.post(f'/api/workspaces/{self.workspace_id}/members/', {
            'user_id': self.admin_user.id,
            'role': 'ADMIN'
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        admin_member_id = resp.data['id']

        # Admin cannot delete workspace
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(f'/api/workspaces/{self.workspace_id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin cannot grant OWNER role
        response = self.client.post(f'/api/workspaces/{self.workspace_id}/members/', {
            'user_id': self.stranger.id,
            'role': 'OWNER'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invitation_flow_and_tenant_security(self):
        # Owner invites user
        self.client.force_authenticate(user=self.owner)
        resp = self.client.post(f'/api/workspaces/{self.workspace_id}/invite/', {
            'email': 'invited@example.com',
            'role': 'MEMBER'
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        token = resp.data['token']

        # Stranger cannot view invitations list
        self.client.force_authenticate(user=self.stranger)
        resp = self.client.get('/api/invitations/')
        self.assertEqual(len(resp.data), 0)

        # Invited user accepts invitation with token
        resp = self.client.post('/api/invitations/accept/', {'token': token})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(WorkspaceMember.objects.filter(workspace=self.workspace, user=self.stranger, status='ACTIVE').exists())

        # Cannot reuse token
        resp = self.client.post('/api/invitations/accept/', {'token': token})
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_remove_sole_owner(self):
        self.client.force_authenticate(user=self.owner)
        owner_member = WorkspaceMember.objects.get(workspace=self.workspace, user=self.owner)
        response = self.client.delete(f'/api/workspaces/{self.workspace_id}/members/{owner_member.id}/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_suspended_and_removed_members_denied_access(self):
        # Add a suspended member and a removed member
        suspended_user = User.objects.create_user(username='suspended', email='suspended@example.com', password='password123')
        removed_user = User.objects.create_user(username='removed', email='removed@example.com', password='password123')

        WorkspaceMember.objects.create(workspace=self.workspace, user=suspended_user, role='MEMBER', status='SUSPENDED')
        WorkspaceMember.objects.create(workspace=self.workspace, user=removed_user, role='MEMBER', status='REMOVED')

        # Suspended member cannot view workspace
        self.client.force_authenticate(user=suspended_user)
        response = self.client.get('/api/workspaces/')
        self.assertEqual(len(response.data), 0)
        response = self.client.get(f'/api/workspaces/{self.workspace_id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Removed member cannot view workspace
        self.client.force_authenticate(user=removed_user)
        response = self.client.get('/api/workspaces/')
        self.assertEqual(len(response.data), 0)
        response = self.client.get(f'/api/workspaces/{self.workspace_id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cross_tenant_invitation_and_workspace_isolation_matrix(self):
        # Create Workspace B owned by User B
        user_b = User.objects.create_user(username='user_b', email='user_b@example.com', password='password123')
        ws_b = Workspace.objects.create(name='Workspace B', owner=user_b, created_by=user_b)
        WorkspaceMember.objects.create(workspace=ws_b, user=user_b, role='OWNER', status='ACTIVE')

        # User B creates invitation in Workspace B
        inv_b = Invitation.objects.create(
            workspace=ws_b,
            email='invite_b@example.com',
            role='MEMBER',
            token='token_b_123',
            invited_by=user_b,
            expires_at=timezone.now() + timedelta(days=7)
        )

        # Owner (User A) attempts to access Workspace B resources
        self.client.force_authenticate(user=self.owner)

        # Cannot GET Workspace B detail
        res = self.client.get(f'/api/workspaces/{ws_b.id}/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        # Cannot PATCH Workspace B
        res = self.client.patch(f'/api/workspaces/{ws_b.id}/', {'name': 'Hacked Workspace'})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        # Cannot DELETE Workspace B
        res = self.client.delete(f'/api/workspaces/{ws_b.id}/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        # Cannot GET Workspace B members
        res = self.client.get(f'/api/workspaces/{ws_b.id}/members/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        # Cannot list or delete Workspace B invitations
        res = self.client.get('/api/invitations/')
        inv_ids = [inv['id'] for inv in res.data]
        self.assertNotIn(inv_b.id, inv_ids)

        res = self.client.delete(f'/api/invitations/{inv_b.id}/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
