from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ActivityLogViewSet

router = DefaultRouter()
router.register(r'workspaces/(?P<workspace_id>[^/.]+)', ActivityLogViewSet, basename='activity-log')

urlpatterns = [
    path('', include(router.urls)),
]
