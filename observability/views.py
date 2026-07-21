from rest_framework import viewsets, permissions
from django.shortcuts import get_object_or_404
from workspaces.models import Workspace
from .models import ActivityLog
from .serializers import ActivityLogSerializer

class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        workspace = get_object_or_404(Workspace, id=self.kwargs['workspace_id'])
        return ActivityLog.objects.filter(workspace=workspace)
