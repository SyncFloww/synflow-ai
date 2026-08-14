from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AIAgentViewSet, AgentTaskViewSet, AIModelViewSet, PromptTemplateViewSet,
    GeneratedContentViewSet, ContentGenerationViewSet, GenerationHistoryViewSet,
    ExecuteAgentView, GenerateContentView,
    AIJobViewSet, AIContentProjectViewSet, AIScriptViewSet,
    AIIdeaGeneratorView, AIScriptGeneratorView, AIImageGeneratorView, AIVideoGeneratorView,
    AIVoiceStudioView, CustomVoiceView, VoiceConsentView, AIAudioMixerView,
    AICaptionView, AIMagicEditorView, AIUsageView
)

router = DefaultRouter()
router.register('agents', AIAgentViewSet, basename='aiagent')
router.register('tasks', AgentTaskViewSet, basename='agenttask')
router.register('models', AIModelViewSet, basename='aimodel')
router.register('templates', PromptTemplateViewSet, basename='prompttemplate')
router.register('content', GeneratedContentViewSet, basename='generatedcontent')
router.register('generations', ContentGenerationViewSet, basename='contentgeneration')
router.register('histories', GenerationHistoryViewSet, basename='generationhistory')
router.register('jobs', AIJobViewSet, basename='aijob')
router.register('projects', AIContentProjectViewSet, basename='aiproject')
router.register('scripts', AIScriptViewSet, basename='aiscript')

urlpatterns = [
    path('', include(router.urls)),
    path('agents/<str:agent_type>/execute/', ExecuteAgentView.as_view(), name='execute_agent'),
    path('content/generate/', GenerateContentView.as_view(), name='generate_content'),
    
    # AI Media Studio endpoints
    path('ideas/generate/', AIIdeaGeneratorView.as_view(), name='ai_ideas_generate'),
    path('scripts/generate/', AIScriptGeneratorView.as_view(), name='ai_scripts_generate'),
    path('images/generate/', AIImageGeneratorView.as_view(), name='ai_images_generate'),
    path('videos/generate/', AIVideoGeneratorView.as_view(), name='ai_videos_generate'),
    path('voices/', AIVoiceStudioView.as_view(), name='ai_voices_list'),
    path('voices/generate/', AIVoiceStudioView.as_view(), name='ai_voices_generate'),
    path('voices/custom/', CustomVoiceView.as_view(), name='ai_voices_custom'),
    path('voices/consent/', VoiceConsentView.as_view(), name='ai_voices_consent'),
    path('audio/mix/', AIAudioMixerView.as_view(), name='ai_audio_mix'),
    path('captions/generate/', AICaptionView.as_view(), name='ai_captions_generate'),
    path('editor/action/', AIMagicEditorView.as_view(), name='ai_editor_action'),
    path('usage/', AIUsageView.as_view(), name='ai_usage'),
]
