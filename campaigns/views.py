from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import models

from .models import (
    Campaign, CampaignGoal, CampaignBudget, CampaignAsset, CampaignMember,
    CampaignAnalytics, CampaignSchedule, CampaignStep, CampaignExecution,
    CampaignRun, CampaignLog, CampaignTemplate
)
from .serializers import (
    CampaignSerializer, CampaignGoalSerializer, CampaignBudgetSerializer,
    CampaignAssetSerializer, CampaignMemberSerializer, CampaignAnalyticsSerializer,
    CampaignScheduleSerializer, CampaignStepSerializer, CampaignExecutionSerializer,
    CampaignRunSerializer, CampaignLogSerializer, CampaignTemplateSerializer
)
from .services import CampaignWorkflowService

class CampaignViewSet(viewsets.ModelViewSet):
    serializer_class = CampaignSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Campaign.objects.filter(
            models.Q(user=user) |
            models.Q(workspace__members__user=user, workspace__members__status='ACTIVE') |
            models.Q(brand__workspace__members__user=user, brand__workspace__members__status='ACTIVE')
        ).distinct().order_by('-created_at')

    def perform_create(self, serializer):
        brand = serializer.validated_data.get('brand')
        workspace = serializer.validated_data.get('workspace')
        if not workspace and brand:
            workspace = brand.workspace
        campaign = serializer.save(user=self.request.user, workspace=workspace)
        CampaignBudget.objects.get_or_create(campaign=campaign, defaults={'allocated': campaign.budget})
        CampaignAnalytics.objects.get_or_create(campaign=campaign)

    @action(detail=True, methods=['post'], url_path='execute')
    def execute(self, request, pk=None):
        campaign = self.get_object()
        execution = CampaignWorkflowService.execute_campaign(campaign)
        return Response(CampaignExecutionSerializer(execution).data, status=status.HTTP_200_OK)

class CampaignGoalViewSet(viewsets.ModelViewSet):
    serializer_class = CampaignGoalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CampaignGoal.objects.filter(campaign__user=self.request.user)

class CampaignBudgetViewSet(viewsets.ModelViewSet):
    serializer_class = CampaignBudgetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CampaignBudget.objects.filter(campaign__user=self.request.user)

class CampaignAssetViewSet(viewsets.ModelViewSet):
    serializer_class = CampaignAssetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CampaignAsset.objects.filter(campaign__user=self.request.user)

class CampaignMemberViewSet(viewsets.ModelViewSet):
    serializer_class = CampaignMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CampaignMember.objects.filter(campaign__user=self.request.user)

class CampaignAnalyticsViewSet(viewsets.ModelViewSet):
    serializer_class = CampaignAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CampaignAnalytics.objects.filter(campaign__user=self.request.user)

class CampaignScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = CampaignScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CampaignSchedule.objects.filter(campaign__user=self.request.user)

class CampaignStepViewSet(viewsets.ModelViewSet):
    serializer_class = CampaignStepSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CampaignStep.objects.filter(campaign__user=self.request.user)

class CampaignExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CampaignExecutionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CampaignExecution.objects.filter(campaign__user=self.request.user).order_by('-started_at')

class CampaignTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = CampaignTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return CampaignTemplate.objects.filter(
            models.Q(user=user) | models.Q(is_public=True)
        ).distinct().order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='instantiate')
    def instantiate(self, request, pk=None):
        template = self.get_object()
        name = request.data.get('name', f"Campaign from {template.name}")
        brand_id = request.data.get('brand')
        workspace_id = request.data.get('workspace')

        brand = None
        workspace = None
        if brand_id:
            from social.models import Brand
            brand = Brand.objects.filter(id=brand_id).first()
        if workspace_id:
            from workspaces.models import Workspace
            workspace = Workspace.objects.filter(id=workspace_id).first()

        campaign = CampaignWorkflowService.create_campaign_from_template(
            template=template,
            user=request.user,
            name=name,
            workspace=workspace,
            brand=brand
        )
        return Response(CampaignSerializer(campaign).data, status=status.HTTP_201_CREATED)
