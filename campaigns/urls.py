from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CampaignViewSet, CampaignGoalViewSet, CampaignBudgetViewSet,
    CampaignAssetViewSet, CampaignMemberViewSet, CampaignAnalyticsViewSet,
    CampaignScheduleViewSet, CampaignStepViewSet, CampaignExecutionViewSet,
    CampaignTemplateViewSet
)

router = DefaultRouter()
router.register(r'campaigns', CampaignViewSet, basename='campaign')
router.register(r'goals', CampaignGoalViewSet, basename='campaigngoal')
router.register(r'budgets', CampaignBudgetViewSet, basename='campaignbudget')
router.register(r'assets', CampaignAssetViewSet, basename='campaignasset')
router.register(r'members', CampaignMemberViewSet, basename='campaignmember')
router.register(r'analytics', CampaignAnalyticsViewSet, basename='campaignanalytics')
router.register(r'schedules', CampaignScheduleViewSet, basename='campaignschedule')
router.register(r'steps', CampaignStepViewSet, basename='campaignstep')
router.register(r'executions', CampaignExecutionViewSet, basename='campaignexecution')
router.register(r'templates', CampaignTemplateViewSet, basename='campaigntemplate')

urlpatterns = [
    path('', include(router.urls)),
]
