from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkspaceViewSet, InvitationViewSet

router = DefaultRouter()
router.register('invitations', InvitationViewSet, basename='invitation')
router.register('', WorkspaceViewSet, basename='workspace')

urlpatterns = [
    path('<int:pk>/members/<int:member_id>/', WorkspaceViewSet.as_view({'patch': 'manage_member', 'delete': 'manage_member'}), name='workspace-manage-member'),
    path('', include(router.urls)),
]
