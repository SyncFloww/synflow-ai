from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SupportTicketViewSet, CustomerHealthViewSet

router = DefaultRouter()
router.register('tickets', SupportTicketViewSet, basename='ticket')
router.register('customer_health', CustomerHealthViewSet, basename='customer_health')

urlpatterns = [
    path('', include(router.urls)),
]
