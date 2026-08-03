from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from workspaces.models import Workspace, WorkspaceMember
from approvals.models import (
    ApprovalWorkflow, ApprovalStage, ApprovalRequest,
    ReviewerAssignment, ApprovalDecision, ApprovalComment,
    ReviewHistory, WorkspaceActivityFeed, NotificationEvent
)
from approvals.services import ApprovalWorkflowService

class CollaborationAndApprovalTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='creator', email='creator@example.com', password='Password123!')
        self.reviewer = User.objects.create_user(username='reviewer', email='reviewer@example.com', password='Password123!')
        self.client.force_authenticate(user=self.user)

        self.workspace = Workspace.objects.create(name='Approval Workspace', owner=self.user)
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.user, role='OWNER', status='ACTIVE')
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.reviewer, role='ADMIN', status='ACTIVE')

    def test_workflow_creation_and_submission(self):
        workflow = ApprovalWorkflowService.create_workflow(
            workspace=self.workspace,
            name='Content Approval Pipeline',
            description='Standard 2-step approval',
            stages_data=[
                {'name': 'Editor Review', 'role_required': 'editor', 'approver_id': self.reviewer.id},
                {'name': 'Manager Signoff', 'role_required': 'manager'}
            ]
        )

        self.assertEqual(workflow.name, 'Content Approval Pipeline')
        self.assertEqual(workflow.stages.count(), 2)

        req = ApprovalWorkflowService.submit_for_review(
            user=self.user,
            content_type='content',
            object_id=101,
            title='Campaign Launch Post',
            workspace=self.workspace,
            workflow=workflow,
            reviewer=self.reviewer,
            comments='Please review asap.'
        )

        self.assertEqual(req.status, 'in_review')
        self.assertIsNotNone(req.current_stage)
        self.assertEqual(req.current_stage.step_number, 1)

        # Verify activity feed & notification
        self.assertTrue(WorkspaceActivityFeed.objects.filter(workspace=self.workspace, activity_type='approval_submitted').exists())
        self.assertTrue(NotificationEvent.objects.filter(recipient=self.reviewer, event_type='approval_assigned').exists())

    def test_approval_decision_lifecycle(self):
        req = ApprovalWorkflowService.submit_for_review(
            user=self.user,
            content_type='campaign',
            object_id=202,
            title='Q3 Promotion',
            workspace=self.workspace,
            reviewer=self.reviewer,
            comments='Ready for check'
        )

        # Make decision as reviewer
        dec = ApprovalWorkflowService.make_decision(
            approval_request=req,
            reviewer=self.reviewer,
            decision='approved',
            reason='Looks great!'
        )

        req.refresh_from_db()
        self.assertEqual(req.status, 'approved')
        self.assertEqual(dec.decision, 'approved')
        self.assertTrue(ReviewHistory.objects.filter(approval_request=req, action='approved').exists())

    def test_approval_comments_api(self):
        req = ApprovalWorkflowService.submit_for_review(
            user=self.user,
            content_type='content',
            object_id=303,
            title='Blog Post Review',
            workspace=self.workspace,
            reviewer=self.reviewer
        )

        # Add comment via API
        url = f'/api/approvals/requests/{req.id}/comment/'
        res = self.client.post(url, {'comment': 'I updated paragraph 2.'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ApprovalComment.objects.filter(approval_request=req).count(), 1)

    def test_approval_decision_via_api(self):
        req = ApprovalWorkflowService.submit_for_review(
            user=self.user,
            content_type='content',
            object_id=404,
            title='Video Asset Approval',
            workspace=self.workspace,
            reviewer=self.reviewer
        )

        self.client.force_authenticate(user=self.reviewer)
        url = f'/api/approvals/requests/{req.id}/decide/'
        res = self.client.post(url, {'decision': 'changes_requested', 'reason': 'Adjust sound balance'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        req.refresh_from_db()
        self.assertEqual(req.status, 'changes_requested')
