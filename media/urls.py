from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MediaFolderViewSet, MediaViewSet, MediaTagViewSet

router = DefaultRouter()
router.register('folders', MediaFolderViewSet, basename='mediafolder')
router.register('items', MediaViewSet, basename='media')
router.register('tags', MediaTagViewSet, basename='mediatag')

urlpatterns = [
    path('', include(router.urls)),
]
