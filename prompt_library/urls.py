from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PromptLibraryViewSet, PromptCategoryViewSet, PromptVariableViewSet

router = DefaultRouter()
router.register(r'prompts', PromptLibraryViewSet, basename='promptlibrary')
router.register(r'categories', PromptCategoryViewSet, basename='promptcategory')
router.register(r'variables', PromptVariableViewSet, basename='promptvariable')

urlpatterns = [
    path('', include(router.urls)),
]
