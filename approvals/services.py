from django.db import transaction
from django.utils import timezone
from typing import Dict, Any, Optional

from .models import (
    ApprovalWorkflow, ApprovalStage, ApprovalRequest,
    ReviewerAssignment, ApprovalDecision, ApprovalComment,
    ReviewHistory, WorkspaceActivityFeed, NotificationEvent
)
from workspaces.models import Workspace

class ApprovalWorkflowService:
    """
    Service for Collaboration & Approval Workflows (Milestone 8).
    Flow:
    Draft -> Submit for Review -> Reviewer Assignment -> Comments -> Approval / Rejection -> Revision -> Scheduling -> Publishing
    """

    @staticmethod
    def create_workflow(workspace: Workspace, name: str, description: str = '', stages_data: list = None) -> ApprovalWorkflow:
        with transaction.atomic():
            workflow = ApprovalWorkflow.objects.create(
                workspace=workspace,
                name=name,
                description=description
            )
            if stages_data:
                for idx, stage_info in enumerate(stages_data, start=1):
                    ApprovalStage.objects.create(
                        workflow=workflow,
                        step_number=idx,
                        name=stage_info.get('name', f'Stage {idx}'),
                        role_required=stage_info.get('role_required', 'manager'),
                        approver_id=stage_info.get('approver_id')
                    )
        return workflow

    @staticmethod
    def submit_for_review(
        user,
        content_type: str,
        object_id: int,
        title: str = 'Approval Request',
        workspace: Optional[Workspace] = None,
        workflow: Optional[ApprovalWorkflow] = None,
        reviewer = None,
        comments: str = ''
    ) -> ApprovalRequest:
        with transaction.atomic():
            req = ApprovalRequest.objects.create(
                workspace=workspace,
                workflow=workflow,
                user=user,
                reviewer=reviewer,
                content_type=content_type,
                object_id=object_id,
                title=title,
                status='pending',
                comments=comments
            )

            # Copy stages from workflow if exists
            if workflow and workflow.stages.exists():
                first_stage = None
                for st in workflow.stages.all():
                    created_stage = ApprovalStage.objects.create(
                        approval_request=req,
                        step_number=st.step_number,
                        name=st.name,
                        role_required=st.role_required,
                        approver=st.approver,
                        status='pending'
                    )
                    if st.step_number == 1:
                        first_stage = created_stage

                req.current_stage = first_stage
                req.status = 'in_review'
                req.save()

            if reviewer:
                ReviewerAssignment.objects.create(
                    approval_request=req,
                    stage=req.current_stage,
                    reviewer=reviewer,
                    status='pending'
                )
                NotificationEvent.objects.create(
                    workspace=workspace,
                    recipient=reviewer,
                    event_type='approval_assigned',
                    title=f"New Review Assigned: {title}",
                    message=f"{user.username} requested your approval on {content_type} #{object_id}."
                )

            ReviewHistory.objects.create(
                approval_request=req,
                user=user,
                action='submitted',
                notes=f"Submitted for review. {comments}".strip()
            )

            WorkspaceActivityFeed.objects.create(
                workspace=workspace,
                user=user,
                activity_type='approval_submitted',
                description=f"{user.username} submitted '{title}' for review.",
                target_content_type=content_type,
                target_object_id=object_id
            )

        return req

    @staticmethod
    def make_decision(
        approval_request: ApprovalRequest,
        reviewer,
        decision: str, # 'approved', 'rejected', 'changes_requested'
        reason: str = ''
    ) -> ApprovalDecision:
        with transaction.atomic():
            dec = ApprovalDecision.objects.create(
                approval_request=approval_request,
                stage=approval_request.current_stage,
                reviewer=reviewer,
                decision=decision,
                reason=reason
            )

            if decision == 'approved':
                # Check if there are further stages
                if approval_request.current_stage:
                    next_stage = ApprovalStage.objects.filter(
                        approval_request=approval_request,
                        step_number__gt=approval_request.current_stage.step_number
                    ).order_by('step_number').first()

                    if next_stage:
                        approval_request.current_stage.status = 'approved'
                        approval_request.current_stage.save()
                        approval_request.current_stage = next_stage
                        approval_request.status = 'in_review'
                        if next_stage.approver:
                            ReviewerAssignment.objects.create(
                                approval_request=approval_request,
                                stage=next_stage,
                                reviewer=next_stage.approver
                            )
                    else:
                        if approval_request.current_stage:
                            approval_request.current_stage.status = 'approved'
                            approval_request.current_stage.save()
                        approval_request.status = 'approved'
                else:
                    approval_request.status = 'approved'

            elif decision == 'rejected':
                if approval_request.current_stage:
                    approval_request.current_stage.status = 'rejected'
                    approval_request.current_stage.save()
                approval_request.status = 'rejected'

            elif decision == 'changes_requested':
                if approval_request.current_stage:
                    approval_request.current_stage.status = 'changes_requested'
                    approval_request.current_stage.save()
                approval_request.status = 'changes_requested'

            approval_request.save()

            ReviewHistory.objects.create(
                approval_request=approval_request,
                user=reviewer,
                action=decision,
                notes=reason
            )

            NotificationEvent.objects.create(
                workspace=approval_request.workspace,
                recipient=approval_request.user,
                event_type=f'approval_{decision}',
                title=f"Approval Decision ({decision.replace('_', ' ').title()}): {approval_request.title}",
                message=f"{reviewer.username} marked your request as {decision}. {reason}".strip()
            )

            WorkspaceActivityFeed.objects.create(
                workspace=approval_request.workspace,
                user=reviewer,
                activity_type=f'approval_{decision}',
                description=f"{reviewer.username} marked '{approval_request.title}' as {decision}.",
                target_content_type=approval_request.content_type,
                target_object_id=approval_request.object_id
            )

        return dec

    @staticmethod
    def add_comment(approval_request: ApprovalRequest, author, comment_text: str) -> ApprovalComment:
        with transaction.atomic():
            comment = ApprovalComment.objects.create(
                approval_request=approval_request,
                author=author,
                comment=comment_text
            )

            WorkspaceActivityFeed.objects.create(
                workspace=approval_request.workspace,
                user=author,
                activity_type='approval_comment',
                description=f"{author.username} commented on '{approval_request.title}'.",
                target_content_type=approval_request.content_type,
                target_object_id=approval_request.object_id
            )

        return comment
