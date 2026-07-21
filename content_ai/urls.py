from django.urls import path
from .views import GenerateContentView

urlpatterns = [
    path('workspaces/<uuid:workspace_id>/generate/', GenerateContentView.as_view(), name='ai-generate'),
]
