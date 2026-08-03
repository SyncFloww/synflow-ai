from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmployeeViewSet, LeaveRequestViewSet

router = DefaultRouter()
router.register('employees', EmployeeViewSet, basename='employee')
router.register('leaves', LeaveRequestViewSet, basename='leave')

urlpatterns = [
    path('', include(router.urls)),
]
