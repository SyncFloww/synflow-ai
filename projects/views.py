from rest_framework import viewsets, permissions
from .models import Project
from .serializers import ProjectSerializer

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filter projects by the currently authenticated user
        queryset = Project.objects.filter(user=self.request.user)
        project_type = self.request.query_params.get('project_type')
        if project_type:
            queryset = queryset.filter(project_type=project_type)
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        # Automatically associate the new project with the logged-in user
        serializer.save(user=self.request.user)
