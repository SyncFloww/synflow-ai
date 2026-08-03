from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import PromptLibrary, PromptCategory, PromptVariable
from .serializers import PromptLibrarySerializer, PromptCategorySerializer, PromptVariableSerializer

class PromptCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = PromptCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = PromptCategory.objects.all()

class PromptVariableViewSet(viewsets.ModelViewSet):
    serializer_class = PromptVariableSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = PromptVariable.objects.all()

class PromptLibraryViewSet(viewsets.ModelViewSet):
    serializer_class = PromptLibrarySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PromptLibrary.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='render')
    def render_prompt(self, request, pk=None):
        prompt = self.get_object()
        user_variables = request.data.get('variables', {}) # dictionary of variable name -> user value
        
        rendered_text = prompt.prompt_text
        for var_name, var_val in user_variables.items():
            rendered_text = rendered_text.replace(f"{{{{{var_name}}}}}", str(var_val))
            rendered_text = rendered_text.replace(f"{{{var_name}}}", str(var_val))
            
        return Response({
            'original_prompt_id': prompt.id,
            'title': prompt.title,
            'rendered_text': rendered_text
        }, status=status.HTTP_200_OK)
