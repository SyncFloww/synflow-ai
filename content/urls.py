from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContentFolderViewSet, ContentViewSet, ContentVersionViewSet, ContentTagViewSet

router = DefaultRouter()
router.register('folders', ContentFolderViewSet, basename='contentfolder')
router.register('items', ContentViewSet, basename='content')
router.register('versions', ContentVersionViewSet, basename='contentversion')
router.register('tags', ContentTagViewSet, basename='contenttag')

urlpatterns = [
    path('', include(router.urls)),
]
