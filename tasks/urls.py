from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, ActivityLogViewSet

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'activities', ActivityLogViewSet, basename='activitylog')

urlpatterns = [
    path('', include(router.urls)),
]
