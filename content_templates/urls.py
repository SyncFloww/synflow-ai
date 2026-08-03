from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContentTemplateViewSet

router = DefaultRouter()
router.register(r'templates', ContentTemplateViewSet, basename='contenttemplate')

urlpatterns = [
    path('', include(router.urls)),
]
