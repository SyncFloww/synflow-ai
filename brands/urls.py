from django.urls import path
from .views import BrandListCreateAPIView, BrandDetailAPIView

urlpatterns = [
    path("workspaces/<uuid:workspace_id>/", BrandListCreateAPIView.as_view()),
    path("workspaces/<uuid:workspace_id>/<uuid:pk>/", BrandDetailAPIView.as_view()),
]
