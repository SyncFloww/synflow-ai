from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContentViewSet, MediaAssetViewSet

router = DefaultRouter()
router.register(r'media', MediaAssetViewSet, basename='media')
router.register(r'contents', ContentViewSet, basename='content')

urlpatterns = [
    path('workspaces/<uuid:workspace_id>/', include(router.urls)),
]
