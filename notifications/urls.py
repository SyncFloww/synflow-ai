from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, NotificationSettingViewSet

router = DefaultRouter()
router.register('items', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
    path('settings/', NotificationSettingViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}), name='notification_settings'),
]
