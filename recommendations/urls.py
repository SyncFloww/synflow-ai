from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AIRecommendationViewSet

router = DefaultRouter()
router.register(r'recommendations', AIRecommendationViewSet, basename='recommendation')

urlpatterns = [
    path('', include(router.urls)),
]
