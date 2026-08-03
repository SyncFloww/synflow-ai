from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ApprovalWorkflowViewSet, ApprovalRequestViewSet,
    WorkspaceActivityFeedViewSet, NotificationEventViewSet
)

router = DefaultRouter()
router.register(r'workflows', ApprovalWorkflowViewSet, basename='approvalworkflow')
router.register(r'requests', ApprovalRequestViewSet, basename='approvalrequest')
router.register(r'activity-feed', WorkspaceActivityFeedViewSet, basename='activityfeed')
router.register(r'notifications', NotificationEventViewSet, basename='notificationevent')

urlpatterns = [
    path('', include(router.urls)),
]
