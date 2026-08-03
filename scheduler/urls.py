from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CalendarEventViewSet, ScheduleViewSet

router = DefaultRouter()
router.register('events', CalendarEventViewSet, basename='calendarevent')
router.register('queue', ScheduleViewSet, basename='schedule')

urlpatterns = [
    path('', include(router.urls)),
]
