from django.urls import path
from .views import MockConnectView, DisconnectView, AccountStatusView, SocialAccountListAPIView

urlpatterns = [
    path('workspaces/<uuid:workspace_id>/', SocialAccountListAPIView.as_view(), name='social-list'),
    path('workspaces/<uuid:workspace_id>/connect/', MockConnectView.as_view(), name='social-connect'),
    path('<uuid:account_id>/disconnect/', DisconnectView.as_view(), name='social-disconnect'),
    path('<uuid:account_id>/status/', AccountStatusView.as_view(), name='social-status'),
]
