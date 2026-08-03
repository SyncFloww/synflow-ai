from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AIAgentViewSet, AgentTaskViewSet, AIModelViewSet, PromptTemplateViewSet,
    GeneratedContentViewSet, ContentGenerationViewSet, GenerationHistoryViewSet,
    ExecuteAgentView, GenerateContentView
)

router = DefaultRouter()
router.register('agents', AIAgentViewSet, basename='aiagent')
router.register('tasks', AgentTaskViewSet, basename='agenttask')
router.register('models', AIModelViewSet, basename='aimodel')
router.register('templates', PromptTemplateViewSet, basename='prompttemplate')
router.register('content', GeneratedContentViewSet, basename='generatedcontent')
router.register('generations', ContentGenerationViewSet, basename='contentgeneration')
router.register('histories', GenerationHistoryViewSet, basename='generationhistory')

urlpatterns = [
    path('', include(router.urls)),
    path('agents/<str:agent_type>/execute/', ExecuteAgentView.as_view(), name='execute_agent'),
    path('content/generate/', GenerateContentView.as_view(), name='generate_content'),
]
