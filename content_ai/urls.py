from django.urls import path
from .views import GenerateContentView, GenerationHistoryAPIView

urlpatterns = [
    path('workspaces/<uuid:workspace_id>/generate/', GenerateContentView.as_view(), name='ai-generate'),
    path('workspaces/<uuid:workspace_id>/history/', GenerationHistoryAPIView.as_view(), name='ai-history'),
]
