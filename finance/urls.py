from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RevenueRecordViewSet, ExpenseRecordViewSet, SubscriptionViewSet

router = DefaultRouter()
router.register('revenues', RevenueRecordViewSet, basename='revenue')
router.register('expenses', ExpenseRecordViewSet, basename='expense')
router.register('subscriptions', SubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('', include(router.urls)),
]
