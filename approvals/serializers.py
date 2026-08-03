from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    ApprovalWorkflow, ApprovalStage, ApprovalRequest,
    ReviewerAssignment, ApprovalDecision, ApprovalComment,
    ReviewHistory, ApprovalHistory, WorkspaceActivityFeed, NotificationEvent
)

class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class ApprovalStageSerializer(serializers.ModelSerializer):
    approver_detail = UserMiniSerializer(source='approver', read_only=True)

    class Meta:
        model = ApprovalStage
        fields = '__all__'

class ApprovalWorkflowSerializer(serializers.ModelSerializer):
    stages = ApprovalStageSerializer(many=True, read_only=True)

    class Meta:
        model = ApprovalWorkflow
        fields = '__all__'

class ReviewerAssignmentSerializer(serializers.ModelSerializer):
    reviewer_detail = UserMiniSerializer(source='reviewer', read_only=True)

    class Meta:
        model = ReviewerAssignment
        fields = '__all__'

class ApprovalDecisionSerializer(serializers.ModelSerializer):
    reviewer_detail = UserMiniSerializer(source='reviewer', read_only=True)

    class Meta:
        model = ApprovalDecision
        fields = '__all__'

class ApprovalCommentSerializer(serializers.ModelSerializer):
    author_detail = UserMiniSerializer(source='author', read_only=True)

    class Meta:
        model = ApprovalComment
        fields = '__all__'

class ReviewHistorySerializer(serializers.ModelSerializer):
    user_detail = UserMiniSerializer(source='user', read_only=True)

    class Meta:
        model = ReviewHistory
        fields = '__all__'

class WorkspaceActivityFeedSerializer(serializers.ModelSerializer):
    user_detail = UserMiniSerializer(source='user', read_only=True)

    class Meta:
        model = WorkspaceActivityFeed
        fields = '__all__'

class NotificationEventSerializer(serializers.ModelSerializer):
    recipient_detail = UserMiniSerializer(source='recipient', read_only=True)

    class Meta:
        model = NotificationEvent
        fields = '__all__'

class ApprovalRequestSerializer(serializers.ModelSerializer):
    user_detail = UserMiniSerializer(source='user', read_only=True)
    reviewer_detail = UserMiniSerializer(source='reviewer', read_only=True)
    stages = ApprovalStageSerializer(many=True, read_only=True)
    reviewer_assignments = ReviewerAssignmentSerializer(many=True, read_only=True)
    decisions = ApprovalDecisionSerializer(many=True, read_only=True)
    comments_list = ApprovalCommentSerializer(many=True, read_only=True)
    review_histories = ReviewHistorySerializer(many=True, read_only=True)

    class Meta:
        model = ApprovalRequest
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']
