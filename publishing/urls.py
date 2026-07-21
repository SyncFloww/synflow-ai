from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PostViewSet

router = DefaultRouter()
router.register(r'workspaces/(?P<workspace_id>[^/.]+)', PostViewSet, basename='post')

urlpatterns = [
    path('', include(router.urls)),
]
