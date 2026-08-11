from rest_framework import viewsets, permissions
from django.db import models
from .models import Task, ActivityLog
from .serializers import TaskSerializer, ActivityLogSerializer

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Allow viewing tasks assigned to or by the user
        return Task.objects.filter(
            models.Q(assigned_to=self.request.user) | models.Q(assigned_by=self.request.user)
        ).order_by('-created_at')

    def perform_create(self, serializer):
        task = serializer.save(assigned_by=self.request.user)
        # Log activity
        ActivityLog.objects.create(
            user=self.request.user,
            action=f"Created task: {task.title}",
            details=f"Assigned to {task.assigned_to.username}. Due on {task.due_date}"
        )

    def perform_update(self, serializer):
        task = serializer.save()
        # Log activity
        ActivityLog.objects.create(
            user=self.request.user,
            action=f"Updated task: {task.title}",
            details=f"Status: {task.status}"
        )

class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ActivityLog.objects.filter(user=self.request.user).order_by('-created_at')
from django.db import models
