from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Campaign, CampaignGoal, CampaignBudget, CampaignAsset, CampaignMember,
    CampaignAnalytics, CampaignSchedule, CampaignStep, CampaignExecution,
    CampaignRun, CampaignLog, CampaignTemplate
)

class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class CampaignGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignGoal
        fields = '__all__'

class CampaignBudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignBudget
        fields = '__all__'

class CampaignAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignAsset
        fields = '__all__'

class CampaignMemberSerializer(serializers.ModelSerializer):
    user_detail = UserMiniSerializer(source='user', read_only=True)
    class Meta:
        model = CampaignMember
        fields = ['id', 'campaign', 'user', 'user_detail', 'role']

class CampaignAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignAnalytics
        fields = '__all__'

class CampaignScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignSchedule
        fields = '__all__'

class CampaignStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignStep
        fields = '__all__'

class CampaignLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignLog
        fields = '__all__'

class CampaignRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignRun
        fields = '__all__'

class CampaignExecutionSerializer(serializers.ModelSerializer):
    runs = CampaignRunSerializer(many=True, read_only=True)
    logs = CampaignLogSerializer(many=True, read_only=True)

    class Meta:
        model = CampaignExecution
        fields = '__all__'

class CampaignTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignTemplate
        fields = '__all__'
        read_only_fields = ['user']

class CampaignSerializer(serializers.ModelSerializer):
    goals = CampaignGoalSerializer(many=True, read_only=True)
    budget_detail = CampaignBudgetSerializer(source='campaign_budget', read_only=True)
    assets = CampaignAssetSerializer(source='campaign_assets', many=True, read_only=True)
    members = CampaignMemberSerializer(many=True, read_only=True)
    analytics_detail = CampaignAnalyticsSerializer(source='campaign_analytics', read_only=True)
    schedules = CampaignScheduleSerializer(many=True, read_only=True)
    steps = CampaignStepSerializer(many=True, read_only=True)
    executions = CampaignExecutionSerializer(many=True, read_only=True)

    class Meta:
        model = Campaign
        fields = [
            'id', 'user', 'workspace', 'brand', 'name', 'description', 'goal', 
            'start_date', 'end_date', 'budget', 'status', 'created_at', 'updated_at',
            'goals', 'budget_detail', 'assets', 'members', 'analytics_detail',
            'schedules', 'steps', 'executions'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
