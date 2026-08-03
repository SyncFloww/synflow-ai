from django.db import models
from django.contrib.auth.models import User
from workspaces.models import Workspace

class ApprovalWorkflow(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, null=True, blank=True, related_name='approval_workflows')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Workflow: {self.name}"

class ApprovalStage(models.Model):
    workflow = models.ForeignKey(ApprovalWorkflow, on_delete=models.CASCADE, null=True, blank=True, related_name='stages')
    approval_request = models.ForeignKey('ApprovalRequest', on_delete=models.CASCADE, null=True, blank=True, related_name='stages')
    step_number = models.IntegerField(default=1)
    name = models.CharField(max_length=255, default='Stage')
    role_required = models.CharField(max_length=100, default='manager')
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_stages')
    status = models.CharField(max_length=50, default='pending')

    def __str__(self):
        return f"Stage {self.step_number}: {self.name}"

class ApprovalRequest(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('in_review', 'In Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('changes_requested', 'Changes Requested'),
    )
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, null=True, blank=True, related_name='approval_requests')
    workflow = models.ForeignKey(ApprovalWorkflow, on_delete=models.SET_NULL, null=True, blank=True, related_name='requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approval_requests_sent')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approval_requests_received')
    content_type = models.CharField(max_length=100, default='content') # e.g. "campaign", "content"
    object_id = models.IntegerField(default=0) # campaign or content id
    title = models.CharField(max_length=255, default='Approval Request')
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='pending')
    current_stage = models.ForeignKey(ApprovalStage, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_requests')
    comments = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Approval Request #{self.id} ({self.status}) for {self.content_type}"

class ReviewerAssignment(models.Model):
    approval_request = models.ForeignKey(ApprovalRequest, on_delete=models.CASCADE, related_name='reviewer_assignments')
    stage = models.ForeignKey(ApprovalStage, on_delete=models.CASCADE, null=True, blank=True, related_name='assignments')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_assignments')
    status = models.CharField(max_length=50, default='pending')
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Assignment: {self.reviewer.username} on Request #{self.approval_request.id}"

class ApprovalDecision(models.Model):
    DECISION_CHOICES = (
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('changes_requested', 'Changes Requested'),
    )
    approval_request = models.ForeignKey(ApprovalRequest, on_delete=models.CASCADE, related_name='decisions')
    stage = models.ForeignKey(ApprovalStage, on_delete=models.SET_NULL, null=True, blank=True, related_name='decisions')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approval_decisions')
    decision = models.CharField(max_length=25, choices=DECISION_CHOICES)
    reason = models.TextField(blank=True, default='')
    decided_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Decision ({self.decision}) by {self.reviewer.username} for Request #{self.approval_request.id}"

class ApprovalComment(models.Model):
    approval_request = models.ForeignKey(ApprovalRequest, on_delete=models.CASCADE, related_name='comments_list')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.username} on Request #{self.approval_request.id}"

class ReviewHistory(models.Model):
    approval_request = models.ForeignKey(ApprovalRequest, on_delete=models.CASCADE, related_name='review_histories')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100) # e.g. "submitted", "approved", "rejected", "requested_changes"
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review History #{self.id} - {self.action} by {self.user.username}"

class ApprovalHistory(models.Model):
    approval_request = models.ForeignKey(ApprovalRequest, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"History #{self.id} - {self.action} by {self.user.username}"

class WorkspaceActivityFeed(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, null=True, blank=True, related_name='activity_feed')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=100)
    description = models.TextField()
    target_content_type = models.CharField(max_length=100, blank=True, default='')
    target_object_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Activity: {self.activity_type} by {self.user.username}"

class NotificationEvent(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, null=True, blank=True, related_name='notification_events')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_events')
    event_type = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Event ({self.event_type}) for {self.recipient.username}"

# Alias for WorkspaceActivity
WorkspaceActivity = WorkspaceActivityFeed
