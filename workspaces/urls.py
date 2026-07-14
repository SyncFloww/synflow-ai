from django.urls import path
from .views import WorkspaceListCreateAPIView, WorkspaceDetailAPIView, WorkspaceMembersAPIView, WorkspaceInviteAPIView, AcceptInvitationAPIView

urlpatterns = [
    path("", WorkspaceListCreateAPIView.as_view()),
    path("<uuid:pk>/", WorkspaceDetailAPIView.as_view()),
    path("<uuid:pk>/members/", WorkspaceMembersAPIView.as_view()),
    path("<uuid:pk>/invitations/", WorkspaceInviteAPIView.as_view()),
    path("invitations/<uuid:token>/accept/", AcceptInvitationAPIView.as_view()),
]
